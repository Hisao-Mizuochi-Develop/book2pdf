#!/usr/bin/env python3
"""入力画像に対して OCR 精度向上を目指した前処理を適用するスクリプト。

Usage:
    python scripts/preprocess_image.py \
        --input-zip benchmark-ocr-OW003001.zip \
        --output-zip benchmark-ocr-OW003002-sharpen.zip \
        --pattern sharpen_light

Supported patterns:
    - baseline: 前処理なし（元画像をそのままコピー）
    - sharpen_light: 軽度シャープニング
    - sharpen_light_upscale_2x: 2倍アップスケーリング＋軽度シャープニング
    - contrast_gamma: コントラスト強調＋ガンマ補正
    - contrast_gamma_sharpen_light: コントラスト強調＋ガンマ補正＋軽度シャープニング
    - denoise: ノイズ除去
    - 4x_upscale: 4倍アップスケーリング
    - 4x_upscale_sharpen: 4倍アップスケーリング＋軽度シャープニング
    - local_binarization: 局所的二値化（OpenCV adaptiveThreshold）
    - local_binarization_sharpen: 局所的二値化＋軽度シャープニング
    - contrast_strong: 強コントラスト（enhance 2.0）
    - contrast_strong_4x: 強コントラスト＋4倍アップスケーリング
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


def _convolve2d_valid(arr: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """純粋な numpy で 2D 畳み込みを行う（scipy 非依存）。

    arr は元画像より十分大きくパディング済みであることを前提とする。
    出力サイズは arr と同じになるように周囲をトリムする。
    """
    k_h, k_w = kernel.shape
    # 入力をカーネルより大きく取り、畳み込み後に元のサイズに戻せるようにする
    pad_h = k_h // 2
    pad_w = k_w // 2
    # 畳み込み後の有効領域サイズ
    out_h = arr.shape[0] - k_h + 1
    out_w = arr.shape[1] - k_w + 1
    # ストライドを使って展開
    sub_shape = (out_h, out_w, k_h, k_w)
    strides = (
        arr.strides[0],
        arr.strides[1],
        arr.strides[0],
        arr.strides[1],
    )
    windows = np.lib.stride_tricks.as_strided(
        arr, shape=sub_shape, strides=strides, writeable=False
    )
    result = np.tensordot(windows, kernel, axes=([2, 3], [0, 1]))
    # arr と同じサイズに戻すため周囲をゼロパディング
    full = np.pad(result, ((pad_h, pad_h), (pad_w, pad_w)), mode="constant")
    # サイズ調整（奇数カーネルでぴったり合うが、偶数カーネルにも対応）
    full = full[: arr.shape[0], : arr.shape[1]]
    return full


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


def upscale_4x(img: Image.Image) -> Image.Image:
    """4倍の Lanczos 補間でアップスケーリング。"""
    new_size = (img.width * 4, img.height * 4)
    return img.resize(new_size, Image.Resampling.LANCZOS)


def local_binarization(img: Image.Image) -> Image.Image:
    """局所的二値化（Pillow / numpy で実装）。

    文字と背景の分離を強め、薄字や陰影の影響を抑制する。
    OpenCV 非依存で動作する。
    """
    # グレースケールに変換
    gray = img.convert("L")
    arr = np.array(gray).astype(np.float32)

    # 局所平均を計算（blockSize=11 の移動平均）
    block_size = 11
    pad = block_size // 2
    padded = np.pad(arr, pad, mode="edge")

    # 2D 移動平均を畳み込みで計算
    kernel = np.ones((block_size, block_size), dtype=np.float32) / (block_size * block_size)
    local_mean = _convolve2d_valid(padded, kernel)

    # padding 分を元のサイズに戻す
    local_mean = local_mean[pad:pad + arr.shape[0], pad:pad + arr.shape[1]]

    # 適応的閾値処理（平均から定数 C=2 を引いた値）
    c = 2.0
    binary = (arr > (local_mean - c)).astype(np.uint8) * 255

    # 元画像のモードに応じて出力
    bin_img = Image.fromarray(binary, mode="L")
    if img.mode == "RGB":
        return bin_img.convert("RGB")
    return bin_img


def contrast_strong(img: Image.Image) -> Image.Image:
    """強コントラスト。文字と背景の差をより強調する。"""
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(2.0)


PATTERNS: dict[str, Callable[[Image.Image], Image.Image]] = {
    "baseline": lambda img: img,
    "sharpen_light": sharpen_light,
    "sharpen_light_upscale_2x": lambda img: sharpen_light(upscale_2x(img)),
    "contrast_gamma": contrast_gamma,
    "contrast_gamma_sharpen_light": lambda img: sharpen_light(contrast_gamma(img)),
    "denoise": denoise,
    "4x_upscale": upscale_4x,
    "4x_upscale_sharpen": lambda img: sharpen_light(upscale_4x(img)),
    "local_binarization": local_binarization,
    "local_binarization_sharpen": lambda img: sharpen_light(local_binarization(img)),
    "contrast_strong": contrast_strong,
    "contrast_strong_4x": lambda img: contrast_strong(upscale_4x(img)),
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
