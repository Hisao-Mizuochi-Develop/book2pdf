"""Y 座標変換パターンを比較する実験スクリプトです。

OCR 結果 XML と元画像を使い、複数の Y 座標変換式で PDF を生成します。
生成した PDF からテキスト bbox を抽出し、XML 座標や元画像上の位置と比較します。
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


def parse_xml(xml_path: Path) -> list[dict]:
    """XML からページ情報を解析します。"""
    root = ET.parse(xml_path).getroot()
    pages = []
    for page_idx, page_elem in enumerate(root.findall("PAGE")):
        lines = []
        for line_elem in page_elem.iter("LINE"):
            lines.append(
                {
                    "x": float(line_elem.get("X", 0)),
                    "y": float(line_elem.get("Y", 0)),
                    "w": float(line_elem.get("WIDTH", 0)),
                    "h": float(line_elem.get("HEIGHT", 0)),
                    "text": line_elem.get("STRING", ""),
                }
            )
        pages.append(
            {
                "index": page_idx,
                "xml_width": float(page_elem.get("WIDTH", 0)),
                "xml_height": float(page_elem.get("HEIGHT", 0)),
                "image_name": page_elem.get("IMAGENAME", ""),
                "lines": lines,
            }
        )
    return pages


def find_image(png_dir: Path, image_name: str) -> Path | None:
    """XML の image_name から元画像パスを推定します。"""
    stem = Path(image_name).stem
    for suffix in ("_L", "_R"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    for path in png_dir.glob("*.png"):
        if path.stem == stem:
            return path
    return None


def compute_pdf_y(xml_y: float, xml_h: float, scale_y: float, pdf_h: float, font_size: float, mode: str) -> float:
    """指定されたモードで PDF の Y 座標を計算します。"""
    if mode == "bottom":
        # XML の下端を PDF の下端に合わせる（旧式）
        return pdf_h - (xml_y + xml_h) * scale_y
    if mode == "top":
        # XML の上端を PDF の上端に合わせ、baseline 分下げる
        return pdf_h - (xml_y * scale_y) - font_size
    if mode == "top_no_offset":
        # XML の上端を PDF の上端に合わえるが、baseline 補正なし
        return pdf_h - (xml_y * scale_y)
    if mode == "middle":
        # XML の中央を基準にする
        return pdf_h - (xml_y + xml_h / 2) * scale_y - font_size / 2
    raise ValueError(f"unknown mode: {mode}")


def generate_pdf(
    pages: list[dict],
    png_dir: Path,
    output_path: Path,
    mode: str,
    color: tuple[float, float, float] = (0, 0.5, 0),
    fill_opacity: float = 0.8,
) -> None:
    """指定された Y 座標変換モードで PDF を生成します。"""
    doc = fitz.open()
    for page_data in pages:
        image_path = find_image(png_dir, page_data["image_name"])
        if image_path is None or not image_path.exists():
            raise FileNotFoundError(f"image not found: {page_data['image_name']}")

        with Image.open(image_path) as img:
            img_w, img_h = img.size

        pdf_w = float(img_w)
        pdf_h = float(img_h)
        page = doc.new_page(width=pdf_w, height=pdf_h)
        page.insert_image(fitz.Rect(0, 0, pdf_w, pdf_h), filename=str(image_path))

        scale_x = pdf_w / page_data["xml_width"] if page_data["xml_width"] > 0 else 1.0
        scale_y = pdf_h / page_data["xml_height"] if page_data["xml_height"] > 0 else 1.0

        for line in page_data["lines"]:
            xml_x = line["x"]
            xml_y = line["y"]
            xml_w = line["w"]
            xml_h = line["h"]
            text = line["text"]

            pdf_x = xml_x * scale_x
            line_width = xml_w * scale_x
            line_height = xml_h * scale_y
            font_size = max(line_height, 1.0)
            text_width = fitz.get_text_length(text, fontsize=font_size)
            if text_width > line_width and line_width > 0:
                font_size = max(font_size * (line_width / text_width) * 0.95, 1.0)

            pdf_y = compute_pdf_y(xml_y, xml_h, scale_y, pdf_h, font_size, mode)

            page.insert_text(
                point=(pdf_x, pdf_y),
                text=text,
                fontsize=font_size,
                color=color,
                fill_opacity=fill_opacity,
                render_mode=0,
            )
    doc.save(str(output_path))
    doc.close()


def extract_bboxes(pdf_path: Path) -> list[list[tuple[float, float, float, float, str]]]:
    """PDF から各ページのテキスト bbox を抽出します。"""
    doc = fitz.open(str(pdf_path))
    result = []
    for page in doc:
        page_bboxes = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    bbox = span["bbox"]
                    page_bboxes.append((bbox[0], bbox[1], bbox[2], bbox[3], span["text"]))
        result.append(page_bboxes)
    doc.close()
    return result


def render_overview(
    pages: list[dict],
    png_dir: Path,
    bboxes_by_mode: dict[str, list[list[tuple[float, float, float, float, str]]]],
    output_dir: Path,
    max_lines: int = 20,
) -> None:
    """元画像に各モードの bbox を重ねた比較画像を生成します。"""
    colors = {
        "bottom": (255, 0, 0),       # 赤
        "top": (0, 255, 0),          # 緑
        "top_no_offset": (0, 0, 255), # 青
        "middle": (255, 255, 0),     # 黄
    }
    for page_data in pages:
        image_path = find_image(png_dir, page_data["image_name"])
        if image_path is None:
            continue
        with Image.open(image_path) as img:
            draw = ImageDraw.Draw(img)
            for mode, pages_bboxes in bboxes_by_mode.items():
                page_bboxes = pages_bboxes[page_data["index"]]
                for bbox in page_bboxes[:max_lines]:
                    x0, y0, x1, y1, _ = bbox
                    draw.rectangle([x0, y0, x1, y1], outline=colors.get(mode, (128, 128, 128)), width=2)
            out_path = output_dir / f"{image_path.stem}_overview.png"
            img.save(out_path)
            print(f"saved {out_path}")


def compare_numeric(
    pages: list[dict],
    bboxes_by_mode: dict[str, list[list[tuple[float, float, float, float, str]]]],
) -> None:
    """XML 座標と各モードの PDF bbox を数値的に比較します。"""
    for page_data in pages:
        print(f"=== Page {page_data['index'] + 1} ===")
        xml_h = page_data["xml_height"]
        pdf_h = 942.0  # 元画像サイズに依存するが、サンプルは 664x942
        scale_y = pdf_h / xml_h
        for line in page_data["lines"][:5]:
            text = line["text"][:20]
            xml_top = line["y"]
            xml_bottom = line["y"] + line["h"]
            expected_top = pdf_h - xml_top * scale_y
            expected_bottom = pdf_h - xml_bottom * scale_y
            print(f"  XML '{text}' y={xml_top} h={line['h']} -> expected pdf top={expected_top:.1f} bottom={expected_bottom:.1f}")
            for mode, pages_bboxes in bboxes_by_mode.items():
                for bbox in pages_bboxes[page_data["index"]]:
                    if bbox[4][:5] == text[:5]:
                        print(f"    {mode:15s} bbox top={bbox[1]:.1f} bottom={bbox[3]:.1f}")
                        break
                else:
                    print(f"    {mode:15s} no match")


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    xml_path = base_dir / "input_6971e033.sorted.xml"
    png_dir = base_dir / "sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed"
    output_dir = base_dir / "tmp_y_compare"
    output_dir.mkdir(exist_ok=True)

    pages = parse_xml(xml_path)
    print(f"parsed {len(pages)} pages from {xml_path}")

    modes = ["bottom", "top", "top_no_offset", "middle"]
    bboxes_by_mode: dict[str, list[list[tuple[float, float, float, float, str]]]] = {}
    for mode in modes:
        pdf_path = output_dir / f"compare_{mode}.pdf"
        generate_pdf(pages, png_dir, pdf_path, mode)
        print(f"generated {pdf_path}")
        bboxes_by_mode[mode] = extract_bboxes(pdf_path)

    compare_numeric(pages, bboxes_by_mode)
    render_overview(pages, png_dir, bboxes_by_mode, output_dir)


if __name__ == "__main__":
    main()
