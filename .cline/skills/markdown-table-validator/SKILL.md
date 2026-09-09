---
name: markdown-table-validator
description: |
  Validate Markdown pipe-table column alignment in any *.md file.
  Activate when creating or editing Markdown tables, especially in
  *-TASKS.md, *.md documentation, or any file containing pipe-delimited tables.
  Can be invoked explicitly or automatically by file-modifier / task-manager.
compatibility: VS Code + Cline
metadata:
  author: book2pdf-team
  version: "1.0"
---

# markdown-table-validator

## 概要
本スキルは、Markdown パイプテーブルのカラム整合性を検証し、ずれがあれば具体的な修正指針を提示します。

## 検証対象
- `docs/**/*.md`
- `*/docs/**/*.md`
- その他、プロジェクト内のすべての `*.md` ファイル

## 手順

### 1. カラム整合性の検証

対象ファイルを読み込み、以下を検証する。

#### 判定ルール

- `|` で始まる各行（テーブル行）について、セクション内で `|` の数（NF）が統一されているかチェックする
- テーブルヘッダー区切り行（例: `|---|---|---|---|---|`）は区切りとして扱うが、`| の数` も検証対象とする
- `## ` 見出し行または `---`（水平線、テーブル区切りを除く）でセクションを区切り、各セクション内で `|` の数が揃っているか検証する

#### 具体的な検証コマンド

```bash
# テーブル行の | の数を確認（行番号付き）
awk -F'|' '/^\|/ {if (prev_nf != "" && prev_nf != NF) print "MISMATCH at line " NR ": | count=" NF ", prev=" prev_nf; prev_nf=NF}' <file>
```

または Python スクリプト: `scripts/lint-task-md.py`

### 2. 発見された不整合の修正指針

| 不整合パターン | 修正方法 |
|---|---|
| 末尾の `|  |  |  |` が欠落している | 行末に欠落した `|` と空セルを追加する |
| テキスト内に `|` が含まれている | 意味を損なわない範囲で表現を変更する（例: `a\|b` → `a or b`） |
| ヘッダー行とデータ行の列数が異なる | ヘッダー行を基準に、データ行の列数を揃える |

### 3. 修復後の再検証

修正後、必ず再度検証を実行し、すべてのテーブル行の `|` の数が揃っていることを確認する。

## 自動化連携

### CI / GitHub Actions
`.github/workflows/lint-task-md.yml` により、PR 作成時・`main` ブランチ push 時に自動検証が実行される。

### pre-commit
`.pre-commit-config.yaml` により、ローカルのコミット前にも自動検証が実行される。

### 手動実行
```bash
python scripts/lint-task-md.py
```

## よくある境界ケース

- 意図的な空行: テーブル内の空行は通常存在しないが、セクション区切りの空行は検証対象外
- テーブル区切り行 `|---|---|`: `|` の数としてカウントされるため、データ行と一致させる
- コードブロック内の `|`: Markdown のコードブロック（ ``` で囲まれた部分）はパイプテーブルとして扱わない