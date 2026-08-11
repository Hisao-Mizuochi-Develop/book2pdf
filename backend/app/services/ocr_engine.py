"""OCR エンジンのラッパーサービスです。

このモジュールでは、国立国会図書館の ndlocr_cli を利用して
画像ファイルに対する OCR 処理を実行する機能を提供します。

実行環境に応じて以下の 3 つの実装から選択します。
- RemoteNdloCrOcrEngine: ocr-worker コンテナの HTTP API を呼び出す（本番用）
- NdloCrOcrEngine: 同じコンテナ内の ndlocr_cli を直接 import して実行
- MockOcrEngine: テスト・開発用のモック
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# 抽象基底クラスを定義するための import です
# 異なる OCR エンジン実装を共通のインターフェースで扱えるようにします
from abc import ABC, abstractmethod

# 環境変数を読み込むための標準ライブラリです
# ocr-worker の URL を取得するために使用します
import os

# ファイルをコピーするための標準ライブラリです
# ndlocr_cli 用の入力ディレクトリを作成する際に使用します
from shutil import copy2

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
from pathlib import Path

# HTTP クライアントです
# ocr-worker コンテナの API を呼び出すために使用します
import httpx

# ndlocr_cli が利用可能かどうかを確認します
# 利用できない環境ではモック実装にフォールバックします
try:
    # 国立国会図書館の OCR 推論クラスを読み込みます
    from cli.core import OcrInferrer

    # import に成功した場合は True を設定します
    _NDLOCR_AVAILABLE = True
except Exception:  # pragma: no cover
    # ndlocr_cli がインストールされていないか、依存 submodule が不足しています
    _NDLOCR_AVAILABLE = False


class OcrResult:
    """OCR 処理の結果を表すクラスです。"""

    def __init__(self, text: str, output_dir: Path, success: bool = True) -> None:
        """OCR 結果を初期化します。

        Args:
            text: 認識されたテキスト全体
            output_dir: OCR 結果が出力されたディレクトリ
            success: 処理が成功したかどうか
        """
        # 認識結果のテキスト本文です
        self.text = text

        # OCR 結果が保存されたディレクトリのパスです
        self.output_dir = output_dir

        # 処理が成功したかどうかを示すフラグです
        self.success = success


class BaseOcrEngine(ABC):
    """OCR エンジンの共通インターフェースです。

    異なる OCR 実装（リモートの ocr-worker、同じコンテナ内の ndlocr_cli、モックなど）を
    同じ使い方で切り替えられるようにするための抽象クラスです。
    """

    @abstractmethod
    def run(self, image_files: list[str], work_dir: Path) -> OcrResult:
        """画像ファイルに対して OCR 処理を実行します。

        Args:
            image_files: OCR 対象の画像ファイルパスのリスト
            work_dir: OCR 処理に使用する作業ディレクトリ

        Returns:
            OCR 処理結果
        """
        ...


class RemoteNdloCrOcrEngine(BaseOcrEngine):
    """ocr-worker コンテナの HTTP API を呼び出す OCR エンジンです。

    backend コンテナと ocr-worker コンテナが別れている環境で使用します。
    """

    def __init__(
        self,
        worker_url: str,
        config_file: str | Path = "/opt/ocr-worker/config.yml",
    ) -> None:
        """エンジンを初期化します。

        Args:
            worker_url: ocr-worker のベース URL（例: http://ocr-worker:8001）
            config_file: ocr-worker コンテナ内の ndlocr_cli 設定ファイルパス
        """
        # 末尾のスラッシュを取り除いて URL を保持します
        self.worker_url = worker_url.rstrip("/")

        # ocr-worker コンテナ内の設定ファイルパスを保持します
        self.config_file = str(config_file)

    def run(self, image_files: list[str], work_dir: Path) -> OcrResult:
        """画像ファイルに対して OCR 処理を実行します。

        Args:
            image_files: OCR 対象の画像ファイルパスのリスト
            work_dir: OCR 処理に使用する作業ディレクトリ

        Returns:
            OCR 処理結果
        """
        # ndlocr_cli の single 形式の入力ディレクトリを作成します
        # input_root/img/ の下に画像ファイルを配置します
        input_root = work_dir / "input"
        img_dir = input_root / "img"
        img_dir.mkdir(parents=True, exist_ok=True)

        # すべての画像ファイルを入力ディレクトリにコピーします
        for src_path in image_files:
            src = Path(src_path)
            dst = img_dir / src.name
            copy2(src, dst)

        # OCR の出力先ディレクトリを作成します
        output_root = work_dir / "output"
        output_root.mkdir(parents=True, exist_ok=True)

        # ocr-worker の /ocr エンドポイントに送信するリクエストボディです
        request_body = {
            "input_root": str(input_root),
            "output_root": str(output_root),
            "config_file": self.config_file,
            "proc_range": "0..3",
            "save_image": False,
            "save_xml": True,
            "dump": False,
            "input_structure": "s",
            "ruby_only": False,
        }

        # ocr-worker に HTTP POST で OCR 実行をリクエストします
        # OCR は数分かかることがあるため、タイムアウトを長めに設定します
        response = httpx.post(
            f"{self.worker_url}/ocr",
            json=request_body,
            timeout=600.0,
        )

        # HTTP エラーがあれば例外を発生させます
        response.raise_for_status()

        # レスポンス JSON を取得します
        data = response.json()

        # OCR 結果を返します
        return OcrResult(
            text=data.get("text", ""),
            output_dir=Path(data.get("output_dir", str(output_root))),
        )


class NdloCrOcrEngine(BaseOcrEngine):
    """ndlocr_cli を利用した OCR エンジンです。

    backend と ocr-worker が同じコンテナ内にいる場合や、
    ndlocr_cli を直接インストールした環境で使用します。
    """

    def __init__(self, config_file: str | Path = "config.yml") -> None:
        """エンジンを初期化します。

        Args:
            config_file: ndlocr_cli 用の設定ファイルパス
        """
        # ndlocr_cli の設定ファイルパスを保持します
        self.config_file = str(config_file)

    def run(self, image_files: list[str], work_dir: Path) -> OcrResult:
        """画像ファイルに対して OCR 処理を実行します。

        Args:
            image_files: OCR 対象の画像ファイルパスのリスト
            work_dir: OCR 処理に使用する作業ディレクトリ

        Returns:
            OCR 処理結果
        """
        # ndlocr_cli が利用できない場合は実行できません
        if not _NDLOCR_AVAILABLE:
            raise RuntimeError("ndlocr_cli が利用できない環境で OCR を実行しようとしました")

        # ndlocr_cli の single 形式の入力ディレクトリを作成します
        # input_root/img/ の下に画像ファイルを配置します
        input_root = work_dir / "input"
        img_dir = input_root / "img"
        img_dir.mkdir(parents=True, exist_ok=True)

        # すべての画像ファイルを入力ディレクトリにコピーします
        for src_path in image_files:
            src = Path(src_path)
            dst = img_dir / src.name
            copy2(src, dst)

        # OCR の出力先ディレクトリを作成します
        output_root = work_dir / "output"
        output_root.mkdir(parents=True, exist_ok=True)

        # ndlocr_cli 用の設定辞書を作成します
        # proc_range "0..3" は ノド元分割〜文字認識までの全処理を意味します
        cfg = {
            "input_root": str(input_root),
            "output_root": str(output_root),
            "config_file": self.config_file,
            "proc_range": "0..3",
            "save_image": False,
            "save_xml": True,
            "dump": False,
            "input_structure": "s",
            "ruby_only": False,
        }

        # 設定を解析して ndlocr_cli 用の形式に変換します
        from cli.core import utils as ndlocr_utils

        infer_cfg = ndlocr_utils.parse_cfg(cfg)
        if infer_cfg is None:
            raise RuntimeError("ndlocr_cli の設定解析に失敗しました")

        # 出力ディレクトリを準備します
        infer_cfg["output_root"] = ndlocr_utils.mkdir_with_duplication_check(
            infer_cfg["output_root"]
        )

        # OCR 推論を実行します
        inferrer = OcrInferrer(infer_cfg)
        inferrer.run()

        # 出力ディレクトリからテキストファイルを収集します
        result_text = self._collect_text(output_root)

        # OCR 結果を返します
        return OcrResult(text=result_text, output_dir=Path(infer_cfg["output_root"]))

    def _collect_text(self, output_root: Path) -> str:
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


class MockOcrEngine(BaseOcrEngine):
    """テスト・開発用のモック OCR エンジンです。

    ndlocr_cli がインストールされていない環境で、
    OCR 処理の流れを確認するために使用します。
    """

    def run(self, image_files: list[str], work_dir: Path) -> OcrResult:
        """画像ファイル名をもとにモックの OCR 結果を返します。

        Args:
            image_files: OCR 対象の画像ファイルパスのリスト
            work_dir: OCR 処理に使用する作業ディレクトリ

        Returns:
            モックの OCR 処理結果
        """
        # 出力先ディレクトリを作成します
        output_root = work_dir / "output"
        output_root.mkdir(parents=True, exist_ok=True)

        # 各画像ファイル名からモックテキストを生成します
        lines: list[str] = []
        for image_path in image_files:
            # ファイル名だけを取り出します
            name = Path(image_path).name
            # 「ファイル名の画像から認識されたテキスト」という形式のモック結果です
            lines.append(f"{name} から認識されたテキスト")

        # モック結果を結合します
        result_text = "\n".join(lines)

        # モックの OCR 結果を返します
        return OcrResult(text=result_text, output_dir=output_root)


def create_ocr_engine(use_mock: bool = False) -> BaseOcrEngine:
    """利用可能な OCR エンジンのインスタンスを作成します。

    優先順位:
    1. 明示的にモックが指定された場合はモック
    2. OCR_WORKER_URL 環境変数が設定されていればリモートの ocr-worker
    3. 同じコンテナ内に ndlocr_cli があれば直接実行
    4. それ以外はモック

    Args:
        use_mock: モックエンジンを強制的に使用するかどうか

    Returns:
        BaseOcrEngine を実装した OCR エンジンインスタンス
    """
    # 明示的にモックが指定された場合はモックを返します
    if use_mock:
        return MockOcrEngine()

    # ocr-worker の URL が設定されていればリモートエンジンを返します
    worker_url = os.environ.get("OCR_WORKER_URL")
    if worker_url:
        return RemoteNdloCrOcrEngine(worker_url=worker_url)

    # ndlocr_cli が利用可能な場合は本物のエンジンを返します
    if _NDLOCR_AVAILABLE:
        return NdloCrOcrEngine()

    # それ以外の場合はモックを返します
    return MockOcrEngine()
