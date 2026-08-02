"""OCRエンジンモジュール

NDLOCR-Lite を共通インターフェースで呼び出し、画像からテキストを抽出する。
本ツールは書籍・印刷物の OCR に対応する単一エンジン構成 (NDLOCR-Lite) で運用する。

OCR 結果は process_folder_collect() でリストとして取得し、
各種ビルダー (pdf_builder, markdown_writer) に渡して変換できる。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

from core import ocr_preprocess, text_replacements
from core.config import load_config

# ============================================================
# NDLOCR-Lite エンジン
# ============================================================

class NDLOCREngine:
    """NDLOCR-Lite エンジン (書籍・印刷物全般、レイアウト解析付き)。"""

    key = "ndlocr"
    description = "NDLOCR-Lite — 書籍・印刷物全般、レイアウト解析付き"

    def is_available(self):
        if shutil.which("ndlocr-lite"):
            return True, "ndlocr-lite コマンドが見つかりました"

        ndlocr_dir = self._find_dir()
        if ndlocr_dir:
            return True, f"ndlocr-lite ディレクトリが見つかりました: {ndlocr_dir}"

        return False, (
            "NDLOCR-Lite がインストールされていません。\n"
            "インストール: git clone https://github.com/ndl-lab/ndlocr-lite && "
            "cd ndlocr-lite && pip install -r requirements.txt"
        )

    def process_single(self, image_path, preprocess_opts=None):
        if not os.path.exists(image_path):
            return False, f"ファイルが見つかりません: {image_path}"

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # 前処理が有効なら、tmpdir に前処理済み画像を作って NDLOCR に渡す
                input_for_ocr = self._maybe_preprocess(image_path, tmpdir, preprocess_opts)

                use_system = bool(shutil.which("ndlocr-lite"))
                # NDLOCR の出力先は前処理画像と分けるためサブディレクトリを切る
                ocr_out = os.path.join(tmpdir, "_ocr_out")
                os.makedirs(ocr_out, exist_ok=True)
                cmd = self._build_command(input_for_ocr, ocr_out, use_system)
                result = subprocess.run(
                    cmd, capture_output=True, text=True, encoding="utf-8", timeout=120,
                )
                if result.returncode != 0:
                    return False, f"OCRエラー: {result.stderr}"
                text = self._collect_text(ocr_out)
                return True, text
            except subprocess.TimeoutExpired:
                return False, "OCR処理がタイムアウトしました（120秒）"
            except Exception as e:
                return False, f"OCR処理中にエラー: {e}"

    def _maybe_preprocess(self, image_path, tmpdir, opts):
        """前処理が有効なら tmpdir に前処理済み画像を保存し、そのパスを返す。
        無効ならオリジナルパスをそのまま返す。
        """
        if not opts or not opts.get("enabled"):
            return image_path
        ext = os.path.splitext(image_path)[1].lower() or ".png"
        # NDLOCR は .jpg / .png を受け付ける。前処理後はロスレス維持で .png にする
        if ext not in (".png", ".jpg", ".jpeg"):
            ext = ".png"
        dst = os.path.join(tmpdir, "_preprocessed" + ext)
        ocr_preprocess.preprocess_file(
            image_path, dst,
            upscale=float(opts.get("upscale", 1.5)),
            enhance_contrast=bool(opts.get("enhance_contrast", True)),
            binarize=bool(opts.get("binarize", False)),
            binarize_threshold=int(opts.get("binarize_threshold", 180)),
        )
        return dst

    def _find_dir(self):
        base = os.path.dirname(os.path.abspath(__file__))
        for rel in ("ndlocr-lite", os.path.join("..", "ndlocr-lite")):
            path = os.path.join(base, rel)
            if os.path.exists(os.path.join(path, "src", "ocr.py")):
                return os.path.abspath(path)
        return None

    def _build_command(self, input_path, output_dir, use_system):
        if use_system:
            cmd = ["ndlocr-lite"]
        else:
            ndlocr_dir = self._find_dir()
            if not ndlocr_dir:
                raise RuntimeError("ndlocr-lite が見つかりません")
            cmd = [sys.executable, os.path.join(ndlocr_dir, "src", "ocr.py")]

        if os.path.isdir(input_path):
            cmd.extend(["--sourcedir", input_path])
        else:
            cmd.extend(["--sourceimg", input_path])
        cmd.extend(["--output", output_dir])
        return cmd

    def _collect_text(self, output_dir):
        # NDLOCR-Lite は同じ内容を .txt / .json / .xml で出力するため
        # .txt 優先で読み、無い場合のみ .json から抽出する
        text_parts = []
        json_fallbacks = []
        txt_seen_stems = set()
        for root, _dirs, files in os.walk(output_dir):
            for f in sorted(files):
                filepath = os.path.join(root, f)
                stem, ext = os.path.splitext(f)
                if ext == ".txt":
                    with open(filepath, encoding="utf-8") as fh:
                        text_parts.append(fh.read())
                    txt_seen_stems.add(stem)
                elif ext == ".json":
                    json_fallbacks.append((stem, filepath))

        for stem, filepath in json_fallbacks:
            if stem in txt_seen_stems:
                continue
            try:
                with open(filepath, encoding="utf-8") as fh:
                    data = json.load(fh)
                extracted = self._extract_json_text(data)
                if extracted:
                    text_parts.append(extracted)
            except (json.JSONDecodeError, KeyError):
                pass

        return "\n".join(text_parts) if text_parts else ""

    def _extract_json_text(self, data):
        texts = []
        if isinstance(data, dict):
            if "text" in data:
                texts.append(str(data["text"]))
            for key in ("children", "blocks", "lines", "words", "results"):
                if key in data and isinstance(data[key], list):
                    for item in data[key]:
                        t = self._extract_json_text(item)
                        if t:
                            texts.append(t)
        elif isinstance(data, list):
            for item in data:
                t = self._extract_json_text(item)
                if t:
                    texts.append(t)
        return "\n".join(texts)


# ============================================================
# 公開API
# ============================================================

_ENGINE = NDLOCREngine()


def get_available_engines():
    """利用可能な OCR エンジンのリストを返す (NDLOCR-Lite のみ)。"""
    available, message = _ENGINE.is_available()
    return [{
        "key": _ENGINE.key,
        "description": _ENGINE.description,
        "available": available,
        "message": message,
    }]


def is_available():
    """OCR エンジンが利用可能かチェックする。

    Returns:
        (available, message) のタプル
    """
    return _ENGINE.is_available()


def _resolve_preprocess_opts(preprocess_opts):
    """呼び出し側が opts を渡さなかったら config から読む。"""
    if preprocess_opts is not None:
        return preprocess_opts
    cfg = load_config()
    return cfg.get("ocr", {}).get("preprocess", {})


def _resolve_replacements_opts(replacements_opts):
    """呼び出し側が opts を渡さなかったら config から読む。"""
    if replacements_opts is not None:
        return replacements_opts
    cfg = load_config()
    return cfg.get("ocr", {}).get("replacements", {})


def _apply_replacements_to_results(results, replacements_opts):
    """results に対して置換辞書を適用する。

    無効化されていればそのまま返す。エラーメッセージはサイレントに無視する
    (UI 側で別途辞書ロードのバリデーションを行う想定)。
    """
    if not replacements_opts or not replacements_opts.get("enabled", True):
        return results
    path = replacements_opts.get("path") or text_replacements.default_path()
    new_results, _err = text_replacements.apply_to_results(results, path=path)
    return new_results


def process_single(image_path, preprocess_opts=None, replacements_opts=None):
    """単一の画像に対して OCR を実行し、テキストを返す。

    Args:
        preprocess_opts: 前処理パラメータ dict。None なら config から読む。
            { "enabled": bool, "upscale": float, "enhance_contrast": bool,
              "binarize": bool, "binarize_threshold": int }
        replacements_opts: 置換辞書パラメータ dict。None なら config から読む。
            { "enabled": bool, "path": str }

    Returns:
        (success, text_or_error) のタプル
    """
    available, msg = _ENGINE.is_available()
    if not available:
        return False, msg
    opts = _resolve_preprocess_opts(preprocess_opts)
    success, text = _ENGINE.process_single(image_path, preprocess_opts=opts)
    if not success:
        return success, text
    rep_opts = _resolve_replacements_opts(replacements_opts)
    new_results = _apply_replacements_to_results([("_", text)], rep_opts)
    return True, new_results[0][1]


def process_folder_collect(
    input_folder, on_progress=None,
    preprocess_opts=None, replacements_opts=None,
):
    """フォルダ内の画像を一括 OCR 処理し、結果をリストで返す。

    Args:
        preprocess_opts: 前処理パラメータ dict。None なら config から読む。
        replacements_opts: 置換辞書パラメータ dict。None なら config から読む。

    Returns:
        (success, results_or_error) のタプル
        成功時: results は [(filename, text), ...] のリスト
    """
    available, msg = _ENGINE.is_available()
    if not available:
        return False, msg

    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')
    image_files = sorted([
        f for f in os.listdir(input_folder) if f.lower().endswith(image_extensions)
    ])
    if not image_files:
        return False, "画像ファイルが見つかりません"

    opts = _resolve_preprocess_opts(preprocess_opts)
    total = len(image_files)
    results = []

    for i, filename in enumerate(image_files, 1):
        filepath = os.path.join(input_folder, filename)
        success, text = _ENGINE.process_single(filepath, preprocess_opts=opts)
        if success:
            results.append((filename, text))
        else:
            results.append((filename, f"[OCRエラー: {text}]"))
        if on_progress:
            on_progress(i, total, filename)

    rep_opts = _resolve_replacements_opts(replacements_opts)
    results = _apply_replacements_to_results(results, rep_opts)

    return True, results
