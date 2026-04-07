# oh-my-wiki

> Raw data in, structured knowledge out. Your personal Wikipedia, compiled by AI.

Feed it your notes, bookmarks, articles, screenshots, diary entries — oh-my-wiki compiles them into a structured wiki of interconnected markdown articles with backlinks, categories, and an index. View it in Obsidian. Query it with your AI agent.

No embeddings. No vector database. No RAG. The file system IS the retrieval mechanism.

## Quick Start

```bash
pip install oh-my-wiki

omw init ~/my-knowledge
omw ingest https://example.com/article
omw ingest ~/notes/meeting-notes.md
echo "Quick thought about transformers" | omw ingest -
omw compile
```

Open `wiki/` in Obsidian and explore.

## How It Works

```
raw/  →  detect  →  extract  →  compile  →  index  →  wiki/
                                                         ↑
                                                query → file-back
                                                lint  → fix
```

1. **Ingest** raw data into `raw/` — URLs, local files, stdin, batch imports
2. **Compile** the wiki — LLM extracts topics/entities, plans articles, writes prose
3. **Index** automatically — `index.md` + category pages + hub article ranking
4. **Query** the wiki — agent navigates index → categories → articles → backlinks
5. **File back** — query results become wiki articles, enriching the knowledge base
6. **Lint** — health checks find broken links, orphans, stale articles, duplicates

## What You Get

```
wiki/
  index.md                    # Agent entry point — categories, hubs, all articles A-Z
  WIKI_REPORT.md              # Health metrics, coverage gaps, freshness
  _categories/
    research.md               # Articles in this category with one-line summaries
    people.md
    technology.md
  transformer-architecture.md # Full article with backlinks, sources, connections
  andrej-karpathy.md
  my-startup.md
  _queries/
    20240320_how_does_attention_work.md  # Filed-back query result
```

Every article has:
- YAML frontmatter (title, aliases, categories, tags, confidence, sources)
- `> One-line summary` for fast agent scanning
- `## Connections` with `[[wikilinks]]` to related articles
- `## Sources` linking back to raw files

## Commands

```bash
omw init [directory]              # Initialize workspace (raw/, wiki/, .omw/)
omw ingest <source>               # Add to raw/ (URL, file, or - for stdin)
omw ingest --batch urls.txt       # Bulk ingest
omw compile                       # Incremental compile (default)
omw compile --full                # Full rebuild
omw query "question"              # Ask the wiki (via /omw skill)
omw status                        # Wiki stats
omw lint                          # Health checks
omw report                        # Generate WIKI_REPORT.md
omw watch                         # Auto-notify on raw/ changes
omw install                       # Install as Claude Code skill
omw claude install                # Project-level CLAUDE.md + hook
```

## As an AI Skill

oh-my-wiki works as a skill inside AI coding assistants. Install once:

```bash
omw install                       # Claude Code
omw install --platform codex      # Codex
omw install --platform opencode   # OpenCode
omw install --platform claw       # OpenClaw / ClawPy
```

Then type `/omw compile .` in your assistant to compile your wiki.

The assistant reads your raw files, extracts topics and entities, plans articles, writes them with `[[wikilinks]]`, builds the index, and generates a health report. All orchestrated via `skill.md`.

## Obsidian

Point Obsidian at `wiki/` as a vault. Everything works out of the box:
- `[[wikilinks]]` render as clickable links
- Backlinks panel shows incoming references
- Graph view visualizes article connections
- Tags from frontmatter are searchable
- Aliases enable `[[alternate name]]` resolution

## Inspired By

- **Andrej Karpathy's "LLM Knowledge Bases"** — raw data compiled into .md wikis, queried by LLMs, with health checks and feedback loops
- **Farzapedia** — 2,500 diary entries → 400 articles with backlinks, built for the agent, not the human

## Architecture

- **Wiki-first** — the wiki IS the knowledge base, not a derived view of a graph
- **Zero required dependencies** — stdlib-only Python; LLM calls made by host agent
- **Incremental compilation** — adding one raw file updates only affected articles
- **Agent-optimized** — index.md → categories → articles → backlinks navigation
- **Provenance tracking** — every article traces back to raw sources with confidence levels

## Related Projects

- [graphify](https://github.com/safishamsi/graphify) — knowledge graph from any folder (complementary: structure vs prose)
- [clawpy](https://github.com/andykhan/clawpy) — multi-model CLI agent (future standalone backend)

## License

MIT
