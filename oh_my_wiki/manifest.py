"""Manifest — tracks raw→article mapping and article→article dependencies."""
from __future__ import annotations

import json
from pathlib import Path

from oh_my_wiki.cache import file_hash

_MANIFEST_PATH = ".omw/manifest.json"


def _empty_manifest() -> dict:
    return {
        "version": 1,
        "last_compile": "",
        "raw_files": {},
        "articles": {},
        "categories": {},
    }


def load(root: Path = Path(".")) -> dict:
    """Load manifest from .omw/manifest.json."""
    path = root / _MANIFEST_PATH
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or "version" not in data:
            return _empty_manifest()
        return data
    except Exception:
        return _empty_manifest()


def save(manifest: dict, root: Path = Path(".")) -> None:
    """Save manifest to .omw/manifest.json."""
    path = root / _MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2))


def register_raw_file(manifest: dict, file_path: str) -> str:
    """Register a raw file in the manifest. Returns its hash."""
    p = Path(file_path)
    h = file_hash(p)
    manifest.setdefault("raw_files", {})[h] = {
        "path": file_path,
        "mtime": p.stat().st_mtime,
        "articles": [],
    }
    return h


def register_article(
    manifest: dict,
    title: str,
    file_path: str,
    sources: list[str],
    backlinks_to: list[str],
    word_count: int = 0,
    confidence: str = "medium",
) -> None:
    """Register a compiled article in the manifest."""
    manifest.setdefault("articles", {})[title] = {
        "file": file_path,
        "sources": sources,
        "backlinks_to": backlinks_to,
        "word_count": word_count,
        "confidence": confidence,
    }


def register_category(manifest: dict, category: str, articles: list[str]) -> None:
    """Register a category with its article list."""
    manifest.setdefault("categories", {})[category] = articles


def get_articles_for_source(manifest: dict, source_hash: str) -> list[str]:
    """Get article titles that were compiled from a given raw file hash."""
    raw = manifest.get("raw_files", {}).get(source_hash, {})
    return raw.get("articles", [])


def get_sources_for_article(manifest: dict, title: str) -> list[str]:
    """Get raw file hashes that contributed to an article."""
    art = manifest.get("articles", {}).get(title, {})
    return art.get("sources", [])


def get_backlink_targets(manifest: dict, title: str) -> list[str]:
    """Get articles that this article links TO."""
    art = manifest.get("articles", {}).get(title, {})
    return art.get("backlinks_to", [])


def find_affected_articles(manifest: dict, changed_hashes: list[str]) -> list[str]:
    """Given changed raw file hashes, find all articles that need updating.

    Returns directly affected articles (compiled from changed sources).
    """
    affected: set[str] = set()
    for h in changed_hashes:
        affected.update(get_articles_for_source(manifest, h))
    return list(affected)


def update_from_compile(
    manifest: dict,
    timestamp: str,
    raw_files: list[str],
    articles: dict,
    categories: dict,
) -> None:
    """Update manifest after a compile run.

    articles: {title: {file, sources, backlinks_to, word_count, confidence}}
    categories: {category_name: [article_titles]}
    """
    manifest["last_compile"] = timestamp

    # Register raw files
    for f in raw_files:
        try:
            register_raw_file(manifest, f)
        except OSError:
            continue

    # Register articles and link back to raw files
    for title, info in articles.items():
        register_article(
            manifest,
            title=title,
            file_path=info.get("file", ""),
            sources=info.get("sources", []),
            backlinks_to=info.get("backlinks_to", []),
            word_count=info.get("word_count", 0),
            confidence=info.get("confidence", "medium"),
        )
        # Update raw_files → articles mapping
        for src_hash in info.get("sources", []):
            if src_hash in manifest.get("raw_files", {}):
                arts = manifest["raw_files"][src_hash].setdefault("articles", [])
                if title not in arts:
                    arts.append(title)

    # Register categories
    for cat, art_list in categories.items():
        register_category(manifest, cat, art_list)
