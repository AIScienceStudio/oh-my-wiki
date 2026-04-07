# 10 — ClawPy Integration (Standalone Mode)

## Problem

oh-my-wiki's default mode is as a **skill** — the host agent (Claude Code, Codex, etc.) provides LLM intelligence. But sometimes you want to run oh-my-wiki without a host agent:

- **Cron jobs**: Auto-compile nightly when raw/ changes
- **CI/CD**: Compile wiki as part of a build pipeline
- **CLI-only**: User doesn't have Claude Code, just wants to run `omw compile`
- **Batch processing**: Ingest + compile 100 sources in one shot
- **Different models**: Use GPT-4, Gemini, or a local model instead of Claude

## Solution: ClawPy as Backend

ClawPy (`/home/projects/claude-exp/clawpy`) is a multi-model CLI coding agent — a Python rewrite of Claude Code. It provides:

- **Provider layer**: Anthropic, OpenAI, Gemini, Ollama, DeepSeek (all via direct HTTP, no SDK deps)
- **Engine**: Agentic loop with tool execution, token budgets, auto-compact
- **Tool system**: File read/write/edit, bash, grep, glob, web fetch
- **Streaming**: Async SSE parser, works with all providers

oh-my-wiki can use ClawPy's provider + engine as its LLM backend for standalone operation.

## Architecture

### Skill Mode (Default)

```
User  →  Claude Code  →  skill.md instructions  →  oh-my-wiki Python functions
                ↓
         Claude API (via host agent)
```

### Standalone Mode (via ClawPy)

```
User  →  omw compile --engine clawpy  →  oh-my-wiki Python functions
                                              ↓
                                         ClawPy Engine
                                              ↓
                                         Provider (Anthropic/OpenAI/Gemini/Ollama/DeepSeek)
```

## Integration Points

### 1. Provider Access

oh-my-wiki needs LLM calls for three operations:
- **Extract**: Read raw file → produce structured JSON
- **Plan**: Read extractions + index → produce compilation plan
- **Write**: Read raw sources + plan → produce article markdown

In skill mode, the host agent does these. In standalone mode, oh-my-wiki calls ClawPy:

```python
# oh_my_wiki/engine.py (new module for standalone mode)

from clawpy.provider.registry import create as create_provider
from clawpy.config.config import Config

async def llm_call(prompt: str, model: str | None = None) -> str:
    """Make a single LLM call via ClawPy's provider layer."""
    config = Config()
    if model:
        config.model = model
    provider = create_provider(config.provider, config.provider_config())
    # Simple single-turn call, no tool use needed
    response = await provider.send([{"role": "user", "content": prompt}])
    return response.text
```

### 2. Parallel Extraction via ClawPy Agents

For extraction (15-20 files per batch), oh-my-wiki can use ClawPy's agent tool:

```python
# oh_my_wiki/engine.py

async def parallel_extract(files: list[Path], batch_size: int = 15) -> list[dict]:
    """Extract from multiple files in parallel using ClawPy."""
    batches = [files[i:i+batch_size] for i in range(0, len(files), batch_size)]
    tasks = [llm_call(build_extraction_prompt(batch)) for batch in batches]
    results = await asyncio.gather(*tasks)
    return [json.loads(r) for r in results]
```

### 3. Tool Reuse

ClawPy's tools can be used by oh-my-wiki's standalone engine:

| ClawPy Tool | oh-my-wiki Use |
|-------------|---------------|
| `FileReadTool` | Read raw files for extraction prompts |
| `FileWriteTool` | Write compiled articles |
| `FileEditTool` | Update existing articles during incremental compile |
| `GrepTool` | Search wiki for backlink references |
| `GlobTool` | Find files matching patterns |
| `WebFetchTool` | Ingest URLs directly |

### 4. Configuration

```bash
# Use default provider (from clawpy config or ANTHROPIC_API_KEY)
omw compile --engine clawpy

# Specify model
omw compile --engine clawpy --model claude-sonnet-4-6

# Use OpenAI
omw compile --engine clawpy --provider openai --model gpt-4o

# Use local model
omw compile --engine clawpy --provider ollama --model llama3

# Environment variables (same as clawpy)
ANTHROPIC_API_KEY=sk-... omw compile --engine clawpy
OPENAI_API_KEY=sk-... omw compile --engine clawpy --provider openai
```

## Dependency Structure

ClawPy is an **optional dependency**, not required:

```toml
[project.optional-dependencies]
standalone = ["clawpy"]
all = ["pypdf", "html2text", "watchdog", "clawpy"]
```

```python
# oh_my_wiki/engine.py
try:
    from clawpy.provider.registry import create as create_provider
    from clawpy.config.config import Config
    CLAWPY_AVAILABLE = True
except ImportError:
    CLAWPY_AVAILABLE = False

def ensure_clawpy():
    if not CLAWPY_AVAILABLE:
        raise ImportError(
            "Standalone mode requires clawpy. Install with: pip install oh-my-wiki[standalone]"
        )
```

## Module: `oh_my_wiki/engine.py`

New module added for standalone mode:

```python
"""LLM engine for standalone mode (no host agent). Uses ClawPy as backend."""

class WikiEngine:
    """Manages LLM calls for extraction, planning, and article writing."""
    
    def __init__(self, provider: str = "anthropic", model: str | None = None):
        ensure_clawpy()
        self.config = Config()
        self.config.provider = provider
        if model:
            self.config.model = model
        self.provider = create_provider(provider, self.config.provider_config())
    
    async def extract(self, files: list[Path]) -> list[dict]:
        """Extract topics/entities from raw files."""
        ...
    
    async def plan(self, extractions: list[dict], wiki_dir: Path) -> dict:
        """Generate compilation plan."""
        ...
    
    async def write_article(self, plan_entry: dict, sources: list[Path]) -> str:
        """Write a single article from plan + sources."""
        ...
    
    async def update_article(self, existing: str, new_sources: list[Path], reason: str) -> str:
        """Merge new information into existing article."""
        ...
```

## CLI Integration

```python
# __main__.py additions

def _get_engine(args) -> WikiEngine | None:
    """Get standalone engine if --engine flag is set."""
    if hasattr(args, 'engine') and args.engine == 'clawpy':
        from oh_my_wiki.engine import WikiEngine
        return WikiEngine(
            provider=getattr(args, 'provider', 'anthropic'),
            model=getattr(args, 'model', None),
        )
    return None  # Skill mode — host agent handles LLM calls

# In compile command:
engine = _get_engine(args)
if engine:
    # Standalone: use engine for extract/plan/write
    asyncio.run(standalone_compile(engine, raw_dir, wiki_dir))
else:
    # Skill mode: print instructions for host agent
    print_skill_instructions(raw_dir, wiki_dir)
```

## Comparison: Skill vs Standalone

| Aspect | Skill Mode | Standalone (ClawPy) |
|--------|-----------|-------------------|
| LLM calls | Host agent (free, already running) | Direct API calls (costs tokens) |
| Parallelism | Host agent's subagent system | asyncio.gather on provider calls |
| Tool access | Host agent's tools (read, write, grep, etc.) | ClawPy's tool registry |
| Model | Whatever host agent uses | User-configurable (any provider) |
| Setup | Just `omw install` | Need API key + `pip install oh-my-wiki[standalone]` |
| Best for | Interactive use in IDE | Automation, CI/CD, cron, batch |

## Implementation Phase

This is **Phase 4** (Advanced). Not in MVP.

Implementation order:
1. `oh_my_wiki/engine.py` — WikiEngine class with ClawPy provider integration
2. Update `__main__.py` — Add `--engine`, `--provider`, `--model` flags
3. Update `compile.py` — Accept optional engine parameter
4. Update `query.py` — Accept optional engine for standalone query mode
5. Tests with mocked provider

## ClawPy Promotion

The clawpy integration naturally promotes clawpy:
- oh-my-wiki README mentions clawpy as the standalone backend
- `pip install oh-my-wiki[standalone]` pulls in clawpy
- Users discover clawpy as a general-purpose multi-model agent through oh-my-wiki
- Both projects reference each other in their READMEs

This creates a small ecosystem:
```
graphify  — knowledge graph extraction
oh-my-wiki — wiki compilation  
clawpy    — multi-model agent engine (powers standalone oh-my-wiki)
```
