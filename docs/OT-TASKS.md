# タスク管理

本ファイルは、`backend` / `frontend` / `ocr-worker` / `localapp` を横断するプロジェクト全体のタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する
- タスク No は「モジュール識別子（2文字）＋ ユースケースNo（3桁）＋ 通番（3桁）」とする
  - 識別子: `OT`=横断・その他
  - 例：ユースケース001の1番目のタスク → `OT001001`
- 通番は各ユースケース内で 001 から連番で振る

---

## ユースケースNo | OT001

ユースケース
プロジェクト全体のドキュメント整備

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OT001001 | 全体計画書・設計決定事項・コーディング規約の整備 | 2026-08-11 | 2026-08-11 | 設計 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | プロジェクト全体の構成を `docs/SY-WEB-OCR-SYSTEM-PLAN.md` にまとめる |  |  |  |
|  | 技術選定の理由を `docs/SY-DESIGN-DECISIONS.md` にまとめる |  |  |  |
|  | Python / TypeScript / Rust のコーディング規約を `docs/OT-CODING-CONVENTIONS.md` にまとめる |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: `docs/SY-WEB-OCR-SYSTEM-PLAN.md` を新規作成し、システム全体構成・アーキテクチャ・処理フローを記載した |  |  |  |
|  | 2026-08-11: `docs/SY-DESIGN-DECISIONS.md` を新規作成し、技術選定と将来の課題を記載した |  |  |  |
|  | 2026-08-11: `docs/OT-CODING-CONVENTIONS.md` を新規作成し、各言語のコーディング規約を定めた |  |  |  |
| OT001002 | 結合テスト手順書の作成 | 2026-08-12 | 2026-08-12 | ドキュメント |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `frontend` / `backend` / `ocr-worker` を横断した結合テスト手順を `./docs/OT-INTEGRATION-TEST-GUIDE.md` にまとめる |  |  |  |
|  | テスト準備、コンテナ起動、UI / cURL による手順、トラブルシューティング、終了処理を含める |  |  |  |
|  | `docs/SY-WEB-OCR-SYSTEM-PLAN.md` のフォルダ・ファイル構成と関連ドキュメントに `OT-INTEGRATION-TEST-GUIDE.md` へのリンクを追加する |  |  |  |
|  | `.clinerules` に `./docs/` 配下にも `OT-TASKS.md` / `OT-WORK-LOG.md` / `OT-CAVEATS.md` を配置するルールを明記する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: `./docs/OT-INTEGRATION-TEST-GUIDE.md` を新規作成し、Docker Compose 起動から PDF ダウンロードまでの手順を記載した |  |  |  |
|  | 2026-08-12: `docs/SY-WEB-OCR-SYSTEM-PLAN.md` の「フォルダ・ファイル構成」に `OT-INTEGRATION-TEST-GUIDE.md` を追加し、関連ドキュメントセクションへのリンクを含めた |  |  |  |
|  | 2026-08-12: トラブルシューティングとして backend 再ビルド、`GlobalHydra` エラー、CORS、PDF `ERR_ABORTED`、OCR タイムアウトについて記載した |  |  |  |
|  | 2026-08-12: `.clinerules` の「フォルダ・ドキュメント配置ルール」に `./docs/` 用の `OT-TASKS.md` / `OT-WORK-LOG.md` / `OT-CAVEATS.md` 配置ルールを追加した |  |  |  |
|  | 2026-08-12: `./docs/OT-TASKS.md` / `./docs/OT-WORK-LOG.md` / `./docs/OT-CAVEATS.md` を新規作成し、backend/docs/ に誤作成した横断タスク OT003001 を移行した |  |  |  |

---

## ユースケースNo | OT002

ユースケース
複数モジュールにまたがる注意事項の一元管理

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OT002001 | 全体横断の注意事項ファイルを作成する | 2026-08-12 | 2026-08-12 | ドキュメント |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `./docs/OT-CAVEATS.md` を新規作成し、複数モジュールにまたがる注意事項を集約する |  |  |  |
|  | 各モジュール固有の注意事項は `<module>/docs/<モジュール識別子>-CAVEATS.md` に残し、ここでは全体横断の視点だけを記載する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: `./docs/OT-CAVEATS.md` を新規作成し、Docker Compose 上での結合テストに関する全体横断の注意事項を記載した |  |  |  |
|  | 2026-08-12: 各モジュール固有の注意事項については `backend/docs/BE-CAVEATS.md` / `ocr-worker/docs/OW-CAVEATS.md` へのリンクを設置した |  |  |  |
| OT002002 | `OT-CAVEATS.md` の分離設計と移行計画策定 | 2026-09-06 | 2026-09-06 | ドキュメント設計 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `docs/OT-CAVEATS.md` の内容を、モジュール固有の注意事項と横断的な注意事項に分類する |  |  |  |
|  | 各モジュール固有の注意事項の移行先（`backend/docs/BE-CAVEATS.md` / `localapp/docs/LA-CAVEATS.md` / `ocr-worker/docs/OW-CAVEATS.md` / `frontend/docs/FE-CAVEATS.md`）を決定する |  |  |  |
|  | 横断的な注意事項を集約する `docs/SY-CAVEATS.md` の構成案を作成する |  |  |  |
|  | `docs/OT-TASKS.md` / `docs/OT-WORK-LOG.md` に本タスクを記録する |  |  |  |
|  | 実際の移行・削除は OT002003 として別タスクで実施する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-06: `docs/OT-CAVEATS.md` の内容を分類し、モジュール固有の項目と横断的な項目に分離した |  |  |  |
|  | 2026-09-06: 各モジュールの `*-CAVEATS.md` への移行先と `docs/SY-CAVEATS.md` の構成を決定した |  |  |  |
|  | 2026-09-06: `docs/OT-TASKS.md` / `docs/OT-WORK-LOG.md` に OT002002 として記録した |  |  |  |
|  | 2026-09-06: `docs/README.md` の dead link を `SY-CAVEATS.md` に修正した |  |  |  |
| OT002003 | `docs/OT-CAVEATS.md` の内容を各モジュールの `*-CAVEATS.md` に再配布し、OT-CAVEATS.md を削除する | 2026-09-06 | 2026-09-06 | ドキュメント整理 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `docs/OT-CAVEATS.md` に記載されているモジュール固有の注意事項を `backend/docs/BE-CAVEATS.md` / `localapp/docs/LA-CAVEATS.md` / `ocr-worker/docs/OW-CAVEATS.md` に移動する |  |  |  |
|  | `frontend/docs/FE-CAVEATS.md` で既にカバーされている項目は `docs/OT-CAVEATS.md` から削除するのみとする |  |  |  |
|  | 横断的な参照だけを `docs/SY-CAVEATS.md` に集約し、新規作成する |  |  |  |
|  | 再配布完了後、`docs/OT-CAVEATS.md` を削除する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-06: `backend/docs/BE-CAVEATS.md` に OCR タイムアウト設定、性能テストの `LOG_LEVEL=DEBUG` 前提、進捗通知の `JobResponse` 拡張と将来の `/progress` エンドポイント方針を追加した |  |  |  |
|  | 2026-09-06: `localapp/docs/LA-CAVEATS.md` に HTTP ポーリング優先、1 秒間隔 / 10 秒タイムアウト、指数関数的バックオフリトライ、リトライ前の進捗メッセージを追加した |  |  |  |
|  | 2026-09-06: `ocr-worker/docs/OW-CAVEATS.md` に OCR 呼び出し側の `--max-time 600` タイムアウト設定を追加した |  |  |  |
|  | 2026-09-06: `docs/SY-CAVEATS.md` を新規作成し、`docs/SY-PROGRESS-NOTIFICATION-SPEC.md` への横断的な参照を集約した |  |  |  |
|  | 2026-09-06: `docs/OT-CAVEATS.md` を削除した |  |  |  |

---

## ユースケースNo | OT003

ユースケース
進捗通知方式の整備と localapp ポーリングの改善

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OT003001 | 進捗通知のポーリング方式仕様策定と localapp リトライ実装 | 2026-09-03 | 2026-09-03 | 設計 / 実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `docs/progress-notification-polling-design.md` と `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` を統合し、SSE / HTTP ポーリングの全体仕様を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に整理する |  |  |  |
|  | 進捗ペイロード `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止する |  |  |  |
|  | ポーリングプロトコルを文書化する（1 リクエストあたり 10 秒タイムアウト、1 秒 / 2 秒 / 4 秒の指数関数的バックオフ、最大 3 回リトライ） |  |  |  |
|  | `localapp/src-tauri/src/commands/backend_api/backend_api_impl.rs` の `GET /api/jobs/{job_id}` ポーリング処理に、per-request タイムアウトと指数関数的バックオフによるリトライを実装する |  |  |  |
|  | リトライ前に「ジョブ状態の取得を再試行します」という進捗メッセージを UI に通知し、ユーザーに一過性の通信エラーであることを伝える |  |  |  |
|  | `docs/OT-TASKS.md` / `docs/OT-WORK-LOG.md` / `docs/OT-CAVEATS.md` / `docs/SY-WEB-OCR-SYSTEM-PLAN.md` / `docs/README.md` を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-03: `docs/progress-notification-polling-design.md` を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に統合し、前者を削除した |  |  |  |
|  | 2026-09-03: `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止した |  |  |  |
|  | 2026-09-03: ポーリングプロトコル（10 秒タイムアウト、1/2/4 秒バックオフ、最大 3 回リトライ）を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に文書化した |  |  |  |
|  | 2026-09-03: `localapp/src-tauri/src/commands/backend_api/backend_api_impl.rs` に `poll_job_status` ヘルパーを追加し、per-request タイムアウトと指数関数的バックオフによるリトライを実装した |  |  |  |
|  | 2026-09-03: `docs/README.md` / `docs/SY-WEB-OCR-SYSTEM-PLAN.md` / `docs/OT-CAVEATS.md` / `docs/OT-TASKS.md` / `docs/OT-WORK-LOG.md` を更新した |  |  |  |
|  | 2026-09-03: `cargo check --tests` と `cargo test backend_api_impl -- --nocapture` にてコンパイル・テストを確認した |  |  |  |
|  | 2026-09-03: localapp OCR タイムアウトの原因調査を実施し、タイムアウト値の管理方法（設定ファイル vs ハードコード vs 環境変数）を明確化した — 調査報告書 [localapp/docs/LA-TIMEOUT-INVESTIGATION-REPORT-OT003001.md](../localapp/docs/LA-TIMEOUT-INVESTIGATION-REPORT-OT003001.md) |  |  |  |
|  | 2026-09-03: `localapp/src-tauri/src/config.rs` に `http_client_timeout_sec` / `upload_timeout_sec` / `ocr_request_timeout_sec` / `poll_request_timeout_sec` を追加し、すべてのタイムアウト値を設定ファイルで一元管理できるようにした |  |  |  |
|  | 2026-09-03: `localapp/src-tauri/src/commands/backend_api.rs` と `backend_api_impl.rs` のハードコードされたタイムアウト値を、設定ファイルから読み込んだ値を参照するように変更した |  |  |  |
|  | 2026-09-03: 本タスク完了。タスク完了日付を 2026-09-03 に記入 |  |  |  |

---

## ユースケースNo | OT007

ユースケース
`OT` に誤分類された System / 全体設計タスクの切り出しと運用ルール整備

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OT007001 | `OT` に誤分類された System タスクを `SY` に分離し、運用ルールとスキルマトリックスを整備する | 2026-09-05 | 2026-09-05 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `docs/OT-TASKS.md` に本タスク（OT007001）を追記する |  |  |  |
|  | `docs/SY-TASKS.md` を新規作成し、元 `OT001001` / `OT003001` に含まれていた System / 全体設計・仕様策定部分を `SY` タスクとして移行記録する |  |  |  |
|  | `.clinerules` に `SY` / `OT` の使い分けルールと 3 層スキル選択マトリックスを追加する |  |  |  |
|  | `workflow-runner/SKILL.md` v2.0 を新規作成し、4 フェーズワークフローと選択的スキル読込を定義する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-05: `docs/OT-TASKS.md` に本タスク（OT007001）を追記した |  |  |  |
|  | 2026-09-05: `docs/SY-TASKS.md` を新規作成し、元 `OT001001` / `OT003001` の System / 全体設計・仕様策定部分を `SY` タスクとして分離記録した |  |  |  |
|  | 2026-09-05: `.clinerules` に `SY` / `OT` の使い分けルールと 3 層スキル選択マトリックスを追加した |  |  |  |
|  | 2026-09-05: `.cline/skills/workflow-runner/SKILL.md` を v2.0 に更新し、4 フェーズワークフローと選択的スキル読込を定義した |  |  |  |

---

## ユースケースNo | OT008

ユースケース
localapp 単体 OCR→PDF 技術調査・選定

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OT008001 | localapp 単体 OCR→PDF 技術調査・選定（LA008007 連携） | 2026-09-03 | 2026-09-04 | 調査 / 設計 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | localapp 単体で動作する OCR→PDF パイプラインの技術調査と選定を行う |  |  |  |
|  | 候補技術（Tesseract / `leptess` / `printpdf` 等）を調査し、PoC を実施する |  |  |  |
|  | 選定結果を `localapp/docs/LA-OCR-TECHNOLOGY-SURVEY-LA008007.md` にまとめる |  |  |  |
|  | LA008007 と連携し、localapp 側の調査結果を反映する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-04: LA008007 の技術調査・選定が完了した。`printpdf` 0.7.0（画像→A4 PDF 埋め込み）と `leptess` 0.14.0（Tesseract 5.x ラッパー）を採用した |  |  |  |
|  | 2026-09-04: 調査レポート `localapp/docs/LA-OCR-TECHNOLOGY-SURVEY-LA008007.md` を作成した |  |  |  |

---

## ユースケースNo | OT009

ユースケース
タスク管理ファイルのカラムずれ・空行整備

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OT009001 | タスク管理ファイルのカラムずれ・空行整備 | 2026-09-09 | 2026-09-09 | 文書整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `frontend/docs/FE-TASKS.md` のカラムずれを修正する |  |  |  |
|  | `frontend/docs/FE-TASKS.md` の余分な空行を削除する |  |  |  |
|  | `FE002001`・`FE002002` の【タスク完了日付】を削除し未完了状態に戻す（AI が誤って完了日付を記入したため） |  |  |  |
|  | 必要に応じて `backend/docs/BE-TASKS.md` など他のタスク管理ファイルも同様に整備する |  |  |  |
|  | 【注意事項】 |  |  |  |
|  | パイプテーブルの列数を5列（タスクNO, タスクタイトル, 起票日付, 完了日付, タスク種別）に統一する |  |  |  |
|  | テーブル行のテキスト内に pipe 文字が含まれる場合は、意味を損なわない範囲で表現を変更する |  |  |  |
|  | セクション区切り（`---`）の前後の空行は Markdown 見出し構造を維持するため適切に残す |  |  |  |
|  | タスク完了日付の削除理由を【実施結果】欄に明記する |  |  |  |
|  | `FE002002` の作業再開（ブランチ `feature/FE002002-fe002001-uat-bugfix` の実装作業）は本 OT タスクとは分けて実施する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-09: `frontend/docs/FE-TASKS.md` の行98-109（FE001002の実施結果）のカラムずれを修正（末尾の空セル4つを追加） |  |  |  |
|  | 2026-09-09: `FE002001` の【タスク完了日付】を削除し、訂正理由を【実施結果】欄に追記 |  |  |  |
|  | 2026-09-09: `FE002002` の【タスク完了日付】を削除し、訂正理由を【実施結果】欄に追記 |  |  |  |
|  | 2026-09-09: `feature/OT009001-fix-task-md-column-alignment` ブランチを `main` へ `--no-ff` マージ完了 |  |  |  |
---

## ユースケースNo | OT010

ユースケース
新規モジュール識別子 `PJ` の設立と `.clinerules`/AgentSkills ガバナンスの移行

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OT010001 | 新規モジュール識別子 `PJ` の設立と `.clinerules`/AgentSkills ガバナンスの移行 | 2026-09-09 | 2026-09-09 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `.clinerules` に `PJ` 識別子を追加し、`.clinerules`/AgentSkills/JIRA/Confluence/Slack 等のツール連携を `PJ` の対象とする |  |  |  |
|  | `.clinerules` の識別子選択基準と具体例を `PJ` 対応に更新する |  |  |  |
|  | `docs/PJ-TASKS.md` を新規作成し、`.clinerules`/AgentSkills ガバナンスのユースケース `PJ001` とツール連携のプレースホルダー `PJ002`–`PJ004` を定義する |  |  |  |
|  | `docs/SY-TASKS.md` から `.clinerules`/AgentSkills 関連タスク `SY007001` / `SY007003` / `SY007011` / `SY007012` / `SY007013` を削除し、移行先を記録する |  |  |  |
|  | `docs/PJ-TASKS.md` に移行元タスク `SY007001`–`SY007013`（該当 5 件）を `PJ001001`–`PJ001005` として連番で再記録する |  |  |  |
|  | `docs/PJ-WORK-LOG.md` / `docs/PJ-CAVEATS.md` を新規作成する |  |  |  |
|  | `docs/OT-AGENT-SKILLS-GUIDE.md` の識別子一覧に `PJ` を追加する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-09: `.clinerules` に `PJ` 識別子を追加し、識別子選択基準・具体例・スキルマトリックスを更新した |  |  |  |
|  | 2026-09-09: `docs/PJ-TASKS.md` を新規作成し、`PJ001`（`.clinerules`/AgentSkills ガバナンス）と `PJ002`–`PJ004`（JIRA/Confluence/Slack プレースホルダー）を定義した |  |  |  |
|  | 2026-09-09: `docs/PJ-WORK-LOG.md` / `docs/PJ-CAVEATS.md` を新規作成した |  |  |  |
|  | 2026-09-09: `docs/SY-TASKS.md` から `SY007001` / `SY007003` / `SY007011` / `SY007012` / `SY007013` を削除し、移行履歴セクションを追加した |  |  |  |
|  | 2026-09-09: `docs/PJ-TASKS.md` に `PJ001001`–`PJ001005` として移行元タスクを再記録した（後に `OT010002` にて `PJ001001`–`PJ001013` に番号振り直し） |  |  |  |
|  | 2026-09-09: `docs/OT-AGENT-SKILLS-GUIDE.md` の `task-manager` セクション識別子リストに `PJ` を追加した |  |  |  |
|  | 2026-09-09: `docs/OT-TASKS.md` に `OT010` ユースケースと `OT010001` タスクを追加した |  |  |  |
| OT010002 | `OT010001` UAT 対応：`SY007` 残存タスクの `PJ` 番号振り直しと追加移行 | 2026-09-09 | 2026-09-09 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `docs/SY-TASKS.md` に残存していた `SY007002` / `SY007004` / `SY007005` / `SY007006` / `SY007007` / `SY007008` / `SY007009` / `SY007010` の 8 タスクを `docs/PJ-TASKS.md` に追加移行する |  |  |  |
|  | `docs/PJ-TASKS.md` の既存 `PJ001002`–`PJ001005` を `PJ001003` / `PJ001011`–`PJ001013` に番号振り直しする |  |  |  |
|  | `docs/SY-TASKS.md` の `SY007` 移行履歴を 13 件分に更新する |  |  |  |
|  | `docs/OT-TASKS.md` の `OT010001` 【実施結果】欄の PJ 番号に番号振り直しの注記を追加する |  |  |  |
|  | `docs/PJ-WORK-LOG.md` に振り直し・追加移行の作業記録を追記する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-09: `docs/SY-TASKS.md` から `SY007002`–`SY007010` の 8 タスクを削除し、`docs/PJ-TASKS.md` に `PJ001002` / `PJ001004`–`PJ001010` として追加移行した |  |  |  |
|  | 2026-09-09: `docs/PJ-TASKS.md` の既存 `PJ001002`–`PJ001005` を `PJ001003` / `PJ001011`–`PJ001013` に番号振り直しした |  |  |  |
|  | 2026-09-09: `docs/SY-TASKS.md` の移行履歴テーブルを 13 件分に更新した |  |  |  |
|  | 2026-09-09: `docs/OT-TASKS.md` の `OT010001` 【実施結果】に番号振り直し注記を追加し、`OT010002` を起票した |  |  |  |
|  | 2026-09-09: `docs/PJ-WORK-LOG.md` に振り直し・追加移行の作業記録を追記した |  |  |  |
| OT010003 | `docs/SY-TASKS.md` の「識別子運用ルール」セクション削除と `.clinerules` 参照整理 | 2026-09-09 | 2026-09-09 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `docs/SY-TASKS.md` の「識別子運用ルール」セクションを削除し、`.clinerules` の **Task Identifier Rules** を正とする |  |  |  |
|  | `docs/PJ-TASKS.md` の `PJ001001` 【実施結果】欄を修正し、「識別子運用ルール明記」の記述を削除・整理する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-09: `docs/SY-TASKS.md` から「識別子運用ルール」セクションを削除した |  |  |  |
|  | 2026-09-09: `docs/PJ-TASKS.md` の `PJ001001` 【計画】・【実施結果】から「識別子運用ルール」の記述を削除し、タスク粒度の方針明記のみに整理した |  |  |  |
| OT010004 | 各 `<識別子>-TASKS.md` の「タスク粒度の方針」を自識別子のみの記述に統一する | 2026-09-09 | 2026-09-09 | 運用整備 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `docs/SY-TASKS.md` / `docs/OT-TASKS.md` / `frontend/docs/FE-TASKS.md` / `localapp/docs/LA-TASKS.md` / `backend/docs/BE-TASKS.md` / `ocr-worker/docs/OW-TASKS.md` の「タスク粒度の方針」の識別子説明を自識別子のみに統一する |  |  |  |
|  | 例の数を各ファイル 1 つに統一する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-09: 上記 6 ファイルの識別子説明を自識別子のみに統一し、例を 1 つに整理した |  |  |  |

