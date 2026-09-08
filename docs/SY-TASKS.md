# タスク管理（System / 全体設計・仕様・横断基盤）

本ファイルは、`backend` / `frontend` / `ocr-worker` / `localapp` を横断するプロジェクト全体の「設計・仕様・横断基盤」に関するタスクを追記型で管理するものです。

- 個別モジュールの実装タスクは各 `<module>/docs/<識別子>-TASKS.md` に記載してください。
- 複数モジュールにまたがる実装作業は `docs/OT-TASKS.md` に記載してください。
- 本来 `SY` であるタスクが `OT` や他の識別子で起票されていた場合、履歴を本ファイルに移行記録し、元タスクからは設計・仕様部分を除きます。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する
- タスク No は「モジュール識別子（2文字）＋ ユースケースNo（3桁）＋ 通番（3桁）」とする
  - 識別子: `SY`=System/全体設計・仕様・横断基盤, `BE`=backend, `FE`=frontend, `OW`=ocr-worker, `LA`=localapp, `OT`=横断・その他
  - 例：ユースケース001の1番目のタスク → `SY001001`
  - 例：ユースケース002の1番目のタスク → `SY002001`
- 通番は各ユースケース内で 001 から連番で振る

## 識別子運用ルール

| 識別子 | 対象 | 成果物の例 |
|---|---|---|
| `SY` | システム全体の設計、仕様策定、横断基盤、コーディング規約、運用ルール | `docs/SY-*.md`, `.clinerules` の全体ルール |
| `OT` | 複数モジュールにまたがる実装、結合テスト、横断作業記録の整理 | `docs/OT-*.md`, 複数モジュールのコード変更 |
| `BE` / `FE` / `LA` / `OW` | 各モジュール固有の実装・テスト | `<module>/docs/<識別子>-TASKS.md` |

---

## ユースケースNo | 001

ユースケース
プロジェクト全体のドキュメント整備と横断基盤の確立

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| SY001001 | 全体計画書・設計決定事項・コーディング規約の整備 | 2026-08-11 | 2026-08-11 | 設計 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | プロジェクト全体の構成を `docs/SY-WEB-OCR-SYSTEM-PLAN.md` にまとめる |  |  |  |
|  | 技術選定の理由を `docs/SY-DESIGN-DECISIONS.md` にまとめる |  |  |  |
|  | Python / TypeScript / Rust のコーディング規約を `docs/OT-CODING-CONVENTIONS.md` にまとめる |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: `docs/SY-WEB-OCR-SYSTEM-PLAN.md` を新規作成し、システム全体構成・アーキテクチャ・処理フローを記載した |  |  |  |
|  | 2026-08-11: `docs/SY-DESIGN-DECISIONS.md` を新規作成し、技術選定と将来の課題を記載した |  |  |  |
|  | 2026-08-11: `docs/OT-CODING-CONVENTIONS.md` を新規作成し、各言語のコーディング規約を定めた |  |  |  |
|  | 【移行履歴】 |  |  |  |
|  | 元 `OT001001` として起票・完了したが、内容が System / 全体設計に該当するため、本ファイルに分離記録した（実施結果は変更なし） |  |  |  |

---

## ユースケースNo | 002

ユースケース
進捗通知方式の全体仕様策定

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| SY002001 | 進捗通知のポーリング方式全体仕様策定 | 2026-09-03 | 2026-09-03 | 仕様 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `docs/progress-notification-polling-design.md` と `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` を統合し、SSE / HTTP ポーリングの全体仕様を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に整理する |  |  |  |
|  | 進捗ペイロード `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止する |  |  |  |
|  | ポーリングプロトコルを文書化する（1 リクエストあたり 10 秒タイムアウト、1 秒 / 2 秒 / 4 秒の指数関数的バックオフ、最大 3 回リトライ） |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-03: `docs/progress-notification-polling-design.md` を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に統合し、前者を削除した |  |  |  |
|  | 2026-09-03: `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止した |  |  |  |
|  | 2026-09-03: ポーリングプロトコル（10 秒タイムアウト、1/2/4 秒バックオフ、最大 3 回リトライ）を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に文書化した |  |  |  |
|  | 2026-09-03: `docs/README.md` / `docs/SY-WEB-OCR-SYSTEM-PLAN.md` を更新した |  |  |  |
|  | 【移行履歴】 |  |  |  |
|  | 元 `OT003001` に含まれていた「進捗通知ポーリング方式の仕様策定」部分を `SY` タスクとして分離記録した。`localapp` 側のリトライ実装・タイムアウト設定ファイル化は `OT003001` に残した |  |  |  |

---

## ユースケースNo | 007

ユースケース
`.clinerules` にユーザー対話時の厳格なワークフロー・表現ルールの改善

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| SY007001 | `SY` 識別子の運用ルールと 3 層スキル選択マトリックスを文書化する | 2026-09-05 | 2026-09-05 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `docs/SY-TASKS.md` に識別子運用ルールを明記する |  |  |  |
|  | `.clinerules` に `SY` / `OT` の使い分けルールと 3 層スキル選択マトリックスを追加する |  |  |  |
|  | `workflow-runner/SKILL.md` v2.0 を新規作成し、4 フェーズワークフローと選択的スキル読込を定義する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-05: `docs/SY-TASKS.md` に識別子運用ルールとタスク粒度の方針を明記した |  |  |  |
|  | 2026-09-05: `.clinerules` に `SY` / `OT` の使い分けルールと 3 層スキル選択マトリックスを追加した |  |  |  |
|  | 2026-09-05: `.cline/skills/workflow-runner/SKILL.md` を v2.0 に更新し、4 フェーズワークフローと選択的スキル読込を定義した |  |  |  |
| SY007002 | タスク着手時確認テンプレートの追加と `.clinerules` の整備 | 2026-09-06 | 2026-09-06 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.cline/skills/workflow-runner/SKILL.md` に「タスク着手時確認テンプレート」を追加する |  |  |  |
|  | Phase 1 Gate 1 / Phase 2 Gate 2 でテンプレートを使用するよう参照を追加する |  |  |  |
|  | `.clinerules` の `SY` / `OT` 識別子選択基準と `workflow-runner` 利用ルールを整備する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-06: `.cline/skills/workflow-runner/SKILL.md` に「タスク着手時確認テンプレート」を追加した |  |  |  |
|  | 2026-09-06: Phase 1 Gate 1 / Phase 2 Gate 2 でテンプレートを参照するよう更新した |  |  |  |
|  | 2026-09-06: `.clinerules` の識別子選択基準と `workflow-runner` 利用ルールを整備した |  |  |  |
|  | 2026-09-06: コミット `f3a18b34` として `.clinerules`, `.cline/skills/workflow-runner/SKILL.md`, `docs/SY-TASKS.md` を一括コミットした |  |  |  |
|  | 【移行履歴】 |  |  |  |
|  | `.clinerules` の変更は元々 `SY007001` の一環として実施されたものだが、当時未コミットのまま残っていたため、本タスクでまとめてコミットした |  |  |  |
| SY007003 | スキル読み込み時の `read_files` 必須ルールを `.clinerules` と `workflow-runner/SKILL.md` に追加する | 2026-09-06 | 2026-09-06 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.clinerules` の **Workflow Runner Usage** に、スキルファイル読み込み時は必ず `read_files` で実ファイルを開く規則を追加する |  |  |  |
|  | `.cline/skills/workflow-runner/SKILL.md` の **選択的スキル読込ルール** に、同様の `read_files` 必須規則を追加する |  |  |  |
|  | `docs/SY-TASKS.md` に本タスクを起票する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-06: `.clinerules` に「スキルファイル読み込みは `read_files` で実ファイルを開く」ルールを追加した |  |  |  |
|  | 2026-09-06: `.cline/skills/workflow-runner/SKILL.md` に「スキルファイル読み込みは `read_files` で実ファイルを開く」ルールを追加した |  |  |  |
|  | 2026-09-06: `docs/SY-TASKS.md` に `SY007003` を起票した |  |  |  |
|  | 2026-09-06: `.clinerules` に「タスクは並行実行せず、Phase 4 完了・コミット後に次のタスクを開始する」ルールを追加した |  |  |  |
|  | 2026-09-06: `.cline/skills/task-manager/SKILL.md` に「タスクは並行実行せず、Phase 4 完了・コミット後に次のタスクを開始する」ルールを追加した |  |  |  |
|  | 2026-09-06: `docs/SY-WORK-LOG.md` を新規作成した |  |  |  |
|  | 2026-09-06: 本タスクの変更を一括コミット `docs(SY007003): add parallel-task prohibition rule and post-process records` として記録した |  |  |  |
|  | 【移行履歴】 |  |  |  |
|  | 元々 `SY007001` / `SY007002` の整備作業中に指摘された運用漏れであり、個別の修正タスクとして分離した |  |  |  |
|  | 本タスク実施中に並行タスク禁止ルールの追加が発生したため、未コミット変更を `SY007003` に吸収して一括コミットした |  |  |  |
| SY007004 | ブランチ運用の再発防止ルールとユーザー表現ルールを追加する | 2026-09-06 | 2026-09-06 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.clinerules` に「タスク番号発行後実装」「feature ブランチ戦略」「重複ブランチ・重複コミット・重複実装禁止」ルールを追加する |  |  |  |
|  | `.clinerules` に「ユーザー表現の引用禁止」「意図の一般化・拡大解釈禁止」「二者択一の承認提示」ルールを追加する |  |  |  |
|  | `workflow-runner/SKILL.md` の Phase 1 に「ブランチ・タスク番号・重複確認」手順を追加する |  |  |  |
|  | `workflow-runner/SKILL.md` の Phase 4 に「未コミット確認・feature ブランチ作成・コミット・--no-ff マージ・ブランチ削除・push」の詳細手順を追加する |  |  |  |
|  | `branch-naming.md` に「禁止事項（Prohibited Operations）」セクションを追加する |  |  |  |
|  | `docs/SY-TASKS.md` に本タスク `SY007004` を起票する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-06: `.clinerules` にブランチ運用・重複防止ルールを追加した |  |  |  |
|  | 2026-09-06: `.clinerules` にユーザー表現・承認提示ルールを追加した |  |  |  |
|  | 2026-09-06: `workflow-runner/SKILL.md` の Phase 1 / Phase 4 を更新した |  |  |  |
|  | 2026-09-06: `branch-naming.md` に禁止事項セクションを追加した |  |  |  |
|  | 2026-09-06: `docs/SY-TASKS.md` に `SY007004` を起票した |  |  |  |
|  | 2026-09-06: 変更を feature ブランチ `feature/SY007004-clinerules-branch-rules` から main へ `--no-ff` マージした |  |  |  |
| SY007005 | ユーザー対話時の判断委ね構造とユースケース・タスク言及形式のルール追加 | 2026-09-07 | 2026-09-07 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.clinerules` の **User Communication** に「判断委ねの構造」（状況・選択肢・推奨・明示的質問）を追加する |  |  |  |
|  | `.clinerules` の **User Communication** に「ユースケース・タスク言及形式」（`SY007005` / `ユースケースNo ｜ 007` 等の canonical 形式）を追加する |  |  |  |
|  | `docs/SY-TASKS.md` に `SY007005` を起票する |  |  |  |
|  | `docs/SY-WORK-LOG.md` に `SY007005` の実施内容・結果を追記する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-07: `.clinerules` にユーザー対話時の判断委ね構造とユースケース・タスク言及形式のルールを追加した |  |  |  |
|  | 2026-09-07: `docs/SY-TASKS.md` に `SY007005` を起票した |  |  |  |
|  | 2026-09-07: `docs/SY-WORK-LOG.md` に `SY007005` の実施内容・結果を追記した |  |  |  |
|  | 2026-09-07: 変更を feature ブランチ `feature/SY007005-clinerules-user-comm-rules` から main へ `--no-ff` マージした |  |  |  |
| SY007006 | テスト関連ワークフローと検証合格基準のAgentSkills改善 | 2026-09-07 | 2026-09-07 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.clinerules` に「Phase 4 必須報告ルール」セクションを追加し、7項目のレポート枠組みを定義する |  |  |  |
|  | `.cline/skills/workflow-runner/SKILL.md` の Phase 4「最終報告書」手順を更新し、`.clinerules` の 7項目枠組みと `test-manager` スキルの Verification Report Template を参照させる |  |  |  |
|  | `.cline/skills/test-manager/SKILL.md` に「Verification Report Template（検証レポートテンプレート）」セクションを新設する |  |  |  |
|  | `.clinerules` / `workflow-runner/SKILL.md` / `test-manager/SKILL.md` において、ビルドテスト・単体テストの All Pass 基準と、ユーザー検証テスト合格までタスクを完了としないルールを追加する |  |  |  |
|  | `docs/SY-TASKS.md` に `SY007006` を起票する |  |  |  |
|  | `docs/SY-WORK-LOG.md` に `SY007006` の実施内容・結果を追記する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-07: `.clinerules` に「Phase 4 必須報告ルール」を追加した |  |  |  |
|  | 2026-09-07: `.cline/skills/workflow-runner/SKILL.md` の Phase 4「最終報告書」手順を更新した |  |  |  |
|  | 2026-09-07: `.cline/skills/test-manager/SKILL.md` に Verification Report Template（検証レポートテンプレート）を追加した |  |  |  |
|  | 2026-09-07: `docs/SY-TASKS.md` に `SY007006` を起票し、`SY007005` をユースケースNo 007 配下に整理した |  |  |  |
|  | 2026-09-07: `docs/SY-WORK-LOG.md` に `SY007006` の実施内容・結果を追記した |  |  |  |
|  | 2026-09-07: 変更を feature ブランチ `feature/SY007006-test-workflow-agentskills-improvement` から main へ `--no-ff` マージした |  |  |  |
|  | 2026-09-07: ユーザー検証テスト合格までタスクを完了としないルールを `.clinerules` / `workflow-runner/SKILL.md` / `test-manager/SKILL.md` に追加した |  |  |  |
|  | 2026-09-07: `.clinerules` / `workflow-runner/SKILL.md` にビルドテスト・単体テストの All Pass 基準を追加した |  |  |  |
|  | 2026-09-07: `test-manager/SKILL.md` の Verification Report Template に FAIL 時の再テスト手順とユーザー検証テスト承認ルールを追加した |  |  |  |
|  | 2026-09-07: `docs/SY-TASKS.md` の `SY007006` スコープを検証合格基準・ユーザー検証承認ゲートの追加に拡張した |  |  |  |
|  | 2026-09-07: `.clinerules` の **ユーザーコミュニケーション** セクションの英語記載を日本語に翻訳・入れ替えた |  |  |  |

---

## ユースケースNo | 009

ユースケース
モジュール横断不具合発見時のタスク管理

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| SY007007 | `.clinerules` と `workflow-runner` にモジュール横断不具合対応フローを追加 | 2026-09-07 | 2026-09-07 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.clinerules` に「Cross-Module Defect Handling」セクションを追加する |  |  |  |
|  | 対応中のタスク実行中に他のモジュールの不具合が見つかった場合は、対応中タスクを一時中断し、不具合発生モジュールのタスク登録を行うルールを定義する |  |  |  |
|  | 不具合発生モジュールのタスクが対応中タスクの完了に影響する場合は、追加タスクの完了を優先するルールを定義する |  |  |  |
|  | 不具合発生モジュールのタスクが対応中タスクの完了に影響しない場合は、追加タスクはタスク登録までとするルールを定義する |  |  |  |
|  | `.cline/skills/workflow-runner/SKILL.md` の Phase 3 に「Phase 3-A: 他モジュール不具合発見時の対応」を追加する |  |  |  |
|  | 規定ワークフロー（Phase 1〜Phase 2・Gate 1/2）に従ったタスク登録手順を定義する |  |  |  |
|  | `.clinerules` の **Core Constraints** に「原則として1タスク1ブランチを厳守する」ルールを追加する |  |  |  |
|  | `.cline/skills/workflow-runner/SKILL.md` の Git 運用手順に「原則として1タスク1ブランチを厳守する」ルールを追加する |  |  |  |
|  | `docs/SY-WORK-LOG.md` に本タスクの実施内容・結果を追記する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-07: `.clinerules` に「Cross-Module Defect Handling」セクションを追加した |  |  |  |
|  | 2026-09-07: `.clinerules` に「原則として1タスク1ブランチを厳守する」ルールを追加した |  |  |  |
|  | 2026-09-07: `.cline/skills/workflow-runner/SKILL.md` の Phase 3 に「Phase 3-A: 他モジュール不具合発見時の対応」を追加した |  |  |  |
|  | 2026-09-07: `.cline/skills/workflow-runner/SKILL.md` の Phase 3 に漏れていた「Phase 3-A: 他モジュール不具合発見時の対応」を追加した |  |  |  |
|  | 2026-09-07: `.cline/skills/workflow-runner/SKILL.md` の Git 運用手順に「原則として1タスク1ブランチを厳守する」ルールを追加した |  |  |  |
|  | 2026-09-07: `docs/SY-WORK-LOG.md` に本 `SY007007` の実施内容・結果を追記した |  |  |  |
|  | 2026-09-07: 変更を feature ブランチ `feature/SY007007-cross-module-defect-handling` から main へ `--no-ff` マージした |  |  |  |
|  | 2026-09-07: Phase 3-A の漏れを `main` で追加修正・コミットした |  |  |  |
|  | 2026-09-07: 漏れていた Phase 3-A 追加コミットを `docs/SY-TASKS.md` と `docs/SY-WORK-LOG.md` に反映した |  |  |  |
| SY007008 | `.clinerules`、AgentSkills の英文部分の日本語化 | 2026-09-07 | 2026-09-07 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.clinerules` の `Identity` / `Core Constraints` / `Approval Required` / `Project Context` / `Workflow Runner Usage` の英文を日本語に翻訳する |  |  |  |
|  | `code-generator/SKILL.md`、`file-modifier/SKILL.md`、`task-manager/SKILL.md`、`test-manager/SKILL.md`、`workflow-runner/SKILL.md` の英文セクション見出し（`## Overview` / `## Step-by-step Instructions` / `## Common Edge Cases`）を日本語にする |  |  |  |
|  | YAML frontmatter（`name` / `compatibility` / `author` / `version`）やコード・コマンド・ファイルパスは翻訳対象外とする |  |  |  |
|  | `docs/SY-WORK-LOG.md` に本 `SY007008` の実施内容・結果を追記する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-07: `.clinerules` の `Identity` / `Core Constraints` / `Approval Required` / `Project Context` / `Workflow Runner Usage` の英文を日本語に翻訳した |  |  |  |
|  | 2026-09-07: `code-generator/SKILL.md`、`file-modifier/SKILL.md`、`task-manager/SKILL.md`、`test-manager/SKILL.md`、`workflow-runner/SKILL.md` の英文セクション見出しを日本語化した |  |  |  |
|  | 2026-09-07: `.clinerules` 内の `Verification Report Template（検証レポートテンプレート）` の表記を `検証レポートテンプレート` に統一した |  |  |  |
|  | 2026-09-07: `docs/SY-WORK-LOG.md` に本 `SY007008` の実施内容・結果を追記した |  |  |  |
|  | 2026-09-07: 変更を feature ブランチ `feature/SY007008-english-to-japanese` から main へ `--no-ff` マージした |  |  |  |
| SY007009 | タスク完了基準・UAT判定ガイドの `.clinerules`・`workflow-runner` への追加 | 2026-09-08 | 2026-09-08 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.clinerules` に「タスク完了基準（必須チェックリスト）」を新設する |  |  |  |
|  | 完了日付を `<識別子>-TASKS.md` に記入する前の必須条件（Phase 3 PASS / Gate 3 承認 / UAT 合格 / Git merge 完了）を明文化する |  |  |  |
|  | `.clinerules` に「UAT実施要否判定ガイド」を新設する |  |  |  |
|  | UAT が必要なタスクと不要なタスクの判定基準を明確にする |  |  |  |
|  | `workflow-runner/SKILL.md` の Phase 4 手順4に「完了基準チェック」を追加する |  |  |  |
|  | 完了日付記入前に、ビルドPASS・テストPASS・UAT合格・Git merge の確認を義務付ける |  |  |  |
|  | `docs/SY-WORK-LOG.md` に本タスクの実施内容・結果を追記する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-08: `docs/SY-TASKS.md` に `SY007009` を起票した |  |  |  |
|  | 2026-09-08: `.clinerules` に「タスク完了基準」と「ユーザー検証テスト（UAT）実施要否判定ガイド」を追加した |  |  |  |
|  | 2026-09-08: `workflow-runner/SKILL.md` の Phase 4 に「完了基準チェック」を追加し、完了日付記入を完了基準満た後のみに限定した |  |  |  |
|  | 2026-09-08: `docs/SY-WORK-LOG.md` に本タスクの実施内容を追記した |  |  |  |
|  | 2026-09-08: Git commit / merge 実施（完了日付は merge 後に記入） |  |  |  |
| SY007010 | UAT 派生バグ対応タスク管理ルールの策定 | 2026-09-08 | 2026-09-08 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.clinerules` に「UAT 派生バグ対応タスク管理ルール」を新設する |  |  |  |
|  | 起票規則（`<元タスク番号> UATバグ対応`）を定める |  |  |  |
|  | バグ対応の集約（同一元タスク由来のバグを 1 タスクに統合）を定める |  |  |  |
|  | 完了順序（UATバグ対応完了 ≠ 元タスク完了；元タスク完了はユーザー承認必須）を定める |  |  |  |
|  | `.cline/skills/task-manager/SKILL.md` に「UAT 不具合発見時のタスク起票手順」を追加する |  |  |  |
|  | `.cline/skills/workflow-runner/SKILL.md` の冒頭に「1 タスク 1 ブランチ」の大前提を追加する（`.clinerules` との重複を許容） |  |  |  |
|  | `docs/SY-WORK-LOG.md` に本タスクの実施記録を追記する |  |  |  |
|  | 【実施結果】 |  |  |  |
| SY007011 | ブランチ運用スキルの独立と承認・マージブロック強化ルールの策定 | 2026-09-08 | 2026-09-08 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.cline/skills/branch-manager/SKILL.md` を新規作成し、分散しているブランチ運用ルールを一元化する |  |  |  |
|  | `.clinerules` に「マージ前最終承認チェックリスト（絶対遵守）」を追加する |  |  |  |
|  | `.clinerules` に「git 履歴の存在 ≠ タスク完了」の明文化を追加する |  |  |  |
|  | `.clinerules` にマージブロック条件（UAT合格発言なし・完了日付なし・Gate 3未承認）を禁止事項として追加する |  |  |  |
|  | `workflow-runner/SKILL.md` の Git 運用セクションからブランチ運用部分を削除し、`branch-manager` への参照に変更する |  |  |  |
|  | `workflow-runner/SKILL.md` の Phase 4 に「マージブロック条件チェック」を追加する |  |  |  |
|  | `task-manager/SKILL.md` に「タスク管理表との照合義務」を追加する |  |  |  |
|  | `branch-naming.md` に「マージ済みブランチの再作成例外」を明記する |  |  |  |
|  | 各種ドキュメントの重複記述を `branch-manager` への参照に一本化する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-08: `.cline/skills/branch-manager/SKILL.md` を新規作成し、ブランチ運用ルールを一元化した |  |  |  |
|  | 2026-09-08: ブランチ命名規則を `feature/<タスクNo>-<タスクのタイトル>` に変更した |  |  |  |
|  | 2026-09-08: ブランチ削除を AI 自動実行からユーザー手動実行に変更し、`.clinerules`・`workflow-runner`・`branch-manager` に反映した |  |  |  |
|  | 2026-09-08: マージ前承認チェックリストの表現を「ユーザーによるUAT明示的合格発言」「Gate 3 で承認依頼を実施して承認を得る」に統一した |  |  |  |
|  | 2026-09-08: `workflow-runner/references/branch-naming.md` の内容を整理し、`branch-manager` へのリダイレクト表記に簡潔化した |  |  |  |
|  | 2026-09-08: Git commit 実施 |  |  |  |
|  | 2026-09-08: `main` ブランチへ `--no-ff` でマージ完了（マージコミット: `22c1db4e`） |  |  |  |
|  | 2026-09-08: 不要となった feature ブランチの削除はユーザーが手動で実施（AI は自動削除しない） |  |  |  |
| SY007012 | UAT クロスモジュール不具合のタスク起票手順と優先順位ルールの明文化 | 2026-09-09 |  | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.clinerules` の `Cross-Module Defect Handling` に「UAT フェーズでの適用」を追加する |  |  |  |
|  | `workflow-runner/SKILL.md` の Phase 3-A に「UAT フェーズでの適用」を追加する |  |  |  |
|  | `task-manager/SKILL.md` の「UAT 不具合発見時の対応」にクロスモジュールの特別対応を追加する |  |  |  |
|  | `docs/SY-WORK-LOG.md` に本タスクの実施記録を追記する |  |  |  |
|  | 【実施結果】 |  |  |  |
