"""OCR 処理の進捗ファイル書き込みユーティリティです。

OW004001: backend の SSE 連携のため、ocr-worker と backend が
同じファイル形式・パス規約で進捗を共有できるようにします。

SY002002: ocr-worker コンテナ内の in-memory ストアとして機能します。
backend コンテナから HTTP (GET /progress/{job_id}) で参照されます。

SY002003: 各ページの開始・完了時刻を蓄積し、frontend のデバッグ表示に
正しく伝達できるようにします。
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

# SY002002: in-memory 進捗ストア
# 複数スレッドからアクセスされる可能性があるため、将来的に threading.Lock の導入を検討
_progress_store: dict[str, dict] = {}

# SY002002: キャンセル要求されたジョブ ID を保持するセットです。
# backend から `POST /cancel/{job_id}` を受信した際に追加されます。
_cancelled_jobs: set[str] = set()


def _now_iso() -> str:
    """UTC の秒精度 ISO 8601 タイムスタンプを返します。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_progress(
    job_id: str | None,
    current_page: int,
    total_pages: int,
    message: str,
    phase: str | None = None,
    elapsed_seconds: float | None = None,
    file_name: str | None = None,
) -> None:
    """OCR ページ処理の進捗を in-memory ストアに書き込みます。

    Parameters
    ----------
    job_id : str | None
        進捗を保存するジョブ ID。
    current_page : int
        現在処理済みのページ数（1-based）。
    total_pages : int
        処理対象の総ページ数。
    message : str
        進捗メッセージ。
    phase : str | None
        ページ処理のフェーズ。"start" または "end"。
    elapsed_seconds : float | None
        ページ処理の経過時間（秒）。phase="end" の場合に設定。
    file_name : str | None
        処理対象の画像ファイル名。
    """
    if not job_id:
        return

    progress = round(0.1 + 0.5 * (current_page / total_pages), 2) if total_pages > 0 else 0.0

    # 既存の store を取得または初期化
    store = _progress_store.get(job_id)
    if store is None:
        store = {
            "job_id": job_id,
            "status": "processing",
            "progress": progress,
            "current_page": current_page,
            "total_pages": total_pages,
            "message": message,
            "timestamp": _now_iso(),
            "ocrPages": [],
        }
    else:
        store["progress"] = progress
        store["current_page"] = current_page
        store["total_pages"] = total_pages
        store["message"] = message
        store["timestamp"] = _now_iso()
        if store.get("status") != "processing":
            store["status"] = "processing"

    # ocrPages 配列の初期化
    if "ocrPages" not in store:
        store["ocrPages"] = []

    page_idx = current_page - 1  # 0-based index

    # 配列が短ければ拡張
    while len(store["ocrPages"]) <= page_idx:
        store["ocrPages"].append({
            "pageIndex": len(store["ocrPages"]),
            "fileName": file_name or f"page_{len(store['ocrPages']) + 1:03d}",
            "start": None,
            "end": None,
            "elapsedMs": None,
        })

    page_entry = store["ocrPages"][page_idx]

    if phase == "start":
        page_entry["start"] = _now_iso()
        if file_name:
            page_entry["fileName"] = os.path.basename(file_name)
    elif phase == "end":
        page_entry["end"] = _now_iso()
        if elapsed_seconds is not None:
            page_entry["elapsedMs"] = int(round(elapsed_seconds * 1000))
        if file_name:
            page_entry["fileName"] = os.path.basename(file_name)

    _progress_store[job_id] = store


def get_progress(job_id: str) -> dict | None:
    """指定したジョブ ID の進捗を取得します。

    Parameters
    ----------
    job_id : str
        ジョブ ID。

    Returns
    -------
    dict | None
        進捗データ。存在しない場合は None。
    """
    return _progress_store.get(job_id)


def mark_cancelled(job_id: str) -> None:
    """指定したジョブ ID をキャンセル済みとしてマークします。

    SY002002: backend からのキャンセル要求を受け取り、OCR 処理完了後に
    結果を破棄するために使用します。

    Parameters
    ----------
    job_id : str
        キャンセル対象のジョブ ID。
    """
    _cancelled_jobs.add(job_id)


def is_cancelled(job_id: str | None) -> bool:
    """指定したジョブ ID がキャンセル済みかどうかを判定します。

    Parameters
    ----------
    job_id : str | None
        判定対象のジョブ ID。

    Returns
    -------
    bool
        キャンセル済みの場合は True、それ以外は False。
    """
    if not job_id:
        return False
    return job_id in _cancelled_jobs


def clear_cancelled(job_id: str) -> None:
    """指定したジョブ ID のキャンセルマークを解除します。

    Parameters
    ----------
    job_id : str
        キャンセルマークを解除するジョブ ID。
    """
    _cancelled_jobs.discard(job_id)


def delete_progress(job_id: str) -> None:
    """指定したジョブ ID の進捗データを削除します。

    Parameters
    ----------
    job_id : str
        削除対象のジョブ ID。
    """
    _progress_store.pop(job_id, None)
    _cancelled_jobs.discard(job_id)
