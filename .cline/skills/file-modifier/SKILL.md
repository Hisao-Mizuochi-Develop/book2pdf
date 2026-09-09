---
name: file-modifier
description: |
  Update existing documents and reports using replace_in_file only.
  Activate when modifying existing markdown files in docs/, backend/docs/,
  frontend/docs/, localapp/docs/, ocr-worker/docs/, or test_cases/**.
  Strictly prohibits write_to_file for existing files.
compatibility: Designed for Cline / VS Code
metadata:
  author: book2pdf-team
  version: "1.0"
---

# file-modifier

## 概要
本スキルは、既存ドキュメント（`.clinerules` 自身も含む）の更新時に **replace_in_file のみ**を使用することを強制します。

## 手順

1. **新規 or 既存を判定する**
   - ファイルがすでに存在する → `replace_in_file` のみ使用
   - ファイルが存在しない → `write_to_file` を使用可能

2. **replace_in_file の実装**
   - SEARCH に既存テキストの末尾マーカー（区切り行、見出し、セクション終端）を含める
   - テーブルの `|---|---|---|` 区切り行を SEARCH に指定して追記する

3. **禁止事項**
   - `write_to_file` で既存ファイルを上書きしない
   - `sed -i` などの直接ファイル書き換えを使わない

4. **`.clinerules` 自身も対象**
    - `.clinerules` を更新する場合も、必ず `replace_in_file` を使用する

## 5. Markdown テーブル更新後の検証

- `*-TASKS.md` や `docs/**/*.md` のパイプテーブルを更新した場合は、必ず `markdown-table-validator` スキルを適用する
- または `python scripts/lint-task-md.py` を実行し、カラム整合性を確認する
- 同一セクション内のすべてのテーブル行が同じ数の `|` を持つことを確認する

## よくある境界ケース
- 文末に追記する場合: 既存の `---` や `##` 見出しを SEARCH に含める
- Markdown テーブル編集後は `|` の数が揃っているか必ず検証する
