# 01 — Architecture

## Pipeline

```
ingest  →  detect  →  extract  →  compile  →  index  →  wiki/
  │           │          │           │           │         │
  ▼           ▼          ▼           ▼           ▼         ▼
raw/       stats      topics    articles    index.md    ready
           cache     entities   backlinks   categories
                    summaries   sources     hub articles
                                            ┌──────────────┐
                                            │ query → answer│
                                            │   ↓           │
                                            │ file-back     │
                                            │   ↓           │
                                            │ wiki grows    │
                                            ├──────────────┤
                                            │ lint → report │
                                            │   ↓           │
                                            │ fix → wiki    │
                                            │   heals       │
                                            └──────────────┘
```

Key difference from graphify: oh-my-wiki has an **extract** step (entities/topics from raw files) that feeds into a **compile** step (plan + write articles). graphify merges extract + build into a graph; oh-my-wiki keeps extraction and article writing as separate concerns.

## Module Map

| Module | Entry Function | In → Out |
|--------|---------------|----------|
| `ingest.py` | `ingest(source, raw_dir)` | URL/file/text → saved .md in `raw/` with YAML frontmatter |
| `detect.py` | `detect(raw_dir)` | directory → `{files, types, total_words, warning}` |
| `detect.py` | `detect_incremental(raw_dir)` | directory + manifest → `{new_files, unchanged, deleted}` |
| `extract.py` | `extract(raw_file)` | raw file → `{topics, entities, summary, suggested_titles}` |
| `compile.py` | `plan(extractions, wiki_dir)` | all extractions + current index → compilation plan |
| `compile.py` | `write_article(plan_entry, raw_sources)` | plan + sources → article markdown string |
| `compile.py` | `update_article(existing, new_sources)` | existing article + new data → merged article |
| `index.py` | `rebuild_index(wiki_dir)` | wiki directory → `index.md` + category pages |
| `index.py` | `compute_hub_articles(wiki_dir)` | wiki directory → ranked list by backlink count |
| `query.py` | `prepare_query(question, wiki_dir)` | question → candidate article paths to read |
| `query.py` | `file_back(question, answer, wiki_dir)` | Q&A → saved query article + updated source articles |
| `lint.py` | `lint(wiki_dir)` | wiki directory → `{errors, warnings, info, fixable}` |
| `lint.py` | `fix(wiki_dir, issues)` | issues list → auto-fixed wiki |
| `analyze.py` | `analyze(wiki_dir)` | wiki directory → `WIKI_REPORT.md` (health, hubs, gaps, freshness) |

### Supporting Modules

| Module | Purpose | Based On |
|--------|---------|----------|
| `article.py` | Article data model: parse/render frontmatter, extract backlinks, compute metrics | New |
| `cache.py` | SHA256-based extraction cache, atomic writes | graphify `cache.py` |
| `security.py` | URL validation, safe fetch, size limits, redirect blocking | graphify `security.py` |
| `manifest.py` | Track raw→article mapping + article→article dependencies | graphify `manifest.py` + extensions |
| `watch.py` | Filesystem watcher for raw/ changes, triggers incremental compile | graphify `watch.py` |
| `diff.py` | Compare wiki states between compiles, generate changelog | graphify `analyze.graph_diff` |
| `__main__.py` | CLI entry point: `omw <command>` | graphify `__main__.py` |
| `skill.md` | Claude Code skill definition — LLM orchestration instructions | graphify `skill.md` |

## Directory Layout

### Package Structure

```
oh-my-wiki/
  oh_my_wiki/
    __init__.py
    __main__.py          # CLI: omw <command>
    article.py           # Article model (parse/render frontmatter + body + backlinks)
    ingest.py            # Source ingestion (URL, file, stdin)
    detect.py            # File discovery, classification, word counting
    extract.py           # Topic/entity extraction helpers (templates for LLM)
    compile.py           # Compilation plan + article writing/merging
    index.py             # index.md, category pages, hub article ranking
    query.py             # Query routing + file-back
    lint.py              # Health checks
    analyze.py           # Wiki-wide analysis → WIKI_REPORT.md
    diff.py              # Wiki state comparison + changelog
    cache.py             # SHA256 extraction cache
    manifest.py          # raw→article + article→article dependency tracking
    security.py          # URL validation, safe fetch
    watch.py             # Filesystem watcher
    skill.md             # Claude Code skill
    skill-codex.md       # Codex skill
    skill-opencode.md    # OpenCode skill
    skill-claw.md        # OpenClaw/ClawPy skill
  tests/
    fixtures/
      sample_raw/        # Example raw files for testing
      sample_wiki/       # Expected wiki output for testing
    test_article.py
    test_ingest.py
    test_detect.py
    test_extract.py
    test_compile.py
    test_index.py
    test_query.py
    test_lint.py
    test_analyze.py
    test_cache.py
  worked/                # Real worked examples (like graphify's worked/)
    personal-notes/
      raw/
      wiki/
  pyproject.toml
  README.md
  ARCHITECTURE.md
  LICENSE
```

### Runtime Directory Layout

```
my-knowledge/                   # User's project root
  raw/                          # Raw data (user-managed input)
    notes/
      2024-01-meeting.md
      startup-idea.md
    articles/
      karpathy-llm-kb.md
      farzapedia.md
    papers/
      attention-is-all-you-need.pdf
    media/
      screenshot-2024-03-20.png
      inspiration-board.jpg
    diary/
      2024-01.md
      2024-02.md
  wiki/                         # Compiled wiki (LLM-maintained, user reads)
    index.md                    # Master catalog — agent entry point
    WIKI_REPORT.md              # Auto-generated health report
    _categories/                # Category index pages
      people.md
      projects.md
      research.md
      media.md
      personal.md
    _queries/                   # Filed-back query results
      20240320_how_does_attention_work.md
    transformer-architecture.md # Regular article
    andrej-karpathy.md
    my-startup.md
    studio-ghibli.md
    ...
  .omw/                         # oh-my-wiki internal state (gitignored)
    cache/                      # SHA256-keyed extraction cache
      {hash}.json               # Cached extraction per raw file
    manifest.json               # raw file hash → [article titles] + article → [backlink targets]
    compile-log.json            # Last compile: what changed, what was created/updated/deleted
    wiki-snapshot.json          # Serialized wiki state for diff computation
```

## Data Flow: Full Compile

```
1. User: omw compile --full
2. detect(raw/) → {files by type, total_words, warnings}
3. For each raw file (parallelizable via subagents):
   a. Check cache: file_hash(path) → cached extraction?
   b. If cache miss: LLM extracts {topics, entities, summary, suggested_titles}
   c. Save to cache
4. plan(all_extractions, wiki/) → [{title, sources, category, outline, action: create|update}]
5. For each planned article (parallelizable):
   a. If create: LLM writes article from raw sources + plan outline
   b. If update: LLM merges existing article + new sources
6. rebuild_index(wiki/) → index.md + category pages (deterministic)
7. analyze(wiki/) → WIKI_REPORT.md
8. Save manifest + compile-log + wiki-snapshot
```

## Data Flow: Incremental Compile

```
1. User: omw compile (default is incremental)
2. detect_incremental(raw/) → {new_files, modified_files, deleted_files, unchanged}
3. If no changes: "Wiki is up to date." → done
4. For each new/modified raw file:
   a. Extract {topics, entities, summary, suggested_titles} (cache miss)
5. Impact analysis (LLM):
   a. Read current index.md (catalog of all existing articles)
   b. For each new extraction, decide:
      - Create new article? (topic not covered)
      - Update existing article(s)? (new info for existing topic)
      - No action? (redundant info)
6. Execute plan:
   a. Write new articles
   b. Update affected articles (LLM reads existing + new source → merged)
   c. Handle deletions: if raw file removed, mark affected articles as "source removed"
7. Cascade: new [[wikilinks]] pointing to non-existent articles → create stubs
8. rebuild_index(wiki/)
9. analyze(wiki/) → WIKI_REPORT.md
10. Update manifest + compile-log
```

## Data Flow: Query

```
1. User: omw query "Who are my closest collaborators on ML research?"
2. prepare_query(question, wiki/) →
   a. LLM parses question → key topics: [collaborators, ML, research]
   b. Read index.md → find candidate articles by title/category/descriptor
   c. Return ranked list of article paths to read
3. Host agent reads 2-5 articles, follows backlinks as needed
4. Synthesizes answer citing specific articles
5. If --file-back: file_back(question, answer, wiki/) →
   a. Save as wiki/_queries/YYYYMMDD_slug.md
   b. Update source articles' Notes section with cross-reference
   c. Rebuild index
```

## LLM Orchestration Model

oh-my-wiki follows graphify's architecture: **the Python library handles deterministic work; the skill.md instructs the host LLM how to orchestrate the intelligent parts.**

What Python code does (no LLM needed):
- File I/O (read/write articles, manage directories)
- Frontmatter parsing and rendering
- SHA256 caching
- Index generation (count backlinks, sort articles, format index.md)
- Backlink extraction (regex `\[\[(.+?)\]\]`)
- Manifest tracking
- URL fetching and normalization
- Health check detection (broken links, orphans — structural checks)

What the host LLM does (via skill.md orchestration):
- Extract topics/entities from raw files
- Plan which articles to create/update
- Write article prose
- Merge new information into existing articles
- Impact analysis for incremental updates
- Answer queries against the wiki
- Suggest connections (lint "find duplicates" check)

This separation means oh-my-wiki works with ANY LLM agent that supports skills — Claude Code, Codex, OpenCode, OpenClaw, or clawpy.
