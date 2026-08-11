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

# PDF 生成ライブラリ（PyMuPDF）です
import fitz

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

    Args:
        extract_dir: ZIP 展開先のルートディレクトリ
        image_name: 探す画像ファイル名

    Returns:
        画像ファイルのパス。見つからない場合は None
    """
    # ファイル名のみを取得します
    # 万が一パスが含まれていてもファイル名部分だけを使います
    name = Path(image_name).name

    # 展開ディレクトリ以下を再帰的に探します
    for path in extract_dir.rglob(name):
        # ファイルであればそのパスを返します
        if path.is_file():
            return path

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
        return pix.width, pix.height
    except Exception:
        # 画像の読み込みに失敗した場合は None を返します
        # 呼び出し元で XML のサイズ情報またはデフォルト値を使用します
        return None


def _insert_text_line(
    page: fitz.Page,
    line: OcrLine,
    page_height: float,
    font_path: str | None = None,
) -> None:
    """ページに 1 行分の透明テキストを挿入します。

    Args:
        page: テキストを挿入する PDF ページ
        line: OCR 行データ
        page_height: ページの高さ（座標変換用）
        font_path: 使用するフォントファイルのパス（省略可）
    """
    # 画像座標系（左上原点）から PDF 座標系（左下原点）へ変換します
    # fitz の insert_text は baseline（文字の下端）を基準に配置します
    pdf_x = float(line.x)
    pdf_y = page_height - float(line.y) - float(line.height)

    # テキスト行の幅と高さです
    line_width = float(line.width)
    line_height = float(line.height)

    # 文字列が入るようにフォントサイズを調整します
    # まずは行の高さをフォントサイズの初期値とします
    font_size = max(line_height, 1.0)

    # テキストの実際の幅を計算します
    text_width = fitz.get_text_length(line.text, fontsize=font_size)

    # テキスト幅が行幅を超える場合はフォントサイズを縮小します
    if text_width > line_width and line_width > 0:
        # 縮小率を計算します（少し余裕を持たせるため 0.95 を掛けます）
        scale = (line_width / text_width) * 0.95
        font_size = max(font_size * scale, 1.0)

    # 透明テキストを挿入する際の追加オプションです
    # 日本語フォントが見つかっている場合は fontfile を指定します
    text_options: dict = {
        "point": (pdf_x, pdf_y),
        "text": line.text,
        "fontsize": font_size,
        "color": (0, 0, 0),
        "fill_opacity": 0,
        "render_mode": 0,
    }
    if font_path is not None:
        text_options["fontfile"] = font_path
        text_options["fontname"] = "japanesefont"

    # 透明テキストを挿入します
    # color=(0, 0, 0)、opacity=0 で目に見えないが選択可能なテキストになります
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

    try:
        # 各ページについて処理します
        for page_data in pages:
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
            else:
                # 画像が見つからないか読み込めない場合は XML のサイズ情報を使用します
                img_width = page_data.width
                img_height = page_data.height

            # サイズが取得できない場合はデフォルト値を使用します
            if img_width <= 0 or img_height <= 0:
                img_width = 595
                img_height = 842

            # PDF に新しいページを追加します
            page = doc.new_page(width=img_width, height=img_height)

            # ページ画像が読み込める場合は背景に配置します
            if image_size is not None:
                # ページ全体を覆う矩形を作成します
                rect = fitz.Rect(0, 0, img_width, img_height)
                # 画像をページに配置します
                page.insert_image(rect, filename=str(image_path))

            # ページ内のテキスト行を透明テキストレイヤーとして配置します
            for line in page_data.lines:
                _insert_text_line(page, line, float(img_height), font_path)

        # PDF ファイルを保存します
        doc.save(str(pdf_path))
    finally:
        # ドキュメントをクローズします
        doc.close()

    # 生成した PDF ファイルのパスを返します
    return pdf_path
