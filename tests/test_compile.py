"""Tests for compile.py — plan validation, article helpers."""
from oh_my_wiki.compile import (
    create_stub,
    detect_needed_stubs,
    validate_plan,
)


class TestValidatePlan:
    def test_valid(self):
        plan = {
            "articles": [
                {"title": "A", "action": "create", "sources": ["raw/a.md"]},
                {"title": "B", "action": "update", "new_sources": ["raw/b.md"]},
                {"title": "C", "action": "stub"},
            ]
        }
        assert validate_plan(plan) == []

    def test_missing_articles(self):
        errors = validate_plan({})
        assert any("missing" in e.lower() for e in errors)

    def test_invalid_action(self):
        plan = {"articles": [{"title": "A", "action": "delete"}]}
        errors = validate_plan(plan)
        assert any("invalid action" in e.lower() for e in errors)

    def test_duplicate_title(self):
        plan = {
            "articles": [
                {"title": "A", "action": "create", "sources": ["raw/a.md"]},
                {"title": "A", "action": "update"},
            ]
        }
        errors = validate_plan(plan)
        assert any("duplicate" in e.lower() for e in errors)

    def test_create_without_sources(self):
        plan = {"articles": [{"title": "A", "action": "create"}]}
        errors = validate_plan(plan)
        assert any("sources" in e.lower() for e in errors)


class TestCreateStub:
    def test_basic(self):
        stub = create_stub("Test Topic", categories=["research"])
        assert stub.title == "Test Topic"
        assert stub.status == "stub"
        assert stub.confidence == "low"
        assert "research" in stub.categories
        md = stub.to_markdown()
        assert "Stub article" in md


class TestDetectNeededStubs:
    def test_finds_missing_links(self):
        plan = {"articles": [{"title": "A", "action": "create", "sources": ["raw/a.md"]}]}
        texts = {"A": "# A\n\nSee [[B]] and [[C]]."}
        existing = {"D"}

        stubs = detect_needed_stubs(plan, texts, existing)
        titles = {s["title"] for s in stubs}
        assert "B" in titles
        assert "C" in titles
        assert "D" not in titles  # already exists
        assert "A" not in titles  # being created

    def test_no_stubs_needed(self):
        plan = {"articles": [{"title": "A", "action": "create", "sources": ["raw/a.md"]}]}
        texts = {"A": "# A\n\nSee [[B]]."}
        existing = {"B"}

        stubs = detect_needed_stubs(plan, texts, existing)
        assert stubs == []
