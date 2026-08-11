"""ZIP アーカイブから画像ファイルを展開するサービスです。

ブラウザからアップロードされた ZIP ファイルを共有ボリューム内に展開し、
backend と ocr-worker の両方からアクセスできる状態で、
OCR 処理の対象となる画像ファイルの一覧を取得します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# ZIP ファイルを読み書きするための標準ライブラリです
import zipfile

# 環境変数を読み込むための標準ライブラリです
# テスト時の展開先ディレクトリを切り替えるために使用します
import os

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
# 文字列のパス結合より安全で読みやすくなります
from pathlib import Path

# バイナリストリームの型を表すための import です
# ZIP ファイルのようなバイナリデータを受け取る引数の型ヒントに使用します
from typing import BinaryIO

# OCR 処理対象とする画像ファイルの拡張子です
# 大文字・小文字は区別せずに判定します
_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif", ".webp"}
)

# ZIP 展開先のベースディレクトリです
# 本番環境では backend / ocr-worker 両コンテナで共有される /data/extracted を使用します
# テスト環境では EXTRACT_BASE_DIR 環境変数で別のパスを指定できます
_EXTRACT_BASE_DIR = Path(os.environ.get("EXTRACT_BASE_DIR", "/data/extracted"))


def is_image_file(path: Path) -> bool:
    """指定されたパスが画像ファイルかどうかを判定します。

    Args:
        path: 判定対象のファイルパス

    Returns:
        画像ファイルの場合は True、そうでない場合は False
    """
    # ディレクトリは画像ファイルではありません
    if path.is_dir():
        return False

    # 拡張子を小文字で取得して判定します
    return path.suffix.lower() in _IMAGE_EXTENSIONS


def extract_images_from_zip(
    zip_file: BinaryIO,
    job_id: str,
) -> tuple[list[str], Path]:
    """ZIP ファイルから画像ファイルを展開して一覧を返します。

    Args:
        zip_file: アップロードされた ZIP ファイルのバイナリストリーム
        job_id: 展開先ディレクトリを識別するためのジョブ ID

    Returns:
        画像ファイルの相対パス一覧と、展開先ディレクトリパスのタプル
    """
    # 共有ボリューム内にジョブ専用の展開ディレクトリを作成します
    # backend と ocr-worker の両方から同じパスでアクセスできます
    extract_path = _EXTRACT_BASE_DIR / job_id
    extract_path.mkdir(parents=True, exist_ok=True)

    # ZIP ファイルを展開します
    # with 文を使うと、ファイルを自動的にクローズできます
    with zipfile.ZipFile(zip_file) as zf:
        # ZIP 内のすべてのファイルを展開ディレクトリに展開します
        zf.extractall(extract_path)

    # 展開されたファイルの中から画像ファイルを再帰的に探します
    # rglob("*") で extract_path 以下のすべてのファイルとディレクトリを取得します
    image_files = [
        # 相対パスを文字列に変換してリストに格納します
        str(path.relative_to(extract_path))
        # 画像ファイルのみを対象とします
        for path in extract_path.rglob("*")
        if is_image_file(path)
    ]

    # ファイル名順にソートして安定した順序を保ちます
    # OCR 処理時にページ順が狂わないようにするためです
    image_files.sort()

    # 画像ファイル一覧と展開先ディレクトリパスを呼び出し元に返します
    return image_files, extract_path
