"""Tests for extract.py — schema validation."""
from oh_my_wiki.extract import validate_extraction


class TestValidateExtraction:
    def test_valid(self):
        data = {
            "source_file": "raw/test.md",
            "topics": [{"name": "ML", "relevance": "primary"}],
            "entities": [{"name": "Python", "type": "tool"}],
            "summary": "A test file.",
            "suggested_titles": ["Machine Learning"],
        }
        assert validate_extraction(data) == []

    def test_missing_required(self):
        data = {"source_file": "raw/test.md"}
        errors = validate_extraction(data)
        assert len(errors) >= 3  # missing topics, entities, summary, suggested_titles

    def test_invalid_topics_type(self):
        data = {
            "source_file": "raw/test.md",
            "topics": "not a list",
            "entities": [],
            "summary": "x",
            "suggested_titles": [],
        }
        errors = validate_extraction(data)
        assert any("list" in e for e in errors)

    def test_topic_missing_name(self):
        data = {
            "source_file": "raw/test.md",
            "topics": [{"relevance": "primary"}],
            "entities": [],
            "summary": "x",
            "suggested_titles": [],
        }
        errors = validate_extraction(data)
        assert any("name" in e for e in errors)
