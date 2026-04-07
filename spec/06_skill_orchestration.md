# 06 — Skill & LLM Orchestration

## Architecture

oh-my-wiki is a **skill** — a Python library paired with a `skill.md` file that instructs the host LLM agent (Claude Code, Codex, OpenCode, OpenClaw, ClawPy) how to orchestrate the pipeline.

This is the same architecture as graphify:
- Python code handles deterministic work (file I/O, caching, frontmatter, indexing)
- `skill.md` tells the LLM what steps to follow, what subagents to launch, what prompts to use
- The host agent provides the intelligence (extraction, planning, writing, merging)

### Why skill, not standalone app?

1. **No API key management** — the host agent already has API access
2. **No streaming/SSE code** — the host agent handles LLM communication
3. **Subagent parallelism for free** — Claude Code's Agent tool, Codex's parallel agents
4. **Tool reuse** — the host agent can read files, search, write — oh-my-wiki doesn't need to implement these
5. **Platform portability** — same Python library works with any host that supports skills

### Future: Standalone mode via ClawPy

When oh-my-wiki needs to run without a host agent (e.g., cron job, CI pipeline), it can use ClawPy as the LLM backend. ClawPy provides:
- Multi-model support (Anthropic, OpenAI, Gemini, Ollama, DeepSeek)
- Tool system (file read/write/edit, bash, grep, glob)
- Engine with agentic loop
- Provider-agnostic API

This is a Phase 3+ feature. For MVP, oh-my-wiki is skill-only.

## skill.md Structure

The skill.md follows graphify's proven format: trigger, steps, prompts, output expectations.

### Trigger

```
/omw compile .       → full compile on current directory
/omw compile         → incremental compile
/omw query "..."     → query against wiki
/omw lint            → run health checks
/omw ingest <url>    → ingest a URL
```

### Step-by-Step Orchestration (Compile)

```markdown
### Step 1 — Ensure oh-my-wiki is installed

[Same pattern as graphify: detect Python, check import, pip install if needed]

### Step 2 — Detect files

python3 -c "
from oh_my_wiki.detect import detect
from pathlib import Path
import json
result = detect(Path('raw'))
print(json.dumps(result))
"

Present clean summary:
  Raw corpus: X files · ~Y words
    notes:    N files
    articles: N files
    papers:   N files
    images:   N files

### Step 3 — Check for existing wiki

python3 -c "
from oh_my_wiki.index import wiki_status
from pathlib import Path
import json
result = wiki_status(Path('wiki'))
print(json.dumps(result))
"

If wiki exists: run incremental compile (Step 4b)
If no wiki: run full compile (Step 4a)

### Step 4a — Full Compile: Extract

Launch N subagents in parallel (chunk raw files into groups of 15-20).

Each subagent:
1. Reads assigned raw files
2. Extracts topics, entities, summary, suggested_titles per file
3. Outputs JSON extraction results

After all subagents complete:

python3 -c "
from oh_my_wiki.cache import save_cached
from pathlib import Path
import json
# Save each extraction to cache
extractions = json.loads('''[EXTRACTION_RESULTS]''')
for ext in extractions:
    save_cached(Path(ext['source_file']), ext)
"

### Step 4b — Incremental Compile: Detect Changes + Extract

python3 -c "
from oh_my_wiki.detect import detect_incremental
from pathlib import Path
import json
result = detect_incremental(Path('raw'))
print(json.dumps(result))
"

Only extract new/modified files. Cache hits for unchanged.

### Step 5 — Plan

Single LLM call:
- Input: all extractions + current index.md + manifest
- Output: compilation plan JSON

python3 -c "
from oh_my_wiki.compile import validate_plan
import json
plan = json.loads('''[PLAN_JSON]''')
validate_plan(plan)
print(json.dumps(plan))
"

Present plan to user:
  Create: 3 articles
  Update: 2 articles
  Stubs:  1
  No action: 2 raw files (absorbed into updates)

### Step 6 — Write Articles

Launch subagents in parallel:
- Batch 1: All "create" articles (parallel)
- Batch 2: All "update" articles (parallel, can overlap with batch 1)
- Batch 3: All "stub" articles (after batches 1-2 complete)

Each subagent:
1. Receives plan entry + raw source files + list of existing article titles
2. Writes article following the template from spec 02
3. Outputs the article markdown

Save each article:

python3 -c "
from oh_my_wiki.article import save_article
from pathlib import Path
save_article(Path('wiki'), title='...', content='''...''')
"

### Step 7 — Index + Report

python3 -c "
from oh_my_wiki.index import rebuild_index
from oh_my_wiki.analyze import generate_report
from pathlib import Path
wiki = Path('wiki')
stats = rebuild_index(wiki)
report = generate_report(wiki)
Path(wiki / 'WIKI_REPORT.md').write_text(report)
print(f'Indexed {stats[\"total_articles\"]} articles in {stats[\"total_categories\"]} categories')
"

### Step 8 — Update State

python3 -c "
from oh_my_wiki.manifest import update_manifest
from oh_my_wiki.diff import save_snapshot
from pathlib import Path
update_manifest(Path('.omw'), plan, extractions)
save_snapshot(Path('.omw'), Path('wiki'))
"

Present final summary.
```

## Multi-Platform Support

### Claude Code

- **Skill file**: `~/.claude/skills/oh-my-wiki/SKILL.md`
- **CLAUDE.md section**: Tells Claude to check wiki/ before searching raw/ for context
- **PreToolUse hook**: On Glob/Grep, suggests reading wiki/index.md first

```python
# .claude/settings.json hook
{
    "matcher": "Glob|Grep",
    "hooks": [{
        "type": "command",
        "command": "[ -f wiki/index.md ] && echo 'oh-my-wiki: Wiki exists. Read wiki/index.md and navigate articles instead of searching raw files.' || true"
    }]
}
```

### Codex / OpenCode / OpenClaw

- **Skill file**: Platform-specific location
- **AGENTS.md section**: Same rules as CLAUDE.md but in AGENTS.md format

### ClawPy (Future)

- ClawPy can load oh-my-wiki as a tool/skill directly
- Uses ClawPy's engine for LLM calls instead of relying on host agent
- Enables: `omw compile --engine clawpy --model claude-sonnet`

## Install/Uninstall Commands

Follows graphify's exact pattern:

```python
# __main__.py
elif cmd == "install":
    install(platform=platform)
elif cmd == "claude":
    if subcmd == "install":
        claude_install()      # CLAUDE.md + PreToolUse hook
    elif subcmd == "uninstall":
        claude_uninstall()
elif cmd in ("codex", "opencode", "claw"):
    if subcmd == "install":
        agents_install(Path("."), cmd)
    elif subcmd == "uninstall":
        agents_uninstall(Path("."))
```

## Token Efficiency

### Compile Cost Model

| Operation | LLM Calls | Tokens (approx) |
|-----------|-----------|-----------------|
| Extract 50 raw files (first run) | 3 subagents × ~2K input | ~30K input, ~10K output |
| Plan (50 files → 40 articles) | 1 call, ~5K input | ~5K input, ~2K output |
| Write 40 articles | 3 subagents × ~3K input | ~36K input, ~40K output |
| **Full compile total** | ~10 LLM calls | ~70K input, ~52K output |

| Operation | LLM Calls | Tokens (approx) |
|-----------|-----------|-----------------|
| Incremental: 1 new file | 1 extract + 1 plan + 1 write | ~5K input, ~3K output |

### Query Cost Model

| Operation | LLM Calls | Tokens (approx) |
|-----------|-----------|-----------------|
| Read index.md | 0 (agent reads file) | ~2K context |
| Read 3 articles | 0 (agent reads files) | ~6K context |
| Synthesize answer | Part of agent's turn | ~1K output |
| **Total per query** | 0 additional | ~8K context consumed |

This is the key advantage of the wiki structure: queries are essentially free (just file reads). Compare to graphify's query which requires BFS/DFS graph traversal calls.
