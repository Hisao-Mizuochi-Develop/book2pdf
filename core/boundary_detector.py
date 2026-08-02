"""境界検出アルゴリズム

キャプチャ時の左右クロップ範囲を決める。Strategy パターンで方式を切り替える。

- FullFrameBoundary: 既定。クロップせずウィンドウ全体を取り込む。
  余白のトリミングは取り込み後の専用トリミングタブで行う方針のため、
  取り込み時に自動で横方向を削ることはしない（誤検出で本文を不可逆に
  失うのを避ける）。
- ManualBoundary: ユーザーがドラッグで指定した固定座標で左右をクロップ。
  「1ページだけ取りたい」等、明示的に範囲を絞りたいとき用。

加えて、トリミングタブから呼び出す
``detect_content_box`` で、4 辺すべての余白を自動検出する関数を提供する。
"""

from abc import ABC, abstractmethod

import numpy as np
from PIL import Image, ImageChops


class BoundaryDetector(ABC):
    """境界検出の基底クラス"""

    @abstractmethod
    def detect(self, image):
        """画像から左右の境界座標を返す。

        Args:
            image: BGR形式の numpy 配列

        Returns:
            (left, right) のタプル
        """
        pass


class FullFrameBoundary(BoundaryDetector):
    """クロップせず画像全体を使う（既定）。

    取り込み時に自動で左右を削ると、誤検出で本文を不可逆に失う恐れがある。
    余白の除去は取り込み後の専用トリミングタブに任せる方針のため、ここでは
    常に画像全幅 (0, width) を返す。ページ変化検出も全幅で行われる。
    """

    def detect(self, image):
        return 0, image.shape[1]


class ManualBoundary(BoundaryDetector):
    """手動指定による固定境界

    ユーザーがドラッグ操作で指定した左右の座標をそのまま使用する。
    """

    def __init__(self, left=0, right=0):
        self.left = left
        self.right = right

    def detect(self, image):
        right = self.right if self.right > 0 else image.shape[1]
        return self.left, right


def detect_content_box(
    im: Image.Image,
    threshold: int = 12,
    padding: int = 0,
) -> tuple[int, int, int, int] | None:
    """画像のコンテンツ領域 (非背景部分) のバウンディングボックスを返す。

    4 隅のピクセル中央値を背景色とみなし、しきい値以上の差がある領域を
    コンテンツとして抽出する。電子書籍ビューアのように余白が単色
    (白や薄いベージュ) で囲まれている画像で有効。

    Args:
        im: PIL Image
        threshold: 背景との輝度差しきい値 (0..255)。大きくするほど寛容
        padding: 検出領域の周囲に確保する余白 (ピクセル)

    Returns:
        (left, top, right, bottom) の絶対座標。検出失敗時は None。
    """
    if im is None:
        return None

    rgb = im.convert("RGB")
    w, h = rgb.size
    if w < 4 or h < 4:
        return (0, 0, w, h)

    # 4 隅から背景色を推定 (中央値で外れ値に強くする)
    corners = [rgb.getpixel((0, 0)), rgb.getpixel((w - 1, 0)),
               rgb.getpixel((0, h - 1)), rgb.getpixel((w - 1, h - 1))]
    bg = tuple(int(np.median([c[i] for c in corners])) for i in range(3))

    bg_im = Image.new("RGB", (w, h), bg)
    diff = ImageChops.difference(rgb, bg_im).convert("L")
    mask = diff.point(lambda v: 255 if v > threshold else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return None

    left, top, right, bottom = bbox
    if padding:
        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(w, right + padding)
        bottom = min(h, bottom + padding)
    return left, top, right, bottom


def detect_margins(
    im: Image.Image,
    threshold: int = 12,
    padding: int = 0,
) -> tuple[int, int, int, int] | None:
    """画像の余白 (左/右/上/下マージン) を自動検出して返す。

    トリミングタブの 4 マージン入力欄に直接流し込める形式で返す。

    Returns:
        (left_margin, right_margin, top_margin, bottom_margin)
        検出失敗時は None。
    """
    box = detect_content_box(im, threshold=threshold, padding=padding)
    if box is None:
        return None
    w, h = im.size
    left, top, right, bottom = box
    return left, max(0, w - right), top, max(0, h - bottom)


def create_detector(method, manual_left=0, manual_right=0):
    """境界検出方式に応じた検出器を生成する。

    Args:
        method: "manual" なら手動座標でクロップ。それ以外（"full" や旧来の
            "pixel_compare" / "canny_edge" 等）は全画面取り込み。
        manual_left, manual_right: 手動指定時のウィンドウ相対座標
    """
    if method == "manual":
        return ManualBoundary(manual_left, manual_right)
    return FullFrameBoundary()
