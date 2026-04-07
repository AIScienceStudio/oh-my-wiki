"""Tests for query.py — query preparation and file-back."""
from pathlib import Path

from oh_my_wiki.article import Article, save_article
from oh_my_wiki.query import file_back, prepare_query


def _create_wiki(wiki_dir):
    wiki_dir.mkdir(exist_ok=True)
    save_article(wiki_dir, Article(
        title="Machine Learning",
        body="# Machine Learning\n\n> ML overview.\n\n## Overview\n\nML is great.",
        categories=["research"],
    ))
    save_article(wiki_dir, Article(
        title="Python",
        body="# Python\n\n> A language.\n\n## Overview\n\nPython is nice.",
        categories=["technology"],
    ))


class TestPrepareQuery:
    def test_empty_wiki(self, tmp_path):
        result = prepare_query("test?", tmp_path / "wiki")
        assert result["candidates"] == []

    def test_returns_candidates(self, tmp_path):
        wiki = tmp_path / "wiki"
        _create_wiki(wiki)
        # Need index.md for prepare_query
        from oh_my_wiki.index import rebuild_index
        rebuild_index(wiki)

        result = prepare_query("What is ML?", wiki)
        assert len(result["candidates"]) == 2
        assert result["budget"] == 5


class TestFileBack:
    def test_creates_query_article(self, tmp_path):
        wiki = tmp_path / "wiki"
        _create_wiki(wiki)

        path = file_back(
            question="What is machine learning?",
            answer="ML is a field of AI.",
            source_article_titles=["Machine Learning"],
            wiki_dir=wiki,
        )
        assert path.exists()
        text = path.read_text()
        assert "Q: What is machine learning?" in text
        assert "ML is a field of AI." in text
        assert "[[Machine Learning]]" in text

    def test_updates_source_article(self, tmp_path):
        wiki = tmp_path / "wiki"
        _create_wiki(wiki)

        file_back(
            question="What is ML?",
            answer="It's AI.",
            source_article_titles=["Machine Learning"],
            wiki_dir=wiki,
        )

        ml_text = (wiki / "machine-learning.md").read_text()
        assert "Referenced in query" in ml_text

    def test_no_duplicate_references(self, tmp_path):
        wiki = tmp_path / "wiki"
        _create_wiki(wiki)

        file_back("Q1?", "A1", ["Machine Learning"], wiki)
        file_back("Q1?", "A1", ["Machine Learning"], wiki)

        ml_text = (wiki / "machine-learning.md").read_text()
        assert ml_text.count("Q: Q1?") == 1
