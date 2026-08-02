# tests/test_trimmer.py

from PIL import Image
import os
from core.trimmer import trim_margins, process_images


def test_trim_margins():
    img = Image.new("RGB", (100, 100), "white")
    trimmed = trim_margins(img, 10, 10, 20, 20)
    assert trimmed.size == (80, 60)


def test_process_images(tmp_path):
    inp = tmp_path / "in"
    out = tmp_path / "out"
    inp.mkdir()
    Image.new("RGB", (100, 100), "white").save(inp / "001.png")

    success, msg = process_images(str(inp), str(out), 10, 10, 10, 10)
    assert success
    assert (out / "001.png").exists()
