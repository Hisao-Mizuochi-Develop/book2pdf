---
name: test-manager
description: |
  Handle test data, benchmarks, and validation reports.
  Activate when working with test_cases/, testdata/, or validation tasks.
compatibility: Docker + backend API required
metadata:
  author: book2pdf-team
  version: "1.0"
---

# test-manager

## Overview
本スキルは、テストデータの配置、backend API 経由のフルフロー実行、検証レポートの作成とインデックス追加を定めます。

## Pre-work

1. **テストデータはユーザーの資産として扱う**
    - 明示的なユーザー指示がある場合を除き、勝手に変更しない
    - `git checkout --` による revert、上書き、クリーンアップを名目とした削除は禁止

2. **実施前のルール確認**
    - `.clinerules` を `read_file` で読み込み確認する
    - `<module>/docs/tasks.md` でタスク種別を確認する
    - テスト・検証・調査系タスクの場合は `docs/integration-test-guide.md` を読み込む

## Step-by-step Instructions

1. **テストデータの配置**
   - 各モジュール固有 → `<module>/testdata/<タスクNo>-<概要>/`
   - 各モジュール固有の結果レポート → `<module>/test-results/<タスクNo>-<概要>/README.md`
   - プロジェクト全体共有 → `test_cases/`
   - `test_cases/` 内のファイルを参照する場合は、原則として `test_cases/` からの相対パスで統一する
   - `testdata/` は Git 管理対象（.gitignore で除外しない）
   - root 直下に `ocr-results-*` フォルダを作成しない

2. **backend API 経由のフルフロー実行（原則）**
   - `docker compose up -d` で backend / ocr-worker コンテナ起動を確認
   - テスト・検証タスクでコンテナを起動する場合は、必ず専用ブランチ内で実施する
   - `POST /api/jobs` でジョブ作成
   - `POST /api/jobs/{job_id}/upload` で ZIP アップロード
   - `POST /api/jobs/{job_id}/ocr` で OCR 実行
   - `GET /api/jobs/{job_id}` で completed までポーリング
   - `docker compose cp` で成果物をホスト側にコピー

3. **単体動作確認のみの例外**
   - `tasks.md` に「単体動作確認（backend 連携なし）」と明記されている場合のみ、ocr-worker を直接実行してよい
   - それ以外の検証は必ず backend API 経由で実施する

4. **検証レポートの作成**
   - 配置: `test_cases/ocr-results-<タスクNo>/`
   - 命名: `<レポート名>-<タスクNo>.md`（例: `preprocess-comparison-report-003003.md`）
   - レポートに含める内容:
     - タスク名・実施日・目的
     - 対象データ、OCR エンジン、評価指標
     - 使用データへのパス・実行手順
     - 期待結果・実際の結果
     - 判定（PASS/FAIL）
     - スクリーンショット（該当する場合）
   - レポート本文には以下を記載:
     - 概要・比較パターン
     - 定量的結果（処理時間、メモリ使用量、文字認識率など）
     - 考察・結論・今後の検討事項

5. **付属データの同梱**
   - CSV、テキスト、画像、比較用 PDF などをレポートと同じディレクトリに配置する
   - レポート本文から相対パスで参照する

6. **PDF の目視確認手順**
   - `docker compose cp backend:/data/pdfs/<job_id>.pdf ./test_cases/ocr-results-<タスクNo>/<パターン名>/pdfs/` で PDF を取得する
   - コピーした PDF を開いて目視で品質を確認
   - 確認結果をレポートに記載する

7. **`test_cases/README.md` へのインデックス追加**
   - 既存セクションがある場合: テーブルの `|---|---|---|` 区切り行を SEARCH に指定して追記
   - セクションがない場合: 該当するセクション見出しを新規作成し、エントリを追加
   - インデックス追加後、他のエントリが欠落していないか確認する

## Prohibited Actions

- `git checkout -- <testdata パス>` による revert
- ユーザーが更新した画像・ZIP・PDF・メタデータの上書き
- クリーンアップを名目としたテストデータの削除や整理
- 差分検出時は、まずユーザーの意図を確認
