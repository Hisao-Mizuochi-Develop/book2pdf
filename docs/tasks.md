# タスク管理

本ファイルは、`backend` / `frontend` / `ocr-worker` / `localapp` を横断するプロジェクト全体のタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する
- タスク No は「ユースケースNo（3桁）＋ 通番（3桁）」とする
  - 例：ユースケース001の1番目のタスク → `001001`
  - 例：ユースケース002の1番目のタスク → `002001`
- 通番は各ユースケース内で 001 から連番で振る

---

## ユースケースNo | 001

ユースケース
プロジェクト全体のドキュメント整備

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 001001 | 全体計画書・設計決定事項・コーディング規約の整備 | 2026-08-11 | 2026-08-11 | 設計 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | プロジェクト全体の構成を `docs/web-ocr-system-plan.md` にまとめる |  |  |  |
|  | 技術選定の理由を `docs/design-decisions.md` にまとめる |  |  |  |
|  | Python / TypeScript / Rust のコーディング規約を `docs/coding-conventions.md` にまとめる |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: `docs/web-ocr-system-plan.md` を新規作成し、システム全体構成・アーキテクチャ・処理フローを記載した |  |  |  |
|  | 2026-08-11: `docs/design-decisions.md` を新規作成し、技術選定と将来の課題を記載した |  |  |  |
|  | 2026-08-11: `docs/coding-conventions.md` を新規作成し、各言語のコーディング規約を定めた |  |  |  |
| 001002 | 結合テスト手順書の作成 | 2026-08-12 | 2026-08-12 | ドキュメント |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `frontend` / `backend` / `ocr-worker` を横断した結合テスト手順を `./docs/integration-test-guide.md` にまとめる |  |  |  |
|  | テスト準備、コンテナ起動、UI / cURL による手順、トラブルシューティング、終了処理を含める |  |  |  |
|  | `docs/web-ocr-system-plan.md` のフォルダ・ファイル構成と関連ドキュメントに `integration-test-guide.md` へのリンクを追加する |  |  |  |
|  | `.clinerules` に `./docs/` 配下にも `tasks.md` / `work_log.md` / `caveats.md` を配置するルールを明記する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: `./docs/integration-test-guide.md` を新規作成し、Docker Compose 起動から PDF ダウンロードまでの手順を記載した |  |  |  |
|  | 2026-08-12: `docs/web-ocr-system-plan.md` の「フォルダ・ファイル構成」に `integration-test-guide.md` を追加し、関連ドキュメントセクションへのリンクを含めた |  |  |  |
|  | 2026-08-12: トラブルシューティングとして backend 再ビルド、`GlobalHydra` エラー、CORS、PDF `ERR_ABORTED`、OCR タイムアウトについて記載した |  |  |  |
|  | 2026-08-12: `.clinerules` の「フォルダ・ドキュメント配置ルール」に `./docs/` 用の `tasks.md` / `work_log.md` / `caveats.md` 配置ルールを追加した |  |  |  |
|  | 2026-08-12: `./docs/tasks.md` / `./docs/work_log.md` / `./docs/caveats.md` を新規作成し、backend/docs/ に誤作成した横断タスク 006001 を移行した |  |  |  |

---

## ユースケースNo | 002

ユースケース
複数モジュールにまたがる注意事項の一元管理

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 002001 | 全体横断の注意事項ファイルを作成する | 2026-08-12 | 2026-08-12 | ドキュメント |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `./docs/caveats.md` を新規作成し、複数モジュールにまたがる注意事項を集約する |  |  |  |
|  | 各モジュール固有の注意事項は `<module>/docs/caveats.md` に残し、ここでは全体横断の視点だけを記載する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: `./docs/caveats.md` を新規作成し、Docker Compose 上での結合テストに関する全体横断の注意事項を記載した |  |  |  |
|  | 2026-08-12: 各モジュール固有の注意事項については `backend/docs/caveats.md` / `ocr-worker/docs/caveats.md` へのリンクを設置した |  |  |  |

---

## ユースケースNo | 006

ユースケース
進捗通知方式の整備と localapp ポーリングの改善

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 006001 | 進捗通知のポーリング方式仕様策定と localapp リトライ実装 | 2026-09-03 | 2026-09-03 | 設計 / 実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `docs/progress-notification-polling-design.md` と `docs/progress-notification-spec.md` を統合し、SSE / HTTP ポーリングの全体仕様を `docs/progress-notification-spec.md` に整理する |  |  |  |
|  | 進捗ペイロード `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止する |  |  |  |
|  | ポーリングプロトコルを文書化する（1 リクエストあたり 10 秒タイムアウト、1 秒 / 2 秒 / 4 秒の指数関数的バックオフ、最大 3 回リトライ） |  |  |  |
|  | `localapp/src-tauri/src/commands/backend_api/backend_api_impl.rs` の `GET /api/jobs/{job_id}` ポーリング処理に、per-request タイムアウトと指数関数的バックオフによるリトライを実装する |  |  |  |
|  | リトライ前に「ジョブ状態の取得を再試行します」という進捗メッセージを UI に通知し、ユーザーに一過性の通信エラーであることを伝える |  |  |  |
|  | `docs/tasks.md` / `docs/work_log.md` / `docs/caveats.md` / `docs/web-ocr-system-plan.md` / `docs/README.md` を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-03: `docs/progress-notification-polling-design.md` を `docs/progress-notification-spec.md` に統合し、前者を削除した |  |  |  |
|  | 2026-09-03: `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止した |  |  |  |
|  | 2026-09-03: ポーリングプロトコル（10 秒タイムアウト、1/2/4 秒バックオフ、最大 3 回リトライ）を `docs/progress-notification-spec.md` に文書化した |  |  |  |
|  | 2026-09-03: `localapp/src-tauri/src/commands/backend_api/backend_api_impl.rs` に `poll_job_status` ヘルパーを追加し、per-request タイムアウトと指数関数的バックオフによるリトライを実装した |  |  |  |
|  | 2026-09-03: `docs/README.md` / `docs/web-ocr-system-plan.md` / `docs/caveats.md` / `docs/tasks.md` / `docs/work_log.md` を更新した |  |  |  |
|  | 2026-09-03: `cargo check --tests` と `cargo test backend_api_impl -- --nocapture` にてコンパイル・テストを確認した |  |  |  |
|  | 2026-09-03: localapp OCR タイムアウトの原因調査を実施し、タイムアウト値の管理方法（設定ファイル vs ハードコード vs 環境変数）を明確化した — 調査報告書 [localapp/docs/timeout-investigation-report-006001.md](../localapp/docs/timeout-investigation-report-006001.md) |  |  |  |
|  | 2026-09-03: `localapp/src-tauri/src/config.rs` に `http_client_timeout_sec` / `upload_timeout_sec` / `ocr_request_timeout_sec` / `poll_request_timeout_sec` を追加し、すべてのタイムアウト値を設定ファイルで一元管理できるようにした |  |  |  |
|  | 2026-09-03: `localapp/src-tauri/src/commands/backend_api.rs` と `backend_api_impl.rs` のハードコードされたタイムアウト値を、設定ファイルから読み込んだ値を参照するように変更した |  |  |  |
|  | 2026-09-03: 本タスク完了。タスク完了日付を 2026-09-03 に記入 |  |  |  |
