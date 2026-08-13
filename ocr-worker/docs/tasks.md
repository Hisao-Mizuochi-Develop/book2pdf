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
| 003001 | 現状 OCR 認識精度の再測定 | 2026-08-13 |  | 調査 |
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
|  | （再測定後に記載予定） |  |  |  |
| 003002 | 入力画像前処理の効果検証 | 2026-08-13 |  | 改善調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | 解像度調整（アップスケーリング / ダウンスケーリング）の効果を検証する |  |  |  |
|  | コントラスト強調・ガンマ補正の効果を検証する |  |  |  |
|  | ノイズ除去・シャープニングの効果を検証する |  |  |  |
|  | 前処理パターンごとに OCR 精度を比較し、効果的な前処理を特定する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | （未実施） |  |  |  |
| 003003 | config.yml パラメータ調整の効果検証 | 2026-08-13 |  | 改善調査 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `ocr-worker/config.yml` の `layout_extraction.score_thr`、`line_ocr.additional_elements` などを調整する |  |  |  |
|  | パラメータパターンごとに OCR 精度を比較する |  |  |  |
|  | 改善効果と処理時間への影響を評価する |  |  |  |
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

