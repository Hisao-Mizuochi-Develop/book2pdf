---
name: task-manager
description: |
  Manage tasks, work logs, and progress tracking for the book2pdf project.
  Activate when creating or updating <MODULE>-TASKS.md, <MODULE>-WORK-LOG.md, or task entries.
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
   - 識別子:
     - `SY` … System/全体設計・仕様、全体基盤、結合試験、性能試験、等
     - `FE` … frontend
     - `BE` … backend
     - `OW` … ocr-worker
     - `LA` … localapp
     - `OT` … 横断・その他（other）
   - 例: ocr-worker のユースケース003の1番目 → `OW003001`
   - 通番は各ユースケース内で 001 から連番

2. **タスク粒度**
   - 数時間〜1日以内で完了できる単位
   - 1つのタスクに複数の責務が含まれる場合は分割を検討
    - ただし、達成可能な単位を保ち、細部を無理に別タスクに分けすぎない

3. **記録場所**
   - タスク管理表 → `<module>/docs/<MODULE>-TASKS.md`
   - 作業ログ → `<module>/docs/<MODULE>-WORK-LOG.md`
   - 全体横断 → `./docs/OT-WORK-LOG.md`, `./docs/OT-TASKS.md`
    - 作業の記録はタスク詳細欄に箇条書きで記載する

4. **計画の変更**
   - 一度記載した【計画】は削除せず、追記のみ
   - 実施しない場合は、その理由を【計画】欄内に追記

5. **タスク実装方針**
    - 将来の課題も含め、原則としてすべての項目を実装する

## Common Edge Cases
- 新規ユースケースが必要な場合: まずユーザーに提案し、承認を得てから起票
