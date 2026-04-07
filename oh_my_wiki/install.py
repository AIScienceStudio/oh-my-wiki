"""Install oh-my-wiki as a skill for AI coding assistants."""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Skill file locations per platform
# ---------------------------------------------------------------------------

_PLATFORM_CONFIG: dict[str, dict] = {
    "claude": {
        "skill_file": "skill.md",
        "skill_dst": Path(".claude") / "skills" / "oh-my-wiki" / "SKILL.md",
        "claude_md": True,
    },
    "codex": {
        "skill_file": "skill.md",
        "skill_dst": Path(".agents") / "skills" / "oh-my-wiki" / "SKILL.md",
        "claude_md": False,
    },
    "opencode": {
        "skill_file": "skill.md",
        "skill_dst": Path(".config") / "opencode" / "skills" / "oh-my-wiki" / "SKILL.md",
        "claude_md": False,
    },
    "claw": {
        "skill_file": "skill.md",
        "skill_dst": Path(".claw") / "skills" / "oh-my-wiki" / "SKILL.md",
        "claude_md": False,
    },
}

_SKILL_REGISTRATION = (
    "\n# oh-my-wiki\n"
    "- **oh-my-wiki** (`~/.claude/skills/oh-my-wiki/SKILL.md`) "
    "- compile raw data into personal wiki. Trigger: `/omw`\n"
    "When the user types `/omw`, invoke the Skill tool "
    'with `skill: "omw"` before doing anything else.\n'
)

_SETTINGS_HOOK = {
    "matcher": "Glob|Grep",
    "hooks": [
        {
            "type": "command",
            "command": (
                "[ -f wiki/index.md ] && "
                "echo 'oh-my-wiki: Wiki exists. Read wiki/index.md and navigate "
                "articles instead of searching raw files.' || true"
            ),
        }
    ],
}


# ---------------------------------------------------------------------------
# Global skill install (to ~/.claude/skills/)
# ---------------------------------------------------------------------------

def install(platform: str = "claude") -> None:
    """Install the skill file to the platform's skill directory."""
    if platform not in _PLATFORM_CONFIG:
        print(
            f"error: unknown platform '{platform}'. "
            f"Choose from: {', '.join(_PLATFORM_CONFIG)}",
            file=sys.stderr,
        )
        sys.exit(1)

    cfg = _PLATFORM_CONFIG[platform]
    skill_src = Path(__file__).parent / cfg["skill_file"]
    if not skill_src.exists():
        print(f"error: {cfg['skill_file']} not found — reinstall oh-my-wiki", file=sys.stderr)
        sys.exit(1)

    skill_dst = Path.home() / cfg["skill_dst"]
    skill_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(skill_src, skill_dst)
    print(f"  skill installed  ->  {skill_dst}")

    if cfg["claude_md"]:
        claude_md = Path.home() / ".claude" / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text()
            if "oh-my-wiki" in content:
                print(f"  CLAUDE.md        ->  already registered")
            else:
                claude_md.write_text(content.rstrip() + _SKILL_REGISTRATION)
                print(f"  CLAUDE.md        ->  skill registered")
        else:
            claude_md.parent.mkdir(parents=True, exist_ok=True)
            claude_md.write_text(_SKILL_REGISTRATION.lstrip())
            print(f"  CLAUDE.md        ->  created")

    print()
    print("Done. Open your AI coding assistant and type:")
    print()
    print("  /omw compile .")
    print()


# ---------------------------------------------------------------------------
# Project-level install (CLAUDE.md / AGENTS.md + hooks)
# ---------------------------------------------------------------------------

_CLAUDE_MD_SECTION = """\
## oh-my-wiki

This project has an oh-my-wiki knowledge base.

Rules:
- Before answering questions about this project's knowledge, read wiki/index.md
- Navigate wiki articles via [[wikilinks]] instead of reading raw/ files directly
- After adding new sources to raw/, suggest running `omw compile` to update the wiki
"""

_CLAUDE_MD_MARKER = "## oh-my-wiki"

_AGENTS_MD_SECTION = _CLAUDE_MD_SECTION  # Same content for all platforms


def claude_install(project_dir: Path | None = None) -> None:
    """Write oh-my-wiki section to project CLAUDE.md + PreToolUse hook."""
    target = (project_dir or Path(".")) / "CLAUDE.md"

    if target.exists():
        content = target.read_text()
        if _CLAUDE_MD_MARKER in content:
            print("oh-my-wiki already configured in CLAUDE.md")
            return
        new_content = content.rstrip() + "\n\n" + _CLAUDE_MD_SECTION
    else:
        new_content = _CLAUDE_MD_SECTION

    target.write_text(new_content)
    print(f"oh-my-wiki section written to {target.resolve()}")

    _install_hook(project_dir or Path("."))
    print()
    print("Claude Code will now check the wiki before searching raw files.")


def _install_hook(project_dir: Path) -> None:
    """Add oh-my-wiki PreToolUse hook to .claude/settings.json."""
    settings_path = project_dir / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])

    if any(h.get("matcher") == "Glob|Grep" and "oh-my-wiki" in str(h) for h in pre_tool):
        print(f"  .claude/settings.json  ->  hook already registered")
        return

    pre_tool.append(_SETTINGS_HOOK)
    settings_path.write_text(json.dumps(settings, indent=2))
    print(f"  .claude/settings.json  ->  PreToolUse hook registered")


def _uninstall_hook(project_dir: Path) -> None:
    settings_path = project_dir / ".claude" / "settings.json"
    if not settings_path.exists():
        return
    try:
        settings = json.loads(settings_path.read_text())
    except json.JSONDecodeError:
        return
    pre_tool = settings.get("hooks", {}).get("PreToolUse", [])
    filtered = [h for h in pre_tool if not (h.get("matcher") == "Glob|Grep" and "oh-my-wiki" in str(h))]
    if len(filtered) == len(pre_tool):
        return
    settings["hooks"]["PreToolUse"] = filtered
    settings_path.write_text(json.dumps(settings, indent=2))
    print(f"  .claude/settings.json  ->  PreToolUse hook removed")


def claude_uninstall(project_dir: Path | None = None) -> None:
    """Remove oh-my-wiki section from CLAUDE.md + hook."""
    target = (project_dir or Path(".")) / "CLAUDE.md"

    if not target.exists():
        print("No CLAUDE.md found — nothing to do")
        return

    content = target.read_text()
    if _CLAUDE_MD_MARKER not in content:
        print("oh-my-wiki section not found in CLAUDE.md — nothing to do")
        return

    cleaned = re.sub(
        r"\n*## oh-my-wiki\n.*?(?=\n## |\Z)",
        "",
        content,
        flags=re.DOTALL,
    ).rstrip()
    if cleaned:
        target.write_text(cleaned + "\n")
        print(f"oh-my-wiki section removed from {target.resolve()}")
    else:
        target.unlink()
        print(f"CLAUDE.md was empty after removal — deleted")

    _uninstall_hook(project_dir or Path("."))


def agents_install(project_dir: Path, platform: str) -> None:
    """Write oh-my-wiki section to AGENTS.md (Codex/OpenCode/OpenClaw)."""
    target = (project_dir or Path(".")) / "AGENTS.md"

    if target.exists():
        content = target.read_text()
        if _CLAUDE_MD_MARKER in content:
            print(f"oh-my-wiki already configured in AGENTS.md")
            return
        new_content = content.rstrip() + "\n\n" + _AGENTS_MD_SECTION
    else:
        new_content = _AGENTS_MD_SECTION

    target.write_text(new_content)
    print(f"oh-my-wiki section written to {target.resolve()}")


def agents_uninstall(project_dir: Path) -> None:
    """Remove oh-my-wiki section from AGENTS.md."""
    target = (project_dir or Path(".")) / "AGENTS.md"

    if not target.exists():
        print("No AGENTS.md found — nothing to do")
        return

    content = target.read_text()
    if _CLAUDE_MD_MARKER not in content:
        print("oh-my-wiki section not found in AGENTS.md — nothing to do")
        return

    cleaned = re.sub(
        r"\n*## oh-my-wiki\n.*?(?=\n## |\Z)",
        "",
        content,
        flags=re.DOTALL,
    ).rstrip()
    if cleaned:
        target.write_text(cleaned + "\n")
    else:
        target.unlink()
    print(f"oh-my-wiki section removed from {target.resolve()}")
