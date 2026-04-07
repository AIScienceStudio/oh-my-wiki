# 09 — Naming & Branding

## Name

**oh-my-wiki** — the project/repo name.
**omw** — the CLI binary.

### Why "oh-my-wiki"

- Nods to the "oh-my-*" convention (oh-my-zsh, oh-my-posh) — tools that transform a mundane experience into something powerful
- Memorable, playful, distinct from graphify's technical tone
- "wiki" immediately communicates what it produces
- `omw` as CLI is short, easy to type, no conflicts with common binaries

### PyPI Name

`oh-my-wiki` (check availability). Fallback: `ohmywiki` or `oh_my_wiki`.

The CLI command is always `omw` regardless of package name.

### Python Package

```python
import oh_my_wiki
```

Module directory: `oh_my_wiki/` (underscore, PEP 8 convention).

## Tagline

> Raw data in, structured knowledge out. Your personal Wikipedia, compiled by AI.

Short version for badges/headers:
> LLM-powered personal wiki compiler

## Positioning

### vs graphify

| | graphify | oh-my-wiki |
|---|---------|-----------|
| Metaphor | "X-ray" — reveals hidden structure | "Librarian" — organizes your knowledge |
| Output | Knowledge graph + report | Wiki articles you can read |
| Best for | Understanding codebases, research corpora | Personal knowledge, life context, inspiration |
| Vibe | Technical, analytical | Personal, creative, warm |

They're complementary, not competing. graphify finds structure you didn't know was there. oh-my-wiki writes the articles you'd write if you had infinite time.

### vs Notion/Obsidian

oh-my-wiki is not a note-taking app. It's the step AFTER note-taking — it compiles your scattered notes into an organized wiki. Obsidian is the viewer, not the competitor.

### vs RAG

"I built a similar system to this a year ago with RAG but it was ass." — Farzapedia

oh-my-wiki is explicitly positioned as the anti-RAG. No embeddings, no vector DB, no chunking. The file system IS the retrieval mechanism.

## README Structure

```markdown
# oh-my-wiki

> Raw data in, structured knowledge out. Your personal Wikipedia, compiled by AI.

[badges: PyPI, CI, Python version]

Feed it your notes, bookmarks, articles, screenshots, diary entries — oh-my-wiki
compiles them into a structured wiki of interconnected markdown articles with
backlinks, categories, and an index. View it in Obsidian. Query it with your AI agent.

## Quick Start
  omw init
  omw ingest <url-or-file>
  omw compile
  # Open wiki/ in Obsidian

## How It Works
  [pipeline diagram: raw/ → detect → extract → compile → wiki/]

## What You Get
  [screenshot of wiki in Obsidian with graph view]

## Commands
  [CLI reference table]

## Inspired By
  - Andrej Karpathy's "LLM Knowledge Bases"
  - Farzapedia's personal Wikipedia

## Install
  pip install oh-my-wiki

## Related
  - graphify — knowledge graph from any folder (complementary)
  - clawpy — multi-model CLI agent (standalone backend)
```

## Logo / Visual Identity

- **Icon concept**: An open book with interconnected nodes/links emanating from it
- **Color**: Warm amber/gold (contrast with graphify's likely blue/tech palette)
- **Style**: Minimal line art, works at 16x16 favicon size

(Actual logo creation is out of scope for MVP — placeholder text-based logo is fine.)

## Community Messaging

For social posts / launch:
- "I built a tool that turns my messy notes into a personal Wikipedia"
- "No RAG, no embeddings — just markdown files an AI agent actually understands"
- "Inspired by @karpathy's LLM Knowledge Bases and @farzapedia — now anyone can do it"
