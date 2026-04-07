# 08 — Edge Cases, Open Questions & Missing Details

## 1. YAML Frontmatter Parser (No PyYAML)

Every module depends on `article.py` parsing frontmatter. We need a stdlib-only parser.

### Subset to Support

oh-my-wiki frontmatter is well-structured (we control the output), so we only need:

```
Scalars:     title: "Transformer Architecture"    → str
             confidence: high                      → str
             word_count: 1250                      → int
             backlink_count: 7                     → int
Dates:       created: 2024-03-15T10:30:00Z        → str (keep as ISO string)
Lists:       sources:                              → list[str]
               - raw/papers/paper.pdf
               - raw/articles/article.md
             tags:                                 → list[str]
               - neural-networks
               - attention
Inline list: aliases: ["transformers", "the transformer"]  → list[str]
```

### NOT needed

- Nested dicts/objects
- Multi-line strings (`|`, `>`)
- Anchors/aliases (`&`, `*`)
- Flow mappings (`{key: val}`)
- Comments mid-value
- Type coercion beyond str/int

### Parser spec

```python
def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown text.
    
    Returns (metadata_dict, body_text_after_frontmatter).
    If no frontmatter (no leading ---), returns ({}, full_text).
    """

def render_frontmatter(meta: dict) -> str:
    """Render a metadata dict back to YAML frontmatter string.
    
    Lists render as:
      - block style for 1+ items
      - inline [] style for aliases (Obsidian prefers this)
    Strings with special chars get quoted.
    """
```

~60 lines of code. Test against all article fixtures.

## 2. Image Handling

### During Ingestion

Images copied to `raw/` as-is (binary files). No frontmatter injected into images — instead, a companion `.md` sidecar is created:

```
raw/
  screenshot-2024-03-20.png       # Binary image
  screenshot-2024-03-20.png.md    # Sidecar with metadata
```

Sidecar:
```yaml
---
source_file: screenshot-2024-03-20.png
type: image
captured_at: 2024-03-20T10:30:00Z
contributor: "me"
---
Image: screenshot-2024-03-20.png
```

### During Extraction

LLM uses vision to describe the image. Extraction output:
```json
{
  "source_file": "raw/screenshot-2024-03-20.png",
  "topics": [{"name": "UI Design", "relevance": "primary"}],
  "entities": [{"name": "Landing Page Mockup", "type": "concept"}],
  "summary": "Screenshot of a landing page mockup with gradient background, hero text...",
  "image_description": "Full visual description for article prose"
}
```

### In Wiki Articles

Images are referenced but NOT copied to `wiki/`. Articles use relative paths back to `raw/`:

```markdown
## Sources
- `raw/screenshot-2024-03-20.png` — landing page mockup screenshot
```

For Obsidian rendering, users can configure Obsidian to also scan `raw/` or create symlinks. oh-my-wiki does NOT manage Obsidian vault configuration.

### Future: Image Embedding

Phase 3+ option: `omw compile --copy-images` copies referenced images into `wiki/_assets/` and uses Obsidian embed syntax `![[_assets/screenshot.png]]`.

## 3. Error Recovery During Compilation

### Atomic Article Writes

Each article is written via atomic file operations (write to tmp, then `os.replace()`). If compilation crashes mid-way:
- Already-written articles are valid and complete
- Partially-written articles don't exist (tmp file gets orphaned)
- Index may be stale (but `omw lint --fix` rebuilds it)

### Compile Log as Checkpoint

The compile-log is updated incrementally during compilation:
```json
{
  "status": "in_progress",
  "completed": ["Article A", "Article B"],
  "pending": ["Article C", "Article D"],
  "failed": []
}
```

On next `omw compile`, check for `status: in_progress`:
- Resume from where it left off (skip completed, retry pending)
- User can also `omw compile --full` to start over

### Manifest Consistency

Manifest is only updated AFTER all articles are successfully written. If compile crashes before manifest update, next run re-detects everything and re-plans (slightly wasteful but safe — cached extractions still save most work).

## 4. Manual Edits to Wiki Articles

### Policy: LLM-Maintained, User-Readable

The wiki is the LLM's domain (Karpathy: "I rarely touch it directly"). However, we should handle the case where a user does edit.

### Detection

During incremental compile, before updating an article:
1. Compare article's current SHA256 against the hash stored in manifest
2. If different AND the article wasn't scheduled for update → user edited it
3. Options:
   - **Default**: Warn and skip: "Article 'X' was manually modified. Skipping update. Use --force to overwrite."
   - **--force**: Overwrite manual edits with compiled version
   - **--merge**: LLM merges manual edits with new compiled content (Phase 2+)

### `## User Notes` section

Convention: if users want to add content that survives compilation, add a `## User Notes` section. The compiler preserves this section during updates.

## 5. Article Rename / Title Change

### When It Happens

Incremental compile may decide an article's title should change (e.g., new source reveals better name).

### Strategy

1. **Compile creates new article** with the new title
2. **Old article becomes a redirect**: content replaced with frontmatter `redirect: "New Title"` + body `→ See [[New Title]]`
3. **Lint detects redirect articles** and suggests cleanup: update all `[[Old Title]]` references to `[[New Title]]`, then delete redirect
4. This keeps backlinks working until cleanup

Alternatively (simpler for MVP): titles are immutable once created. Compiler only updates content, never renames.

## 6. Git Workflow

### What to Commit

| Directory | Commit? | Why |
|-----------|---------|-----|
| `raw/` | Yes | User's source data, valuable |
| `wiki/` | Yes | The compiled knowledge base, useful for history |
| `.omw/cache/` | No (gitignore) | Derivable from raw/, large |
| `.omw/manifest.json` | Yes | Small, tracks state |
| `.omw/compile-log.json` | Optional | Useful for debugging |
| `.omw/wiki-snapshot.json` | No (gitignore) | Derivable |

### `.gitignore` template (created by `omw init`)

```
.omw/cache/
.omw/wiki-snapshot.json
```

### Merge Conflicts

Since wiki/ is auto-generated, merge conflicts in wiki articles should be resolved by re-running `omw compile --full`. The source of truth is `raw/` + `manifest.json`.

## 7. Sensitive Data Handling

### Problem

oh-my-wiki handles PERSONAL data (diaries, conversations, names of friends). Unlike graphify (which processes code), there's a risk of sensitive info leaking into wiki articles in unexpected ways.

### Approach

1. **No automatic filtering**: Unlike graphify's sensitive file patterns, oh-my-wiki doesn't filter raw files — the user explicitly chose to ingest them.

2. **Confidence as a signal**: Articles compiled from sensitive sources (diary, conversations) get `confidence: medium` or `low` — the LLM should avoid stating personal details as facts.

3. **`--private` flag on ingest**: Mark a raw file as private. Private sources contribute to articles but are not listed by filename in the Sources section — just "private source."

4. **Wiki stays local**: oh-my-wiki never uploads content anywhere. The wiki is local files. Users decide whether to commit to git, share, etc.

5. **Future: redaction rules**: Config file listing patterns (names, phone numbers) to redact from wiki output.

## 8. Raw Directory Organization

### Policy: Users Organize However They Want

`raw/` can have any subdirectory structure:
```
raw/
  diary/2024-01.md
  papers/attention.pdf
  screenshots/whiteboard.png
  notes/meeting.md
  raw-dump-everything-here.md
```

`detect.py` walks `raw/` recursively (same as graphify's `os.walk`). Subdirectory names don't affect classification — file extension and content heuristics determine type.

### Subdirectory hints

If a subdirectory is named `papers/`, `diary/`, `notes/`, etc., the compiler can use this as a classification hint (but not override the heuristic).

## 9. Scale Limits

### Target Scale

- **Sweet spot**: 50-500 articles, 50K-500K words
- **Works well**: Up to ~1,000 articles, ~1M words
- **Degrades**: Beyond ~1,000 articles, index.md becomes too large for a single agent read

### Graceful Degradation

At >500 articles:
- Index.md shows only top 20 per category (with "... and N more" links to category pages)
- Category pages become the primary navigation (agents read category first, then drill)
- `omw compile` warns: "Large wiki (N articles). Consider using `omw query` with `--budget` to limit context."

At >1,000 articles:
- Recommend splitting into sub-wikis (e.g., `research-wiki/`, `personal-wiki/`)
- Or: introduce section indexes (e.g., `wiki/_sections/ml/index.md`) — mini index pages for major topic areas
- This is where graphify's graph approach may become complementary

### Future: Tiered Index

For very large wikis, replace flat index.md with:
```
index.md          → links to section indexes
_sections/
  ml/index.md     → Machine Learning section (50 articles)
  people/index.md → People section (80 articles)
  ...
```

Agent navigates: index.md → section index → article. One extra hop but keeps context manageable.

## 10. Obsidian Compatibility Details

### Vault Setup

oh-my-wiki does NOT create `.obsidian/` config. User opens `wiki/` as an Obsidian vault manually.

### Recommended Obsidian Settings (documented in README)

- **Files & Links**: Use `[[Wikilinks]]` (default)
- **Default location for new attachments**: Set to `_assets` if using `--copy-images`
- **Graph view**: Works out of the box — articles are nodes, wikilinks are edges
- **Tags pane**: Works with frontmatter `tags` field
- **Backlinks pane**: Works with `[[wikilinks]]`

### What Renders Well

| Feature | Renders in Obsidian | Renders in GitHub/other |
|---------|-------------------|----------------------|
| `[[wikilinks]]` | Yes (clickable) | Shows as plain text `[[wikilinks]]` |
| Frontmatter | Yes (properties panel) | Rendered as YAML block |
| `> blockquote summary` | Yes (styled) | Yes (styled) |
| Tags in frontmatter | Yes (searchable) | No |
| Category page links | Yes (if `_categories/` in vault) | Broken (relative path) |

### Aliases

Obsidian resolves aliases automatically when using `[[alias]]` if the target article has `aliases: [...]` in frontmatter. This means `[[transformers]]` resolves to "Transformer Architecture" without any extra work.

## 11. Ingest Deduplication

### URL Deduplication

On `omw ingest <url>`:
1. Check if `raw/` already contains a file with matching `source_url` in frontmatter
2. If found: "Already ingested: raw/existing-file.md (use --force to re-fetch)"
3. If `--force`: re-fetch and overwrite

### Content Deduplication

On `omw ingest <local-file>`:
1. SHA256 of file content
2. Check against all existing raw file hashes in manifest
3. If match: "Duplicate content already exists as: raw/existing-file.md"

### Near-Duplicate Detection

Phase 2+: During lint, LLM compares raw files with similar content_hash prefixes or similar titles to suggest merges.

## 12. Coexistence with graphify

### No Conflict

graphify outputs to `graphify-out/`. oh-my-wiki outputs to `wiki/` and `.omw/`. No overlapping files.

### Complementary Usage

A user could run both on the same `raw/` directory:
- graphify: structural knowledge graph, community detection, god nodes
- oh-my-wiki: prose wiki articles, categories, backlinks

The graphify graph and oh-my-wiki articles would cover the same data from different angles. A future integration could:
- Use graphify's community labels as oh-my-wiki categories
- Use graphify's god nodes as oh-my-wiki hub articles
- Link graphify's GRAPH_REPORT.md from oh-my-wiki's index.md

This is not in scope for MVP but the directory layout ensures no conflicts.

## 13. Non-English Content

### Policy

oh-my-wiki is language-agnostic. The LLM handles extraction and compilation in whatever language the source material uses.

### Considerations

- Article titles: use the dominant language of the source
- Mixed-language sources: the LLM should compile in the language of the majority of sources (or user preference)
- `omw init --lang en` (future): set preferred wiki language in config
- Frontmatter keywords (`title`, `categories`, etc.) are always in English — only content/titles vary
