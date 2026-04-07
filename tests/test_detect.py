"""Tests for detect.py — file discovery and classification."""
from pathlib import Path

from oh_my_wiki.detect import FileType, classify_file, detect


class TestClassifyFile:
    def test_markdown(self, tmp_path):
        f = tmp_path / "note.md"
        f.write_text("# Hello")
        assert classify_file(f) == FileType.NOTE

    def test_pdf(self, tmp_path):
        f = tmp_path / "paper.pdf"
        f.write_bytes(b"%PDF-1.4")
        assert classify_file(f) == FileType.PAPER

    def test_image(self, tmp_path):
        f = tmp_path / "photo.png"
        f.write_bytes(b"\x89PNG")
        assert classify_file(f) == FileType.IMAGE

    def test_csv(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("a,b,c\n1,2,3")
        assert classify_file(f) == FileType.DATA

    def test_unknown(self, tmp_path):
        f = tmp_path / "binary.exe"
        f.write_bytes(b"\x00")
        assert classify_file(f) is None

    def test_paper_detection(self, tmp_path):
        f = tmp_path / "paper.md"
        f.write_text(
            "# Attention Is All You Need\n\n"
            "arXiv:1706.03762\n\n"
            "## Abstract\n\n"
            "We propose a new architecture based on attention.\n\n"
            "Proceedings of NeurIPS 2017.\n"
        )
        assert classify_file(f) == FileType.PAPER


class TestDetect:
    def test_empty_dir(self, tmp_path):
        result = detect(tmp_path)
        assert result["total_files"] == 0
        assert result["warning"] == "No supported files found."

    def test_mixed_files(self, tmp_path):
        (tmp_path / "note.md").write_text("hello")
        (tmp_path / "photo.png").write_bytes(b"\x89PNG")
        (tmp_path / "data.csv").write_text("a,b")
        result = detect(tmp_path)
        assert result["total_files"] == 3
        assert len(result["files"]["note"]) == 1
        assert len(result["files"]["image"]) == 1
        assert len(result["files"]["data"]) == 1

    def test_skips_hidden(self, tmp_path):
        (tmp_path / ".hidden.md").write_text("secret")
        (tmp_path / "visible.md").write_text("hello")
        result = detect(tmp_path)
        assert result["total_files"] == 1

    def test_skips_sensitive(self, tmp_path):
        (tmp_path / "credentials.json").write_text("{}")
        (tmp_path / "note.md").write_text("hello")
        result = detect(tmp_path)
        assert result["total_files"] == 1
        assert len(result["skipped_sensitive"]) == 1

    def test_recursive(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "deep.md").write_text("hello")
        result = detect(tmp_path)
        assert result["total_files"] == 1
