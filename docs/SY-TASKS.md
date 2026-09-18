# System タスク管理表

> 最終更新: 2026/09/18

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
> > - 2026-09-15: frontend のポーリング間隔を `NEXT_PUBLIC_POLL_INTERVAL_MS` 環境変数から読み込むように変更（デフォルト 1000 ms）。`frontend/src/lib/api.ts` のハードコード 2000 ms を置換
> > - 2026-09-15: `docker-compose.yml` に `NEXT_PUBLIC_POLL_INTERVAL_MS=1000`（frontend サービス）と `OCR_WORKER_POLL_INTERVAL=1.0`（backend サービス）を追加
> > - 2026-09-15: frontend 単体テスト（`npm test -- --run`）、backend 単体テスト（`.venv/bin/pytest`）、frontend ビルド（`npm run build`）、frontend Docker リビルドを実施し、いずれも成功
> > - 2026-09-15: 実行中の `frontend` / `backend` コンテナ内で、それぞれ `NEXT_PUBLIC_POLL_INTERVAL_MS=1000` / `OCR_WORKER_POLL_INTERVAL=1.0` が反映されていることを確認
> > - 2026-09-15: 実際の OCR ジョブ（job_id=`91f5de94-7f37-4cd5-8f8e-b382ae283f67`）で backend → ocr-worker の進捗ポーリングが約 1 秒間隔で動作することを確認
> > - 2026-09-15: `backend/tests/test_jobs.py` において `PDFファイル生成中です` メッセージが進捗マージロジックとして検証されていることを確認（実環境では PDF 生成が 1 秒未満で完了しポーリングで観測できなかったため、テストレベルで担保）
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
> > #### 追加対応: ポーリング間隔の設定外部化
> > - Frontend→Backend の polling 間隔を `NEXT_PUBLIC_POLL_INTERVAL_MS` 環境変数で設定可能にし、デフォルトを 1000ms にする
> > - Backend→ocr-worker の polling 間隔を `OCR_WORKER_POLL_INTERVAL` 環境変数で設定可能にし、デフォルトを 1.0 秒にする
> > - `docker-compose.yml` に両方の環境変数を追加し、設定値の一元管理を行う
> >
> > #### 追加対応: 「OCR 結果」表示エリアの削除
> > - ユーザー確認の結果、OCR 生テキストの表示は不要と判断
> > - `frontend/src/app/page.tsx` の OCR 結果 `<pre>` 表示ブロックを削除
> > - `frontend/src/hooks/useOcrJob.ts` の `result` 状態・`setResult` 呼び出し・戻り値からの `result` を削除
> > - `frontend/src/types/index.ts` の未使用 `ResultPanelProps` 型を削除
> > - 影響テスト（`frontend/src/app/__tests__/page.test.tsx`、`frontend/src/hooks/__tests__/useOcrJob.test.ts`）を更新
> >

> > - 2026-09-15: `frontend/src/components/progress/ProgressPanel.tsx` のステップ判定を `status`（uploaded / processing / completed）と `progress` の両方で行うように修正。`status=completed` 時は最終ステップを完了表示とし、`status=processing` 時は `progress >= 0.75` で PDF 生成中ステップをアクティブにする
> > - 2026-09-15: `ocr-worker/ndlocr_cli_patches/inference.py` line 285 のページ処理開始時メッセージを「OCR 処理を開始します（n/n）」から「OCR 処理中です（n/n）」に変更
> > - 2026-09-15: `backend/app/routers/jobs.py` の `_run_ocr_and_generate_pdf` で OCR 全ページ完了後に `progress=0.75, message="PDF ファイル生成中です"` の進捗更新を追加。PDF 生成完了時のメッセージを「PDF ファイル生成が完了しました」に統一
> > - 2026-09-15: 影響を受けるテストを更新：`backend/tests/test_ocr.py` の完了メッセージアサーションを修正、`frontend/src/components/progress/__tests__/ProgressPanel.test.tsx` に status ベースのステップ遷移テストを追加、`frontend/src/hooks/__tests__/useOcrJob.test.ts` / `frontend/src/app/__tests__/page.msw.test.tsx` の完了メッセージを修正
> > - 2026-09-15: backend 全テスト 41/41 PASS、frontend 全テスト 62/62 PASS、`npm run build` PASS、`npx tsc --noEmit` PASS
> > - 2026-09-15: UAT 不具合発見：プログレスバーが表示されない。原因は `frontend/src/app/globals.css` に `--primary` / `--muted` など shadcn/ui 標準 CSS 変数が未定義だったため。これらを追加しライト/ダーク両モードで定義。frontend build PASS、テスト 62/62 PASS を確認
> > - 2026-09-15: `frontend/src/lib/api.ts` の `POLL_INTERVAL_MS` を環境変数 `NEXT_PUBLIC_POLL_INTERVAL_MS` から取得するように変更。無効値時のデフォルトを 1000ms に設定
> > - 2026-09-15: `docker-compose.yml` に `OCR_WORKER_POLL_INTERVAL=1.0` と `NEXT_PUBLIC_POLL_INTERVAL_MS=1000` を追加し、コンテナ間ポーリング間隔を一元管理
> > - 2026-09-15: `frontend/src/app/page.tsx` から「OCR 結果」表示エリアを削除。`useOcrJob` から `result` 状態を削除し、`frontend/src/types/index.ts` の未使用 `ResultPanelProps` 型も削除。影響テストを更新
> > - 2026-09-15: `frontend/src/components/upload/ImageList.tsx` の「アップロードされた画像」ファイル名一覧を縦3行固定・横スクロールバーのグリッドレイアウトに変更。`frontend/src/components/upload/__tests__/ImageList.test.tsx` は既存アサートで維持
> > - 2026-09-15: UAT 不具合発見：ZIP アップロード時に `__MACOSX/._*` などの macOS リソースフォークファイルが画像一覧に表示される。`backend/app/services/zip_extractor.py` で `__MACOSX` ディレクトリ配下を画像一覧から除外。`backend/tests/test_jobs.py` に `test_upload_zip_excludes_macosx_resource_forks` を追加
> > - 2026-09-15: UAT フィードバック対応：`frontend/src/components/progress/ProgressPanel.tsx` の進捗ステップラベルから「中」を削除（「ZIPアップロード中」→「ZIPアップロード」、「OCR処理中」→「OCR処理」、「PDF生成中」→「PDF生成」）。影響テスト `frontend/src/components/progress/__tests__/ProgressPanel.test.tsx` を更新
> > - 2026-09-15: **Phase 3 検証完了**：backend 全テスト 42/42 PASS、frontend 全テスト 62/62 PASS、frontend build PASS。タスク完了承認および UAT 実施を待つ
> - 2026-09-17: UAT 不具合発見（debug タイミング表示）: `frontend/src/hooks/useOcrJob.ts` の `extractActualPage` が全角括弧 `（）` のみを解析していたため、プロキシ/ブラウザ正規化による半角括弧 `()` メッセージから actualPage を抽出できず、ページ単位タイミングが記録されなかった
> - 2026-09-17: `extractActualPage` の正規表現を全角・半角括弧両方に対応させ、半角括弧ケースの単体テストを `frontend/src/hooks/__tests__/useOcrJob.test.ts` に追加
> - 2026-09-17: UAT 不具合発見（current_page オフバイワン）: `ocr-worker/ndlocr_cli_patches/inference.py` の ruby_only パスが 0-based `current_page` を報告しており、frontend のフォールバックと整合しない
> - 2026-09-17: `ocr-worker/ndlocr_cli_patches/inference.py` の通常パス・ルビ推定パス両方で `current_page` を 1-based (`page_idx + 1`) に統一
> - 2026-09-17: UAT 不具合発見（進捗メッセージ消失）: `backend/app/routers/jobs.py` の `_merge_progress_data` が進捗値の大きい側の message を常に採用するため、backend が空メッセージで更新すると ocr-worker の per-page メッセージが上書きされ、タイミング抽出に必要なページ情報が失われる
> - 2026-09-17: `_merge_progress_data` を修正し、進捗値が大きい側の message が空の場合はもう一方の非空メッセージにフォールバック。`backend/tests/test_progress.py` にマージロジックの単体テストを追加
> - 2026-09-17: **Phase 3 再検証完了**：backend 全テスト 53/53 PASS、frontend 全テスト 89/89 PASS、ocr-worker 全テスト 10/10 PASS、frontend build PASS。タスク完了承認および UAT 実施を待つ
> > - 2026-09-17: UAT 不具合発見：`ruby_only=True`（ルビ推定モード）時に per-page 進捗が通知されない。`ocr-worker/ndlocr_cli_patches/inference.py` の `_infer_ruby_only` に `_update_progress` 呼び出しを追加し、通常モード `_infer` と同じ進捗セマンティクスで通知するように修正
> > - 2026-09-17: `ocr-worker/tests/test_main.py` に `test_run_ocr_with_ruby_only_returns_accepted_and_result` を追加し、`ruby_only=True` 時の進捗 completed 状態を検証
> > - 2026-09-17: ocr-worker 全テスト 10/10 PASS
> > - 2026-09-18: `ruby_only=True` UAT 実施（job_id `ruby-uat-003`）。backend は現在 `ruby_only=False` をハードコードしているため、ocr-worker `/ocr` エンドポイントに直接 `ruby_only=True`、`input_structure='s'`、`enable_progress=True` を指定してリクエスト。per-page 進捗（`current_page=1`、`total_pages=1`、`status=completed`）およびページ処理時間の DEBUG ログ出力を確認
> > - 2026-09-18: **Phase 3 再検証完了**：backend 全テスト 53/53 PASS、frontend 全テスト 89/89 PASS、ocr-worker 全テスト 10/10 PASS、frontend build PASS（`NODE_ENV=production`）。タスク完了承認を待つ
> > - 2026-09-18: UAT 不具合発見：`OCR 処理時間（ページ毎）` でページ 1, 2 の開始・完了時刻が記録されず、ページ 3 のみ完了時刻が記録される。Docker Desktop から全コンテナを削除・リビルドし、Safari のキャッシュをクリアしても再現するため、frontend/backend のイベントフローをトレースする一時的なデバッグログを追加
> > - 2026-09-18: `frontend/src/hooks/useOcrJob.ts` の `reset()` / `handleUploaded()` 内の `setTimingDebug` をアップデータ関数形式 `(() => ({...}))` に統一し、React 18 Automatic Batching による state 上書きを防止
> > - 2026-09-18: `backend/app/services/job_manager.py` に `_now_iso()` を導入し、backend の UTC タイムスタンプを frontend/ocr-worker と同じミリ秒 `Z` 形式に正規化
> > - 2026-09-18: `backend/app/routers/jobs.py` の ocr-worker 進捗ポーリングに `[WORKER-POLL]` / `[WORKER-RESPONSE]` 通信ログを追加
> > - 2026-09-18: frontend の一時デバッグログ（`[RAW-EVENT]` / `[PARSED-EVENT]` / `[TIMING-BEFORE]` / `[TIMING-AFTER]` / `[TIMING-STATE]` / `[TIMING-DEBUG]`）を削除
> > - 2026-09-18: **Phase 3 検証完了**：backend 全テスト 53/53 PASS、frontend 全テスト 89/89 PASS、frontend build PASS。UAT 実施およびタスク完了承認を待つ
> > - 2026-09-18: コンソールへの通信内容デバッグ出力を実装。`frontend/src/lib/api.ts` の HTTP/SSE 通信に `[API-DEBUG]` / `[SSE-DEBUG]` ログを追加（`NEXT_PUBLIC_DEBUG_API` 環境変数で HTTP 詳細ログを制御、SSE イベントは常時出力）。`backend/app/routers/jobs.py` の frontend 受信エンドポイントに `[API-IN]` / `[API-OUT]` ログを追加。`backend/app/services/ocr_engine.py` / `backend/app/routers/jobs.py` の ocr-worker 通信に `[OCR-WORKER-REQ]` / `[OCR-WORKER-RES]` ログを追加
> > - 2026-09-18: テスト用 `FakeResponse` に `text` 属性を追加し、backend 全テスト 53/53 PASS、frontend 全テスト 89/89 PASS、frontend build PASS を維持
> > - 2026-09-18: UAT 不具合発見（OCR 処理時間（ページ毎）の開始・経過が空欄）: `backend/app/routers/jobs.py` の `_merge_progress_data` が progress の大きい backend のメッセージを常に採用するため、ocr-worker の per-page メッセージ `(N/M)` が上書きされ、frontend でのページ遷移検出に必要な情報が失われていた
> > - 2026-09-18: `_merge_progress_data` の message 選択を `_select_merged_message()` に分離。ocr-worker の per-page メッセージ `(N/M)` / `（N/M）` は常に優先し、それ以外は progress の大きい側の message を採用するように変更
> > - 2026-09-18: `frontend/src/hooks/useOcrJob.ts` の `updateTimingDebug` に一時的な `[TIMING-DEBUG]` ログを追加し、entry / page check / page transition / PDF generation detected / terminal state の遷移をブラウザコンソールで確認できるようにする
> > - 2026-09-18: `backend/app/services/job_manager.py` の `_now_iso()` を秒精度 `YYYY-MM-DDTHH:MM:SSZ` に統一し、ocr-worker/frontend と同じ形式にする
> > - 2026-09-18: `ocr-worker/ndlocr_cli_patches/progress_reporter.py` と `ocr-worker/app/main.py` のタイムスタンプ生成を秒精度 `YYYY-MM-DDTHH:MM:SSZ` に統一
> > - 2026-09-18: backend テスト `test_get_job_prefers_backend_progress_when_larger` / `test_merge_progress_data_prefers_higher_progress_message_when_nonempty` を新しい message マージルールに合わせて更新
> > - 2026-09-18: **Phase 3 再検証完了**：backend 全テスト 53/53 PASS、frontend 全テスト 89/89 PASS、frontend build PASS。Docker コンテナリビルド・UAT 実施を待つ
>
