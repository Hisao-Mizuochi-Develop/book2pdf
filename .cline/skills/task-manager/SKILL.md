---
name: task-manager
description: |
  Manage tasks, work logs, and progress tracking for the book2pdf project.
  Activate when creating or updating <モジュール識別子>-TASKS.md, <モジュール識別子>-WORK-LOG.md, or task entries.
compatibility: VS Code + Cline
metadata:
  author: book2pdf-team
  version: "1.0"
---

# task-manager

## Overview
本スキルは、book2pdf プロジェクトのタスク管理表・作業ログの運用ルールを定めます。

## Step-by-step Instructions

1. **タスクNo体系**
   - 形式: モジュール識別子(2桁) + ユースケースNo(3桁) + 通番(3桁)（計8文字）
   - 識別子（簡易対応）:
     - `SY` … System/全体設計・仕様・横断基盤・横断実装・結合テスト
     - `FE` … frontend
     - `BE` … backend
     - `OW` … ocr-worker
     - `LA` … localapp
     - `OT` … Other / その他
   - 詳細な定義、選択基準、具体例は `.clinerules` の **Task Identifier Rules** を参照する
   - 例: ocr-worker のユースケース003の1番目 → `OW003001`
   - 通番は各ユースケース内で 001 から連番

2. **タスク粒度**
   - 数時間〜1日以内で完了できる単位
   - 1つのタスクに複数の責務が含まれる場合は分割を検討
    - ただし、達成可能な単位を保ち、細部を無理に別タスクに分けすぎない

3. **記録場所**
   - タスク管理表 → `<module>/docs/<モジュール識別子>-TASKS.md`
   - 作業ログ → `<module>/docs/<モジュール識別子>-WORK-LOG.md`
   - 全体横断 → `./docs/OT-WORK-LOG.md`, `./docs/OT-TASKS.md`
    - 作業の記録はタスク詳細欄に箇条書きで記載する

4. **計画の変更**
   - 一度記載した【計画】は削除せず、追記のみ
   - 実施しない場合は、その理由を【計画】欄内に追記

5. **タスク実装方針**
    - 将来の課題も含め、原則としてすべての項目を実装する

6. **タスクの並行実行禁止**
    - タスクは並行して進めない
    - 現在のタスクが完了（Phase 4 終了・コミット）してから、次のタスクを開始する
    - ただし、チーム開発で複数の人間開発者が別々のタスクを並行して作業する場合はこの限りではない

7. **実装後の記録更新**
   - タスク完了後、`workflow-runner` スキルに従い以下を更新する
     - `<module>/docs/<モジュール識別子>-TASKS.md` の【実施結果】
     - `<module>/docs/<モジュール識別子>-WORK-LOG.md` の【実施実績】
   - 完了日付を `<module>/docs/<モジュール識別子>-TASKS.md` に記載する

## Common Edge Cases
- 新規ユースケースが必要な場合: まずユーザーに提案し、承認を得てから起票
