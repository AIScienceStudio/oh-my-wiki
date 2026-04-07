"""Tests for article.py — frontmatter parsing, backlinks, Article model."""
from pathlib import Path

from oh_my_wiki.article import (
    Article,
    compute_backlink_counts,
    extract_wikilinks,
    parse_frontmatter,
    render_frontmatter,
    safe_filename,
)


class TestParseFrontmatter:
    def test_basic(self):
        text = '---\ntitle: "Hello"\nconfidence: high\n---\n\nBody text.'
        meta, body = parse_frontmatter(text)
        assert meta["title"] == "Hello"
        assert meta["confidence"] == "high"
        assert body.strip() == "Body text."

    def test_no_frontmatter(self):
        text = "Just some text."
        meta, body = parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_integer_value(self):
        text = "---\nword_count: 1250\n---\n\nBody."
        meta, _ = parse_frontmatter(text)
        assert meta["word_count"] == 1250

    def test_block_list(self):
        text = "---\nsources:\n  - raw/a.md\n  - raw/b.md\n---\n\nBody."
        meta, _ = parse_frontmatter(text)
        assert meta["sources"] == ["raw/a.md", "raw/b.md"]

    def test_inline_list(self):
        text = '---\naliases: ["transformers", "the transformer"]\n---\n\nBody.'
        meta, _ = parse_frontmatter(text)
        assert meta["aliases"] == ["transformers", "the transformer"]

    def test_empty_value_starts_list(self):
        text = "---\ntags:\n  - ml\n  - ai\ntitle: Test\n---\n\nBody."
        meta, _ = parse_frontmatter(text)
        assert meta["tags"] == ["ml", "ai"]
        assert meta["title"] == "Test"

    def test_quoted_string(self):
        text = '---\ntitle: "Hello: World"\n---\n\nBody.'
        meta, _ = parse_frontmatter(text)
        assert meta["title"] == "Hello: World"


class TestRenderFrontmatter:
    def test_basic(self):
        meta = {"title": "Test", "confidence": "high", "word_count": 100}
        result = render_frontmatter(meta)
        assert result.startswith("---")
        assert result.endswith("---")
        assert "title: Test" in result
        assert "word_count: 100" in result

    def test_block_list(self):
        meta = {"sources": ["a.md", "b.md"]}
        result = render_frontmatter(meta)
        assert "  - a.md" in result
        assert "  - b.md" in result

    def test_aliases_inline(self):
        meta = {"aliases": ["foo", "bar"]}
        result = render_frontmatter(meta)
        assert 'aliases: ["foo", "bar"]' in result

    def test_roundtrip(self):
        meta = {
            "title": "Test Article",
            "aliases": ["test", "testing"],
            "sources": ["raw/a.md"],
            "confidence": "high",
            "word_count": 500,
        }
        rendered = render_frontmatter(meta)
        parsed, _ = parse_frontmatter(rendered + "\n\nBody.")
        assert parsed["title"] == "Test Article"
        assert parsed["aliases"] == ["test", "testing"]
        assert parsed["sources"] == ["raw/a.md"]
        assert parsed["word_count"] == 500


class TestExtractWikilinks:
    def test_basic(self):
        text = "See [[Transformers]] and [[BERT]] for more."
        links = extract_wikilinks(text)
        assert links == ["Transformers", "BERT"]

    def test_pipe_syntax(self):
        text = "See [[Transformer Architecture|transformers]] here."
        links = extract_wikilinks(text)
        assert links == ["Transformer Architecture"]

    def test_dedup(self):
        text = "See [[Foo]] and [[Foo]] again."
        links = extract_wikilinks(text)
        assert links == ["Foo"]

    def test_none(self):
        text = "No links here."
        links = extract_wikilinks(text)
        assert links == []


class TestArticle:
    def test_to_markdown_and_back(self):
        a = Article(
            title="Test",
            body="# Test\n\n> Summary.\n\n## Overview\n\nSome text.",
            categories=["research"],
            tags=["ml"],
            confidence="high",
        )
        md = a.to_markdown()
        assert "title: Test" in md
        assert "confidence: high" in md

        b = Article.from_markdown(md)
        assert b.title == "Test"
        assert b.categories == ["research"]
        assert b.confidence == "high"

    def test_word_count_auto(self):
        a = Article(title="X", body="one two three four five")
        md = a.to_markdown()
        assert a.word_count == 5


class TestSafeFilename:
    def test_basic(self):
        assert safe_filename("Transformer Architecture") == "transformer-architecture"

    def test_special_chars(self):
        assert safe_filename("Q: How does it work?") == "q-how-does-it-work"

    def test_truncate(self):
        name = "a" * 200
        assert len(safe_filename(name)) <= 120


class TestComputeBacklinkCounts:
    def test_basic(self, tmp_path):
        (tmp_path / "a.md").write_text(
            '---\ntitle: "A"\n---\n\n# A\n\nSee [[B]].'
        )
        (tmp_path / "b.md").write_text(
            '---\ntitle: "B"\n---\n\n# B\n\nSee [[A]].'
        )
        counts = compute_backlink_counts(tmp_path)
        assert counts.get("A", 0) == 1
        assert counts.get("B", 0) == 1

    def test_no_self_link_counting(self, tmp_path):
        (tmp_path / "a.md").write_text(
            '---\ntitle: "A"\n---\n\n# A\n\nSee [[A]] and [[B]].'
        )
        (tmp_path / "b.md").write_text(
            '---\ntitle: "B"\n---\n\n# B\n\nStandalone.'
        )
        counts = compute_backlink_counts(tmp_path)
        # A links to itself and B. Self-links count (article references itself).
        assert counts.get("B", 0) == 1
