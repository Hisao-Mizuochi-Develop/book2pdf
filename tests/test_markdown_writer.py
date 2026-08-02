# tests/test_markdown_writer.py

import os
from core.markdown_writer import write_markdown
from core.chapter_detector import Chapter


def test_write_markdown_basic(tmp_path):
    results = [("001.png", "本文1"), ("002.png", "本文2")]
    out = tmp_path / "out.md"
    success, msg = write_markdown(results, str(out))
    assert success
    assert out.exists()


def test_write_markdown_with_chapter(tmp_path):
    results = [("001.png", "本文")]
    chapters = [Chapter(0, "001.png", "第1章", 1)]
    out = tmp_path / "out.md"
    success, msg = write_markdown(results, str(out), chapters=chapters)
    text = out.read_text()
    assert "第1章" in text
