"""ocr-worker の FastAPI アプリケーションです。

backend コンテナから HTTP で OCR 実行をリクエストされ、
コンテナ内の ndlocr_cli を使って OCR 処理を行います。
"""

# 型注釈を文字列として遅延評価できるようにするための標準ライブラリです
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# 標準ライブラリ — アプリケーションのログ出力を管理する
# 環境変数 LOG_LEVEL で出力レベルを切り替える
import logging

# 標準ライブラリ — OS とのファイルシステム操作を提供する
# os.makedirs() で出力ディレクトリを作成するために使用する
import os

# 標準ライブラリ — 一時ディレクトリと一時ファイルの作成を行う
# 前処理済み画像の一時保存先として tempfile.mkdtemp() を使用する
import tempfile

# 標準ライブラリ — 処理時間を計測する
# OCR 実行開始・終了時刻の差分を計測してログに出力する
import time

# 標準ライブラリ — job_id が未指定の場合に一意な ID を発行します
# BE009001: リクエスト側が job_id を省略した場合に使用します
import uuid

# 現在日時を取得するための標準ライブラリです
# 進捗ファイルに更新時刻を記録するために使用します
from datetime import datetime, timezone

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
# Path("/data/jobs") のように OS 非依存のパス操作を提供する
from pathlib import Path

# 外部ライブラリ（ndlocr_cli）— OCR 推論エンジン
# OcrInferrer: 画像からテキストを抽出するメインクラス
from cli.core import OcrInferrer

# 外部ライブラリ（ndlocr_cli）— OCR ユーティリティ関数群
# 画像の前処理・後処理に使用する補助関数
from cli.core import utils as ndlocr_utils

# SY002002: in-memory 進捗ストア操作とキャンセル管理を行うモジュールです
from cli.core.progress_reporter import (
    delete_progress,
    is_cancelled,
    mark_cancelled,
)
from cli.core.progress_reporter import (
    get_progress as get_progress_from_store,
)

# BE009001: OCR 結果の非同期一時保存用インメモリストアです
import app.result_store as result_store

# 外部ライブラリ — FastAPI Web フレームワーク
# FastAPI: アプリケーション本体を構築, HTTPException: HTTP エラーレスポンスを返す
# BackgroundTasks: レスポンス後に非同期タスクを実行するための依存関係です
from fastapi import BackgroundTasks, FastAPI, HTTPException

# 外部ライブラリ — FastAPI の非同期処理補助機能
# run_in_threadpool: 同期処理（OCR 等の重い処理）をスレッドプールで実行し、イベントループをブロックしないようにする
from fastapi.concurrency import run_in_threadpool

# 外部ライブラリ（Hydra）— 設定管理フレームワークのグローバルインスタンス
# GlobalHydra.instance().clear(): 同一プロセス内で複数回 ndlocr_cli を実行する際に、設定の再初期化を可能にする
from hydra.core.global_hydra import GlobalHydra

# 外部ライブラリ — Python Imaging Library（画像処理）
# Image.open(): 画像ファイルを開く, ImageFilter: 画像フィルタ（シャープ化等）
from PIL import Image, ImageFilter

# 外部ライブラリ — データ検証・シリアライズライブラリ
# BaseModel: API のリクエスト・レスポンス型を定義, Field: フィールドの制約（デフォルト値等）を設定
from pydantic import BaseModel, Field

# アプリケーション全体のログレベルを設定します
# uvicorn 起動前に設定することで、各モジュールの DEBUG ログも出力されます
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# 本モジュール用のロガーを取得します
logger = logging.getLogger(__name__)

# 前処理の有無を環境変数で制御します
# デフォルトは ON（true）です
PREPROCESS_ENABLED = os.environ.get("PREPROCESS_ENABLED", "true").lower() in ("true", "1", "yes", "on")

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

    # 進捗ファイルへの書き込みを有効にするかどうかです
    # backend から呼び出される場合は False にして、backend 側が進捗を管理します
    enable_progress: bool = Field(default=True, description="進捗ファイルへの書き込みを有効にするかどうか")


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


class OcrAcceptedResponse(BaseModel):
    """BE009001: POST /ocr の即時受理レスポンスモデルです。"""

    # 受付メッセージです
    message: str = Field(..., description="受付メッセージ")

    # バックグラウンド OCR タスクを識別するジョブ ID です
    job_id: str = Field(..., description="ジョブ ID")


class OcrResultResponse(BaseModel):
    """BE009001: GET /result/{job_id} の成功レスポンスモデルです。"""

    # 認識されたテキスト全文です
    text: str = Field(..., description="認識テキスト")

    # OCR 結果が出力されたディレクトリのパスです
    output_dir: str = Field(..., description="OCR 結果の出力ディレクトリパス")


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


def _preprocess_image(src_path: Path, dst_path: Path) -> None:
    """画像に sharpen_light_upscale_2x 前処理を適用して保存します。

    Args:
        src_path: 元画像のパス
        dst_path: 前処理済み画像の出力パス
    """
    # 元画像を読み込みます
    with Image.open(src_path) as img:
        # 必要に応じて RGB 変換します（PNG の透過チャンネル対応）
        if img.mode != "RGB":
            img = img.convert("RGB")

        # 2 倍アップスケール（LANCZOS 補間）
        new_size = (img.width * 2, img.height * 2)
        img = img.resize(new_size, Image.Resampling.LANCZOS)

        # 軽度シャープニング
        # OW003003 で最も効果的だったパラメータです
        img = img.filter(
            ImageFilter.UnsharpMask(radius=2, percent=80, threshold=3)
        )

        # 出力ディレクトリがなければ作成します
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # 前処理済み画像を保存します
        img.save(dst_path, format=src_path.suffix.lstrip(".").upper() or "PNG")


def _preprocess_input_root(input_root: str, job_id: str | None) -> tuple[str, Path]:
    """input_root 以下の画像を前処理し、一時ディレクトリに出力します。

    Args:
        input_root: 元の入力ディレクトリパス
        job_id: 進捗通知用のジョブ ID（一時ディレクトリ名に使用）

    Returns:
        (前処理済みの input_root パス, 一時ディレクトリの Path)
    """
    src_root = Path(input_root)
    src_img_dir = src_root / "img"

    # 一時ディレクトリを作成します
    # job_id があれば識別しやすい名前にします
    suffix = f"_{job_id}" if job_id else ""
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"ocr_preprocess{suffix}_"))
    dst_root = tmp_dir / "input"
    dst_img_dir = dst_root / "img"

    logger.debug(
        "前処理を開始します: src=%s, dst=%s",
        src_img_dir,
        dst_img_dir,
    )

    # 対象画像を前処理してコピーします
    processed_count = 0
    for src_path in sorted(src_img_dir.iterdir()):
        if not src_path.is_file():
            continue
        if src_path.suffix.lower() not in _IMAGE_EXTENSIONS:
            continue

        dst_path = dst_img_dir / src_path.name
        _preprocess_image(src_path, dst_path)
        processed_count += 1

    logger.debug(
        "前処理が完了しました: processed_count=%d, dst_root=%s",
        processed_count,
        dst_root,
    )

    return str(dst_root), tmp_dir


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
    """進捗情報を in-memory ストアに書き出します。

    SY002002: ocr-worker コンテナ内の in-memory ストアに保存します。
    backend コンテナから HTTP (GET /progress/{job_id}) で参照されます。

    Args:
        job_id: 進捗通知対象のジョブ ID（未設定時は何もしません）
        status: ジョブの状態文字列
        progress: 進捗率（0.0 〜 1.0）
        current_page: 現在処理中のページ番号
        total_pages: 処理対象の総ページ数
        message: 補足メッセージ
    """
    if job_id is None:
        return

    from cli.core.progress_reporter import _progress_store

    _progress_store[job_id] = {
        "job_id": job_id,
        "status": status,
        "progress": round(progress, 2),
        "current_page": current_page,
        "total_pages": total_pages,
        "message": message,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


@app.post("/cancel/{job_id}")
async def cancel_ocr(job_id: str) -> dict[str, str]:
    """指定したジョブの OCR 処理をキャンセルマークします。

    SY002002: backend からのキャンセル要求を受け取り、OCR 処理が完了した際に
    結果を破棄するために使用します。処理中のスレッドを強制終了することはできないため、
    協調的キャンセルとして動作します。

    Args:
        job_id: キャンセル対象のジョブ ID。

    Returns:
        キャンセル受付結果。
    """
    mark_cancelled(job_id)
    logger.info("OCR キャンセルを受け付けました: job_id=%s", job_id)
    return {"message": "キャンセル要求を受け付けました", "job_id": job_id}


@app.delete("/progress/{job_id}")
async def delete_progress_endpoint(job_id: str) -> dict[str, str]:
    """指定したジョブの進捗データを削除します。

    SY002002: backend からのクリーンアップ要求を受け取り、ocr-worker 内の
    in-memory 進捗ストアから該当ジョブのデータを削除します。

    Args:
        job_id: 削除対象のジョブ ID。

    Returns:
        削除結果。
    """
    delete_progress(job_id)
    logger.info("進捗データを削除しました: job_id=%s", job_id)
    return {"message": "進捗データを削除しました", "job_id": job_id}


class OcrProgressResponse(BaseModel):
    """OCR 進捗取得レスポンスのモデルです。"""

    job_id: str = Field(..., description="ジョブ ID")
    current_page: int = Field(..., description="現在処理済みのページ数")
    total_pages: int = Field(..., description="処理対象の総ページ数")
    progress: float = Field(..., description="進捗率（0.0〜1.0）")
    status: str = Field(..., description="処理状態")
    message: str = Field(..., description="進捗メッセージ")
    timestamp: str = Field(..., description="更新時刻（ISO 8601）")


@app.get("/progress/{job_id}")
async def get_progress(job_id: str) -> OcrProgressResponse:
    """指定したジョブの OCR 処理進捗を取得します。

    SY002002: backend の _progress_event_generator から 1秒間隔でポーリングされます。

    Args:
        job_id: ジョブ ID。

    Returns:
        進捗情報。

    Raises:
        HTTPException: 進捗情報が見つからない場合（404）。
    """
    data = get_progress_from_store(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="進捗情報が見つかりません")

    return OcrProgressResponse(
        job_id=data["job_id"],
        current_page=data["current_page"],
        total_pages=data["total_pages"],
        progress=data["progress"],
        status=data["status"],
        message=data["message"],
        timestamp=data["timestamp"],
    )


async def _run_ocr_background(request: OcrRequest, job_id: str) -> None:
    """BE009001: OCR 処理をバックグラウンドで実行し、結果ストアに保存します。

    Args:
        request: OCR 実行リクエスト
        job_id: 進捗通知・結果取得用のジョブ ID
    """
    # 進捗通知に使用するジョブ ID です（引数で確定済み）
    job_id_for_progress = job_id

    # 前処理済み一時ディレクトリ（前処理 ON の場合に設定）
    preprocess_tmp_dir: Path | None = None

    # 実際に ndlocr_cli に渡す input_root です
    # 前処理 ON の場合は一時ディレクトリ、OFF の場合はリクエスト値そのまま
    input_root_for_ocr = request.input_root

    try:
        # 前処理が有効な場合は画像を前処理します
        if PREPROCESS_ENABLED:
            logger.debug("前処理を適用します: job_id=%s", job_id)
            input_root_for_ocr, preprocess_tmp_dir = _preprocess_input_root(
                request.input_root,
                job_id,
            )
        else:
            logger.debug("前処理は無効化されています: job_id=%s", job_id)

        # 処理対象の総ページ数（画像数）を事前に数えます
        total_pages = _count_images(input_root_for_ocr)

        # ndlocr_cli 用の設定辞書を作成します
        cfg = {
            "input_root": input_root_for_ocr,
            "output_root": request.output_root,
            "config_file": request.config_file,
            "proc_range": request.proc_range,
            "save_image": request.save_image,
            "save_xml": request.save_xml,
            "dump": request.dump,
            "input_structure": request.input_structure,
            "ruby_only": request.ruby_only,
        }

        # OCR 処理開始を進捗ファイルに記録します
        # backend から呼び出される場合は enable_progress=False で抑制されます
        if request.enable_progress:
            _write_progress(
                job_id_for_progress,
                status="processing",
                progress=0.0,
                current_page=0,
                total_pages=total_pages,
                message=f"OCR 処理を開始しました（1/{total_pages}）",
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
        # FIX(OW004001): backend の SSE 連携のため job_id を設定します
        if job_id_for_progress:
            inferrer.job_id = job_id_for_progress

        # OCR 処理の実行時間を計測します
        logger.debug(
            "OCR 処理を開始します: job_id=%s, total_pages=%d",
            job_id_for_progress,
            total_pages,
        )
        ocr_start_time = time.time()

        # OCR 処理を実行します
        await run_in_threadpool(inferrer.run)

        # OCR 処理の実行時間を計算します
        ocr_elapsed = time.time() - ocr_start_time
        ocr_avg = ocr_elapsed / total_pages if total_pages > 0 else 0.0
        logger.debug(
            "OCR 処理が完了しました: job_id=%s, elapsed=%.3fs, avg_per_page=%.3fs",
            job_id_for_progress,
            ocr_elapsed,
            ocr_avg,
        )

        # 出力ディレクトリからテキストファイルを収集します
        result_text = await run_in_threadpool(
            _collect_text,
            Path(infer_cfg["output_root"]),
        )

        # キャンセル済みの場合は結果を破棄し failed 状態を保存します
        # OCR 処理中のスレッドを強制終了できないため、完了後に協調的に破棄します
        if is_cancelled(job_id_for_progress):
            logger.info(
                "キャンセル済みジョブの結果を破棄します: job_id=%s",
                job_id_for_progress,
            )
            cancel_message = "ジョブがキャンセルされました"
            if request.enable_progress:
                _write_progress(
                    job_id_for_progress,
                    status="cancelled",
                    progress=0.0,
                    current_page=0,
                    total_pages=total_pages,
                    message=cancel_message,
                )
            result_store.save_error(job_id, cancel_message)
            return

        # OCR 処理完了を進捗ファイルに記録します
        if request.enable_progress:
            _write_progress(
                job_id_for_progress,
                status="completed",
                progress=1.0,
                current_page=total_pages,
                total_pages=total_pages,
                message="OCR 処理が完了しました",
            )

        # OCR 結果をストアに保存します
        result_store.save_result(job_id, result_text, infer_cfg["output_root"])
        return
    except Exception as exc:
        # エラーのトレースバックを文字列に変換します
        # ログと結果ストアの両方に含めて、backend 側で原因を確認できるようにします
        import traceback

        tb_str = traceback.format_exc()
        error_message = f"OCR 処理に失敗しました: {exc}\n{tb_str}"

        # エラー内容をログに出力します
        logger.error(error_message)

        # エラー発生を進捗ファイルに記録します
        if request.enable_progress:
            _write_progress(
                job_id_for_progress,
                status="failed",
                progress=0.0,
                current_page=0,
                total_pages=total_pages,
                message=error_message,
            )

        # エラー発生を結果ストアに記録します
        result_store.save_error(job_id, error_message)
        return
    finally:
        # 前処理済み一時ディレクトリの cleanup を実施します
        if preprocess_tmp_dir is not None and preprocess_tmp_dir.exists():
            import shutil

            logger.debug(
                "前処理済み一時ディレクトリを削除します: %s",
                preprocess_tmp_dir,
            )
            shutil.rmtree(preprocess_tmp_dir)


@app.post("/ocr", response_model=OcrAcceptedResponse, status_code=202)
async def run_ocr(
    request: OcrRequest,
    background_tasks: BackgroundTasks,
) -> OcrAcceptedResponse:
    """BE009001: OCR 処理をバックグラウンドで開始します。

    Args:
        request: OCR 実行リクエスト
        background_tasks: レスポンス後に OCR 処理を実行するための FastAPI タスク

    Returns:
        202 Accepted とジョブ ID
    """
    # 進捗通知・結果取得に使用するジョブ ID を確定します
    # リクエスト側が指定しなければサーバー側で一意に発行します
    job_id = request.job_id or str(uuid.uuid4())

    # 結果ストアを processing 状態で初期化します
    # これにより、backend が即座に GET /result/{job_id} で問い合わせても
    # 404 ではなく 202 を返せます
    result_store.init_result(job_id)

    # バックグラウンドで OCR 処理を開始します
    # レスポンス送信後に非同期的に実行され、イベントループをブロックしません
    background_tasks.add_task(_run_ocr_background, request, job_id)

    logger.info("OCR 処理を受け付けました: job_id=%s", job_id)
    return OcrAcceptedResponse(
        message="OCR 処理を開始しました",
        job_id=job_id,
    )


@app.get("/result/{job_id}")
async def get_result(job_id: str) -> OcrResultResponse:
    """BE009001: OCR 処理結果を取得します。

    Args:
        job_id: 対象のジョブ ID

    Returns:
        完了時はテキストと出力ディレクトリ

    Raises:
        HTTPException: 処理中（202）、失敗（500）、または存在しない場合（404）
    """
    result = result_store.get_result(job_id)
    if result is None:
        logger.debug("指定されたジョブの結果が見つかりません: job_id=%s", job_id)
        raise HTTPException(
            status_code=404,
            detail="指定されたジョブが見つかりません",
        )

    status = result.get("status")
    if status == "processing":
        raise HTTPException(status_code=202, detail="OCR 処理中です")
    if status == "failed":
        message = result.get("message") or "OCR 処理に失敗しました"
        logger.debug("OCR 失敗結果を返します: job_id=%s", job_id)
        raise HTTPException(status_code=500, detail=message)

    return OcrResultResponse(
        text=result.get("text", ""),
        output_dir=result.get("output_dir", ""),
    )

