"""PDF生成モジュール

PNG画像をファイル名順に1つのPDFファイルに結合する。
OCR結果からテキストのみのPDF、または画像+不可視テキストの検索可能PDFも生成できる。

chapters 引数 ([Chapter, ...]) を渡すと、対応するページにしおり
(PDF アウトライン) を埋め込む。chapter_detector.detect_chapters の
出力をそのまま渡せる。
"""

import os
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus import Image as RLImage


def _chapters_by_filename(chapters):
    """[Chapter, ...] を {filename: Chapter} に変換する。"""
    return {c.filename: c for c in (chapters or [])}


def _emit_bookmark(c, key, title, level):
    """canvas に bookmark + outline entry を 1 件追加する。

    title が長すぎる場合 PDF ビューアで切り詰められるので 80 文字に制限する。
    """
    safe_title = title[:80] if title else "(untitled)"
    c.bookmarkPage(key)
    c.addOutlineEntry(safe_title, key, level=max(0, level - 1), closed=False)


class _BookmarkFlowable(Flowable):
    """SimpleDocTemplate 用: 描画時に bookmark + outline を追加するゼロサイズ Flowable。"""

    def __init__(self, key, title, level=1):
        super().__init__()
        self.key = key
        self.title = title
        self.level = level

    def wrap(self, _aW, _aH):
        return (0, 0)

    def draw(self):
        _emit_bookmark(self.canv, self.key, self.title, self.level)


class _OutlineCanvas(canvas.Canvas):
    """save 時にアウトラインパネルを開く canvas。SimpleDocTemplate に渡す用。"""

    def save(self):
        self.showOutline()
        super().save()


def images_to_pdf(folder_path, output_folder, output_filename, on_progress=None, chapters=None):
    """指定フォルダ内の画像をPDFに変換する。

    Args:
        folder_path: 画像フォルダパス
        output_folder: 出力先フォルダパス
        output_filename: 出力PDFファイル名
        on_progress: 進捗コールバック (current, total, filename)
        chapters: しおり用の章リスト (chapter_detector.Chapter のリスト)

    Returns:
        (success, message) のタプル
    """
    image_extensions = ('.png', '.jpg', '.jpeg')
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(image_extensions)]
    image_files.sort()

    if not image_files:
        return False, "指定されたフォルダに画像ファイルが見つかりません。"

    if not output_filename.lower().endswith('.pdf'):
        output_filename += '.pdf'

    os.makedirs(output_folder, exist_ok=True)
    output_pdf = os.path.join(output_folder, output_filename)

    chapter_map = _chapters_by_filename(chapters)
    c = canvas.Canvas(output_pdf)
    total_files = len(image_files)

    try:
        for i, image_file in enumerate(image_files, 1):
            full_path = os.path.join(folder_path, image_file)
            with Image.open(full_path) as img:
                width, height = img.size
            c.setPageSize((width, height))
            c.drawImage(full_path, 0, 0, width, height)
            ch = chapter_map.get(image_file)
            if ch is not None:
                _emit_bookmark(c, f"page_{i}", ch.title, ch.level)
            c.showPage()

            if on_progress:
                on_progress(i, total_files, image_file)

        if chapter_map:
            c.showOutline()
        c.save()
    except Exception as e:
        return False, f"PDF作成中にエラー: {e}"

    return True, f"PDFファイルを作成しました: {output_pdf}"


def images_to_searchable_pdf(image_folder, results, output_path, on_progress=None, chapters=None):
    """画像+不可視OCRテキストの検索可能PDFを生成する。

    見た目は画像PDFと同一だが、OCRテキストが不可視レイヤーとして
    重ねられており、テキスト検索（Ctrl+F）が可能。

    Args:
        image_folder: 画像フォルダパス
        results: [(filename, text), ...] のリスト（OCR結果）
        output_path: 出力PDFファイルパス
        on_progress: 進捗コールバック (current, total, filename)
        chapters: しおり用の章リスト (chapter_detector.Chapter のリスト)

    Returns:
        (success, message) のタプル
    """
    if not results:
        return False, "変換するデータがありません。"

    if not output_path.lower().endswith('.pdf'):
        output_path += '.pdf'

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

        chapter_map = _chapters_by_filename(chapters)
        c = canvas.Canvas(output_path)
        total = len(results)

        for i, (filename, text) in enumerate(results, 1):
            image_path = os.path.join(image_folder, filename)
            if not os.path.exists(image_path):
                continue

            img = Image.open(image_path)
            width, height = img.size
            c.setPageSize((width, height))

            # 画像を描画
            c.drawImage(image_path, 0, 0, width, height)
            img.close()

            # 不可視テキストをオーバーレイ（検索用）
            if text.strip():
                font_size = 12
                leading = font_size * 1.4
                c.setFont('HeiseiMin-W3', font_size)
                text_obj = c.beginText(0, height - font_size)
                text_obj.setTextRenderMode(3)  # invisible
                for line in text.split("\n"):
                    line = line.strip()
                    if line:
                        text_obj.textLine(line)
                    else:
                        text_obj.moveCursor(0, leading)
                c.drawText(text_obj)

            ch = chapter_map.get(filename)
            if ch is not None:
                _emit_bookmark(c, f"page_{i}", ch.title, ch.level)

            c.showPage()

            if on_progress:
                on_progress(i, total, filename)

        if chapter_map:
            c.showOutline()
        c.save()
        return True, f"検索可能PDFを作成しました: {output_path}"

    except Exception as e:
        return False, f"検索可能PDF生成エラー: {e}"


def text_to_pdf(results, output_path, on_progress=None, chapters=None):
    """OCR結果からテキストのみのPDFを生成する。

    Args:
        results: [(filename, text), ...] のリスト
        output_path: 出力PDFファイルパス
        on_progress: 進捗コールバック (current, total, filename)
        chapters: しおり用の章リスト (chapter_detector.Chapter のリスト)

    Returns:
        (success, message) のタプル
    """
    if not results:
        return False, "変換するデータがありません。"

    if not output_path.lower().endswith('.pdf'):
        output_path += '.pdf'

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        # 日本語CIDフォントを登録
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

        # スタイル定義
        heading_style = ParagraphStyle(
            'JaHeading',
            fontName='HeiseiMin-W3',
            fontSize=14,
            leading=20,
            spaceAfter=10,
            spaceBefore=15,
        )
        body_style = ParagraphStyle(
            'JaBody',
            fontName='HeiseiMin-W3',
            fontSize=10,
            leading=16,
            firstLineIndent=10,
        )

        chapter_map = _chapters_by_filename(chapters)
        canvasmaker = _OutlineCanvas if chapter_map else canvas.Canvas

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        story = []
        total = len(results)

        for i, (filename, text) in enumerate(results, 1):
            if i > 1:
                story.append(PageBreak())

            ch = chapter_map.get(filename)
            if ch is not None:
                story.append(_BookmarkFlowable(f"page_{i}", ch.title, ch.level))

            # ページヘッダー（ファイル名）
            story.append(Paragraph(escape(filename), heading_style))
            story.append(Spacer(1, 5 * mm))

            # テキスト本文を段落ごとに追加
            for line in text.split("\n"):
                line = line.strip()
                if line:
                    story.append(Paragraph(escape(line), body_style))
                else:
                    story.append(Spacer(1, 3 * mm))

            if on_progress:
                on_progress(i, total, filename)

        doc.build(story, canvasmaker=canvasmaker)
        return True, f"テキストPDFを作成しました: {output_path}"

    except Exception as e:
        return False, f"テキストPDF生成エラー: {e}"


def images_with_text_pdf(
    image_folder, results, output_path, on_progress=None, chapters=None, reflow=False,
):
    """ページ画像と OCR テキストを見開き型（画像ページ→テキストページ）で交互に配置した PDF を生成する。

    Markdown 出力の「ページ画像を併記」と同様に、各ページについてまず
    ページ画像をそのまま1ページとして配置し、続けて同じページの OCR
    テキストを次のページに配置する。以降のページも同じ順で繰り返す。

    Args:
        image_folder: 画像フォルダパス
        results: [(filename, text), ...] のリスト（OCR結果）
        output_path: 出力PDFファイルパス
        on_progress: 進捗コールバック (current, total, filename)
        chapters: しおり用の章リスト (chapter_detector.Chapter のリスト)
        reflow: True なら本文を段落整形してから書き出す

    Returns:
        (success, message) のタプル
    """
    if not results:
        return False, "変換するデータがありません。"

    if not output_path.lower().endswith('.pdf'):
        output_path += '.pdf'

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if reflow:
        from .text_reflow import reflow_text

    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

        heading_style = ParagraphStyle(
            'JaHeading',
            fontName='HeiseiMin-W3',
            fontSize=14,
            leading=20,
            spaceAfter=10,
            spaceBefore=15,
        )
        body_style = ParagraphStyle(
            'JaBody',
            fontName='HeiseiMin-W3',
            fontSize=10,
            leading=16,
            firstLineIndent=10,
        )

        chapter_map = _chapters_by_filename(chapters)
        canvasmaker = _OutlineCanvas if chapter_map else canvas.Canvas

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )
        avail_w, avail_h = doc.width, doc.height

        story = []
        total = len(results)

        for i, (filename, text) in enumerate(results, 1):
            if i > 1:
                story.append(PageBreak())

            ch = chapter_map.get(filename)
            if ch is not None:
                story.append(_BookmarkFlowable(f"page_{i}_image", ch.title, ch.level))

            # 画像ページ — 用紙に収まるよう縦横比を保って縮小する
            image_path = os.path.join(image_folder, filename)
            if os.path.exists(image_path):
                with Image.open(image_path) as im:
                    iw, ih = im.size
                scale = min(avail_w / iw, avail_h / ih, 1.0)
                story.append(RLImage(image_path, width=iw * scale, height=ih * scale))
            else:
                story.append(Paragraph(escape(f"[画像が見つかりません: {filename}]"), body_style))

            # 続けてテキストページ
            story.append(PageBreak())
            story.append(Paragraph(escape(filename), heading_style))
            story.append(Spacer(1, 5 * mm))

            body_text = reflow_text(text) if reflow else text
            for line in body_text.split("\n"):
                line = line.strip()
                if line:
                    story.append(Paragraph(escape(line), body_style))
                else:
                    story.append(Spacer(1, 3 * mm))

            if on_progress:
                on_progress(i, total, filename)

        doc.build(story, canvasmaker=canvasmaker)
        return True, f"画像+テキストPDFを作成しました: {output_path}"

    except Exception as e:
        return False, f"画像+テキストPDF生成エラー: {e}"
