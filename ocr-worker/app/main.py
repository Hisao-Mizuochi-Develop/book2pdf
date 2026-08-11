"""ocr-worker の FastAPI アプリケーションです。

backend コンテナから HTTP で OCR 実行をリクエストされ、
コンテナ内の ndlocr_cli を使って OCR 処理を行います。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
from pathlib import Path

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

        # OCR 処理を実行します
        await run_in_threadpool(inferrer.run)

        # 出力ディレクトリからテキストファイルを収集します
        result_text = await run_in_threadpool(
            _collect_text,
            Path(infer_cfg["output_root"]),
        )

        # OCR 結果を返します
        return OcrResponse(
            success=True,
            text=result_text,
            output_dir=infer_cfg["output_root"],
            message="",
        )
    except Exception as exc:
        # エラーが発生した場合は HTTP 500 エラーを返します
        raise HTTPException(
            status_code=500,
            detail=f"OCR 処理に失敗しました: {exc}",
        ) from exc
