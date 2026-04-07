"""Tests for analyze.py — WIKI_REPORT.md generation."""
from pathlib import Path

from oh_my_wiki.article import Article, save_article
from oh_my_wiki.analyze import generate_report, save_report
from oh_my_wiki.index import rebuild_index


def _create_wiki(wiki_dir):
    wiki_dir.mkdir(exist_ok=True)
    save_article(wiki_dir, Article(
        title="Machine Learning",
        body="# Machine Learning\n\n> ML overview.\n\n## Connections\n\n- [[Python]]",
        categories=["research"],
        confidence="high",
        sources=["raw/ml.md"],
    ))
    save_article(wiki_dir, Article(
        title="Python",
        body="# Python\n\n> A language.\n\n## Connections\n\n- [[Machine Learning]]",
        categories=["technology"],
        confidence="high",
    ))
    save_article(wiki_dir, Article(
        title="Orphan Topic",
        body="# Orphan Topic\n\n> No links to this.",
        categories=["uncategorized"],
        confidence="low",
        status="active",
    ))
    rebuild_index(wiki_dir)


class TestGenerateReport:
    def test_basic(self, tmp_path):
        wiki = tmp_path / "wiki"
        _create_wiki(wiki)

        report = generate_report(wiki)
        assert "Wiki Report" in report
        assert "3 articles" in report
        assert "## Hub Articles" in report
        assert "## Health" in report

    def test_empty_wiki(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        report = generate_report(wiki)
        assert "Empty wiki" in report

    def test_with_raw_dir(self, tmp_path):
        wiki = tmp_path / "wiki"
        raw = tmp_path / "raw"
        raw.mkdir()
        (raw / "note.md").write_text("some content here with multiple words")
        _create_wiki(wiki)

        report = generate_report(wiki, raw_dir=raw)
        assert "Raw corpus" in report

    def test_coverage_gaps(self, tmp_path):
        wiki = tmp_path / "wiki"
        _create_wiki(wiki)
        # Add a stub
        save_article(wiki, Article(
            title="Stub Topic",
            body="# Stub\n\n> Stub.",
            status="stub",
            confidence="low",
        ))
        rebuild_index(wiki)

        report = generate_report(wiki)
        assert "Coverage Gaps" in report
        assert "stub" in report.lower()


class TestSaveReport:
    def test_writes_file(self, tmp_path):
        wiki = tmp_path / "wiki"
        _create_wiki(wiki)

        path = save_report(wiki)
        assert path.exists()
        assert "WIKI_REPORT" in path.name
        assert "Wiki Report" in path.read_text()
