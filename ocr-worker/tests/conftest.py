"""ocr-worker テスト全体で共通に使用する設定を定義します。

本番環境では ndlocr_cli / hydra / PIL などが必要ですが、
ユニットテストではこれらをモックして import 可能にします。
"""

from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ocr-worker ディレクトリを import 対象に追加します
_OCR_WORKER_DIR = Path(__file__).resolve().parent.parent
if str(_OCR_WORKER_DIR) not in sys.path:
    sys.path.insert(0, str(_OCR_WORKER_DIR))

# 前処理を無効化しておき、PIL への依存を回避します
os.environ["PREPROCESS_ENABLED"] = "false"


# ---------------------------------------------------------------------------
# 外部ライブラリのモック化（import 順序を制御するため関数でラップ）
# ---------------------------------------------------------------------------
def _install_pil_mock() -> None:
    """PIL / Pillow をモックします。"""
    pil = types.ModuleType("PIL")
    pil.Image = types.SimpleNamespace()
    pil.ImageFilter = types.SimpleNamespace()
    sys.modules["PIL"] = pil
    sys.modules["PIL.Image"] = pil.Image
    sys.modules["PIL.ImageFilter"] = pil.ImageFilter


def _install_hydra_mock() -> None:
    """Hydra のグローバルインスタンスをモックします。"""
    hydra = types.ModuleType("hydra")
    hydra.core = types.ModuleType("hydra.core")
    global_hydra = types.ModuleType("hydra.core.global_hydra")

    class _GlobalHydra:
        """テスト用の GlobalHydra スタブです。"""

        _initialized: bool = False

        def is_initialized(self) -> bool:
            return self._initialized

        def clear(self) -> None:
            self._initialized = False

        @classmethod
        def instance(cls) -> _GlobalHydra:
            return cls()

    global_hydra.GlobalHydra = _GlobalHydra
    hydra.core.global_hydra = global_hydra
    sys.modules["hydra"] = hydra
    sys.modules["hydra.core"] = hydra.core
    sys.modules["hydra.core.global_hydra"] = global_hydra


def _install_cli_mock() -> types.ModuleType:
    """cli.core 以下をモックし、progress_reporter だけは実装を使用します。

    Returns:
        実際の progress_reporter モジュール。
    """
    cli_pkg = types.ModuleType("cli")
    cli_core = types.ModuleType("cli.core")

    # progress_reporter は ocr-worker 内のパッチファイルをそのまま読み込みます
    progress_reporter_path = _OCR_WORKER_DIR / "ndlocr_cli_patches" / "progress_reporter.py"
    spec = importlib.util.spec_from_file_location(
        "cli.core.progress_reporter",
        progress_reporter_path,
    )
    progress_reporter = importlib.util.module_from_spec(spec)

    sys.modules["cli"] = cli_pkg
    sys.modules["cli.core"] = cli_core
    spec.loader.exec_module(progress_reporter)
    sys.modules["cli.core.progress_reporter"] = progress_reporter
    cli_core.progress_reporter = progress_reporter

    # OcrInferrer / utils はテストで差し替え可能なスタブです
    class FakeOcrInferrer:
        """テスト用の OcrInferrer スタブです。"""

        def __init__(self, cfg: dict) -> None:
            self.cfg = cfg
            self.job_id: str | None = None

        def run(self) -> None:
            """何もしません。"""

    class FakeUtils:
        """テスト用の ndlocr_cli utils スタブです。"""

        @staticmethod
        def parse_cfg(cfg: dict) -> dict:
            return dict(cfg)

        @staticmethod
        def mkdir_with_duplication_check(path: str) -> str:
            return path

    cli_core.OcrInferrer = FakeOcrInferrer
    cli_core.utils = FakeUtils()

    return progress_reporter


# テスト対象のアプリケーションを import する前にモックを整えます
_install_pil_mock()
_install_hydra_mock()
_progress_reporter = _install_cli_mock()

# app.main の import 時にモックが適用された状態にするため、ここで import します
from app.main import app

# BE009001: OCR 結果ストアへのアクセス用です
import app.result_store as _result_store


@pytest.fixture
def client() -> TestClient:
    """FastAPI のテストクライアントを返します。"""
    return TestClient(app)


@pytest.fixture
def progress_reporter() -> types.ModuleType:
    """テスト対象の progress_reporter モジュールを返します。"""
    return _progress_reporter


@pytest.fixture(autouse=True)
def _reset_progress_store() -> None:
    """各テスト実行前に in-memory ストアをクリアします。"""
    _progress_reporter._progress_store.clear()
    _progress_reporter._cancelled_jobs.clear()
    _result_store._results.clear()
    yield
    _progress_reporter._progress_store.clear()
    _progress_reporter._cancelled_jobs.clear()
    _result_store._results.clear()
