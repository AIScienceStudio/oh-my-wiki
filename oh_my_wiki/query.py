"""Query system — prepare queries against the wiki and file back results."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from oh_my_wiki.article import (
    Article,
    extract_wikilinks,
    list_articles,
    parse_frontmatter,
    safe_filename,
)


def prepare_query(question: str, wiki_dir: Path, budget: int = 5) -> dict:
    """Analyze the wiki index and return candidate articles to read.

    Returns {candidates: [{title, file, category, relevance}], index_summary: str}.
    The host LLM reads these articles to answer the question.
    """
    index_path = wiki_dir / "index.md"
    if not index_path.exists():
        return {"candidates": [], "index_summary": "Wiki is empty."}

    index_text = index_path.read_text(errors="ignore")
    articles = list_articles(wiki_dir)

    if not articles:
        return {"candidates": [], "index_summary": "Wiki has no articles."}

    # Build search data
    search_entries = []
    for a in articles:
        search_entries.append({
            "title": a.title,
            "file": safe_filename(a.title) + ".md",
            "categories": a.categories,
            "aliases": a.aliases,
            "tags": a.tags,
            "backlink_count": a.backlink_count,
            "confidence": a.confidence,
        })

    return {
        "candidates": search_entries[:budget * 3],  # give LLM 3x budget to choose from
        "index_summary": index_text,
        "budget": budget,
        "question": question,
    }


def file_back(
    question: str,
    answer: str,
    source_article_titles: list[str],
    wiki_dir: Path,
) -> Path:
    """Save a query result as a wiki article and update source articles.

    Returns the path of the saved query article.
    """
    now = datetime.now(timezone.utc)
    slug = re.sub(r"[^\w]", "_", question[:50].lower()).strip("_") or "query"
    title = f"Q: {question[:80]}"

    # Build source links
    source_lines = "\n".join(f"- [[{t}]]" for t in source_article_titles)

    body = (
        f"# {title}\n\n"
        f"> Query result filed back into wiki on {now.strftime('%Y-%m-%d')}.\n\n"
        f"## Answer\n\n{answer}\n\n"
        f"## Source Articles\n\n{source_lines}\n"
    )

    article = Article(
        title=title,
        body=body,
        categories=["queries"],
        tags=_extract_query_tags(question),
        confidence="medium",
        status="active",
    )

    # Save to _queries/
    queries_dir = wiki_dir / "_queries"
    queries_dir.mkdir(exist_ok=True)
    filename = f"{now.strftime('%Y%m%d')}_{slug}.md"
    path = queries_dir / filename
    path.write_text(article.to_markdown(), encoding="utf-8")

    # Update source articles with cross-reference
    for art_title in source_article_titles:
        _add_query_reference(wiki_dir, art_title, title)

    return path


def _extract_query_tags(question: str) -> list[str]:
    """Extract simple tags from a question (lowercase significant words)."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "what", "how", "why",
        "when", "where", "who", "which", "do", "does", "did", "can", "could",
        "should", "would", "my", "your", "our", "their", "this", "that",
        "for", "with", "from", "about", "into", "and", "or", "but", "not",
        "in", "on", "at", "to", "of", "it", "its", "be", "have", "has",
    }
    words = re.findall(r"[a-zA-Z]+", question.lower())
    return [w for w in words if w not in stop_words and len(w) > 2][:5]


def _add_query_reference(wiki_dir: Path, article_title: str, query_title: str) -> None:
    """Add a query cross-reference to an article's Notes section."""
    filename = safe_filename(article_title) + ".md"
    path = wiki_dir / filename
    if not path.exists():
        return

    text = path.read_text(errors="ignore")
    ref_line = f"\nReferenced in query: [[{query_title}]]"

    # Check if already referenced
    if query_title in text:
        return

    # Append to Notes section if it exists, or create one
    if "## Notes" in text:
        text = text.rstrip() + "\n" + ref_line + "\n"
    else:
        text = text.rstrip() + "\n\n## Notes\n" + ref_line + "\n"

    path.write_text(text, encoding="utf-8")
