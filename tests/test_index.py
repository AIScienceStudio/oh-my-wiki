"""Tests for index.py — index generation and hub ranking."""
from pathlib import Path

from oh_my_wiki.article import Article, save_article
from oh_my_wiki.index import hub_articles, rebuild_index, wiki_status


def _create_sample_wiki(wiki_dir: Path) -> None:
    """Create a small wiki for testing."""
    save_article(wiki_dir, Article(
        title="Machine Learning",
        body="# Machine Learning\n\n> Overview of ML.\n\n## Overview\n\nML is great.\n\n## Connections\n\n- [[Python]]\n- [[BERT]]",
        categories=["research"],
        confidence="high",
        sources=["raw/ml.md"],
    ))
    save_article(wiki_dir, Article(
        title="Python",
        body="# Python\n\n> A programming language.\n\n## Overview\n\nPython is versatile.\n\n## Connections\n\n- [[Machine Learning]]",
        categories=["technology"],
        confidence="high",
        sources=["raw/python.md"],
    ))
    save_article(wiki_dir, Article(
        title="BERT",
        body="# BERT\n\n> Bidirectional encoder.\n\n## Overview\n\nBERT uses [[Machine Learning]].\n\n## Connections\n\n- [[Machine Learning]]",
        categories=["research"],
        confidence="medium",
        sources=["raw/bert.md"],
    ))


class TestWikiStatus:
    def test_empty(self, tmp_path):
        status = wiki_status(tmp_path / "nonexistent")
        assert not status["exists"]

    def test_with_articles(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        _create_sample_wiki(wiki)
        status = wiki_status(wiki)
        assert status["exists"]
        assert status["total_articles"] == 3
        assert "research" in status["categories"]


class TestRebuildIndex:
    def test_empty_wiki(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        stats = rebuild_index(wiki)
        assert stats["total_articles"] == 0
        assert (wiki / "index.md").exists()

    def test_with_articles(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        _create_sample_wiki(wiki)

        stats = rebuild_index(wiki)
        assert stats["total_articles"] == 3
        assert stats["total_categories"] == 2

        index = (wiki / "index.md").read_text()
        assert "Machine Learning" in index
        assert "Python" in index
        assert "BERT" in index
        assert "## Categories" in index
        assert "## All Articles" in index

    def test_category_pages(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        _create_sample_wiki(wiki)
        rebuild_index(wiki)

        cat_dir = wiki / "_categories"
        assert cat_dir.exists()
        assert (cat_dir / "research.md").exists()
        assert (cat_dir / "technology.md").exists()

        research = (cat_dir / "research.md").read_text()
        assert "Machine Learning" in research
        assert "BERT" in research


class TestHubArticles:
    def test_ranking(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        _create_sample_wiki(wiki)
        rebuild_index(wiki)  # ensure backlink counts are computed

        hubs = hub_articles(wiki)
        # Machine Learning should be most backlinked (linked from Python and BERT)
        assert len(hubs) > 0
        assert hubs[0]["title"] == "Machine Learning"
