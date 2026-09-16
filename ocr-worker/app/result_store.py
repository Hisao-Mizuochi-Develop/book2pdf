"""ocr-worker の OCR 結果を非同期に保持するインメモリストアです。

BE009001: backend から fire-and-forget で POST /ocr を受けた後、
GET /result/{job_id} で結果を問い合わせられるようにするための一時保管領域です。
"""

from __future__ import annotations

# スレッド安全性を確保するためのロックです
import threading

# TTL 判定のための時刻取得に使用します
import time

# 型注釈用です
from typing import Any

# 結果ストアのスレッドセーフな読み書きのためのロックです
_lock = threading.Lock()

# ジョブ ID をキーとする結果辞書です
# value は {"status": "processing|completed|failed", "text": str|None,
#           "output_dir": str|None, "message": str|None,
#           "created_at": float} です
_results: dict[str, dict[str, Any]] = {}

# 結果の有効期限（秒）です
# BE009001: 24 時間経過した結果は自動的に削除します
TTL_SECONDS = 24 * 60 * 60


def init_result(job_id: str) -> None:
    """指定したジョブ ID の結果エントリを processing 状態で初期化します。

    Args:
        job_id: 対象のジョブ ID
    """
    with _lock:
        _results[job_id] = {
            "status": "processing",
            "text": None,
            "output_dir": None,
            "message": None,
            "created_at": time.time(),
        }


def save_result(job_id: str, text: str, output_dir: str) -> None:
    """指定したジョブ ID の結果を completed 状態で保存します。

    Args:
        job_id: 対象のジョブ ID
        text: 認識結果テキスト全文
        output_dir: OCR 結果の出力先ディレクトリパス
    """
    with _lock:
        data = _results.get(job_id, {})
        data.update(
            {
                "status": "completed",
                "text": text,
                "output_dir": output_dir,
                "message": None,
            }
        )
        if "created_at" not in data:
            data["created_at"] = time.time()
        _results[job_id] = data


def save_error(job_id: str, message: str) -> None:
    """指定したジョブ ID の結果を failed 状態で保存します。

    Args:
        job_id: 対象のジョブ ID
        message: エラーメッセージ
    """
    with _lock:
        data = _results.get(job_id, {})
        data.update(
            {
                "status": "failed",
                "text": None,
                "output_dir": None,
                "message": message,
            }
        )
        if "created_at" not in data:
            data["created_at"] = time.time()
        _results[job_id] = data


def get_result(job_id: str) -> dict[str, Any] | None:
    """指定したジョブ ID の結果を取得します。

    取得前に TTL を超過した古いエントリを削除します。

    Args:
        job_id: 対象のジョブ ID

    Returns:
        結果辞書、または存在しない場合は None
    """
    _cleanup()
    with _lock:
        return _results.get(job_id)


def delete_result(job_id: str) -> bool:
    """指定したジョブ ID の結果を削除します。

    Args:
        job_id: 対象のジョブ ID

    Returns:
        削除できた場合は True、存在しなかった場合は False
    """
    with _lock:
        return _results.pop(job_id, None) is not None


def _cleanup() -> None:
    """TTL を超過した結果エントリを削除します。"""
    now = time.time()
    with _lock:
        expired = [
            job_id
            for job_id, data in _results.items()
            if now - data.get("created_at", now) > TTL_SECONDS
        ]
        for job_id in expired:
            del _results[job_id]
