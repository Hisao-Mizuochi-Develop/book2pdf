---
name: workflow-runner
description: |
  Execute tasks in 3-phase workflow (pre-work, execution, post-work) with Git operations.
  Activate when starting, executing, or completing any task.
compatibility: Git + Docker + Cline
metadata:
  author: book2pdf-team
  version: "1.0"
---

# workflow-runner

## Overview
本スキルは、タスクの実行を「前処理・処理・後処理」の3フェーズで統一し、Git 運用と合わせて定めます。

## モジュール識別子
本スキルで参照するモジュール識別子（2文字）とその対応は以下の通りです。

- `SY` … System/全体設計・仕様、全体基盤、結合試験、性能試験、等
- `BE` … backend
- `FE` … frontend
- `OW` … ocr-worker
- `LA` … localapp
- `OT` … 横断・その他（other）

## Step-by-step Instructions

### Phase 1: Pre-work

1. `.clinerules` を `read_file` で読み込み、プロジェクトルールを確認する
2. `git status` で working tree clean を確認
3. `git checkout main && git pull` で main ブランチを最新化
4. `git checkout -b feature/<タスクNo>-<短縮名>` でブランチ作成
5. `<module>/docs/<モジュール識別子>-TASKS.md` の【計画】に実施手順を記載
6. `<module>/docs/<モジュール識別子>-WORK-LOG.md` に【実施予定】エントリを作成
   - 日時・目的・前提条件
   - 実施予定コマンド
   - 想定される結果や注意点
7. **ユーザーに計画を提示し、承認を取得**

### Phase 2: Execution

1. 実装を順次実行
2. 節目のフェーズごとにユーザーに状況報告と承認依頼
3. 承認を得てから次のフェーズへ進む

### Phase 3: Post-work

1. **コミット前の必須チェック**
   - ユーザー動作テストの実施結果を確認
   - 「合格」の明示的な判定を記録
   - `docs/` 配下の変更がある場合はユーザー承認を取得
2. **ドキュメント更新**（実装完了後）:
   - `<モジュール識別子>-TASKS.md` の【実施結果】に追記
   - `<モジュール識別子>-WORK-LOG.md` に【実施実績】セクションを追記
   - `<モジュール識別子>-CAVEATS.md` に注意事項を追記
   - 評価・テストを含むタスクはレポートを作成し、`<モジュール識別子>-TASKS.md` にリンクを追加
   - 仕様書ドキュメントの「フォルダ・ファイル構成」セクションを更新した場合は反映を確認
3. `git add -A && git commit -m "<タスクNo>: <内容>"`
4. `git checkout main && git merge feature/<タスクNo>-<xxx>`
5. `<モジュール識別子>-TASKS.md` に完了日付を記載
6. ユーザーにタスク完了を報告

## Common Edge Cases
- 未コミットの変更がある場合は先にコミットまたは stash する
- マージ後は feature ブランチを削除してもよい（プロジェクト方針に従う）
