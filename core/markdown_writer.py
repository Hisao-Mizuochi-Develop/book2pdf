"""Markdown出力モジュール

OCR結果を .md ファイルとして出力する。
ページ区切り（---）で区分し、フロントマター付き。

reflow=True を渡すと、各ページ本文に対して text_reflow.reflow_text() を適用し、
OCR で混入した改行を結合して読みやすい段落に整形する。

chapters を渡すと、対応するページに ``## 章タイトル`` 見出しを挿入する。
embed_images=True にすると、image_folder の各ページ画像を出力 .md と同階層の
``<basename>_pages/`` にコピーし、``![p.NNN](path)`` 形式で本文先頭に併記する。
RAG / LLM に渡したときに「該当ページの図を見せて」と言われたら画像を返せる。
"""

import os
import shutil
from datetime import datetime


def _copy_images(results, image_folder, output_path):
    """image_folder の各ページ画像を出力先サブフォルダにコピーし、
    {filename: relative_path} の dict を返す。
    """
    out_dir = os.path.dirname(output_path) or "."
    base = os.path.splitext(os.path.basename(output_path))[0]
    pages_dir_name = f"{base}_pages"
    pages_dir_abs = os.path.join(out_dir, pages_dir_name)
    os.makedirs(pages_dir_abs, exist_ok=True)

    rel_map = {}
    for filename, _text in results:
        src = os.path.join(image_folder, filename)
        if not os.path.exists(src):
            continue
        dst = os.path.join(pages_dir_abs, filename)
        # 既存と同一なら上書きを避ける (mtime 比較は省略、shutil.copy2 で十分)
        try:
            shutil.copy2(src, dst)
        except OSError:
            continue
        rel_map[filename] = f"{pages_dir_name}/{filename}".replace(os.sep, "/")
    return rel_map


def write_markdown(
    results, output_path, title=None, source=None, reflow=False,
    chapters=None, embed_images=False, image_folder=None,
):
    """OCR結果をMarkdownファイルとして出力する。

    Args:
        results: [(filename, text), ...] のリスト（OCR結果）
        output_path: 出力ファイルパス
        title: ドキュメントタイトル（省略時はファイル名から生成）
        source: ソース情報（省略時は空）
        reflow: True なら本文を段落整形して書き出す
        chapters: chapter_detector.Chapter のリスト。該当ページに見出しを挿入
        embed_images: True なら各ページ画像へのリンクを併記
        image_folder: 画像フォルダパス (embed_images=True のとき必須)

    Returns:
        (success, message) のタプル
    """
    if not results:
        return False, "変換するデータがありません。"

    if not output_path.lower().endswith(".md"):
        output_path += ".md"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if not title:
        title = os.path.splitext(os.path.basename(output_path))[0]

    if reflow:
        from .text_reflow import reflow_text

    chapter_map = {c.filename: c for c in (chapters or [])}
    image_rel = {}
    if embed_images and image_folder:
        image_rel = _copy_images(results, image_folder, output_path)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            # フロントマター
            f.write("---\n")
            f.write(f"title: \"{title}\"\n")
            f.write(f"date: {datetime.now().strftime('%Y-%m-%d')}\n")
            if source:
                f.write(f"source: \"{source}\"\n")
            f.write(f"pages: {len(results)}\n")
            f.write("---\n\n")

            # 各ページの内容
            for i, (filename, text) in enumerate(results):
                if i > 0:
                    f.write("\n---\n\n")

                f.write(f"<!-- page: {filename} -->\n\n")

                # 章見出し (該当ページのみ)
                ch = chapter_map.get(filename)
                if ch is not None:
                    hashes = "#" * max(1, min(6, ch.level))
                    f.write(f"{hashes} {ch.title}\n\n")

                # 画像リンク併記
                rel = image_rel.get(filename)
                if rel:
                    page_label = os.path.splitext(filename)[0]
                    f.write(f"![p.{page_label}]({rel})\n\n")

                body = reflow_text(text) if reflow else text
                # 本文書き出し: 整形済みでも生でも、行末空白だけは落とす
                for line in body.split("\n"):
                    line = line.rstrip()
                    f.write(f"{line}\n" if line else "\n")

        return True, f"Markdownファイルを作成しました: {output_path}"

    except Exception as e:
        return False, f"Markdown生成エラー: {e}"
