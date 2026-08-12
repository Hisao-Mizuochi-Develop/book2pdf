"""ocr-worker の FastAPI アプリケーションです。

backend コンテナから HTTP で OCR 実行をリクエストされ、
コンテナ内の ndlocr_cli を使って OCR 処理を行います。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
from pathlib import Path

# 現在日時を取得するための標準ライブラリです
# 進捗ファイルに更新時刻を記録するために使用します
from datetime import datetime, timezone

# JSON 形式で進捗ファイルを書き出すための標準ライブラリです
import json

# ファイル操作でディレクトリ作成が必要なための標準ライブラリです
import os

# ログ出力のための標準ライブラリです
# 環境変数 LOG_LEVEL で出力レベルを切り替えます
import logging

# 処理時間を計測するための標準ライブラリです
import time

# FastAPI の機能を読み込みます
# FastAPI: アプリケーション本体
# HTTPException: HTTP エラーレスポンスを返す
from fastapi import FastAPI, HTTPException

# 非同期処理中に同期処理をスレッドプールで実行するための機能です
# OCR 処理は重いため、イベントループをブロックしないようにします
from fastapi.concurrency import run_in_threadpool

# リクエスト・レスポンスの型とルールを宣言するための import です
from pydantic import BaseModel, Field

# ndlocr_cli の OCR 推論クラスを読み込みます
from cli.core import OcrInferrer

# ndlocr_cli のユーティリティ関数を読み込みます
from cli.core import utils as ndlocr_utils

# Hydra のグローバルインスタンスをクリアするための import です
# 同一プロセス内で複数回 ndlocr_cli を実行する際に、設定の再初期化を可能にします
from hydra.core.global_hydra import GlobalHydra

# アプリケーション全体のログレベルを設定します
# uvicorn 起動前に設定することで、各モジュールの DEBUG ログも出力されます
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# 本モジュール用のロガーを取得します
logger = logging.getLogger(__name__)

# FastAPI アプリケーションを作成します
app = FastAPI(title="ocr-worker")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """ヘルスチェック用エンドポイントです。

    Returns:
        正常状態を示す JSON レスポンス
    """
    return {"status": "ok"}


class OcrRequest(BaseModel):
    """OCR 実行リクエストのモデルです。"""

    # OCR 対象の画像が配置されたディレクトリのパスです
    # ndlocr_cli の single 形式では input_root/img/ 以下に画像を配置します
    input_root: str = Field(..., description="OCR 対象画像の親ディレクトリパス")

    # OCR 結果の出力先ディレクトリのパスです
    output_root: str = Field(..., description="OCR 結果の出力先ディレクトリパス")

    # ndlocr_cli 用の設定ファイルパスです
    config_file: str = Field(
        default="/app/ndlocr_cli/config.yml",
        description="ndlocr_cli 用の設定ファイルパス",
    )

    # 実行する処理範囲です
    # "0..3" は ノド元分割〜文字認識までの全処理を意味します
    proc_range: str = Field(default="0..3", description="処理範囲")

    # 中間画像を保存するかどうかです
    save_image: bool = Field(default=False, description="中間画像を保存するかどうか")

    # XML 形式の結果を保存するかどうかです
    save_xml: bool = Field(default=True, description="XML 結果を保存するかどうか")

    # 入力構造の形式です
    # "s" は single 形式（1つのディレクトリに画像を配置）を意味します
    input_structure: str = Field(default="s", description="入力構造の形式")

    # ルビのみを対象とするかどうかです
    ruby_only: bool = Field(default=False, description="ルビのみを対象とするかどうか")

    # デバッグ用ダンプを出力するかどうかです
    dump: bool = Field(default=False, description="デバッグ用ダンプを出力するかどうか")

    # 進捗通知用のジョブ ID です
    # backend 側で SSE 配信を行う際に、どのジョブの進捗かを識別するために使用します
    job_id: str | None = Field(default=None, description="進捗通知用のジョブ ID")


class OcrResponse(BaseModel):
    """OCR 実行レスポンスのモデルです。"""

    # OCR 処理が成功したかどうかです
    success: bool = Field(..., description="処理成否")

    # 認識されたテキスト全文です
    text: str = Field(default="", description="認識テキスト")

    # OCR 結果が出力されたディレクトリのパスです
    output_dir: str = Field(default="", description="OCR 結果の出力ディレクトリパス")

    # 補足メッセージ（エラー時など）です
    message: str = Field(default="", description="補足メッセージ")


def _collect_text(output_root: Path) -> str:
    """OCR 出力ディレクトリからテキストを収集します。

    Args:
        output_root: OCR 結果のルートディレクトリ

    Returns:
        収集したテキスト全文
    """
    # テキストファイルの一覧を格納するリストです
    text_files: list[Path] = []

    # output_root 以下の txt ディレクトリを再帰的に探します
    for txt_dir in output_root.rglob("txt"):
        # ディレクトリ内の .txt ファイルを取得します
        text_files.extend(txt_dir.glob("*.txt"))

    # ファイル名順にソートして安定した順序を保ちます
    text_files.sort()

    # 各テキストファイルの内容を連結します
    parts: list[str] = []
    for text_file in text_files:
        # UTF-8 としてファイルを読み込みます
        parts.append(text_file.read_text(encoding="utf-8"))

    # 連結したテキストを返します
    return "\n".join(parts)


# OCR 対象として扱う画像ファイルの拡張子一覧です
# これらの拡張子を持つファイルを画像としてカウントします
_IMAGE_EXTENSIONS: set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
    ".bmp",
    ".gif",
}


def _count_images(input_root: str) -> int:
    """入力ディレクトリ内の画像ファイル数を数えます。

    Args:
        input_root: OCR 対象画像の親ディレクトリパス

    Returns:
        画像ファイルの総数
    """
    # ndlocr_cli の single 形式では input_root/img/ 以下に画像を配置します
    img_dir = Path(input_root) / "img"

    # 画像ディレクトリが存在しない場合は 0 ページとします
    if not img_dir.exists():
        return 0

    # 画像ファイルの数を数えます
    count = 0
    for file_path in img_dir.iterdir():
        # ファイルかつ対象拡張子の場合のみカウントします
        if file_path.is_file() and file_path.suffix.lower() in _IMAGE_EXTENSIONS:
            count += 1

    return count


def _write_progress(
    job_id: str | None,
    status: str,
    progress: float,
    current_page: int = 0,
    total_pages: int = 0,
    message: str = "",
) -> None:
    """進捗情報を共有ファイルに書き出します。

    Args:
        job_id: 進捗通知対象のジョブ ID（未設定時は何もしません）
        status: ジョブの状態文字列
        progress: 進捗率（0.0 〜 1.0）
        current_page: 現在処理中のページ番号
        total_pages: 処理対象の総ページ数
        message: 補足メッセージ
    """
    # job_id が指定されていない場合は進捗書き出しを行いません
    if job_id is None:
        return

    # 進捗ファイルの保存先ディレクトリです
    # docker-compose.yml で backend と共有しています
    progress_dir = Path("/data/progress")

    # ディレクトリが存在しない場合は作成します
    progress_dir.mkdir(parents=True, exist_ok=True)

    # ジョブ ID ごとに JSON ファイルを作成します
    progress_file = progress_dir / f"{job_id}.json"

    # 現在時刻を UTC で ISO 8601 形式で取得します
    now = datetime.now(timezone.utc).isoformat()

    # 進捗情報を辞書にまとめます
    data = {
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "current_page": current_page,
        "total_pages": total_pages,
        "message": message,
        "timestamp": now,
    }

    # JSON 形式でファイルに書き出します
    progress_file.write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )


@app.post("/ocr", response_model=OcrResponse)
async def run_ocr(request: OcrRequest) -> OcrResponse:
    """OCR 処理を実行するエンドポイントです。

    Args:
        request: OCR 実行リクエスト

    Returns:
        OCR 実行結果

    Raises:
        HTTPException: OCR 処理に失敗した場合
    """
    # 進捗通知に使用するジョブ ID を取得します
    job_id = request.job_id

    # 処理対象の総ページ数（画像数）を事前に数えます
    total_pages = _count_images(request.input_root)

    # ndlocr_cli 用の設定辞書を作成します
    cfg = {
        "input_root": request.input_root,
        "output_root": request.output_root,
        "config_file": request.config_file,
        "proc_range": request.proc_range,
        "save_image": request.save_image,
        "save_xml": request.save_xml,
        "dump": request.dump,
        "input_structure": request.input_structure,
        "ruby_only": request.ruby_only,
    }

    try:
        # OCR 処理開始を進捗ファイルに記録します
        _write_progress(
            job_id,
            status="processing",
            progress=0.0,
            current_page=0,
            total_pages=total_pages,
            message="OCR 処理を開始しました",
        )

        # Hydra のグローバルインスタンスをクリアします
        # 同一プロセス内で複数回 ndlocr_cli を実行する際に、設定の再初期化を可能にします
        if GlobalHydra.instance().is_initialized():
            GlobalHydra.instance().clear()

        # 設定を解析して ndlocr_cli 用の形式に変換します
        # OCR の初期化は重い可能性があるため、スレッドプールで実行します
        infer_cfg = await run_in_threadpool(ndlocr_utils.parse_cfg, cfg)
        if infer_cfg is None:
            raise RuntimeError("ndlocr_cli の設定解析に失敗しました")

        # 出力ディレクトリを準備します
        infer_cfg["output_root"] = await run_in_threadpool(
            ndlocr_utils.mkdir_with_duplication_check,
            infer_cfg["output_root"],
        )

        # OCR 推論インスタンスを作成します
        inferrer = await run_in_threadpool(OcrInferrer, infer_cfg)

        # OCR 処理の実行時間を計測します
        logger.debug("OCR 処理を開始します: job_id=%s, total_pages=%d", job_id, total_pages)
        ocr_start_time = time.time()

        # OCR 処理を実行します
        await run_in_threadpool(inferrer.run)

        # OCR 処理の実行時間を計算します
        ocr_elapsed = time.time() - ocr_start_time
        ocr_avg = ocr_elapsed / total_pages if total_pages > 0 else 0.0
        logger.debug(
            "OCR 処理が完了しました: job_id=%s, elapsed=%.3fs, avg_per_page=%.3fs",
            job_id,
            ocr_elapsed,
            ocr_avg,
        )

        # 出力ディレクトリからテキストファイルを収集します
        result_text = await run_in_threadpool(
            _collect_text,
            Path(infer_cfg["output_root"]),
        )

        # OCR 処理完了を進捗ファイルに記録します
        _write_progress(
            job_id,
            status="completed",
            progress=1.0,
            current_page=total_pages,
            total_pages=total_pages,
            message="OCR 処理が完了しました",
        )

        # OCR 結果を返します
        return OcrResponse(
            success=True,
            text=result_text,
            output_dir=infer_cfg["output_root"],
            message="",
        )
    except Exception as exc:
        # エラー発生を進捗ファイルに記録します
        _write_progress(
            job_id,
            status="failed",
            progress=0.0,
            current_page=0,
            total_pages=total_pages,
            message=f"OCR 処理に失敗しました: {exc}",
        )

        # エラーが発生した場合は HTTP 500 エラーを返します
        raise HTTPException(
            status_code=500,
            detail=f"OCR 処理に失敗しました: {exc}",
        ) from exc
