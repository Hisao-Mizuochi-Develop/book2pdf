# 作業ログ

本ドキュメントは、book2pdf プロジェクトのバックエンドタスク実施にあたり実行したコマンドとその結果を記録したものです。

## 2026-08-11 Python 仮想環境の作成とパッケージインストール

### 目的

FastAPI バックエンドに必要な Python パッケージを仮想環境にインストールする。

### 前提

- `backend/requirements.txt` が作成済み
- Python 3 がインストール済み

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
python -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

### 結果

- 仮想環境 `backend/.venv` を作成
- 以下のパッケージをインストール
  - fastapi-0.128.8
  - uvicorn-0.39.0
  - python-multipart-0.0.20
  - pymupdf-1.26.5
  - pydantic-2.13.4
  - pydantic-settings-2.11.0
- ndlocr_cli は `requirements.txt` でコメントアウトされているため未インストール

### 注意事項

- pip のバージョンが古い（21.2.4）ため、アップグレードを推奨
  - アップグレードコマンド: `/Users/hisao/Documents/work4/sakura/book2pdf/backend/.venv/bin/python -m pip install --upgrade pip`

---

## 2026-08-11 タスク001001：FastAPI プロジェクトの初期構成

### 目的

FastAPI プロジェクトのディレクトリ構成、依存定義、Dockerfile、基本動作確認用テストを作成する。

### 前提

- `backend/.venv` が作成済みであること
- `backend/requirements.txt` が作成済みであること

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend

# ディレクトリ構成の作成
mkdir -p app/core app/models app/routers app/services tests
touch app/__init__.py app/core/__init__.py app/models/__init__.py \
      app/routers/__init__.py app/services/__init__.py tests/__init__.py

# テスト用パッケージの追加インストール
source .venv/bin/activate
pip install pytest httpx

# テストの実行
python -m pytest tests/test_main.py -v
```

### 結果

- 以下のファイルを作成した
  - `app/main.py`：FastAPI アプリケーションエントリポイント
  - `app/core/config.py`：pydantic-settings による設定管理
  - `app/models/job.py`：ジョブ関連の Pydantic モデル
  - `app/services/job_manager.py`：メモリ内ジョブ状態管理サービス
  - `app/routers/jobs.py`：ジョブ関連 API ルーター
  - `tests/test_main.py`：基本動作確認用テスト
  - `run.py`：開発用 Uvicorn 起動スクリプト
  - `Dockerfile`：python:3.11-slim ベースのバックエンドイメージ
- `requirements.txt` に `pytest` と `httpx` を追加した
- `pytest` を実行し、3 件のテストがすべて pass した

### 注意事項

- ローカル開発環境の Python バージョンは 3.9.6 であるため、Python 3.10+ の型注釈記法（`dict | None` など）がそのままでは使えなかった
- 各 Python ファイルの先頭に `from __future__ import annotations` を追加することで対応した
- Docker コンテナ内では Python 3.11 を使用するため、本番環境では型注釈の問題は発生しない

---

## 2026-08-11 Python 仮想環境と Dockerfile のバージョンアップ（3.9 → 3.12）

### 目的

ローカル開発環境と Docker コンテナの Python バージョンを統一し、最新の安定版機能を活用できるようにする。

### 前提

- Homebrew で `python@3.12`（3.12.13）がインストール済み
- `backend/Dockerfile` は `python:3.11-slim` を使用していた
- `backend/.venv` は Python 3.9.6 で作成されていた

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend

# 既存の仮想環境を削除
rm -rf .venv

# Python 3.12 で仮想環境を作成
/opt/homebrew/bin/python3.12 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# pip を最新化
pip install --upgrade pip

# 依存パッケージをインストール
pip install -r requirements.txt
pip install pytest httpx

# テスト実行
python -m pytest tests/test_main.py -v
```

### 結果

- `backend/.venv` を Python 3.12.13 で再作成した
- 依存パッケージが Python 3.12 用のバイナリホイールで正常にインストールされた
- `pytest` を実行し、3 件のテストがすべて pass した
- `backend/Dockerfile` のベースイメージを `python:3.11-slim` から `python:3.12-slim` に更新した

### 注意事項

- `requirements.txt` には `pytest` と `httpx` が含まれているため、別途 `pip install pytest httpx` は不要となった（ただし requirements.txt に追加済みのため重複しても問題ない）
- テスト実行時に `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead` という警告が出力された
  - これは `fastapi.testclient` / `starlette.testclient` の組み合わせに関するもので、現時点ではテストは pass する
  - 必要に応じて `httpx2` の導入やテストクライアントの見直しを検討する
- Python 3.12 にしたことで、`from __future__ import annotations` がなくても `dict | None` などの新しい型注釈が使えるようになった
  - 既存コードの `from __future__ import annotations` は互換性を保つため、そのまま残しても問題ない

---

## 2026-08-11 タスク001002：ZIP アップロード・展開機能の実装

### 目的

FastAPI バックエンドに ZIP アップロード・展開機能を追加し、ジョブに紐づけて OCR 対象の画像ファイル一覧を取得できるようにする。

### 前提

- `backend/.venv` が Python 3.12 で作成済み
- タスク001001 で FastAPI の基本構成が完了済み
- `backend/app/models/job.py`、`app/services/job_manager.py`、`app/routers/jobs.py` が作成済み

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend

# テストの実行
source .venv/bin/activate
python -m pytest tests/test_jobs.py -v
python -m pytest tests/ -v
```

### 結果

- 以下のファイルを作成・更新した
  - `app/models/job.py`：`UPLOADED` 状態を追加、`JobUploadResponse` と `JobResponse.files` を追加
  - `app/services/job_manager.py`：`files` フィールドと `temp_dir` 保存機能を追加
  - `app/services/zip_extractor.py`：ZIP 展開・画像抽出サービスを新規作成
  - `app/routers/jobs.py`：`POST /api/jobs/{job_id}/upload` エンドポイントを追加
  - `tests/test_jobs.py`：5 件のテストを新規作成
  - `backend/docs/backend-system-spec.md`：フォルダ・ファイル構成を更新
  - `backend/docs/tasks.md`：タスク001002 の完了日付と実施結果を追記
- `pytest` を実行し、既存テストを含む 8 件すべて pass した
- フィードバックを受け、各ソースファイルの import 部分に初学者向けのコメントを追加した
- さらに、docs/coding-conventions.md の 2.4 コメントに「コメント行以外のプログラムの各行に原則コメントを記載する」ルールを追加した
- 新ルールに従い、作成済みのすべての backend ソースコードにコメントを追加した
  - 対象ファイル: app/main.py, app/core/config.py, app/models/job.py, app/services/job_manager.py, app/services/zip_extractor.py, app/routers/jobs.py, tests/test_main.py, tests/test_jobs.py

---

## 2026-08-11 タスク001003：ndlocr_cli 連携の実装

### 目的

FastAPI バックエンドに ndlocr_cli 連携機能を追加し、アップロードされた画像に対して OCR 処理を実行できるようにする。

### 前提

- `backend/.venv` が Python 3.12 で作成済み
- タスク001002 で ZIP アップロード・展開機能が完了済み
- ndlocr_cli はローカル開発環境には未インストール

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend

# ndlocr_cli の README を確認
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/README.md
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/main.py
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/cli/core/__init__.py
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/cli/core/inference.py

# テストの実行
source .venv/bin/activate
python -m pytest tests/ -v
```

### 結果

- GitHub 上の ndlocr_cli リポジトリを確認し、`OcrInferrer` クラスが `cfg` dict を受け取って `run()` を実行する形式であることを把握した
- 以下のファイルを作成・更新した
  - `app/services/ocr_engine.py`：BaseOcrEngine / NdloCrOcrEngine / MockOcrEngine を新規作成
  - `app/models/job.py`：JobOcrResponse レスポンスモデルを追加
  - `app/services/job_manager.py`：update_job_with_ocr_result 関数を追加し、COMPLETED / FAILED 状態遷移に対応
  - `app/routers/jobs.py`：POST /api/jobs/{job_id}/ocr エンドポイントを追加
  - `tests/test_ocr.py`：OCR 実行のテストを 5 件新規作成
  - `backend/docs/backend-system-spec.md`：フォルダ・ファイル構成を更新
  - `backend/docs/tasks.md`：タスク001003 の完了日付と実施結果を追記
- `pytest` を実行し、既存テストを含む 13 件すべて pass した

### 注意事項

- ndlocr_cli はローカル開発環境に未インストールのため、`create_ocr_engine()` は自動的に MockOcrEngine を返す
- 実際の ndlocr_cli 動作確認は、ocr-worker コンテナ構築後に実施する
- NdloCrOcrEngine は、ndlocr_cli の single 形式入力（input_root/img/）を作成し、OcrInferrer を呼び出す実装とした
- OCR 結果のテキストは output_root 以下の txt ディレクトリから .txt ファイルを収集して連結する
- `fastapi.testclient` / `starlette.testclient` の組み合わせによる `httpx` の非推奨警告は継続して出力されている
  - 現時点ではテストは pass するため対応保留
- ZIP 展開後の一時ディレクトリは `job_manager` に `temp_dir` として保持する
  - OCR 処理完了までディレクトリを保持する必要がある
  - プロセス再起動時に失われるため、将来の永続化対応時に設計を見直す

---

## 2026-08-11 タスク001004：backend と ocr-worker の連携対応

### 目的

backend コンテナから ocr-worker コンテナの HTTP API を呼び出して、
実際の ndlocr_cli による OCR 処理を実行できるようにする。

### 前提

- ocr-worker コンテナが構築・起動済み
- backend のジョブ管理・ZIP 展開・OCR エンドポイントが実装済み
- ndlocr_cli はローカル開発環境には未インストール

### 実施コマンド

```bash
# backend ローカルテスト実行
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend
python -m pytest tests/ -q

# Docker コンテナのビルド・起動
cd /Users/hisao/Documents/work4/sakura/book2pdf
docker compose build --no-cache
docker compose up -d

# ヘルスチェック確認
curl -s http://localhost:8000/health
curl -s http://localhost:8001/health

# サンプル画像を ZIP 圧縮
cp "sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/001.png" \
   "sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/002.png" \
   /tmp/book2pdf-test/
cd /tmp/book2pdf-test && zip sample.zip *.png

# ジョブ作成
curl -s -X POST http://localhost:8000/api/jobs/ | jq

# ZIP アップロード
curl -s -X POST \
  -F "file=@/tmp/book2pdf-test/sample.zip;type=application/zip" \
  http://localhost:8000/api/jobs/ad889bc6-6613-44c6-a14b-e33e28a0477c/upload | jq

# OCR 実行
curl -s --max-time 600 \
  -X POST http://localhost:8000/api/jobs/ad889bc6-6613-44c6-a14b-e33e28a0477c/ocr | jq
```

### 結果

- backend のローカル pytest で 13 件すべて pass
- Docker コンテナのビルド・起動に成功
- backend（:8000/health）と ocr-worker（:8001/health）の両方が `{"status":"ok"}` を返すことを確認
- サンプル画像 2 枚（001.png, 002.png）で OCR テストを実施
- ジョブ状態が `completed` になり、認識テキストがレスポンスに含まれることを確認
  - 例：「咸毅成[著]」「RAC」「精度改善」などの表記を認識

### 注意事項

- ZIP アップロード時は `Content-Type: application/zip` を明示的に指定する必要がある
  - curl では `-F "file=@sample.zip;type=application/zip"` の形式を使用
- OCR 処理は数分かかるため、curl では `--max-time 600` など長めのタイムアウトを設定
- ローカル pytest では共有ボリューム `/data/extracted` が使用できないため、
  `backend/tests/conftest.py` で `EXTRACT_BASE_DIR` 環境変数に一時ディレクトリを設定
  - `pytest_configure` フックを使用し、テストファイルの import より前に環境変数を設定

---

## 2026-08-11 タスク002001：SSE 進捗通知機能の実装

### 目的

OCR 処理の進捗を Server-Sent Events（SSE）でリアルタイムに配信する機能を実装する。

### 前提

- backend と ocr-worker が Docker Compose で分離している
- 両コンテナ間で `/data/progress` 共有ボリュームを使用する
- `backend/tests/conftest.py` でテスト用の一時ディレクトリ設定が行われている

### 実施コマンド

```bash
# backend ローカルテスト実行
# PROGRESS_POLL_INTERVAL を短縮して高速に実行
# conftest.py で自動設定済み
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend
python -m pytest tests/test_progress.py -q

# すべての backend テスト実行
python -m pytest tests/ -q
```

### 結果

- `backend/tests/test_progress.py` の 3 件のテストが pass
- 既存の `test_main.py` / `test_jobs.py` / `test_ocr.py` も含めた全テストが pass

### 注意事項

- SSE エンドポイントは進捗ファイル `/data/progress/{job_id}.json` をポーリングして配信する
- 本番環境では `PROGRESS_POLL_INTERVAL` を省略し、デフォルトの 0.5 秒間隔を使用する
- テスト時は `conftest.py` で `PROGRESS_POLL_INTERVAL=0.05` を設定し、高速化している
- プロキシ環境で SSE が不安定な場合は、別途ポーリング方式（005001）を検討する

---

## 2026-08-11 タスク003001：検索可能 PDF 生成機能の実装

### 目的

OCR 結果（ndlocr_cli の `.sorted.xml` と画像ファイル）から検索可能 PDF を生成し、
`GET /api/jobs/{job_id}/pdf` でダウンロードできるようにする。

### 前提

- タスク001004 までで ZIP アップロード・OCR 実行・ocr-worker 連携が完了済み
- `backend/.venv` が Python 3.12 で作成済み
- `pymupdf`（fitz）が `requirements.txt` 経由でインストール済み

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend

# 特定のテストファイルを実行
.venv/bin/python -m pytest tests/test_pdf.py -v

# 進捗通知テストの動作確認
.venv/bin/python -m pytest tests/test_progress.py -v --timeout=15

# すべての backend テストを実行
.venv/bin/python -m pytest tests/ -v --timeout=60
```

### 結果

- 以下のファイルを作成・更新した
  - `app/services/xml_parser.py`：ndlocr_cli の `.sorted.xml` をパースし、ページ画像パス・テキスト・座標を取得するサービスを新規作成
  - `app/services/pdf_generator.py`：PyMuPDF（fitz）で画像を背景・認識テキストを透明テキストレイヤーとして配置し、検索可能 PDF を生成するサービスを新規作成
  - `app/services/job_manager.py`：`update_job_with_pdf_path()` 関数を追加し、ジョブ情報への PDF パス保存に対応
  - `app/routers/jobs.py`：`GET /api/jobs/{job_id}/pdf` エンドポイントを追加し、OCR 成功後に PDF 生成を自動実行する処理を追加
  - `tests/test_pdf.py`：PDF 生成・XML 解析・ダウンロード API の正常系・異常系テストを 7 件新規作成
  - `tests/test_progress.py`：SSE 進捗 generator を直接 `async for` でテストする形に書き換え
  - `backend/docs/backend-system-spec.md`：フォルダ・ファイル構成と API 一覧を更新
  - `backend/docs/caveats.md`：`TestClient` 経由の SSE テストの不安定性を追記
  - `backend/docs/tasks.md`：タスク003001 の完了日付と実施結果を追記
- `pytest` を実行し、backend の全 23 件のテストが pass した

### 注意事項

- ndlocr_cli の出力 XML にはページ順を示す `.sorted.xml` ファイルがある
  - `xml_parser.py` では `*_?.sorted.xml` を glob 検索し、ファイル名でソートして順序を決定する
- PDF 生成時に元画像が見つからない場合、`ValueError` を発生させる
  - テストでは存在しない画像パスを指定し、エラー発生を確認している
- `fastapi.testclient.TestClient` 経由の `StreamingResponse` テストは不安定だった
  - 非同期 generator が yield した chunk がクライアント側に確実に届かず、テストが停止・失敗する
  - 対応として `_progress_event_generator` を直接 import して `async for` で検証する形に変更した
  - 詳細は `backend/docs/caveats.md` の「`fastapi.testclient.TestClient` 経由の SSE テストの不安定性」を参照
- PDF 生成は OCR 成功後に自動実行されるが、PDF 生成に失敗しても OCR 結果は返す
  - 失敗時はジョブメッセージに「OCR は成功しましたが PDF 生成に失敗しました」と記録する

---

## 2026-08-11 タスク003001続き：PDF ダウンロード API の結合テスト

### 目的

backend / ocr-worker / frontend を連携させて、ZIP アップロード → OCR → PDF ダウンロードまでの結合テストを実施する。

### 前提

- タスク003001 で PDF 生成機能の実装とユニットテストが完了していること
- Docker Compose で backend / ocr-worker / frontend が起動していること
- テスト用 ZIP ファイルが用意されていること

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# すべてのサービスを最新イメージで起動
docker compose up -d --build backend

# OpenAPI エンドポイント一覧確認
curl -s http://localhost:8000/openapi.json | jq '.paths | keys'

# 結合テスト: ジョブ作成 → ZIP アップロード → OCR → PDF ダウンロード
JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
echo "Job ID: $JOB_ID"

curl -s -X POST -F "file=@/tmp/book2pdf-test/sample.zip;type=application/zip" \
  "http://localhost:8000/api/jobs/$JOB_ID/upload" | jq .

curl -s --max-time 600 -X POST "http://localhost:8000/api/jobs/$JOB_ID/ocr" &
OCR_PID=$!
for i in $(seq 1 120); do
  sleep 5
  STATUS=$(curl -s "http://localhost:8000/api/jobs/$JOB_ID" | jq -r '.status')
  echo "$(date +%H:%M:%S) status: $STATUS"
  [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] && break
done
wait $OCR_PID 2>/dev/null

curl -s -o /tmp/book2pdf-test/output.pdf -w "HTTP status: %{http_code}\n" \
  "http://localhost:8000/api/jobs/$JOB_ID/pdf"
file /tmp/book2pdf-test/output.pdf
```

### 結果

- 初回のテストで `GET /api/jobs/{job_id}/pdf` が 404 エラー（`{"detail":"Not Found"}`）になった
  - OpenAPI ドキュメントにも `/api/jobs/{job_id}/pdf` が含まれていなかった
- 原因は backend コンテナが最新のソースコードで再ビルドされていなかったこと
  - ホスト側の `backend/app/routers/jobs.py` には `download_pdf` 関数が存在していたが、
    実行中のコンテナイメージには含まれていなかった
- 対応として `docker compose up -d --build backend` を実行し、backend イメージを再ビルド・再起動した
- 再起動後、OpenAPI ドキュメントに `/api/jobs/{job_id}/pdf` が表示されるようになった
- 再度結合テストを実施し、以下を確認した
  - `POST /api/jobs/` でジョブ作成に成功
  - `POST /api/jobs/{job_id}/upload` で ZIP アップロードに成功（画像 2 枚を検出）
  - `POST /api/jobs/{job_id}/ocr` で OCR が完了し `completed` ステータスになる
  - `GET /api/jobs/{job_id}/pdf` で HTTP 200、`Content-Type: application/pdf`、2 ページの PDF が取得できる

### 注意事項

- backend コードを変更した後は、必ず `docker compose up -d --build backend` などでイメージを再ビルドすること
  - 単なる `docker compose restart backend` ではホスト側のソース変更が反映されない
- テスト用のジョブは backend のメモリ内に保持されているため、backend 再起動後は過去のジョブにアクセスできなくなる
  - 永続化は別タスク（004001）で対応予定

