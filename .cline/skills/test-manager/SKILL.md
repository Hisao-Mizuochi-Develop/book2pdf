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

## モジュール識別子
本スキルで参照するモジュール識別子（2文字）とその対応は `.clinerules` の **Task Identifier Rules** を正とします。
簡易対応は以下の通りです。

- `SY` … System/全体設計・仕様・横断基盤・横断実装・結合テスト
- `BE` … backend
- `FE` … frontend
- `OW` … ocr-worker
- `LA` … localapp
- `OT` … Other / その他

詳細な定義、選択基準、具体例は `.clinerules` を参照してください。

## Pre-work

1. **テストデータはユーザーの資産として扱う**
    - 明示的なユーザー指示がある場合を除き、勝手に変更しない
    - `git checkout --` による revert、上書き、クリーンアップを名目とした削除は禁止

2. **実施前のルール確認**
    - `.clinerules` を `read_file` で読み込み確認する
    - `<module>/docs/<モジュール識別子>-TASKS.md` でタスク種別を確認する
    - テスト・検証・調査系タスクの場合は `docs/OT-INTEGRATION-TEST-GUIDE.md` を読み込む

## Step-by-step Instructions

1. **テストデータの配置**
   - 各モジュール固有 → `test_cases/testdata/<module>/<タスクNo>-<概要>/`
   - 各モジュール固有の結果レポート → `<module>/test-results/<タスクNo>-<概要>/README.md`
   - プロジェクト全体共有 → `test_cases/`
   - `test_cases/` 内のファイルを参照する場合は、原則として `test_cases/` からの相対パスで統一する
   - `test_cases/testdata/` は Git 管理対象（.gitignore で除外しない）
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
   - `<モジュール識別子>-TASKS.md` に「単体動作確認（backend 連携なし）」と明記されている場合のみ、ocr-worker を直接実行してよい
   - それ以外の検証は必ず backend API 経由で実施する

4. **検証レポートの作成**
   - 配置: `test_cases/results/ocr-results-<タスクNo>/`
   - 命名: `<レポート名>-<タスクNo>.md`（例: `preprocess-comparison-report-OW003003.md`）
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
   - `docker compose cp backend:/data/pdfs/<job_id>.pdf ./test_cases/results/ocr-results-<タスクNo>/<パターン名>/pdfs/` で PDF を取得する
   - コピーした PDF を開いて目視で品質を確認
   - 確認結果をレポートに記載する

7. **`test_cases/README.md` へのインデックス追加**
   - 既存セクションがある場合: テーブルの `|---|---|---|` 区切り行を SEARCH に指定して追記
   - セクションがない場合: 該当するセクション見出しを新規作成し、エントリを追加
   - インデックス追加後、他のエントリが欠落していないか確認する

## Verification Report Template（検証レポートテンプレート）

本テンプレートは、`workflow-runner` Phase 4 の「最終報告書」に埋め込んで使用する標準フォーマットです。Clineは報告時、以下の表とフォーマットを必ずそのまま出力に含めること。

### テストフェーズ毎の実施済みテスト項目と合否判定結果

| テストフェーズ | 確認項目（実施内容） | 合否判定基準 | 結果 |
|---|---|---|---|
| **ビルド** | 対象モジュールのビルド/コンパイルがエラーなしで完了する | エラー 0 件、警告は許容範囲内 | □ PASS / □ FAIL / □ N/A |
| **単体テスト**<br>(CI/CD実施項目) | 既存および新規のテストスイートが全件通過する | 失敗 0 件、スキップ 0 件（意図的スキップを除く） | □ PASS / □ FAIL / □ N/A |
| **動作確認**<br>(ユーザー検証項目の自動テスト) | 主要ユースケースおよびユーザー検証項目を満たす自動テストが正常に完了する | 期待結果と実際の結果が完全に一致する | □ PASS / □ FAIL / □ N/A |

**再テスト手順**: いずれかのテストフェーズで FAIL または N/A（該当する場合）となった場合、該当する問題を修正し、該当テストフェーズを再度実施することを繰り返す。ビルド、単体テスト、動作確認のいずれも FAIL 0 件となるまで最終報告書を作成しない。

### 【ユーザー検証試験についての準備】

#### 1. テスト環境準備状況

| 項目 | 確認内容 | 状態・準備状況の詳細 |
|---|---|---|
| コンテナ起動 | `docker compose up -d` で全サービスが Healthy 状態になる | □ 完了 / □ 未完了 (詳細: ) |
| データ配置 | 検証に必要なテストデータが所定のパスに配置されている | □ 完了 / □ 未完了 (詳細: ) |
| 依存関係 | 必要なパッケージ/ライブラリが環境にインストール済み | □ 完了 / □ 未完了 (詳細: ) |

#### 2. ユーザーテスト項目と実施方法
*(ユーザーが実際に手動で検証、または結果を確認するための具体的なテストケースと手順を記述すること)*
- **テストケース1:** [画面/機能名]
  - **実施方法・手順:** 1. 〇〇にアクセスする / 2. 〇〇を入力してボタンを押す
  - **期待される結果:** 〇〇が表示され、エラーが出ないこと
  - **判定:** □ PASS / □ FAIL
- **テストケース2:** ...

### 総合判定

- 各フェーズ（ビルド、単体テスト、動作確認）がすべて PASS の場合: **PASS**
- いずれかのフェーズが FAIL または N/A（該当する場合）の場合: **FAIL**（要修正・再検証）

### ユーザー検証テストの承認

ユーザー検証テストを要するタスクでは、上記総合判定が PASS となった後も、**ユーザーが実際に検証を実施し、明示的に合格を出すまでタスクを完了としない**。ユーザー検証テストの実施手順・判定基準は本テンプレートの「ユーザーテスト項目と実施方法」に従って提示し、最終報告書にその結果を記載すること。

## Prohibited Actions

- `git checkout -- <testdata パス>` による revert
- ユーザーが更新した画像・ZIP・PDF・メタデータの上書き
- クリーンアップを名目としたテストデータの削除や整理
- 差分検出時は、まずユーザーの意図を確認
