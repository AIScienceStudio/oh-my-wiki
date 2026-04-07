"""Filesystem watcher — monitor raw/ for changes and trigger incremental compile."""
from __future__ import annotations

import time
from pathlib import Path

from oh_my_wiki.detect import NOTE_EXTENSIONS, PAPER_EXTENSIONS, IMAGE_EXTENSIONS, DATA_EXTENSIONS

_WATCHED_EXTENSIONS = NOTE_EXTENSIONS | PAPER_EXTENSIONS | IMAGE_EXTENSIONS | DATA_EXTENSIONS
_SKIP_DIRS = {".omw", "wiki", ".git", "__pycache__", ".venv", "venv"}


def watch(watch_path: Path, debounce: float = 3.0) -> None:
    """Watch watch_path/raw/ for changes and notify user to recompile.

    Since all compilation requires LLM calls, the watcher only notifies —
    it doesn't auto-compile (unlike graphify which can do AST-only rebuilds).

    debounce: seconds to wait after last change before notifying.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError as e:
        raise ImportError(
            "watchdog not installed. Run: uv pip install oh-my-wiki[watch]"
        ) from e

    raw_dir = watch_path / "raw"
    if not raw_dir.exists():
        print(f"[omw watch] No raw/ directory at {watch_path}. Run `omw init` first.")
        return

    last_trigger: float = 0.0
    pending: bool = False
    changed: set[Path] = set()

    class Handler(FileSystemEventHandler):
        def on_any_event(self, event):
            nonlocal last_trigger, pending
            if event.is_directory:
                return
            path = Path(event.src_path)
            if path.suffix.lower() not in _WATCHED_EXTENSIONS:
                return
            if any(part in _SKIP_DIRS for part in path.parts):
                return
            if any(part.startswith(".") for part in path.parts):
                return
            last_trigger = time.monotonic()
            pending = True
            changed.add(path)

    handler = Handler()
    observer = Observer()
    observer.schedule(handler, str(raw_dir), recursive=True)
    observer.start()

    print(f"[omw watch] Watching {raw_dir.resolve()}")
    print(f"[omw watch] Changes will notify you to run `omw compile`")
    print(f"[omw watch] Press Ctrl+C to stop")

    # Write needs_compile flag location
    flag_path = watch_path / ".omw" / "needs_compile"

    try:
        while True:
            time.sleep(0.5)
            if pending and (time.monotonic() - last_trigger) >= debounce:
                pending = False
                batch = list(changed)
                changed.clear()

                print(f"\n[omw watch] {len(batch)} file(s) changed:")
                for p in batch[:10]:
                    print(f"  {p.name}")
                if len(batch) > 10:
                    print(f"  ... and {len(batch) - 10} more")

                # Write flag file
                flag_path.parent.mkdir(parents=True, exist_ok=True)
                flag_path.write_text(str(len(batch)))

                print(f"[omw watch] Run `omw compile` or use /omw in your agent to update the wiki.")
    except KeyboardInterrupt:
        print("\n[omw watch] Stopped.")
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Watch raw/ for changes")
    parser.add_argument("path", nargs="?", default=".", help="Project root (default: .)")
    parser.add_argument("--debounce", type=float, default=3.0)
    args = parser.parse_args()
    watch(Path(args.path), debounce=args.debounce)
