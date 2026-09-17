"""ジョブ関連の API エンドポイントを定義するルーターです。

このファイルでは、ZIP アップロードやジョブ状態確認など、
OCR ジョブに関する HTTP エンドポイントを実装します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# 非同期処理でスリープするための標準ライブラリです
# SSE 配信中の進捗ポーリング間隔で使用します
import asyncio

# ログ出力のための標準ライブラリです
# 環境変数 LOG_LEVEL で出力レベルを切り替えます
import logging

# 環境変数を読み込むための標準ライブラリです
# ポーリング間隔をテスト時に変更するために使用します
import os

# ディレクトリ削除に使用する標準ライブラリです
# SY002002: ジョブキャンセル時のファイルクリーンアップに使用します
import shutil

# 処理時間を計測するための標準ライブラリです
import time

# ZIP ファイルの検証で使う標準ライブラリです
# 不正な ZIP ファイルを判定するために使用します
import zipfile

# 日時付き PDF ファイル名を生成するための標準ライブラリです
from datetime import datetime, timedelta, timezone

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
from pathlib import Path

# ocr-worker への HTTP ポーリング用非同期クライアントです
# SY002002: per-page 進捗を ocr-worker の REST API から取得するために使用します
import httpx

# FastAPI の機能を読み込みます
# APIRouter: エンドポイントをグループ化する
# HTTPException: HTTP エラーレスポンスを返す
# UploadFile: アップロードされたファイルを受け取る
from fastapi import APIRouter, HTTPException, UploadFile

# FileResponse: ファイルダウンロード用レスポンス
# StreamingResponse: SSE 配信用レスポンス
from fastapi.responses import FileResponse, StreamingResponse

# アプリケーション設定を読み込みます
from app.core.config import settings

# ジョブ関連の Pydantic モデルを読み込みます
# リクエスト・レスポンスの型とルールを定義しています
from app.models.job import (
    JobCreateResponse,
    JobOcrResponse,
    JobResponse,
    JobStatus,
    JobUploadResponse,
    ProgressEvent,
)

# ジョブ状態管理サービスを読み込みます
# ZIP 展開・画像抽出サービスを読み込みます
from app.services import job_manager, zip_extractor

# OCR エンジンを読み込みます
from app.services.ocr_engine import create_ocr_engine

# 検索可能 PDF 生成サービスを読み込みます
from app.services.pdf_generator import generate_searchable_pdf

# このルーターで定義するエンドポイントの共通設定です
# tags は自動生成される API ドキュメントでグループ名として使われます
router = APIRouter(tags=["jobs"])

# 本モジュール用のロガーを取得します
# ログレベルは app.main で一括設定されます
logger = logging.getLogger(__name__)


@router.post("/", response_model=JobCreateResponse)
def create_job() -> JobCreateResponse:
    """新しい OCR ジョブを作成します。

    このエンドポイントは ZIP アップロードの前に呼ばれる想定です。
    ジョブ ID を発行し、メモリ内で初期状態（pending）を保持します。
    """
    # 新しいジョブを作成してその ID を取得します
    job_id = job_manager.create_job()

    # レスポンスモデルに合わせて返却します
    # 初期状態は PENDING（処理待ち）です
    return JobCreateResponse(job_id=job_id, status=JobStatus.PENDING)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    """指定されたジョブ ID の状態を取得します。

    SY002002:
    - backend の in-memory ジョブ状態と ocr-worker の per-page 進捗をマージして返します
    - ocr-worker から取得する progress / current_page / total_pages / message を優先します
    - status は backend のフェーズ値を優先します

    Args:
        job_id: 確認したいジョブの ID

    Returns:
        ジョブの現在の状態（進捗情報を含む）

    Raises:
        HTTPException: ジョブが存在しない場合に 404 エラーを返します
    """
    # ジョブ管理サービスからジョブ情報を取得します
    job = job_manager.get_job(job_id)

    # ジョブが存在しない場合は 404 エラーを返します
    if job is None:
        raise HTTPException(status_code=404, detail="指定されたジョブが見つかりません")

    # ocr-worker のベース URL を設定から取得します
    ocr_worker_url = (
        settings.ocr_worker_url
        if settings.ocr_worker_url
        else "http://ocr-worker:8001"
    )

    # ocr-worker から per-page 進捗を取得してマージします
    progress_data: dict = {}
    try:
        async with httpx.AsyncClient(timeout=_OCR_WORKER_TIMEOUT) as client:
            response = await client.get(f"{ocr_worker_url}/progress/{job_id}")
            if response.status_code == 200:
                progress_data = response.json()
    except (httpx.HTTPError, ValueError):
        # ocr-worker へのアクセスに失敗しても、backend のジョブ情報は返します
        logger.debug("ocr-worker からの進捗取得に失敗しました: job_id=%s", job_id)

    # backend のフェーズ進捗を取得します
    backend_progress = job_manager.get_progress(job_id) or {}

    # 取得した状態をレスポンスモデルに変換して返します
    # job["status"] は文字列なので、JobStatus 列挙型に変換します
    merged = _merge_progress_data(backend_progress, progress_data)
    return JobResponse(
        job_id=job_id,
        status=JobStatus(job["status"]),
        message=merged["message"],
        files=job.get("files", []),
        text=job.get("text", ""),
        progress=merged["progress"],
        current_page=merged["current_page"],
        total_pages=merged["total_pages"],
    )


@router.delete("/{job_id}")
async def cancel_job(job_id: str) -> dict[str, str]:
    """指定されたジョブをキャンセルし、関連リソースをクリーンアップします。

    SY002002:
    - backend の in-memory ジョブ状態を cancelled に更新します
    - 実行中のバックグラウンドタスクにキャンセルを要求します
    - ocr-worker に `POST /cancel/{job_id}` でキャンセルを伝播します
    - ジョブに紐づくファイル（extract_dir / output_dir / pdf_path）を削除します
    - 進捗情報を削除します

    Args:
        job_id: キャンセル対象のジョブ ID

    Returns:
        キャンセル結果メッセージ

    Raises:
        HTTPException: ジョブが存在しない場合に 404 エラーを返します
    """
    # ジョブが存在するか確認します
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="指定されたジョブが見つかりません")

    # 既に完了・失敗・キャンセル済みのジョブは再キャンセル不可とします
    if job["status"] in (
        JobStatus.COMPLETED.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELLED.value,
    ):
        raise HTTPException(
            status_code=400,
            detail=f"ジョブは {job['status']} 状態のためキャンセルできません",
        )

    # ジョブ状態を cancelled に更新します
    job_manager.update_job_status(
        job_id,
        JobStatus.CANCELLED,
        message="ジョブがキャンセルされました",
    )
    job_manager.update_progress(
        job_id,
        status="cancelled",
        progress=0.0,
        current_page=0,
        total_pages=job.get("total_pages", 0),
        message="ジョブがキャンセルされました",
    )

    # 実行中のバックグラウンドタスクにキャンセルを要求します
    cancelled = job_manager.cancel_task(job_id)
    if cancelled:
        logger.info("バックグラウンドタスクのキャンセルを要求しました: job_id=%s", job_id)

    # ocr-worker にキャンセルを伝播します
    ocr_worker_url = (
        settings.ocr_worker_url
        if settings.ocr_worker_url
        else "http://ocr-worker:8001"
    )
    try:
        async with httpx.AsyncClient(timeout=_OCR_WORKER_TIMEOUT) as client:
            response = await client.post(f"{ocr_worker_url}/cancel/{job_id}")
            if response.status_code != 200:
                logger.warning(
                    "ocr-worker へのキャンセル伝播が失敗しました: job_id=%s, status=%d",
                    job_id,
                    response.status_code,
                )
    except httpx.HTTPError as exc:
        logger.warning(
            "ocr-worker へのキャンセル伝播中にエラーが発生しました: job_id=%s, error=%s",
            job_id,
            exc,
        )

    # ジョブに紐づくファイルを削除します
    # 削除に失敗しても API エラーにはせず、ログに記録します
    for key in ("extract_dir", "output_dir", "pdf_path"):
        path_str = job.get(key)
        if not path_str:
            continue
        try:
            path = Path(path_str)
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                logger.debug(
                    "ジョブファイルを削除しました: job_id=%s, path=%s",
                    job_id,
                    path,
                )
        except (OSError, shutil.Error) as exc:
            logger.warning(
                "ジョブファイルの削除に失敗しました: job_id=%s, key=%s, error=%s",
                job_id,
                key,
                exc,
            )

    # in-memory ストアからジョブと進捗を削除します
    job_manager.delete_job(job_id)

    return {"message": "ジョブをキャンセルしました", "job_id": job_id}


@router.post("/{job_id}/upload", response_model=JobUploadResponse)
async def upload_zip(job_id: str, file: UploadFile) -> JobUploadResponse:
    """指定されたジョブに ZIP ファイルをアップロードして展開します。

    Args:
        job_id: アップロード対象のジョブ ID
        file: アップロードされた ZIP ファイル

    Returns:
        ジョブ ID、更新後の状態、展開された画像ファイル一覧

    Raises:
        HTTPException: ジョブが存在しない場合や ZIP 展開に失敗した場合
    """
    # ジョブが存在するか確認します
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="指定されたジョブが見つかりません")

    # アップロードされたファイルが ZIP かどうかを確認します
    if file.content_type not in ("application/zip", "application/x-zip-compressed"):
        raise HTTPException(status_code=400, detail="ZIP ファイルをアップロードしてください")

    try:
        # ZIP ファイルを展開して画像ファイル一覧を取得します
        # 展開先は backend / ocr-worker 両方からアクセスできる共有ボリュームです
        files, extract_dir = zip_extractor.extract_images_from_zip(file.file, job_id)
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="不正な ZIP ファイルです") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ZIP の展開に失敗しました: {exc}") from exc

    # ジョブ状態を UPLOADED に更新し、ファイル一覧と展開先ディレクトリを保存します
    job_manager.update_job_status(
        job_id,
        JobStatus.UPLOADED,
        files=files,
        extract_dir=extract_dir,
    )

    # レスポンスモデルに合わせて返却します
    # アップロード成功後の状態と画像ファイル一覧を含めます
    return JobUploadResponse(
        job_id=job_id,
        status=JobStatus.UPLOADED,
        files=files,
    )


@router.post("/{job_id}/ocr", response_model=JobOcrResponse)
async def run_ocr(job_id: str) -> JobOcrResponse:
    """指定されたジョブの画像に対して OCR 処理を開始します。

    OCR 処理は数十分〜数時間かかることがあるため、
    このエンドポイントはリクエストを受け付けたら即座に processing 状態を返し、
    実際の OCR→PDF 生成はバックグラウンドで非同期に実行します。
    クライアントは `GET /api/jobs/{job_id}` で完了をポーリングしてください。

    Args:
        job_id: OCR 処理対象のジョブ ID

    Returns:
        ジョブ ID、受付後の状態

    Raises:
        HTTPException: ジョブが存在しない場合や画像が未アップロードの場合
    """
    # ジョブが存在するか確認します
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="指定されたジョブが見つかりません")

    # 画像ファイルがアップロード済みか確認します
    if job["status"] != JobStatus.UPLOADED.value:
        raise HTTPException(
            status_code=400,
            detail="OCR を実行する前に ZIP ファイルをアップロードしてください",
        )

    # 展開された画像ファイルの相対パス一覧を取得します
    image_files = job.get("files", [])
    if len(image_files) == 0:
        raise HTTPException(
            status_code=400,
            detail="OCR 対象の画像ファイルが見つかりません",
        )

    # 展開先ディレクトリを取得します
    extract_dir = job.get("extract_dir")
    if extract_dir is None:
        raise HTTPException(
            status_code=500,
            detail="展開先ディレクトリが見つかりません",
        )

    # ジョブ状態を PROCESSING に更新します
    job_manager.update_job_status(job_id, JobStatus.PROCESSING)

    # OCR 処理をバックグラウンドで非同期に開始します
    # HTTP 接続を長時間維持せず、即座にレスポンスを返すため、タイムアウトを回避できます
    logger.debug("OCR エンドポイント処理を開始します: job_id=%s", job_id)
    task = asyncio.create_task(_run_ocr_and_generate_pdf(job_id, extract_dir, image_files))
    job_manager.register_task(job_id, task)

    # レスポンスモデルに合わせて即座に返却します
    return JobOcrResponse(
        job_id=job_id,
        status=JobStatus.PROCESSING,
        text="",
        message="OCR処理を開始しました",
    )


async def _run_ocr_and_generate_pdf(
    job_id: str,
    extract_dir: str,
    image_files: list[str],
) -> None:
    """OCR と PDF 生成を非同期に実行し、ジョブ状態を更新します。

    OCR エンジンの `run()` と `generate_searchable_pdf()` は同期ブロッキング処理のため、
    `asyncio.to_thread` で別スレッドに委譲してイベントループをブロックしません。
    処理が完了したらジョブ状態を COMPLETED または FAILED に更新します。

    SY002002: ジョブキャンセル時に協調的に停止します。タスク終了時に
    `job_manager.delete_task` で追跡を解除します。
    """
    start_time = time.time()

    try:
        # OCR エンジンを作成します
        # ocr-worker が設定されていればリモート呼び出し、なければモックにフォールバックします
        ocr_engine = create_ocr_engine(use_mock=False)

        # 画像ファイルの相対パスを展開ディレクトリ内の絶対パスに変換します
        absolute_image_files = [
            str(Path(extract_dir) / image_file)
            for image_file in image_files
        ]

        total_pages = len(image_files)

        # OCR 処理開始を記録します
        job_manager.update_progress(
            job_id,
            status="processing",
            progress=0.0,
            current_page=0,
            total_pages=total_pages,
            message="OCR処理を開始しました",
        )

        # キャンセル済みでないかチェックします
        await asyncio.sleep(0)

        # BE009001: OCR 処理は ocr-worker への非同期 HTTP 呼び出しで実行します
        result = await ocr_engine.run_async(
            image_files=absolute_image_files,
            work_dir=Path(extract_dir),
            job_id=job_id,
        )

        # キャンセル済みでないかチェックします
        await asyncio.sleep(0)

        # OCR 全ページ処理が完了したら PDF 生成フェーズに移行します
        job_manager.update_progress(
            job_id,
            status="processing",
            progress=0.75,
            current_page=total_pages,
            total_pages=total_pages,
            message="PDFファイル生成中です",
        )
    except asyncio.CancelledError:
        # ユーザーによるキャンセルまたはシャットダウン時のクリーンアップです
        logger.info("OCR タスクがキャンセルされました: job_id=%s", job_id)
        job_manager.update_progress(
            job_id,
            status="cancelled",
            progress=0.0,
            current_page=0,
            total_pages=total_pages,
            message="ジョブがキャンセルされました",
        )
        job_manager.update_job_status(
            job_id,
            JobStatus.CANCELLED,
            message="ジョブがキャンセルされました",
        )
        job_manager.delete_task(job_id)
        return
    except Exception as exc:
        # OCR処理中にエラーが発生した場合は FAILED 状態に更新します
        logger.exception("OCR処理に失敗しました: job_id=%s", job_id)
        job_manager.update_progress(
            job_id,
            status="failed",
            progress=0.0,
            current_page=0,
            total_pages=total_pages,
            message=f"OCR処理に失敗しました: {exc}",
        )
        job_manager.update_job_with_ocr_result(
            job_id,
            message=f"OCR処理に失敗しました: {exc}",
        )
        job_manager.update_job_status(
            job_id,
            JobStatus.FAILED,
            message=f"OCR処理に失敗しました: {exc}",
        )
        job_manager.delete_task(job_id)
        return

    # OCR 結果をジョブ情報に保存します（ステータスは PROCESSING のまま）
    job_manager.update_job_with_ocr_result(
        job_id,
        text=result.text,
        output_dir=str(result.output_dir),
    )

    # BE009001: ocr-worker 側で処理失敗が検出された場合は FAILED に遷移します
    if not result.success:
        logger.error("OCR 処理が失敗しました: job_id=%s", job_id)
        job_manager.update_progress(
            job_id,
            status="failed",
            progress=0.0,
            current_page=0,
            total_pages=total_pages,
            message="OCR 処理に失敗しました",
        )
        job_manager.update_job_status(
            job_id,
            JobStatus.FAILED,
            message="OCR 処理に失敗しました",
        )
        job_manager.delete_task(job_id)
        return

    # キャンセル済みでないかチェックします
    await asyncio.sleep(0)

    # OCR 結果から検索可能 PDF を生成します
    try:
        pdf_path = await asyncio.to_thread(
            generate_searchable_pdf,
            job_id=job_id,
            output_dir=result.output_dir,
            extract_dir=Path(extract_dir),
        )
        job_manager.update_job_with_pdf_path(
            job_id,
            pdf_path=str(pdf_path),
            message="PDFファイル生成が完了しました",
        )
        # PDF 生成が完了してから COMPLETED に遷移します
        # これにより、フロントエンドが completed を検出した時点では
        # PDF が必ず生成済みであることが保証されます
        job_manager.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            message="PDFファイル生成が完了しました",
        )
        # PDF生成完了を記録します
        job_manager.update_progress(
            job_id,
            status="completed",
            progress=1.0,
            current_page=total_pages,
            total_pages=total_pages,
            message="PDFファイル生成が完了しました",
        )
    except asyncio.CancelledError:
        # ユーザーによるキャンセルまたはシャットダウン時のクリーンアップです
        logger.info("PDF 生成タスクがキャンセルされました: job_id=%s", job_id)
        job_manager.update_progress(
            job_id,
            status="cancelled",
            progress=0.0,
            current_page=0,
            total_pages=total_pages,
            message="ジョブがキャンセルされました",
        )
        job_manager.update_job_status(
            job_id,
            JobStatus.CANCELLED,
            message="ジョブがキャンセルされました",
        )
        job_manager.delete_task(job_id)
        return
    except Exception as pdf_exc:
        # PDF 生成に失敗した場合は FAILED に遷移します
        logger.exception("PDF 生成に失敗しました: job_id=%s", job_id)
        job_manager.update_progress(
            job_id,
            status="failed",
            progress=0.7,
            current_page=total_pages,
            total_pages=total_pages,
            message=f"OCR は成功しましたが PDF 生成に失敗しました: {pdf_exc}",
        )
        job_manager.update_job_with_pdf_path(
            job_id,
            pdf_path="",
            message=f"OCR は成功しましたが PDF 生成に失敗しました: {pdf_exc}",
        )
        job_manager.update_job_status(
            job_id,
            JobStatus.FAILED,
            message=f"OCR は成功しましたが PDF 生成に失敗しました: {pdf_exc}",
        )
        job_manager.delete_task(job_id)
        return

    # OCR エンドポイント全体の処理時間を計算します
    elapsed = time.time() - start_time
    logger.debug(
        "OCR エンドポイント処理が完了しました: job_id=%s, elapsed=%.3fs",
        job_id,
        elapsed,
    )

    # タスクの追跡を解除します
    job_manager.delete_task(job_id)


# ocr-worker の per-page 進捗ポーリング間隔（秒）です。
# SY002002: §5.2.2 に従い 1 秒間隔でポーリングします。
_OCR_WORKER_POLL_INTERVAL = float(
    os.environ.get("OCR_WORKER_POLL_INTERVAL", "1.0")
)

# ocr-worker への HTTP リクエストタイムアウト（秒）です。
# SY002002: §5.2.2 に従い 3 秒とします。
_OCR_WORKER_TIMEOUT = float(os.environ.get("OCR_WORKER_TIMEOUT", "3.0"))

# SSE ハートビート間隔（秒）です
# 長時間データが流れない場合にプロキシ/ブラウザのタイムアウト切断を防ぐため一定間隔で送信します
_HEARTBEAT_INTERVAL = 15.0


def _merge_progress_data(
    backend_data: dict | None,
    worker_data: dict | None,
) -> dict:
    """backend のフェーズ進捗と ocr-worker の per-page 進捗をマージします。

    SY002002 §5.4 のマージルールに従います:
    - status / timestamp → backend (フェーズ進捗) 優先
    - progress → 値の大きい方を優先
      (OCR 中は ocr-worker の per-page 進捗を、PDF 生成中は backend のフェーズ進捗を優先)
    - message → 進捗値が大きい側のメッセージを優先しますが、空文字の場合は
      もう一方の非空メッセージにフォールバックします
    - current_page / total_pages → ocr-worker (per-page 進捗) 優先

    Args:
        backend_data: backend の in-memory フェーズ進捗。None の場合は worker のみ。
        worker_data: ocr-worker から取得した per-page 進捗。None の場合は backend のみ。

    Returns:
        マージされた進捗データ辞書。
    """
    backend_data = backend_data or {}
    worker_data = worker_data or {}

    # backend 優先フィールド（status / timestamp）
    # ocr-worker の status はページ単位処理中固定の可能性があるため
    status = backend_data.get("status", worker_data.get("status", "processing"))
    timestamp = backend_data.get("timestamp", worker_data.get("timestamp", ""))

    # ocr-worker 優先フィールド（per-page 進捗）
    # ただし、backend のフェーズ進捗（PDF 生成など）が ocr-worker の進捗より
    # 進んでいる場合は backend の値を優先して、正しいメッセージを表示します。
    worker_progress = worker_data.get("progress", 0.0)
    backend_progress = backend_data.get("progress", 0.0)
    if backend_progress >= worker_progress:
        progress = backend_progress
        # 進捗値が大きい側の message を優先しますが、空文字の場合は
        # もう一方の意味のあるメッセージを保持します (FE002003/SY002003 UAT バグ対応)。
        message = backend_data.get("message", "") or worker_data.get("message", "")
    else:
        progress = worker_progress
        message = worker_data.get("message", "") or backend_data.get("message", "")
    current_page = worker_data.get("current_page", backend_data.get("current_page", 0))
    total_pages = worker_data.get("total_pages", backend_data.get("total_pages", 0))

    return {
        "status": status,
        "progress": progress,
        "current_page": current_page,
        "total_pages": total_pages,
        "message": message,
        "timestamp": timestamp,
    }


@router.get("/{job_id}/pdf")
async def download_pdf(job_id: str) -> FileResponse:
    """指定されたジョブの生成済み PDF をダウンロードします。

    Args:
        job_id: ダウンロード対象のジョブ ID

    Returns:
        PDF ファイルのレスポンス

    Raises:
        HTTPException: ジョブが存在しない、未完了、または PDF が未生成の場合
    """
    # ジョブが存在するか確認します
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="指定されたジョブが見つかりません")

    # OCR 処理が完了しているか確認します
    if job["status"] != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail="PDF のダウンロードは OCR 処理完了後に可能です",
        )

    # PDF パスが保存されているか確認します
    pdf_path = job.get("pdf_path", "")
    if not pdf_path:
        raise HTTPException(
            status_code=400,
            detail="PDF が生成されていません",
        )

    # PDF ファイルが実際に存在するか確認します
    path = Path(pdf_path)
    if not path.exists():
        logger.debug(
            "PDF ダウンロード要求に対象ファイルが存在しません: job_id=%s, pdf_path=%s",
            job_id,
            pdf_path,
        )
        raise HTTPException(
            status_code=404,
            detail="PDF ファイルが見つかりません",
        )

    file_size = path.stat().st_size
    logger.debug(
        "PDF ダウンロードを返します: job_id=%s, pdf_path=%s, size=%d bytes",
        job_id,
        pdf_path,
        file_size,
    )

    # 日時付きのユニークな PDF ファイル名を生成します
    # 日本時間（JST）でタイムスタンプを付与します
    jst = timezone(timedelta(hours=9))
    timestamp = datetime.now(jst).strftime("%Y%m%d_%H%M%S")
    filename = f"{job_id}_{timestamp}.pdf"

    # PDF ファイルを返します
    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=filename,
    )


async def _progress_event_generator(job_id: str):
    """SSE 配信用の進捗イベントジェネレータです。

    SY002002:
    - backend の in-memory フェーズ進捗 (job_manager.get_progress)
    - ocr-worker の per-page 進捗 (GET /progress/{job_id})
    をマージして Server-Sent Events 形式でクライアントに送信します。
    ジョブが completed または failed になったら配信を終了します。

    Args:
        job_id: 進捗配信対象のジョブ ID

    Yields:
        SSE 形式の進捗イベント文字列
    """
    # ocr-worker のベース URL を設定から取得します
    ocr_worker_url = (
        settings.ocr_worker_url
        if settings.ocr_worker_url
        else "http://ocr-worker:8000"
    )

    # ocr-worker への非同期 HTTP クライアントです
    client = httpx.AsyncClient(timeout=_OCR_WORKER_TIMEOUT)

    # 前回読み込んだ進捗データを保持します
    last_data: dict | None = None

    # 前回イベント（またはハートビート）を送信した時刻を保持します
    last_send_time = asyncio.get_event_loop().time()

    # イベントループに制御を渡し、TestClient がレスポンスを受信できるようにします
    await asyncio.sleep(0)

    try:
        # ジョブが完了または失敗するまでポーリングを続けます
        while True:
            event_sent = False

            # 1. backend のフェーズ進捗を in-memory ストアから取得します
            backend_data = job_manager.get_progress(job_id)

            # 2. ocr-worker の per-page 進捗を HTTP GET でポーリングします
            worker_data: dict | None = None
            try:
                response = await client.get(
                    f"{ocr_worker_url}/progress/{job_id}"
                )
                if response.status_code == 200:
                    worker_data = response.json()
                elif response.status_code == 404:
                    # ocr-worker にまだデータがない（処理開始前など）は正常系です
                    logger.info(
                        "ocr-worker に進捗データが見つかりません: job_id=%s",
                        job_id,
                    )
                else:
                    logger.warning(
                        "ocr-worker から予期しないステータス: job_id=%s, status=%d",
                        job_id,
                        response.status_code,
                    )
            except httpx.TimeoutException:
                logger.warning(
                    "ocr-worker へのポーリングがタイムアウトしました: job_id=%s",
                    job_id,
                )
            except httpx.ConnectError:
                logger.error(
                    "ocr-worker への接続に失敗しました: job_id=%s",
                    job_id,
                )
            except ValueError as exc:
                logger.error(
                    "ocr-worker へのポーリング中にエラー: job_id=%s, error=%s",
                    job_id,
                    exc,
                )

            # 3. 両方のデータソースをマージします
            # backend はステータス（フェーズ遷移）の権威、
            # ocr-worker は per-page 進捗の権威です
            data = _merge_progress_data(backend_data, worker_data)

            # 前回と内容が異なる場合のみイベントを送信します
            if data != last_data:
                last_data = data.copy()
                last_send_time = asyncio.get_event_loop().time()
                event_sent = True

                # 進捗イベントモデルを作成します
                event = ProgressEvent(
                    job_id=job_id,
                    status=JobStatus(data["status"]),
                    progress=data.get("progress", 0.0),
                    current_page=data.get("current_page", 0),
                    total_pages=data.get("total_pages", 0),
                    message=data.get("message", ""),
                    timestamp=data.get("timestamp", ""),
                )

                # SSE 形式でイベントを yield します
                # DEBUG(SY002003): frontend に送出する直前のマージ済みイベント内容をログに記録します
                logger.info(
                    "[SSE-EVENT] job_id=%s status=%s progress=%.2f current_page=%d total_pages=%d message=%r",
                    job_id,
                    data["status"],
                    data.get("progress", 0.0),
                    data.get("current_page", 0),
                    data.get("total_pages", 0),
                    data.get("message", ""),
                )
                event_text = f"data: {event.model_dump_json()}\n\n"
                yield event_text

                # クライアントに chunk を消費する時間を与えます
                # TestClient の同期ストリーミングでは、yield 直後に次のループに進むと
                # イベントが欠落する可能性があるため、ここで制御を渡します
                await asyncio.sleep(0)

                # 完了または失敗状態になったら配信を終了します
                if data["status"] in (
                    JobStatus.COMPLETED.value,
                    JobStatus.FAILED.value,
                ):
                    # ストリーム終了前に制御を渡し、最後のチャンクが確実に送信されるようにします
                    await asyncio.sleep(0)
                    # クライアントに正常終了を示す [DONE] シグナルを送信します
                    yield "data: [DONE]\n\n"
                    break

            # 進捗イベントが送信されず、ハートビート間隔が経過していたら keepalive を送信します
            # プロキシやブラウザのタイムアウト切断を防ぎます
            if not event_sent:
                now = asyncio.get_event_loop().time()
                if now - last_send_time >= _HEARTBEAT_INTERVAL:
                    last_send_time = now
                    # SSE コメント行としてハートビートを送信（クライアント側では無視される）
                    yield ": keepalive\n\n"
                    await asyncio.sleep(0)

            # 次のポーリングまでスリープします
            await asyncio.sleep(_OCR_WORKER_POLL_INTERVAL)

    finally:
        # httpx クライアントを確実にクローズします
        await client.aclose()
        # ジェネレータ終了時に最後の制御を渡し、ストリームのクリーンアップを助けます
        await asyncio.sleep(0)


@router.get("/{job_id}/events")
async def stream_job_events(job_id: str) -> StreamingResponse:
    """指定されたジョブの進捗を SSE で配信します。

    Args:
        job_id: 進捗配信対象のジョブ ID

    Returns:
        Server-Sent Events 形式のストリーミングレスポンス

    Raises:
        HTTPException: ジョブが存在しない場合に 404 エラーを返します
    """
    # ジョブが存在するか確認します
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="指定されたジョブが見つかりません")

    # SSE 形式でストリーミングレスポンスを返します
    # Cache-Control: no-cache → プロキシやブラウザがレスポンスをキャッシュしないようにします
    # X-Accel-Buffering: no → Nginx 等のリバースプロキシが SSE ストリームをバッファリングしないようにします
    return StreamingResponse(
        _progress_event_generator(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
