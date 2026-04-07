# 07 — Implementation Plan

## Tech Stack

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "oh-my-wiki"
version = "0.1.0"
description = "LLM-powered personal wiki compiler — raw data in, structured knowledge base out"
readme = "README.md"
license = { file = "LICENSE" }
keywords = ["wiki", "knowledge-base", "llm", "obsidian", "personal-wiki", "claude", "claude-code", "codex"]
requires-python = ">=3.10"
dependencies = []    # Zero required deps — stdlib only

[project.optional-dependencies]
pdf = ["pypdf", "html2text"]
watch = ["watchdog"]
all = ["pypdf", "html2text", "watchdog"]

[project.scripts]
omw = "oh_my_wiki.__main__:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["oh_my_wiki*"]

[tool.setuptools.package-data]
oh_my_wiki = ["skill.md", "skill-codex.md", "skill-opencode.md", "skill-claw.md"]
```

### Why zero dependencies?

| Need | Solution |
|------|----------|
| URL fetching | `urllib.request` (same as graphify) |
| HTML → markdown | Regex fallback (30 lines), `html2text` optional |
| YAML frontmatter | Custom parser (~50 lines — frontmatter is simple, well-structured) |
| JSON | stdlib `json` |
| File hashing | `hashlib.sha256` |
| Atomic writes | `os.replace()` (same as graphify) |
| Path handling | `pathlib.Path` |
| Date/time | `datetime` stdlib |
| Regex | `re` stdlib |
| LLM calls | Host agent (Claude Code, etc.) — not our code |

## Reuse from graphify

These modules can be directly adapted from graphify with minimal changes:

| graphify Module | oh-my-wiki Module | What Changes |
|----------------|-------------------|-------------|
| `cache.py` | `cache.py` | Change directory from `graphify-out/cache/` to `.omw/cache/`. Same SHA256 + atomic write pattern. |
| `security.py` | `security.py` | Direct copy. URL validation, safe_fetch, size limits, redirect blocking. |
| `ingest.py` | `ingest.py` | Add new source types (stdin, conversation, data). Keep tweet/arxiv/webpage/pdf handlers. Change output dir to `raw/`. |
| `detect.py` | `detect.py` | Remove code-specific logic (CODE_EXTENSIONS, tree-sitter types). Add personal data types (conversation, data). Keep paper detection heuristic, sensitive file filtering, skip dirs, word counting, incremental detection. |
| `__main__.py` | `__main__.py` | Different command set but same pattern: argparse, platform dispatch, install/uninstall. |

## Modules to Write Fresh

| Module | Complexity | Key Challenges |
|--------|-----------|----------------|
| `article.py` | Medium | Frontmatter parsing without PyYAML dependency; backlink extraction regex; article validation |
| `compile.py` | High | Compilation plan schema; incremental impact analysis logic; article merge templates |
| `extract.py` | Medium | Extraction schema validation; prompt templates for different file types |
| `index.py` | Medium | Hub article ranking; category page generation; deterministic index rebuild |
| `query.py` | Low | Query preparation (candidate article ranking); file-back logic |
| `lint.py` | Medium | Structural checks (broken links, orphans, staleness); output formatting |
| `analyze.py` | Medium | WIKI_REPORT.md generation; freshness scoring; coverage gap detection |
| `diff.py` | Low | Wiki state snapshot; comparison between compiles |
| `manifest.py` | Medium | Dependency graph (raw→article, article→article); cascade detection |
| `watch.py` | Low | Adapt graphify's watchdog pattern for raw/ directory |
| `skill.md` | High | Detailed step-by-step orchestration for host LLM; prompt templates |

## Implementation Phases

### Phase 1 — Foundation (MVP)

Goal: `omw init` + `omw ingest` + `omw compile --full` + `omw status` working end-to-end.

```
1. article.py        — Frontmatter parser/renderer, Article dataclass, backlink regex
2. security.py       — Copy from graphify, adapt paths
3. cache.py          — Copy from graphify, change dir to .omw/cache/
4. ingest.py         — Adapt from graphify, add stdin/local file support
5. detect.py         — Adapt from graphify, remove code-specific, add personal data types
6. extract.py        — Extraction schema, validation, prompt templates
7. compile.py        — Full compile: plan schema, article templates, compile orchestration
8. index.py          — rebuild_index(), category page generation
9. manifest.py       — Basic raw→article tracking
10. __main__.py      — CLI: init, ingest, compile, status
11. skill.md         — Claude Code skill (compile flow)
```

Deliverable: A user can init a workspace, ingest 10-20 sources, run `/omw compile .` in Claude Code, and get a working wiki with index.md + articles + categories.

### Phase 2 — Intelligence

Goal: Incremental compile, query, lint, report.

```
1. detect.py         — Add detect_incremental() with manifest comparison
2. compile.py        — Add incremental compile with impact analysis
3. manifest.py       — Add article→article dependency tracking, cascade detection
4. query.py          — Query preparation, file-back
5. lint.py           — All structural checks + auto-fix
6. analyze.py        — WIKI_REPORT.md generation
7. diff.py           — Wiki state snapshots + changelog
8. skill.md          — Add query + lint orchestration
```

Deliverable: Incremental compilation works. Users can query the wiki and file back results. Lint catches issues.

### Phase 3 — Polish & Multi-Platform

Goal: Production-ready, multi-platform, watched.

```
1. watch.py          — Filesystem watcher for raw/ changes
2. skill-codex.md    — Codex skill
3. skill-opencode.md — OpenCode skill  
4. skill-claw.md     — OpenClaw/ClawPy skill
5. __main__.py       — Add install/uninstall for all platforms
6. Worked examples   — Real raw/ → wiki/ demonstrations
7. Tests             — Full test suite
8. README.md         — Documentation
```

### Phase 4 — Advanced (Future)

```
1. ClawPy integration  — Standalone mode without host agent
2. MCP server          — Expose wiki as MCP resource
3. Semantic lint        — LLM-powered duplicate/connection detection
4. Batch ingest        — Apple Notes, iMessage, Notion export importers
5. Search engine       — Simple web UI for wiki search (like Karpathy's vibe-coded search)
6. Marp integration    — Generate slideshows from wiki articles
7. Image generation    — matplotlib/mermaid diagrams from wiki data
```

## Testing Strategy

### Unit Tests (No LLM)

Every deterministic module gets unit tests with fixtures:

```
tests/
  fixtures/
    sample_raw/
      note.md              # Simple note with frontmatter
      tweet.md             # Ingested tweet
      paper.md             # Academic paper (.md with paper signals)
    sample_wiki/
      index.md             # Valid index
      article-a.md         # Article with backlinks
      article-b.md         # Article with backlinks
      _categories/
        research.md
    sample_extractions/
      note.json            # Extraction output
      tweet.json
  test_article.py          # Frontmatter parsing, backlink extraction, validation
  test_ingest.py           # URL classification, filename generation, frontmatter injection
  test_detect.py           # File discovery, classification, paper detection, incremental
  test_extract.py          # Schema validation
  test_compile.py          # Plan validation, article template rendering
  test_index.py            # Index generation, category pages, hub ranking
  test_lint.py             # All structural checks
  test_cache.py            # SHA256, atomic writes, cache hit/miss
  test_manifest.py         # Dependency tracking, cascade detection
```

### Integration Tests (With Mock LLM)

For compile/query/lint flows, use fixture extraction results and pre-written articles instead of calling an actual LLM.

### End-to-End Tests (Worked Examples)

The `worked/` directory contains real raw data + expected wiki output, allowing full pipeline validation.

## File Dependencies

```
article.py      → (none — foundation)
security.py     → (none)
cache.py        → (none)
ingest.py       → security.py
detect.py       → (none)
extract.py      → cache.py
compile.py      → article.py, extract.py, cache.py, manifest.py
index.py        → article.py
query.py        → article.py, index.py
lint.py         → article.py, index.py, manifest.py
analyze.py      → article.py, index.py, lint.py, manifest.py
diff.py         → article.py, manifest.py
manifest.py     → article.py
watch.py        → detect.py
__main__.py     → all modules
skill.md        → references all Python entry points
```

Build order (no circular deps): article → security, cache → ingest, detect → extract → manifest → compile, index → query, lint → analyze, diff → watch → __main__ → skill.md
