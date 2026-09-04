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

## Step-by-step Instructions

1. **テストデータの配置**
   - 各モジュール固有 → `<module>/testdata/<タスクNo>-<概要>/`
   - プロジェクト全体共有 → `test_cases/`
   - `testdata/` は Git 管理対象（.gitignore で除外しない）

2. **backend API 経由のフルフロー実行**
   - `docker compose up -d` で backend / ocr-worker コンテナ起動を確認
   - `POST /api/jobs` でジョブ作成
   - `POST /api/jobs/{job_id}/upload` で ZIP アップロード
   - `POST /api/jobs/{job_id}/ocr` で OCR 実行
   - `GET /api/jobs/{job_id}` で completed までポーリング
   - `docker compose cp` で成果物をホスト側にコピー

3. **検証レポートの作成**
   - 配置: `test_cases/ocr-results-<タスクNo>/`
   - 命名: `<レポート種別>-report-<タスクNo>.md`
   - 必ず `test_cases/README.md` にインデックス追加

## Prohibited Actions

- `git checkout -- <testdata パス>` による revert
- ユーザーが更新した画像・ZIP・PDF・メタデータの上書き
- クリーンアップを名目としたテストデータの削除や整理
- 差分検出時は、まずユーザーの意図を確認
