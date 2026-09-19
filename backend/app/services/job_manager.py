"""ジョブの状態管理を行う簡易サービスです。

現時点ではメモリ内（辞書）でジョブ状態を管理します。
将来的には SQLite などの永続化ストレージへの移行を検討します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# 非同期タスクを管理するための標準ライブラリです
# SY002002: OCR バックグラウンドタスクのキャンセルに使用します
import asyncio

# UUID（汎用一意識別子）を生成するための import です
# ジョブ ID に重複しにくい識別子を発行するために使用します
import uuid

# 現在日時を取得するための import です
# ジョブの作成時刻と更新時刻を UTC で記録するために使用します
from datetime import datetime, timezone


def _now_iso() -> str:
    """frontend/ocr-worker と一致する ISO 8601 UTC タイムスタンプを返します。

    SY002003: 秒までの統一フォーマットとし、ミリ秒・タイムゾーン表記の混在を防ぎます。
    例: 2026-09-18T12:34:56Z
    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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

# フェーズ進捗を保存する辞書です。
# キー: job_id（文字列）、値: 進捗イベントデータの辞書。
# ocr-worker からの per-page 進捗とは分離され、
# backend 自身が管理するジョブフェーズ進捗を保持します。
# SY002002: ファイル共有方式から in-memory 方式に変更しました。
_progress_data: dict[str, dict] = {}

# 実行中の OCR バックグラウンドタスクを追跡する辞書です。
# キー: job_id（文字列）、値: asyncio.Task インスタンス。
# SY002002: ジョブキャンセル時にタスクを停止するために使用します。
_running_tasks: dict[str, asyncio.Task] = {}


def update_progress(
    job_id: str,
    status: str,
    progress: float,
    current_page: int,
    total_pages: int,
    message: str,
) -> None:
    """指定されたジョブのフェーズ進捗を in-memory ストアに書き込みます。

    Args:
        job_id: 対象ジョブ ID
        status: ジョブ状態（processing / completed / failed）
        progress: 進捗率（0.0〜1.0）
        current_page: 現在のページ（フェーズ番号として使用）
        total_pages: 総ページ数（フェーズ総数として使用）
        message: 進捗メッセージ
    """
    now = _now_iso()
    _progress_data[job_id] = {
        "status": status,
        "progress": progress,
        "current_page": current_page,
        "total_pages": total_pages,
        "message": message,
        "timestamp": now,
    }


def get_progress(job_id: str) -> dict | None:
    """指定されたジョブのフェーズ進捗を取得します。

    Args:
        job_id: 取得対象のジョブ ID

    Returns:
        進捗データの辞書。存在しない場合は None。
    """
    return _progress_data.get(job_id)


def delete_progress(job_id: str) -> None:
    """指定されたジョブのフェーズ進捗を in-memory ストアから削除します。

    Args:
        job_id: 削除対象のジョブ ID
    """
    _progress_data.pop(job_id, None)


def create_job() -> str:
    """新しい OCR ジョブを作成します。

    Returns:
        作成されたジョブの一意な ID（UUID）を文字列で返します。
    """
    # UUID4 を使って重複しにくい識別子を生成します
    job_id = str(uuid.uuid4())

    # 現在時刻を UTC で取得します
    # ISO 8601 形式の文字列として保存することで、後から読みやすくなります
    now = _now_iso()

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
    _jobs[job_id]["updated_at"] = _now_iso()
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
    text: str = "",
    output_dir: str = "",
    message: str = "",
) -> bool:
    """OCR 処理結果をジョブ情報に保存します。

    この関数はジョブの状態（status）を変更しません。
    状態遷移は呼び出し元で update_job_status を使って行ってください。

    Args:
        job_id: 更新対象のジョブ ID
        text: 認識されたテキスト全文
        output_dir: OCR 結果が出力されたディレクトリパス
        message: 補足メッセージ（エラー時など）

    Returns:
        更新に成功した場合は True、ジョブが存在しなかった場合は False
    """
    # ジョブが存在しない場合は更新せず False を返します
    if job_id not in _jobs:
        return False

    # 更新時刻を現在時刻に設定します
    _jobs[job_id]["updated_at"] = _now_iso()

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
    _jobs[job_id]["updated_at"] = _now_iso()

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
    _jobs[job_id]["updated_at"] = _now_iso()

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
        # SY002003: frontend/ocr-worker と同じ "timestamp" キーで統一します
        "timestamp": job.get("updated_at", ""),
    }


def register_task(job_id: str, task: asyncio.Task) -> None:
    """指定されたジョブのバックグラウンドタスクを登録します。

    SY002002: OCR 処理などの長時間非同期タスクを追跡し、
    キャンセル時に停止できるようにします。

    Args:
        job_id: タスクに紐づくジョブ ID
        task: 登録する asyncio.Task インスタンス
    """
    _running_tasks[job_id] = task


def get_task(job_id: str) -> asyncio.Task | None:
    """指定されたジョブの実行中タスクを取得します。

    Args:
        job_id: 取得対象のジョブ ID

    Returns:
        実行中の asyncio.Task インスタンス。存在しない場合は None。
    """
    return _running_tasks.get(job_id)


def delete_task(job_id: str) -> None:
    """指定されたジョブの実行中タスクを追跡辞書から削除します。

    Args:
        job_id: 削除対象のジョブ ID
    """
    _running_tasks.pop(job_id, None)


def cancel_task(job_id: str) -> bool:
    """指定されたジョブの実行中タスクにキャンセルを要求します。

    SY002002: 協調的キャンセルを行います。タスク内部でキャンセルチェック
    （await asyncio.sleep(0) など）を行っている場合にのみ即座に停止します。
    同期ブロッキング処理中は、処理が完了するまで停止しない場合があります。

    Args:
        job_id: キャンセル対象のジョブ ID

    Returns:
        キャンセル要求が行われた場合は True、タスクが存在しなかった場合は False
    """
    task = _running_tasks.get(job_id)
    if task is None:
        return False

    task.cancel()
    return True


def delete_job(job_id: str) -> bool:
    """指定されたジョブの情報を in-memory ストアから削除します。

    SY002002: ジョブキャンセル時にジョブ情報と進捗情報の両方を削除します。

    Args:
        job_id: 削除対象のジョブ ID

    Returns:
        削除に成功した場合は True、ジョブが存在しなかった場合は False
    """
    if job_id not in _jobs:
        return False

    _jobs.pop(job_id, None)
    _progress_data.pop(job_id, None)
    _running_tasks.pop(job_id, None)
    return True
