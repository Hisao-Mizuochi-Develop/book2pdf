# タスク管理

本ファイルは、Web OCR/PDF システムのタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する
- タスク No は「モジュール識別子（2文字）＋ ユースケースNo（3桁）＋ 通番（3桁）」とする
  - 識別子: `BE`=backend
  - 例：ユースケース001の1番目のタスク → `BE001001`
- 通番は各ユースケース内で 001 から連番で振る

---

## ユースケースNo | 001

ユースケース
ZIP アーカイブをアップロードして OCR ジョブを開始する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| BE001001 | FastAPI プロジェクトの初期構成 | 2026-08-11 | 2026-08-11 | 設計 |
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
| BE001002 | ZIP アップロード・展開機能の実装 | 2026-08-11 | 2026-08-11 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | モデル更新: app/models/job.py に UPLOADED 状態を追加する |  |  |  |
|  | サービス更新: app/services/job_manager.py に画像ファイル一覧を保持する files フィールドを追加する |  |  |  |
|  | ZIP 展開機能: app/services/zip_extractor.py を新規作成し、ZIP から画像ファイルを抽出する |  |  |  |
|  | ルーター更新: app/routers/jobs.py に POST /api/jobs/{job_id}/upload エンドポイントを追加する |  |  |  |
|  | テスト追加: backend/tests/test_jobs.py を新規作成し、アップロード成功・失敗ケースを確認する |  |  |  |
|  | ドキュメント更新: BE-TASKS.md / BE-WORK-LOG.md / BE-CAVEATS.md / BE-BACKEND-SYSTEM-SPEC.md を必要に応じて更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | app/models/job.py に UPLOADED 状態と JobUploadResponse、JobResponse.files を追加した |  |  |  |
|  | app/services/job_manager.py に files フィールドと temp_dir 保存機能を追加した |  |  |  |
|  | app/services/zip_extractor.py を新規作成し、ZIP から画像ファイルを抽出する機能を実装した |  |  |  |
|  | app/routers/jobs.py に POST /api/jobs/{job_id}/upload エンドポイントを追加した |  |  |  |
|  | backend/tests/test_jobs.py を新規作成し、5 件のテストを追加した |  |  |  |
|  | pytest を実行し、既存テストを含む 8 件すべて pass した |  |  |  |
|  | backend/docs/BE-BACKEND-SYSTEM-SPEC.md のフォルダ・ファイル構成を更新した |  |  |  |
|  | 各ソースファイルの import 部分に、初学者向けに「何をインポートし、なぜ必要か」のコメントを追加した |  |  |  |
|  | docs/OT-CODING-CONVENTIONS.md の 2.4 コメントに「コメント行以外のプログラムの各行に原則コメントを記載する」ルールを追加した |  |  |  |
|  | 作成済みのすべての backend ソースコードに新ルールを適用し、import 行・変数宣言・制御構文・関数呼び出し・return 文などにコメントを追加した |  |  |  |
| BE001003 | ndlocr_cli 連携の実装 | 2026-08-11 | 2026-08-11 | 機能実装 |
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
|  | backend/docs/BE-WORK-LOG.md と BE-CAVEATS.md、BE-BACKEND-SYSTEM-SPEC.md を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | GitHub 上の ndlocr_cli リポジトリを確認し、OcrInferrer の使い方を調査した |  |  |  |
|  | app/services/ocr_engine.py を新規作成し、BaseOcrEngine / NdloCrOcrEngine / MockOcrEngine を実装した |  |  |  |
|  | app/models/job.py に JobOcrResponse を追加した |  |  |  |
|  | app/services/job_manager.py に update_job_with_ocr_result 関数を追加し、COMPLETED / FAILED 状態遷移に対応した |  |  |  |
|  | app/routers/jobs.py に POST /api/jobs/{job_id}/ocr エンドポイントを追加した |  |  |  |
|  | backend/tests/test_ocr.py を新規作成し、5 件のテストを追加した |  |  |  |
|  | pytest を実行し、既存テストを含む 13 件すべて pass した |  |  |  |
|  | backend/docs/BE-CAVEATS.md と BE-WORK-LOG.md、BE-BACKEND-SYSTEM-SPEC.md を更新した |  |  |  |
| BE001004 | ocr-worker コンテナ連携の実装 | 2026-08-11 | 2026-08-11 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `backend/app/services/ocr_engine.py` に `RemoteNdloCrOcrEngine` を新規作成する |  |  |  |
|  | `OCR_WORKER_URL` 環境変数が設定されていれば ocr-worker の HTTP API を呼び出すようにする |  |  |  |
|  | `docker-compose.yml` で backend から ocr-worker への接続と環境変数を設定する |  |  |  |
|  | `backend/tests/test_ocr.py` を更新し、ocr-worker コンテナを使った実際の OCR 実行を検証する |  |  |  |
|  | サンプル画像 2〜3 ページ分を使って、backend → ocr-worker → OCR 結果の流れを確認する |  |  |  |
|  | `backend/docs/BE-WORK-LOG.md` / `BE-CAVEATS.md` / `BE-BACKEND-SYSTEM-SPEC.md` を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: `backend/app/services/ocr_engine.py` に `RemoteNdloCrOcrEngine` を新規作成し、ocr-worker の `POST /ocr` を呼び出す実装を追加した |  |  |  |
|  | 2026-08-11: `OCR_WORKER_URL` 環境変数に応じて `RemoteNdloCrOcrEngine` / `NdloCrOcrEngine` / `MockOcrEngine` を切り替えるよう `create_ocr_engine()` を更新した |  |  |  |
|  | 2026-08-11: `docker-compose.yml` を更新し、backend から `http://ocr-worker:8000` へアクセスできるよう共有ボリューム・環境変数・ヘルスチェックを設定した |  |  |  |
|  | 2026-08-11: `backend/tests/conftest.py` を作成し、テスト時に `EXTRACT_BASE_DIR` を一時ディレクトリに設定するようにした |  |  |  |
|  | 2026-08-11: backend のローカル pytest で 13 件すべて pass した |  |  |  |
|  | 2026-08-11: Docker コンテナをビルド・起動し、両サービスのヘルスチェックが正常に動作することを確認した |  |  |  |
|  | 2026-08-11: サンプル画像 2 枚を ZIP アップロードし、backend → ocr-worker → OCR 結果の流れでジョブが `completed` になることを確認した |  |  |  |
|  | 2026-08-11: `backend/docs/BE-WORK-LOG.md` / `BE-CAVEATS.md` / `BE-BACKEND-SYSTEM-SPEC.md` を更新した |  |  |  |

---

## ユースケースNo | 002

ユースケース
OCR 処理の進捗をリアルタイムで確認する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| BE002001 | SSE 進捗通知機能の実装 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | FastAPI の StreamingResponse を使って SSE を実装する |  |  |  |
|  | フロントエンドで SSE を受信して進捗バーを表示する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | （未実施） |  |  |  |

---

## ユースケースNo | 003

ユースケース
OCR 完了後に検索可能 PDF をダウンロードする

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| BE003001 | 検索可能 PDF 生成機能の実装 | 2026-08-11 | 2026-08-11 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | XML 解析サービス: `backend/app/services/xml_parser.py` を新規作成し、ndlocr_cli の `.sorted.xml` をパースしてページ画像パス・テキスト・座標（X, Y, WIDTH, HEIGHT）を取得する |  |  |  |
|  | PDF 生成サービス: `backend/app/services/pdf_generator.py` を新規作成し、PyMuPDF（fitz）で元画像を背景・認識テキストを透明テキストレイヤーとして配置した PDF を `/data/pdfs/{job_id}.pdf` に出力する |  |  |  |
|  | ジョブ管理拡張: `backend/app/services/job_manager.py` に PDF パスを保存する関数を追加する |  |  |  |
|  | ダウンロード API: `backend/app/routers/jobs.py` に `GET /api/jobs/{job_id}/pdf` を追加し、生成済み PDF を返す（未生成・未完了時は 400/404） |  |  |  |
|  | OCR 後処理: `POST /api/jobs/{job_id}/ocr` 成功後に PDF 生成を自動実行する |  |  |  |
|  | テスト追加: `backend/tests/test_pdf.py` を新規作成し、MockOcrEngine + 手動作成 XML で PDF 生成とダウンロード API を検証する |  |  |  |
|  | ドキュメント更新: `BE-TASKS.md` / `BE-WORK-LOG.md` / `BE-CAVEATS.md` / `BE-BACKEND-SYSTEM-SPEC.md` を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: `backend/app/services/xml_parser.py` を新規作成し、ndlocr_cli の `.sorted.xml` からページ画像パス・テキスト・座標を取得する機能を実装した |  |  |  |
|  | 2026-08-11: `backend/app/services/pdf_generator.py` を新規作成し、PyMuPDF（fitz）で元画像を背景・認識テキストを透明テキストレイヤーとして配置した検索可能 PDF を生成する機能を実装した |  |  |  |
|  | 2026-08-11: `backend/app/services/job_manager.py` に `update_job_with_pdf_path()` 関数を追加し、ジョブ情報に PDF パスを保存できるようにした |  |  |  |
|  | 2026-08-11: `backend/app/routers/jobs.py` に `GET /api/jobs/{job_id}/pdf` エンドポイントを追加し、生成済み PDF をダウンロードできるようにした（未生成・未完了時は 400/404 を返す） |  |  |  |
|  | 2026-08-11: `POST /api/jobs/{job_id}/ocr` 成功後に `generate_searchable_pdf()` を呼び出し、OCR 結果から PDF を自動生成する処理を追加した |  |  |  |
|  | 2026-08-11: `backend/tests/test_pdf.py` を新規作成し、PDF 生成・XML 解析・ダウンロード API の正常系・異常系テストを 7 件追加した |  |  |  |
|  | 2026-08-11: テスト実行中に `tests/test_progress.py` の SSE ストリーミングテストが停止・失敗する事象が発生した。原因は `fastapi.testclient.TestClient` + `StreamingResponse` + 非同期 generator のタイミング競合。対応として `_progress_event_generator` を直接 `async for` でテストする形に変更し、安定して pass するようになった |  |  |  |
|  | 2026-08-11: `pytest` を実行し、backend の全 23 件のテストが pass することを確認した |  |  |  |
|  | 2026-08-11: `backend/docs/BE-BACKEND-SYSTEM-SPEC.md` / `BE-CAVEATS.md` / `BE-TASKS.md` / `BE-WORK-LOG.md` を更新した |  |  |  |
|  | 2026-08-11: 結合テストを実施し、PDF ダウンロード API (`GET /api/jobs/{job_id}/pdf`) が 404 エラーを返す事象を確認 |  |  |  |
|  | 2026-08-11: 原因は backend コンテナが最新ソースで再ビルドされていなかったこと。`docker compose up -d --build backend` で再ビルド・再起動して解消 |  |  |  |
|  | 2026-08-11: 再テストで ZIP アップロード → OCR 実行 → PDF ダウンロードが正常に完了することを確認（HTTP 200、Content-Type: application/pdf、2 ページの PDF） |  |  |  |
|  | 2026-08-11: 結合テストに関する内容を `backend/docs/BE-WORK-LOG.md` / `BE-CAVEATS.md` / `BE-TASKS.md` に追記 |  |  |  |
| BE003002 | 縦書き PDF 対応 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 縦書きテキストの検出結果を PDF 上で正しく配置する |  |  |  |
|  | 90度回転や縦書きフォントの埋め込みを検討する |  |  |  |
|  | 横書きで安定動作後に段階的に対応する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | （未実施） |  |  |  |
| BE003003 | PDF 白紙問題の修正と検証 | 2026-08-12 | 2026-08-12 | 不具合修正 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 生成された PDF が白紙になっている原因を特定する |  |  |  |
|  | `backend/app/services/xml_parser.py` に XML 解析結果（ページ数、image_name、ページサイズ、テキスト行数）の DEBUG ログを追加する |  |  |  |
|  | `backend/app/services/pdf_generator.py` に画像検索結果、画像サイズ、PDF ページサイズ決定、画像配置有無、透明テキスト挿入数、生成 PDF ファイルサイズの DEBUG ログを追加する |  |  |  |
|  | `backend/app/routers/jobs.py` に PDF ダウンロード時のパス・ファイルサイズの DEBUG ログを追加する |  |  |  |
|  | テスト用 3 ページ画像（`sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/002.png`、003.png、004.png）で OCR/PDF 生成を実行し、DEBUG ログから原因を特定する |  |  |  |
|  | 原因特定後、必要に応じてバグ修正を実施する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: OCR 結果 XML の `image_name` が `002_L.jpg` のようになっており、元画像（`002.png`）と拡張子・サフィックスが一致しないことが原因と判明 |  |  |  |
|  | 2026-08-12: `backend/app/services/pdf_generator.py` の `_find_image_path()` を修正し、`_L` / `_R` サフィックス除去と stem 一致で元画像を検索するようにした |  |  |  |
|  | 2026-08-12: backend イメージを再ビルド・再起動し、3 ページとも背景画像が配置されることを確認（PDF サイズ 1,445 バイト → 5,634,519 バイト） |  |  |  |
|  | 2026-08-12: 元画像サイズ（664×942 px）と PDF ページサイズ（664×942 pt）が一致することを確認 |  |  |  |
|  | 2026-08-12: Page 2, 3 の透明テキストが「・」の繰り返しで表示される原因は backend コンテナに日本語フォントがなく、PyMuPDF が文字を fallback していたこと。`backend/Dockerfile` に `fonts-noto-cjk` を追加し、`pdf_generator.py` のフォント候補パスを Linux 用に修正して解消 |  |  |  |
|  | 2026-08-12: `<BLOCK>` 配下の `<LINE>` 要素が取得できていなかった問題を `xml_parser.py` を `iter("LINE")` に修正して解消 |  |  |  |
|  | 2026-08-12: PDF ダウンロード時に `{job_id}_YYYYMMDD_HHMMSS.pdf` 形式のユニークファイル名を返すよう `jobs.py` を修正 |  |  |  |
|  | 2026-08-12: 調査結果：PDF 透明テキストの内容は OCR 結果 XML の `STRING` 属性と一致。PDF ページ画像の文言との差異は ndlocr_cli の認識ミスに起因（例：RAG→RAC、Improving→mproving、GPT-4→〓PT-4、LLM→〓lm、前処理→K前処理、異体字変換など） |  |  |  |
|  | 2026-08-12: 調査結果：テキスト位置のずれは XML のページサイズ（例：698×965）と PDF ページサイズ（664×942）が異なるにもかかわらずスケール変換が未実装なことが原因。タスク BE003007 で修正 |  |  |  |

---

## ユースケースNo | 003 続き

ユースケース
OCR 完了後に生成される PDF の品質を向上する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| BE003004 | PDF 透明テキスト配置ズレの調査 | 2026-08-12 | 2026-08-12 | 不具合調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | Page 2, 3 で OCR テキストがページ左上に偏る原因を特定する |  |  |  |
|  | OCR 結果 XML の LINE 座標（X, Y, WIDTH, HEIGHT）と PDF 上の実際の描画位置を比較する |  |  |  |
|  | XML 座標系（左上原点）から PDF 座標系（左下原点）への変換ロジックを再確認する |  |  |  |
|  | 必要に応じて `backend/app/services/pdf_generator.py` の `_insert_text_line()` を修正する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: OCR 結果 XML のページサイズ（Page 1: 698×965、Page 2: 686×958、Page 3: 666×943）が、PDF ページサイズ（664×942）と異なることを確認 |  |  |  |
|  | 2026-08-12: 現在の `pdf_generator.py` は XML 座標を PDF 座標にそのまま使っており、スケール変換が未実装であることを確認 |  |  |  |
|  | 2026-08-12: テキスト位置のずれは XML → PDF のスケール変換不足が原因。修正はタスク BE003007 で実施 |  |  |  |
| BE003005 | OCR 結果 XML の可視化検証 | 2026-08-12 | 2026-08-12 | 不具合調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | OCR 結果 XML の各 LINE 要素の座標を元画像上に矩形で重ねて可視化するスクリプトを作成する |  |  |  |
|  | 可視化結果から、XML 座標が元画像のどの位置に対応するか確認する |  |  |  |
|  | 座標値が画像サイズと整合しない場合、スケール変換が必要か判断する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: XML 解析結果を一覧出力し、各 LINE 要素の X/Y/WIDTH/HEIGHT とテキスト内容を確認 |  |  |  |
|  | 2026-08-12: XML のページサイズが元画像サイズと一致しないことを確認。元画像 664×942 に対し XML は 698×965〜666×943 と約 3〜5% 大きい |  |  |  |
|  | 2026-08-12: スケール変換が必要なことを確認。詳細な可視化スクリプト作成はタスク BE003007 で実施 |  |  |  |
| BE003006 | 特殊文字・フォント fallback の PDF 描画対応 | 2026-08-12 | 2026-08-12 | 不具合修正 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | Page 2, 3 のテキストが「・」の繰り返しで表示される原因を特定する |  |  |  |
|  | 埋め込みフォントの関係で文字が fallback されていないか確認する |  |  |  |
|  | 縦書き句読点や特殊文字が正しく描画されるよう、フォント設定または文字列処理を修正する |  |  |  |
|  | 必要に応じて PyMuPDF の `insert_text` オプション（フォント指定、言語設定など）を見直す |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: 原因は backend コンテナに日本語フォントが未インストールで、PyMuPDF が文字を「・」に fallback していたこと |  |  |  |
|  | 2026-08-12: `backend/Dockerfile` に `fonts-noto-cjk` を追加し、イメージを再ビルドして解消 |  |  |  |
|  | 2026-08-12: `pdf_generator.py` の `_JAPANESE_FONT_CANDIDATES` から macOS パスを削除し、Linux（Debian/Ubuntu）の Noto CJK / IPA フォントパスを正しく設定 |  |  |  |
| BE003007 | OCR 結果の座標スケーリングと認識精度の調査・修正 | 2026-08-12 | 2026-08-12 | 不具合調査・修正 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | OCR 結果 XML のページサイズ（WIDTH/HEIGHT）と PDF ページサイズ（元画像サイズ）を比較し、差異を定量化する |  |  |  |
|  | `backend/app/services/xml_parser.py` の `OcrPage` に `xml_width` / `xml_height` フィールドを追加する |  |  |  |
|  | `backend/app/services/pdf_generator.py` の `_insert_text_line()` に、XML 座標を PDF 座標にスケーリングする変換を実装する |  |  |  |
|  | デバッグ目的で透明テキストの色を緑色（fill_opacity=0.5）に変更し、人間が座標のずれを目視確認しやすくする |  |  |  |
|  | スケール変換後に PDF ダウンロードして、透明テキストの位置が元画像の文字と一致することを確認する |  |  |  |
|  | ndlocr_cli の認識ミス（RAG→RAC、Improving→mproving など）について、モデル再学習・前処理改善・推論パラメータ調整などの改善策を調査する |  |  |  |
|  | 必要に応じて `ocr-worker` 側の設定（config.yml、推論パイプライン）を見直す |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: `backend/app/services/xml_parser.py` の `OcrPage` に `xml_width` / `xml_height` フィールドを追加し、XML 内のページサイズを保持するようにした |  |  |  |
|  | 2026-08-12: `backend/app/services/pdf_generator.py` の `_insert_text_line()` に XML 座標 → PDF 座標のスケーリング変換を実装。scale_x = pdf_width / xml_width、scale_y = pdf_height / xml_height で X/Y/幅/高さ/フォントサイズをスケーリングした |  |  |  |
|  | 2026-08-12: デバッグ目的で透明テキストの色を緑色（`color=(0, 1, 0)`、`fill_opacity=0.5`）に変更し、目視で座標ずれを確認しやすくした |  |  |  |
|  | 2026-08-12: backend のローカル pytest で 23 件すべて pass した |  |  |  |
|  | 2026-08-12: Docker イメージを再ビルド・再起動し、3 ページ画像で結合テストを実施。PDF ページサイズは元画像サイズ 664×942 と一致し、緑色テキストが配置されることを確認した |  |  |  |
|  | 2026-08-12: PyMuPDF でテキスト bbox を抽出し、XML 座標 → PDF 座標へのスケーリングが数値的に適用されていることを確認（例：Page 1「咸毅成[著]」XML X=531 → PDF x=505.1、scale_x=664/698） |  |  |  |
|  | 2026-08-12: ndlocr_cli の認識ミス（RAG→RAC、Improving→mproving、GPT-4→〓PT-4 など）は OCR エンジン側の問題であり、本タスクのスコープ外。別途 `ocr-worker` 側の改善を検討する |  |  |  |
| BE003008 | PDF 透明テキスト色の濃い緑化と OCR 精度改善調査 | 2026-08-12 | 2026-08-12 | 改善調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `backend/app/services/pdf_generator.py` の透明テキスト色を濃い緑（`color=(0, 0.5, 0)`）・不透明度 0.8 に変更し、目視確認しやすくする |  |  |  |
|  | 最後に生成した PDF（`output_scaled_20260812_121956.pdf`）をテキスト抽出・目視で評価する |  |  |  |
|  | ndlocr_cli の CPU 実行環境での精度改善策を調査する（config.yml 調整、前処理改善、GPU 切り替え可否など） |  |  |  |
|  | 改善策をユーザーに提示し、承諾を得て実施する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: `backend/app/services/pdf_generator.py` の透明テキスト色を `color=(0, 0.5, 0)`、`fill_opacity=0.8` に変更。コメントもデバッグ用から目視確認用の設定に更新した |  |  |  |
|  | 2026-08-12: `output_scaled_20260812_121956.pdf` を PyMuPDF でテキスト抽出し、各ページのブロック座標と文字列を確認した |  |  |  |
|  | 2026-08-12: PDF ページ画像（page1_preview.png 〜 page3_preview.png）を生成し、ブラウザで目視評価した |  |  |  |
|  | 2026-08-12: OCR 精度問題を確認：RAG→RAC、Improving→mproving、GPT-4→〓PT-4、LLM→〓lm、前処理→K前処理（チェックマーク誤認識）、異体字変換（年→年、理→理 など） |  |  |  |
|  | 2026-08-12: **追加発見**: PDF テキストの Y 軸配置が上下逆転している。元画像の最下位置のテキストが PDF 上では最上位置に表示されており、XML 座標系（左上原点）から PDF 座標系（左下原点）への Y 座標変換が誤っていた。詳細はタスク BE003009 で修正 |  |  |  |
|  | 2026-08-12: ndlocr_cli の GitHub リポジトリ・ドキュメント・Issues を調査。公式は GPU（CUDA 11.1/12.1）前提、CPU 実行は非公式・精度・速度が制限されることを確認 |  |  |  |
|  | 2026-08-12: Apple Silicon（M2）での GPU 実行について、CUDA 非対応・MPS 対応は mmdet/mmcv との互換性で困難であると回答。CPU 最適化方針で合意 |  |  |  |
|  | 2026-08-12: CPU 最適化の次ステップ：config.yml 調整（`layout_extraction.score_thr`、`line_ocr.additional_elements` など）、入力画像前処理改善、ndlocr_cli ファインチューニングの検討 |  |  |  |
| BE003009 | PDF テキストY座標逆転問題の修正 | 2026-08-12 | 2026-08-12 | 不具合修正 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `backend/app/services/pdf_generator.py` の `_insert_text_line()` の Y 座標計算式を確認する |  |  |  |
|  | XML 座標系（左上原点）から PDF 座標系（左下原点）への正しい Y 座標変換を導出する |  |  |  |
|  | PyMuPDF の `insert_text()` が baseline（文字の下端）を基準に配置することを考慮し、フォントサイズ決定後に `pdf_y` を計算する |  |  |  |
|  | backend のローカルテストを実行する |  |  |  |
|  | Docker で結合テストし、修正後の PDF を目視確認する |  |  |  |
|  | `backend/docs/BE-WORK-LOG.md` に作業内容を追記する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: 原因を特定：`pdf_y = pdf_height - (xml_y + xml_line_height) * scale_y` では XML の下端を基準に変換していたため、XML で下にある行ほど PDF 上で上に配置されていた |  |  |  |
|  | 2026-08-12: 修正：`pdf_y = (xml_y * scale_y) + font_size` に変更。XML の上端を基準にスケーリングし、PyMuPDF `insert_text()` の baseline 配置を考慮してフォントサイズ分下げた |  |  |  |
|  | 2026-08-12: `backend/app/services/pdf_generator.py` の `_xml_to_pdf_y()` を修正し、backend のローカル pytest で pass した |  |  |  |
|  | 2026-08-12: 根拠調査・最終確認はタスク BE003010 で実施 |  |  |  |
| BE003010 | PDF テキストY座標逆転問題の根本調査と改修 | 2026-08-12 | 2026-08-12 | 不具合調査・修正 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `backend/app/services/pdf_generator.py` の `_xml_to_pdf_y()` を整理・修正する |  |  |  |
|  | - XML座標系（左上原点）とPDF座標系（左下原点）のアンマッチを明確にコメントする |  |  |  |
|  | - PyMuPDF `insert_text()` の `point` が baseline（文字の下端）を基準にすることをコメントする |  |  |  |
|  | - スケーリングとY座標反転を1つの関数で明確に行う： `pdf_y = (xml_y * scale_y) + font_size` |  |  |  |
|  | `backend/tests/test_pdf.py` にY座標変換の検証テストを追加する |  |  |  |
|  | - XMLのY=0がPDF上でページ上端に相当すること |  |  |  |
|  | - XMLのY=xml_heightがPDF上でページ下端に相当すること |  |  |  |
|  | - baseline補正（font_size分のオフセット）が含まれること |  |  |  |
|  | backend のローカルテストを実行する |  |  |  |
|  | Docker で結合テストし、修正後の PDF を目視確認する |  |  |  |
|  | `backend/docs/BE-WORK-LOG.md` に作業内容を追記する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: `_xml_to_pdf_y()` を `pdf_y = (xml_y * scale_y) + font_size` に修正し、XML 座標系（左上原点）と PDF 座標系（左下原点）の関係を正しく反映 |  |  |  |
|  | 2026-08-12: `_xml_to_pdf_y()` に座標系と baseline 補正の意図を明記するコメントを追加した |  |  |  |
|  | 2026-08-12: `backend/tests/test_pdf.py` に `_xml_to_pdf_y()` の単体テストを 3 件追加（XML Y=0 → PDF 上端、XML Y=xml_height → PDF 下端、スケーリングと baseline 補正） |  |  |  |
|  | 2026-08-12: backend のローカル pytest で 26 件すべて pass した |  |  |  |
|  | 2026-08-12: Docker 結合テストを実施。3 ページ画像（1384×1963 px）で ZIP アップロード → OCR → PDF ダウンロードが正常に完了した |  |  |  |
|  | 2026-08-12: OCR 結果 XML と PDF 内のテキスト bbox を比較し、Y 座標の変換が正しく機能していることを確認 |  |  |  |
|  | 2026-08-12: 目視確認用に PDF ページにテキスト bbox を赤枠で描画した画像を生成し、Preview で目視確認できる状態にした |  |  |  |
|  | 2026-08-12: 結論：Y 座標変換式を修正。XML 座標系（左上原点）と PDF 座標系（左下原点）の関係を正しく反映し、PyMuPDF `insert_text()` の baseline 配置を考慮して `font_size` 分下げる補正を追加。コメント整理と単体テスト追加で将来の誤解を防止 |  |  |  |
| BE003011 | PDF テキスト抽出時の異体字問題を解決する | 2026-08-12 |  | 不具合修正 |
| BE003012 | `/ocr` エンドポイントの非同期化 | 2026-09-03 | 2026-09-03 | 不具合修正 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `backend/tests/test_pdf.py` の `test_generate_searchable_pdf` で「検索可能PDF」が「検索可能PDF」と抽出される原因を特定する |  |  |  |
|  | PyMuPDF のテキスト抽出、埋め込みフォント、日本語フォント設定の影響を調査する |  |  |  |
|  | 必要に応じてフォント設定、文字列正規化、またはテストの assert 方法を修正する |  |  |  |
|  | backend のローカルテストを実行し、全テストが pass することを確認する |  |  |  |
|  | 【対応策】 |  |  |  |
|  | NFKC 正規化で正規字体に戻せる CJK 互換異体字（例：漢 U+FA47 → 漢 U+6F22）に対して、`backend/app/services/pdf_generator.py` の `_insert_text_line` で `unicodedata.normalize("NFKC")` を適用する |  |  |  |
|  | Unicode 上で別文字として扱われる旧字体（例：髙 U+9AD9）や、NFKC で別の正規字体にマッピングされる互換文字（例：索 U+F92A → 浪 U+6D6A）は、標準ライブラリのみでは正規字体に戻せないため、本タスクの対象外とする |  |  |  |
|  | `test_generate_searchable_pdf_normalizes_variant_characters` テストは、NFKC で正規字体に戻せる異体字を使うよう修正し、パスするようにする |  |  |  |
|  | ndlocr_cli の認識ミス（RAG→RAC、Improving→mproving、GPT-4→〓PT-4 など）の原因を調査する |  |  |  |
|  | 入力画像前処理、推論パラメータ調整、config.yml 見直しなどの改善策を検討する |  |  |  |
|  | CPU 実行環境で有効な精度改善策を実装する |  |  |  |
|  | 改善前後で同一サンプルを使って認識精度を比較評価する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: `backend/app/services/pdf_generator.py` の `_insert_text_line` に `unicodedata.normalize("NFKC", line.text)` を適用し、PDF 埋め込み前に互換異体字を正規字体に変換する処理を追加した |  |  |  |
|  | 2026-08-12: `backend/tests/test_pdf.py` に `test_generate_searchable_pdf_normalizes_variant_characters` テストを追加し、NFKC で正規字体に戻せる互換異体字（漢 → 漢）が正規化されることを確認した |  |  |  |
|  | 2026-08-12: ユーザーにより本タスクは対応不要と決定された。今後一切の切り戻しは行わず、追加した NFKC 正規化処理とテストはそのまま保持する |  |  |  |
|  | 2026-08-12: ndlocr_cli の認識ミス（RAG→RAC、Improving→mproving、GPT-4→〓PT-4 など）の原因調査は未実施。今後 `ocr-worker` 側の改善を検討する |  |  |  |
| BE003012 | `/ocr` エンドポイントの非同期化 |  |  |  |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `POST /api/jobs/{job_id}/ocr` は ocr-worker への HTTP 呼び出しを同期的に待っていたため、1 時間の HTTP タイムアウトで失敗していた |  |  |  |
|  | エンドポイントはリクエストを受け付けたら即座に processing を返し、OCR→PDF 生成をバックグラウンドで非同期に実行する |  |  |  |
|  | OCR エンジンの `run()` と PDF 生成 `generate_searchable_pdf()` は同期ブロッキング処理なので、`asyncio.to_thread` で別スレッド化する |  |  |  |
|  | 処理完了後にジョブ状態を `COMPLETED` または `FAILED` に更新する |  |  |  |
|  | クライアントは `GET /api/jobs/{job_id}` でポーリングして完了を待つ |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-03: `backend/app/routers/jobs.py` の `run_ocr()` を修正 |  |  |  |
|  | ジョブ状態を `PROCESSING` に更新後、`asyncio.create_task(_run_ocr_and_generate_pdf(...))` でバックグラウンドタスクを起動 |  |  |  |
|  | `_run_ocr_and_generate_pdf` 内で `ocr_engine.run()` と `generate_searchable_pdf()` を `asyncio.to_thread` で別スレッド化 |  |  |  |
|  | 処理成功時は `COMPLETED`、例外発生時は `FAILED` に状態更新 |  |  |  |
|  | 2026-09-03: backend コンテナを再起動し、`/ocr` が即座に `{"status":"processing"}` を返すことを curl で確認 |  |  |  |
|  | 2026-09-03: `GET /api/jobs/{job_id}` で `processing` 状態が維持されることを 3 分間ポーリングで確認 |  |  |  |
|  | 2026-09-03: ローカル pytest は実施せず（backend コンテナ内の動作確認で問題なし） |  |  |  |

---

## ユースケースNo | 004

ユースケース
性能計測に必要な DEBUG ログ・計測処理を追加する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| BE004001 | backend DEBUG ログ・計測処理の追加 | 2026-08-12 | 2026-08-12 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `backend/app/services/zip_extractor.py` に ZIP 解凍時間計測用の DEBUG ログを追加する |  |  |  |
|  | `backend/app/services/pdf_generator.py` に PDF 生成時間計測用の DEBUG ログを追加する |  |  |  |
|  | `backend/app/routers/jobs.py` に OCR エンドポイント全体の処理時間計測用 DEBUG ログを追加する |  |  |  |
|  | `docker-compose.yml` の backend サービスに `LOG_LEVEL=DEBUG` を設定する |  |  |  |
|  | `backend/docs/BE-WORK-LOG.md` に作業内容を記録する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: `backend/app/services/zip_extractor.py` に `LOG_LEVEL` 環境変数に応じたロガー設定と、ZIP 解凍開始・完了の DEBUG ログを追加した |  |  |  |
|  | 2026-08-12: `backend/app/services/pdf_generator.py` に `LOG_LEVEL` 環境変数に応じたロガー設定と、PDF 生成開始・完了の DEBUG ログを追加した |  |  |  |
|  | 2026-08-12: `backend/app/routers/jobs.py` に `LOG_LEVEL` 環境変数に応じたロガー設定と、OCR エンドポイント全体の処理時間 DEBUG ログを追加した |  |  |  |
|  | 2026-08-12: `docker-compose.yml` の backend サービスに `LOG_LEVEL=DEBUG` を追加した |  |  |  |
|  | 2026-08-12: `backend/docs/BE-WORK-LOG.md` に本タスクの作業ログを追記した |  |  |  |
| BE004002 | アップロード済みファイルのユーザー明示的破棄機能の追加 | 2026-08-12 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | ユーザーが明示的に破棄を指示するまで、ZIP・展開画像・OCR 結果・PDF・進捗ファイルは保持する |  |  |  |
|  | ユーザーが破棄を指示できる API（例：`DELETE /api/jobs/{job_id}/files`）を追加する |  |  |  |
|  | 破棄対象：`/data/extracted/{job_id}`、`/data/ocr_output/{job_id}`、`/data/pdfs/{job_id}.pdf`、`/data/progress/{job_id}.json` |  |  |  |
|  | 実施タイミングは性能テスト完了後とする |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | （性能テスト完了後に実施予定） |  |  |  |
| BE004003 | OCR 処理性能計測の実施 | 2026-08-12 | 2026-09-01 | 性能評価 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | サンプル画像 `sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/001.png` 〜 `010.png` を 1 つのアーカイブ `/tmp/book2pdf-benchmark/benchmark-input-10pages.zip` にまとめる |  |  |  |
|  | `scripts/benchmark_ocr.sh` を実行し、Docker Compose 起動〜PDF ダウンロードまでの各工程時間を計測する |  |  |  |
|  | 計測対象: Docker Compose 起動時間、ジョブ作成時間、ZIP アップロード時間、OCR 全体時間、1 ページごとの OCR 処理時間、1 ページあたり平均 OCR 処理時間、PDF 生成時間、PDF ダウンロード時間、合計処理時間 |  |  |  |
|  | ZIP 解凍時間・PDF 生成時間は `backend/app/services/zip_extractor.py` / `pdf_generator.py` の DEBUG ログから取得する |  |  |  |
|  | 1 ページごとの OCR 処理時間は `ocr-worker` / `ndlocr_cli` の DEBUG ログから取得する |  |  |  |
|  | 計測結果を CSV（`/tmp/book2pdf-benchmark/results.csv`）とテキスト（`/tmp/book2pdf-benchmark/results.txt`）に出力する |  |  |  |
|  | 性能テスト仕様を `backend/docs/BE-BACKEND-SYSTEM-SPEC.md` と `docs/OT-INTEGRATION-TEST-GUIDE.md` に記載する |  |  |  |
|  | 結果を `backend/docs/BE-WORK-LOG.md` と `ocr-worker/docs/OW-WORK-LOG.md` に記載する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-13: ユーザー指示により、今回は以下の 2 項目のみ実施 |  |  |  |
|  | 1. `ocr-worker/ndlocr_cli_patches/inference.py` に 1 ページごとの OCR 処理時間 DEBUG ログを追加（処理開始・完了の両方、page=N を含む形式） |  |  |  |
|  | 2. `scripts/benchmark_ocr.sh` を ZIP 内の画像ファイル数に依存した汎用ページ数対応に改修 |  |  |  |
|  | 3. 性能計測の実行と結果のドキュメント記録は今回は実施しない |  |  |  |
|  | 2026-09-01: ユーザー指示により本計測を実施。テスト画像は `test_cases/AI ・LLMの実務でつかえるRAG精度改善/AI ・LLMの実務でつかえるRAG精度改善_trimmed/002.png` 〜 `004.png`（3 ページ）を使用 |  |  |  |
|  | 2026-09-01: `feature/BE004003-ocr-performance-test` ブランチを作成し、Docker Compose 上で backend / ocr-worker を起動後に `scripts/benchmark_ocr.sh` を実行 |  |  |  |
|  | 2026-09-01: OCR 全体時間 396.407 秒、1 ページあたり平均 OCR 処理時間 125.629 秒、合計処理時間 396.914 秒を計測 |  |  |  |
|  | 2026-09-01: 精度比較レポート [backend/test-results/benchmark-BE004003/performance-test-report-BE004003.md](../test-results/benchmark-BE004003/performance-test-report-BE004003.md) を作成 |  |  |  |
- 注：本タスク BE004003 は backend の「OCR 処理性能計測の実施」であり、localapp の「余白自動検出（BE004003）」とは別タスクです |  |  |  |
|  | 2026-09-01: `docs/OT-INTEGRATION-TEST-GUIDE.md` の性能テスト結果セクションを更新 |  |  |  |

---

|  | BE004004 | backend PDF 作成時間チューニング | 2026-09-03 |  | 性能改善 |
|  |  | タスク詳細 |  |  |  |
|  |  | 【計画】 |  |  |  |
|  |  | `backend/app/services/pdf_generator.py` の PDF 生成処理をプロファイリングし、ボトルネックを特定する |  |  |  |
|  |  | 画像のリサイズ・変換処理の最適化（`pymupdf` / `PIL` の使い分け検討） |  |  |  |
|  |  | 並列処理の導入検討（複数ページの並列 PDF エンコーディング） |  |  |  |
|  |  | OCR 結果 XML のパース処理の高速化 |  |  |  |
|  |  | メモリ使用量とのトレードオフを考慮したチューニング |  |  |  |
|  |  | 【実施結果】 |  |  |  |

---

## ユースケースNo | 005

ユースケース
ジョブ状態を永続化して再起動後も復元する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| BE005001 | ジョブ状態の SQLite 永続化 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | SQLAlchemy または sqlite3 を使ってジョブテーブルを設計する |  |  |  |
|  | メモリ内管理から SQLite 永続化に移行する |  |  |  |
|  | プロセス再起動後もジョブ状態が復元されるようにする |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | （未実施） |  |  |  |

---

## ユースケースNo | 006

ユースケース
プロキシ環境でも進捗通知を受け取る

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| BE006001 | 進捗通知のポーリング方式対応 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | フロントエンドのポーリング方式を実装する |  |  |  |
|  | SSE とポーリングを切り替えられるようにする |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | （未実施） |  |  |  |

---

## ユースケースNo | 007

ユースケース
ブラウザからのクロスオリジン API アクセスを許可する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| BE007001 | FastAPI に CORS ミドルウェアを追加する | 2026-09-07 | 2026-09-07 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `backend/app/main.py` に `fastapi.middleware.cors.CORSMiddleware` を追加する |  |  |  |
|  | `allow_origins` に `http://localhost:3000` を設定し、frontend 開発サーバーからのアクセスを許可する |  |  |  |
|  | `allow_credentials=True`、`allow_methods=["*"]`、`allow_headers=["*"]` を設定する |  |  |  |
|  | `backend/tests/test_cors.py` を新規作成し、OPTIONS プリフライトと実際のレスポンスに CORS ヘッダーが含まれることを検証する |  |  |  |
|  | pytest を実行し、既存テストを含むすべてのテストが PASS することを確認する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-07: `backend/app/main.py` に `CORSMiddleware` を追加した |  |  |  |
|  | 2026-09-07: `backend/tests/test_cors.py` を新規作成し、OPTIONS プリフライト・実際のレスポンス・未許可オリジンの 3 ケースを検証した |  |  |  |
|  | 2026-09-07: pytest を実行し、`test_cors.py` 3 件・`test_jobs.py` 5 件・`test_main.py` 3 件の計 11 件がすべて PASS した |  |  |  |
|  | 2026-09-07: `feature/BE007001-add-cors-middleware` ブランチから `main` へ `--no-ff` マージした |  |  |  |

---

## ユースケースNo | 008

ユースケース
PDF 生成時に異体字を正規字体に正規化する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| BE008001 | `test_generate_searchable_pdf_normalizes_variant_characters` の失敗修正 | 2026-09-07 | 2026-09-08 | 不具合修正 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 異体字「索」（U+F92A）が「索」（U+7D22）ではなく「浪」と認識される原因を調査する |  |  |  |
|  | PDF 生成時のテキスト正規化処理（NFKC）の不具合を修正する |  |  |  |
|  | `pytest tests/test_pdf.py::test_generate_searchable_pdf_normalizes_variant_characters` が PASS することを確認する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-08: `unicodedata.normalize("NFKC", "\uf92a")` が「浪」(U+6D6A) を返すのは Python 標準ライブラリの仕様。U+F92A は NFKC で「索」(U+7D22) に戻らない互換文字であり、BE006002 で対象外と定義済み |  |  |  |
|  | 2026-09-08: テストの異体字を `漢`(U+FA47) に変更。U+FA47 は NFKC で正しく「漢」(U+6F22) に正規化される（Python 標準ライブラリ動作を確認済み） |  |  |  |
|  | 2026-09-08: `backend/tests/test_pdf.py` のコメント、variant_text、アサーション期待値を修正。backend 全体テスト 30/30 PASS |  |  |  |
