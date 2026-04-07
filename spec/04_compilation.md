# 04 — Compilation Strategy

This is the most architecturally significant module. The compiler decides: given raw data, which articles to create, which to update, and which to leave alone.

## Overview

Compilation has three modes:

| Mode | When | What Happens |
|------|------|-------------|
| **Full** | First run, or `--full` flag | Extract all raw files, plan all articles, write everything from scratch |
| **Incremental** | Default on subsequent runs | Detect changes, extract only new/modified files, impact analysis, update affected articles |
| **Single** | `--article "Name"` | Force recompile one specific article from its sources |

## Phase 1: Extraction

### What extraction produces

For each raw file, the LLM extracts a structured JSON (see `02_data_model.md` for full schema):

```json
{
  "source_file": "raw/articles/karpathy-llm-kb.md",
  "topics": [...],
  "entities": [...],
  "summary": "...",
  "suggested_titles": [...],
  "suggested_categories": [...],
  "key_claims": [...]
}
```

### Extraction prompt architecture

Follows graphify's subagent pattern (skill.md Step B2): raw files are chunked into groups of 15-20 and dispatched to parallel subagents. Each subagent receives:

1. A list of raw files to process
2. The extraction schema (what fields to output)
3. Instructions to read each file and produce one extraction JSON per file
4. For images: use vision to describe content, extract text, identify concepts
5. For PDFs: extract text pages, identify structure (abstract, sections, references)

### Caching

Extraction results are cached by SHA256 of file contents (same as graphify's `cache.py`):
- Cache key: `SHA256(file_contents + resolved_path)`
- Cache entry: `.omw/cache/{hash}.json`
- Atomic writes via tmp + `os.replace()`
- On incremental compile, unchanged files get cache hits → no LLM calls needed

### Paper detection

Borrow graphify's heuristic: `.md`/`.txt` files with >= 3 of these signals are classified as papers (not notes):
- arxiv, doi, abstract, proceedings, journal, preprint
- LaTeX citations, numbered citations, equation references
- arXiv ID pattern, "we propose", "literature"

Papers get special extraction: citation mining, author extraction, abstract as summary.

## Phase 2: Planning

The planning step receives ALL extractions (cached + new) and the current wiki state, then produces a compilation plan.

### Planning input

```json
{
  "extractions": [...],           // All extraction results
  "existing_articles": [...],     // Titles + summaries from current index.md
  "existing_categories": [...],   // Current category list
  "manifest": {...}               // Current raw→article mapping
}
```

### Planning output (compilation plan)

```json
{
  "articles": [
    {
      "title": "Diffusion Models",
      "action": "create",
      "sources": ["raw/papers/diffusion-paper.pdf"],
      "categories": ["research", "machine-learning"],
      "outline": "Overview of diffusion models, key concepts (forward/reverse process, noise schedule), connections to score matching and transformers",
      "related_existing": ["Machine Learning", "Neural Networks"]
    },
    {
      "title": "Machine Learning",
      "action": "update",
      "new_sources": ["raw/articles/new-ml-post.md"],
      "reason": "New source covers recent developments in efficient training that should be added to the Overview and Key Concepts sections"
    },
    {
      "title": "Score Matching",
      "action": "stub",
      "reason": "Referenced in planned 'Diffusion Models' article but no dedicated source material",
      "categories": ["research"]
    }
  ],
  "no_action": [
    {
      "source": "raw/notes/random-thought.md",
      "reason": "Content too brief/vague to warrant a standalone article. Key point absorbed into 'Machine Learning' update."
    }
  ]
}
```

### Planning rules

1. **One article per distinct topic** — don't merge unrelated topics into one article. If a raw file covers 3 topics, it may contribute to 3 articles.

2. **Prefer updating over creating** — if a new source adds information to an existing topic, update the existing article rather than creating a duplicate. The LLM checks existing article titles + summaries to detect overlap.

3. **Minimum viable article** — don't create an article from a single brief mention. If the source material for a topic is less than ~100 words, either absorb it into a related article's Notes section or create a stub.

4. **Stubs for forward references** — if a planned article references a topic that has no article yet and no source material, create a stub. Stubs are real articles with `status: stub` and a brief outline, not broken links.

5. **Category consistency** — prefer existing categories over new ones. Only create a new category if >= 3 articles would belong to it.

6. **Conflict detection** — if two sources provide contradictory information about the same topic, flag it in the plan so the article gets a `## Conflicts` section.

## Phase 3: Writing

### Creating a new article

The LLM receives:
1. The plan entry (title, outline, categories)
2. The relevant raw source file(s) — full text
3. A list of existing article titles (so it can create accurate `[[wikilinks]]`)
4. The article template (frontmatter + body structure from `02_data_model.md`)

The LLM writes the complete article. Key instructions:
- Start with a one-line summary in blockquote
- Write the Overview from source material, citing specific sources
- Identify and define Key Concepts with bullet points
- Create Connections section with `[[wikilinks]]` to existing articles
- List all Sources with brief descriptions
- Set confidence based on source quality/quantity

### Updating an existing article

The LLM receives:
1. The existing article (full text)
2. The new source material
3. The reason for update (from plan)
4. List of all article titles (for wikilinks)

The LLM produces a merged version:
- Integrate new information into existing sections (don't just append)
- Add new Key Concepts if the source introduces them
- Add new Connections if the source reveals them
- Update Sources section
- Update confidence if warranted
- Update the `updated` timestamp
- If conflicting info: add a `## Conflicts` section

### Writing parallelism

Like graphify's Step B3, articles are written by parallel subagents. Each subagent writes 3-5 articles. Subagents don't depend on each other (article content is based on raw sources + plan, not on other articles being written in the same batch).

However, there's a sequencing constraint: stubs should be created AFTER main articles, because main articles may add more context about what the stub should say. In practice:
1. Write all `create` articles in parallel
2. Write all `update` articles in parallel (can overlap with step 1)
3. Create all `stub` articles (informed by what was just written)

## Phase 4: Indexing

After all articles are written, rebuild the index deterministically (no LLM needed):

1. Scan `wiki/` for all `.md` files
2. Parse frontmatter from each
3. Compute backlink counts (scan all articles for `[[wikilinks]]`)
4. Generate `index.md`:
   - Stats line (article count, word count, last compiled)
   - Categories section (sorted by article count)
   - Recent Updates (sorted by `updated` timestamp, top 10)
   - Most Connected (sorted by backlink count, top 10)
   - All Articles A-Z (title, category, source count, confidence)
5. Generate/update category pages in `_categories/`
6. Generate `WIKI_REPORT.md` (wiki health analysis)

## Phase 5: Post-Compile

1. **Update manifest**: Record new raw→article mappings, article→article backlinks
2. **Write compile-log**: Record what changed, for diff/status commands
3. **Snapshot wiki state**: Serialized summary for future diff comparisons

## Incremental Compile: Impact Analysis

This is the key differentiator from graphify, which rebuilds the entire graph on `--update`.

### Change detection

```
1. Load manifest (last known state)
2. Scan raw/: compare file hashes + mtimes against manifest
3. Classify: new files, modified files, deleted files, unchanged
```

### Impact propagation

For each changed raw file:
```
1. Look up manifest: which articles were compiled from this file?
2. Those articles are DIRECTLY affected → marked for update
3. Look up backlinks: which articles link TO the affected articles?
4. Those articles are INDIRECTLY affected → candidates for update
   (LLM decides if they actually need changes)
```

For deleted raw files:
```
1. Look up manifest: which articles depended on this file?
2. If article has OTHER sources → update (remove references to deleted source)
3. If article has NO other sources → mark as stale/archive
```

### Efficiency target

For a wiki with 100 articles, adding one raw file should:
- Extract: 1 file (others are cache hits)
- Plan: 1 LLM call (reads index.md + new extraction)
- Write: 1-3 articles (1 create + 0-2 updates)
- Index: rebuild (deterministic, <1 second)
- Total LLM calls: ~3 (extract + plan + write)

Compare to full compile: ~100+ LLM calls.

## Compilation Prompt Templates

### Extraction Prompt (per subagent)

```
You are extracting structured information from raw source files for a personal knowledge wiki.

For each file below, produce a JSON extraction with these fields:
- topics: [{name, relevance: "primary"|"secondary"}]
- entities: [{name, type: "person"|"tool"|"concept"|"organization"|"place", role?}]
- summary: One paragraph summarizing the key information
- suggested_titles: Article titles this source could contribute to (2-5)
- suggested_categories: Categories from: [people, projects, research, media, personal, technology, places, ideas]
- key_claims: Specific factual claims or insights worth preserving (3-10)

Be specific. Extract actual names, dates, numbers, and quotes — not vague descriptions.
For images, describe what you see and extract any visible text.

Files to process:
[file contents here]
```

### Planning Prompt

```
You are planning a wiki compilation. Given the extractions from raw source files and the current state of the wiki, decide which articles to create, update, or leave alone.

Current wiki has {N} articles. See index below for existing article titles and summaries.

Rules:
1. Prefer updating existing articles over creating duplicates
2. One article per distinct topic (don't merge unrelated topics)
3. Create stubs for forward references that have no source material
4. Minimum ~100 words of source material to justify a standalone article
5. Flag conflicting information between sources

Extractions:
[extractions here]

Current index.md:
[index content here]

Output a JSON compilation plan.
```

### Article Writing Prompt

```
You are writing an article for a personal knowledge wiki. Write in clear, informative prose.

Title: {title}
Categories: {categories}
Outline: {outline}

Source material:
[raw file contents]

Existing articles you can link to with [[wikilinks]]:
[list of titles]

Format:
- Start with YAML frontmatter (title, aliases, created, updated, sources, categories, tags, confidence, word_count, backlink_count: 0, status: active)
- H1 title
- > One-line summary (blockquote)
- ## Overview (2-3 paragraphs)
- ## Key Concepts (if technical/research)
- ## Connections (wikilinks to related articles)
- ## Sources (raw file paths with descriptions)
- ## Notes (optional: observations, cross-references)

Write for a knowledgeable reader. Don't be encyclopedic — capture what's interesting and unique from the sources. Use [[wikilinks]] naturally in the text, not just in the Connections section.
```
