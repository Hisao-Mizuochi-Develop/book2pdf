#!/usr/bin/env python3
"""003007: 各前処理パターンのページごと『〓』出現数を集計するスクリプト."""
import re
from pathlib import Path

RESULTS_DIR = Path("ocr-results-003007")
PATTERNS = [
    "baseline_2x",
    "4x_upscale",
    "4x_upscale_sharpen",
    "local_binarization",
    "local_binarization_sharpen",
    "contrast_strong",
    "contrast_strong_4x",
]

def main():
    rows = []
    for pattern in PATTERNS:
        pattern_dir = RESULTS_DIR / pattern
        output_dirs = sorted(pattern_dir.glob("output_*"))
        if not output_dirs:
            print(f"WARN: no output dir for {pattern}")
            continue
        output_dir = output_dirs[0]
        txt_files = sorted(output_dir.rglob("*.txt"))
        # ファイル名からページ番号を抽出 (例: 001_main.txt -> 001)
        page_counts = {}
        for txt_file in txt_files:
            m = re.match(r"(\d+)_.*\.txt", txt_file.name)
            if not m:
                continue
            page = m.group(1)
            text = txt_file.read_text(encoding="utf-8", errors="ignore")
            count = text.count("〓")
            page_counts[page] = page_counts.get(page, 0) + count
        total = sum(page_counts.values())
        rows.append((pattern, page_counts, total))

    # ページ番号の一覧
    all_pages = sorted({p for _, pages, _ in rows for p in pages.keys()})

    # ヘッダ
    header = ["pattern"] + all_pages + ["total"]
    print("| " + " | ".join(header) + " |")
    print("|" + "|".join(["---"] * len(header)) + "|")

    for pattern, pages, total in rows:
        cells = [pattern] + [str(pages.get(p, 0)) for p in all_pages] + [str(total)]
        print("| " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
