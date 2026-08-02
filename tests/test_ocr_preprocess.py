# tests/test_ocr_preprocess.py

from PIL import Image
from core.ocr_preprocess import preprocess_image


def test_preprocess_upscale():
    img = Image.new("RGB", (100, 100), "white")
    out = preprocess_image(img, upscale=2.0)
    assert out.size == (200, 200)


def test_preprocess_contrast():
    img = Image.new("RGB", (100, 100), "gray")
    out = preprocess_image(img, enhance_contrast=True)
    assert out.mode == "L"
