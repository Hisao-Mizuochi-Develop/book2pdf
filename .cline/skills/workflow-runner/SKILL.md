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

## Step-by-step Instructions

### Phase 1: Pre-work

1. `git status` で working tree clean を確認
2. `git checkout main && git pull` で main ブランチを最新化
3. `git checkout -b feature/<タスクNo>-<短縮名>` でブランチ作成
4. `<module>/docs/tasks.md` の【計画】に実施手順を記載
5. `<module>/docs/work_log.md` に【実施予定】エントリを作成
6. **ユーザーに計画を提示し、承認を取得**

### Phase 2: Execution

1. 実装を順次実行
2. 節目のフェーズごとにユーザーに状況報告と承認依頼
3. 承認を得てから次のフェーズへ進む

### Phase 3: Post-work

1. **ドキュメント更新**（実装完了後）:
   - `tasks.md` の【実施結果】に追記
   - `work_log.md` に【実施実績】セクションを追記
   - `caveats.md` に注意事項を追記
2. `git add -A && git commit -m "<タスクNo>: <内容>"`
3. `git checkout main && git merge feature/<タスクNo>-<xxx>`
4. `tasks.md` に完了日付を記載
5. ユーザーにタスク完了を報告

## Common Edge Cases
- 未コミットの変更がある場合は先にコミットまたは stash する
- マージ後は feature ブランチを削除してもよい（プロジェクト方針に従う）
