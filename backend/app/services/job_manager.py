"""ジョブの状態管理を行う簡易サービスです。

現時点ではメモリ内（辞書）でジョブ状態を管理します。
将来的には SQLite などの永続化ストレージへの移行を検討します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# UUID（汎用一意識別子）を生成するための import です
# ジョブ ID に重複しにくい識別子を発行するために使用します
import uuid

# 現在日時を取得するための import です
# ジョブの作成時刻と更新時刻を UTC で記録するために使用します
from datetime import datetime, timezone

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
# ZIP 展開先のパスを保持するために使用します
from pathlib import Path

# ジョブの状態を表す列挙型を読み込みます
# 同じ models パッケージ内の job.py で定義しています
from app.models.job import JobStatus


# ジョブ状態を保存する辞書です
# キー: job_id（文字列）、値: ジョブの情報を持つ辞書
# 現時点ではプロセス再起動すると内容は失われます
_jobs: dict[str, dict] = {}


def create_job() -> str:
    """新しい OCR ジョブを作成します。

    Returns:
        作成されたジョブの一意な ID（UUID）を文字列で返します。
    """
    # UUID4 を使って重複しにくい識別子を生成します
    job_id = str(uuid.uuid4())

    # 現在時刻を UTC で取得します
    # ISO 8601 形式の文字列として保存することで、後から読みやすくなります
    now = datetime.now(timezone.utc).isoformat()

    # ジョブの初期状態を辞書に保存します
    _jobs[job_id] = {
        # ジョブの現在の状態を文字列として保存します
        "status": JobStatus.PENDING.value,
        # ジョブが作成された時刻です
        "created_at": now,
        # ジョブの状態が最後に更新された時刻です
        "updated_at": now,
        # エラー時などに使用する補足メッセージです
        "message": "",
        # 展開された画像ファイルの相対パスを保存するリストです
        "files": [],
        # OCR 処理の進捗率です（0.0 〜 1.0）
        "progress": 0.0,
        # 現在処理中のページ番号です
        "current_page": 0,
        # 処理対象の総ページ数です
        "total_pages": 0,
    }

    # 作成したジョブの ID を呼び出し元に返します
    return job_id


def get_job(job_id: str) -> dict | None:
    """指定された ID のジョブ情報を取得します。

    Args:
        job_id: 取得対象のジョブ ID

    Returns:
        ジョブ情報の辞書。存在しない場合は None を返します。
    """
    # 辞書の get メソッドを使うと、存在しないキーでもエラーになりません
    return _jobs.get(job_id)


def update_job_status(
    job_id: str,
    status: JobStatus,
    message: str = "",
    files: list[str] | None = None,
    extract_dir: Path | None = None,
) -> bool:
    """指定されたジョブの状態を更新します。

    Args:
        job_id: 更新対象のジョブ ID
        status: 新しいジョブ状態
        message: 補足メッセージ（省略可）
        files: 画像ファイルパスの一覧（省略可）
        extract_dir: ZIP 展開先のディレクトリパス（省略可）

    Returns:
        更新に成功した場合は True、ジョブが存在しなかった場合は False
    """
    # ジョブが存在しない場合は更新せず False を返します
    if job_id not in _jobs:
        return False

    # 状態と更新時刻、メッセージを更新します
    _jobs[job_id]["status"] = status.value
    _jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
    _jobs[job_id]["message"] = message

    # files が指定された場合のみ更新します
    if files is not None:
        _jobs[job_id]["files"] = files

    # extract_dir が指定された場合のみ更新します
    if extract_dir is not None:
        _jobs[job_id]["extract_dir"] = str(extract_dir)

    return True


def update_job_with_ocr_result(
    job_id: str,
    success: bool,
    text: str = "",
    output_dir: str = "",
    message: str = "",
) -> bool:
    """OCR 処理結果をもとにジョブ状態を更新します。

    Args:
        job_id: 更新対象のジョブ ID
        success: OCR 処理が成功したかどうか
        text: 認識されたテキスト全文
        output_dir: OCR 結果が出力されたディレクトリパス
        message: 補足メッセージ（エラー時など）

    Returns:
        更新に成功した場合は True、ジョブが存在しなかった場合は False
    """
    # ジョブが存在しない場合は更新せず False を返します
    if job_id not in _jobs:
        return False

    # 処理結果に応じて状態を更新します
    if success:
        _jobs[job_id]["status"] = JobStatus.COMPLETED.value
    else:
        _jobs[job_id]["status"] = JobStatus.FAILED.value

    # 更新時刻を現在時刻に設定します
    _jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    # OCR 結果のテキストを保存します
    _jobs[job_id]["text"] = text

    # OCR 結果の出力ディレクトリを保存します
    _jobs[job_id]["output_dir"] = output_dir

    # 補足メッセージを保存します
    _jobs[job_id]["message"] = message

    return True


def update_job_with_pdf_path(
    job_id: str,
    pdf_path: str,
    message: str = "",
) -> bool:
    """生成された PDF ファイルパスをジョブ情報に保存します。

    Args:
        job_id: 更新対象のジョブ ID
        pdf_path: 生成された PDF ファイルのパス
        message: 補足メッセージ（省略可）

    Returns:
        更新に成功した場合は True、ジョブが存在しなかった場合は False
    """
    # ジョブが存在しない場合は更新せず False を返します
    if job_id not in _jobs:
        return False

    # PDF パスを保存します
    _jobs[job_id]["pdf_path"] = pdf_path

    # 更新時刻を現在時刻に設定します
    _jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    # メッセージが指定されている場合は追記します
    if message:
        _jobs[job_id]["message"] = message

    return True


def update_job_progress(
    job_id: str,
    progress: float,
    current_page: int = 0,
    total_pages: int = 0,
    message: str = "",
) -> bool:
    """指定されたジョブの進捗情報を更新します。

    Args:
        job_id: 更新対象のジョブ ID
        progress: 進捗率（0.0 〜 1.0）
        current_page: 現在処理中のページ番号
        total_pages: 処理対象の総ページ数
        message: 補足メッセージ

    Returns:
        更新に成功した場合は True、ジョブが存在しなかった場合は False
    """
    # ジョブが存在しない場合は更新せず False を返します
    if job_id not in _jobs:
        return False

    # 進捗率を 0.0 〜 1.0 の範囲にClampします
    # min/max を使って範囲外の値を補正します
    _jobs[job_id]["progress"] = min(1.0, max(0.0, progress))

    # 現在処理中のページ番号を更新します
    _jobs[job_id]["current_page"] = current_page

    # 総ページ数を更新します
    _jobs[job_id]["total_pages"] = total_pages

    # 更新時刻を現在時刻に設定します
    _jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    # 補足メッセージを保存します
    if message:
        _jobs[job_id]["message"] = message

    return True


def get_job_progress(job_id: str) -> dict | None:
    """指定されたジョブの進捗情報を取得します。

    Args:
        job_id: 取得対象のジョブ ID

    Returns:
        進捗情報の辞書。存在しない場合は None を返します。
    """
    # ジョブが存在しない場合は None を返します
    job = _jobs.get(job_id)
    if job is None:
        return None

    # 進捗に関するフィールドのみを抽出して返します
    return {
        # ジョブの現在の状態です
        "status": job["status"],
        # 進捗率です
        "progress": job.get("progress", 0.0),
        # 現在処理中のページ番号です
        "current_page": job.get("current_page", 0),
        # 処理対象の総ページ数です
        "total_pages": job.get("total_pages", 0),
        # 補足メッセージです
        "message": job.get("message", ""),
        # 最終更新時刻です
        "updated_at": job.get("updated_at", ""),
    }
