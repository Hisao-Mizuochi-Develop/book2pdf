"""OCR 処理の進捗ファイル書き込みユーティリティです。

OW004001: backend の SSE 連携のため、ocr-worker と backend が
同じファイル形式・パス規約で進捗を共有できるようにします。
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def write_progress(
    job_id: str | None,
    current_page: int,
    total_pages: int,
    message: str,
) -> None:
    """OCR ページ処理の進捗をファイルに書き込みます。

    Parameters
    ----------
    job_id : str | None
        進捗ファイル名に使用するジョブ ID。
    current_page : int
        現在処理済みのページ数。
    total_pages : int
        処理対象の総ページ数。
    message : str
        進捗メッセージ。
    """
    if not job_id:
        return
    progress_dir = Path(os.environ.get("PROGRESS_DIR", "/data/progress"))
    progress_dir.mkdir(parents=True, exist_ok=True)
    progress_file = progress_dir / f"{job_id}.json"
    temp_file = progress_dir / f"{job_id}.json.tmp"
    progress = round(0.1 + 0.5 * (current_page / total_pages), 2) if total_pages > 0 else 0.0
    data = {
        "status": "processing",
        "progress": progress,
        "current_page": current_page,
        "total_pages": total_pages,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # 原子書き込み: 一時ファイルに書き込んでから rename で入れ替え
    temp_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    temp_file.replace(progress_file)
