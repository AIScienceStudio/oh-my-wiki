"""CLI entry point — omw <command>."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _cmd_init(args: list[str]) -> None:
    """Initialize a new wiki workspace."""
    directory = Path(args[0]) if args else Path(".")
    directory = directory.resolve()

    raw_dir = directory / "raw"
    wiki_dir = directory / "wiki"
    omw_dir = directory / ".omw"

    raw_dir.mkdir(parents=True, exist_ok=True)
    wiki_dir.mkdir(parents=True, exist_ok=True)
    omw_dir.mkdir(parents=True, exist_ok=True)
    (omw_dir / "cache").mkdir(exist_ok=True)

    # Create .gitignore if it doesn't exist
    gitignore = directory / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(".omw/cache/\n.omw/wiki-snapshot.json\n")

    # Initialize empty manifest
    from oh_my_wiki.manifest import save, _empty_manifest
    manifest_path = omw_dir / "manifest.json"
    if not manifest_path.exists():
        save(_empty_manifest(), directory)

    # Check for existing raw files
    from oh_my_wiki.detect import detect
    result = detect(raw_dir)
    total = result["total_files"]

    print(f"Initialized oh-my-wiki workspace at {directory}")
    print(f"  raw/   — add your source data here")
    print(f"  wiki/  — compiled wiki output")
    print(f"  .omw/  — internal state (cache, manifest)")
    if total > 0:
        print(f"\nFound {total} files in raw/. Run `omw compile` to build your wiki.")


def _cmd_ingest(args: list[str]) -> None:
    """Ingest a source into raw/."""
    if not args:
        print("Usage: omw ingest <source> [--type TYPE] [--author NAME] [--contributor NAME]", file=sys.stderr)
        sys.exit(2)

    source = args[0]
    author = None
    contributor = None
    source_type = None
    force = False
    batch_file = None
    i = 1

    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            source_type = args[i + 1]
            i += 2
        elif args[i] == "--author" and i + 1 < len(args):
            author = args[i + 1]
            i += 2
        elif args[i] == "--contributor" and i + 1 < len(args):
            contributor = args[i + 1]
            i += 2
        elif args[i] == "--force":
            force = True
            i += 1
        elif args[i] == "--batch":
            batch_file = Path(args[0])
            i += 1
        else:
            i += 1

    raw_dir = Path("raw")

    from oh_my_wiki.ingest import ingest, ingest_batch

    if batch_file:
        results = ingest_batch(batch_file, raw_dir, author=author, contributor=contributor)
        print(f"\nIngested {len(results)} sources.")
    else:
        ingest(
            source, raw_dir,
            author=author,
            contributor=contributor,
            source_type=source_type,
            force=force,
        )


def _cmd_compile(args: list[str]) -> None:
    """Compile the wiki from raw data.

    In skill mode (default), this prints instructions for the host LLM.
    In standalone mode (--engine clawpy), it runs compilation directly.
    """
    full = "--full" in args
    dry_run = "--dry-run" in args

    raw_dir = Path("raw")
    wiki_dir = Path("wiki")

    if not raw_dir.exists():
        print("No raw/ directory found. Run `omw init` first.", file=sys.stderr)
        sys.exit(1)

    from oh_my_wiki.detect import detect, detect_incremental

    if full:
        result = detect(raw_dir)
    else:
        result = detect_incremental(raw_dir)

    total = result["total_files"]
    if total == 0:
        print("No files found in raw/. Add sources with `omw ingest`.", file=sys.stderr)
        sys.exit(3)

    # Print corpus summary
    files = result["files"]
    print(f"Corpus: {total} files · ~{result['total_words']:,} words")
    for ftype, flist in files.items():
        if flist:
            print(f"  {ftype:10s} {len(flist)} files")

    if result.get("warning"):
        print(f"\nWarning: {result['warning']}")

    if result.get("incremental"):
        new_count = sum(len(v) for v in result.get("new_files", {}).values())
        deleted = result.get("deleted_files", [])
        if new_count == 0 and not deleted:
            print("\nWiki is up to date. No changes detected.")
            return
        print(f"\nChanges: {new_count} new/modified, {len(deleted)} deleted")

    if dry_run:
        print("\n(dry run — no compilation performed)")
        return

    # In skill mode, print what the host agent should do
    print(f"\nReady for compilation. Use the /omw skill in your AI agent,")
    print(f"or run `omw compile --engine clawpy` for standalone mode.")


def _cmd_status(args: list[str]) -> None:
    """Show wiki status."""
    raw_dir = Path("raw")
    wiki_dir = Path("wiki")

    print("oh-my-wiki:", Path(".").resolve())
    print()

    # Raw stats
    if raw_dir.exists():
        from oh_my_wiki.detect import detect
        result = detect(raw_dir)
        files = result["files"]
        parts = [f"{len(v)} {k}" for k, v in files.items() if v]
        print(f"Raw:   {result['total_files']} files ({', '.join(parts)})")
    else:
        print("Raw:   (no raw/ directory — run `omw init`)")

    # Wiki stats
    if wiki_dir.exists():
        from oh_my_wiki.index import wiki_status
        status = wiki_status(wiki_dir)
        if status["exists"] and status["total_articles"] > 0:
            print(f"Wiki:  {status['total_articles']} articles, {status['total_words']:,} words, {len(status['categories'])} categories")
            extras = []
            if status["stubs"]:
                extras.append(f"{status['stubs']} stubs")
            if status["stale"]:
                extras.append(f"{status['stale']} stale")
            if extras:
                print(f"       {', '.join(extras)}")
        else:
            print("Wiki:  (empty — run `omw compile`)")
    else:
        print("Wiki:  (no wiki/ directory — run `omw compile`)")

    # Cache stats
    cache_dir = Path(".omw/cache")
    if cache_dir.exists():
        cache_count = len(list(cache_dir.glob("*.json")))
        print(f"Cache: {cache_count} extractions cached")

    # Compile log
    from oh_my_wiki.compile import load_compile_log
    log = load_compile_log()
    if log:
        print(f"Last:  {log.get('mode', 'unknown')} compile at {log.get('timestamp', 'unknown')[:19]}")


def _cmd_lint(args: list[str]) -> None:
    """Run health checks (placeholder — full implementation in Phase 2)."""
    wiki_dir = Path("wiki")
    if not wiki_dir.exists():
        print("No wiki/ directory found.", file=sys.stderr)
        sys.exit(1)

    from oh_my_wiki.article import list_articles, extract_wikilinks, compute_backlink_counts

    articles = list_articles(wiki_dir)
    if not articles:
        print("Wiki is empty.")
        return

    # Collect all known titles + aliases
    known_titles: set[str] = set()
    for a in articles:
        known_titles.add(a.title)
        for alias in a.aliases:
            known_titles.add(alias)

    errors = 0
    warnings = 0

    # Check broken links
    for a in articles:
        links = extract_wikilinks(a.body)
        for link in links:
            if link not in known_titles and not link.startswith("_categories/"):
                print(f"  ERROR  Broken link: [[{link}]] in \"{a.title}\"")
                errors += 1

    # Check orphans
    backlinks = compute_backlink_counts(wiki_dir)
    for a in articles:
        if backlinks.get(a.title, 0) == 0 and a.status != "stub":
            print(f"  WARN   Orphan: \"{a.title}\" has 0 backlinks")
            warnings += 1

    # Check missing frontmatter
    for a in articles:
        if not a.confidence:
            print(f"  ERROR  Missing confidence: \"{a.title}\"")
            errors += 1

    # Check oversized
    for a in articles:
        wc = a.word_count or len(a.body.split())
        if wc > 3000:
            print(f"  WARN   Oversized: \"{a.title}\" is {wc:,} words")
            warnings += 1

    print(f"\n{len(articles)} articles: {errors} errors, {warnings} warnings")


def _print_help() -> None:
    print("oh-my-wiki — LLM-powered personal wiki compiler")
    print()
    print("Usage: omw <command> [options]")
    print()
    print("Commands:")
    print("  init [directory]         Initialize a new wiki workspace")
    print("  ingest <source>          Add a source to raw/ (URL, file, or - for stdin)")
    print("  compile [--full]         Compile/update wiki from raw/")
    print("  status                   Show wiki stats")
    print("  lint                     Run health checks")
    print("  help                     Show this help")
    print()
    print("Examples:")
    print("  omw init ~/my-knowledge")
    print("  omw ingest https://example.com/article")
    print("  omw ingest ~/notes/meeting.md")
    print("  echo 'Quick thought' | omw ingest -")
    print("  omw compile --full")
    print()


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        _print_help()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "init": _cmd_init,
        "ingest": _cmd_ingest,
        "compile": _cmd_compile,
        "status": _cmd_status,
        "lint": _cmd_lint,
    }

    handler = commands.get(cmd)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Run 'omw help' for usage.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
