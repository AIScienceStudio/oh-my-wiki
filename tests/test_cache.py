"""Tests for cache.py — SHA256 extraction cache."""
from oh_my_wiki.cache import (
    check_cache,
    clear_cache,
    file_hash,
    load_cached,
    save_cached,
)


class TestFileHash:
    def test_deterministic(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("hello world")
        h1 = file_hash(f)
        h2 = file_hash(f)
        assert h1 == h2
        assert len(h1) == 64  # SHA256 hex

    def test_different_content(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("hello")
        f2.write_text("world")
        assert file_hash(f1) != file_hash(f2)


class TestCache:
    def test_miss(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("hello")
        assert load_cached(f, tmp_path) is None

    def test_save_and_load(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("hello")
        data = {"topics": [{"name": "Test"}], "summary": "A test"}
        save_cached(f, data, tmp_path)
        result = load_cached(f, tmp_path)
        assert result == data

    def test_invalidates_on_change(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("hello")
        save_cached(f, {"v": 1}, tmp_path)
        f.write_text("changed!")
        assert load_cached(f, tmp_path) is None

    def test_clear(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("hello")
        save_cached(f, {"v": 1}, tmp_path)
        count = clear_cache(tmp_path)
        assert count == 1
        assert load_cached(f, tmp_path) is None


class TestCheckCache:
    def test_mixed(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("cached")
        f2.write_text("uncached")
        save_cached(f1, {"cached": True}, tmp_path)

        cached, uncached = check_cache([str(f1), str(f2)], tmp_path)
        assert len(cached) == 1
        assert cached[0]["cached"] is True
        assert uncached == [str(f2)]
