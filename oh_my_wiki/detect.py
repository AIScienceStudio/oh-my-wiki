"""File discovery, type classification, and corpus stats."""
from __future__ import annotations

import json
import os
import re
from enum import Enum
from pathlib import Path


class FileType(str, Enum):
    NOTE = "note"
    PAPER = "paper"
    IMAGE = "image"
    DATA = "data"


NOTE_EXTENSIONS = {".md", ".txt", ".rst"}
PAPER_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
DATA_EXTENSIONS = {".csv", ".json", ".jsonl"}

CORPUS_WARN_THRESHOLD = 500_000   # words — above this, warn about token cost
FILE_COUNT_UPPER = 200

# Files that may contain secrets — skip silently
_SENSITIVE_PATTERNS = [
    re.compile(r"(^|[\\/])\.(env|envrc)(\.|$)", re.IGNORECASE),
    re.compile(r"\.(pem|key|p12|pfx|cert|crt|der|p8)$", re.IGNORECASE),
    re.compile(r"(credential|secret|passwd|password|token|private_key)", re.IGNORECASE),
    re.compile(r"(id_rsa|id_dsa|id_ecdsa|id_ed25519)(\.pub)?$"),
    re.compile(r"(\.netrc|\.pgpass|\.htpasswd)$", re.IGNORECASE),
]

# Signals that a .md/.txt file is a converted academic paper
_PAPER_SIGNALS = [
    re.compile(r"\barxiv\b", re.IGNORECASE),
    re.compile(r"\bdoi\s*:", re.IGNORECASE),
    re.compile(r"\babstract\b", re.IGNORECASE),
    re.compile(r"\bproceedings\b", re.IGNORECASE),
    re.compile(r"\bjournal\b", re.IGNORECASE),
    re.compile(r"\bpreprint\b", re.IGNORECASE),
    re.compile(r"\\cite\{"),
    re.compile(r"\[\d+\]"),
    re.compile(r"\d{4}\.\d{4,5}"),
    re.compile(r"\bwe propose\b", re.IGNORECASE),
]
_PAPER_SIGNAL_THRESHOLD = 3

_SKIP_DIRS = {
    "venv", ".venv", "env", ".env",
    "node_modules", "__pycache__", ".git",
    "dist", "build", "target", "out",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".omw", "wiki",  # Don't scan our own output
}


def _is_sensitive(path: Path) -> bool:
    name = path.name
    full = str(path)
    return any(p.search(name) or p.search(full) for p in _SENSITIVE_PATTERNS)


def _looks_like_paper(path: Path) -> bool:
    try:
        text = path.read_text(errors="ignore")[:3000]
        hits = sum(1 for pattern in _PAPER_SIGNALS if pattern.search(text))
        return hits >= _PAPER_SIGNAL_THRESHOLD
    except Exception:
        return False


def classify_file(path: Path) -> FileType | None:
    ext = path.suffix.lower()
    if ext in PAPER_EXTENSIONS:
        return FileType.PAPER
    if ext in IMAGE_EXTENSIONS:
        return FileType.IMAGE
    if ext in DATA_EXTENSIONS:
        return FileType.DATA
    if ext in NOTE_EXTENSIONS:
        if _looks_like_paper(path):
            return FileType.PAPER
        return FileType.NOTE
    return None


def extract_pdf_text(path: Path) -> str:
    """Extract plain text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def count_words(path: Path) -> int:
    try:
        if path.suffix.lower() == ".pdf":
            return len(extract_pdf_text(path).split())
        return len(path.read_text(errors="ignore").split())
    except Exception:
        return 0


def detect(raw_dir: Path) -> dict:
    """Scan raw_dir recursively and classify all files.

    Returns {files: {type: [paths]}, total_files, total_words, warning, skipped_sensitive}.
    """
    files: dict[str, list[str]] = {t.value: [] for t in FileType}
    total_words = 0
    skipped_sensitive: list[str] = []

    for dirpath, dirnames, filenames in os.walk(raw_dir, followlinks=False):
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d not in _SKIP_DIRS
        ]
        for fname in filenames:
            if fname.startswith("."):
                continue
            p = Path(dirpath) / fname
            if _is_sensitive(p):
                skipped_sensitive.append(str(p))
                continue
            ftype = classify_file(p)
            if ftype:
                files[ftype.value].append(str(p))
                total_words += count_words(p)

    total_files = sum(len(v) for v in files.values())

    warning: str | None = None
    if total_files == 0:
        warning = "No supported files found."
    elif total_words >= CORPUS_WARN_THRESHOLD or total_files >= FILE_COUNT_UPPER:
        warning = (
            f"Large corpus: {total_files} files, ~{total_words:,} words. "
            f"Compilation will be expensive."
        )

    return {
        "files": files,
        "total_files": total_files,
        "total_words": total_words,
        "warning": warning,
        "skipped_sensitive": skipped_sensitive,
    }


# ---------------------------------------------------------------------------
# Incremental detection
# ---------------------------------------------------------------------------

_MANIFEST_PATH = ".omw/manifest.json"


def load_manifest(manifest_path: str = _MANIFEST_PATH) -> dict:
    """Load the manifest from a previous run."""
    try:
        return json.loads(Path(manifest_path).read_text())
    except Exception:
        return {}


def save_manifest(manifest: dict, manifest_path: str = _MANIFEST_PATH) -> None:
    """Save manifest to disk."""
    p = Path(manifest_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(manifest, indent=2))


def detect_incremental(raw_dir: Path, manifest_path: str = _MANIFEST_PATH) -> dict:
    """Detect only new or modified files since the last run.

    Compares current file mtimes against the stored manifest.
    """
    full = detect(raw_dir)
    manifest = load_manifest(manifest_path)
    raw_files = manifest.get("raw_files", {})

    if not raw_files:
        full["incremental"] = True
        full["new_files"] = full["files"]
        full["unchanged_files"] = {k: [] for k in full["files"]}
        full["deleted_files"] = []
        return full

    # Build hash → path lookup from old manifest
    old_paths: dict[str, float] = {}
    for _hash, info in raw_files.items():
        old_paths[info.get("path", "")] = info.get("mtime", 0)

    new_files: dict[str, list[str]] = {k: [] for k in full["files"]}
    unchanged_files: dict[str, list[str]] = {k: [] for k in full["files"]}

    for ftype, file_list in full["files"].items():
        for f in file_list:
            stored_mtime = old_paths.get(f)
            try:
                current_mtime = Path(f).stat().st_mtime
            except Exception:
                current_mtime = 0
            if stored_mtime is None or current_mtime > stored_mtime:
                new_files[ftype].append(f)
            else:
                unchanged_files[ftype].append(f)

    # Deleted files
    current_files = {f for flist in full["files"].values() for f in flist}
    deleted_files = [
        info.get("path", "")
        for info in raw_files.values()
        if info.get("path", "") and info["path"] not in current_files
    ]

    full["incremental"] = True
    full["new_files"] = new_files
    full["unchanged_files"] = unchanged_files
    full["deleted_files"] = deleted_files
    return full
