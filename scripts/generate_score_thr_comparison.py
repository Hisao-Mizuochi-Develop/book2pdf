#!/usr/bin/env python3
"""003005 score_thr 5パターンの PDF からページ画像を生成し、比較 HTML を作成します。"""

from pathlib import Path
import pymupdf

BASE_DIR = Path("/Users/hisao/Documents/work4/sakura/book2pdf/ocr-results-003005")
PATTERNS = [
    ("score-thr-0.1-preprocess-on", "0.1"),
    ("score-thr-0.2-preprocess-on", "0.2"),
    ("score-thr-0.3-preprocess-on", "0.3"),
    ("score-thr-0.4-preprocess-on", "0.4"),
    ("score-thr-0.5-preprocess-on", "0.5"),
]
PAGE_TITLES = [
    "Page 1: 表紙 (002.png)",
    "Page 2: 注意書き (003.png)",
    "Page 3: はじめに (004.png)",
]
DPI = 150


def pdf_to_images(pdf_path: Path, output_dir: Path, prefix: str) -> list[Path]:
    """PDF の各ページを PNG 画像に変換します。"""
    doc = pymupdf.open(str(pdf_path))
    images: list[Path] = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # DPI を設定してレンダリング
        mat = pymupdf.Matrix(DPI / 72, DPI / 72)
        pix = page.get_pixmap(matrix=mat)
        out_path = output_dir / f"{prefix}-page{page_num + 1}.png"
        pix.save(str(out_path))
        images.append(out_path)
    doc.close()
    return images


def main() -> None:
    img_dir = BASE_DIR / "pdf_page_images_5patterns"
    img_dir.mkdir(parents=True, exist_ok=True)

    html_path = BASE_DIR / "visual-compare-5patterns.html"

    # 各パターンの PDF を画像に変換
    for pattern_dir, score_thr in PATTERNS:
        pdf_dir = BASE_DIR / pattern_dir / "pdfs"
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(f"PDF not found in {pdf_dir}")
        pdf_to_images(pdf_files[0], img_dir, f"score-thr-{score_thr}")

    # HTML 生成
    html_lines = [
        "<!DOCTYPE html>",
        '<html lang="ja">',
        "<head>",
        '  <meta charset="UTF-8">',
        "  <title>003005 score_thr 5パターン PDF ページ画像目視比較</title>",
        "  <style>",
        "    body { font-family: sans-serif; margin: 1rem; }",
        "    h1 { font-size: 1.2rem; }",
        "    h2 { font-size: 1rem; margin-top: 1.5rem; border-bottom: 1px solid #999; padding-bottom: 0.3rem; }",
        "    .row { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }",
        "    .col { flex: 1; min-width: 180px; max-width: 220px; text-align: center; }",
        "    .col img { width: 100%; border: 1px solid #ccc; }",
        "    .label { font-size: 0.85rem; color: #333; margin: 0.3rem 0; }",
        "    .meta { font-size: 0.85rem; color: #555; margin-bottom: 0.5rem; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <h1>003005 score_thr 比較: 5パターン（前処理 ON）</h1>",
        "  <div class=\"meta\">",
        "    score_thr: 0.1 / 0.2 / 0.3 / 0.4 / 0.5<br>",
        "    テストデータ: benchmark-ocr-003002.zip (002.png, 003.png, 004.png)",
        "  </div>",
    ]

    for page_idx, title in enumerate(PAGE_TITLES):
        html_lines.append(f"  <h2>{title}</h2>")
        html_lines.append('  <div class="row">')
        for pattern_dir, score_thr in PATTERNS:
            img_name = f"score-thr-{score_thr}-page{page_idx + 1}.png"
            html_lines.append('    <div class="col">')
            html_lines.append(f'      <div class="label">score_thr={score_thr}</div>')
            html_lines.append(f'      <img src="pdf_page_images_5patterns/{img_name}">')
            html_lines.append("    </div>")
        html_lines.append("  </div>")

    html_lines.extend([
        "</body>",
        "</html>",
    ])

    html_path.write_text("\n".join(html_lines), encoding="utf-8")
    print(f"Generated images in {img_dir}")
    print(f"Generated HTML: {html_path}")


if __name__ == "__main__":
    main()
