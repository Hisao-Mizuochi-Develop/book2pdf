# OT タスク管理表

本ファイルは、`backend` / `frontend` / `ocr-worker` / `localapp` の個別の機能や性能、または全体の機能や性能に関すること以外のタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

> 最終更新: 2026/09/20

---

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する
- タスク No は「モジュール識別子（2文字）＋ ユースケースNo（3桁）＋ 通番（3桁）」とする
  - 識別子: `OT`=横断・その他
  - 例：ユースケース001の1番目のタスク → `OT001001`
- 通番は各ユースケース内で 001 から連番で振る

## ユースケース一覧

| ユースケースNo | タイトル |
|---|---|
| [OT001](#ot001) | プロジェクト全体のドキュメント整備 |
| [OT002](#ot002) | 複数モジュールにまたがる注意事項の一元管理 |
| [OT003](#ot003) | 進捗通知方式の整備と localapp ポーリングの改善 |
| [OT004](#ot004) | `OT` に誤分類された System / 全体設計タスクの切り出しと運用ルール整備 |
| [OT005](#ot005) | localapp 単体 OCR→PDF 技術調査・選定 |
| [OT006](#ot006) | タスク管理ファイルのカラムずれ・空行整備 |
| [OT007](#ot007) | 新規モジュール識別子 `PJ` の設立と `.clinerules`/AgentSkills ガバナンスの移行 |
| [OT008](#ot008) | タスク管理ファイルフォーマット統一と整合性全チェック |
| [OT009](#ot009) | ドキュメント最終更新日メタデータ標準化と運用ルール整備 |
| [OT010](#ot010) | docs/ 配下の図を Mermaid 化する |
| [OT011](#ot011) | `frontend` タスク管理表から不要なユースケースを削除する |

---

<a id="ot001"></a>
## ユースケースNo | OT001

ユースケース
プロジェクト全体のドキュメント整備

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [OT001001](#ot001001) 全体計画書・設計決定事項・コーディング規約の整備 | 2026-08-11 | 2026-08-11 | 設計 |
| [OT001002](#ot001002) 結合テスト手順書の作成 | 2026-08-12 | 2026-08-12 | ドキュメント |

<a id="ot001001"></a>
### OT001001 全体計画書・設計決定事項・コーディング規約の整備

<div align="right"><a href="#ot001">タスク一覧へ↩︎</a></div>

> 【計画】
> - プロジェクト全体の構成を `docs/SY-WEB-OCR-SYSTEM-PLAN.md` にまとめる
> - 技術選定の理由を `docs/SY-DESIGN-DECISIONS.md` にまとめる
> - Python / TypeScript / Rust のコーディング規約を `docs/PJ-CODING-CONVENTIONS.md` にまとめる
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot001002"></a>
### OT001002 結合テスト手順書の作成

<div align="right"><a href="#ot001">タスク一覧へ↩︎</a></div>

> 【計画】
> - `frontend` / `backend` / `ocr-worker` を横断した結合テスト手順を `./docs/SY-INTEGRATION-TEST-GUIDE.md` にまとめる
> - テスト準備、コンテナ起動、UI / cURL による手順、トラブルシューティング、終了処理を含める
> - `docs/SY-WEB-OCR-SYSTEM-PLAN.md` のフォルダ・ファイル構成と関連ドキュメントに `SY-INTEGRATION-TEST-GUIDE.md` へのリンクを追加する
> - `.clinerules` に `./docs/` 配下にも `OT-TASKS.md` / `OT-WORK-LOG.md` / `OT-CAVEATS.md` を配置するルールを明記する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot002"></a>
## ユースケースNo | OT002

ユースケース
複数モジュールにまたがる注意事項の一元管理

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [OT002001](#ot002001) 全体横断の注意事項ファイルを作成する | 2026-08-12 | 2026-08-12 | ドキュメント |
| [OT002002](#ot002002) `OT-CAVEATS.md` の分離設計と移行計画策定 | 2026-09-06 | 2026-09-06 | ドキュメント設計 |
| [OT002003](#ot002003) `docs/OT-CAVEATS.md` の内容を各モジュールの `*-CAVEATS.md` に再配布する | 2026-09-06 | 2026-09-06 | ドキュメント整理 |

<a id="ot002001"></a>
### OT002001 全体横断の注意事項ファイルを作成する

<div align="right"><a href="#ot002">タスク一覧へ↩︎</a></div>

> 【計画】
> - `./docs/OT-CAVEATS.md` を新規作成し、複数モジュールにまたがる注意事項を集約する
> - 各モジュール固有の注意事項は `<module>/docs/<モジュール識別子>-CAVEATS.md` に残し、ここでは全体横断の視点だけを記載する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot002002"></a>
### OT002002 `OT-CAVEATS.md` の分離設計と移行計画策定

<div align="right"><a href="#ot002">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/OT-CAVEATS.md` の内容を、モジュール固有の注意事項と横断的な注意事項に分類する
> - 各モジュール固有の注意事項の移行先（`backend/docs/BE-CAVEATS.md` / `localapp/docs/LA-CAVEATS.md` / `ocr-worker/docs/OW-CAVEATS.md` / `frontend/docs/FE-CAVEATS.md`）を決定する
> - 横断的な注意事項を集約する `docs/SY-CAVEATS.md` の構成案を作成する
> - `docs/OT-TASKS.md` / `docs/OT-WORK-LOG.md` に本タスクを記録する
> - 実際の移行・削除は OT002003 として別タスクで実施する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot002003"></a>
### OT002003 `docs/OT-CAVEATS.md` の内容を各モジュールの `*-CAVEATS.md` に再配布する

<div align="right"><a href="#ot002">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/OT-CAVEATS.md` に記載されているモジュール固有の注意事項を `backend/docs/BE-CAVEATS.md` / `localapp/docs/LA-CAVEATS.md` / `ocr-worker/docs/OW-CAVEATS.md` に移動する
> - `frontend/docs/FE-CAVEATS.md` で既にカバーされている項目は `docs/OT-CAVEATS.md` から削除するのみとする
> - 横断的な参照だけを `docs/SY-CAVEATS.md` に集約し、新規作成する
> - 再配布完了後、`docs/OT-CAVEATS.md` を削除する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot003"></a>
## ユースケースNo | OT003

ユースケース
進捗通知方式の整備と localapp ポーリングの改善

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [OT003001](#ot003001) 進捗通知のポーリング方式仕様策定と localapp リトライ実装 | 2026-09-03 | 2026-09-03 | 設計 / 実装 |

<a id="ot003001"></a>
### OT003001 進捗通知のポーリング方式仕様策定と localapp リトライ実装

<div align="right"><a href="#ot003">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/progress-notification-polling-design.md` と `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` を統合し、SSE / HTTP ポーリングの全体仕様を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に整理する
> - 進捗ペイロード `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止する
> - ポーリングプロトコルを文書化する（1 リクエストあたり 10 秒タイムアウト、1 秒 / 2 秒 / 4 秒の指数関数的バックオフ、最大 3 回リトライ）
> - `localapp/src-tauri/src/commands/backend_api/backend_api_impl.rs` の `GET /api/jobs/{job_id}` ポーリング処理に、per-request タイムアウトと指数関数的バックオフによるリトライを実装する
> - リトライ前に「ジョブ状態の取得を再試行します」という進捗メッセージを UI に通知し、ユーザーに一過性の通信エラーであることを伝える
> - `docs/OT-TASKS.md` / `docs/OT-WORK-LOG.md` / `docs/OT-CAVEATS.md` / `docs/SY-WEB-OCR-SYSTEM-PLAN.md` / `docs/README.md` を更新する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot004"></a>
## ユースケースNo | OT004

ユースケース
`OT` に誤分類された System / 全体設計タスクの切り出しと運用ルール整備

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [OT004001](#ot004001) `OT` に誤分類された System タスクを `SY` に分離し、運用ルールとスキルマトリックスを整備する | 2026-09-05 | 2026-09-05 | 運用整備 |
| [OT004002](#ot004002) `OT` の識別子を名乗るが内容が `PJ`/`OW`/`SY` 系のガイド文書を正しい識別子に再分類する | 2026-09-13 | 2026-09-13 | 運用整備 |

<a id="ot004001"></a>
### OT004001 `OT` に誤分類された System タスクを `SY` に分離し、運用ルールとスキルマトリックスを整備する

<div align="right"><a href="#ot004">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/OT-TASKS.md` に本タスク（OT004001）を追記する
> - `docs/SY-TASKS.md` を新規作成し、元 `OT001001` / `OT003001` に含まれていた System / 全体設計・仕様策定部分を `SY` タスクとして移行記録する
> - `.clinerules` に `SY` / `OT` の使い分けルールと 3 層スキル選択マトリックスを追加する
> - `workflow-runner/SKILL.md` v2.0 を新規作成し、4 フェーズワークフローと選択的スキル読込を定義する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot004002"></a>
### OT004002 `OT` の識別子を名乗るが内容が `PJ`/`OW`/`SY` 系のガイド文書を正しい識別子に再分類する

<div align="right"><a href="#ot004">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/OT-AGENT-SKILLS-GUIDE.md` を `docs/PJ-AGENT-SKILLS-GUIDE.md` に改名する
> - `docs/OT-OCR-PREPROCESSING-GUIDE.md` を `docs/OW-OCR-PREPROCESSING-GUIDE.md` に改名する
> - `docs/OT-INTEGRATION-TEST-GUIDE.md` を `docs/SY-INTEGRATION-TEST-GUIDE.md` に改名する
> - `docs/OT-DEBUG-LOGGING-GUIDE.md` を `docs/SY-DEBUG-LOGGING-GUIDE.md` に改名する
> - `docs/OT-CODING-CONVENTIONS.md` を `docs/PJ-CODING-CONVENTIONS.md` に改名する
> - 上記ファイル名を参照しているすべてのドキュメント内リンクを新ファイル名に更新する
> - `python scripts/lint-task-md.py` でパイプテーブル整合性を検証する
>
> 【実施結果】
> - 2026-09-13: `docs/README.md` の「タスク管理・作業ログ・注意事項」セクションを新設し、すべての `XX-TASKS.md` / `XX-WORK-LOG.md` / `XX-CAVEATS.md` へのリンクを集約した
> - 2026-09-13: 各モジュールセクション（BE/FE/LA/OW/PJ/SY/OT）から `*-TASKS.md` / `*-WORK-LOG.md` / `*-CAVEATS.md` の個別記載を削除した
> - 2026-09-13: 紛失していた `* 2.md` ファイルを削除し、`.clinerules` へのリンクしかなかった `OT-AGENT-SKILLS-GUIDE.md` の重複エントリを解消した
> - 2026-09-13: `docs/README.md` の最終更新日を `2026/09/13` に更新した
> - 2026-09-13: `python scripts/lint-task-md.py` でパイプテーブル整合性を検証し ALL PASS を確認した
> - 2026-09-13: 変更を `feature/OT004002-ot-docs-reclassify` および `feature/OT004002-ot-docs-reclassify-followup` でコミットし、`main` へ `--no-ff` マージ・push した
> - 2026-09-13: `docs/OT-TASKS.md` のユースケース一覧（OT002～OT008）にページ内リンク用 HTML アンカー `<a id="ot00X">` を追加し、一覧からの遷移が機能するように修正した
> - 2026-09-13: `OT002003` のタイトルを修正し（`OT-CAVEATS.md` を削除する → 内容を各モジュールに再配布する）、ファイル削除の意図をより正確に表現した
>
<a id="ot005"></a>
## ユースケースNo | OT005

ユースケース
localapp 単体 OCR→PDF 技術調査・選定

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [OT005001](#ot005001) localapp 単体 OCR→PDF 技術調査・選定（LA008007 連携） | 2026-09-03 | 2026-09-04 | 調査 / 設計 |

<a id="ot005001"></a>
### OT005001 localapp 単体 OCR→PDF 技術調査・選定（LA008007 連携）

<div align="right"><a href="#ot005">タスク一覧へ↩︎</a></div>

> 【計画】
> - localapp 単体で動作する OCR→PDF パイプラインの技術調査と選定を行う
> - 候補技術（Tesseract / `leptess` / `printpdf` 等）を調査し、PoC を実施する
> - 選定結果を `localapp/docs/LA-OCR-TECHNOLOGY-SURVEY-LA008007.md` にまとめる
> - LA008007 と連携し、localapp 側の調査結果を反映する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot006"></a>
## ユースケースNo | OT006

ユースケース
タスク管理ファイルのカラムずれ・空行整備

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [OT006001](#ot006001) タスク管理ファイルのカラムずれ・空行整備 | 2026-09-09 | 2026-09-09 | 文書整備 |

<a id="ot006001"></a>
### OT006001 タスク管理ファイルのカラムずれ・空行整備

<div align="right"><a href="#ot006">タスク一覧へ↩︎</a></div>

> 【計画】
> - `frontend/docs/FE-TASKS.md` のカラムずれを修正する
> - `frontend/docs/FE-TASKS.md` の余分な空行を削除する
> - `FE002001`・`FE002002` の【タスク完了日付】を削除し未完了状態に戻す（AI が誤って完了日付を記入したため）
> - 必要に応じて `backend/docs/BE-TASKS.md` など他のタスク管理ファイルも同様に整備する
>
> 【注意事項】
> - パイプテーブルの列数を5列（タスクNO, タスクタイトル, 起票日付, 完了日付, タスク種別）に統一する
> - テーブル行のテキスト内に pipe 文字が含まれる場合は、意味を損なわない範囲で表現を変更する
> - セクション区切り（`---`）の前後の空行は Markdown 見出し構造を維持するため適切に残す
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot007"></a>
## ユースケースNo | OT007

ユースケース
新規モジュール識別子 `PJ` の設立と `.clinerules`/AgentSkills ガバナンスの移行

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [OT007001](#ot007001) 新規モジュール識別子 `PJ` の設立と `.clinerules`/AgentSkills ガバナンスの移行 | 2026-09-09 | 2026-09-09 | 運用整備 |
| [OT007002](#ot007002) `OT007001` UAT 対応：`SY007` 残存タスクの `PJ` 番号振り直しと追加移行 | 2026-09-09 | 2026-09-09 | 運用整備 |
| [OT007003](#ot007003) `docs/SY-TASKS.md` の「識別子運用ルール」セクション削除と `.clinerules` 参照整理 | 2026-09-09 | 2026-09-09 | 運用整備 |
| [OT007004](#ot007004) 各 `<識別子>-TASKS.md` の「タスク粒度の方針」を自識別子のみの記述に統一する | 2026-09-09 | 2026-09-09 | 運用整備 |
| [OT007005](#ot007005) タスク管理ファイルフォーマット統一と整合性全チェック | 2026-09-09 | 2026-09-09 | ドキュメント整理 |
| [OT007006](#ot007006) `localapp/docs/LA-TASKS.md` レイアウト改善（見出しアンカー・ブロッククォート・4列テーブル化・ユースケース一覧） | 2026-09-09 | 2026-09-10 | 文書整備 |
| [OT007007](#ot007007) `OT007006` UATバグ対応：ページ内リンクを Markdown 構文から HTML アンカーに修正 | 2026-09-10 | 2026-09-10 | 不具合修正 |
| [OT007008](#ot007008) `OT007005` UATバグ対応：LA-TASKS.md のコンフリクトマーカー解消 | 2026-09-10 | 2026-09-10 | 不具合修正 |
| [OT007009](#ot007009) タスク管理ファイルのテンプレート作成 | 2026-09-10 | 2026-09-10 | ドキュメント整備 |

<a id="ot007001"></a>
### OT007001 新規モジュール識別子 `PJ` の設立と `.clinerules`/AgentSkills ガバナンスの移行

<div align="right"><a href="#ot007">タスク一覧へ↩︎</a></div>

> 【計画】
> - `.clinerules` に `PJ` 識別子を追加し、`.clinerules`/AgentSkills/JIRA/Confluence/Slack 等のツール連携を `PJ` の対象とする
> - `.clinerules` の識別子選択基準と具体例を `PJ` 対応に更新する
> - `docs/PJ-TASKS.md` を新規作成し、`.clinerules`/AgentSkills ガバナンスのユースケース `PJ001` とツール連携のプレースホルダー `PJ002`–`PJ004` を定義する
> - `docs/SY-TASKS.md` から `.clinerules`/AgentSkills 関連タスク `SY007001` / `SY007003` / `SY007011` / `SY007012` / `SY007013` を削除し、移行先を記録する
> - `docs/PJ-TASKS.md` に移行元タスク `SY007001`–`SY007013`（該当 5 件）を `PJ001001`–`PJ001005` として連番で再記録する
> - `docs/PJ-WORK-LOG.md` / `docs/PJ-CAVEATS.md` を新規作成する
> - `docs/PJ-AGENT-SKILLS-GUIDE.md` の識別子一覧に `PJ` を追加する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot007002"></a>
### OT007002 `OT007001` UAT 対応：`SY007` 残存タスクの `PJ` 番号振り直しと追加移行

<div align="right"><a href="#ot007">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/SY-TASKS.md` に残存していた `SY007002` / `SY007004` / `SY007005` / `SY007006` / `SY007007` / `SY007008` / `SY007009` / `SY007010` の 8 タスクを `docs/PJ-TASKS.md` に追加移行する
> - `docs/PJ-TASKS.md` の既存 `PJ001002`–`PJ001005` を `PJ001003` / `PJ001011`–`PJ001013` に番号振り直しする
> - `docs/SY-TASKS.md` の `SY007` 移行履歴を 13 件分に更新する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot007003"></a>
### OT007003 `docs/SY-TASKS.md` の「識別子運用ルール」セクション削除と `.clinerules` 参照整理

<div align="right"><a href="#ot007">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/SY-TASKS.md` の「識別子運用ルール」セクションを削除し、`.clinerules` の **Task Identifier Rules** を正とする
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot007004"></a>
### OT007004 各 `<識別子>-TASKS.md` の「タスク粒度の方針」を自識別子のみの記述に統一する

<div align="right"><a href="#ot007">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/SY-TASKS.md` / `docs/OT-TASKS.md` / `frontend/docs/FE-TASKS.md` / `localapp/docs/LA-TASKS.md` / `backend/docs/BE-TASKS.md` / `ocr-worker/docs/OW-TASKS.md` の「タスク粒度の方針」の識別子説明を自識別子のみに統一する
> - 例の数を各ファイル 1 つに統一する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot007005"></a>
### OT007005 タスク管理ファイルフォーマット統一と整合性全チェック

<div align="right"><a href="#ot007">タスク一覧へ↩︎</a></div>

> 【計画】
> - `ocr-worker/docs/OW-TASKS.md` のヘッダー番号ミスを修正する
> - `localapp/docs/LA-TASKS.md` のテーブルフォーマットを他の `*-TASKS.md` と統一する
> - すべての `*-TASKS.md` で linter を実行し、37 ファイル ALL PASS を確認する
>
> 【実施結果】
> - 2026-09-09: `ocr-worker/docs/OW-TASKS.md` のヘッダー番号ミスを 3 件修正（005→004、009→005、003-FUTURE→003）
> - 2026-09-09: `localapp/docs/LA-TASKS.md` のテーブル外 `### LAxxx` セクション（48 個）をテーブル内に統合し、他の `*-TASKS.md` とフォーマットを統一
> - 2026-09-09: `python scripts/lint-task-md.py` で全 37 ファイルを検証し ALL PASS を確認した
>
<a id="ot007006"></a>
### OT007006 `localapp/docs/LA-TASKS.md` レイアウト改善（見出しアンカー・ブロッククォート・4列テーブル化・ユースケース一覧）

<div align="right"><a href="#ot007">タスク一覧へ↩︎</a></div>

> 【計画】
> - `localapp/docs/LA-TASKS.md` にユースケース見出し・タスク見出しの `<a id="...">` アンカーを挿入する
> - 各ユースケースのタスク一覧テーブルを4列化し、タスク行内にアンカーリンクを配置する
> - 「ユースケース一覧」テーブルをファイル先頭に追加し、アンカーリンクを設置する
> - `python scripts/lint-task-md.py` でパイプテーブル整合性を検証する
> - 2026-09-10: 「ユースケース一覧」テーブルをファイル先頭に追加し、アンカーリンクを設置した
> - 2026-09-10: 各ユースケースセクションに「ユースケース一覧へ↩︎」、各タスクセクションに「タスク一覧へ↩︎」のページ内リンクを追加した
> - 2026-09-10: LA002012→LA002011、LA002013→LA002012 のリナンバリングを `LA-TASKS.md` / `LA-WORK-LOG.md` / `LA-CAVEATS.md` に反映した
> - 2026-09-10: `python scripts/lint-task-md.py` で全 37 ファイルを検証し ALL PASS を確認した
> - 2026-09-10: `npm run build`（frontend）および `cargo check`（Rust）はエラー 0 件で PASS した
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot007007"></a>
### OT007007 `OT007006` UATバグ対応：ページ内リンクを Markdown 構文から HTML アンカーに修正

<div align="right"><a href="#ot007">タスク一覧へ↩︎</a></div>

> 【計画】
> - `localapp/docs/LA-TASKS.md` の「ユースケース一覧へ↩︎」「タスク一覧へ↩︎」戻りリンクを Markdown `[text](#anchor)` 構文から生の HTML `<a href="#anchor">text</a>` に変更する
> - HTML ブロック（`<div align="right">`）内では Markdown リンクがレンダラによって解析されないため、生の HTML アンカーに置き換える
> - `python scripts/lint-task-md.py` でパイプテーブル整合性を検証する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot007008"></a>
### OT007008 `OT007005` UATバグ対応：LA-TASKS.md のコンフリクトマーカー解消

<div align="right"><a href="#ot007">タスク一覧へ↩︎</a></div>

> 【計画】
> - `localapp/docs/LA-TASKS.md` に残存していた `feature/OT007005-task-md-format-unify` マージ時のコンフリクトマーカー（`<<<<<<< HEAD` / `=======` / `>>>>>>>`）を解消する
> - main 側（HTML アンカー・4列テーブル・ブロッククォート形式）を採用し、feature 側の旧形式を破棄する
> - `python scripts/lint-task-md.py` でパイプテーブル整合性を検証する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot007009"></a>
### OT007009 タスク管理ファイルのテンプレート作成

<div align="right"><a href="#ot007">タスク一覧へ↩︎</a></div>

> 【計画】
> - `localapp/docs/LA-TASKS.md` の構造を元に、`*.clinerules/skills/task-manager/references/TEMPLATE-TASKS.md` を新規作成する
> - 具体的なタスク内容は含めず、プレースホルダーのみとする
> - `python scripts/lint-task-md.py` でパイプテーブル整合性を検証する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot008"></a>
## ユースケースNo | OT008

ユースケース
タスク管理ファイルフォーマット統一と整合性全チェック

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [OT008001](#ot008001) タスク管理ファイルフォーマット統一と整合性全チェック | 2026-09-09 | 2026-09-09 | ドキュメント整理 |
| [OT008002](#ot008002) `SY-TASKS.md` から `SY007` を削除し、`SY007005`/`SY007006` を `PJ-TASKS.md` に統合移行 | 2026-09-10 | 2026-09-10 | 運用整備 |

<a id="ot008001"></a>
### OT008001 タスク管理ファイルフォーマット統一と整合性全チェック

<div align="right"><a href="#ot008">タスク一覧へ↩︎</a></div>

> 【計画】
> - `ocr-worker/docs/OW-TASKS.md` のヘッダー番号ミスを修正する
>   - `## ユースケースNo / 005` → `## ユースケースNo / 004`（OW004001 が入っているため）
>   - 1 つ目の `## ユースケースNo / 009` → `## ユースケースNo / 005`（OW005001 が入っているため）
>   - `## ユースケースNo / 003-FUTURE` → `## ユースケースNo / 003`（形式統一）
> - `localapp/docs/LA-TASKS.md` のテーブルフォーマットを他の `*-TASKS.md` と統一する
>   - 箇条書きをテーブル行として統合する
> - すべての `*-TASKS.md` で linter を実行し、37 ファイル ALL PASS を確認する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot008003"></a>
### OT008003 `backend/docs/BE-TASKS.md` のテンプレート形式移行

<div align="right"><a href="#ot008">タスク一覧へ↩︎</a></div>

> 【計画】
> - `backend/docs/BE-TASKS.md` を `TEMPLATE-TASKS.md` 構造に移行する
> - タイトルを 「# backend タスク管理表」に変更する
> - `## ユースケース一覧` セクションを追加する
> - 各ユースケースに HTML アンカー・戻りリンクを追加する
> - タスクサマリーテーブルを4列形式に変更する
> - タスク詳細を独立セクションに移行する
> - `BE003` の分割を統合する
> - `python scripts/lint-task-md.py` で ALL PASS を確認する
>
> 【実施結果】
> - 2026-09-10: `backend/docs/BE-TASKS.md` のタイトルを 「# backend タスク管理表」に変更した
> - 2026-09-10: `## ユースケース一覧` セクションを追加し、BE001〜BE008 をリンク化した
> - 2026-09-10: 各ユースケースに HTML アンカー `<a id="be00x">` を追加した
> - 2026-09-10: 各ユースケースに `ユースケース一覧へ↩︎` 戻りリンクを追加した
> - 2026-09-10: タスクサマリーテーブルを4列形式（タスク/起票日付/完了日付/種別）に変更した
> - 2026-09-10: タスク詳細を独立セクション `### BE00x00x タスクタイトル` に移行した
> - 2026-09-10: `BE003` / `BE003 続き` を統合した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した - 2026-09-09: `ocr-worker/docs/OW-TASKS.md` のヘッダー番号ミスを 3 件修正（005→004、009→005、003-FUTURE→003）
> - 2026-09-09: `localapp/docs/LA-TASKS.md` のテーブル外 `### LAxxx` セクション（48 個）をテーブル内に統合し、他の `*-TASKS.md` とフォーマットを統一（1782 行→1383 行）
> - 2026-09-09: linter でプロジェクト内 37 Markdown ファイルを全チェックし、ALL PASS を確認
> - 2026-09-09: `ocr-worker/docs/OW-TASKS.md` の重複していた `## ユースケースNo / 003` 見出しを 1 つに統合し、OW003008 を同一テーブルに移動。テーブル間の空行を削除して 003 内のタスク（OW003001〜OW003008）を連続したテーブル行として再構成
> - 2026-09-09: `docs/SY-TASKS.md` の末尾移行履歴セクション（SY007001〜SY007013 の PJ 移行記録）を削除
> - 2026-09-09: `localapp/docs/LA-TASKS.md` の LA002008-1/2/3 を LA002008 に統合（完了日を 2026-08-20 に更新し、詳細欄に各派生修正の実施日・内容・種別を追記）
>
<a id="ot008002"></a>
### OT008002 `SY-TASKS.md` から `SY007` を削除し、`SY007005`/`SY007006` を `PJ-TASKS.md` に統合移行

<div align="right"><a href="#ot008">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/SY-TASKS.md` から `SY007` ユースケースを削除する
> - `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` の `PJ001` に `PJ001017` として追加する
> - `python scripts/lint-task-md.py` でパイプテーブル整合性を検証する
>
> 【実施結果】
> - 2026-09-10: `docs/SY-TASKS.md` から `SY007` ユースケースを削除した
> - 2026-09-10: `SY007005` と `SY007006` を統合し、`docs/PJ-TASKS.md` に `PJ001017` として追加した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot008003"></a>
### OT008003 `backend/docs/BE-TASKS.md` のテンプレート形式移行

<div align="right"><a href="#ot008">タスク一覧へ↩︎</a></div>

> 【計画】
> - `backend/docs/BE-TASKS.md` を `TEMPLATE-TASKS.md` 構造に移行する
> - タイトルを 「# backend タスク管理表」に変更する
> - `## ユースケース一覧` セクションを追加する
> - 各ユースケースに HTML アンカー・戻りリンクを追加する
> - タスクサマリーテーブルを4列形式に変更する
> - タスク詳細を独立セクションに移行する
> - `BE003` の分割を統合する
> - `python scripts/lint-task-md.py` で ALL PASS を確認する
>
> 【実施結果】
> - 2026-09-10: `backend/docs/BE-TASKS.md` のタイトルを 「# backend タスク管理表」に変更した
> - 2026-09-10: `## ユースケース一覧` セクションを追加し、BE001〜BE008 をリンク化した
> - 2026-09-10: 各ユースケースに HTML アンカー `<a id="be00x">` を追加した
> - 2026-09-10: 各ユースケースに `ユースケース一覧へ↩︎` 戻りリンクを追加した
> - 2026-09-10: タスクサマリーテーブルを4列形式（タスク/起票日付/完了日付/種別）に変更した
> - 2026-09-10: タスク詳細を独立セクション `### BE00x00x タスクタイトル` に移行した
> - 2026-09-10: `BE003` / `BE003 続き` を統合した
> - 2026-09-10: `python scripts/lint-task-md.py` で 37 ファイル ALL PASS を確認した
>
<a id="ot009"></a>
## ユースケースNo | OT009

ユースケース
ドキュメント最終更新日メタデータ標準化と運用ルール整備

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [OT009001](#ot009001) すべてのドキュメントに「最終更新」メタデータを追加し、更新時の運用ルールを `.clinerules` と AgentSkills に定める | 2026-09-13 | 2026-09-13 | 運用整備 |

<a id="ot009001"></a>
### OT009001 すべてのドキュメントに「最終更新」メタデータを追加し、更新時の運用ルールを `.clinerules` と AgentSkills に定める

<div align="right"><a href="#ot009">タスク一覧へ↩︎</a></div>

> 【計画】
> - プロジェクト内すべての Markdown ドキュメント（`docs/` 配下、各モジュール `*/docs/` 配下）に「最終更新: yyyy/mm/dd」メタデータを追加する
> - `memo/` 配下も同様に「最終更新」メタデータを追加する（git 対象外のまま）
> - `.clinerules` に「ドキュメントを更新する際は、当該ファイルの最終更新日を必ず更新すること」を追加する
> - 必要に応じて `file-modifier` などの AgentSkills に「最終更新日更新」の手順ガイドラインを追加する
> - テンプレートファイル（`TEMPLATE-TASKS.md` など）にも「最終更新」セクションを追加し、新規文書作成時に確実に設置されるようにする
> - `python scripts/lint-task-md.py` でパイプテーブル整合性を検証する
>
> 【実施結果】
> - 2026-09-13: プロジェクト内54ファイルの Markdown ドキュメントに「最終更新: 2026/09/13」メタデータを追加した
> - 2026-09-13: `docs/` 配下、`backend/docs/`、`frontend/docs/`、`localapp/docs/`、`ocr-worker/docs/` 配下の全ファイルを対象とした
> - 2026-09-13: `memo/` 配下（git 対象外）の全 Markdown ファイルにも同様に「最終更新」メタデータを追加した
> - 2026-09-13: `.clinerules` に「Document Last-Updated Metadata Rule」セクションを追加し、日付形式・追加対象・更新ルールを定めた
> - 2026-09-13: `.cline/skills/task-manager/references/TEMPLATE-TASKS.md` に「最終更新: yyyy/mm/dd」プレースホルダーを追加した
> - 2026-09-13: `python scripts/lint-task-md.py` でパイプテーブル整合性を検証し、OT-TASKS.md は ALL PASS を確認した
> - 2026-09-13: 全ドキュメントのヘッダー構成を `docs/README.md` と統一した。タイトル → 説明文 → `> 最終更新:` メタデータ → `---` セパレータ の構成とし、config-reference.md・CHANGELOG-20250815.md（reference/localapp/docs/）も含めた 40 ファイルを一括修正した
> - 2026-09-13: `.clinerules` のタスク完了確定フローを強化（承認→日付記入→git作業→最終報告の厳密なステップ化）。`task-manager/SKILL.md`・`branch-manager/SKILL.md` も新フローに整合して更新した
>
<a id="ot010"></a>
## ユースケースNo | OT010

ユースケース
docs/ 配下の図を Mermaid 化する

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [OT010001](#ot010001) `docs/SY-WEB-OCR-SYSTEM-PLAN.md` の全体アーキテクチャ図を Mermaid 化する | 2026-09-14 | 2026-09-14 | ドキュメント |
| [OT010002](#ot010002) `docs/README.md` のインデックスが各 docs 配下のドキュメントを網羅しているか確認と修正 | 2026-09-14 | 2026-09-14 | ドキュメント |

<a id="ot010001"></a>
### OT010001 `docs/SY-WEB-OCR-SYSTEM-PLAN.md` の全体アーキテクチャ図を Mermaid 化する

<div align="right"><a href="#ot010">タスク一覧へ↩︎</a></div>

> 【計画】
> - プロジェクト内の `docs/` 配下（backend/docs/、frontend/docs/、localapp/docs/、ocr-worker/docs/、docs/）の Markdown ファイルを精査し、Mermaid 化されていない図を特定する
> - `docs/SY-WEB-OCR-SYSTEM-PLAN.md` の `## 3. 全体アーキテクチャ` にある ASCII アート図を Mermaid `flowchart TD` に変換する
> - `.clinerules` の Mermaid ルールに従い、波括弧 `{}`・角括弧 `[]` を含むラベルはダブルクォートで囲む
> - `python scripts/lint-task-md.py` でパイプテーブル整合性を検証する
>
> 【実施結果】
> - 2026-09-14: backend/docs/、frontend/docs/、localapp/docs/、ocr-worker/docs/、docs/ の Markdown ファイルを精査し、未 Mermaid 化の図が `docs/SY-WEB-OCR-SYSTEM-PLAN.md` の 1 箇所のみであることを確認
> - 2026-09-14: `docs/SY-WEB-OCR-SYSTEM-PLAN.md` の `## 3. 全体アーキテクチャ` にある ASCII アート図を Mermaid `flowchart TD` に変換
> - 2026-09-14: §10・§11 のすべてのファイル・フォルダに trailing comment を追加し、`.cline/skills/` 以下の実ファイル構成を反映
> - 2026-09-14: `docs/OT-WORK-LOG.md` にコメント追記作業のログを追加
> - 2026-09-14: `python scripts/lint-task-md.py` で `docs/OT-TASKS.md` / `docs/OT-WORK-LOG.md` / `docs/SY-WEB-OCR-SYSTEM-PLAN.md` のパイプテーブル整合性を確認（memo/ 配下の既存 2 ファイルを除き ALL PASS）

<a id="ot010002"></a>
### OT010002 `docs/README.md` のインデックスが各 docs 配下のドキュメントを網羅しているか確認と修正

<div align="right"><a href="#ot010">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/` 配下、各モジュール `docs/` 配下の `.md` ファイルを一覧取得し、`docs/README.md` と比較する
> - `docs/README.md` に不足しているドキュメントを追加する
> - `docs/README.md` から重複エントリを削除する
> - `docs/README.md` の最終更新日を更新する
> - `python scripts/lint-task-md.py` でパイプテーブル整合性を検証する
>
> 【実施結果】
> - 2026-09-14: `docs/` 配下・各モジュール `docs/` 配下の `.md` ファイルを一覧取得し、`docs/README.md` と比較
> - 2026-09-14: `docs/README.md` に不足していた `SY-CONTAINER-3LAYER-ARCHITECTURE.md`、`SY-CONTAINER-PROGRESS-API-DESIGN.md`、`SY-SSE-PROGRESS-DELIVERY-GUIDE.md`、`SY-STORAGE-MIGRATION-GUIDE.md`、`SY-BOOK2PDF_AGENT_SKILLS_MANUAL.md`、`backend/docs/BE007001-report.md` を追加
> - 2026-09-14: `docs/README.md` から `SY-CAVEATS.md` の重複エントリを削除
> - 2026-09-14: `docs/README.md` の最終更新日を `2026/09/14` に更新
> - 2026-09-14: `feature/SY002002-get-job-progress-integration` ブランチから `docs/SY-CONTAINER-3LAYER-ARCHITECTURE.md` と `docs/SY-STORAGE-MIGRATION-GUIDE.md` を復元・追加
> - 2026-09-14: Cline checkpoint から `docs/SY-SSE-PROGRESS-DELIVERY-GUIDE.md` を復元・追加
> - 2026-09-14: `python scripts/lint-task-md.py` で `docs/OT-TASKS.md` / `docs/README.md` のパイプテーブル整合性を確認（ALL PASS）
>

<a id="ot011"></a>
## ユースケースNo | OT011

ユースケース
`frontend` タスク管理表から不要なユースケースを削除する

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [OT011001](#ot011001) `frontend/docs/FE-TASKS.md` から FE004 ユースケースを削除する | 2026-09-20 | 2026-09-20 | ドキュメント整理 |

<a id="ot011001"></a>
### OT011001 `frontend/docs/FE-TASKS.md` から FE004 ユースケースを削除する

<div align="right"><a href="#ot011">タスク一覧へ↩︎</a></div>

> 【計画】
> - `frontend/docs/FE-TASKS.md` から不要なユースケース FE004 とタスク FE004001 を削除する
> - 削除対象:
>   - ユースケース一覧テーブルの FE004 行
>   - FE004 ユースケースセクション（タスクテーブルと FE004001 詳細）
> - `python scripts/lint-task-md.py` でパイプテーブル整合性を検証する
>
> 【実施結果】
> - 2026-09-20: `frontend/docs/FE-TASKS.md` からユースケース一覧テーブルの FE004 行を削除
> - 2026-09-20: `frontend/docs/FE-TASKS.md` から FE004 ユースケースセクション（FE004001 詳細を含む）を削除
> - 2026-09-20: `python scripts/lint-task-md.py` で `docs/OT-TASKS.md` / `frontend/docs/FE-TASKS.md` のパイプテーブル整合性を確認（ALL PASS）
> - 2026-09-20: `memo/` 配下の lint 不整合はユーザーから「私的なメモのため触らないで」と指示があり、対象外とした
>

