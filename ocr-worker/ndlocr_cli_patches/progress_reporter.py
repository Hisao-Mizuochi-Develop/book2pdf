"""OCR 処理の進捗ファイル書き込みユーティリティです。

OW004001: backend の SSE 連携のため、ocr-worker と backend が
同じファイル形式・パス規約で進捗を共有できるようにします。

SY002002: ocr-worker コンテナ内の in-memory ストアとして機能します。
backend コンテナから HTTP (GET /progress/{job_id}) で参照されます。
"""
from __future__ import annotations

from datetime import datetime, timezone

# SY002002: in-memory 進捗ストア
# 複数スレッドからアクセスされる可能性があるため、将来的に threading.Lock の導入を検討
_progress_store: dict[str, dict] = {}

# SY002002: キャンセル要求されたジョブ ID を保持するセットです。
# backend から `POST /cancel/{job_id}` を受信した際に追加されます。
_cancelled_jobs: set[str] = set()


def write_progress(
    job_id: str | None,
    current_page: int,
    total_pages: int,
    message: str,
) -> None:
    """OCR ページ処理の進捗を in-memory ストアに書き込みます。

    Parameters
    ----------
    job_id : str | None
        進捗を保存するジョブ ID。
    current_page : int
        現在処理済みのページ数。
    total_pages : int
        処理対象の総ページ数。
    message : str
        進捗メッセージ。
    """
    if not job_id:
        return
    progress = round(0.1 + 0.5 * (current_page / total_pages), 2) if total_pages > 0 else 0.0
    _progress_store[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": progress,
        "current_page": current_page,
        "total_pages": total_pages,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


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
