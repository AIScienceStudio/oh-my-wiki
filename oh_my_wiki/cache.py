"""Per-file extraction cache — skip unchanged files on re-run."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def file_hash(path: Path) -> str:
    """SHA256 of file contents + resolved path. Prevents cache collisions on identical content."""
    p = Path(path)
    h = hashlib.sha256()
    h.update(p.read_bytes())
    h.update(b"\x00")
    h.update(str(p.resolve()).encode())
    return h.hexdigest()


def content_hash(data: bytes) -> str:
    """SHA256 of raw content bytes."""
    return hashlib.sha256(data).hexdigest()


def cache_dir(root: Path = Path(".")) -> Path:
    """Returns .omw/cache/ — creates it if needed."""
    d = Path(root) / ".omw" / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_cached(path: Path, root: Path = Path(".")) -> dict | None:
    """Return cached extraction for this file if hash matches, else None."""
    try:
        h = file_hash(path)
    except OSError:
        return None
    entry = cache_dir(root) / f"{h}.json"
    if not entry.exists():
        return None
    try:
        return json.loads(entry.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def save_cached(path: Path, result: dict, root: Path = Path(".")) -> None:
    """Save extraction result for this file. Atomic write via tmp + os.replace."""
    h = file_hash(path)
    entry = cache_dir(root) / f"{h}.json"
    tmp = entry.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(result))
        os.replace(tmp, entry)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def clear_cache(root: Path = Path(".")) -> int:
    """Delete all .omw/cache/*.json files. Returns count deleted."""
    d = cache_dir(root)
    count = 0
    for f in d.glob("*.json"):
        f.unlink()
        count += 1
    return count


def check_cache(
    files: list[str],
    root: Path = Path("."),
) -> tuple[list[dict], list[str]]:
    """Check extraction cache for a list of file paths.

    Returns (cached_extractions, uncached_file_paths).
    """
    cached: list[dict] = []
    uncached: list[str] = []

    for fpath in files:
        result = load_cached(Path(fpath), root)
        if result is not None:
            cached.append(result)
        else:
            uncached.append(fpath)

    return cached, uncached
