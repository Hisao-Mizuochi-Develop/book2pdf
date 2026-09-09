# Project タスク管理表

本ファイルは、Project のタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する
- タスク No は「モジュール識別子（2文字）＋ ユースケースNo（3桁）＋ 通番（3桁）」とする
  - 識別子: `PJ`=Project/プロジェクト運用・ガバナンス・ツール連携
  - 例：ユースケース001の1番目のタスク → `PJ001001`
- 通番は各ユースケース内で 001 から連番で振る


## ユースケース一覧

| ユースケースNo | タイトル |
|---|---|
| [PJ001](#pj001) | `.clinerules` / AgentSkills / ガバナンス・運用ルールの整備 |
| [PJ002](#pj002) | JIRA 連携設定・運用 |
| [PJ003](#pj003) | Confluence 連携設定・運用 |
| [PJ004](#pj004) | Slack 連携設定・運用 |

---

<a id="pj001"></a>
## ユースケースNo | PJ001

ユースケース
`.clinerules` / AgentSkills / ガバナンス・運用ルールの整備

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [PJ001001](#pj001001) `SY` 識別子の運用ルールと 3 層スキル選択マトリックスを文書化する | 2026-09-05 | 2026-09-05 | 運用整備 |
| [PJ001002](#pj001002) タスク着手時確認テンプレートの追加と `.clinerules` の整備 | 2026-09-06 | 2026-09-06 | 運用整備 |
| [PJ001003](#pj001003) スキル読み込み時の `read_files` 必須ルールを `.clinerules` と `workflow-runner/SKILL.md` に追加する | 2026-09-06 | 2026-09-06 | 運用整備 |
| [PJ001004](#pj001004) ブランチ運用の再発防止ルールとユーザー表現ルールを追加する | 2026-09-06 | 2026-09-06 | 運用整備 |
| [PJ001005](#pj001005) ユーザー対話時の判断委ね構造とユースケース・タスク言及形式のルール追加 | 2026-09-07 | 2026-09-07 | 運用整備 |
| [PJ001006](#pj001006) テスト関連ワークフローと検証合格基準のAgentSkills改善 | 2026-09-07 | 2026-09-07 | 運用整備 |
| [PJ001007](#pj001007) `.clinerules` と `workflow-runner` にモジュール横断不具合対応フローを追加する | 2026-09-07 | 2026-09-07 | 運用整備 |
| [PJ001008](#pj001008) `.clinerules`、AgentSkills の英文部分の日本語化 | 2026-09-07 | 2026-09-07 | 運用整備 |
| [PJ001009](#pj001009) タスク完了基準・UAT判定ガイドの `.clinerules`・`workflow-runner` への追加 | 2026-09-08 | 2026-09-08 | 運用整備 |
| [PJ001010](#pj001010) UAT 派生バグ対応タスク管理ルールの策定 | 2026-09-08 | 2026-09-08 | 運用整備 |
| [PJ001011](#pj001011) ブランチ運用スキルの独立と承認・マージブロック強化ルールの策定 | 2026-09-08 | 2026-09-08 | 運用整備 |
| [PJ001012](#pj001012) UAT クロスモジュール不具合のタスク起票手順と優先順位ルールの明文化 | 2026-09-09 | 2026-09-09 | 運用整備 |
| [PJ001013](#pj001013) Markdown pipe-table カラムずれ防止 AgentSkill・CI 導入 | 2026-09-09 | 2026-09-09 | 運用整備 |
| [PJ001014](#pj001014) feature ブランチ作業開始前のブランチ健全性チェックルール追加 | 2026-09-09 | 2026-09-09 | 運用整備 |
| [PJ001015](#pj001015) タスク管理表整合性検証ワークフローの強化 | 2026-09-09 | 2026-09-09 | 運用整備 |
| [PJ001016](#pj001016) PJ001015 UAT バグ対応 | 2026-09-09 | 2026-09-09 | 運用整備 |
| [PJ001017](#pj001017) `.clinerules`、AgentSkills の Phase 4 必須報告ルールとテストワークフロー整備 | 2026-09-10 | 2026-09-10 | 運用整備 |
| [PJ001018](#pj001018) `.clinerules` と `task-manager` AgentSkill に `TEMPLATE-TASKS.md` 参照義務を追加する | 2026-09-10 | | 運用整備 |

<a id="pj001001"></a>
### PJ001001 `SY` 識別子の運用ルールと 3 層スキル選択マトリックスを文書化する

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/SY-TASKS.md` にタスク粒度の方針を明記する
> - `.clinerules` に `SY` / `OT` の使い分けルールと 3 層スキル選択マトリックスを追加する
> - `workflow-runner/SKILL.md` v2.0 を新規作成し、4 フェーズワークフローと選択的スキル読込を定義する
>
> 【実施結果】
> - 2026-09-05: `docs/SY-TASKS.md` にタスク粒度の方針を明記した
> - 2026-09-05: `.clinerules` に `SY` / `OT` の使い分けルールと 3 層スキル選択マトリックスを追加した
> - 2026-09-05: `.cline/skills/workflow-runner/SKILL.md` を v2.0 に更新し、4 フェーズワークフローと選択的スキル読込を定義した
>
<a id="pj001002"></a>
### PJ001002 タスク着手時確認テンプレートの追加と `.clinerules` の整備

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.cline/skills/workflow-runner/SKILL.md` に「タスク着手時確認テンプレート」を追加する
> - Phase 1 Gate 1 / Phase 2 Gate 2 でテンプレートを使用するよう参照を追加する
> - `.clinerules` の `SY` / `OT` 識別子選択基準と `workflow-runner` 利用ルールを整備する
>
> 【実施結果】
> - 2026-09-06: `.cline/skills/workflow-runner/SKILL.md` に「タスク着手時確認テンプレート」を追加した
> - 2026-09-06: Phase 1 Gate 1 / Phase 2 Gate 2 でテンプレートを参照するよう更新した
> - 2026-09-06: `.clinerules` の識別子選択基準と `workflow-runner` 利用ルールを整備した
> - 2026-09-06: コミット `f3a18b34` として `.clinerules`, `.cline/skills/workflow-runner/SKILL.md`, `docs/SY-TASKS.md` を一括コミットした
>
<a id="pj001003"></a>
### PJ001003 スキル読み込み時の `read_files` 必須ルールを `.clinerules` と `workflow-runner/SKILL.md` に追加する

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` の **Workflow Runner Usage** に、スキルファイル読み込み時は必ず `read_files` で実ファイルを開く規則を追加する
> - `.cline/skills/workflow-runner/SKILL.md` の **選択的スキル読込ルール** に、同様の `read_files` 必須規則を追加する
> - `docs/SY-TASKS.md` に本タスクを起票する
>
> 【実施結果】
> - 2026-09-06: `.clinerules` に「スキルファイル読み込みは `read_files` で実ファイルを開く」ルールを追加した
> - 2026-09-06: `.cline/skills/workflow-runner/SKILL.md` に「スキルファイル読み込みは `read_files` で実ファイルを開く」ルールを追加した
> - 2026-09-06: `docs/SY-TASKS.md` に `SY007003` を起票した
> - 2026-09-06: `.clinerules` に「タスクは並行実行せず、Phase 4 完了・コミット後に次のタスクを開始する」ルールを追加した
> - 2026-09-06: `.cline/skills/task-manager/SKILL.md` に「タスクは並行実行せず、Phase 4 完了・コミット後に次のタスクを開始する」ルールを追加した
> - 2026-09-06: `docs/SY-WORK-LOG.md` を新規作成した
> - 2026-09-06: 本タスクの変更を一括コミット `docs(SY007003): add parallel-task prohibition rule and post-process records` として記録した
>
<a id="pj001004"></a>
### PJ001004 ブランチ運用の再発防止ルールとユーザー表現ルールを追加する

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` に「タスク番号発行後実装」「feature ブランチ戦略」「重複ブランチ・重複コミット・重複実装禁止」ルールを追加する
> - `.clinerules` に「ユーザー表現の引用禁止」「意図の一般化・拡大解釈禁止」「二者択一の承認提示」ルールを追加する
> - `workflow-runner/SKILL.md` の Phase 1 に「ブランチ・タスク番号・重複確認」手順を追加する
> - `workflow-runner/SKILL.md` の Phase 4 に「未コミット確認・feature ブランチ作成・コミット・--no-ff マージ・ブランチ削除・push」の詳細手順を追加する
> - `branch-naming.md` に「禁止事項（Prohibited Operations）」セクションを追加する
> - `docs/SY-TASKS.md` に本タスク `SY007004` を起票する
>
> 【実施結果】
> - 2026-09-06: `.clinerules` にブランチ運用・重複防止ルールを追加した
> - 2026-09-06: `.clinerules` にユーザー表現・承認提示ルールを追加した
> - 2026-09-06: `workflow-runner/SKILL.md` の Phase 1 / Phase 4 を更新した
> - 2026-09-06: `branch-naming.md` に禁止事項セクションを追加した
> - 2026-09-06: `docs/SY-TASKS.md` に `SY007004` を起票した
> - 2026-09-06: 変更を feature ブランチ `feature/SY007004-clinerules-branch-rules` から main へ `--no-ff` マージした
>
<a id="pj001005"></a>
### PJ001005 ユーザー対話時の判断委ね構造とユースケース・タスク言及形式のルール追加

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` の **User Communication** に「判断委ねの構造」（状況・選択肢・推奨・明示的質問）を追加する
> - `.clinerules` の **User Communication** に「ユースケース・タスク言及形式」（`SY007005` / `ユースケースNo ｜ 007` 等の canonical 形式）を追加する
> - `docs/SY-TASKS.md` に `SY007005` を起票する
> - `docs/SY-WORK-LOG.md` に `SY007005` の実施内容・結果を追記する
>
> 【実施結果】
> - 2026-09-07: `.clinerules` にユーザー対話時の判断委ね構造とユースケース・タスク言及形式のルールを追加した
> - 2026-09-07: `docs/SY-TASKS.md` に `SY007005` を起票した
> - 2026-09-07: `docs/SY-WORK-LOG.md` に `SY007005` の実施内容・結果を追記した
> - 2026-09-07: 変更を feature ブランチ `feature/SY007005-clinerules-user-comm-rules` から main へ `--no-ff` マージした
>
<a id="pj001006"></a>
### PJ001006 テスト関連ワークフローと検証合格基準のAgentSkills改善

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` に「Phase 4 必須報告ルール」セクションを追加し、7項目のレポート枠組みを定義する
> - `.cline/skills/workflow-runner/SKILL.md` の Phase 4「最終報告書」手順を更新し、`.clinerules` の 7項目枠組みと `test-manager` スキルの Verification Report Template を参照させる
> - `.cline/skills/test-manager/SKILL.md` に「Verification Report Template（検証レポートテンプレート）」セクションを新設する
> - `.clinerules` / `workflow-runner/SKILL.md` / `test-manager/SKILL.md` において、ビルドテスト・単体テストの All Pass 基準と、ユーザー検証テスト合格までタスクを完了としないルールを追加する
> - `docs/SY-TASKS.md` に `SY007006` を起票する
> - `docs/SY-WORK-LOG.md` に `SY007006` の実施内容・結果を追記する
>
> 【実施結果】
> - 2026-09-07: `.clinerules` に「Phase 4 必須報告ルール」を追加した
> - 2026-09-07: `.cline/skills/workflow-runner/SKILL.md` の Phase 4「最終報告書」手順を更新した
> - 2026-09-07: `.cline/skills/test-manager/SKILL.md` に Verification Report Template（検証レポートテンプレート）を追加した
> - 2026-09-07: `docs/SY-TASKS.md` に `SY007006` を起票し、`SY007005` をユースケースNo 007 配下に整理した
> - 2026-09-07: `docs/SY-WORK-LOG.md` に `SY007006` の実施内容・結果を追記した
> - 2026-09-07: 変更を feature ブランチ `feature/SY007006-test-workflow-agentskills-improvement` から main へ `--no-ff` マージした
> - 2026-09-07: ユーザー検証テスト合格までタスクを完了としないルールを `.clinerules` / `workflow-runner/SKILL.md` / `test-manager/SKILL.md` に追加した
> - 2026-09-07: `.clinerules` / `workflow-runner/SKILL.md` にビルドテスト・単体テストの All Pass 基準を追加した
> - 2026-09-07: `test-manager/SKILL.md` の Verification Report Template に FAIL 時の再テスト手順とユーザー検証テスト承認ルールを追加した
> - 2026-09-07: `docs/SY-TASKS.md` の `SY007006` スコープを検証合格基準・ユーザー検証承認ゲートの追加に拡張した
> - 2026-09-07: `.clinerules` の **ユーザーコミュニケーション** セクションの英語記載を日本語に翻訳・入れ替えた
>
<a id="pj001007"></a>
### PJ001007 `.clinerules` と `workflow-runner` にモジュール横断不具合対応フローを追加する

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` に「Cross-Module Defect Handling」セクションを追加する
> - 対応中のタスク実行中に他のモジュールの不具合が見つかった場合は、対応中タスクを一時中断し、不具合発生モジュールのタスク登録を行うルールを定義する
> - 不具合発生モジュールのタスクが対応中タスクの完了に影響する場合は、追加タスクの完了を優先するルールを定義する
> - 不具合発生モジュールのタスクが対応中タスクの完了に影響しない場合は、追加タスクはタスク登録までとするルールを定義する
> - `.cline/skills/workflow-runner/SKILL.md` の Phase 3 に「Phase 3-A: 他モジュール不具合発見時の対応」を追加する
> - 規定ワークフロー（Phase 1〜Phase 2・Gate 1/2）に従ったタスク登録手順を定義する
> - `.clinerules` の **Core Constraints** に「原則として1タスク1ブランチを厳守する」ルールを追加する
> - `.cline/skills/workflow-runner/SKILL.md` の Git 運用手順に「原則として1タスク1ブランチを厳守する」ルールを追加する
> - `docs/SY-WORK-LOG.md` に本タスクの実施内容・結果を追記する
>
> 【実施結果】
> - 2026-09-07: `.clinerules` に「Cross-Module Defect Handling」セクションを追加した
> - 2026-09-07: `.clinerules` に「原則として1タスク1ブランチを厳守する」ルールを追加した
> - 2026-09-07: `.cline/skills/workflow-runner/SKILL.md` の Phase 3 に「Phase 3-A: 他モジュール不具合発見時の対応」を追加した
> - 2026-09-07: `.cline/skills/workflow-runner/SKILL.md` の Phase 3 に漏れていた「Phase 3-A: 他モジュール不具合発見時の対応」を追加した
> - 2026-09-07: `.cline/skills/workflow-runner/SKILL.md` の Git 運用手順に「原則として1タスク1ブランチを厳守する」ルールを追加した
> - 2026-09-07: `docs/SY-WORK-LOG.md` に本 `SY007007` の実施内容・結果を追記した
> - 2026-09-07: 変更を feature ブランチ `feature/SY007007-cross-module-defect-handling` から main へ `--no-ff` マージした
> - 2026-09-07: Phase 3-A の漏れを `main` で追加修正・コミットした
> - 2026-09-07: 漏れていた Phase 3-A 追加コミットを `docs/SY-TASKS.md` と `docs/SY-WORK-LOG.md` に反映した
>
<a id="pj001008"></a>
### PJ001008 `.clinerules`、AgentSkills の英文部分の日本語化

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` の `Identity` / `Core Constraints` / `Approval Required` / `Project Context` / `Workflow Runner Usage` の英文を日本語に翻訳する
> - `code-generator/SKILL.md`、`file-modifier/SKILL.md`、`task-manager/SKILL.md`、`test-manager/SKILL.md`、`workflow-runner/SKILL.md` の英文セクション見出し（`## Overview` / `## Step-by-step Instructions` / `## Common Edge Cases`）を日本語にする
> - YAML frontmatter（`name` / `compatibility` / `author` / `version`）やコード・コマンド・ファイルパスは翻訳対象外とする
> - `docs/SY-WORK-LOG.md` に本 `SY007008` の実施内容・結果を追記する
>
> 【実施結果】
> - 2026-09-07: `.clinerules` の `Identity` / `Core Constraints` / `Approval Required` / `Project Context` / `Workflow Runner Usage` の英文を日本語に翻訳した
> - 2026-09-07: `code-generator/SKILL.md`、`file-modifier/SKILL.md`、`task-manager/SKILL.md`、`test-manager/SKILL.md`、`workflow-runner/SKILL.md` の英文セクション見出しを日本語化した
> - 2026-09-07: `.clinerules` 内の `Verification Report Template（検証レポートテンプレート）` の表記を `検証レポートテンプレート` に統一した
> - 2026-09-07: `docs/SY-WORK-LOG.md` に本 `SY007008` の実施内容・結果を追記した
> - 2026-09-07: 変更を feature ブランチ `feature/SY007008-english-to-japanese` から main へ `--no-ff` マージした
>
<a id="pj001009"></a>
### PJ001009 タスク完了基準・UAT判定ガイドの `.clinerules`・`workflow-runner` への追加

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` に「タスク完了基準（必須チェックリスト）」を新設する
> - 完了日付を `<識別子>-TASKS.md` に記入する前の必須条件（Phase 3 PASS / Gate 3 承認 / UAT 合格 / Git merge 完了）を明文化する
> - `.clinerules` に「UAT実施要否判定ガイド」を新設する
> - UAT が必要なタスクと不要なタスクの判定基準を明確にする
> - `workflow-runner/SKILL.md` の Phase 4 手順4に「完了基準チェック」を追加する
> - 完了日付記入前に、ビルドPASS・テストPASS・UAT合格・Git merge の確認を義務付ける
> - `docs/SY-WORK-LOG.md` に本タスクの実施内容・結果を追記する
>
> 【実施結果】
> - 2026-09-08: `docs/SY-TASKS.md` に `SY007009` を起票した
> - 2026-09-08: `.clinerules` に「タスク完了基準」と「ユーザー検証テスト（UAT）実施要否判定ガイド」を追加した
> - 2026-09-08: `workflow-runner/SKILL.md` の Phase 4 に「完了基準チェック」を追加し、完了日付記入を完了基準満た後のみに限定した
> - 2026-09-08: `docs/SY-WORK-LOG.md` に本タスクの実施内容を追記した
> - 2026-09-08: Git commit / merge 実施（完了日付は merge 後に記入）
>
<a id="pj001010"></a>
### PJ001010 UAT 派生バグ対応タスク管理ルールの策定

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` に「UAT 派生バグ対応タスク管理ルール」を新設する
> - 起票規則（`<元タスク番号> UATバグ対応`）を定める
> - バグ対応の集約（同一元タスク由来のバグを 1 タスクに統合）を定める
> - 完了順序（UATバグ対応完了 ≠ 元タスク完了；元タスク完了はユーザー承認必須）を定める
> - `.cline/skills/task-manager/SKILL.md` に「UAT 不具合発見時のタスク起票手順」を追加する
> - `.cline/skills/workflow-runner/SKILL.md` の冒頭に「1 タスク 1 ブランチ」の大前提を追加する（`.clinerules` との重複を許容）
> - `docs/SY-WORK-LOG.md` に本タスクの実施記録を追記する
>
> 【実施結果】
> - `.clinerules` に「UAT 派生バグ対応タスク管理ルール」を新設した
> - `task-manager/SKILL.md` と `workflow-runner/SKILL.md` を更新した
>
<a id="pj001011"></a>
### PJ001011 ブランチ運用スキルの独立と承認・マージブロック強化ルールの策定

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.cline/skills/branch-manager/SKILL.md` を新規作成し、分散しているブランチ運用ルールを一元化する
> - `.clinerules` に「マージ前最終承認チェックリスト（絶対遵守）」を追加する
> - `.clinerules` に「git 履歴の存在 ≠ タスク完了」の明文化を追加する
> - `.clinerules` にマージブロック条件（UAT合格発言なし・完了日付なし・Gate 3未承認）を禁止事項として追加する
> - `workflow-runner/SKILL.md` の Git 運用セクションからブランチ運用部分を削除し、`branch-manager` への参照に変更する
> - `workflow-runner/SKILL.md` の Phase 4 に「マージブロック条件チェック」を追加する
> - `task-manager/SKILL.md` に「タスク管理表との照合義務」を追加する
> - `branch-naming.md` に「マージ済みブランチの再作成例外」を明記する
> - 各種ドキュメントの重複記述を `branch-manager` への参照に一本化する
>
> 【実施結果】
> - 2026-09-08: `.cline/skills/branch-manager/SKILL.md` を新規作成し、ブランチ運用ルールを一元化した
> - 2026-09-08: ブランチ命名規則を `feature/<タスクNo>-<タスクのタイトル>` に変更した
> - 2026-09-08: ブランチ削除を AI 自動実行からユーザー手動実行に変更し、`.clinerules`・`workflow-runner`・`branch-manager` に反映した
> - 2026-09-08: マージ前承認チェックリストの表現を「ユーザーによるUAT明示的合格発言」「Gate 3 で承認依頼を実施して承認を得る」に統一した
> - 2026-09-08: `workflow-runner/references/branch-naming.md` の内容を整理し、`branch-manager` へのリダイレクト表記に簡潔化した
> - 2026-09-08: Git commit 実施
> - 2026-09-08: `main` ブランチへ `--no-ff` でマージ完了（マージコミット: `22c1db4e`）
> - 2026-09-08: 不要となった feature ブランチの削除はユーザーが手動で実施（AI は自動削除しない）
>
<a id="pj001012"></a>
### PJ001012 UAT クロスモジュール不具合のタスク起票手順と優先順位ルールの明文化

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` の `Cross-Module Defect Handling` に「UAT フェーズでの適用」を追加する
> - `workflow-runner/SKILL.md` の Phase 3-A に「UAT フェーズでの適用」を追加する
> - `task-manager/SKILL.md` の「UAT 不具合発見時の対応」にクロスモジュールの特別対応を追加する
> - `docs/SY-WORK-LOG.md` に本タスクの実施記録を追記する
>
> 【実施結果】
> - 2026-09-09: `.clinerules` に「5. UAT フェーズでの適用」を追加した
> - 2026-09-09: `workflow-runner/SKILL.md` の Phase 3-A に「5. UAT フェーズでの適用」を追加した
> - 2026-09-09: `task-manager/SKILL.md` の「8. UAT 不具合発見時の対応」に「クロスモジュールの場合」を追加した
> - 2026-09-09: `docs/SY-WORK-LOG.md` に本タスクの実施記録を追記した
> - 2026-09-09: Git commit 実施
> - 2026-09-09: `main` ブランチへ `--no-ff` でマージ完了
>
<a id="pj001013"></a>
### PJ001013 Markdown pipe-table カラムずれ防止 AgentSkill・CI 導入

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - AgentSkill `markdown-table-validator` を新規作成する
> - `.clinerules` に「Markdown Pipe-Table Editing Rules」セクションを追加する
> - `file-modifier/SKILL.md` に Markdown テーブル検証ルールを追加する
> - `task-manager/SKILL.md` にタスク管理表更新後のカラム整合性チェックを追加する
> - `workflow-runner/SKILL.md` の Phase 3 に Markdown テーブル検証を追加する
> - `scripts/lint-task-md.py` を新規作成する
> - `.github/workflows/lint-task-md.yml` を新規作成する
> - `.pre-commit-config.yaml` を新規作成する
> - `docs/OT-AGENT-SKILLS-GUIDE.md` に `markdown-table-validator` を追加する
>
> 【実施結果】
> - `markdown-table-validator` AgentSkill と `scripts/lint-task-md.py` を新規作成した
> - `.github/workflows/lint-task-md.yml` と `.pre-commit-config.yaml` を新規作成した
>
<a id="pj001014"></a>
### PJ001014 feature ブランチ作業開始前のブランチ健全性チェックルール追加

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` に「Branch Health Check Rules」セクションを追加する
> - `.cline/skills/branch-manager/SKILL.md` に「作業開始前のブランチ健全性確認」を追加する
> - `.cline/skills/workflow-runner/SKILL.md` の Phase 1 / Phase 4 を更新する
> - `docs/PJ-WORK-LOG.md` に実施記録を追記する
>
> 【実施結果】
> - 2026-09-09: `.clinerules` に「Branch Health Check Rules」セクションを追加した
> - 2026-09-09: `.cline/skills/branch-manager/SKILL.md` に「作業開始前のブランチ健全性確認」を追加した
> - 2026-09-09: `.cline/skills/workflow-runner/SKILL.md` の Phase 1 / Phase 4 を更新した
> - 2026-09-09: `docs/PJ-WORK-LOG.md` に実施記録を追記した
>
<a id="pj001015"></a>
### PJ001015 タスク管理表整合性検証ワークフローの強化

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` に新規タスク起票テンプレート・Plan モード編集禁止ルールを追加する
> - `scripts/lint-task-md.py` に「完了日付・実施結果」整合性検証を追加する
> - `workflow-runner/SKILL.md` Phase 1 に完了状態確認手順を追加する
>
> 【実施結果】
> - 2026-09-09: `.clinerules` に「Task Management Integrity Rules」を新設した
> - 2026-09-09: `scripts/lint-task-md.py` に「完了日付・実施結果」整合性検証を追加した
> - 2026-09-09: `workflow-runner/SKILL.md` Phase 1 に完了状態確認手順を追加した
> - 2026-09-09: `docs/PJ-TASKS.md` PJ001010 / PJ001013 の【実施結果】空欄を追記した
>
<a id="pj001016"></a>
### PJ001016 PJ001015 UAT バグ対応

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - PJ001015 の【実施結果】空欄を修正する
> - PJ001014 の【実施結果】空欄と完了日付を修正する
>
> 【実施結果】
> - PJ001015 / PJ001014 の【実施結果】と【完了日付】を修正し、UAT 不合格を解消した
>

---

<a id="pj001017"></a>
### PJ001017 `.clinerules`、AgentSkills の Phase 4 必須報告ルールとテストワークフロー整備

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` に Phase 4 必須報告ルールを追加する
> - `workflow-runner/SKILL.md` に Phase 4 必須報告ルールを追加する
> - `test-manager/SKILL.md` に Phase 4 必須報告ルールを追加する
> - テスト関連ワークフローを AgentSkills に統合する
>
> 【実施結果】
> - 2026-09-10: `.clinerules` / `workflow-runner/SKILL.md` / `test-manager/SKILL.md` に Phase 4 必須報告ルールを追加した
> - 2026-09-10: テスト関連ワークフローを AgentSkills に統合した
>
<a id="pj001018"></a>
### PJ001018 `.clinerules` と `task-manager` AgentSkill に `TEMPLATE-TASKS.md` 参照義務を追加する

<div align="right"><a href="#pj001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.cline/skills/task-manager/SKILL.md` の「手順」に `TEMPLATE-TASKS.md` 参照義務を追加する
> - `.cline/skills/task-manager/SKILL.md` の「参考資料」リンクを「必須参照」に昇格させる
> - `.clinerules` にタスク管理表作成・更新時のテンプレート参照義務を追加する
> - `python scripts/lint-task-md.py` でパイプテーブル整合性を検証する
>
> 【実施結果】
> - （未実施）
>
<a id="pj002"></a>
## ユースケースNo | PJ002

ユースケース
JIRA 連携設定・運用

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| （将来のタスクをここに追加） | | | |


---

<a id="pj003"></a>
## ユースケースNo | PJ003

ユースケース
Confluence 連携設定・運用

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| （将来のタスクをここに追加） | | | |


---

<a id="pj004"></a>
## ユースケースNo | PJ004

ユースケース
Slack 連携設定・運用

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| （将来のタスクをここに追加） | | | |

