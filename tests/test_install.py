"""Tests for install.py — project-level install/uninstall."""
from pathlib import Path

from oh_my_wiki.install import claude_install, claude_uninstall


class TestClaudeInstall:
    def test_creates_claude_md(self, tmp_path):
        claude_install(tmp_path)
        claude_md = tmp_path / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "oh-my-wiki" in content
        assert "wiki/index.md" in content

    def test_appends_to_existing(self, tmp_path):
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("## Existing Section\n\nSome content.\n")
        claude_install(tmp_path)
        content = claude_md.read_text()
        assert "Existing Section" in content
        assert "oh-my-wiki" in content

    def test_idempotent(self, tmp_path):
        claude_install(tmp_path)
        claude_install(tmp_path)  # Should not duplicate
        content = (tmp_path / "CLAUDE.md").read_text()
        assert content.count("oh-my-wiki") == 2  # heading + one reference

    def test_creates_hook(self, tmp_path):
        claude_install(tmp_path)
        settings = tmp_path / ".claude" / "settings.json"
        assert settings.exists()
        import json
        data = json.loads(settings.read_text())
        hooks = data.get("hooks", {}).get("PreToolUse", [])
        assert any("oh-my-wiki" in str(h) for h in hooks)


class TestClaudeUninstall:
    def test_removes_section(self, tmp_path):
        claude_install(tmp_path)
        claude_uninstall(tmp_path)
        claude_md = tmp_path / "CLAUDE.md"
        if claude_md.exists():
            assert "oh-my-wiki" not in claude_md.read_text()

    def test_noop_if_not_installed(self, tmp_path):
        claude_uninstall(tmp_path)  # Should not raise
