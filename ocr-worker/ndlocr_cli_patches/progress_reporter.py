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
