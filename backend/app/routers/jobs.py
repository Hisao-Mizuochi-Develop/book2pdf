"""ジョブ関連の API エンドポイントを定義するルーターです。

このファイルでは、ZIP アップロードやジョブ状態確認など、
OCR ジョブに関する HTTP エンドポイントを実装します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# ZIP ファイルの検証で使う標準ライブラリです
# 不正な ZIP ファイルを判定するために使用します
import zipfile

# 非同期処理でスリープするための標準ライブラリです
# SSE 配信中の進捗ファイルポーリング間隔で使用します
import asyncio

# JSON 形式の進捗ファイルを読み込むための標準ライブラリです
import json

# 環境変数を読み込むための標準ライブラリです
# 進捗ファイルディレクトリをテスト時に変更するために使用します
import os

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
from pathlib import Path

# ログ出力のための標準ライブラリです
# 環境変数 LOG_LEVEL で出力レベルを切り替えます
import logging

# 処理時間を計測するための標準ライブラリです
import time

# 日時付き PDF ファイル名を生成するための標準ライブラリです
from datetime import datetime, timedelta, timezone

# FastAPI の機能を読み込みます
# APIRouter: エンドポイントをグループ化する
# HTTPException: HTTP エラーレスポンスを返す
# UploadFile: アップロードされたファイルを受け取る
from fastapi import APIRouter, HTTPException, UploadFile

# FileResponse: ファイルダウンロード用レスポンス
# StreamingResponse: SSE 配信用レスポンス
from fastapi.responses import FileResponse, StreamingResponse

# ジョブ関連の Pydantic モデルを読み込みます
# リクエスト・レスポンスの型とルールを定義しています
from app.models.job import (
    JobCreateResponse,
    JobOcrResponse,
    JobResponse,
    JobUploadResponse,
    JobStatus,
    ProgressEvent,
)

# ジョブ状態管理サービスを読み込みます
from app.services import job_manager

# ZIP 展開・画像抽出サービスを読み込みます
from app.services import zip_extractor

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
def get_job(job_id: str) -> JobResponse:
    """指定されたジョブ ID の状態を取得します。

    Args:
        job_id: 確認したいジョブの ID

    Returns:
        ジョブの現在の状態

    Raises:
        HTTPException: ジョブが存在しない場合に 404 エラーを返します
    """
    # ジョブ管理サービスからジョブ情報を取得します
    job = job_manager.get_job(job_id)

    # ジョブが存在しない場合は 404 エラーを返します
    if job is None:
        raise HTTPException(status_code=404, detail="指定されたジョブが見つかりません")

    # 取得した状態をレスポンスモデルに変換して返します
    # job["status"] は文字列なので、JobStatus 列挙型に変換します
    return JobResponse(
        job_id=job_id,
        status=JobStatus(job["status"]),
        message=job.get("message", ""),
        files=job.get("files", []),
        text=job.get("text", ""),
    )


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
    asyncio.create_task(_run_ocr_and_generate_pdf(job_id, extract_dir, image_files))

    # レスポンスモデルに合わせて即座に返却します
    return JobOcrResponse(
        job_id=job_id,
        status=JobStatus.PROCESSING,
        text="",
        message="OCR 処理を開始しました",
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
    """
    start_time = time.time()

    # OCR エンジンを作成します
    # ocr-worker が設定されていればリモート呼び出し、なければモックにフォールバックします
    ocr_engine = create_ocr_engine(use_mock=False)

    try:
        # 画像ファイルの相対パスを展開ディレクトリ内の絶対パスに変換します
        absolute_image_files = [
            str(Path(extract_dir) / image_file)
            for image_file in image_files
        ]

        # OCR 処理は同期ブロッキングなので別スレッドで実行します
        result = await asyncio.to_thread(
            ocr_engine.run,
            image_files=absolute_image_files,
            work_dir=Path(extract_dir),
            job_id=job_id,
        )
    except Exception as exc:
        # OCR 処理中にエラーが発生した場合は FAILED 状態に更新します
        logger.exception("OCR 処理に失敗しました: job_id=%s", job_id)
        job_manager.update_job_with_ocr_result(
            job_id,
            message=f"OCR 処理に失敗しました: {exc}",
        )
        job_manager.update_job_status(
            job_id,
            JobStatus.FAILED,
            message=f"OCR 処理に失敗しました: {exc}",
        )
        return

    # OCR 結果をジョブ情報に保存します（ステータスは PROCESSING のまま）
    job_manager.update_job_with_ocr_result(
        job_id,
        text=result.text,
        output_dir=str(result.output_dir),
    )

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
            message="PDF 生成が完了しました",
        )
        # PDF 生成が完了してから COMPLETED に遷移します
        # これにより、フロントエンドが completed を検出した時点では
        # PDF が必ず生成済みであることが保証されます
        job_manager.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            message="PDF 生成が完了しました",
        )
    except Exception as pdf_exc:
        # PDF 生成に失敗した場合は FAILED に遷移します
        logger.exception("PDF 生成に失敗しました: job_id=%s", job_id)
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
        return

    # OCR エンドポイント全体の処理時間を計算します
    elapsed = time.time() - start_time
    logger.debug(
        "OCR エンドポイント処理が完了しました: job_id=%s, elapsed=%.3fs",
        job_id,
        elapsed,
    )


# 進捗ファイルの保存先ディレクトリです
# docker-compose.yml で ocr-worker と共有しています
# テスト時は PROGRESS_DIR 環境変数で上書きできます
_PROGRESS_DIR = Path(os.environ.get("PROGRESS_DIR", "/data/progress"))

# 進捗ファイルのポーリング間隔（秒）です
# テスト時は PROGRESS_POLL_INTERVAL 環境変数で短縮できます
_POLL_INTERVAL = float(os.environ.get("PROGRESS_POLL_INTERVAL", "0.5"))


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

    /data/progress/{job_id}.json をポーリングし、
    更新があれば Server-Sent Events 形式でクライアントに送信します。
    ジョブが completed または failed になったら配信を終了します。

    Args:
        job_id: 進捗配信対象のジョブ ID

    Yields:
        SSE 形式の進捗イベント文字列
    """
    # 進捗ファイルのパスを作成します
    progress_file = _PROGRESS_DIR / f"{job_id}.json"

    # 前回読み込んだ進捗データを保持します
    last_data: dict | None = None

    # イベントループに制御を渡し、TestClient がレスポンスを受信できるようにします
    await asyncio.sleep(0)

    # ジョブが完了または失敗するまでポーリングを続けます
    while True:
        # 進捗ファイルが存在する場合は読み込みます
        if progress_file.exists():
            content = progress_file.read_text(encoding="utf-8")
            data = json.loads(content)

            # 前回と内容が異なる場合のみイベントを送信します
            if data != last_data:
                last_data = data

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
                event_text = f"data: {event.model_dump_json()}\n\n"
                yield event_text

                # クライアントに chunk を消費する時間を与えます
                # TestClient の同期ストリーミングでは、yield 直後に次のループに進むと
                # イベントが欠落する可能性があるため、ここで制御を渡します
                await asyncio.sleep(0)

                # 完了または失敗状態になったら配信を終了します
                if data["status"] in (JobStatus.COMPLETED.value, JobStatus.FAILED.value):
                    # ストリーム終了前に制御を渡し、最後のチャンクが確実に送信されるようにします
                    await asyncio.sleep(0)
                    # クライアントに正常終了を示す [DONE] シグナルを送信します
                    yield "data: [DONE]\n\n"
                    break

        # 次のポーリングまで短時間スリープします
        await asyncio.sleep(_POLL_INTERVAL)

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

    # 進捗ファイル保存ディレクトリが存在しない場合は作成します
    _PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

    # SSE 形式でストリーミングレスポンスを返します
    return StreamingResponse(
        _progress_event_generator(job_id),
        media_type="text/event-stream",
    )
