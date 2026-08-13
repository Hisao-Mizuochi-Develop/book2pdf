#!/usr/bin/env python3
"""入力画像に対して OCR 精度向上を目指した前処理を適用するスクリプト。

Usage:
    python scripts/preprocess_image.py \
        --input-zip benchmark-ocr-003001.zip \
        --output-zip benchmark-ocr-003002-sharpen.zip \
        --pattern sharpen_light

Supported patterns:
    - baseline: 前処理なし（元画像をそのままコピー）
    - sharpen_light: 軽度シャープニング
    - sharpen_light_upscale_2x: 2倍アップスケーリング＋軽度シャープニング
    - contrast_gamma: コントラスト強調＋ガンマ補正
    - contrast_gamma_sharpen_light: コントラスト強調＋ガンマ補正＋軽度シャープニング
    - denoise: ノイズ除去
"""

from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def _pil_to_array(img: Image.Image) -> np.ndarray:
    return np.array(img)


def _array_to_pil(arr: np.ndarray, mode: str) -> Image.Image:
    return Image.fromarray(arr, mode=mode)


def sharpen_light(img: Image.Image) -> Image.Image:
    """軽度シャープニング。輪郭をほどほどに鮮明化する。"""
    return img.filter(
        ImageFilter.UnsharpMask(radius=2, percent=80, threshold=3)
    )


def upscale_2x(img: Image.Image) -> Image.Image:
    """2倍の Lanczos 補間でアップスケーリング。"""
    new_size = (img.width * 2, img.height * 2)
    return img.resize(new_size, Image.Resampling.LANCZOS)


def contrast_gamma(img: Image.Image) -> Image.Image:
    """コントラスト強調＋ガンマ補正。

    文字と背景の分離を強め、薄字や記号の認識率向上を狙う。
    """
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

    arr = _pil_to_array(img).astype(np.float32) / 255.0
    gamma = 0.8
    arr = np.power(arr, gamma)
    arr = (arr * 255.0).clip(0, 255).astype(np.uint8)
    return _array_to_pil(arr, img.mode)


def denoise(img: Image.Image) -> Image.Image:
    """軽度のノイズ除去。"""
    # PIL には純粋な「ノイズ除去」フィルタがないため、
    # 軽く median フィルタを適用する。
    return img.filter(ImageFilter.MedianFilter(size=3))


PATTERNS: dict[str, Callable[[Image.Image], Image.Image]] = {
    "baseline": lambda img: img,
    "sharpen_light": sharpen_light,
    "sharpen_light_upscale_2x": lambda img: sharpen_light(upscale_2x(img)),
    "contrast_gamma": contrast_gamma,
    "contrast_gamma_sharpen_light": lambda img: sharpen_light(contrast_gamma(img)),
    "denoise": denoise,
}


def preprocess_zip(input_zip: Path, output_zip: Path, pattern: str) -> None:
    """ZIP 内の画像に前処理を適用して新しい ZIP を作成する。"""
    if pattern not in PATTERNS:
        raise ValueError(
            f"Unknown pattern: {pattern}. Supported: {list(PATTERNS.keys())}"
        )

    processor = PATTERNS[pattern]

    with zipfile.ZipFile(input_zip, "r") as zin, zipfile.ZipFile(
        output_zip, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                img = Image.open(io.BytesIO(data))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                processed = processor(img)
                buf = io.BytesIO()
                fmt = "PNG" if info.filename.lower().endswith(".png") else "JPEG"
                processed.save(buf, format=fmt)
                data = buf.getvalue()
            zout.writestr(info, data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply image preprocessing for OCR benchmark."
    )
    parser.add_argument(
        "--input-zip",
        type=Path,
        required=True,
        help="Path to input ZIP containing images.",
    )
    parser.add_argument(
        "--output-zip",
        type=Path,
        required=True,
        help="Path to output ZIP with preprocessed images.",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        required=True,
        choices=list(PATTERNS.keys()),
        help="Preprocessing pattern to apply.",
    )
    args = parser.parse_args()

    preprocess_zip(args.input_zip, args.output_zip, args.pattern)
    print(f"Created {args.output_zip} with pattern '{args.pattern}'")


if __name__ == "__main__":
    main()
