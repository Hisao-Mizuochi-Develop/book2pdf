"""検索可能 PDF を生成するサービスです。

OCR 結果（XML）と元のページ画像を組み合わせて、
元画像を背景に、認識テキストを透明テキストレイヤーとして配置した PDF を作成します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# 環境変数を読み込むための標準ライブラリです
# PDF 出力先ディレクトリをテスト時に変更するために使用します
import os

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
from pathlib import Path

# ログ出力のための標準ライブラリです
# 環境変数 LOG_LEVEL で出力レベルを切り替えます
import logging

# 処理時間を計測するための標準ライブラリです
import time

# PDF 生成ライブラリ（PyMuPDF）です
import fitz

# テキストの異体字を正規字体に統一するための標準ライブラリです
# PDF テキスト抽出時に異体字が出ないよう、埋め込み前に正規化します
import unicodedata

# OCR 結果の XML 解析サービスを読み込みます
from app.services.xml_parser import (
    OcrLine,
    OcrPage,
    find_sorted_xml,
    parse_sorted_xml,
)

# PDF ファイルの出力先ベースディレクトリです
# 本番環境では backend / ocr-worker 両コンテナで共有される /data/pdfs を使用します
# テスト環境では PDF_OUTPUT_DIR 環境変数で別のパスを指定できます
_PDF_OUTPUT_DIR = Path(os.environ.get("PDF_OUTPUT_DIR", "/data/pdfs"))

# ログレベルを環境変数 LOG_LEVEL から取得します（未設定時は INFO）
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

# logging モジュールにログレベルを設定します
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# 本モジュール用のロガーを取得します
logger = logging.getLogger(__name__)

# 日本語テキストを PDF に埋め込むためのフォント候補パスです
# 環境によって異なるため、複数の候補から先に見つかったものを使用します
_JAPANESE_FONT_CANDIDATES: list[str] = [
    # 環境変数で明示的に指定されたフォント
    os.environ.get("JAPANESE_FONT_PATH", ""),
    # macOS のヒラギノフォント
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Linux の Noto CJK フォント
    # Debian/Ubuntu の fonts-noto-cjk パッケージは opentype ディレクトリに配置されます
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    # Linux の IPA フォント
    "/usr/share/fonts/truetype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
]


def _find_japanese_font() -> str | None:
    """システムから日本語フォントファイルを検索します。

    Returns:
        見つかった日本語フォントファイルのパス。見つからない場合は None
    """
    # 候補パスを順に確認します
    for candidate in _JAPANESE_FONT_CANDIDATES:
        # 空文字列や None の候補は無視します
        if not candidate:
            continue

        # ファイルが存在する場合はそのパスを返します
        font_path = Path(candidate)
        if font_path.exists():
            return str(font_path)

    # 見つからない場合は None を返します
    return None


def _find_image_path(extract_dir: Path, image_name: str) -> Path | None:
    """展開ディレクトリ内から指定された画像ファイルを探します。

    ndlocr_cli は入力画像を前処理し、XML 内の image_name が
    「元ファイル名 + _L.jpg」などに変更される場合があるため、
    元の画像ファイル名でもマッチングを試みます。

    Args:
        extract_dir: ZIP 展開先のルートディレクトリ
        image_name: 探す画像ファイル名（XML 内の image_name）

    Returns:
        画像ファイルのパス。見つからない場合は None
    """
    # ファイル名のみを取得します
    # 万が一パスが含まれていてもファイル名部分だけを使います
    name = Path(image_name).name

    logger.debug(
        "画像ファイルを検索します: extract_dir=%s, image_name=%s",
        extract_dir,
        image_name,
    )

    # ndlocr_cli による前処理でファイル名に _L / _R などのサフィックスが
    # 付与されたり、拡張子が .jpg に変更されたりする場合があるため、
    # 元の画像ファイル名を推定します
    stem = Path(name).stem
    # _L や _R で終わる場合はそのサフィックスを除去します
    for suffix in ("_L", "_R"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break

    # 展開ディレクトリ以下を再帰的に探します
    fallback_path: Path | None = None
    for path in extract_dir.rglob("*"):
        # ディレクトリは無視します
        if not path.is_file():
            continue

        # 完全一致するファイルがあれば最優先で返します
        if path.name == name:
            logger.debug("画像ファイルを発見しました（完全一致）: %s", path)
            return path

        # ファイル名の stem が一致すれば元画像とみなします
        # 複数候補がある場合は最初に見つかったものを採用します
        if fallback_path is None and path.stem == stem:
            fallback_path = path

    if fallback_path is not None:
        logger.debug("画像ファイルを発見しました（stem 一致）: %s", fallback_path)
        return fallback_path

    logger.debug(
        "画像ファイルが見つかりませんでした: extract_dir=%s, name=%s",
        extract_dir,
        name,
    )
    # 見つからない場合は None を返します
    return None


def _image_size(path: Path) -> tuple[int, int] | None:
    """画像ファイルの幅と高さを取得します。

    画像ファイルが破損しているか読み込めない場合は None を返します。

    Args:
        path: 画像ファイルパス

    Returns:
        幅と高さのタプル。読み込めない場合は None
    """
    try:
        # fitz で画像ファイルを開きます
        pix = fitz.Pixmap(str(path))

        # 幅と高さを返します
        logger.debug(
            "画像サイズを取得しました: path=%s, width=%d, height=%d",
            path,
            pix.width,
            pix.height,
        )
        return pix.width, pix.height
    except Exception as exc:
        # 画像の読み込みに失敗した場合は None を返します
        # 呼び出し元で XML のサイズ情報またはデフォルト値を使用します
        logger.debug(
            "画像サイズの取得に失敗しました: path=%s, error=%s",
            path,
            exc,
        )
        return None


def _xml_to_pdf_y(
    xml_y: float,
    xml_height: float,
    pdf_height: float,
    font_size: float,
) -> float:
    """XML 座標系の Y 座標を PDF 座標系の Y 座標に変換します。

    座標系の違い:
      - XML（ndlocr_cli 出力）: 原点 (0, 0) はページ左下。
        Y 座標は「ページ下端からの距離」を表す。
      - PDF（PyMuPDF / fitz）: 原点 (0, 0) はページ左下。
        Y 座標は「ページ下端からの距離」を表す。

    両座標系とも Y 座標は「ページ下端からの距離」として解釈できるため、
    スケーリングのみを行い、上下方向の反転は不要です。

    PyMuPDF の `insert_text(point=(x, y))` は、
    指定した y をテキストの baseline（文字の下端）の位置として配置します。
    XML の Y は行の上端を表しているため、PDF の baseline 位置に合わせるために
    フォントサイズ分だけ下にずらします。

    変換式:
      pdf_y = (xml_y * scale_y) + font_size

    Args:
        xml_y: XML 座標系での Y 座標（ページ下端からの距離）
        xml_height: XML 内のページ高さ
        pdf_height: PDF ページの高さ（元画像サイズ）
        font_size: 挿入するテキストのフォントサイズ

    Returns:
        PDF 座標系での Y 座標（baseline 位置）
    """
    # XML 座標系から PDF 座標系への Y 方向スケールを計算します
    # XML ページ高さと PDF ページ高さが異なる場合に対応します
    scale_y = pdf_height / xml_height if xml_height > 0 else 1.0

    # XML の Y 座標はページ下端からの距離として解釈し、
    # PDF 座標系でも同じ向き（下端からの距離）にスケーリングします
    pdf_y = (xml_y * scale_y) + font_size

    # baseline がページ下端より下にならないよう 0 でクリップします
    return max(pdf_y, 0.0)


def _insert_text_line(
    page: fitz.Page,
    line: OcrLine,
    xml_width: float,
    xml_height: float,
    pdf_width: float,
    pdf_height: float,
    font_path: str | None = None,
) -> None:
    """ページに 1 行分の透明テキストを挿入します。

    XML 座標系（左上原点）から PDF 座標系（左下原点）へ変換する際、
    XML ページサイズと PDF ページサイズの差異をスケーリングで吸収します。

    Args:
        page: テキストを挿入する PDF ページ
        line: OCR 行データ
        xml_width: XML 内のページ幅
        xml_height: XML 内のページ高さ
        pdf_width: PDF ページの幅（元画像サイズ）
        pdf_height: PDF ページの高さ（元画像サイズ）
        font_path: 使用するフォントファイルのパス（省略可）
    """
    # XML 座標系から PDF 座標系へのスケールを計算します
    # XML ページサイズと PDF ページサイズが異なる場合に対応します
    scale_x = pdf_width / xml_width if xml_width > 0 else 1.0
    scale_y = pdf_height / xml_height if xml_height > 0 else 1.0

    # OCR 行データを数値に変換します
    xml_x = float(line.x)
    xml_y = float(line.y)
    xml_line_width = float(line.width)
    xml_line_height = float(line.height)

    # XML 座標を PDF 座標にスケーリングします
    pdf_x = xml_x * scale_x

    # テキスト行の幅と高さも PDF 座標系にスケーリングします
    line_width = xml_line_width * scale_x
    line_height = xml_line_height * scale_y

    # 異体字（例：「索」→「索」）を正規字体に統一します
    # PDF テキスト抽出時に異体字が出ないよう、埋め込み前に NFKC 正規化を適用します
    normalized_text = unicodedata.normalize("NFKC", line.text)

    # 文字列が入るようにフォントサイズを調整します
    # まずは行の高さをフォントサイズの初期値とします
    font_size = max(line_height, 1.0)

    # テキストの実際の幅を計算します（正規化後の文字列を使用）
    text_width = fitz.get_text_length(normalized_text, fontsize=font_size)

    # テキスト幅が行幅を超える場合はフォントサイズを縮小します
    if text_width > line_width and line_width > 0:
        # 縮小率を計算します（少し余裕を持たせるため 0.95 を掛けます）
        scale = (line_width / text_width) * 0.95
        font_size = max(font_size * scale, 1.0)

    # XML 座標系（左上原点）から PDF 座標系（左下原点）へ Y 座標を変換します
    pdf_y = _xml_to_pdf_y(
        xml_y=xml_y,
        xml_height=xml_height,
        pdf_height=pdf_height,
        font_size=font_size,
    )

    # 透明テキストを挿入する際の追加オプションです
    # 日本語フォントが見つかっている場合は fontfile を指定します
    # 目視確認しやすいように濃い緑色・不透明度 0.8 でテキストを描画します
    text_options: dict = {
        "point": (pdf_x, pdf_y),
        "text": normalized_text,
        "fontsize": font_size,
        "color": (0, 0.5, 0),
        "fill_opacity": 0.8,
        "render_mode": 0,
    }
    if font_path is not None:
        text_options["fontfile"] = font_path
        text_options["fontname"] = "japanesefont"

    # 濃い緑色の半透明テキストを挿入します
    # OCR テキストレイヤーが元画像上で目視確認しやすい設定です
    page.insert_text(**text_options)


def generate_searchable_pdf(
    job_id: str,
    output_dir: Path,
    extract_dir: Path,
) -> Path:
    """OCR 結果から検索可能 PDF を生成します。

    Args:
        job_id: ジョブ ID（PDF ファイル名に使用）
        output_dir: OCR 結果が格納されたディレクトリ
        extract_dir: ZIP 展開先ディレクトリ（元画像を探すため）

    Returns:
        生成された PDF ファイルのパス

    Raises:
        FileNotFoundError: OCR 結果の XML が見つからない場合
        RuntimeError: PDF 生成中にエラーが発生した場合
    """
    # OCR 出力ディレクトリから .sorted.xml ファイルを探します
    xml_path = find_sorted_xml(output_dir)
    if xml_path is None:
        raise FileNotFoundError(
            f"OCR 結果の XML が見つかりません: {output_dir}"
        )

    # XML ファイルを解析してページ情報を取得します
    pages = parse_sorted_xml(xml_path)

    # ページ情報が空の場合はエラーとします
    if not pages:
        raise RuntimeError(
            f"XML からページ情報を取得できませんでした: {xml_path}"
        )

    # PDF 出力ディレクトリが存在しない場合は作成します
    _PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 出力 PDF ファイルのパスを作成します
    pdf_path = _PDF_OUTPUT_DIR / f"{job_id}.pdf"

    # 日本語フォントを検索します
    font_path = _find_japanese_font()

    # 新しい PDF ドキュメントを作成します
    doc = fitz.open()

    # PDF 生成時間を計測します
    logger.debug("PDF 生成を開始します: job_id=%s, pages=%d", job_id, len(pages))
    pdf_start_time = time.time()

    try:
        # 各ページについて処理します
        for page_idx, page_data in enumerate(pages):
            # ページ画像ファイルを探します
            image_path = _find_image_path(extract_dir, page_data.image_name)

            # ページ画像が存在し、読み込めるかを判定します
            image_size: tuple[int, int] | None = None
            if image_path is not None and image_path.exists():
                image_size = _image_size(image_path)

            # ページサイズを決定します
            if image_size is not None:
                # 画像ファイルから実際のサイズを取得します
                img_width, img_height = image_size
                logger.debug(
                    "PDF ページサイズ（画像から取得）: page_idx=%d, width=%d, height=%d",
                    page_idx,
                    img_width,
                    img_height,
                )
            else:
                # 画像が見つからないか読み込めない場合は XML のサイズ情報を使用します
                img_width = page_data.width
                img_height = page_data.height
                logger.debug(
                    "PDF ページサイズ（XML から取得）: page_idx=%d, width=%d, height=%d",
                    page_idx,
                    img_width,
                    img_height,
                )

            # サイズが取得できない場合はデフォルト値を使用します
            if img_width <= 0 or img_height <= 0:
                img_width = 595
                img_height = 842
                logger.debug(
                    "PDF ページサイズ（デフォルト値を使用）: page_idx=%d, width=%d, height=%d",
                    page_idx,
                    img_width,
                    img_height,
                )

            # PDF に新しいページを追加します
            page = doc.new_page(width=img_width, height=img_height)

            # ページ画像が読み込める場合は背景に配置します
            if image_size is not None:
                # ページ全体を覆う矩形を作成します
                rect = fitz.Rect(0, 0, img_width, img_height)
                # 画像をページに配置します
                page.insert_image(rect, filename=str(image_path))
                logger.debug(
                    "PDF ページに画像を配置しました: page_idx=%d, image_path=%s",
                    page_idx,
                    image_path,
                )
            else:
                logger.debug(
                    "PDF ページに画像を配置しませんでした: page_idx=%d, image_name=%s",
                    page_idx,
                    page_data.image_name,
                )

            # ページ内のテキスト行を透明テキストレイヤーとして配置します
            text_count = 0
            for line in page_data.lines:
                _insert_text_line(
                    page,
                    line,
                    xml_width=float(page_data.xml_width),
                    xml_height=float(page_data.xml_height),
                    pdf_width=float(img_width),
                    pdf_height=float(img_height),
                    font_path=font_path,
                )
                text_count += 1
            logger.debug(
                "PDF ページに透明テキストを配置しました: page_idx=%d, text_count=%d",
                page_idx,
                text_count,
            )

        # PDF ファイルを保存します
        doc.save(str(pdf_path))
    finally:
        # ドキュメントをクローズします
        doc.close()

    # PDF 生成時間を計算します
    pdf_elapsed = time.time() - pdf_start_time
    pdf_file_size = pdf_path.stat().st_size if pdf_path.exists() else 0
    logger.debug(
        "PDF 生成が完了しました: job_id=%s, elapsed=%.3fs, pages=%d, path=%s, size=%d bytes",
        job_id,
        pdf_elapsed,
        len(pages),
        pdf_path,
        pdf_file_size,
    )

    # 生成した PDF ファイルのパスを返します
    return pdf_path
