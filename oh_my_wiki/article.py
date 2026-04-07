"""Article data model — frontmatter parser/renderer, backlink extraction, validation."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Frontmatter parser (stdlib only, no PyYAML)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]")
_INLINE_LIST_RE = re.compile(r"^\[(.+)\]$")


def _parse_value(raw: str) -> str | int | list[str]:
    """Parse a single YAML scalar value."""
    raw = raw.strip()
    # Inline list: ["a", "b", "c"]
    m = _INLINE_LIST_RE.match(raw)
    if m:
        items = []
        for item in m.group(1).split(","):
            item = item.strip().strip('"').strip("'")
            if item:
                items.append(item)
        return items
    # Quoted string
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        return raw[1:-1]
    # Integer
    try:
        return int(raw)
    except ValueError:
        pass
    return raw


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown text.

    Returns (metadata_dict, body_text_after_frontmatter).
    If no frontmatter (no leading ---), returns ({}, full_text).
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text

    body = text[m.end():]
    meta: dict = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for line in m.group(1).splitlines():
        # Continuation of a list
        if line.startswith("  - ") or line.startswith("  -\t"):
            if current_key is not None and current_list is not None:
                val = line.strip().removeprefix("- ").strip().strip('"').strip("'")
                current_list.append(val)
                continue

        # New key: value
        if ":" in line and not line.startswith(" "):
            # Flush previous list
            if current_key and current_list is not None:
                meta[current_key] = current_list
                current_list = None
                current_key = None

            colon = line.index(":")
            key = line[:colon].strip()
            value_part = line[colon + 1:].strip()

            if not value_part:
                # Start of a block list
                current_key = key
                current_list = []
            else:
                meta[key] = _parse_value(value_part)

    # Flush trailing list
    if current_key and current_list is not None:
        meta[current_key] = current_list

    return meta, body


def render_frontmatter(meta: dict) -> str:
    """Render a metadata dict to YAML frontmatter string (including --- delimiters)."""
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, list):
            if key == "aliases":
                # Inline style for Obsidian
                items = ", ".join(f'"{v}"' for v in value)
                lines.append(f"{key}: [{items}]")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
        elif isinstance(value, int):
            lines.append(f"{key}: {value}")
        elif isinstance(value, str) and any(c in value for c in ':"{}[]'):
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Article dataclass
# ---------------------------------------------------------------------------

@dataclass
class Article:
    """Represents a single wiki article."""

    title: str
    body: str
    aliases: list[str] = field(default_factory=list)
    created: str = ""
    updated: str = ""
    sources: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    confidence: str = "medium"
    word_count: int = 0
    backlink_count: int = 0
    status: str = "active"

    def to_markdown(self) -> str:
        """Render the article as a complete markdown file with frontmatter."""
        self.word_count = len(self.body.split())
        if not self.created:
            self.created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if not self.updated:
            self.updated = self.created

        meta = {
            "title": self.title,
            "aliases": self.aliases,
            "created": self.created,
            "updated": self.updated,
            "sources": self.sources,
            "categories": self.categories,
            "tags": self.tags,
            "confidence": self.confidence,
            "word_count": self.word_count,
            "backlink_count": self.backlink_count,
            "status": self.status,
        }
        # Drop empty lists
        meta = {k: v for k, v in meta.items() if v or isinstance(v, int)}
        return render_frontmatter(meta) + "\n\n" + self.body

    @classmethod
    def from_markdown(cls, text: str) -> Article:
        """Parse a markdown file into an Article."""
        meta, body = parse_frontmatter(text)
        return cls(
            title=meta.get("title", ""),
            body=body.strip(),
            aliases=_ensure_list(meta.get("aliases", [])),
            created=str(meta.get("created", "")),
            updated=str(meta.get("updated", "")),
            sources=_ensure_list(meta.get("sources", [])),
            categories=_ensure_list(meta.get("categories", [])),
            tags=_ensure_list(meta.get("tags", [])),
            confidence=str(meta.get("confidence", "medium")),
            word_count=int(meta.get("word_count", 0)),
            backlink_count=int(meta.get("backlink_count", 0)),
            status=str(meta.get("status", "active")),
        )


def _ensure_list(val) -> list[str]:
    if isinstance(val, list):
        return [str(v) for v in val]
    if isinstance(val, str) and val:
        return [val]
    return []


# ---------------------------------------------------------------------------
# Backlink utilities
# ---------------------------------------------------------------------------

def extract_wikilinks(text: str) -> list[str]:
    """Extract all [[wikilink]] targets from markdown text.

    Handles [[Title]] and [[Title|Display Text]] formats.
    Returns deduplicated list preserving first-seen order.
    """
    seen: set[str] = set()
    result: list[str] = []
    for match in _WIKILINK_RE.finditer(text):
        target = match.group(1).strip()
        if target and target not in seen:
            seen.add(target)
            result.append(target)
    return result


def compute_backlink_counts(wiki_dir: Path) -> dict[str, int]:
    """Scan all articles in wiki_dir and count incoming backlinks per title.

    Returns {article_title: number_of_articles_linking_to_it}.
    """
    # Build title → filename mapping (including aliases)
    title_map: dict[str, str] = {}  # lowered title/alias → canonical title
    articles: dict[str, str] = {}   # filename → full text

    for md_file in wiki_dir.glob("*.md"):
        if md_file.name.startswith("_"):
            continue
        text = md_file.read_text(errors="ignore")
        articles[md_file.name] = text
        meta, _ = parse_frontmatter(text)
        title = meta.get("title", md_file.stem)
        title_map[str(title).lower()] = str(title)
        for alias in _ensure_list(meta.get("aliases", [])):
            title_map[alias.lower()] = str(title)

    # Also scan _categories/ and _queries/
    for subdir in ("_categories", "_queries"):
        sub = wiki_dir / subdir
        if sub.is_dir():
            for md_file in sub.glob("*.md"):
                text = md_file.read_text(errors="ignore")
                articles[f"{subdir}/{md_file.name}"] = text

    # Count backlinks
    counts: dict[str, int] = {t: 0 for t in title_map.values()}
    for _fname, text in articles.items():
        links = extract_wikilinks(text)
        # Deduplicate per-article: each article counts as one backlink regardless of how many times it links
        seen_targets: set[str] = set()
        for link in links:
            canonical = title_map.get(link.lower())
            if canonical and canonical not in seen_targets:
                seen_targets.add(canonical)
                counts[canonical] = counts.get(canonical, 0) + 1

    return counts


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def safe_filename(name: str) -> str:
    """Convert an article title to a safe filename (without extension)."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name[:120] or "untitled"


def save_article(wiki_dir: Path, article: Article) -> Path:
    """Write an article to wiki_dir. Returns the file path."""
    wiki_dir.mkdir(parents=True, exist_ok=True)
    filename = safe_filename(article.title) + ".md"
    path = wiki_dir / filename
    path.write_text(article.to_markdown(), encoding="utf-8")
    return path


def load_article(path: Path) -> Article:
    """Load an article from a markdown file."""
    return Article.from_markdown(path.read_text(encoding="utf-8"))


def list_articles(wiki_dir: Path) -> list[Article]:
    """Load all articles from wiki_dir (excluding _ prefixed dirs and special files)."""
    articles = []
    for md_file in sorted(wiki_dir.glob("*.md")):
        if md_file.name.startswith("_") or md_file.name in ("index.md", "WIKI_REPORT.md"):
            continue
        try:
            articles.append(load_article(md_file))
        except Exception:
            continue
    return articles
