"""OCR ジョブに関連するデータモデルを定義します。

Pydantic を使って、API で受け渡しするデータの型とルールを宣言します。
これにより、FastAPI が自動的にリクエストの検証やレスポンスの整形を行ってくれます。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法（list[str] など）を使えるようになります
from __future__ import annotations

# ジョブの状態を列挙型（Enum）として定義するための import です
from enum import Enum

# API で受け渡すデータの型とルールを宣言するための import です
# FastAPI がリクエストの検証やレスポンスの整形を自動で行ってくれます
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """OCR ジョブの状態を表す列挙型です。

    str と Enum を同時に継承すると、JSON への変換時に文字列として扱われます。
    """

    PENDING = "pending"      # ジョブが作成され、処理待ちの状態
    UPLOADED = "uploaded"    # ZIP アップロード・展開が完了した状態
    PROCESSING = "processing"  # OCR 処理中の状態
    COMPLETED = "completed"  # 処理が正常に完了した状態
    FAILED = "failed"        # 処理中にエラーが発生した状態


class JobCreateResponse(BaseModel):
    """ジョブ作成 API のレスポンスモデルです。"""

    # クライアントが後からジョブ状態を確認する際に使う一意な識別子です
    job_id: str = Field(..., description="作成されたジョブの一意な ID")

    # ジョブの現在の状態を表します
    # 初期状態は PENDING（処理待ち）です
    status: JobStatus = Field(..., description="ジョブの現在の状態")


class JobResponse(BaseModel):
    """ジョブ状態取得 API のレスポンスモデルです。"""

    # 確認対象のジョブを識別するための ID です
    job_id: str = Field(..., description="ジョブの一意な ID")

    # ジョブの現在の状態を表します
    status: JobStatus = Field(..., description="ジョブの現在の状態")

    # エラー発生時などにユーザーに伝える補足メッセージです
    # 通常時は空文字列になります
    message: str = Field(default="", description="補足メッセージ（エラー時など）")

    # ZIP 展開後に抽出された画像ファイルの相対パス一覧です
    # 画像がない場合や未アップロード時は空のリストになります
    files: list[str] = Field(
        default_factory=list,
        description="展開された画像ファイルの相対パス一覧",
    )


class JobUploadResponse(BaseModel):
    """ZIP アップロード API のレスポンスモデルです。"""

    # アップロード対象のジョブを識別するための ID です
    job_id: str = Field(..., description="ジョブの一意な ID")

    # アップロード成功後は UPLOADED 状態になります
    status: JobStatus = Field(..., description="ジョブの現在の状態")

    # 展開された画像ファイルの相対パス一覧です
    # 後続の OCR 処理でこの順序を使用します
    files: list[str] = Field(
        default_factory=list,
        description="展開された画像ファイルの相対パス一覧",
    )


class JobOcrResponse(BaseModel):
    """OCR 実行 API のレスポンスモデルです。"""

    # OCR 処理対象のジョブを識別するための ID です
    job_id: str = Field(..., description="ジョブの一意な ID")

    # OCR 処理後は COMPLETED または FAILED 状態になります
    status: JobStatus = Field(..., description="ジョブの現在の状態")

    # OCR によって認識されたテキスト全文です
    # 処理中や失敗時は空文字列になることがあります
    text: str = Field(default="", description="OCR 認識結果のテキスト")

    # 補足メッセージ（エラー時など）です
    message: str = Field(default="", description="補足メッセージ")
