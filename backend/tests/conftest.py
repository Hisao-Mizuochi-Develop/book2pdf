"""backend テスト全体で共通に使用する設定を定義します。

このファイルは pytest が自動的に読み込むため、
全テストモジュールで共通のセットアップ・クリーンアップを行えます。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
from __future__ import annotations

# 環境変数を操作するための標準ライブラリです
import os

# ディレクトリを削除するための標準ライブラリです
import shutil

# 一時ディレクトリを作成するための標準ライブラリです
import tempfile

# pytest の型ヒント用です
import pytest


def pytest_configure(config: pytest.Config) -> None:
    """pytest 起動時（テストファイルの import より前）に実行されます。

    本番環境では /data/extracted を使用しますが、
    ローカルの pytest 実行時には /data ディレクトリを作成できないため、
    一時ディレクトリを EXTRACT_BASE_DIR 環境変数に設定します。

    Args:
        config: pytest の設定オブジェクト
    """
    # テスト用の一時ディレクトリを作成します
    extract_dir = tempfile.mkdtemp()

    # テスト中に zip_extractor が使用する環境変数を設定します
    os.environ["EXTRACT_BASE_DIR"] = extract_dir

    # テスト中に pdf_generator が使用する環境変数を設定します
    pdf_output_dir = tempfile.mkdtemp()
    os.environ["PDF_OUTPUT_DIR"] = pdf_output_dir

    # テスト中に進捗ファイル用の環境変数を設定します
    progress_dir = tempfile.mkdtemp()
    os.environ["PROGRESS_DIR"] = progress_dir

    # テスト中は進捗ファイルのポーリング間隔を短くします
    # これにより SSE 配信のテストを高速に実行できます
    # 0.01 秒では TestClient の非同期 I/O と競合しやすいため、
    # 0.05 秒に設定しています
    os.environ["PROGRESS_POLL_INTERVAL"] = "0.05"

    # クリーンアップ時に使用できるよう、config オブジェクトに保存します
    config._test_extract_dir = extract_dir  # type: ignore[attr-defined]
    config._test_pdf_output_dir = pdf_output_dir  # type: ignore[attr-defined]
    config._test_progress_dir = progress_dir  # type: ignore[attr-defined]


def pytest_unconfigure(config: pytest.Config) -> None:
    """pytest 終了時に実行されます。

    Args:
        config: pytest の設定オブジェクト
    """
    # テスト用に作成した一時ディレクトリを削除します
    extract_dir = getattr(config, "_test_extract_dir", None)
    if isinstance(extract_dir, str):
        shutil.rmtree(extract_dir, ignore_errors=True)

    pdf_output_dir = getattr(config, "_test_pdf_output_dir", None)
    if isinstance(pdf_output_dir, str):
        shutil.rmtree(pdf_output_dir, ignore_errors=True)

    progress_dir = getattr(config, "_test_progress_dir", None)
    if isinstance(progress_dir, str):
        shutil.rmtree(progress_dir, ignore_errors=True)
