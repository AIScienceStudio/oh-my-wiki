"""Compilation orchestration — plan validation, article helpers, compile log."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from oh_my_wiki.article import Article, save_article, extract_wikilinks, safe_filename


# ---------------------------------------------------------------------------
# Plan schema validation
# ---------------------------------------------------------------------------

VALID_ACTIONS = {"create", "update", "stub"}


def validate_plan(plan: dict) -> list[str]:
    """Validate a compilation plan. Returns list of error messages (empty = valid)."""
    errors: list[str] = []

    if "articles" not in plan:
        errors.append("Plan missing 'articles' list")
        return errors

    if not isinstance(plan["articles"], list):
        errors.append("'articles' must be a list")
        return errors

    seen_titles: set[str] = set()
    for i, entry in enumerate(plan["articles"]):
        if not isinstance(entry, dict):
            errors.append(f"articles[{i}] must be a dict")
            continue

        title = entry.get("title")
        if not title:
            errors.append(f"articles[{i}] missing 'title'")
        elif title in seen_titles:
            errors.append(f"articles[{i}] duplicate title: {title}")
        else:
            seen_titles.add(title)

        action = entry.get("action")
        if action not in VALID_ACTIONS:
            errors.append(f"articles[{i}] invalid action: {action}")

        if action == "create" and not entry.get("sources"):
            errors.append(f"articles[{i}] 'create' action requires 'sources'")

    return errors


# ---------------------------------------------------------------------------
# Article creation helpers
# ---------------------------------------------------------------------------

def create_stub(title: str, categories: list[str] | None = None, reason: str = "") -> Article:
    """Create a stub article — placeholder waiting for source material."""
    cats = categories or ["uncategorized"]
    body = f"# {title}\n\n"
    body += f"> Stub article — needs source material.\n\n"
    body += "## Overview\n\n"
    body += f"*This is a placeholder article.* {reason}\n\n"
    body += "## Connections\n\n"
    body += "*No connections yet.*\n"

    return Article(
        title=title,
        body=body,
        categories=cats,
        confidence="low",
        status="stub",
    )


def article_from_plan_entry(
    entry: dict,
    article_text: str,
) -> Article:
    """Parse an LLM-written article string into an Article object.

    If the LLM output includes frontmatter, parse it.
    Otherwise, construct from plan entry + body text.
    """
    article = Article.from_markdown(article_text)

    # Fill in from plan entry if the LLM didn't include frontmatter
    if not article.title:
        article.title = entry.get("title", "Untitled")
    if not article.categories:
        article.categories = entry.get("categories", ["uncategorized"])
    if not article.sources:
        article.sources = entry.get("sources", entry.get("new_sources", []))
    if not article.status:
        article.status = "active"

    return article


# ---------------------------------------------------------------------------
# Compile log
# ---------------------------------------------------------------------------

def create_compile_log(
    mode: str,
    changes: list[dict],
    raw_files_processed: int = 0,
) -> dict:
    """Create a compile log entry."""
    stats = {"create": 0, "update": 0, "stub": 0, "no_action": 0}
    for change in changes:
        action = change.get("action", "no_action")
        stats[action] = stats.get(action, 0) + 1

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "raw_files_processed": raw_files_processed,
        "articles_created": stats["create"],
        "articles_updated": stats["update"],
        "stubs_created": stats["stub"],
        "changes": changes,
    }


def save_compile_log(log: dict, root: Path = Path(".")) -> None:
    """Save compile log to .omw/compile-log.json."""
    path = root / ".omw" / "compile-log.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=2))


def load_compile_log(root: Path = Path(".")) -> dict | None:
    """Load the last compile log."""
    path = root / ".omw" / "compile-log.json"
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Article writing/updating helpers
# ---------------------------------------------------------------------------

def write_articles_from_plan(
    plan: dict,
    article_texts: dict[str, str],
    wiki_dir: Path,
) -> list[dict]:
    """Write articles to disk based on the plan and LLM-generated texts.

    plan: validated compilation plan
    article_texts: {title: markdown_text} from LLM
    wiki_dir: output directory

    Returns list of change records for the compile log.
    """
    changes: list[dict] = []

    for entry in plan.get("articles", []):
        title = entry["title"]
        action = entry["action"]

        if action == "stub":
            article = create_stub(
                title,
                categories=entry.get("categories"),
                reason=entry.get("reason", ""),
            )
            path = save_article(wiki_dir, article)
            changes.append({
                "action": "stub",
                "article": title,
                "file": str(path),
                "reason": entry.get("reason", ""),
            })
            continue

        text = article_texts.get(title)
        if not text:
            changes.append({
                "action": "no_action",
                "article": title,
                "reason": "No article text provided by LLM",
            })
            continue

        article = article_from_plan_entry(entry, text)
        path = save_article(wiki_dir, article)
        changes.append({
            "action": action,
            "article": title,
            "file": str(path),
            "sources": entry.get("sources", entry.get("new_sources", [])),
        })

    return changes


def detect_needed_stubs(plan: dict, article_texts: dict[str, str], existing_titles: set[str]) -> list[dict]:
    """Find [[wikilinks]] in new articles that point to non-existent articles.

    Returns list of stub plan entries to add.
    """
    # Collect all titles that will exist after this compile
    planned_titles = {e["title"] for e in plan.get("articles", [])}
    all_titles = existing_titles | planned_titles

    # Scan article texts for wikilinks
    needed: set[str] = set()
    for _title, text in article_texts.items():
        links = extract_wikilinks(text)
        for link in links:
            if link not in all_titles and link not in needed:
                needed.add(link)

    return [
        {"title": title, "action": "stub", "reason": "Forward reference from new article"}
        for title in sorted(needed)
    ]
