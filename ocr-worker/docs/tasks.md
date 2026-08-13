# タスク管理

本ファイルは、ocr-worker のタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する

---

## ユースケースNo | 001

ユースケース
ndlocr_cli を実行可能な Docker コンテナ（ocr-worker）を構築する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 001001 | ndlocr_cli 実行環境の Docker コンテナ化 | 2026-08-11 | 2026-08-11 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | ndlocr_cli リポジトリの構成・submodule・公式 Dockerfile を調査する |  |  |  |
|  | ocr-worker/Dockerfile を作成し、ndlocr_cli を Python パッケージとして import できるようにする |  |  |  |
|  | docker-compose.yml を作成・更新し、backend / ocr-worker コンテナを連携させる |  |  |  |
|  | コンテナ内で `from cli.core import OcrInferrer` が成功することを確認する |  |  |  |
|  | サンプル画像で OCR を実行し、XML 出力形式を確認する |  |  |  |
|  | ocr-worker/docs/work_log.md / caveats.md / ocr-worker-system-spec.md を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: ndlocr_cli リポジトリの構成・submodule・公式 Dockerfile を調査 |  |  |  |
|  | 2026-08-11: ocr-worker/Dockerfile を新規作成（python:3.10-slim ベース、CPU 実行用） |  |  |  |
|  | 2026-08-11: プロジェクトルートの docker-compose.yml を新規作成（backend / ocr-worker 連携） |  |  |  |
|  | 2026-08-11: Docker Desktop の起動を確認（v29.6.2） |  |  |  |
|  | 2026-08-11: ocr-worker/docs/work_log.md / caveats.md / ocr-worker-system-spec.md を更新 |  |  |  |
|  | 2026-08-11: backend/docs/backend-system-spec.md を更新 |  |  |  |
|  | 2026-08-11: コンテナビルドに成功（`docker compose build ocr-worker`） |  |  |  |
|  | 2026-08-11: コンテナ内で `from cli.core import OcrInferrer` の import に成功 |  |  |  |
|  | 2026-08-11: `GutterDetector` 経由で `init_detector` の CPU 動作を確認 |  |  |  |
|  | 2026-08-11: サンプル画像で OCR を実行し、XML / txt 出力を確認 |  |  |  |
|  | 2026-08-11: 発生した問題に対して Dockerfile を修正（mmdet init_detector 引数、text_recognition_lightning callbacks / trainer、KyTea ソースビルド） |  |  |  |
| 001002 | ocr-worker OCR API の実装 | 2026-08-11 | 2026-08-11 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `ocr-worker/app/main.py` を新規作成し、OCR 実行用 FastAPI アプリケーションを実装する |  |  |  |
|  | `POST /ocr` エンドポイントを提供し、入力ディレクトリ・出力ディレクトリ・config パスを受け取る |  |  |  |
|  | `OcrInferrer` を使って OCR を実行し、テキスト・XML パス・成否を返す |  |  |  |
|  | `ocr-worker/Dockerfile` を更新し、fastapi / uvicorn / httpx をインストールする |  |  |  |
|  | `docker-compose.yml` で ocr-worker の起動コマンドを FastAPI サーバーに変更する |  |  |  |
|  | `ocr-worker/docs/work_log.md` / `caveats.md` / `ocr-worker-system-spec.md` を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: `ocr-worker/app/main.py` を新規作成（FastAPI + `POST /ocr` + `GET /health`） |  |  |  |
|  | 2026-08-11: `ocr-worker/Dockerfile` を更新（fastapi / uvicorn / python-multipart の追加、Uvicorn 起動） |  |  |  |
|  | 2026-08-11: `docker-compose.yml` を更新（共有ボリューム `/data/extracted`、ヘルスチェック、ポート 8001 マッピング） |  |  |  |
|  | 2026-08-11: `ocr-worker` コンテナを再ビルド・再起動 |  |  |  |
|  | 2026-08-11: `http://localhost:8001/health` で `{"status":"ok"}` を確認 |  |  |  |
|  | 2026-08-11: backend からサンプル画像 2 枚で OCR テストを実施し、ジョブ状態が `completed` になることを確認 |  |  |  |
|  | 2026-08-11: 結合テストで 2 回目以降の OCR リクエストで `GlobalHydra is already initialized` エラーが発生したことを確認 |  |  |  |
|  | 2026-08-11: `ocr-worker/app/main.py` の `infer` 関数で `GlobalHydra.instance().is_initialized()` を確認し、初期化済みの場合は `clear()` してから `initialize()` するように修正 |  |  |  |
|  | 2026-08-11: 修正後の ocr-worker コンテナを再ビルド・再起動し、複数回の OCR リクエストが正常に完了することを確認 |  |  |  |
|  | 2026-08-11: `ocr-worker/docs/work_log.md` / `caveats.md` / `ocr-worker-system-spec.md` を更新 |  |  |  |

---

## ユースケースNo | 002

ユースケース
性能計測に必要な DEBUG ログ・計測処理を追加する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 002001 | ocr-worker DEBUG ログ・計測処理の追加 | 2026-08-12 | 2026-08-12 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `ocr-worker/app/main.py` に `LOG_LEVEL` 環境変数に応じたロガー設定と、OCR 処理開始・完了の DEBUG ログを追加する |  |  |  |
|  | OCR 処理全体の所要時間を DEBUG ログで出力する |  |  |  |
|  | `docker-compose.yml` の ocr-worker サービスに `LOG_LEVEL=DEBUG` を設定する |  |  |  |
|  | `ocr-worker/docs/work_log.md` に作業内容を記録する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: `ocr-worker/app/main.py` に `LOG_LEVEL` 環境変数に応じたロガー設定と、OCR 処理開始・完了・所要時間の DEBUG ログを追加した |  |  |  |
|  | 2026-08-12: `docker-compose.yml` の ocr-worker サービスに `LOG_LEVEL=DEBUG` を追加した |  |  |  |
|  | 2026-08-12: `ocr-worker/docs/work_log.md` に本タスクの作業ログを追記した |  |  |  |
| 002002 | OCR 処理性能計測の実施 | 2026-08-12 |  | 性能評価 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | サンプル画像 001.png〜010.png を 1 つのアーカイブ `benchmark-input-10pages.zip` にまとめる |  |  |  |
|  | backend から 1 回のジョブで 10 ページ ZIP の OCR 処理を呼び出し、ndlocr_cli の DEBUG ログからページごとの処理時間を計測する |  |  |  |
|  | ndlocr_cli の既存ログにページごとの処理時間が出力されていなければ、ソースコードを修正して DEBUG ログを追加する |  |  |  |
|  | ページごとの OCR 処理時間を `ocr-worker/docs/work_log.md` に記載する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | （性能テスト実行後に記載予定） |  |  |  |

---

## ユースケースNo | 003

ユースケース
OCR 読み取り精度向上

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 003001 | 現状 OCR 認識精度の再測定 | 2026-08-13 | 2026-08-13 | 調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 目的：OCR 精度向上施策を検討する前に、現状の ndlocr_cli（CPU 実行）の認識精度を定量的・定性的に把握する |  |  |  |
|  | 1. 環境クリーンアップ：コンテナ内 `/data/extracted/*`、`/data/ocr_output/*`、`/data/pdfs/*` と、ホスト側 `/tmp/book2pdf-*`、作業ディレクトリ内テスト出力を削除する |  |  |  |
|  | 2. テスト用 ZIP の確認：既存の `benchmark-ocr-003001.zip` を使用し、含まれる画像を `unzip -l` で確認する |  |  |  |
|  | 3. Docker Compose 起動：`backend` / `ocr-worker` コンテナを最新イメージで起動する |  |  |  |
|  | 4. OCR 実行：backend API から ZIP をアップロードし、backend → ocr-worker 経由で OCR を実行する。ジョブが `completed` になるまで待機する |  |  |  |
|  | 5. 成果物取得：ocr-worker 出力の XML ファイル、テキストファイル、backend 生成 PDF をホスト側にコピーする |  |  |  |
|  | 6. 精度解析：元画像と OCR 結果テキストを比較し、英数字・記号・漢字・異体字などの認識ミスを一覧化する。定量的には CER（Character Error Rate）を算出し、目視確認も併用する |  |  |  |
|  | 7. ドキュメント記録：測定結果を `ocr-worker/docs/work_log.md` / `backend/docs/work_log.md` に記載し、本タスクの【実施結果】欄に追記する |  |  |  |
|  | ### 詳細実施手順 |  |  |  |
|  | #### 1. 環境クリーンアップ |  |  |  |
|  | ```bash |  |  |  |
|  | cd /Users/hisao/Documents/work4/sakura/book2pdf |  |  |  |
|  | docker compose exec backend rm -rf /data/extracted/* /data/ocr_output/* /data/pdfs/* |  |  |  |
|  | docker compose exec ocr-worker rm -rf /data/ocr_output/* /data/extracted/* |  |  |  |
|  | rm -rf /tmp/book2pdf-* |  |  |  |
|  | ``` |  |  |  |
|  | #### 2. テスト用 ZIP の確認 |  |  |  |
|  | ```bash |  |  |  |
|  | unzip -l benchmark-ocr-003001.zip |  |  |  |
|  | ``` |  |  |  |
|  | #### 3. Docker Compose 起動 |  |  |  |
|  | ```bash |  |  |  |
|  | docker compose up -d --build |  |  |  |
|  | ``` |  |  |  |
|  | #### 4. OCR 実行 |  |  |  |
|  | ```bash |  |  |  |
|  | JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id') |  |  |  |
|  | curl -s -X POST -F "file=@benchmark-ocr-003001.zip;type=application/zip" http://localhost:8000/api/jobs/$JOB_ID/upload | jq . |  |  |  |
|  | curl -s --max-time 1800 -X POST http://localhost:8000/api/jobs/$JOB_ID/ocr | jq . |  |  |  |
|  | curl -s http://localhost:8000/api/jobs/$JOB_ID | jq . |  |  |  |
|  | ``` |  |  |  |
|  | #### 5. 成果物取得 |  |  |  |
|  | ```bash |  |  |  |
|  | # ジョブ情報から output_dir と pdf_path を特定 |  |  |  |
|  | curl -s http://localhost:8000/api/jobs/$JOB_ID | jq . |  |  |  |
|  | # 例：ocr-worker 出力をホストにコピー |  |  |  |
|  | docker compose cp ocr-worker:/data/ocr_output/<job_dir>/ ./ocr-results-003001/ |  |  |  |
|  | docker compose cp backend:/data/pdfs/<pdf_file> ./ocr-results-003001/ |  |  |  |
|  | ``` |  |  |  |
|  | #### 6. 精度解析 |  |  |  |
|  | - 目視確認：元画像と OCR 結果テキスト（`_main.txt`, `_ruby.txt`, XML）を照合し、英数字・記号・漢字・異体字の誤認識を一覧化 |  |  |  |
|  | - 定量的評価：正解テキストがあれば CER を算出。ない場合は認識文字数に対する誤認識箇所数でミス率を算出 |  |  |  |
|  | ```bash |  |  |  |
|  | # 例：CER 計算スクリプト |  |  |  |
|  | python scripts/compare_ocr_accuracy.py --ground-truth ./ground-truth-003001.txt --ocr ./ocr-results-003001/<job_dir>/txt/<page>_main.txt |  |  |  |
|  | ``` |  |  |  |
|  | #### 7. ドキュメント記録 |  |  |  |
|  | - `ocr-worker/docs/work_log.md` に測定結果を記載 |  |  |  |
|  | - `ocr-worker/docs/tasks.md` の 003001【実施結果】欄に追記 |  |  |  |
|  | - 必要に応じて `backend/docs/work_log.md` にも記載 |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-13: `benchmark-ocr-003001.zip`（002.png, 003.png, 004.png）を使用して再測定を実施 |  |  |  |
|  | 2026-08-13: ジョブ ID `aca976fb-db10-47f1-847e-97ecf9b38ae5` で OCR を実行し、status: "completed" となったことを確認 |  |  |  |
|  | 2026-08-13: ocr-worker 出力（XML, `_main.txt`）と backend 生成 PDF を `ocr-results-003001/` に取得 |  |  |  |
|  | 2026-08-13: 認識精度レポート `ocr-results-003001/ocr-accuracy-report-003001.md` を新規作成 |  |  |  |
|  | 2026-08-13: 全体文字数約 1,327 文字、「〓」出現 5 回、明らかな誤認識箇所 002.png で約 7 箇所、003.png で約 5 箇所、004.png で約 8 箇所を確認 |  |  |  |
|  | 2026-08-13: 推定 CER は約 1〜3%（表紙ページはより高い） |  |  |  |
|  | 2026-08-13: 主要な誤認識パターンとして「英数字頭文字」「記号」「漢字の部品類似」「異体字・旧字体」「語尾・助詞」を特定 |  |  |  |
|  | 2026-08-13: XML の CONF 値が 0.998〜1.000 と高いにもかかわらず、実際には明らかな誤認識が含まれることを確認 |  |  |  |
|  | 2026-08-13: 精度向上の方向性として「入力画像前処理」「config.yml パラメータ調整」「推論パイプライン見直し」「後処理」を整理 |  |  |  |
|  | 2026-08-13: `ocr-worker/docs/work_log.md` に本タスクの作業ログを追記 |  |  |  |
| 003002 | 入力画像前処理の効果検証 | 2026-08-13 | 2026-08-13 | 改善調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 目的：003001 で特定した誤認識パターン（英数字頭文字・記号・漢字部品類似）に対し、入力画像前処理の効果を定量的に検証する |  |  |  |
|  | 対象データ：`benchmark-ocr-003001.zip`（002.png, 003.png, 004.png）を再利用する |  |  |  |
|  | 前処理は Python スクリプト（Pillow / OpenCV）で実装し、backend へ ZIP アップロードする前に適用する |  |  |  |
|  | 評価指標：「〓」出現数、明らかな誤認識箇所数、推定 CER、処理時間 |  |  |  |
|  | 実施順序と比較パターン： |  |  |  |
|  | 1. baseline（前処理なし） ※003001 と同一条件のため、本タスクでは再実行せず `ocr-results-003001/` の結果を比較基準として使用する |  |  |  |
|  | 2. sharpen_light（軽度シャープニング） |  |  |  |
|  | 3. sharpen_light_upscale_2x（2 倍アップスケーリング＋軽度シャープニング） |  |  |  |
|  | 4. contrast_gamma（コントラスト強調＋ガンマ補正） |  |  |  |
|  | 5. contrast_gamma_sharpen_light（コントラスト強調＋ガンマ補正＋軽度シャープニング） |  |  |  |
|  | なお、denoise（ノイズ除去）は機械的スキャンでありノイズがない前提で、今回は実施しない |  |  |  |
|  | 各パターンで OCR を実行し、結果を `ocr-results-003002/` に保存する（baseline は 003001 の結果を流用） |  |  |  |
|  | 各ステップごとに結果を報告し、次のパターンを実施するかを確認する |  |  |  |
|  | 最も効果的な前処理パターンを選定し、`ocr-worker/docs/work_log.md` / `ocr-worker/docs/tasks.md` に記録する |  |  |  |
|  | ### 詳細実施手順 |  |  |  |
|  | #### 1. 前処理スクリプトの作成 |  |  |  |
|  | `scripts/preprocess_image.py` を新規作成し、ZIP 内画像に対して以下の前処理を適用できるようにする |  |  |  |
|  | - baseline |  |  |  |
|  | - sharpen_light |  |  |  |
|  | - sharpen_light_upscale_2x |  |  |  |
|  | - contrast_gamma |  |  |  |
|  | - contrast_gamma_sharpen_light |  |  |  |
|  | - denoise（今回は実施しないがスクリプトとしては用意しておく） |  |  |  |
|  | #### 2. 前処理パターンの定義 |  |  |  |
|  | - baseline：前処理なし（比較基準） |  |  |  |
|  | - sharpen_light：軽度シャープニング。輪郭を鮮明化し、英数字・漢字部品類似誤認識を抑制する |  |  |  |
|  | - sharpen_light_upscale_2x：2 倍アップスケーリング＋軽度シャープニング。文字サイズを大きくしつつ輪郭を補強する |  |  |  |
|  | - contrast_gamma：コントラスト強調＋ガンマ補正。薄字・記号の認識率向上を狙う |  |  |  |
|  | - contrast_gamma_sharpen_light：コントラスト強調＋ガンマ補正＋軽度シャープニング。コントラストと輪郭の両方を改善する |  |  |  |
|  | - denoise：ノイズ除去。機械的スキャンでありノイズがない前提で、今回は実施しない |  |  |  |
|  | #### 3. OCR 実行 |  |  |  |
|  | - 各パターンごとに ZIP を生成し、backend API から OCR を実行する |  |  |  |
|  | - ジョブが `completed` になるまで待機する |  |  |  |
|  | - 出力を `ocr-results-003002/<pattern>/` に保存する |  |  |  |
|  | #### 4. 精度比較 |  |  |  |
|  | - 各パターンの OCR 結果と baseline を比較する |  |  |  |
|  | - 主な誤認識箇所（RAG→RAC、GPT-4→〓PT-4、LLM→lm、商→育 など）の改善状況を確認する |  |  |  |
|  | - 「〓」出現数、明らかな誤認識箇所数、推定 CER を集計する |  |  |  |
|  | #### 5. ドキュメント記録 |  |  |  |
|  | - `ocr-worker/docs/work_log.md` に作業ログを追記する |  |  |  |
|  | - `ocr-worker/docs/tasks.md` の 003002【実施結果】欄に結果を追記する |  |  |  |
|  | - 精度比較レポートを `ocr-results-003002/preprocess-comparison-report.md` に作成する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-13: 5 パターンの入力画像前処理を適用し、OCR 精度を比較した（baseline は 003001 の結果を流用） |  |  |  |
|  | 2026-08-13: 最も効果的だったのは `sharpen_light_upscale_2x`（2 倍アップスケーリング＋軽度シャープニング）で、「〓」出現数が baseline 5 個から 3 個へ減少し、003.png・004.png でほぼ完全な認識を実現した |  |  |  |
|  | 2026-08-13: `sharpen_light` のみでは効果が限定的で、`contrast_gamma` は逆に記号・英数字の誤認識を増加させる傾向があった |  |  |  |
|  | 2026-08-13: 精度比較レポート [ocr-results-003002/preprocess-comparison-report.md](ocr-results-003002/preprocess-comparison-report.md) を作成した |  |  |  |
| 003003 | config.yml パラメータ調整の効果検証 | 2026-08-13 |  | 改善調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 目的：003001 で特定した誤認識パターン（英数字頭文字・記号・漢字部品類似）に対し、ndlocr_cli のモデルパラメータを調整することで、前処理だけでは解決しきれなかった誤認識を改善する |  |  |  |
|  | 前提：003001・003002 が完了しており、sharpen_light_upscale_2x が最も効果的だったことが分かっていること |  |  |  |
|  | 前提：評価基準は 003002 と同一（「〓」出現数、明らかな誤認識箇所数）を用い、比較可能とする |  |  |  |
|  | 前提：コンテナ内に ndlocr_cli の config.yml が存在することを事前に確認する |  |  |  |
|  | `ocr-worker/config.yml` の `layout_extraction.score_thr`、`line_ocr.additional_elements` などを調整する |  |  |  |
|  | パラメータパターンごとに OCR 精度を比較する |  |  |  |
|  | 改善効果と処理時間への影響を評価する |  |  |  |
|  | 実施順序と比較パターン： |  |  |  |
|  | 1. baseline（config.yml 変更なし）※003002 の sharpen_light_upscale_2x 結果を流用する |  |  |  |
|  | 2. pattern A: line_ocr.score_thr 下げ ― 認識確信度が低い文字も出力させ、頭文字欠落・小文字化を改善する |  |  |  |
|  | 3. pattern B: layout_extraction.detect.score_thr 下げ ― 小さな文字領域の検出漏れを減らす |  |  |  |
|  | 4. pattern C: A + B の組み合わせ ― 両方のパラメータを同時に変更 |  |  |  |
|  | ### 詳細実施手順 |  |  |  |
|  | #### 1. コンテナ内 config.yml の確認 |  |  |  |
|  | docker compose exec ocr-worker でコンテナ内の config.yml パスと内容を確認する |  |  |  |
|  | #### 2. パラメータ調整用スクリプトの作成 |  |  |  |
|  | `scripts/adjust_ocr_config.py` を新規作成し、config.yml の特定パラメータを上書きする機能を実装する |  |  |  |
|  | #### 3. 各パターンでの OCR 実行 |  |  |  |
|  | 各パターンごとに調整後の config.yml を ocr-worker に配置する |  |  |  |
|  | sharpen_light_upscale_2x 適用済み ZIP（または同条件で新規生成）を使用し、backend API 経由で OCR を実行する |  |  |  |
|  | 結果を `ocr-results-003003/<pattern>/` に保存する |  |  |  |
|  | #### 4. 精度比較 |  |  |  |
|  | 各パターンの OCR 結果と baseline を比較する |  |  |  |
|  | 「〓」出現数、明らかな誤認識箇所数を集計する |  |  |  |
|  | #### 5. ドキュメント記録 |  |  |  |
|  | `ocr-worker/docs/work_log.md` に作業ログを追記する |  |  |  |
|  | `ocr-worker/docs/tasks.md` の 003003【実施結果】欄に結果を追記する |  |  |  |
|  | 精度比較レポートを `ocr-results-003003/config-comparison-report.md` に作成する |  |  |  |
|  | ### 注意事項・リスク |  |  |  |
|  | `score_thr` を下げすぎると、ノイズや見出し線まで文字として認識する可能性がある |  |  |  |
|  | config.yml のパラメータ名・構造は ndlocr_cli のバージョンによって異なる可能性がある |  |  |  |
|  | パラメータ変更の効果は前処理と比べて限定的である可能性がある |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | （未実施） |  |  |  |
| 003005 | ocr-worker OCR 実行時 500 エラーの原因調査・修正（OCR 精度向上前の環境不具合修正） | 2026-08-13 | 2026-08-13 | 不具合修正 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | OCR 精度向上に取り掛かる前に、Docker 環境で OCR 実行時に 500 エラーが発生していた原因を調査する |  |  |  |
|  | ndlocr_cli の依存関係・コンテナ設定・推論パイプラインを確認する |  |  |  |
|  | 必要な修正を実施し、OCR が正常に完了することを検証する |  |  |  |
|  | 作業内容を `ocr-worker/docs/work_log.md` / `caveats.md` に記録する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-13: Docker 環境の不具合を修正し、OCR 実行時の 500 エラーが解消された |  |  |  |
|  | 2026-08-13: 本タスクは OCR 精度向上の前段階として必要となった環境整備である |  |  |  |
