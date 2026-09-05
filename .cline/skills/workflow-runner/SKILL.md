---
name: workflow-runner
description: |
  Execute tasks in a 4-phase workflow (context analysis, planning, implementation/verification, reporting/post-work)
  with selective skill loading and user approval gates. Activate at the start of every task.
compatibility: Git + Docker + Cline
metadata:
  author: book2pdf-team
  version: "2.0"
---

# workflow-runner

## Overview
本スキルは、タスクの実行を以下の 4 フェーズで統一します。

1. **Phase 1: コンテキスト読込・タスク解析**
2. **Phase 2: スキル選択・実行計画**
3. **Phase 3: 実装・検証**
4. **Phase 4: 最終報告・後処理**

`.clinerules` で定義された **Skill Selection Matrix (3-layer)** と **承認ゲート** に従い、必要最小限のスキルを選択して読み込み、ユーザー承認を得ながら進めます。

## モジュール識別子
本スキルで参照するモジュール識別子（2文字）とその対応は `.clinerules` の **Task Identifier Rules** を正とします。
簡易対応は以下の通りです。

- `SY` … System / 全体設計・仕様・横断基盤・横断実装・結合テスト
- `BE` … backend
- `FE` … frontend
- `OW` … ocr-worker
- `LA` … localapp
- `OT` … Other / その他

詳細な定義、選択基準、具体例は `.clinerules` を参照してください。

## Step-by-step Instructions

### Phase 1: コンテキスト読込・タスク解析

1. `.clinerules` を読み込み、プロジェクトルールを確認する
2. タスクの識別子（`SY` / `BE` / `FE` / `OW` / `LA` / `OT`）を判定する
3. 該当するタスク管理ファイルを読み込む
   - `SY` → `docs/SY-TASKS.md`
   - `OT` → `docs/OT-TASKS.md`
   - 各モジュール → `<module>/docs/<識別子>-TASKS.md`
4. 関連するドキュメント・コードを読み込み、タスクの背景と要件を整理する
5. 不明点があればユーザーに確認し、必要に応じて調査スキル（`search_codebase`, `fetch_web_content`）を併用する
6. **Gate 1**: ユーザーに「タスクの理解」と「進め方の方向性」を提示し、承認を取得する

### Phase 2: スキル選択・実行計画

1. `.clinerules` の **Skill Selection Matrix (3-layer)** に従い、必要なスキルを選択する
   - Layer 1: モジュール接頭辞に応じた必須スキル
   - Layer 2: 活動タイプ（`I`=調査, `D`=設計, `C`=コーディング, `R`=レビュー, `T`=テスト）に応じた追加スキル
   - Layer 3: 承認ゲートの通過タイミングを確認
2. 選択したスキルの `SKILL.md` を読み込む
3. 実施手順・確認項目・リスクを整理し、`<識別子>-TASKS.md` の【計画】欄や `<識別子>-WORK-LOG.md` の【実施予定】に記録する
4. **Gate 2**: ユーザーに具体的な実行計画を提示し、承認を取得する

### Phase 3: 実装・検証

1. 承認された計画に沿って実装・設計・調査を実行する
2. 節目ごとにユーザーに状況を報告し、方向性のズレがないか確認する
3. **実装完了後、必ず結果の正常確認を実施する**（ビルド・テスト・検証・動作確認）
4. 問題があれば即座に修正し、再度検証する
5. ドキュメントの更新も必要に応じて実施する（ただし `docs/` 配下の変更はユーザー承認が必要）

### Phase 4: 最終報告・後処理

1. **最終報告書を作成する**:
   - 実施内容の要約
   - 変更ファイル一覧
   - 検証結果（ビルド / テスト / 動作確認）
   - 残タスクや注意事項
2. **Gate 3**: 破壊的変更を含む場合、または `docs/` 配下の変更がある場合は、ユーザーに最終結果を提示し承認を取得する
3. 承認を得たら以下の後処理を実施する:
   - `<識別子>-TASKS.md` の【実施結果】に追記
   - `<識別子>-WORK-LOG.md` に【実施実績】セクションを追記
   - `<識別子>-CAVEATS.md` に注意事項を追記（該当する場合）
   - `<識別子>-TASKS.md` にタスク完了日付を記載
4. Git 運用（プロジェクト方針に従う）:
   - `git add -A && git commit -m "<タスクNo>: <内容>"`
   - 必要に応じて main ブランチへのマージを実施
5. ユーザーにタスク完了を報告する

## 選択的スキル読込ルール

- タスク開始時は必ず `workflow-runner` スキルを最初に読み込む
- 以降、Layer 1 / Layer 2 のマトリックスに従い、必要なスキルのみを追加で読み込む
- すべてのスキルを読み込む必要はない
- タスクの性質が変わった場合（例：調査タスクから実装タスクへ）は、適宜スキルを追加読み込みする

## Common Edge Cases

- 未コミットの変更がある場合は先にコミットまたは stash する
- `docs/` 配下の変更は必ずユーザー承認を取得する
- ユーザーが計画を修正・取り消しを求めた場合は、Phase 2 に戻って再計画する
- マージ後は feature ブランチを削除してもよい（プロジェクト方針に従う）
- タスクが長時間化する場合は、中間報告を挟みつつ進める
