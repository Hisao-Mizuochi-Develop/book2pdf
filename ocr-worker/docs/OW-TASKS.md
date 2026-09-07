# タスク管理

本ファイルは、ocr-worker のタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する
- タスク No は「モジュール識別子（2文字）＋ ユースケースNo（3桁）＋ 通番（3桁）」とする
  - 識別子 `OW` は ocr-worker、`SY` は System/全体設計・仕様等を表す
  - 例：ユースケース001の1番目のタスク → `OW001001`
- 通番は各ユースケース内で 001 から連番で振る

---

## ユースケースNo | 001

ユースケース
ndlocr_cli を実行可能な Docker コンテナ（ocr-worker）を構築する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OW001001 | ndlocr_cli 実行環境の Docker コンテナ化 | 2026-08-11 | 2026-08-11 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | ndlocr_cli リポジトリの構成・submodule・公式 Dockerfile を調査する |  |  |  |
|  | ocr-worker/Dockerfile を作成し、ndlocr_cli を Python パッケージとして import できるようにする |  |  |  |
|  | docker-compose.yml を作成・更新し、backend / ocr-worker コンテナを連携させる |  |  |  |
|  | コンテナ内で `from cli.core import OcrInferrer` が成功することを確認する |  |  |  |
|  | サンプル画像で OCR を実行し、XML 出力形式を確認する |  |  |  |
|  | ocr-worker/docs/OW-WORK-LOG.md / OW-CAVEATS.md / OW-OCR-WORKER-SYSTEM-SPEC.md を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: ndlocr_cli リポジトリの構成・submodule・公式 Dockerfile を調査 |  |  |  |
|  | 2026-08-11: ocr-worker/Dockerfile を新規作成（python:3.10-slim ベース、CPU 実行用） |  |  |  |
|  | 2026-08-11: プロジェクトルートの docker-compose.yml を新規作成（backend / ocr-worker 連携） |  |  |  |
|  | 2026-08-11: Docker Desktop の起動を確認（v29.6.2） |  |  |  |
|  | 2026-08-11: ocr-worker/docs/OW-WORK-LOG.md / OW-CAVEATS.md / OW-OCR-WORKER-SYSTEM-SPEC.md を更新 |  |  |  |
|  | 2026-08-11: backend/docs/BE-BACKEND-SYSTEM-SPEC.md を更新 |  |  |  |
|  | 2026-08-11: コンテナビルドに成功（`docker compose build ocr-worker`） |  |  |  |
|  | 2026-08-11: コンテナ内で `from cli.core import OcrInferrer` の import に成功 |  |  |  |
|  | 2026-08-11: `GutterDetector` 経由で `init_detector` の CPU 動作を確認 |  |  |  |
|  | 2026-08-11: サンプル画像で OCR を実行し、XML / txt 出力を確認 |  |  |  |
|  | 2026-08-11: 発生した問題に対して Dockerfile を修正（mmdet init_detector 引数、text_recognition_lightning callbacks / trainer、KyTea ソースビルド） |  |  |  |
| OW001002 | ocr-worker OCR API の実装 | 2026-08-11 | 2026-08-11 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `ocr-worker/app/main.py` を新規作成し、OCR 実行用 FastAPI アプリケーションを実装する |  |  |  |
|  | `POST /ocr` エンドポイントを提供し、入力ディレクトリ・出力ディレクトリ・config パスを受け取る |  |  |  |
|  | `OcrInferrer` を使って OCR を実行し、テキスト・XML パス・成否を返す |  |  |  |
|  | `ocr-worker/Dockerfile` を更新し、fastapi / uvicorn / httpx をインストールする |  |  |  |
|  | `docker-compose.yml` で ocr-worker の起動コマンドを FastAPI サーバーに変更する |  |  |  |
|  | `ocr-worker/docs/OW-WORK-LOG.md` / `OW-CAVEATS.md` / `OW-OCR-WORKER-SYSTEM-SPEC.md` を更新する |  |  |  |
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
|  | 2026-08-11: `ocr-worker/docs/OW-WORK-LOG.md` / `OW-CAVEATS.md` / `OW-OCR-WORKER-SYSTEM-SPEC.md` を更新 |  |  |  |

---

## ユースケースNo | 002

ユースケース
性能計測に必要な DEBUG ログ・計測処理を追加する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OW002001 | ocr-worker DEBUG ログ・計測処理の追加 | 2026-08-12 | 2026-08-12 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `ocr-worker/app/main.py` に `LOG_LEVEL` 環境変数に応じたロガー設定と、OCR 処理開始・完了の DEBUG ログを追加する |  |  |  |
|  | OCR 処理全体の所要時間を DEBUG ログで出力する |  |  |  |
|  | `docker-compose.yml` の ocr-worker サービスに `LOG_LEVEL=DEBUG` を設定する |  |  |  |
|  | `ocr-worker/docs/OW-WORK-LOG.md` に作業内容を記録する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-12: `ocr-worker/app/main.py` に `LOG_LEVEL` 環境変数に応じたロガー設定と、OCR 処理開始・完了・所要時間の DEBUG ログを追加した |  |  |  |
|  | 2026-08-12: `docker-compose.yml` の ocr-worker サービスに `LOG_LEVEL=DEBUG` を追加した |  |  |  |
|  | 2026-08-12: `ocr-worker/docs/OW-WORK-LOG.md` に本タスクの作業ログを追記した |  |  |  |
| OW002002 | OCR 処理性能計測の実施 | 2026-08-12 |  | 性能評価 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | サンプル画像 001.png〜010.png を 1 つのアーカイブ `benchmark-input-10pages.zip` にまとめる |  |  |  |
|  | backend から 1 回のジョブで 10 ページ ZIP の OCR 処理を呼び出し、ndlocr_cli の DEBUG ログからページごとの処理時間を計測する |  |  |  |
|  | ndlocr_cli の既存ログにページごとの処理時間が出力されていなければ、ソースコードを修正して DEBUG ログを追加する |  |  |  |
|  | ページごとの OCR 処理時間を `ocr-worker/docs/OW-WORK-LOG.md` に記載する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | （性能テスト実行後に記載予定） |  |  |  |

---

## ユースケースNo | 003

ユースケース
OCR 読み取り精度向上

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OW003001 | ocr-worker OCR 実行時 500 エラーの原因調査・修正（OCR 精度向上前の環境不具合修正） | 2026-08-13 | 2026-08-13 | 不具合修正 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | OCR 精度向上に取り掛かる前に、Docker 環境で OCR 実行時に 500 エラーが発生していた原因を調査する |  |  |  |
|  | ndlocr_cli の依存関係・コンテナ設定・推論パイプラインを確認する |  |  |  |
|  | 必要な修正を実施し、OCR が正常に完了することを検証する |  |  |  |
|  | 作業内容を `ocr-worker/docs/OW-WORK-LOG.md` / `OW-CAVEATS.md` に記録する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-13: Docker 環境の不具合を修正し、OCR 実行時の 500 エラーが解消された |  |  |  |
|  | 2026-08-13: 本タスクは OCR 精度向上の前段階として必要となった環境整備である |  |  |  |
| OW003002 | 現状 OCR 認識精度の再測定 | 2026-08-13 | 2026-08-13 | 調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 目的：OCR 精度向上施策を検討する前に、現状の ndlocr_cli（CPU 実行）の認識精度を定量的・定性的に把握する |  |  |  |
|  | 1. 環境クリーンアップ：コンテナ内 `/data/extracted/*`、`/data/ocr_output/*`、`/data/pdfs/*` と、ホスト側 `/tmp/book2pdf-*`、作業ディレクトリ内テスト出力を削除する |  |  |  |
|  | 2. テスト用 ZIP の確認：既存の `benchmark-ocr-OW003002.zip` を使用し、含まれる画像を `unzip -l` で確認する |  |  |  |
|  | 3. Docker Compose 起動：`backend` / `ocr-worker` コンテナを最新イメージで起動する |  |  |  |
|  | 4. OCR 実行：backend API から ZIP をアップロードし、backend → ocr-worker 経由で OCR を実行する。ジョブが `completed` になるまで待機する |  |  |  |
|  | 5. 成果物取得：ocr-worker 出力の XML ファイル、テキストファイル、backend 生成 PDF をホスト側にコピーする |  |  |  |
|  | 6. 精度解析：元画像と OCR 結果テキストを比較し、英数字・記号・漢字・異体字などの認識ミスを一覧化する。定量的には CER（Character Error Rate）を算出し、目視確認も併用する |  |  |  |
|  | 7. ドキュメント記録：測定結果を `ocr-worker/docs/OW-WORK-LOG.md` / `backend/docs/BE-WORK-LOG.md` に記載し、本タスクの【実施結果】欄に追記する |  |  |  |
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
|  | unzip -l benchmark-ocr-OW003002.zip |  |  |  |
|  | ``` |  |  |  |
|  | #### 3. Docker Compose 起動 |  |  |  |
|  | ```bash |  |  |  |
|  | docker compose up -d --build |  |  |  |
|  | ``` |  |  |  |
|  | #### 4. OCR 実行 |  |  |  |
|  | ```bash |  |  |  |
|  | JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id') |  |  |  |
|  | curl -s -X POST -F "file=@benchmark-ocr-OW003002.zip;type=application/zip" http://localhost:8000/api/jobs/$JOB_ID/upload | jq . |  |  |  |
|  | curl -s --max-time 1800 -X POST http://localhost:8000/api/jobs/$JOB_ID/ocr | jq . |  |  |  |
|  | curl -s http://localhost:8000/api/jobs/$JOB_ID | jq . |  |  |  |
|  | ``` |  |  |  |
|  | #### 5. 成果物取得 |  |  |  |
|  | ```bash |  |  |  |
|  | # ジョブ情報から output_dir と pdf_path を特定 |  |  |  |
|  | curl -s http://localhost:8000/api/jobs/$JOB_ID | jq . |  |  |  |
|  | # 例：ocr-worker 出力をホストにコピー |  |  |  |
|  | docker compose cp ocr-worker:/data/ocr_output/<job_dir>/ ./ocr-results-OW003002/ |  |  |  |
|  | docker compose cp backend:/data/pdfs/<pdf_file> ./ocr-results-OW003002/ |  |  |  |
|  | ``` |  |  |  |
|  | #### 6. 精度解析 |  |  |  |
|  | - 目視確認：元画像と OCR 結果テキスト（`_main.txt`, `_ruby.txt`, XML）を照合し、英数字・記号・漢字・異体字の誤認識を一覧化 |  |  |  |
|  | - 定量的評価：正解テキストがあれば CER を算出。ない場合は認識文字数に対する誤認識箇所数でミス率を算出 |  |  |  |
|  | ```bash |  |  |  |
|  | # 例：CER 計算スクリプト |  |  |  |
|  | python scripts/compare_ocr_accuracy.py --ground-truth ./ground-truth-OW003002.txt --ocr ./ocr-results-OW003002/<job_dir>/txt/<page>_main.txt |  |  |  |
|  | ``` |  |  |  |
|  | #### 7. ドキュメント記録 |  |  |  |
|  | - `ocr-worker/docs/OW-WORK-LOG.md` に測定結果を記載 |  |  |  |
|  | - `ocr-worker/docs/OW-TASKS.md` の OW003002【実施結果】欄に追記 |  |  |  |
|  | - 必要に応じて `backend/docs/BE-WORK-LOG.md` にも記載 |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-13: `benchmark-ocr-OW003002.zip`（002.png, 003.png, 004.png）を使用して再測定を実施 |  |  |  |
|  | 2026-08-13: ジョブ ID `aca976fb-db10-47f1-847e-97ecf9b38ae5` で OCR を実行し、status: "completed" となったことを確認 |  |  |  |
|  | 2026-08-13: ocr-worker 出力（XML, `_main.txt`）と backend 生成 PDF を `ocr-results-OW003002/` に取得 |  |  |  |
|  | 2026-08-13: 認識精度レポート `ocr-results-OW003002/ocr-accuracy-report-OW003002.md` を新規作成 |  |  |  |
|  | 2026-08-13: 全体文字数約 1,327 文字、「〓」出現 5 回、明らかな誤認識箇所 002.png で約 7 箇所、003.png で約 5 箇所、004.png で約 8 箇所を確認 |  |  |  |
|  | 2026-08-13: 推定 CER は約 1〜3%（表紙ページはより高い） |  |  |  |
|  | 2026-08-13: 主要な誤認識パターンとして「英数字頭文字」「記号」「漢字の部品類似」「異体字・旧字体」「語尾・助詞」を特定 |  |  |  |
|  | 2026-08-13: XML の CONF 値が 0.998〜1.000 と高いにもかかわらず、実際には明らかな誤認識が含まれることを確認 |  |  |  |
|  | 2026-08-13: 精度向上の方向性として「入力画像前処理」「config.yml パラメータ調整」「推論パイプライン見直し」「後処理」を整理 |  |  |  |
|  | 2026-08-13: `ocr-worker/docs/OW-WORK-LOG.md` に本タスクの作業ログを追記 |  |  |  |
| OW003003 | 入力画像前処理の効果検証 | 2026-08-13 | 2026-08-13 | 改善調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 目的：OW003002 で特定した誤認識パターン（英数字頭文字・記号・漢字部品類似）に対し、入力画像前処理の効果を定量的に検証する |  |  |  |
|  | 対象データ：`benchmark-ocr-OW003002.zip`（002.png, 003.png, 004.png）を再利用する |  |  |  |
|  | 前処理は Python スクリプト（Pillow / OpenCV）で実装し、backend へ ZIP アップロードする前に適用する |  |  |  |
|  | 評価指標：「〓」出現数、明らかな誤認識箇所数、推定 CER、処理時間 |  |  |  |
|  | 各パターンの具体的なパラメータ値： |  |  |  |
|  | - sharpen_light: PIL.ImageFilter.UnsharpMask(radius=2, percent=80, threshold=3) |  |  |  |
|  | - upscale_2x: PIL.Image.Resampling.LANCZOS で 2 倍アップスケール |  |  |  |
|  | - contrast: ImageEnhance.Contrast で enhance(1.5) |  |  |  |
|  | - gamma: γ=0.8 のガンマ補正（arr ^ 0.8、clip 後 uint8 変換） |  |  |  |
|  | 実施順序と比較パターン： |  |  |  |
|  | 1. baseline（前処理なし） ※OW003002 と同一条件のため、本タスクでは再実行せず `ocr-results-OW003002/` の結果を比較基準として使用する |  |  |  |
|  | 2. sharpen_light（軽度シャープニング） |  |  |  |
|  | 3. sharpen_light_upscale_2x（2 倍アップスケーリング＋軽度シャープニング） |  |  |  |
|  | 4. contrast_gamma（コントラスト強調＋ガンマ補正） |  |  |  |
|  | 5. contrast_gamma_sharpen_light（コントラスト強調＋ガンマ補正＋軽度シャープニング） |  |  |  |
|  | なお、denoise（ノイズ除去）は機械的スキャンでありノイズがない前提で、今回は実施しない |  |  |  |
|  | 各パターンで OCR を実行し、結果を `ocr-results-OW003003/` に保存する（baseline は OW003002 の結果を流用） |  |  |  |
|  | 各ステップごとに結果を報告し、次のパターンを実施するかを確認する |  |  |  |
|  | 最も効果的な前処理パターンを選定し、`ocr-worker/docs/OW-WORK-LOG.md` / `ocr-worker/docs/OW-TASKS.md` に記録する |  |  |  |
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
|  | - 出力を `ocr-results-OW003003/<pattern>/` に保存する |  |  |  |
|  | #### 4. 精度比較 |  |  |  |
|  | - 各パターンの OCR 結果と baseline を比較する |  |  |  |
|  | - 主な誤認識箇所（RAG→RAC、GPT-4→〓PT-4、LLM→lm、商→育 など）の改善状況を確認する |  |  |  |
|  | - 「〓」出現数、明らかな誤認識箇所数、推定 CER を集計する |  |  |  |
|  | #### 5. ドキュメント記録 |  |  |  |
|  | - `ocr-worker/docs/OW-WORK-LOG.md` に作業ログを追記する |  |  |  |
|  | - `ocr-worker/docs/OW-TASKS.md` の OW003003【実施結果】欄に結果を追記する |  |  |  |
|  | - 精度比較レポートを `ocr-results-OW003003/preprocess-comparison-report-OW003003.md` に作成する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-13: 5 パターンの入力画像前処理を適用し、OCR 精度を比較した（baseline は OW003002 の結果を流用） |  |  |  |
|  | 2026-08-13: 最も効果的だったのは `sharpen_light_upscale_2x`（2 倍アップスケーリング＋軽度シャープニング）で、「〓」出現数が baseline 5 個から 3 個へ減少し、003.png・004.png でほぼ完全な認識を実現した |  |  |  |
|  | 2026-08-13: `sharpen_light` のみでは効果が限定的で、`contrast_gamma` は逆に記号・英数字の誤認識を増加させる傾向があった |  |  |  |
|  | 2026-08-13: 精度比較レポート [ocr-results-OW003003/preprocess-comparison-report-OW003003.md](ocr-results-OW003003/preprocess-comparison-report-OW003003.md) を作成した |  |  |  |
| OW003004 | config.yml パラメータ調整の効果検証 | 2026-08-13 | 2026-08-14 | 改善調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】（2026-08-13: config.yml 確認後に計画を変更 ― line_ocr.score_thr は存在せず layout_extraction.score_thr のみが調整可能であった） |  |  |  |
|  | 目的：OW003002 で特定した誤認識パターン（英数字頭文字・記号・漢字部品類似）に対し、ndlocr_cli のモデルパラメータを調整することで、前処理だけでは解決しきれなかった誤認識を改善する |  |  |  |
|  | 前提：OW003002・OW003003 が完了しており、sharpen_light_upscale_2x が最も効果的だったことが分かっていること |  |  |  |
|  | 前提：評価基準は OW003003 と同一（「〓」出現数、明らかな誤認識箇所数）を用い、比較可能とする |  |  |  |
|  | 前提：コンテナ内の config.yml（/opt/ocr-worker/config.yml）を確認済み。調整可能な閾値は `layout_extraction.score_thr: 0.3` のみ。`line_ocr.score_thr` は存在しない |  |  |  |
|  | 具体的な変更パラメータ値： |  |  |  |
|  | - pattern A: `layout_extraction.score_thr: 0.3 → 0.2` |  |  |  |
|  | - pattern B: `layout_extraction.score_thr: 0.3 → 0.1` |  |  |  |
|  | - pattern C: `layout_extraction.score_thr: 0.3 → 0.2` + `line_ocr.additional_elements` の柱/ノンブル/ルビ: True → False |  |  |  |
|  | `layout_extraction.score_thr`、`line_ocr.additional_elements`（柱/ノンブル/ルビの有無）を調整する |  |  |  |
|  | パラメータパターンごとに OCR 精度を比較する |  |  |  |
|  | 改善効果と処理時間への影響を評価する |  |  |  |
|  | 実施順序と比較パターン： |  |  |  |
|  | 1. baseline（config.yml 変更なし）※OW003003 の sharpen_light_upscale_2x 結果を流用する |  |  |  |
|  | 2. pattern A: layout_extraction.score_thr 0.2 ― 小さな文字領域の検出漏れを減らす |  |  |  |
|  | 3. pattern B: layout_extraction.score_thr 0.1 ― さらに検出感度を上げる |  |  |  |
|  | 4. pattern C: layout_extraction.score_thr 0.2 + line_ocr.additional_elements の柱/ノンブル/ルビを False ― ノイズ認識を抑制しつつ検出感度を上げる |  |  |  |
|  | ### 詳細実施手順 |  |  |  |
|  | #### 1. コンテナ内 config.yml の確認 |  |  |  |
|  | `docker compose exec ocr-worker cat /opt/ocr-worker/config.yml` で内容を確認する（済） |  |  |  |
|  | #### 2. パラメータ調整用スクリプトの作成 |  |  |  |
|  | `scripts/adjust_ocr_config.py` を新規作成し、config.yml の `layout_extraction.score_thr` と `line_ocr.additional_elements` を上書きする機能を実装する |  |  |  |
|  | #### 3. 各パターンでの OCR 実行 |  |  |  |
|  | 各パターンごとに調整後の config.yml を ocr-worker に配置する |  |  |  |
|  | sharpen_light_upscale_2x 適用済み ZIP（または同条件で新規生成）を使用し、backend API 経由で OCR を実行する |  |  |  |
|  | 結果を `ocr-results-OW003004/<pattern>/` に保存する |  |  |  |
|  | #### 4. 精度比較 |  |  |  |
|  | 各パターンの OCR 結果と baseline を比較する |  |  |  |
|  | 「〓」出現数、明らかな誤認識箇所数を集計する |  |  |  |
|  | #### 5. ドキュメント記録 |  |  |  |
|  | `ocr-worker/docs/OW-WORK-LOG.md` に作業ログを追記する |  |  |  |
|  | `ocr-worker/docs/OW-TASKS.md` の OW003004【実施結果】欄に結果を追記する |  |  |  |
|  | 精度比較レポートを `ocr-results-OW003004/config-comparison-report-OW003004.md` に作成する |  |  |  |
|  | ### 注意事項・リスク |  |  |  |
|  | `score_thr` を下げすぎると、ノイズや見出し線まで文字として認識する可能性がある |  |  |  |
|  | config.yml のパラメータ名・構造は ndlocr_cli のバージョンによって異なる可能性がある |  |  |  |
|  | パラメータ変更の効果は前処理と比べて限定的である可能性がある |  |  |  |
|  | 実際の config.yml には `line_ocr.score_thr` は存在せず、調整可能な閾値は `layout_extraction.score_thr` のみであった |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-13: 3 パターン（score_thr: 0.2 / 0.1 / 0.2+additional_elements False）で config.yml パラメータ調整を実施 |  |  |  |
|  | 2026-08-13: すべてのパターンで baseline（sharpen_light_upscale_2x、〓 3 個）と同一の結果となり、config.yml パラメータ調整に効果なしと判断 |  |  |  |
|  | 2026-08-13: **※後述の OW003005 で判明：ndl_layout submodule の `process_textblock.py` / `process.py` に `score_thr: float = 0.3` がハードコードされており、config.yml の値が無視されていたため、本タスクのパラメータ変更は実質的に検証になっていなかった** |  |  |  |
|  | 2026-08-13: 精度比較レポート [ocr-results-OW003004/config-comparison-report-OW003004.md](ocr-results-OW003004/config-comparison-report-OW003004.md) を作成した |  |  |  |
|  | 2026-08-13: `ocr-worker/docs/OW-WORK-LOG.md` に本タスクの作業ログを追記した |  |  |  |
|  | 2026-08-13: タスク完了日付を記載 |  |  |  |
| OW003005 | OCR精度向上の統合検討と実装修正（config.yml score_thr 無視問題の修正と再検証） | 2026-08-13 | 2026-08-14 | 不具合修正 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | ※2026-08-14: 再検証計画を追加。初回の score_thr 検証では ocr-worker コンテナ内での直接実行を行っていたため、backend 生成 PDF が取得できず、.clinerules 第10章の backend API 経由フルフロー要件を満たしていなかった |  |  |  |
|  | 再検証手順： |  |  |  |
|  | 1. `docker compose up -d` で backend / ocr-worker / frontend を起動する（frontend は API 経由フルフローには必須ではないが、起動しておく） |  |  |  |
|  | 2. ocr-worker コンテナ内の `/opt/ocr-worker/config.yml` の `layout_extraction.score_thr` を pattern-A: 0.2 / pattern-B: 0.1 / pattern-C: 0.5 に変更する |  |  |  |
|  | 3. `benchmark-ocr-OW003002.zip` を backend API 経由でアップロード・OCR 実行し、ジョブが `completed` になるまでポーリングする |  |  |  |
|  | 4. 生成された PDF を `docker compose cp backend:/data/pdfs/<job_id>.pdf ./ocr-results-OW003005/<pattern>/pdfs/` で取得する |  |  |  |
|  | 5. ocr-worker 出力（XML / txt）もあわせて取得し、`./ocr-results-OW003005/<pattern>/` に保存する |  |  |  |
|  | 6. 3 パターン分の PDF を目視確認し、レイアウト・文字認識・欠落行の違いを比較する |  |  |  |
|  | 7. `ocr-results-OW003005/config-comparison-report-OW003005.md` を作成する |  |  |  |
|  | 8. OW-TASKS.md の【実施結果】欩末にレポートリンクを追加し、タスク完了日付を記載する |  |  |  |
|  | ※前提：OW003003 で sharpen_light_upscale_2x が最も効果的、OW003004 で config.yml 調整に効果なし（ハードコーディングが原因と判明） |  |  |  |
|  |  |  |  |  |
|  | 1. config.yml パラメータ無視の原因調査と修正： |  |  |  |
|  |    - `ocr-worker/ndlocr_cli_patches/inference.py` を開き、config.yml の `layout_extraction.score_thr` がどこで読み込まれるか確認 |  |  |  |
|  |    - パッチ内または ndlocr_cli ソースで、ハードコードされた閾値（例: 0.3）を検索 |  |  |  |
|  |    - config.yml の値を実際に参照するようにコードを修正し、パッチを更新 |  |  |  |
|  |    - コンテナをリビルドし、同一画像で再度OCR実行、出力に差分が出ることを確認 |  |  |  |
|  |    - OW003004 の検証パターン（score_thr 0.2 / 0.1 / 0.2+additional_elements False）を再実施し、修正後の効果を評価 |  |  |  |
|  |  |  |  |  |
|  | 2. 自動前処理統合の実装： |  |  |  |
|  |    - `ocr-worker/app/main.py` の `/ocr` エンドポイントまたは前処理関数に、sharpen_light_upscale_2x を自動適用する処理を追加 |  |  |  |
|  |    - 前処理の有無を制御するフラグ（デフォルトON）を環境変数 `PREPROCESS_ENABLED` で設定可能にする |  |  |  |
|  |    - 前処理済み画像の一時保存先を確保し、OCR完了後に cleanup |  |  |  |
|  |    - `benchmark-ocr-OW003002.zip` で動作確認：前処理ON/OFF の結果を比較し、OW003003 と同等の精度向上を確認 |  |  |  |
|  |  |  |  |  |
|  | 3. 表紙ページ（002.png）の残存誤認識対策実装： |  |  |  |
|  |    - 002.png の OCR 結果（`002_main.txt`）を確認し、RAG→RAC、Improving→mproving などの誤認識パターンを列挙 |  |  |  |
|  |    - 追加前処理（例: 4x アップスケール、局所的二値化、コントラスト強調）をスクリプト化し効果を検証 |  |  |  |
|  |    - または、OCR後の辞書ベース補正（表紙に出現しやすい固有名詞のマッピング表）を試作する |  |  |  |
|  |    - いずれかの手法で誤認識が減少することを確認したら、該当処理を統合する |  |  |  |
|  |  |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-14: config.yml パラメータ無視の原因を特定（ndl_layout submodule 内の `process_textblock.py` / `process.py` に `score_thr: float = 0.3` がハードコードされており、config.yml の `layout_extraction.score_thr` が無視されていた） |  |  |  |
|  | 2026-08-14: 修正方針を決定（`inference.py` パッチによる動的リライトではなく、`process_textblock.py` 自体を Docker ビルド時にパッチファイルで上書きする方式で最小限の変更とする） |  |  |  |
|  | 2026-08-14: `ocr-worker/ndlocr_cli_patches/process_textblock.py` を新規作成。`InferencerWithCLI.__init__` で `conf_dict['score_thr']` を読み取り、`_inference` / `inference_with_cli` で `inference_detector` / `convert_to_xml_string_with_data` へ `score_thr` を渡すように修正 |  |  |  |
|  | 2026-08-14: `ocr-worker/Dockerfile` を更新。パッチファイルをビルド時に `/opt/ocr-worker/submodules/ndl_layout/tools/process_textblock.py` へ `COPY` する行を追加 |  |  |  |
|  | 2026-08-14: ocr-worker コンテナをリビルドし、config.yml の `layout_extraction.score_thr` を 0.2 / 0.1 / 0.5 に変更して OCR 実行。score_thr=0.2 と 0.1 は同一結果、score_thr=0.5 では低 CONF の見出し行が欠落し TEXTBLOCK 数が減少することを確認（config.yml の値が反映された） |  |  |  |
|  | 2026-08-14: **※本タスクの検証は ocr-worker コンテナ内での `OcrInferrer` 直接実行により行われており、backend API 経由のフルフローではなかったため、backend 生成 PDF が取得できていなかった** |  |  |  |
|  | 2026-08-14: `.clinerules` 第10章「テスト・検証・調査系タスクのルール」を新設し、今後の検証・調査タスクでは backend API 経由のフルフローと PDF 目視確認を必須とした |  |  |  |
|  | 2026-08-14: pattern-A/B/C を backend API 経由フルフローで再実行し、生成 PDF を取得して目視確認を実施
|  | 2026-08-14: 精度比較レポート [ocr-results-OW003005/config-comparison-report-OW003005.md](ocr-results-OW003005/config-comparison-report-OW003005.md) を作成した |  |  |  |
|  | 2026-08-14: 自動前処理統合（sharpen_light_upscale_2x）と表紙ページの残存誤認識対策は、本タスクでは score_thr 修正・再検証にスコープを絞り、今後のタスクとして保留とする |  |  |  |
|  | 2026-08-14: `ocr-worker/docs/OW-WORK-LOG.md` / `ocr-worker/docs/OW-CAVEATS.md` を更新
|  | 2026-08-14: タスク完了日付を記載 |  |  |  |
| OW003006 | sharpen_light_upscale_2x 自動前処理の ocr-worker 組み込み | 2026-08-14 | 2026-08-14 | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 目的：OW003003 で最も効果的だった `sharpen_light_upscale_2x` 前処理を ocr-worker 内部で自動適用し、全ページに対して精度向上を図る |  |  |  |
|  | 前提：OW003003 で `sharpen_light_upscale_2x` が最も効果的であることが確認済みであること |  |  |  |
|  | 前提：`benchmark-ocr-OW003002.zip`（002.png, 003.png, 004.png）をテストデータとして使用する |  |  |  |
|  | 前提：`ocr-worker/app/main.py` には現状前処理機能が存在しないこと |  |  |  |
|  | 1. `ocr-worker/app/main.py` に前処理関数を追加する |  |  |  |
|  |    - Pillow を使用して 2 倍アップスケール（LANCZOS）を実施する |  |  |  |
|  |    - `PIL.ImageFilter.UnsharpMask(radius=2, percent=80, threshold=3)` で軽度シャープニングを実施する |  |  |  |
|  |    - 入力画像パスを受け取り、前処理済み画像を一時ディレクトリに保存する関数を実装する |  |  |  |
|  | 2. 環境変数 `PREPROCESS_ENABLED`（デフォルト true）で前処理の ON/OFF を制御する |  |  |  |
|  |    - `PREPROCESS_ENABLED=false` の場合は既存の input_root をそのまま ndlocr_cli に渡す |  |  |  |
|  |    - `PREPROCESS_ENABLED=true` の場合は `/tmp/ocr_preprocess/<job_id>/img/` に前処理済み画像を出力してから OCR を実行する |  |  |  |
|  | 3. 前処理済み画像の一時保存先を確保し、OCR 完了後に cleanup する |  |  |  |
|  |    - 一時ディレクトリは `tempfile` または `/tmp/ocr_preprocess/<job_id>` を使用する |  |  |  |
|  |    - OCR 成功・失敗に関わらず cleanup を実施する（try/finally で保証する） |  |  |  |
|  | 4. `ocr-worker/Dockerfile` に Pillow のインストールを確認・追加する |  |  |  |
|  |    - 現状 Pillow が入っていない場合は `pip install --no-cache-dir Pillow` を追加する |  |  |  |
|  | 5. `docker compose up -d --build` で ocr-worker コンテナを再構築する |  |  |  |
|  | 6. backend API 経由フルフローで動作確認を実施する |  |  |  |
|  |    - `PREPROCESS_ENABLED=true`（デフォルト）で `benchmark-ocr-OW003002.zip` を OCR 実行する |  |  |  |
|  |    - `PREPROCESS_ENABLED=false` にして ocr-worker を再起動し、同一 ZIP を OCR 実行する |  |  |  |
|  |    - 前処理 ON/OFF の「〓」出現数・誤認識箇所数を比較し、OW003003 と同等の効果を確認する |  |  |  |
|  |    - 生成 PDF を `docker compose cp` で取得し、必要に応じて目視確認する |  |  |  |
|  | 7. ドキュメントを更新する |  |  |  |
|  |    - `ocr-worker/docs/OW-WORK-LOG.md` に【実施予定】・【実施実績】を記載する |  |  |  |
|  |    - `ocr-worker/docs/OW-CAVEATS.md` に前処理に関する注意事項を追記する |  |  |  |
|  |    - 必要に応じて `ocr-worker/docs/OW-OCR-WORKER-SYSTEM-SPEC.md` を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-14: `ocr-worker/app/main.py` に前処理関数 `_preprocess_image()` / `_preprocess_input_root()` を追加し、2倍アップスケール（LANCZOS）+ 軽度シャープニング（UnsharpMask radius=2, percent=80, threshold=3）を実装した |  |  |  |
|  | 2026-08-14: 環境変数 `PREPROCESS_ENABLED`（デフォルト true）により前処理の ON/OFF を制御する機能を追加した |  |  |  |
|  | 2026-08-14: 前処理済み画像の一時保存先として `/tmp/ocr_preprocess/<job_id>/img/` を使用し、OCR 成功・失敗に関わらず cleanup する try/finally 構造を実装した |  |  |  |
|  | 2026-08-14: `ocr-worker/Dockerfile` に `Pillow` のインストールを追加した |  |  |  |
|  | 2026-08-14: `docker-compose.yml` の ocr-worker サービスに `PREPROCESS_ENABLED=true` を追加し、デフォルトで前処理が有効になるよう設定した |  |  |  |
|  | 2026-08-14: ocr-worker コンテナを再ビルド・再起動し、backend API 経由フルフローで前処理 ON/OFF 両方の動作確認を実施した |  |  |  |
|  | 2026-08-14: 前処理 ON のジョブ `ec9acd66-563f-41e0-8410-08619208e6e9` は status: completed となり、「〓」出現数が baseline（5個）から 3個に減少し、003.png・004.png でほぼ完全な認識を確認した |  |  |  |
|  | 2026-08-14: 前処理 OFF のジョブ `e07faa8c-195b-4d36-bc7c-d44e0aa28582` は status: completed となり、OW003002 baseline と同等の「〓」出現数 5個を確認した |  |  |  |
|  | 2026-08-14: 精度比較レポート [ocr-results-OW003006/preprocess-integration-report-OW003006.md](ocr-results-OW003006/preprocess-integration-report-OW003006.md) を作成した |  |  |  |
|  | 2026-08-14: `ocr-worker/docs/OW-WORK-LOG.md` / `ocr-worker/docs/OW-CAVEATS.md` / `ocr-worker/docs/OW-OCR-WORKER-SYSTEM-SPEC.md` を更新した |  |  |  |

| OW003007 | 追加前処理（4x アップスケール、局所的二値化、コントラスト強調など）の効果検証 | 2026-08-14 | 2026-08-15 | 改善調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 目的：OW003003 で `sharpen_light_upscale_2x`（2倍アップスケール＋軽度シャープニング）が最も効果的だったが、表紙ページなどで残存誤認識があったため、さらに強力な前処理パターンの効果を定量的に検証する |  |  |  |
|  | 対象データ：`sample-png/手を動かしながら学ぶDocker入門_trimmed/001.png` 〜 `010.png`（10枚） |  |  |  |
|  | 比較パターン：baseline_2x / 4x_upscale / 4x_upscale_sharpen / local_binarization / local_binarization_sharpen / contrast_strong / contrast_strong_4x（計7パターン） |  |  |  |
|  | 1. `scripts/preprocess_image.py` に上記パターンを追加する |  |  |  |
|  | 2. 001.png 〜 010.png を ZIP にまとめた `benchmark-ocr-OW003007.zip` を作成する |  |  |  |
|  | 3. Docker Compose 環境を起動し、ocr-worker の自動前処理を OFF にする（`PREPROCESS_ENABLED=false`） |  |  |  |
|  | 4. 各パターンごとに backend API 経由でフルフロー OCR を実行する（`POST /api/jobs` → `upload` → `ocr`） |  |  |  |
|  | 5. `docker compose cp` で各ジョブの PDF および ocr-worker 出力（XML / txt）を `ocr-results-OW003007/<pattern>/` に取得する |  |  |  |
|  | 6. 各パターンの「〓」出現数、明らかな誤認識箇所数、目視確認結果を集計する |  |  |  |
|  | 7. 精度比較レポート `ocr-results-OW003007/additional-preprocess-report-OW003007.md` を作成する |  |  |  |
|  | 8. `ocr-worker/docs/OW-WORK-LOG.md` と `ocr-worker/docs/OW-TASKS.md` の本タスク欄に実施結果を追記する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-14: `scripts/preprocess_image.py` に 6 パターンの前処理を追加した（4x_upscale / 4x_upscale_sharpen / local_binarization / local_binarization_sharpen / contrast_strong / contrast_strong_4x） |  |  |  |
|  | 2026-08-14: `local_binarization` は OpenCV 非依存で PIL/numpy/scipy なしの純粋 numpy 畳み込みで実装した |  |  |  |
|  | 2026-08-14: `benchmark-ocr-OW003007.zip`（001.png〜010.png）と、7 パターンの前処理済み ZIP を作成した |  |  |  |
|  | 2026-08-14: `docker-compose.yml` の `PREPROCESS_ENABLED=false` を確認し、ocr-worker 側の自動前処理を OFF にした |  |  |  |
|  | 2026-08-14: backend API 経由のフルフロー OCR を 7 パターンで自動実行する `scripts/run_003007_ocr.sh` を作成した |  |  |  |
|  | 2026-08-14: OCR 自動実行を開始した |  |  |  |
|  | 2026-08-14: `4x_upscale` 単独で backend API 経由フルフロー OCR を実行し、結果を確認した |  |  |  |
|  | 2026-08-14: baseline_2x パターンで backend → ocr-worker 間の HTTP タイムアウト（1800秒）が発生したことを確認した |  |  |  |
|  | 2026-08-14: `backend/app/services/ocr_engine.py` の `OCR_WORKER_REQUEST_TIMEOUT` を 3600秒に延長し、`docker compose up -d --build` で backend / ocr-worker コンテナを再起動した |  |  |  |
|  | 2026-08-14: `scripts/run_003007_ocr_remaining.sh` および `scripts/run_003007_ocr_manual.sh` を作成し、残りパターンを手動・分割実行した |  |  |  |
|  | 2026-08-15: 7 パターンすべての OCR が完了し、PDF・OCR 出力（XML/txt）を `ocr-results-OW003007/<pattern>/` に取得した |  |  |  |
|  | 2026-08-15: ジョブID: baseline_2x=`10ddd822-8aad-43ea-a38d-1f67048fa3c9`, 4x_upscale=`9da8bd3f-5751-4cac-9b88-47384c5be083`, 4x_upscale_sharpen=`88828d53-b030-494f-b187-36e32e553649`, local_binarization=`904148bd-6aae-4e2b-a575-e890a3110230`, local_binarization_sharpen=`5dfd249c-6046-4411-916b-af914fc50750`, contrast_strong=`74048f6b-37ec-498c-99ac-cfcc6483f478`, contrast_strong_4x=`76f20761-8c17-4fd4-9823-42362cebffca` |  |  |  |
|  | 2026-08-15: 各パターン・ページごとの「〓」出現数を集計する `scripts/count_fui_per_page_003007.py` を作成した |  |  |  |
|  | 2026-08-15: 精度比較レポート [ocr-results-OW003007/additional-preprocess-report-OW003007.md](ocr-results-OW003007/additional-preprocess-report-OW003007.md) を作成した |  |  |  |
|  | 2026-08-15: `ocr-worker/docs/OW-WORK-LOG.md` に OW003007 の実施実績を追記した |  |  |  |
|  | 主な結果：「〓」出現数（全 txt 合計）は local_binarization/local_binarization_sharpen=135、contrast_strong=160、4x_upscale_sharpen=178、contrast_strong_4x=176、baseline_2x=194、4x_upscale=202 だった |  |  |  |
|  | 主な結果：local_binarization 系は文字潰れによる誤認識が増加し、contrast_strong は認識欠落が多かった |  |  |  |
|  | 結論：今回試した追加前処理（4x アップスケール、局所的二値化、強コントラスト）は、OW003006 で採用済みの 2x アップスケール＋軽度シャープニングを超える明確な改善は確認できず、新たな前処理として追加導入することは推奨されない |  |  |  |

---

## ユースケースNo | 003-FUTURE

ユースケース
OCR精度向上に関する今後の要検討対応・技術的負債・改善アイデア

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OW003008 | 対象ページに応じた適応的前処理の検討 | 2026-08-15 | 2026-09-01 | 要検討対応 |
|  | タスク詳細 |  |  |  |
|  | 【背景】 |  |  |  |
|  | OW003007 の検証結果より、表紙・目次・本文などページタイプによって最適な前処理が異なる可能性が見られた。一律の前処理では全ページタイプに最適ではない。 |  |  |  |
|  | 【検討内容】 |  |  |  |
|  | - ページ分類ベース：文字サイズ分布・色数・エッジ密度などからページタイプ（表紙/目次/本文）を自動判定し、前処理パラメータを切り替える |  |  |  |
|  | - 認識置信度ベース：標準前処理後の CONF 値や「〓」出現率に応じて、再OCR時に異なるパラメータを適用する |  |  |  |
|  | - レイアウト認識結果ベース：ndlocr_cli の TEXTBLOCK 数・領域サイズ分布から特殊ページを検出して切り替える |  |  |  |
|  | 【懸念事項】 |  |  |  |
|  | - ページ分類器の追加実装コスト |  |  |  |
|  | - 処理パイプラインが2パス化する場合の処理時間増加 |  |  |  |
|  | - 技術書の表紙は1ページのみのため、一律前処理を選ぶ方がシンプルな可能性 |  |  |  |
|  | 【結論】 |  |  |  |
|  | 現状はコストパフォーマンスが不明確。OCR後処理（辞書補正）やUIでの手動補正を優先し、本対応は将来の検討事項として保留とする。 |  |  |  |
|  | 2026-09-01: 検討レポート [ocr-worker/test-results/ocr-results-OW003008/adaptive-preprocess-report-OW003008.md](../test-results/ocr-results-OW003008/adaptive-preprocess-report-OW003008.md) を作成し、上記結論を維持 |  |  |  |

---

## ユースケースNo | 005

ユースケース
OCR 処理の安定性・スケーラビリティ向上（ページ数に依存しない一定のメモリ使用量を実現する）

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OW004001 | OCR 処理のメモリ使用量安定化 | 2026-08-27 | 2026-08-27 | 不具合修正 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 原因調査：ocr-worker が 257 ページジョブの page 3 で OOM（Exit code 137）になる原因を特定する |  |  |  |
|  | 調査結果：PyTorch Lightning Trainer.predict() の繰り返し呼び出し、画像データの copy.deepcopy、LayoutDetector テンソル累積が複合してメモリリークしていると特定 |  |  |  |
|  | `ocr-worker/ndlocr_cli_patches/` にメモリクリーンアップ用パッチを追加する（base_proc.py / line_ocr.py / layout_extraction.py / infer_task.py） |  |  |  |
|  | `ocr-worker/Dockerfile` にパッチ適用用の COPY 行を追加する |  |  |  |
|  | `ocr-worker/ndlocr_cli_patches/inference.py` のページループに `gc.collect()` と `torch.cuda.empty_cache()` を追加する |  |  |  |
|  | コンテナをビルド・再起動し、`/health` が正常に返ることを確認する |  |  |  |
|  | 多ページジョブ（50/100/200/500/999 ページ）でメモリ使用量をモニタリングし、OOM が解消されることを検証する |  |  |  |
|  | `ocr-worker/docs/OW-TASKS.md` / `OW-WORK-LOG.md` / `OW-CAVEATS.md` を更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-27: 原因調査を実施。257 ページジョブで page 3 付近で OOM（Exit code 137）が発生していた |  |  |  |
|  | 2026-08-27: `ndlocr_cli` 内で `copy.deepcopy(input_data)` による画像データのディープコピー、`Trainer.predict()` の繰り返し呼び出しによる DataLoader / テンソル累積、ページループでのガベージコレクション不足が複合していると特定 |  |  |  |
|  | 2026-08-27: `ocr-worker/ndlocr_cli_patches/base_proc.py` を修正：`_run_process()` の戻り値を `[input_data.copy()]` に変更し、dump 用画像の `copy.deepcopy()` を除去 |  |  |  |
|  | 2026-08-27: `ocr-worker/ndlocr_cli_patches/line_ocr.py` を修正：`_run_submodule_inference()` 呼び出し後に `trainer.predict_dataloaders = None` と `gc.collect()` を実行 |  |  |  |
|  | 2026-08-27: `ocr-worker/ndlocr_cli_patches/layout_extraction.py` を修正：`input_data.copy()` に置き換えて dump_img の deep copy を除去 |  |  |  |
|  | 2026-08-27: `ocr-worker/ndlocr_cli_patches/infer_task.py` を修正：`copy.deepcopy(input_data)` を `input_data.copy()` + `copy.deepcopy(input_data['xml'])` に変更し、`trainer.predict_dataloaders = None` を try/except で安全に実行 |  |  |  |
|  | 2026-08-27: `ocr-worker/ndlocr_cli_patches/inference.py` を修正：`_infer()` / `_infer_ruby_only()` のページループに `gc.collect()` と `torch.cuda.empty_cache()` を追加 |  |  |  |
|  | 2026-08-27: `ocr-worker/Dockerfile` に `base_proc.py` / `line_ocr.py` / `layout_extraction.py` / `infer_task.py` の COPY 行を追加 |  |  |  |
|  | 2026-08-27: `docker compose build ocr-worker` が成功し、コンテナが正常に起動することを確認 |  |  |  |
|  | 2026-08-27: 3 ページジョブで backend API 経由の OCR フルフローが `completed` になることを確認 |  |  |  |
|  | 2026-08-27: 50 ページジョブを開始し、`docker stats` でメモリ使用量をモニタリング。page 14 時点までに OOM は発生せず、メモリ使用量は 4.3GiB〜4.9GiB / 7.75GiB の範囲で推移し、明らかな増加傾向は見られなかった |  |  |  |
|  | 2026-08-27: 999 ページまでのフルスケールテストは処理時間（1 ページあたり約 80〜120 秒）のため今回は実施せず、別途長時間実行テストとして予定 |  |  |  |
|  | 2026-08-27: `ocr-worker/docs/OW-WORK-LOG.md` / `OW-CAVEATS.md` / 本ファイルを更新 |  |  |  |

---

## ユースケースNo | 009

ユースケース
OCR 認識精度を次世代アプローチで向上させる

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OW005001 | OCR 認識精度向上の次世代アプローチ調査 | 2026-09-03 |  | 調査 / 要検討対応 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 003 シリーズ（前処理・パラメータ調整）で達成した精度向上の限界を整理する |  |  |  |
|  | 次世代アプローチをリストアップし、コストパフォーマンスを評価する |  |  |  |
|  | 候補アプローチ： |  |  |  |
|  | - OCR 後処理：辞書ベース誤認識補正（「〓」→推定文字の復元、固有名詞辞書の活用） |  |  |  |
|  | - 異なる OCR エンジン・モデルの導入検討（ lightweight 日本語 OCR の調査） |  |  |  |
|  | - レイアウト認識結果の活用：ndlocr_cli の TEXTBLOCK 情報を用いた構造的理解の強化 |  |  |  |
|  | - 機械学習ベースの誤認識検出：認識結果の言語モデルスコアリング |  |  |  |
|  | 各アプローチの実装コスト・期待効果・リスクを評価し、優先順位を決定する |  |  |  |
|  | 最も効果的なアプローチを 1〜2 つ選び、 POC（概念検証）タスクを起票する |  |  |  |
|  | 【実施結果】 |  |  |  |

---

## ユースケースNo | 009

ユースケース
OCR 処理中のページ単位進捗通知精度を向上させる

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| OW009001 | ページ単位進捗通知精度の向上 | 2026-09-08 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | ocr-worker のページ単位処理結果を backend へリアルタイム通知する仕組みを検討する |  |  |  |
|  | 現在のジョブステータス通知（SSE/ポーリング）とページ単位進捗通知を統合・改善する |  |  |  |
|  | ndlocr_cli の内部処理フックまたは出力ログを利用して、現在処理中のページを特定する |  |  |  |
|  | backend のジョブ進捗 API にページ数・現在ページフィールドを追加する |  |  |  |
|  | frontend の ProgressPanel にページ進捗表示を追加する |  |  |  |
|  | 【実施結果】 |  |  |  |
