# System タスク管理表

本ファイルは、System のタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する
- タスク No は「モジュール識別子（2文字）＋ ユースケースNo（3桁）＋ 通番（3桁）」とする
  - 識別子: `SY`=System/全体設計・仕様・横断基盤
  - 例：ユースケース001の1番目のタスク → `SY001001`
- 通番は各ユースケース内で 001 から連番で振る

## ユースケース一覧

| ユースケースNo | タイトル |
|---|---|
| [SY001](#sy001) | プロジェクト全体のドキュメント整備と横断基盤の確立 |
| [SY002](#sy002) | 進捗通知方式の全体仕様策定 |

---

<a id="sy001"></a>
## ユースケースNo | SY001

ユースケース
プロジェクト全体のドキュメント整備と横断基盤の確立

プロジェクト全体の構成、技術選定、コーディング規約などの横断的な文書と基盤を整備する。

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [SY001001](#sy001001) 全体計画書・設計決定事項・コーディング規約の整備 | 2026-08-11 | 2026-08-11 | 設計 |

<a id="sy001001"></a>
### SY001001 全体計画書・設計決定事項・コーディング規約の整備

<div align="right"><a href="#sy001">タスク一覧へ↩︎</a></div>

> 【計画】
> - プロジェクト全体の構成を `docs/SY-WEB-OCR-SYSTEM-PLAN.md` にまとめる
> - 技術選定の理由を `docs/SY-DESIGN-DECISIONS.md` にまとめる
> - Python / TypeScript / Rust のコーディング規約を `docs/OT-CODING-CONVENTIONS.md` にまとめる
>
> 【実施結果】
> - 2026-08-11: `docs/SY-WEB-OCR-SYSTEM-PLAN.md` を新規作成し、システム全体構成・アーキテクチャ・処理フローを記載した
> - 2026-08-11: `docs/SY-DESIGN-DECISIONS.md` を新規作成し、技術選定と将来の課題を記載した
> - 2026-08-11: `docs/OT-CODING-CONVENTIONS.md` を新規作成し、各言語のコーディング規約を定めた
>

---

<a id="sy002"></a>
## ユースケースNo | SY002

ユースケース
コンテナ間進捗通知のREST API連携方式仕様策定

OCR 処理などの長時間処理に対する進捗通知方式の全体仕様を策定し、コンテナ間の連携を REST API に統一する。

<div align="right"><a href="#ユースケース一覧">ユースケース一覧へ↩︎</a></div>

| タスク | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|
| [SY002001](#sy002001) 進捗通知のポーリング方式全体仕様策定 | 2026-09-03 |  | 仕様 |
| [SY002002](#sy002002) コンテナ間進捗通知のREST API連携方式実装 | 2026-09-12 |  | 横断実装 |

<a id="sy002001"></a>
### SY002001 進捗通知のポーリング方式全体仕様策定

<div align="right"><a href="#sy002">タスク一覧へ↩︎</a></div>

> 【計画】
> - `docs/progress-notification-polling-design.md` と `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` を統合し、SSE / HTTP ポーリングの全体仕様を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に整理する
> - 進捗ペイロード `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止する
> - ポーリングプロトコルを文書化する（1 リクエストあたり 10 秒タイムアウト、1 秒 / 2 秒 / 4 秒の指数関数的バックオフ、最大 3 回リトライ）
>
> 【実施結果】
> - 2026-09-03: `docs/progress-notification-polling-design.md` を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に統合し、前者を削除した
> - 2026-09-03: `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止した
> - 2026-09-03: ポーリングプロトコル（10 秒タイムアウト、1/2/4 秒バックオフ、最大 3 回リトライ）を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に文書化した
> - 2026-09-03: `docs/README.md` / `docs/SY-WEB-OCR-SYSTEM-PLAN.md` を更新した
>
> ---
>
> <a id="sy002002"></a>
> ### SY002002 コンテナ間進捗通知のREST API連携方式実装
>
> <div align="right"><a href="#sy002">タスク一覧へ↩︎</a></div>
>
> > 【計画】
> > #### 問題の整理
> >   - ocr-worker と backend が両方とも `/data/progress/{job_id}.json` に書き込んでおり、ファイル上書きによる競合が発生している
> >   - ocr-worker は `OCR 処理を開始します（1/3）`→`OCR 処理中です（2/3）` の per-page 進捗を書き込む
> >   - backend は「OCR 処理を開始しました」「OCR 処理が完了しました」「PDF を生成中です」のジョブフェーズ進捗を書き込む
> >   - 結果として、ocr-worker のメッセージが backend のメッセージで上書きされ、frontend で per-page 進捗が観測できない
> >   - ファイル共有はコンテナ間の疎結合に反し、将来的な別ホスト・別 Pod 移行を阻害する
> >
> > #### 解決方針（REST API 連携方式）
> >   - ocr-worker に `/progress/{job_id}` GET エンドポイントを追加し、per-page 進捗を内部辞書で管理する
> >   - backend の `_progress_event_generator` は `{job_id}.json`（ジョブフェーズ進捗）と ocr-worker の `/progress/{job_id}`（per-page 進捗）の両方を監視する
> >   - 両ソースをマージして SSE イベントを生成する
> >   - マージ戦略: ocr-worker の per-page 進捗（progress / current_page / message）を優先、status は backend のフェーズ値を優先
> >
> > #### 対象ファイル
> >   - `ocr-worker/ndlocr_cli_patches/progress_reporter.py`: ファイル書き込みを内部辞書更新に変更
> >   - `ocr-worker/app/main.py`: `/progress/{job_id}` GET エンドポイント追加
> >   - `backend/app/routers/jobs.py`: `_progress_event_generator` の ocr-worker HTTP API ポーリングロジック追加
> >   - `backend/app/services/ocr_engine.py`: ocr-worker ホスト設定確認・更新
> >   - `backend/tests/test_progress.py`: ocr-worker HTTP API 連携テスト
> >   - `frontend/src/hooks/__tests__/useOcrJob.test.ts`: 統合テストの更新
> >   - `docs/SY-PROGRESS-NOTIFICATION-SPEC.md`: 仕様文書の更新
> >
> > 【実施結果】
> >