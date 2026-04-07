"""Source ingestion — fetch URLs, copy local files, read stdin into raw/."""
from __future__ import annotations

import json
import re
import shutil
import sys
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from oh_my_wiki.security import safe_fetch, safe_fetch_text, validate_url


def _yaml_str(s: str) -> str:
    """Escape a string for embedding in a YAML double-quoted scalar."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")


def _safe_filename(name: str, suffix: str) -> str:
    """Turn a name/URL into a safe filename."""
    if name.startswith("http"):
        parsed = urllib.parse.urlparse(name)
        name = parsed.netloc + parsed.path
    name = re.sub(r"[^\w\-]", "_", name).strip("_")
    name = re.sub(r"_+", "_", name)[:80]
    return name + suffix


def _detect_url_type(url: str) -> str:
    """Classify the URL for targeted extraction."""
    lower = url.lower()
    if "twitter.com" in lower or "x.com" in lower:
        return "tweet"
    if "arxiv.org" in lower:
        return "arxiv"
    if "github.com" in lower:
        return "github"
    if "youtube.com" in lower or "youtu.be" in lower:
        return "youtube"
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    if path.endswith(".pdf"):
        return "pdf"
    if any(path.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif")):
        return "image"
    return "webpage"


def _html_to_markdown(html: str, url: str) -> str:
    """Convert HTML to clean markdown."""
    try:
        import html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0
        return h.handle(html)
    except ImportError:
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:8000]


def _fetch_tweet(url: str, author: str | None, contributor: str | None) -> tuple[str, str]:
    oembed_url = url.replace("x.com", "twitter.com")
    oembed_api = f"https://publish.twitter.com/oembed?url={urllib.parse.quote(oembed_url)}&omit_script=true"
    try:
        data = json.loads(safe_fetch_text(oembed_api))
        tweet_text = re.sub(r"<[^>]+>", "", data.get("html", "")).strip()
        tweet_author = data.get("author_name", "unknown")
    except Exception:
        tweet_text = f"Tweet at {url} (could not fetch content)"
        tweet_author = "unknown"

    now = datetime.now(timezone.utc).isoformat()
    content = f"""---
source_url: "{url}"
type: tweet
author: "{tweet_author}"
captured_at: {now}
contributor: "{contributor or author or 'unknown'}"
---

# Tweet by @{tweet_author}

{tweet_text}

Source: {url}
"""
    return content, _safe_filename(url, ".md")


def _fetch_webpage(url: str, author: str | None, contributor: str | None) -> tuple[str, str]:
    html = safe_fetch_text(url)
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else url

    markdown = _html_to_markdown(html, url)
    now = datetime.now(timezone.utc).isoformat()
    content = f"""---
source_url: "{url}"
type: webpage
title: "{_yaml_str(title)}"
captured_at: {now}
contributor: "{contributor or author or 'unknown'}"
---

# {title}

Source: {url}

---

{markdown[:12000]}
"""
    return content, _safe_filename(url, ".md")


def _fetch_arxiv(url: str, author: str | None, contributor: str | None) -> tuple[str, str]:
    arxiv_id = re.search(r"(\d{4}\.\d{4,5})", url)
    if not arxiv_id:
        return _fetch_webpage(url, author, contributor)

    api_url = f"https://export.arxiv.org/abs/{arxiv_id.group(1)}"
    try:
        html = safe_fetch_text(api_url)
        abstract_match = re.search(
            r'class="abstract[^"]*"[^>]*>(.*?)</blockquote>', html, re.DOTALL | re.IGNORECASE
        )
        abstract = re.sub(r"<[^>]+>", "", abstract_match.group(1)).strip() if abstract_match else ""
        title_match = re.search(
            r'class="title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE
        )
        title = re.sub(r"<[^>]+>", " ", title_match.group(1)).strip() if title_match else arxiv_id.group(1)
        authors_match = re.search(
            r'class="authors"[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE
        )
        paper_authors = re.sub(r"<[^>]+>", "", authors_match.group(1)).strip() if authors_match else ""
    except Exception:
        title, abstract, paper_authors = arxiv_id.group(1), "", ""

    now = datetime.now(timezone.utc).isoformat()
    aid = arxiv_id.group(1)
    content = f"""---
source_url: "{url}"
arxiv_id: "{aid}"
type: paper
title: "{_yaml_str(title)}"
paper_authors: "{_yaml_str(paper_authors)}"
captured_at: {now}
contributor: "{contributor or author or 'unknown'}"
---

# {title}

**Authors:** {paper_authors}
**arXiv:** {aid}

## Abstract

{abstract}

Source: {url}
"""
    return content, f"arxiv_{aid.replace('.', '_')}.md"


def _check_duplicate_url(raw_dir: Path, url: str) -> Path | None:
    """Check if a URL was already ingested. Returns existing file path or None."""
    for md_file in raw_dir.rglob("*.md"):
        try:
            head = md_file.read_text(errors="ignore")[:500]
            if f'source_url: "{url}"' in head or f"source_url: {url}" in head:
                return md_file
        except Exception:
            continue
    return None


def ingest(
    source: str,
    raw_dir: Path,
    author: str | None = None,
    contributor: str | None = None,
    source_type: str | None = None,
    force: bool = False,
) -> Path:
    """Ingest a source into raw_dir.

    source can be:
      - A URL (http/https)
      - A local file path
      - "-" for stdin

    Returns the path of the saved file.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Stdin
    if source == "-":
        text = sys.stdin.read()
        now = datetime.now(timezone.utc)
        slug = re.sub(r"[^\w]", "_", text[:50].lower()).strip("_") or "stdin"
        filename = f"note_{now.strftime('%Y%m%d_%H%M%S')}_{slug}.md"
        content = f"""---
type: note
title: "Note {now.strftime('%Y-%m-%d %H:%M')}"
captured_at: {now.isoformat()}
contributor: "{contributor or author or 'unknown'}"
---

{text}
"""
        out_path = raw_dir / filename
        out_path.write_text(content, encoding="utf-8")
        return out_path

    # URL
    if source.startswith("http://") or source.startswith("https://"):
        # Dedup check
        if not force:
            existing = _check_duplicate_url(raw_dir, source)
            if existing:
                print(f"Already ingested: {existing} (use --force to re-fetch)")
                return existing

        try:
            validate_url(source)
        except ValueError as exc:
            raise ValueError(f"ingest: {exc}") from exc

        url_type = source_type or _detect_url_type(source)

        try:
            if url_type == "pdf":
                filename = _safe_filename(source, ".pdf")
                out = raw_dir / filename
                out.write_bytes(safe_fetch(source))
                print(f"Downloaded PDF: {out.name}")
                return out

            if url_type == "image":
                suffix = Path(urllib.parse.urlparse(source).path).suffix or ".jpg"
                filename = _safe_filename(source, suffix)
                out = raw_dir / filename
                out.write_bytes(safe_fetch(source))
                # Create sidecar .md
                sidecar = out.parent / (out.name + ".md")
                sidecar.write_text(f"""---
source_file: {out.name}
type: image
captured_at: {datetime.now(timezone.utc).isoformat()}
contributor: "{contributor or author or 'unknown'}"
---

Image: {out.name}
""")
                print(f"Downloaded image: {out.name}")
                return out

            if url_type == "tweet":
                content, filename = _fetch_tweet(source, author, contributor)
            elif url_type == "arxiv":
                content, filename = _fetch_arxiv(source, author, contributor)
            else:
                content, filename = _fetch_webpage(source, author, contributor)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
            raise RuntimeError(f"ingest: failed to fetch {source!r}: {exc}") from exc

        out_path = raw_dir / filename
        counter = 1
        while out_path.exists():
            stem = Path(filename).stem
            out_path = raw_dir / f"{stem}_{counter}.md"
            counter += 1

        out_path.write_text(content, encoding="utf-8")
        print(f"Saved {url_type}: {out_path.name}")
        return out_path

    # Local file
    local_path = Path(source).expanduser()
    if not local_path.exists():
        raise FileNotFoundError(f"ingest: file not found: {source}")

    dest = raw_dir / local_path.name
    counter = 1
    while dest.exists():
        stem = local_path.stem
        suffix = local_path.suffix
        dest = raw_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    if local_path.suffix.lower() in (".md", ".txt", ".rst"):
        # Check if file already has frontmatter
        text = local_path.read_text(errors="ignore")
        if not text.startswith("---"):
            now = datetime.now(timezone.utc).isoformat()
            text = f"""---
type: note
title: "{_yaml_str(local_path.stem)}"
source_path: "{local_path}"
captured_at: {now}
contributor: "{contributor or author or 'unknown'}"
---

{text}"""
        dest.write_text(text, encoding="utf-8")
    else:
        shutil.copy2(local_path, dest)
        # Create sidecar for images
        if local_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
            sidecar = dest.parent / (dest.name + ".md")
            sidecar.write_text(f"""---
source_file: {dest.name}
type: image
captured_at: {datetime.now(timezone.utc).isoformat()}
contributor: "{contributor or author or 'unknown'}"
---

Image: {dest.name}
""")

    print(f"Ingested: {dest.name}")
    return dest


def ingest_batch(batch_file: Path, raw_dir: Path, **kwargs) -> list[Path]:
    """Ingest all sources listed in batch_file (one per line)."""
    results = []
    for line in batch_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            results.append(ingest(line, raw_dir, **kwargs))
        except Exception as exc:
            print(f"Failed: {line} — {exc}")
    return results
