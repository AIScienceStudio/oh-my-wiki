# oh-my-wiki Specification — Quick Reference

> LLM-powered personal wiki compiler. Raw data in, structured knowledge base out.
> Inspired by Karpathy's "LLM Knowledge Bases" and Farzapedia.

## Spec Files

| File | Scope | Status |
|------|-------|--------|
| [00_vision.md](00_vision.md) | Vision, design philosophy, relationship to graphify/clawpy | Done |
| [01_architecture.md](01_architecture.md) | Pipeline, module map, directory layout, data flow | Done |
| [02_data_model.md](02_data_model.md) | Article structure, frontmatter, backlinks, categories, schemas | Done |
| [03_cli.md](03_cli.md) | CLI commands, options, output format, env vars | Done |
| [04_compilation.md](04_compilation.md) | Full/incremental compile, extraction, planning, writing, prompts | Done |
| [05_query_lint_analyze.md](05_query_lint_analyze.md) | Query system, lint checks, WIKI_REPORT.md analysis | Done |
| [06_skill_orchestration.md](06_skill_orchestration.md) | skill.md structure, multi-platform, token efficiency | Done |
| [07_implementation.md](07_implementation.md) | Tech stack, reuse from graphify, phases, testing | Done |
| [08_edge_cases.md](08_edge_cases.md) | YAML parser, images, error recovery, manual edits, git, scale, dedup | Done |
| [09_branding.md](09_branding.md) | Name, tagline, positioning, README structure, visual identity | Done |
| [10_clawpy_integration.md](10_clawpy_integration.md) | Standalone mode via ClawPy, engine.py, multi-model, CLI flags | Done |

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Wiki-first, not graph-first | The wiki IS the knowledge base, not a derived view |
| Zero required dependencies | Stdlib only; LLM calls made by host agent |
| Skill architecture | Python handles deterministic work; skill.md orchestrates LLM |
| Incremental by default | Impact analysis: only update affected articles |
| Agent-optimized structure | index.md → categories → articles → backlinks navigation |
| Obsidian-compatible | [[wikilinks]], aliases, tags, YAML frontmatter — pure markdown |
| File-back feedback loop | Queries enrich the wiki; system gets smarter from usage |

## Architecture at a Glance

```
raw/  →  detect  →  extract  →  compile  →  index  →  wiki/
                                                         ↑
                                                query → file-back
                                                lint  → fix
```

## Reuse from Existing Projects

| From graphify | Module | What |
|---------------|--------|------|
| `cache.py` | `cache.py` | SHA256 extraction cache, atomic writes |
| `security.py` | `security.py` | URL validation, safe fetch |
| `ingest.py` | `ingest.py` | URL fetching (tweet, arxiv, webpage, PDF) |
| `detect.py` | `detect.py` | File discovery, paper heuristic, sensitive filtering |
| `__main__.py` | `__main__.py` | CLI pattern, platform install/uninstall |
| `skill.md` | `skill.md` | Step-by-step LLM orchestration pattern |
| `analyze.py` | `analyze.py` | Hub detection, gap analysis patterns |
| `report.py` | `analyze.py` | WIKI_REPORT.md generation pattern |

| From clawpy | Future | What |
|-------------|--------|------|
| Engine | Standalone mode | LLM backend for non-skill operation |
| Tool system | Tool architecture | Protocol + Registry pattern for commands |
| Provider layer | Multi-model | Support for Anthropic, OpenAI, Gemini, etc. |
