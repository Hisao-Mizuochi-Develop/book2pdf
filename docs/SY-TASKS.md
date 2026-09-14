# System タスク管理表

> 最終更新: 2026/09/15

本ファイルは、System のタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

> 最終更新: 2026/09/15

---

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
> - Python / TypeScript / Rust のコーディング規約を `docs/PJ-CODING-CONVENTIONS.md` にまとめる
>
> 【実施結果】
> - 2026-08-11: `docs/SY-WEB-OCR-SYSTEM-PLAN.md` を新規作成し、システム全体構成・アーキテクチャ・処理フローを記載した
> - 2026-08-11: `docs/SY-DESIGN-DECISIONS.md` を新規作成し、技術選定と将来の課題を記載した
> - 2026-08-11: `docs/PJ-CODING-CONVENTIONS.md` を新規作成し、各言語のコーディング規約を定めた
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
| [SY002001](#sy002001) 進捗通知のポーリング方式全体仕様策定 | 2026-09-03 | 2026-09-03 | 仕様 |
| [SY002002](#sy002002) コンテナ間進捗通知のREST API連携方式実装 | 2026-09-12 |  | 横断実装 |
| [SY002003](#sy002003) SY002002 UATバグ対応 | 2026-09-15 |  | 横断実装 |

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
> - 2026-09-13: `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` を全面再構成。backend SSE 詳細設計・frontend REST ポーリング方式・システムアーキテクチャを Mermaid 図を活用して詳細化
> - 2026-09-13: `docs/SY-CONTAINER-PROGRESS-API-DESIGN.md` を REST API 実装レベル仕様書として再構成。エンドポイント定義・スキーマ・エラーハンドリングを厳密化
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
> >   - `docs/SY-CONTAINER-3LAYER-ARCHITECTURE.md`: コンテナ3層構造を Mermaid 図で文書化（新規作成）
> >   - `docs/SY-STORAGE-MIGRATION-GUIDE.md`: 共有ファイルシステムの EFS/S3 移行方針を文書化（新規作成）
> >
> > 【実施結果】
> > - 2026-09-12: `ocr-worker/ndlocr_cli_patches/progress_reporter.py` を in-memory dict (`_progress_store`) 方式に変更し、ファイル書き込みを廃止
> > - 2026-09-12: `ocr-worker/app/main.py` に `GET /progress/{job_id}` エンドポイントを追加
> > - 2026-09-12: `backend/app/routers/jobs.py` の `_progress_event_generator` を ocr-worker HTTP API ポーリング方式に変更
> > - 2026-09-12: `backend/app/services/ocr_engine.py` の ocr-worker ホスト設定を確認・更新
> > - 2026-09-12: `backend/tests/test_progress.py` に ocr-worker HTTP API 連携テストを追加
> > - 2026-09-12: `frontend/src/hooks/__tests__/useOcrJob.test.ts` を更新
> > - 2026-09-12: `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` を更新
> > - 2026-09-13: UAT 中に発見された `ocr-worker/app/main.py` の import 不整合を修正（`ndlocr_cli_patches.progress_reporter` → `cli.core.progress_reporter`）
> > - 2026-09-13: `backend/tests/test_progress.py` を in-memory store 方式に合わせて更新（6 passed）
> > - 2026-09-13: E2E 検証で `POST /ocr` → `GET /progress/{job_id}` の連携が正常に動作することを確認（progress データが in-memory store に書き込まれ、API で取得可能）
> > - 2026-09-13: backend のファイルベース進捗共有（`_PROGRESS_DIR` / `{job_id}.json`）を完全に削除し、in-memory `job_manager.get_progress()` に移行
> > - 2026-09-13: `_progress_event_generator()` を in-memory データ + ocr-worker HTTP API ポーリング方式に再実装
> > - 2026-09-13: ocr-worker の `GET /progress/{job_id}` エンドポイントを活かしたマージ戦略を実装（`progress` / `current_page` / `message` は ocr-worker 優先、`status` は backend 優先）
> > - 2026-09-13: デッドコード `_POLL_INTERVAL` と `PROGRESS_POLL_INTERVAL` 環境変数、テスト用 `_test_progress_dir` を削除
> > - 2026-09-13: `backend/tests/test_progress.py` の 7 テストを修正・追加し全件 PASS（8/8）、`backend/tests/test_ocr.py` を in-memory 検証に書き換え
> > - 2026-09-13: backend 全テスト 39/39 PASS を確認
> > - 2026-09-13: `docs/SY-CONTAINER-PROGRESS-API-DESIGN.md` / `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` を更新し、ファイルベース進捗の廃止を反映
> > - 2026-09-14: `backend/app/routers/jobs.py` から `_emit_page_progress` 関数本体を削除
> > - 2026-09-14: `backend/app/routers/jobs.py` から `_run_ocr_and_generate_pdf` 内のコメントアウトされた疑似進捗呼び出し dead code を削除
> > - 2026-09-14: `backend/app/routers/jobs.py` から OCR 完了後の疑似進捗更新（progress=0.7）と PDF 生成中の疑似進捗更新（progress=0.9）を削除
> > - 2026-09-14: `backend/tests/test_ocr.py` から `_emit_page_progress` のテスト 2 件を削除
> > - 2026-09-14: backend 全テスト 37/37 PASS を確認
> > - 2026-09-14: frontend `ProgressPanel` を4領域構成にリデザイン（段階的ステップ表示、プログレスバー＋パーセンテージ、1行メッセージエリア、エラー表示エリア）
> > - 2026-09-14: `ProgressPanel` を常時表示に変更し、`latest` が null の場合はステップ1「ZIPアップロード中」/0% で描画
> > - 2026-09-14: `ProgressPanelProps` に `error?: string` を追加し、`page.tsx` からエラーを Props 経由で渡すように変更
> > - 2026-09-14: `useOcrJob` の `handleUploaded` でアップロード完了時に `latestProgress` を初期化し、OCR 実行前に `processing`/`progress=0.1` の仮進捗を注入
> > - 2026-09-14: 影響を受けるテスト（`ProgressPanel.test.tsx`、`useOcrJob.test.ts`、`page.test.tsx`、`page.msw.test.tsx`）を新しい挙動に合わせて更新
> > - 2026-09-14: frontend 全テスト 61/61 PASS、`npm run build` 成功、`npx tsc --noEmit` 成功を確認
> > - 2026-09-14: UAT（ユーザー検証テスト）を再実行。job_id=`b95649e2-152a-4755-9e71-26af1ee4c580` で 1 枚画像の ZIP アップロード → OCR 実行 → 完了までの一連フローを検証
> > - 2026-09-14: backend `GET /api/jobs/{job_id}` と ocr-worker `GET /progress/{job_id}` の進捗値が一致し、`completed` 時に `progress=1.0 / current_page=1 / total_pages=1` となることを確認
> > - 2026-09-14: SSE (`GET /api/jobs/{job_id}/events`) から `processing` / `progress=0.1` / `completed` / `[DONE]` が順に配信されることを確認
> > - 2026-09-14: PDF ダウンロード (`GET /api/jobs/{job_id}/pdf`) が `200 application/pdf` で 18 MB の有効な PDF を返すことを確認
> > - 2026-09-14: backend 全テスト 40/40 PASS、frontend 全テスト 61/61 PASS を UAT 直前に再確認
>
> <a id="sy002003"></a>
> ### SY002003 SY002002 UATバグ対応
>
> <div align="right"><a href="#sy002">タスク一覧へ↩︎</a></div>
>
> > 【計画】
> > #### バグ 1: 大容量ジョブでステップが「ZIPアップロード中」のまま
> >   内容: `frontend/src/components/progress/ProgressPanel.tsx` が progress 値の閾値だけでステップを判定しているため、1〜999 枚のジョブで正しいステップ遷移にならない場合がある
> >   対応方針: `status`（uploaded / processing / completed）と `progress` の両方を使ってアクティブステップを判定する
> >
> > #### バグ 2: OCR サブステップメッセージが「OCR処理を開始します」
> >   内容: `ocr-worker/ndlocr_cli_patches/inference.py` line 285 のページ処理開始時メッセージが「OCR 処理を開始します」になっている
> >   対応方針: メッセージを「OCR 処理中です（n/n）」に変更する
> >
> > #### バグ 3: PDF 生成中/完了メッセージが欠落
> >   内容: `backend/app/routers/jobs.py` の `_run_ocr_and_generate_pdf` で PDF 生成中と完了の進捗更新がない
> >   対応方針: PDF 生成開始時に `progress=0.75, message="PDF ファイル生成中です"` を発行し、完了時に `message="PDF ファイル生成が完了しました"` に変更する
> >
> > #### テスト更新方針
> > - `frontend/src/components/progress/__tests__/ProgressPanel.test.tsx`: status ベースのステップ遷移テストを追加
> > - `backend/tests/test_progress.py`: PDF 生成フェーズの進捗更新テストを追加
> > - backend 全テスト 40/40 PASS、frontend 全テスト 61/61 PASS、frontend build PASS を目指す
> >
> > 【実施結果】
> > - 2026-09-15: `frontend/src/components/progress/ProgressPanel.tsx` のステップ判定を `status`（uploaded / processing / completed）と `progress` の両方で行うように修正。`status=completed` 時は最終ステップを完了表示とし、`status=processing` 時は `progress >= 0.75` で PDF 生成中ステップをアクティブにする
> > - 2026-09-15: `ocr-worker/ndlocr_cli_patches/inference.py` line 285 のページ処理開始時メッセージを「OCR 処理を開始します（n/n）」から「OCR 処理中です（n/n）」に変更
> > - 2026-09-15: `backend/app/routers/jobs.py` の `_run_ocr_and_generate_pdf` で OCR 全ページ完了後に `progress=0.75, message="PDF ファイル生成中です"` の進捗更新を追加。PDF 生成完了時のメッセージを「PDF ファイル生成が完了しました」に統一
> > - 2026-09-15: 影響を受けるテストを更新：`backend/tests/test_ocr.py` の完了メッセージアサーションを修正、`frontend/src/components/progress/__tests__/ProgressPanel.test.tsx` に status ベースのステップ遷移テストを追加、`frontend/src/hooks/__tests__/useOcrJob.test.ts` / `frontend/src/app/__tests__/page.msw.test.tsx` の完了メッセージを修正
> > - 2026-09-15: backend 全テスト 40/40 PASS、frontend 全テスト 62/62 PASS、`npm run build` PASS、`npx tsc --noEmit` PASS
>
