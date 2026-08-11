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

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
from pathlib import Path

# FastAPI の機能を読み込みます
# APIRouter: エンドポイントをグループ化する
# HTTPException: HTTP エラーレスポンスを返す
# UploadFile: アップロードされたファイルを受け取る
from fastapi import APIRouter, HTTPException, UploadFile

# ジョブ関連の Pydantic モデルを読み込みます
# リクエスト・レスポンスの型とルールを定義しています
from app.models.job import (
    JobCreateResponse,
    JobOcrResponse,
    JobResponse,
    JobUploadResponse,
    JobStatus,
)

# ジョブ状態管理サービスを読み込みます
from app.services import job_manager

# ZIP 展開・画像抽出サービスを読み込みます
from app.services import zip_extractor

# OCR エンジンを読み込みます
from app.services.ocr_engine import create_ocr_engine

# このルーターで定義するエンドポイントの共通設定です
# tags は自動生成される API ドキュメントでグループ名として使われます
router = APIRouter(tags=["jobs"])


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
    """指定されたジョブの画像に対して OCR 処理を実行します。

    Args:
        job_id: OCR 処理対象のジョブ ID

    Returns:
        ジョブ ID、更新後の状態、OCR 認識結果テキスト

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

    # OCR エンジンを作成します
    # ocr-worker が設定されていればリモート呼び出し、なければモックにフォールバックします
    ocr_engine = create_ocr_engine(use_mock=False)

    try:
        # OCR 処理を実行します
        # 画像ファイルの相対パスを展開ディレクトリ内の絶対パスに変換します
        absolute_image_files = [
            str(Path(extract_dir) / image_file)
            for image_file in image_files
        ]
        result = ocr_engine.run(
            image_files=absolute_image_files,
            work_dir=Path(extract_dir),
        )
    except Exception as exc:
        # OCR 処理中にエラーが発生した場合は FAILED 状態に更新します
        job_manager.update_job_with_ocr_result(
            job_id,
            success=False,
            message=f"OCR 処理に失敗しました: {exc}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"OCR 処理に失敗しました: {exc}",
        ) from exc

    # OCR 結果をジョブ情報に保存します
    job_manager.update_job_with_ocr_result(
        job_id,
        success=True,
        text=result.text,
        output_dir=str(result.output_dir),
    )

    # レスポンスモデルに合わせて返却します
    return JobOcrResponse(
        job_id=job_id,
        status=JobStatus.COMPLETED,
        text=result.text,
    )
