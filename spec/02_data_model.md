# 02 — Data Model

## Article Structure

Every wiki article follows a strict structure optimized for both Obsidian rendering and LLM agent scanning.

### Frontmatter

```yaml
---
title: "Transformer Architecture"
aliases: ["transformers", "self-attention model", "the transformer"]
created: 2024-03-15T10:30:00Z
updated: 2024-03-20T14:22:00Z
sources:
  - raw/papers/attention-is-all-you-need.pdf
  - raw/articles/karpathy-llm-kb.md
categories:
  - research
  - machine-learning
tags:
  - neural-networks
  - attention
  - nlp
  - deep-learning
confidence: high
word_count: 1250
backlink_count: 7
status: active
---
```

### Frontmatter Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Article title, used as display name and `[[wikilink]]` target |
| `aliases` | string[] | no | Alternative names that resolve to this article |
| `created` | ISO 8601 | yes | When the article was first compiled |
| `updated` | ISO 8601 | yes | When the article was last modified |
| `sources` | string[] | yes | Paths to raw files this article is compiled from |
| `categories` | string[] | yes | Primary categories (used for category pages) |
| `tags` | string[] | no | Finer-grained tags (searchable in Obsidian) |
| `confidence` | enum | yes | `high` (multiple corroborating sources), `medium` (single detailed source), `low` (brief mention or inference) |
| `word_count` | int | yes | Auto-computed on each compile |
| `backlink_count` | int | yes | Auto-computed: number of other articles linking to this one |
| `status` | enum | yes | `active`, `stub` (placeholder, needs content), `stale` (source modified since compile), `archived` |

### Body Structure

```markdown
---
(frontmatter)
---

# Transformer Architecture

> A neural network architecture based on self-attention mechanisms that revolutionized NLP and became the foundation for large language models.

## Overview

The Transformer architecture was introduced in the 2017 paper "Attention Is All You Need" by
Vaswani et al. Unlike previous sequence models based on recurrence (RNNs, LSTMs), the Transformer
relies entirely on attention mechanisms to draw global dependencies between input and output.

The key innovation is the self-attention mechanism, which allows the model to attend to all
positions in the input sequence simultaneously, rather than processing tokens sequentially.

## Key Concepts

- **Self-attention (Scaled Dot-Product Attention)** — computes attention weights between all pairs
  of positions in a sequence. Enables parallel processing and captures long-range dependencies.
- **Multi-head attention** — runs multiple attention functions in parallel, allowing the model
  to attend to information from different representation subspaces.
- **Positional encoding** — since the model has no recurrence, position information is injected
  via sinusoidal or learned embeddings.
- **Feed-forward networks** — applied independently to each position after attention.

## Connections

- [[Attention Mechanisms]] — the foundational mechanism underlying transformers
- [[BERT]] — bidirectional encoder variant, pre-trained on masked language modeling
- [[GPT]] — decoder-only variant, the architecture behind ChatGPT and Claude
- [[Andrej Karpathy]] — discussed transformers in his "LLM Knowledge Bases" post

## Sources

- `raw/papers/attention-is-all-you-need.pdf` — original paper by Vaswani et al. (2017)
- `raw/articles/karpathy-llm-kb.md` — mentioned in context of knowledge compilation

## Notes

This article was created during initial compilation. The connection to [[Andrej Karpathy]]
was discovered during compilation — he discusses transformers in the context of building
personal knowledge bases with LLMs.

Referenced in query: [[Q: How does attention work in modern LLMs?]]
```

### Body Section Reference

| Section | Required | Purpose |
|---------|----------|---------|
| `# Title` | yes | Same as frontmatter title, H1 heading |
| `> Summary` | yes | One-line blockquote — agent can scan title+summary without reading full article |
| `## Overview` | yes | 2-3 paragraph description compiled from sources |
| `## Key Concepts` | for research/technical articles | Bulleted definitions of core concepts |
| `## Connections` | yes | `[[wikilinks]]` to related articles with brief description |
| `## Sources` | yes | Links back to raw files with brief description |
| `## Notes` | optional | LLM-added observations, cross-references from queries, conflict notes |
| `## Conflicts` | only if applicable | When sources disagree, both perspectives documented |

### Design Rationale

**One-line summary (blockquote)**: Critical for agent efficiency. An LLM scanning articles reads title + summary to decide relevance — avoids wasting context on irrelevant articles. This mirrors graphify's approach of including node labels + edge counts in index listings.

**Connections section**: Explicit rather than inline. Agent can quickly find all related articles in one place. Each link has a brief description so the agent knows WHY the connection exists before following it.

**Sources section**: Provenance is not optional. Every article must trace back to raw data. This is the foundation for confidence scoring and staleness detection.

**Status field**: Enables the compiler to create stub articles (placeholder with title + basic outline) when a `[[wikilink]]` targets a non-existent article. Stubs are first-class citizens — they show up in the index and can be expanded later.

## Raw File Frontmatter

Ingested raw files get YAML frontmatter added (consistent with graphify's `ingest.py` pattern):

```yaml
---
source_url: "https://x.com/karpathy/status/..."
type: tweet
title: "LLM Knowledge Bases"
author: "Andrej Karpathy"
captured_at: 2024-03-15T10:30:00Z
contributor: "me"
content_hash: "sha256:abc123..."
---
```

### Raw File Types

| Type | Description | Extensions / Detection |
|------|-------------|----------------------|
| `tweet` | Twitter/X post | `twitter.com`, `x.com` in URL |
| `webpage` | Generic web article | HTTP(S) URL, default |
| `paper` | Academic paper | `.pdf`, or `.md` with paper signals (arxiv, doi, abstract) |
| `note` | Personal note, diary entry | Local `.md`/`.txt` without paper signals |
| `image` | Screenshot, photo, diagram | `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif` |
| `video` | YouTube or video reference | `youtube.com`, `youtu.be` |
| `conversation` | Chat/message export | User-tagged or auto-detected from format |
| `data` | Structured data (CSV, JSON) | `.csv`, `.json`, `.jsonl` |

## Backlink Convention

All inter-article references use Obsidian-style `[[wikilinks]]`:

```markdown
The [[Transformer Architecture]] was a breakthrough that led to [[GPT]] and [[BERT]].
```

Resolution rules:
1. Exact title match (case-insensitive)
2. Alias match (from `aliases` in frontmatter)
3. If no match → broken link (detected by lint)

Backlinks are bidirectional in Obsidian's graph view but only explicit in the source article. The `backlink_count` in frontmatter is computed by scanning all articles for `[[This Article Title]]` or `[[alias]]` references.

## Category System

Categories are discovered during compilation (LLM assigns them), not predefined. The set grows organically.

### Default Seed Categories

When the compiler encounters content it can't categorize, it falls back to:

| Category | Typical Content |
|----------|----------------|
| `people` | Friends, collaborators, public figures |
| `projects` | Startups, side projects, open source |
| `research` | Papers, concepts, methods, algorithms |
| `media` | Books, movies, anime, podcasts, music |
| `personal` | Diary themes, life events, reflections |
| `technology` | Tools, frameworks, languages, platforms |
| `places` | Locations, travel, offices |
| `ideas` | Raw ideas, hypotheses, brainstorms |
| `uncategorized` | Fallback |

### Category Page Format

```markdown
# People

> 23 articles about friends, collaborators, and public figures.

## Articles
- [[Andrej Karpathy]] — AI researcher, Tesla AI director, known for CS231n and minGPT
- [[Sarah Chen]] — co-founder of my startup, ML engineer, Stanford MS
- [[Hayao Miyazaki]] — filmmaker, Studio Ghibli founder, inspiration for design philosophy
...
```

Each article has a one-line descriptor. This is the same pattern as index.md — optimized for agent scanning.

## Extraction Output Schema

The extract step (LLM-powered, cached) produces a structured JSON per raw file:

```json
{
  "source_file": "raw/articles/karpathy-llm-kb.md",
  "source_hash": "sha256:abc123...",
  "topics": [
    {"name": "LLM Knowledge Bases", "relevance": "primary"},
    {"name": "Personal Wiki", "relevance": "primary"},
    {"name": "Obsidian", "relevance": "secondary"},
    {"name": "RAG vs Wiki", "relevance": "secondary"}
  ],
  "entities": [
    {"name": "Andrej Karpathy", "type": "person", "role": "author"},
    {"name": "Obsidian", "type": "tool"},
    {"name": "Marp", "type": "tool"}
  ],
  "summary": "Karpathy describes using LLMs to compile personal knowledge bases from raw data into structured markdown wikis, viewable in Obsidian, with incremental compilation and health checks.",
  "suggested_titles": [
    "LLM Knowledge Bases",
    "Andrej Karpathy",
    "Personal Wiki Compilation"
  ],
  "suggested_categories": ["research", "technology"],
  "key_claims": [
    "At ~100 articles / ~400K words, LLM can answer complex questions against the wiki without RAG",
    "File system structure is the query interface — no embeddings needed",
    "Queries should be filed back into the wiki to enhance it"
  ]
}
```

This schema is validated before compilation consumes it (same pattern as graphify's `validate.py`).

## Manifest Schema

`.omw/manifest.json` tracks the mapping between raw files, extractions, and articles:

```json
{
  "version": 1,
  "last_compile": "2024-03-20T14:22:00Z",
  "raw_files": {
    "sha256:abc123": {
      "path": "raw/articles/karpathy-llm-kb.md",
      "mtime": 1710936600.0,
      "articles": ["LLM Knowledge Bases", "Andrej Karpathy"]
    }
  },
  "articles": {
    "LLM Knowledge Bases": {
      "file": "wiki/llm-knowledge-bases.md",
      "sources": ["sha256:abc123", "sha256:def456"],
      "backlinks_to": ["Andrej Karpathy", "Personal Wiki Compilation", "Obsidian"],
      "backlinks_from": ["AI Research Tools", "Knowledge Management"],
      "word_count": 1250,
      "confidence": "high"
    }
  },
  "categories": {
    "research": ["LLM Knowledge Bases", "Transformer Architecture", ...],
    "people": ["Andrej Karpathy", "Sarah Chen", ...]
  }
}
```

The manifest enables:
- **Incremental detection**: compare raw file mtimes/hashes to find changes
- **Impact analysis**: when a raw file changes, look up which articles depend on it
- **Cascade tracking**: when an article changes, look up which articles backlink to it
- **Staleness detection**: compare `last_compile` against raw file mtimes

## Compile Log Schema

`.omw/compile-log.json` records what happened in the last compile:

```json
{
  "timestamp": "2024-03-20T14:22:00Z",
  "mode": "incremental",
  "duration_seconds": 45,
  "raw_files_processed": 3,
  "articles_created": 1,
  "articles_updated": 2,
  "articles_unchanged": 44,
  "stubs_created": 1,
  "index_rebuilt": true,
  "changes": [
    {"action": "create", "article": "New Research Topic", "sources": ["raw/papers/new-paper.pdf"]},
    {"action": "update", "article": "Machine Learning", "reason": "new source adds information about recent developments"},
    {"action": "update", "article": "Andrej Karpathy", "reason": "new tweet references updated"},
    {"action": "stub", "article": "Diffusion Models", "reason": "linked from New Research Topic but no dedicated source yet"}
  ]
}
```
