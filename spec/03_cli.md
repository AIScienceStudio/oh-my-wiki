# 03 — CLI Interface

## Binary Name

```
omw
```

Short, memorable, no conflict with common tools. "oh-my-wiki" is the project name; `omw` is the CLI (same pattern as graphify → `graphify`).

## Commands

### `omw init [directory]`

Initialize a new wiki workspace.

```bash
omw init                    # Initialize in current directory
omw init ~/my-knowledge     # Initialize in specific directory
```

Creates:
```
<directory>/
  raw/                      # Empty, ready for data
  wiki/                     # Empty, will be populated by compile
  .omw/
    cache/
    manifest.json           # Empty manifest
  .gitignore                # Ignores .omw/cache/
```

If `raw/` already exists with files, prints: "Found N files in raw/. Run `omw compile` to build your wiki."

### `omw ingest <source> [options]`

Add a source to `raw/`.

```bash
# URLs
omw ingest https://x.com/karpathy/status/1234567890
omw ingest https://arxiv.org/abs/1706.03762
omw ingest https://example.com/article
omw ingest https://youtube.com/watch?v=abc123

# Local files
omw ingest ~/notes/meeting.md
omw ingest ~/screenshots/whiteboard.png
omw ingest paper.pdf

# Stdin
echo "Quick thought about transformers" | omw ingest -

# Batch
omw ingest --batch urls.txt              # One URL/path per line

# Options
omw ingest <source> --type tweet         # Override auto-detection
omw ingest <source> --author "Karpathy"  # Tag the original author
omw ingest <source> --contributor "me"   # Tag who added it
omw ingest <source> --category research  # Pre-assign category hint
```

Output:
```
Saved tweet: raw/x_com_karpathy_status_1234567890.md
```

### `omw compile [options]`

Compile or update the wiki from raw data.

```bash
omw compile                              # Incremental (default)
omw compile --full                       # Full rebuild (re-extract everything)
omw compile --article "Transformer Architecture"  # Force recompile specific article
omw compile --dry-run                    # Show plan without executing
omw compile --mode deep                  # More aggressive entity/topic extraction
```

Output (incremental):
```
Detecting changes... 3 new files, 1 modified, 0 deleted

Extracting:
  raw/papers/new-paper.pdf .............. done (cached: 0, extracted: 1)
  raw/articles/new-post.md .............. done
  raw/notes/meeting-notes.md ............ done

Planning:
  Create: "Diffusion Models" (from new-paper.pdf)
  Update: "Machine Learning" (new info from new-post.md)
  Update: "Team Meetings" (new meeting notes)
  Stub: "Score Matching" (linked from Diffusion Models)

Compiling:
  Writing "Diffusion Models" ............ done (1,340 words)
  Updating "Machine Learning" ........... done (+280 words)
  Updating "Team Meetings" .............. done (+150 words)
  Stub "Score Matching" ................. done

Indexing:
  index.md rebuilt (48 articles)
  _categories/research.md updated
  _categories/projects.md unchanged

Done. 1 created, 2 updated, 1 stub, 44 unchanged.
```

### `omw query "<question>" [options]`

Ask a question against the wiki.

```bash
omw query "Who are my closest ML collaborators?"
omw query "What's the connection between attention and optimization?"
omw query "Summarize my startup journey" --file-back
omw query "What should I read next?" --budget 5   # Max 5 articles to read
```

Output:
```
Scanning index.md... 4 candidate articles found.
Reading: People, Machine Learning, My Startup, Research Collaborations

Answer:
Based on your wiki, your closest ML collaborators are...
[detailed answer citing specific articles]

Sources consulted:
  - [[People]] (23 entries)
  - [[Machine Learning]] (backlinked to 12 articles)
  - [[Research Collaborations]] (direct match)
```

With `--file-back`:
```
Answer filed as: wiki/_queries/20240320_who_are_my_closest_ml_collaborators.md
Updated: [[People]] (added query cross-reference)
Updated: [[Machine Learning]] (added query cross-reference)
```

### `omw lint [options]`

Run health checks on the wiki.

```bash
omw lint                                 # Report issues
omw lint --fix                           # Auto-fix what's fixable
omw lint --check broken-links            # Run specific check only
omw lint --json                          # Machine-readable output
```

Output:
```
Wiki Health Check: 48 articles, 32,400 words

Errors (3):
  ✗ Broken link: [[Score Matching]] in "Diffusion Models" → no such article
  ✗ Missing frontmatter: "old-notes.md" lacks 'confidence' field
  ✗ Index drift: index.md lists 47 articles but wiki/ has 48

Warnings (5):
  ⚠ Orphan: "Random Thought 2024-01" has 0 backlinks
  ⚠ Stale: "ML Research" source modified 2024-03-18, article compiled 2024-03-01
  ⚠ Oversized: "My Startup" is 4,200 words (threshold: 3,000)
  ⚠ Duplicate?: "Neural Networks" and "Deep Learning" have 80% tag overlap
  ⚠ Low confidence: 5 articles in "research" category have confidence: low

Info (2):
  ℹ Circular-only: "Alice" ↔ "Bob" linked to each other but no other connections
  ℹ Empty category: "_categories/places.md" has 0 articles

Auto-fixable: 3 issues (run with --fix)
```

### `omw status`

Show wiki statistics.

```bash
omw status
```

Output:
```
oh-my-wiki: ~/my-knowledge

Raw:   52 files (18 notes, 12 articles, 8 papers, 7 images, 4 tweets, 3 other)
Wiki:  48 articles, 32,400 words, 8 categories
       Last compiled: 2024-03-20 14:22 UTC (incremental)
       3 stubs, 2 stale, 1 orphan
Cache: 49 extractions cached (94% hit rate)
Health: 3 errors, 5 warnings (run `omw lint` for details)
```

### `omw watch`

Watch `raw/` for changes and auto-compile incrementally.

```bash
omw watch                                # Watch and auto-compile
omw watch --notify                       # Desktop notification on compile
```

### `omw install [options]`

Install as a skill for AI coding assistants.

```bash
omw install                              # Claude Code (default)
omw install --platform codex             # Codex
omw install --platform opencode          # OpenCode
omw install --platform claw              # OpenClaw / ClawPy

# Also:
omw claude install                       # Write CLAUDE.md section + PreToolUse hook
omw claude uninstall
omw codex install                        # Write AGENTS.md section
omw codex uninstall
```

### `omw report`

Generate or view the WIKI_REPORT.md.

```bash
omw report                               # Generate and print WIKI_REPORT.md
omw report --refresh                     # Force regenerate
```

### `omw diff`

Show what changed since last compile.

```bash
omw diff                                 # Show pending changes (raw/ vs manifest)
omw diff --last                          # Show what last compile changed
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | No raw files found |
| 4 | Lint errors found (with --strict) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OMW_RAW_DIR` | `./raw` | Raw data directory |
| `OMW_WIKI_DIR` | `./wiki` | Wiki output directory |
| `OMW_STATE_DIR` | `./.omw` | Internal state directory |
| `OMW_MAX_ARTICLE_WORDS` | `3000` | Warn threshold for oversized articles |
| `OMW_COMPILE_PARALLELISM` | `5` | Max parallel subagents for compilation |
