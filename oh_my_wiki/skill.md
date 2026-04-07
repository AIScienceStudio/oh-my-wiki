---
name: omw
description: compile raw data (notes, articles, papers, images) into a personal wiki with backlinks, categories, and index
trigger: /omw
---

# /omw

Compile raw data into a personal knowledge wiki. Notes, bookmarks, articles, screenshots, diary entries, papers — anything in `raw/` gets compiled into structured, interlinked markdown articles in `wiki/`.

## Usage

```
/omw compile .                    # full compile on current directory
/omw compile                      # incremental compile (default)
/omw query "..."                  # query against the wiki
/omw lint                         # run health checks
/omw ingest <url>                 # ingest a URL into raw/
```

## What You Must Do When Invoked

Follow these steps in order. Do not skip steps.

### Step 1 — Ensure oh-my-wiki is installed

```bash
PYTHON=$(which python3 2>/dev/null || echo python3)
$PYTHON -c "import oh_my_wiki" 2>/dev/null || uv pip install oh-my-wiki -q 2>&1 | tail -3
$PYTHON -c "import sys; open('.omw_python', 'w').write(sys.executable)"
```

If the import succeeds, move straight to Step 2.

**In every subsequent bash block, use `$(cat .omw_python)` as the Python interpreter.**

### Step 2 — Detect files

```bash
$(cat .omw_python) -c "
import json
from oh_my_wiki.detect import detect, detect_incremental
from oh_my_wiki.index import wiki_status
from pathlib import Path

raw = Path('raw')
wiki = Path('wiki')

if not raw.exists():
    print(json.dumps({'error': 'No raw/ directory. Run omw init first.'}))
else:
    result = detect(raw)
    result['wiki_status'] = wiki_status(wiki)
    print(json.dumps(result))
" > .omw_detect.json
```

Read `.omw_detect.json` silently and present a clean summary:

```
Corpus: X files · ~Y words
  notes:    N files
  papers:   N files
  images:   N files
Wiki: Z articles (or "empty — first compile")
```

Then act on it:
- If `total_files` is 0: stop with "No files found in raw/. Add sources with `omw ingest`."
- If `total_files` > 200 OR `total_words` > 500,000: warn about cost, ask which subfolder to process.
- If `wiki_status.exists` is true and `wiki_status.total_articles` > 0: run **incremental** compile (Step 3b).
- Otherwise: run **full** compile (Step 3a).

### Step 3a — Full Compile: Extract

**Goal**: Extract topics, entities, and summaries from every raw file.

First, check cache:

```bash
$(cat .omw_python) -c "
import json
from oh_my_wiki.cache import check_cache
from pathlib import Path

detect = json.loads(Path('.omw_detect.json').read_text())
all_files = []
for ftype, flist in detect.get('files', {}).items():
    all_files.extend(flist)

cached, uncached = check_cache(all_files)
print(json.dumps({'cached': len(cached), 'uncached': uncached, 'cached_data': cached}))
" > .omw_cache_check.json
```

Read `.omw_cache_check.json`. For uncached files, launch subagents in parallel (chunk into groups of 15-20 files per subagent).

**Each subagent must**:
1. Read the assigned raw files using the Read tool
2. For each file, extract:
   - `source_file`: the file path
   - `topics`: list of `{name, relevance: "primary"|"secondary"}`
   - `entities`: list of `{name, type: "person"|"tool"|"concept"|"organization"|"place"|"event"|"media"}`
   - `summary`: 2-4 sentence summary
   - `suggested_titles`: 2-5 article titles this source could contribute to
   - `suggested_categories`: from [people, projects, research, media, personal, technology, places, ideas]
   - `key_claims`: 3-10 specific factual claims or insights
3. For images: use vision to describe content, extract text, identify concepts
4. Output a JSON array of extraction objects

After all subagents complete, save extractions to cache:

```bash
$(cat .omw_python) -c "
import json
from oh_my_wiki.extract import save_extractions_batch
from pathlib import Path

extractions = json.loads('''PASTE_EXTRACTIONS_JSON_HERE''')
saved = save_extractions_batch(extractions)
print(f'Cached {saved} extractions')
"
```

Merge cached extractions with newly extracted ones into a single list: `all_extractions`.

### Step 3b — Incremental Compile: Detect Changes + Extract

```bash
$(cat .omw_python) -c "
import json
from oh_my_wiki.detect import detect_incremental
from pathlib import Path
result = detect_incremental(Path('raw'))
print(json.dumps(result))
" > .omw_detect.json
```

Check `new_files` — only extract those (unchanged files have cache hits). Follow the same subagent extraction process as Step 3a but only for new/modified files.

If no new files and no deleted files: print "Wiki is up to date." and stop.

### Step 4 — Plan

Single LLM call. You receive all extractions + current wiki state and decide which articles to create, update, or skip.

First, get the current index summary:

```bash
$(cat .omw_python) -c "
import json
from oh_my_wiki.article import list_articles
from pathlib import Path
wiki = Path('wiki')
articles = list_articles(wiki) if wiki.exists() else []
summary = [{'title': a.title, 'categories': a.categories, 'summary': ''} for a in articles]
print(json.dumps(summary))
" > .omw_existing.json
```

Now plan. For each extraction, decide:
- **create**: New article needed (topic not yet covered). Include title, sources, categories, outline.
- **update**: Existing article needs new info. Include title, new_sources, reason.
- **stub**: Forward reference with no source material. Include title, reason.
- **no_action**: Source doesn't warrant a standalone article.

Output your plan as JSON matching this schema:

```json
{
  "articles": [
    {"title": "...", "action": "create|update|stub", "sources": [...], "categories": [...], "outline": "..."},
  ],
  "no_action": [
    {"source": "raw/...", "reason": "..."}
  ]
}
```

Validate the plan:

```bash
$(cat .omw_python) -c "
import json
from oh_my_wiki.compile import validate_plan
plan = json.loads('''PASTE_PLAN_JSON_HERE''')
errors = validate_plan(plan)
if errors:
    print('ERRORS: ' + '; '.join(errors))
else:
    print('Plan valid: ' + str(len(plan['articles'])) + ' articles')
"
```

Present the plan to the user:
```
Plan:
  Create: N articles
  Update: N articles
  Stubs:  N
  No action: N sources
```

### Step 5 — Write Articles

Launch subagents in parallel to write articles. Batch by action:

**Batch 1 — Create** (parallel subagents, 3-5 articles each):
Each subagent receives:
1. The plan entries for its assigned articles
2. The raw source files (read them)
3. The list of ALL article titles (existing + planned) for `[[wikilinks]]`
4. Instructions to write each article with:
   - YAML frontmatter (title, aliases, created, updated, sources, categories, tags, confidence, word_count, backlink_count: 0, status: active)
   - `# Title`
   - `> One-line summary`
   - `## Overview` (2-3 paragraphs)
   - `## Key Concepts` (if technical)
   - `## Connections` (wikilinks to related articles)
   - `## Sources` (raw file paths)
   - `## Notes` (optional observations)

**Batch 2 — Update** (parallel subagents):
Each subagent receives:
1. The existing article text (read the file)
2. The new source material (read the raw file)
3. The reason for update
4. All article titles for wikilinks
5. Instructions to merge new info into existing sections, update timestamp, preserve `## User Notes`

**After both batches complete**, save articles:

```bash
$(cat .omw_python) -c "
import json
from oh_my_wiki.compile import write_articles_from_plan, detect_needed_stubs, create_stub
from oh_my_wiki.article import save_article, list_articles
from pathlib import Path

wiki = Path('wiki')
plan = json.loads('''PASTE_PLAN_JSON_HERE''')
article_texts = json.loads('''PASTE_ARTICLE_TEXTS_JSON_HERE''')
existing_titles = {a.title for a in list_articles(wiki)} if wiki.exists() else set()

changes = write_articles_from_plan(plan, article_texts, wiki)

# Detect and create stubs for forward references
stubs = detect_needed_stubs(plan, article_texts, existing_titles)
for stub_entry in stubs:
    stub = create_stub(stub_entry['title'], reason=stub_entry.get('reason', ''))
    save_article(wiki, stub)
    changes.append({'action': 'stub', 'article': stub_entry['title']})

print(json.dumps({'changes': changes, 'total': len(changes)}))
"
```

### Step 6 — Index + Report

```bash
$(cat .omw_python) -c "
from oh_my_wiki.index import rebuild_index
from pathlib import Path
stats = rebuild_index(Path('wiki'))
print(f\"Indexed {stats['total_articles']} articles in {stats['total_categories']} categories\")
"
```

### Step 7 — Update Manifest

```bash
$(cat .omw_python) -c "
import json
from datetime import datetime, timezone
from oh_my_wiki.manifest import load, save, update_from_compile
from oh_my_wiki.compile import save_compile_log, create_compile_log
from pathlib import Path

manifest = load()
changes = json.loads('''PASTE_CHANGES_JSON_HERE''')
compile_log = create_compile_log(mode='full', changes=changes)
save_compile_log(compile_log)
save(manifest)
print('Compile complete.')
"
```

### Final Summary

Present:
```
Compiled wiki:
  Created: N articles
  Updated: N articles
  Stubs: N
  Total: N articles in wiki/

Open wiki/ in Obsidian to browse, or run /omw query "..." to ask questions.
```

## /omw query

When the user runs `/omw query "question"`:

1. Read `wiki/index.md` to get the full article catalog
2. Identify the 3-5 most relevant articles based on the question and the titles/categories/descriptors in the index
3. Read those articles
4. Follow `[[wikilinks]]` in the Connections sections if they point to relevant content (max 2 hops)
5. Synthesize an answer citing specific articles with `[[wikilinks]]`
6. If `--file-back` was specified:

```bash
$(cat .omw_python) -c "
from oh_my_wiki.article import Article, save_article
from oh_my_wiki.index import rebuild_index
from pathlib import Path
from datetime import datetime, timezone
import re

question = '''QUESTION_HERE'''
answer = '''ANSWER_HERE'''
source_articles = '''SOURCE_ARTICLES_LIST'''

now = datetime.now(timezone.utc)
slug = re.sub(r'[^\w]', '_', question[:50].lower()).strip('_')
title = f'Q: {question[:80]}'

article = Article(
    title=title,
    body=f'# {title}\n\n> Query result filed back into wiki.\n\n## Answer\n\n{answer}\n\n## Source Articles\n\n{source_articles}',
    categories=['queries'],
    confidence='medium',
    status='active',
)

queries_dir = Path('wiki/_queries')
queries_dir.mkdir(exist_ok=True)
path = queries_dir / f\"{now.strftime('%Y%m%d')}_{slug}.md\"
path.write_text(article.to_markdown())
rebuild_index(Path('wiki'))
print(f'Filed back as: {path}')
"
```

## /omw lint

Run `omw lint` via bash and present results. If `--fix` is specified, also run auto-fixes.

## /omw ingest

```bash
$(cat .omw_python) -m oh_my_wiki.ingest URL_OR_PATH raw/
```

After ingesting, suggest running `/omw compile` to update the wiki.
