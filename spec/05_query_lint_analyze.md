# 05 — Query, Lint, and Analysis

## Query System

### Philosophy

No embeddings. No vector search. No RAG pipeline.

The wiki's file structure IS the retrieval mechanism. The LLM navigates it the same way a human would: start at the index, find relevant articles, read them, follow links.

At personal knowledge scale (<500 articles), this is more reliable than RAG because:
1. The LLM reads actual article content, not similarity-matched chunks
2. The index provides a complete catalog with one-line descriptors
3. Backlinks surface connections that embeddings might miss
4. The LLM can reason about WHY articles are related, not just that they are

### Query Flow

```
1. User asks: "What design inspirations should I use for my new landing page?"

2. prepare_query(question, wiki_dir):
   a. LLM parses question → key concepts: [design, inspiration, landing page]
   b. Read index.md → scan all article titles + one-line descriptors
   c. Identify candidates:
      - Direct matches: "Design Inspiration", "Landing Pages"
      - Category matches: _categories/media.md (films, images that inspired me)
      - Related: "Competitors", "Product Design Philosophy"
   d. Return ranked list of article paths

3. Host LLM agent reads top 3-5 articles
   a. Follows backlinks if article references another relevant one
   b. Stops when question is answered or budget exhausted

4. Synthesize answer citing specific articles:
   "Based on your wiki:
   - Your 'Philosophy' articles reference a Studio Ghibli documentary about...
   - 'Competitors' has screenshots of YC company landing pages...
   - You saved 1970s Beatles merch images in 'Media Inspiration'...
   Here's what I'd suggest for your landing page..."

5. Optional file-back (--file-back or default for complex queries)
```

### Query Budget

`--budget N` limits how many articles the agent reads:

| Budget | Behavior |
|--------|----------|
| Default (no flag) | Up to 5 articles, follow up to 2 backlinks each |
| `--budget 3` | Read at most 3 articles |
| `--budget 10` | Deep research mode, up to 10 articles |
| `--budget 1` | Quick lookup — read only the single best match |

### File-Back

When a query result is filed back into the wiki:

1. **Save as query article**: `wiki/_queries/YYYYMMDD_slug.md`

```yaml
---
title: "Q: What design inspirations for my landing page?"
aliases: []
created: 2024-03-20T14:00:00Z
updated: 2024-03-20T14:00:00Z
sources: []
categories:
  - queries
tags:
  - design
  - landing-page
confidence: medium
word_count: 450
backlink_count: 0
status: active
source_articles:
  - "Design Inspiration"
  - "Competitors"
  - "Media Inspiration"
---

# Q: What design inspirations for my landing page?

> Query result filed back into wiki on 2024-03-20.

## Answer

Based on the wiki, the following design inspirations are most relevant...
[full answer text]

## Source Articles

- [[Design Inspiration]] — general design philosophy and influences
- [[Competitors]] — YC company landing page screenshots
- [[Media Inspiration]] — 1970s Beatles merch, Studio Ghibli visual style
```

2. **Cross-reference in source articles**: Append to each cited article's Notes section:

```markdown
## Notes
...
Referenced in query: [[Q: What design inspirations for my landing page?]]
```

3. **Rebuild index**: The query article appears in index.md under "Recent Updates"

This closes Karpathy's feedback loop: "my own explorations and queries always 'add up' in the knowledge base."

## Lint System

### Design

Lint checks are split into two types:
- **Structural checks**: Deterministic, run by Python code (no LLM)
- **Semantic checks**: Require LLM reasoning (duplicate detection, connection suggestions)

### Structural Checks (No LLM)

| Check | Severity | Auto-fixable | Detection |
|-------|----------|-------------|-----------|
| **Broken links** | error | Yes (create stub / remove link) | Regex scan for `\[\[(.+?)\]\]`, check if target exists |
| **Index drift** | error | Yes (rebuild index) | Compare index.md article list vs actual wiki/ files |
| **Missing frontmatter** | error | Yes (add defaults) | Parse frontmatter, check required fields |
| **Invalid frontmatter** | error | No | Validate field types (date format, enum values) |
| **Orphan articles** | warning | No | Articles with `backlink_count: 0` |
| **Stale articles** | warning | Yes (trigger recompile) | Compare source file mtimes vs article `updated` |
| **Empty categories** | warning | Yes (remove page) | Category page lists 0 articles |
| **Oversized articles** | warning | No (suggests split) | `word_count > OMW_MAX_ARTICLE_WORDS` |
| **Missing sources** | error | No | Article references raw/ file that doesn't exist |
| **Circular-only links** | info | No | A ↔ B linked to each other but no other connections |
| **Stubs without sources** | info | No | `status: stub` articles (remind user to add source material) |

### Semantic Checks (LLM Required)

| Check | Severity | Auto-fixable | How |
|-------|----------|-------------|-----|
| **Duplicate topics** | warning | No (suggests merge) | LLM reads pairs of articles with similar titles/tags, decides if they overlap >50% |
| **Suggested connections** | info | No (suggests links) | LLM reads orphan/low-backlink articles and suggests which existing articles they should link to |
| **Inconsistent claims** | warning | No (flags conflict) | LLM compares key_claims across articles for contradictions |
| **Missing topics** | info | No (suggests articles) | LLM analyzes raw/ for topics not yet covered by any article |

### Lint Output Format

```json
{
  "errors": [
    {"check": "broken_link", "article": "Diffusion Models", "detail": "[[Score Matching]] not found", "fix": "create_stub"}
  ],
  "warnings": [
    {"check": "orphan", "article": "Random Thought", "detail": "0 backlinks", "suggestion": "Link from Machine Learning or Personal Notes"}
  ],
  "info": [
    {"check": "stub_without_source", "article": "Score Matching", "detail": "Stub article, no raw source"}
  ],
  "summary": {
    "total_articles": 48,
    "errors": 3,
    "warnings": 5,
    "info": 2,
    "fixable": 3
  }
}
```

### Auto-Fix Behavior (`--fix`)

For each fixable issue:
1. **Broken link → create stub**: Create a minimal article with `status: stub` and one-line description inferred from the linking context
2. **Index drift → rebuild**: Run `rebuild_index(wiki_dir)` deterministically
3. **Missing frontmatter → add defaults**: Set `confidence: low`, `status: active`, `categories: [uncategorized]`, timestamps from file mtime
4. **Stale articles → mark**: Set `status: stale` in frontmatter (doesn't auto-recompile — that requires LLM)
5. **Empty categories → remove**: Delete the category page, remove from index

## Analysis: WIKI_REPORT.md

Like graphify's `GRAPH_REPORT.md`, oh-my-wiki generates a health report that serves as a quick orientation for both humans and agents.

### Report Structure

```markdown
# Wiki Report — my-knowledge (2024-03-20)

## Summary
- 48 articles · 32,400 words · 8 categories
- Last compiled: 2024-03-20 14:22 UTC (incremental)
- Raw corpus: 52 files · ~45,000 words
- Compression: 1.39x (wiki is more concise than raw data)
- Cache hit rate: 94% (49/52 files cached)

## Health
- Confidence: 31 high, 12 medium, 5 low
- Status: 44 active, 3 stubs, 1 stale
- Lint: 3 errors, 5 warnings (see `omw lint`)

## Hub Articles (most backlinked — your core topics)
1. [[Machine Learning]] — 12 backlinks
2. [[Python]] — 9 backlinks
3. [[My Startup]] — 8 backlinks
4. [[Andrej Karpathy]] — 6 backlinks
5. [[Transformer Architecture]] — 5 backlinks

## Coverage Gaps
- 3 stub articles need source material: [[Score Matching]], [[Diffusion Models]], [[RLHF]]
- 5 raw files not yet contributing to any article
- Category "places" has only 1 article

## Recent Activity
- Last 7 days: 3 articles created, 5 updated, 12 queries filed back
- Most active category: research (8 changes)
- Growing topics: "LLM agents" mentioned in 3 new sources but no dedicated article

## Suggested Actions
1. Add source material for stub articles (3 stubs)
2. Review stale article "ML Research" (source modified 19 days ago)
3. Consider creating article for "LLM Agents" (3 mentions, no article)
4. Run `omw lint --fix` to resolve 3 auto-fixable errors
5. Consider merging "Neural Networks" and "Deep Learning" (high tag overlap)

## Freshness
- Oldest article: "Python Basics" (compiled 2024-01-15, 65 days ago)
- Average article age: 22 days
- 5 articles compiled in last 7 days

---
*Generated by oh-my-wiki. See [[index]] to navigate.*
```

### Analysis Computations (Deterministic, No LLM)

| Metric | Computation |
|--------|-------------|
| Hub articles | Sort articles by `backlink_count` descending |
| Compression ratio | `total_raw_words / total_wiki_words` |
| Freshness | Days since each article's `updated` timestamp |
| Coverage gaps | Raw files not in any article's `sources`; stub articles |
| Category distribution | Count articles per category |
| Confidence distribution | Count articles per confidence level |

### Analysis Computations (LLM Suggested)

| Metric | How |
|--------|-----|
| Growing topics | LLM scans recent extractions for topic clusters not yet covered |
| Merge suggestions | LLM compares articles with overlapping tags/categories |
| Missing connections | LLM identifies articles that should link to each other but don't |

The LLM-powered suggestions are generated during `omw report --refresh` or `omw lint` with semantic checks enabled, not on every compile (too expensive).
