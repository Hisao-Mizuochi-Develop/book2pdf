# タスク管理

本ファイルは、Web OCR/PDF システムのタスクを追記型で管理するものです。
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
ZIP アーカイブをアップロードして OCR ジョブを開始する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 001001 | FastAPI プロジェクトの初期構成 | 2026-08-11 | 2026-08-11 | 設計 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | FastAPI アプリケーションのディレクトリ構成を作成する（app/routers, services, models, core, tests） |  |  |  |
|  | requirements.txt を作成する（fastapi, uvicorn[standard], python-multipart, pymupdf, pydantic, pydantic-settings, pytest, httpx） |  |  |  |
|  | backend/Dockerfile を作成する（python:3.11-slim ベース、uvicorn 起動） |  |  |  |
|  | 基本動作確認用テストを作成し、pytest で 3 件 pass することを確認する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | FastAPI アプリケーションのディレクトリ構成を作成した（app/routers, services, models, core, tests） |  |  |  |
|  | requirements.txt を作成・更新した（fastapi, uvicorn, pytest, httpx などを追加） |  |  |  |
|  | backend/Dockerfile を作成した（python:3.11-slim ベース、uvicorn 起動） |  |  |  |
|  | 基本動作確認用テストを作成し、pytest で 3 件 pass した |  |  |  |
| 001002 | ZIP アップロード・展開機能の実装 | 2026-08-11 | 2026-08-11 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | モデル更新: app/models/job.py に UPLOADED 状態を追加する |  |  |  |
|  | サービス更新: app/services/job_manager.py に画像ファイル一覧を保持する files フィールドを追加する |  |  |  |
|  | ZIP 展開機能: app/services/zip_extractor.py を新規作成し、ZIP から画像ファイルを抽出する |  |  |  |
|  | ルーター更新: app/routers/jobs.py に POST /api/jobs/{job_id}/upload エンドポイントを追加する |  |  |  |
|  | テスト追加: backend/tests/test_jobs.py を新規作成し、アップロード成功・失敗ケースを確認する |  |  |  |
|  | ドキュメント更新: tasks.md / work_log.md / caveats.md / backend-system-spec.md を必要に応じて更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | app/models/job.py に UPLOADED 状態と JobUploadResponse、JobResponse.files を追加した |  |  |  |
|  | app/services/job_manager.py に files フィールドと temp_dir 保存機能を追加した |  |  |  |
|  | app/services/zip_extractor.py を新規作成し、ZIP から画像ファイルを抽出する機能を実装した |  |  |  |
|  | app/routers/jobs.py に POST /api/jobs/{job_id}/upload エンドポイントを追加した |  |  |  |
|  | backend/tests/test_jobs.py を新規作成し、5 件のテストを追加した |  |  |  |
|  | pytest を実行し、既存テストを含む 8 件すべて pass した |  |  |  |
|  | backend/docs/backend-system-spec.md のフォルダ・ファイル構成を更新した |  |  |  |
|  | 各ソースファイルの import 部分に、初学者向けに「何をインポートし、なぜ必要か」のコメントを追加した |  |  |  |
|  | docs/coding-conventions.md の 2.4 コメントに「コメント行以外のプログラムの各行に原則コメントを記載する」ルールを追加した |  |  |  |
|  | 作成済みのすべての backend ソースコードに新ルールを適用し、import 行・変数宣言・制御構文・関数呼び出し・return 文などにコメントを追加した |  |  |  |
| 001003 | ndlocr_cli 連携の実装 | 2026-08-11 | 2026-08-11 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | ndlocr_cli の import 方法と OcrInferrer の signature を調査する |  |  |  |
|  | OCR エンジンを抽象化した app/services/ocr_engine.py を新規作成する |  |  |  |
|  | ndlocr_cli が利用できない環境では MockOcrEngine にフォールバックする |  |  |  |
|  | app/models/job.py に JobOcrResponse レスポンスモデルを追加する |  |  |  |
|  | app/services/job_manager.py に PROCESSING/COMPLETED/FAILED 状態遷移を追加する |  |  |  |
|  | app/routers/jobs.py に POST /api/jobs/{job_id}/ocr エンドポイントを追加する |  |  |  |
|  | backend/tests/test_ocr.py を新規作成し、OCR 実行の正常系・異常系テストを追加する |  |  |  |
|  | pytest を実行し、すべてのテストが pass することを確認する |  |  |  |
|  | backend/docs/work_log.md と caveats.md、backend-system-spec.md を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | GitHub 上の ndlocr_cli リポジトリを確認し、OcrInferrer の使い方を調査した |  |  |  |
|  | app/services/ocr_engine.py を新規作成し、BaseOcrEngine / NdloCrOcrEngine / MockOcrEngine を実装した |  |  |  |
|  | app/models/job.py に JobOcrResponse を追加した |  |  |  |
|  | app/services/job_manager.py に update_job_with_ocr_result 関数を追加し、COMPLETED / FAILED 状態遷移に対応した |  |  |  |
|  | app/routers/jobs.py に POST /api/jobs/{job_id}/ocr エンドポイントを追加した |  |  |  |
|  | backend/tests/test_ocr.py を新規作成し、5 件のテストを追加した |  |  |  |
|  | pytest を実行し、既存テストを含む 13 件すべて pass した |  |  |  |
|  | backend/docs/caveats.md と work_log.md、backend-system-spec.md を更新した |  |  |  |
| 001004 | ocr-worker コンテナ連携の実装 | 2026-08-11 | 2026-08-11 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `backend/app/services/ocr_engine.py` に `RemoteNdloCrOcrEngine` を新規作成する |  |  |  |
|  | `OCR_WORKER_URL` 環境変数が設定されていれば ocr-worker の HTTP API を呼び出すようにする |  |  |  |
|  | `docker-compose.yml` で backend から ocr-worker への接続と環境変数を設定する |  |  |  |
|  | `backend/tests/test_ocr.py` を更新し、ocr-worker コンテナを使った実際の OCR 実行を検証する |  |  |  |
|  | サンプル画像 2〜3 ページ分を使って、backend → ocr-worker → OCR 結果の流れを確認する |  |  |  |
|  | `backend/docs/work_log.md` / `caveats.md` / `backend-system-spec.md` を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: `backend/app/services/ocr_engine.py` に `RemoteNdloCrOcrEngine` を新規作成し、ocr-worker の `POST /ocr` を呼び出す実装を追加した |  |  |  |
|  | 2026-08-11: `OCR_WORKER_URL` 環境変数に応じて `RemoteNdloCrOcrEngine` / `NdloCrOcrEngine` / `MockOcrEngine` を切り替えるよう `create_ocr_engine()` を更新した |  |  |  |
|  | 2026-08-11: `docker-compose.yml` を更新し、backend から `http://ocr-worker:8000` へアクセスできるよう共有ボリューム・環境変数・ヘルスチェックを設定した |  |  |  |
|  | 2026-08-11: `backend/tests/conftest.py` を作成し、テスト時に `EXTRACT_BASE_DIR` を一時ディレクトリに設定するようにした |  |  |  |
|  | 2026-08-11: backend のローカル pytest で 13 件すべて pass した |  |  |  |
|  | 2026-08-11: Docker コンテナをビルド・起動し、両サービスのヘルスチェックが正常に動作することを確認した |  |  |  |
|  | 2026-08-11: サンプル画像 2 枚を ZIP アップロードし、backend → ocr-worker → OCR 結果の流れでジョブが `completed` になることを確認した |  |  |  |
|  | 2026-08-11: `backend/docs/work_log.md` / `caveats.md` / `backend-system-spec.md` を更新した |  |  |  |

---

## ユースケースNo | 002

ユースケース
OCR 処理の進捗をリアルタイムで確認する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 002001 | SSE 進捗通知機能の実装 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | FastAPI の StreamingResponse を使って SSE を実装する |  |  |  |
|  | フロントエンドで SSE を受信して進捗バーを表示する |  |  |  |

---

## ユースケースNo | 003

ユースケース
OCR 完了後に検索可能 PDF をダウンロードする

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 003001 | 検索可能 PDF 生成機能の実装 | 2026-08-11 | 2026-08-11 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | XML 解析サービス: `backend/app/services/xml_parser.py` を新規作成し、ndlocr_cli の `.sorted.xml` をパースしてページ画像パス・テキスト・座標（X, Y, WIDTH, HEIGHT）を取得する |  |  |  |
|  | PDF 生成サービス: `backend/app/services/pdf_generator.py` を新規作成し、PyMuPDF（fitz）で元画像を背景・認識テキストを透明テキストレイヤーとして配置した PDF を `/data/pdfs/{job_id}.pdf` に出力する |  |  |  |
|  | ジョブ管理拡張: `backend/app/services/job_manager.py` に PDF パスを保存する関数を追加する |  |  |  |
|  | ダウンロード API: `backend/app/routers/jobs.py` に `GET /api/jobs/{job_id}/pdf` を追加し、生成済み PDF を返す（未生成・未完了時は 400/404） |  |  |  |
|  | OCR 後処理: `POST /api/jobs/{job_id}/ocr` 成功後に PDF 生成を自動実行する |  |  |  |
|  | テスト追加: `backend/tests/test_pdf.py` を新規作成し、MockOcrEngine + 手動作成 XML で PDF 生成とダウンロード API を検証する |  |  |  |
|  | ドキュメント更新: `tasks.md` / `work_log.md` / `caveats.md` / `backend-system-spec.md` を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: `backend/app/services/xml_parser.py` を新規作成し、ndlocr_cli の `.sorted.xml` からページ画像パス・テキスト・座標を取得する機能を実装した |  |  |  |
|  | 2026-08-11: `backend/app/services/pdf_generator.py` を新規作成し、PyMuPDF（fitz）で元画像を背景・認識テキストを透明テキストレイヤーとして配置した検索可能 PDF を生成する機能を実装した |  |  |  |
|  | 2026-08-11: `backend/app/services/job_manager.py` に `update_job_with_pdf_path()` 関数を追加し、ジョブ情報に PDF パスを保存できるようにした |  |  |  |
|  | 2026-08-11: `backend/app/routers/jobs.py` に `GET /api/jobs/{job_id}/pdf` エンドポイントを追加し、生成済み PDF をダウンロードできるようにした（未生成・未完了時は 400/404 を返す） |  |  |  |
|  | 2026-08-11: `POST /api/jobs/{job_id}/ocr` 成功後に `generate_searchable_pdf()` を呼び出し、OCR 結果から PDF を自動生成する処理を追加した |  |  |  |
|  | 2026-08-11: `backend/tests/test_pdf.py` を新規作成し、PDF 生成・XML 解析・ダウンロード API の正常系・異常系テストを 7 件追加した |  |  |  |
|  | 2026-08-11: テスト実行中に `tests/test_progress.py` の SSE ストリーミングテストが停止・失敗する事象が発生した。原因は `fastapi.testclient.TestClient` + `StreamingResponse` + 非同期 generator のタイミング競合。対応として `_progress_event_generator` を直接 `async for` でテストする形に変更し、安定して pass するようになった |  |  |  |
|  | 2026-08-11: `pytest` を実行し、backend の全 23 件のテストが pass することを確認した |  |  |  |
|  | 2026-08-11: `backend/docs/backend-system-spec.md` / `caveats.md` / `tasks.md` / `work_log.md` を更新した |  |  |  |
|  | 2026-08-11: 結合テストを実施し、PDF ダウンロード API (`GET /api/jobs/{job_id}/pdf`) が 404 エラーを返す事象を確認 |  |  |  |
|  | 2026-08-11: 原因は backend コンテナが最新ソースで再ビルドされていなかったこと。`docker compose up -d --build backend` で再ビルド・再起動して解消 |  |  |  |
|  | 2026-08-11: 再テストで ZIP アップロード → OCR 実行 → PDF ダウンロードが正常に完了することを確認（HTTP 200、Content-Type: application/pdf、2 ページの PDF） |  |  |  |
|  | 2026-08-11: 結合テストに関する内容を `backend/docs/work_log.md` / `caveats.md` / `tasks.md` に追記 |  |  |  |
| 003002 | 縦書き PDF 対応 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 縦書きテキストの検出結果を PDF 上で正しく配置する |  |  |  |
|  | 90度回転や縦書きフォントの埋め込みを検討する |  |  |  |
|  | 横書きで安定動作後に段階的に対応する |  |  |  |

---

## ユースケースNo | 004

ユースケース
ジョブ状態を永続化して再起動後も復元する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 004001 | ジョブ状態の SQLite 永続化 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | SQLAlchemy または sqlite3 を使ってジョブテーブルを設計する |  |  |  |
|  | メモリ内管理から SQLite 永続化に移行する |  |  |  |
|  | プロセス再起動後もジョブ状態が復元されるようにする |  |  |  |

---

## ユースケースNo | 005

ユースケース
プロキシ環境でも進捗通知を受け取る

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 005001 | 進捗通知のポーリング方式対応 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | フロントエンドのポーリング方式を実装する |  |  |  |
|  | SSE とポーリングを切り替えられるようにする |  |  |  |


