# 00 — Vision & Design Philosophy

## What oh-my-wiki Is

oh-my-wiki is a personal LLM-powered wiki compiler. You feed it raw data — notes, bookmarks, articles, screenshots, diary entries, research papers, conversations — and an LLM compiles and maintains a structured wiki of interconnected markdown articles.

The wiki IS the knowledge base. No graph database, no vector store, no RAG pipeline, no embeddings. Just markdown files on disk, navigable by both humans (in Obsidian) and LLM agents (via `index.md`).

## Origin

Two viral concepts, March 2025:

**Karpathy's "LLM Knowledge Bases"** — raw data indexed into `raw/`, LLM incrementally "compiles" a wiki (collection of .md files), wiki includes summaries, backlinks, categorized concepts. At ~100 articles / ~400K words, you can ask the LLM complex questions against the wiki. LLM auto-maintains index files. Queries get "filed back" into the wiki. LLM runs "health checks" to find inconsistencies and connections.

**Farzapedia** — 2,500 diary/notes/iMessage entries compiled into 400 detailed articles (friends, startups, research, anime) with backlinks. Built for the AGENT, not the human — structure is easily crawlable. Agent starts at `index.md`, drills into specific pages. Adding new things auto-updates 2-3 related articles. "Super genius librarian for your brain."

## Core Insight

At personal knowledge scale (100-500 articles, under 1M words), the file system structure IS the query interface. An LLM agent starts at `index.md`, reads the catalog, drills into the relevant article, follows backlinks. No embedding search needed. A knowledge base that lets an agent find what it needs via a file system it actually understands just works better than RAG.

## Design Principles

1. **Wiki-first** — the primary artifact is a navigable .md wiki, not a knowledge graph or database. Articles are first-class citizens with prose, nuance, and narrative.

2. **Agent-optimized** — every structural decision (index.md layout, one-line summaries, category pages, backlinks) is designed for efficient LLM agent traversal. The human experience (Obsidian) is a happy consequence.

3. **Incremental by default** — adding one raw file triggers impact analysis, not full rebuild. The LLM decides which existing articles to update, what new articles to create, and what to leave alone.

4. **Feedback loop** — queries enrich the wiki. Every Q&A session can be filed back as an article. The wiki gets smarter from what you ask, not just what you add.

5. **Zero required dependencies** — stdlib-only Python for the core pipeline. The LLM calls are made by the host agent (Claude Code, Codex, etc.), not by oh-my-wiki itself.

6. **Provenance always** — every article traces back to raw sources. Every claim has a source. Confidence levels (high/medium/low) are explicit.

7. **Skill architecture** — oh-my-wiki is a skill (Python library + skill.md) that a host LLM orchestrates, not a standalone LLM application. The Python code handles deterministic work; the LLM provides intelligence.

## What oh-my-wiki Is NOT

- **Not a knowledge graph tool** — that's graphify. oh-my-wiki has no NetworkX, no community detection, no tree-sitter. The wiki is primary, not derived from a graph.
- **Not a RAG system** — no embeddings, no vector database, no similarity search. The file structure IS the retrieval mechanism.
- **Not a note-taking app** — it doesn't help you write notes. It compiles your existing notes/data into a structured wiki.
- **Not a standalone LLM app** — it doesn't call APIs directly. It's a skill that a host agent orchestrates.

## Relationship to Other Projects

| Project | What It Does | Relationship |
|---------|-------------|-------------|
| **graphify** | Raw data → knowledge graph → clustered communities → HTML/JSON/report | Complementary. graphify extracts structure; oh-my-wiki writes prose. graphify's `--wiki` generates template-filled articles from graph data; oh-my-wiki's LLM writes full articles from source material. Borrows patterns: ingest, cache, security, detect, skill.md orchestration, multi-platform install. |
| **clawpy** | Multi-model CLI coding agent (Python rewrite of Claude Code) | Potential future backend. clawpy could serve as the LLM engine for standalone oh-my-wiki operation (no host agent needed). clawpy's tool system (Protocol + Registry) informs oh-my-wiki's command architecture. |

## Success Metrics

- **Compilation quality**: Does the wiki accurately represent the raw data? Are backlinks meaningful? Are categories sensible?
- **Agent efficiency**: Can an LLM agent answer a question by reading index.md + 2-3 articles? (Target: 90% of queries answered within 5 article reads)
- **Incremental precision**: When adding one raw file, does the compiler update only the right articles? (No unnecessary full rebuilds)
- **Human readability**: Does the wiki look good in Obsidian? Are articles well-written? Is the graph view useful?
