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

---

## 2026-08-12 全体横断タスクの管理移行（タスク 006001 → `./docs/tasks.md`）

### 目的

`backend/docs/tasks.md` に誤作成したモジュール横断タスク「結合テスト手順書の作成（タスク 006001）」を、`.clinerules` で定める `./docs/` 配下のタスク管理表に移行する。

### 前提

- `./docs/tasks.md` / `./docs/work_log.md` / `./docs/caveats.md` を新規作成済み
- `backend/docs/tasks.md` のユースケース 006 を削除済み

### 実施コマンド

```bash
# backend/docs/tasks.md からユースケース 006 を削除
# backend/docs/work_log.md から 006001 のエントリを削除
# ./docs/tasks.md / ./docs/work_log.md に内容を移行

# git 状態確認
cd /Users/hisao/Documents/work4/sakura/book2pdf
git status --short
```

### 結果

- `backend/docs/tasks.md` からユースケース 006「結合テスト・運用ドキュメントの整備」を削除した
- `backend/docs/work_log.md` から「2026-08-12 結合テスト手順書の作成（タスク 006001）」のエントリを削除した
- `./docs/tasks.md` の 001002 として「結合テスト手順書の作成」を追加した
- `./docs/work_log.md` の 2026-08-12 エントリとして結合テスト手順書作成を記録した

### 注意事項

- 横断的なタスクは原則 `./docs/tasks.md` で管理し、`<module>/docs/tasks.md` にはそのモジュール固有のタスクのみを記載する
- 今後 `./docs/` 配下を変更する際は `.clinerules` に基づき、ユーザーに変更箇所を提案・許可を得てから実施する

---

## 2026-08-12 タスク004001：backend DEBUG ログ・計測処理の追加

### 目的

性能計測時に各処理の所要時間を DEBUG ログで確認できるようにする。

### 前提

- タスク001004 までで backend / ocr-worker 連携が完了していること
- `backend/app/services/zip_extractor.py`、`pdf_generator.py`、`app/routers/jobs.py` が存在すること
- `docker-compose.yml` で backend サービスが定義されていること

### 実施コマンド

```bash
# ソース変更は手動で実施
# 以下、変更後のファイル内容確認
cd /Users/hisao/Documents/work4/sakura/book2pdf

git diff -- backend/app/services/zip_extractor.py
git diff -- backend/app/services/pdf_generator.py
git diff -- backend/app/routers/jobs.py
git diff -- docker-compose.yml
```

### 結果

- 以下のファイルに `LOG_LEVEL` 環境変数に応じたロガー設定と DEBUG ログを追加した
  - `backend/app/services/zip_extractor.py`: ZIP 解凍開始・完了、展開ファイル数、処理時間を DEBUG ログに出力
  - `backend/app/services/pdf_generator.py`: PDF 生成開始・完了、処理時間を DEBUG ログに出力
  - `backend/app/routers/jobs.py`: OCR エンドポイント全体の処理開始・完了、処理時間を DEBUG ログに出力
- `docker-compose.yml` の backend サービスに `LOG_LEVEL=DEBUG` を追加した
- `backend/docs/tasks.md` にタスク 004001 を追記した
- `backend/docs/work_log.md` に本エントリを追記した

### 注意事項

- 本変更により `LOG_LEVEL=DEBUG` 時に標準出力に多くの DEBUG ログが出力される
- 本番環境では `LOG_LEVEL=INFO`（または `WARNING`）に設定することを推奨する
- ログ出力は `logging.basicConfig` で設定しているため、既存の他のロガー設定との競合には注意する

---

## 2026-08-12 タスク003003：PDF 白紙問題の原因特定・修正・検証

### 目的

生成された PDF が白紙になっている原因を特定し、修正する。

### 前提

- タスク003001 で検索可能 PDF 生成機能が実装済み
- Docker Compose で backend / ocr-worker が起動できること
- テスト用 3 ページ画像が `sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/002.png` などに存在すること
- ホスト側で `jq` がインストールされていること

### 実施コマンド

```bash
# プロジェクトルートに移動
cd /Users/hisao/Documents/work4/sakura/book2pdf

# backend / ocr-worker コンテナを最新ソースで再ビルド・再起動
docker compose up -d --build backend ocr-worker

# テスト用 3 ページ ZIP を作成
mkdir -p /tmp/book2pdf-test2
cp "sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/002.png" \
   "sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/003.png" \
   "sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/004.png" \
   /tmp/book2pdf-test2/
cd /tmp/book2pdf-test2 && zip -q sample-3pages-v2.zip 002.png 003.png 004.png

# ジョブ作成
JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
echo "Job ID: $JOB_ID"
echo "$JOB_ID" > /tmp/book2pdf-test2/job_id_v3.txt

# ZIP アップロード
curl -s -X POST \
  -F "file=@/tmp/book2pdf-test2/sample-3pages-v2.zip;type=application/zip" \
  "http://localhost:8000/api/jobs/$JOB_ID/upload" | jq .

# OCR 実行（バックグラウンドで開始し、ステータスをポーリング）
curl -s --max-time 1200 -X POST "http://localhost:8000/api/jobs/$JOB_ID/ocr" &
OCR_PID=$!
for i in $(seq 1 240); do
  sleep 5
  STATUS=$(curl -s "http://localhost:8000/api/jobs/$JOB_ID" | jq -r '.status')
  echo "$(date +%H:%M:%S) status: $STATUS"
  [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] && break
done
wait $OCR_PID 2>/dev/null

# PDF ダウンロード
curl -s -o ./output_v3.pdf -w "HTTP status: %{http_code}, Content-Type: %{content_type}, Size: %{size_download}\n" \
  "http://localhost:8000/api/jobs/$JOB_ID/pdf"
file ./output_v3.pdf
ls -la ./output_v3.pdf

# PDF ページを PNG にレンダリングして元画像と比較
python - << 'PY'
import fitz
doc = fitz.open('./output_v3.pdf')
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=150)
    out = f'./output_v3_page{i+1}.png'
    pix.save(out)
    print(f'saved {out}: {pix.width}x{pix.height}')
PY

# PDF 内のテキストと bbox を抽出
python - << 'PY'
import fitz
doc = fitz.open('./output_v3.pdf')
for i, page in enumerate(doc):
    print(f'=== Page {i+1} ===')
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                text = span['text'].replace('\n', '\\n')
                print(f'  text="{text}" bbox={span["bbox"]}')
PY
```

### 結果

- PDF 白紙問題の原因を特定した
  - OCR 結果 XML の `image_name` 属性が `002_L.jpg` のようになっており、元画像（`002.png`）と拡張子・サフィックスが一致しなかった
  - `pdf_generator.py` の `_find_image_path()` は完全一致を要求していたため、背景画像が見つからず白紙 PDF（テキストのみの極小 PDF）になっていた
- `backend/app/services/pdf_generator.py` を修正した
  - 画像名から `_L` / `_R` サフィックスを除去
  - 拡張子を無視して stem（ファイル名本体）一致で元画像を探すように変更
- backend イメージを再ビルド・再起動し、修正を反映した
- 3 ページ画像で OCR/PDF 生成を再実行した結果、以下を確認した
  - PDF サイズ: 1,445 バイト → 5,634,519 バイトに増加
  - ページ数: 3 ページ
  - backend ログ: `画像ファイルを発見しました（stem 一致）` / `PDF ページに画像を配置しました` が 3 ページ分出力
  - 元画像サイズ（664×942 px）と PDF ページサイズ（664×942 pt）が一致
- PDF 内テキスト抽出結果
  - Page 1: テキストを検出できず（透明テキストのため PyMuPDF では抽出困難な可能性あり）
  - Page 2: `························` bbox=(108.0, 86.4, 248.1, 115.3)
  - Page 3: `······························!` bbox=(97.0, 73.8, 234.9, 95.8)
- 背景画像配置は正常化したが、Page 2, 3 の透明テキストがページ左上に偏り、「・」の繰り返しで表示される問題が残っている

### 注意事項

- backend コードを変更した後は `docker compose up -d --build backend` でイメージを再ビルドすること
  - `docker compose restart backend` ではホスト側のソース変更が反映されない
- DEBUG ログは `LOG_LEVEL=DEBUG` 時にのみ出力される
- 透明テキストは PDF ビューアでは選択可能だが、PyMuPDF の `get_text('dict')` では検出できない場合がある
- 次のステップ: Page 2, 3 のテキスト配置ズレと「・」繰り返し問題のデバッグ

---

## 2026-08-12 タスク003004〜003006：PDF 透明テキストの配置ズレとフォント fallback 調査

### 目的

PDF 生成後に確認された以下の 2 つの問題を調査し、原因を特定する。

1. Page 2, 3 の透明テキストがページ左上に偏り、「・」の繰り返しで表示される
2. テキストの位置が元画像の文字位置と大きくずれている

### 前提

- backend コンテナが起動済み（`book2pdf-backend`）
- ジョブ `6971e033-eeea-4bbc-8092-63049a5e85a9` の OCR 結果と PDF が生成済み
- 作業ディレクトリは `/Users/hisao/Documents/work4/sakura/book2pdf`

### 実施コマンド

```bash
# コンテナ内の PDF ファイルをホストにコピー
docker cp book2pdf-backend:/data/pdfs/6971e033-eeea-4bbc-8092-63049a5e85a9.pdf ./6971e033-eeea-4bbc-8092-63049a5e85a9_20260812_110212.pdf

# PDF ページを PNG にレンダリング
source backend/.venv/bin/activate
python - << 'PY'
import fitz
doc = fitz.open('./6971e033-eeea-4bbc-8092-63049a5e85a9_20260812_110212.pdf')
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=150)
    out = f'./6971e033_20260812_page{i+1}.png'
    pix.save(out)
    print(f'saved {out}: {pix.width}x{pix.height}')
PY

# PDF 内の透明テキストを抽出
python - << 'PY'
import fitz
doc = fitz.open('./6971e033-eeea-4bbc-8092-63049a5e85a9_20260812_110212.pdf')
for i, page in enumerate(doc):
    print(f'=== Page {i+1} ===')
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                print(f'  text="{span["text"]}" bbox={span["bbox"]}')
PY

# OCR 結果 XML をコンテナからコピー
docker cp book2pdf-backend:/data/extracted/6971e033-eeea-4bbc-8092-63049a5e85a9/output_20260812104515/input/xml/input.sorted.xml ./input_6971e033.sorted.xml

# XML を解析して LINE 要素の座標とテキストを一覧表示
python - << 'PY'
import xml.etree.ElementTree as ET
root = ET.parse('./input_6971e033.sorted.xml').getroot()
for page_idx, page_elem in enumerate(root.findall('PAGE')):
    print(f'=== Page {page_idx+1} (size={page_elem.get("WIDTH")}x{page_elem.get("HEIGHT")}) ===')
    for line in page_elem.iter('LINE'):
        print(f'  x={line.get("X")} y={line.get("Y")} w={line.get("WIDTH")} h={line.get("HEIGHT")} text="{line.get("STRING")}"')
PY
```

### 結果

- PDF 内の透明テキストを抽出したところ、Page 1〜3 すべてでテキストが検出できた
  - これまでの `output_v3.pdf` では Page 1 のみ検出できなかったのは、調査対象の PDF が異なっていたため
- PDF 透明テキストの内容と OCR 結果 XML の `STRING` 属性は一致
  - PDF 生成処理（xml_parser.py → pdf_generator.py）はテキスト内容を正しく受け渡している
- PDF ページ画像の文言との差異は、OCR エンジン（ndlocr_cli）の認識ミスに起因
  - 具体例：
    - `RAG` → `RAC`
    - `Improving` → `mproving`
    - `GPT-4` → `〓PT-4`
    - `LLM` → `〓lm`
    - `前処理` → `K前処理`（チェックマークの誤認識）
    - `年` / `理` / `利` などが異体字（年 / 理 / 利）に変換されている
- テキスト位置のずれの原因は、XML ページサイズと PDF ページサイズの不一致
  - XML ページサイズ：Page 1: 698×965、Page 2: 686×958、Page 3: 666×943
  - PDF ページサイズ（元画像サイズ）：664×942
  - 現在の `pdf_generator.py` は XML 座標を PDF 座標にそのまま使っており、スケール変換が未実装
- Page 2, 3 のテキストが「・」の繰り返しで表示されていた原因は、backend コンテナに日本語フォントが未インストールだったこと
  - PyMuPDF が文字を「・」に fallback していた
  - `backend/Dockerfile` に `fonts-noto-cjk` を追加し、`pdf_generator.py` のフォント候補パスを Linux 用に修正することで解消
- `<BLOCK>` 配下の `<LINE>` 要素が取得できていなかった問題を `xml_parser.py` を `iter("LINE")` に修正することで解消
- PDF ダウンロード時に `{job_id}_YYYYMMDD_HHMMSS.pdf` 形式のユニークファイル名を返すよう `jobs.py` を修正

### 注意事項

- PDF 内の透明テキストは `page.get_text('dict')` で抽出可能だが、フォントによっては文字が「・」に fallback されることがある
- テキスト位置の正確な配置には、XML 座標系から PDF 座標系へのスケール変換が必要
  - scale_x = pdf_width / xml_width
  - scale_y = pdf_height / xml_height
  - pdf_x = xml_x * scale_x
  - pdf_y = pdf_height - (xml_y + xml_height) * scale_y
- OCR 認識精度の改善（RAG→RAC など）は、ndlocr_cli 側のモデル・前処理・推論パラメータを調査する必要がある
- 次のステップ: タスク 003007 で座標スケーリングを実装し、OCR 認識精度の改善策を調査する

## 2026-08-12 003007 OCR 結果の座標スケーリング実装と検証

### 目的

OCR 結果 XML のページサイズと PDF ページサイズ（元画像サイズ）が異なることによる透明テキストの位置ずれを修正する。

### 前提

- タスク 003004/003005 で XML ページサイズと PDF ページサイズの差異が原因であることを特定済み
- 元画像サイズは 664×942、XML ページサイズは Page 1: 698×965、Page 2: 686×958、Page 3: 666×943
- `backend/app/services/xml_parser.py` と `backend/app/services/pdf_generator.py` を修正する

### 実施コマンド

```bash
# 1. ソースコード修正
# backend/app/services/xml_parser.py: OcrPage に xml_width / xml_height を追加
# backend/app/services/pdf_generator.py: _insert_text_line() にスケーリング変換を実装

# 2. テスト修正
# backend/tests/test_pdf.py: 日時付きファイル名に対応

# 3. ローカルテスト実行
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend
source .venv/bin/activate
python -m pytest tests/ -q

# 4. Docker イメージ再ビルド・再起動
cd /Users/hisao/Documents/work4/sakura/book2pdf
docker compose up -d --build backend

# 5. 結合テスト：ジョブ作成 → アップロード → OCR → PDF ダウンロード
JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
echo "$JOB_ID" > /tmp/book2pdf-test2/job_id_scaled.txt
curl -s -X POST -F "file=@/tmp/book2pdf-test2/sample-3pages-v2.zip;type=application/zip" \
  "http://localhost:8000/api/jobs/$JOB_ID/upload" | jq .
curl -s -X POST "http://localhost:8000/api/jobs/$JOB_ID/ocr" | jq .

# 6. PDF ダウンロード
curl -s -D /tmp/book2pdf-test2/headers_scaled.txt \
  -o /tmp/book2pdf-test2/output_scaled.pdf \
  "http://localhost:8000/api/jobs/$JOB_ID/pdf"

# 7. PDF テキスト bbox 抽出
cd /Users/hisao/Documents/work4/sakura/book2pdf
python3 - <<'PY'
import fitz
doc = fitz.open('/tmp/book2pdf-test2/output_scaled.pdf')
for page_idx in range(len(doc)):
    page = doc[page_idx]
    print(f'=== Page {page_idx + 1} ===')
    print(f'Page size: {page.rect.width} x {page.rect.height}')
    for block in page.get_text('dict')['blocks'][:10]:
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                bbox = span['bbox']
                print(f"  bbox=({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}) text='{span['text'][:40]}'")
                break
            break
        break
doc.close()
PY

# 8. XML 座標確認
docker compose exec -T backend python3 <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
xml_path = Path('/data/extracted/0b094576-5b25-4490-94ed-36a9403b306c/output_20260812121350/input/xml/input.sorted.xml')
root = ET.parse(xml_path).getroot()
for idx, page in enumerate(root.findall('PAGE')):
    print(f'=== XML Page {idx+1} ===')
    print(f"  WIDTH={page.get('WIDTH')} HEIGHT={page.get('HEIGHT')}")
    for line in list(page.iter('LINE'))[:5]:
        print(f"  X={line.get('X')} Y={line.get('Y')} W={line.get('WIDTH')} H={line.get('HEIGHT')} TEXT='{line.get('STRING')[:40]}'")
PY

# 9. 作業ディレクトリに PDF をコピー
cp /tmp/book2pdf-test2/output_scaled.pdf /Users/hisao/Documents/work4/sakura/book2pdf/output_scaled_20260812_121956.pdf
```

### 結果

- `backend/app/services/xml_parser.py` の `OcrPage` に `xml_width` / `xml_height` フィールドを追加
- `backend/app/services/pdf_generator.py` の `_insert_text_line()` に XML 座標 → PDF 座標のスケーリング変換を実装
  - `scale_x = pdf_width / xml_width`
  - `scale_y = pdf_height / xml_height`
  - `pdf_x = xml_x * scale_x`
  - `pdf_y = pdf_height - (xml_y + xml_line_height) * scale_y`
  - 幅・高さ・フォントサイズも同様にスケーリング
- デバッグ目的で透明テキストの色を緑色（`color=(0, 1, 0)`、`fill_opacity=0.5`）に変更
- ローカル pytest で 23 件すべて pass
- Docker イメージ再ビルド・再起動後、3 ページ画像で結合テストを実施
- PDF ページサイズは元画像サイズ 664×942 と一致
- PyMuPDF でテキスト bbox を抽出し、XML 座標 → PDF 座標へのスケーリングが数値的に適用されていることを確認
  - 例：Page 1「咸毅成[著]」XML X=531 → PDF x=505.1（scale_x=664/698=0.9513）
  - 例：Page 1「咸毅成[著]」XML Y=840, H=24 → PDF y_top≈98.3、y_bottom≈122.0
- ndlocr_cli の認識ミス（RAG→RAC、Improving→mproving、GPT-4→〓PT-4 など）は OCR エンジン側の問題であり、本タスクのスコープ外

### 注意事項

- PyMuPDF の `insert_text()` は baseline（文字の下端）を基準に配置するため、抽出された bbox の y 値は XML 座標からの単純変換値と完全には一致しない
- 緑色半透明テキストはデバッグ用途であり、本番運用時には元の透明（`color=(0, 0, 0)`、`fill_opacity=0`）に戻す必要がある
- OCR 認識精度の改善は `ocr-worker` 側のモデル・前処理・推論パラメータ調整が必要

---

## 2026-08-12 タスク003008：PDF 透明テキスト色の濃い緑化と OCR 精度改善調査

### 目的

OCR 結果を目視確認しやすくするため、PDF 透明テキストの色を濃い緑に変更するとともに、ndlocr_cli の CPU 実行環境での OCR 精度改善策を調査する。

### 前提

- タスク 003007 で座標スケーリングが実装済み
- 最新の生成 PDF `output_scaled_20260812_121956.pdf` が作業ディレクトリに存在する
- `backend/app/services/pdf_generator.py` のテキスト色を変更する

### 実施コマンド

```bash
# 1. 最新の PDF を確認
ls -lt /Users/hisao/Documents/work4/sakura/book2pdf/*.pdf | head -5

# 2. PDF からテキストと bbox を抽出
cd /Users/hisao/Documents/work4/sakura/book2pdf
python3 - <<'PY'
import fitz
from pathlib import Path
pdf_path = Path('output_scaled_20260812_121956.pdf')
doc = fitz.open(str(pdf_path))
print(f'Pages: {len(doc)}')
for i, page in enumerate(doc[:3]):
    text = page.get_text()
    print(f'--- Page {i+1} (chars={len(text)}) ---')
    print(text[:1000])
    print()
doc.close()
PY

# 3. PDF ページを PNG にレンダリングして目視確認
python3 - <<'PY'
import fitz
from pathlib import Path
pdf_path = Path('output_scaled_20260812_121956.pdf')
doc = fitz.open(str(pdf_path))
for i, page in enumerate(doc[:3]):
    pix = page.get_pixmap(dpi=150)
    pix.save(f'page{i+1}_preview.png')
    print(f'saved page{i+1}_preview.png')
doc.close()
PY

# 4. OCR 結果 XML の先頭を確認
head -100 /Users/hisao/Documents/work4/sakura/book2pdf/input_6971e033.sorted.xml

# 5. ndlocr_cli の README と config.yml を確認
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/README.md | head -200
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/config.yml

# 6. GitHub Issues を確認（精度・モデル関連）
curl -sL "https://api.github.com/repos/ndl-lab/ndlocr_cli/issues?state=all&per_page=30" | python3 -m json.tool | grep -E '"title"|"number"' | head -60
curl -sL "https://api.github.com/repos/ndl-lab/ndlocr_cli/issues/41" | python3 -m json.tool | grep -E '"title"|"body"|"number"'
curl -sL "https://api.github.com/repos/ndl-lab/ndlocr_cli/issues/29" | python3 -m json.tool | grep -E '"title"|"body"|"number"'

# 7. backend ローカルテスト実行
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend
source .venv/bin/activate
python -m pytest tests/ -q
```

### 結果

- `backend/app/services/pdf_generator.py` の透明テキスト色を `color=(0, 0.5, 0)`、`fill_opacity=0.8` に変更
  - コメントも「デバッグ目的で color を緑色、fill_opacity を 0.5 に設定して目視確認しやすくする」から、目視確認用の設定に更新
- `output_scaled_20260812_121956.pdf` のテキスト抽出結果を確認
  - Page 1: 咸毅成[著]、RAC、精度改善、mprovingAccuracy in、Retrieval‑Augmented generation など
  - Page 2: 「本書をお読みになる前に」の本文が縦書き風に配置されている
  - Page 3: 「はじめに」の本文が横書きで配置されている
- PDF ページ画像をブラウザで目視評価
  - Page 1: タイトル・著者名が緑色で重ねられているが、一部のテキストが重複して表示されている
  - Page 2: 縦書きの注意書きテキストが緑色で表示されている
  - Page 3: 横書きの本文が緑色で表示されている
- OCR 精度問題を再確認
  - `RAG` → `RAC`
  - `Improving` → `mproving`
  - `GPT-4` → `〓PT-4`
  - `LLM` → `〓lm`
  - チェックマーク → `K`（例：`前処理` → `K前処理`）
  - 異体字変換（`年` → `年`、`理` → `理`、`利` → `利` など）
- ndlocr_cli の調査結果
  - 公式は GPU（CUDA 11.1/12.1）前提で、CPU 実行は非公式
  - `config.yml` で `layout_extraction.score_thr`、`line_ocr.additional_elements`、`line_order`、`ruby_read` などが調整可能
  - GitHub Issues #41: 日本語は高精度だが英語は日本語ほど出ない
  - GitHub Issues #29: 縦書き・横書きの明示的指定は不可、自動判定
  - GitHub Issues #48: 版面認識モデルのファインチューニングは可能だが独自データセットが必要
- Apple Silicon（M2）での GPU 実行についてユーザーと協議
  - ndlocr_cli は NVIDIA CUDA 前提のため、MPS（Metal Performance Shaders）対応は mmdet/mmcv との互換性で困難
  - ユーザーは「CPU 最適化を進める」方針を選択
- CPU 最適化の次ステップを特定
  - `ocr-worker/config.yml` の調整（`layout_extraction.score_thr`、`line_ocr.additional_elements`）
  - 入力画像の前処理改善（解像度・コントラスト・ノイズ除去）
  - 必要に応じて ndlocr_cli のファインチューニング検討

### 注意事項

- PDF テキスト色の変更は backend のみの変更で、OCR エンジン側には影響しない
- OCR 認識精度の改善には ocr-worker 側の設定変更・前処理・モデル調整が必要
- CPU 最適化の効果には限界があり、最終的には NVIDIA GPU 環境への移行が最も確実な改善策

---

## 2026-08-12 タスク003008：backend ローカルテスト実行

### 目的

`pdf_generator.py` のテキスト色変更後、backend の全テストが引き続き pass することを確認する。

### 前提

- `backend/.venv` が Python 3.12 で作成済み
- `backend/app/services/pdf_generator.py` のテキスト色を変更済み

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend
source .venv/bin/activate
python -m pytest tests/ -q
```

### 結果

- backend の全 23 件のテストが pass した
- 既存の DeprecationWarning（httpx2 / SwigPyObject）は継続して出力されるが、テスト結果に影響なし

### 注意事項

- テスト色変更は `_insert_text_line()` の insert_text オプションのみの変更であり、テストで検証している PDF 生成の成否や構造には影響しない

---

## 2026-08-12 タスク003009：PDF テキストY座標逆転問題の仮修正

### 目的

生成された PDF でテキストの Y 軸配置が上下逆転している問題を、XML 座標系が正しいという仮定のもとで仮修正する。

### 前提

- タスク 003008 で PDF 目視評価を実施済み
- `backend/app/services/pdf_generator.py` の `_insert_text_line()` に Y 座標変換の問題があることをユーザーが指摘
- `backend/.venv` が Python 3.12 で作成済み

### 実施コマンド

```bash
# ソースコード確認
cd /Users/hisao/Documents/work4/sakura/book2pdf
code backend/app/services/pdf_generator.py

# 修正後のローカルテスト実行
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend
source .venv/bin/activate
python -m pytest tests/ -q
```

### 結果

- 原因を特定：`pdf_y = pdf_height - (xml_y + xml_line_height) * scale_y` では、XML 座標系（左上原点）の**下端**を基準に PDF 座標系（左下原点）へ変換していた
  - そのため、XML で `xml_y` が大きい（= 画像の下側に位置する）テキストほど、PDF 上では小さい `pdf_y`（= 上側）に配置され、上下が逆転していた
- 仮修正：`pdf_y = pdf_height - (xml_y * scale_y) - font_size` に変更
  - XML の**上端** `xml_y` を基準に変換し、PyMuPDF の `insert_text()` が baseline（文字の下端）を基準に配置することを考慮して、フォントサイズ分下げた
- `backend/app/services/pdf_generator.py` を仮修正
- backend のローカル pytest で 23 件すべて pass した

### 注意事項

- 今回の仮修正は「XML 座標系が正しい」という前提に基づく。本当に正しいかはタスク 003010 で調査する
- Docker コンテナで結合テストする際は、`docker compose up -d --build backend` でイメージを再ビルドすること
- 修正後の PDF はまだ Docker 結合テストでの目視確認が必要

---

## 2026-08-12 タスク003010：PDF テキストY座標逆転問題の根本調査（XML座標系 vs PDF座標系）

### 目的

OCR 結果 XML の座標系と PyMuPDF の `insert_text()` の座標系を調査し、正しい Y 座標変換式を導出する。

### 前提

- タスク 003009 で仮修正を実施済み
- `input_6971e033.sorted.xml` と `output_scaled_20260812_121956.pdf` が作業ディレクトリに存在する
- `backend/.venv` が Python 3.12 で作成済み
- PyMuPDF、元画像ファイルにアクセス可能

### 実施計画

1. ndlocr_cli の XML 座標系を調査する
   - GitHub リポジトリのソースコード・ドキュメントから `<PAGE>` / `<LINE>` の X, Y, WIDTH, HEIGHT の定義を確認
   - 特に Y がページ上端からの距離か、下端からの距離か、baseline かを特定
2. PyMuPDF（fitz）の `insert_text()` 座標系を調査する
   - 公式ドキュメントから `point` パラメータが文字のどの部分を基準にするかを確認
   - `fontsize` と `point` の関係を確認
3. 実験的に検証する
   - 同一の XML と元画像を使い、Y座標変換パターンを複数用意して PDF を生成
   - 各 PDF からテキスト bbox を抽出し、元画像の文字位置と比較
   - 目視確認用 PNG を生成
4. 正しい変換式を導出し、`backend/app/services/pdf_generator.py` に反映
5. 調査結果を `backend/docs/work_log.md` に追記
6. backend のローカルテストを実行
7. Docker で結合テストし、修正後の PDF を目視確認

### 実施コマンド

```bash
# 1. ndlocr_cli リポジトリの README・ソースを確認
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/README.md | head -200
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/main.py | grep -n -A5 -B5 "LINE\|PAGE\|X=\|Y="

# 2. PyMuPDF ドキュメントを確認
python3 - <<'PY'
import fitz
help(fitz.Page.insert_text)
PY

# 3. 実験用スクリプトで複数パターンの PDF を生成（予定）
# 4. テスト実行
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend
source .venv/bin/activate
python -m pytest tests/ -q
```

### 結果

1. **XML 座標系の調査結果**
   - ndlocr_cli の出力 XML（`.sorted.xml`）では、`<PAGE WIDTH="..." HEIGHT="...">` の HEIGHT はページ全体の高さを表す
   - `<LINE X="..." Y="..." WIDTH="..." HEIGHT="...">` の `X`, `Y` は、**ページ左上を原点 (0,0)** とする座標系で、文字領域の左上隅を表す
   - これは一般的な画像座標系と同じであり、XML の `Y` 値が大きいほどページの下側に位置する

2. **PyMuPDF `insert_text()` の座標系の調査結果**
   - PyMuPDF の PDF 座標系は**左下を原点 (0,0)** とし、`y` 値が大きいほどページの上側に位置する
   - `Page.insert_text(point=(x, y), ...)` の `point` は、**テキストの baseline（文字の下端）** を指定する
   - したがって、XML の `Y`（文字上端）を PDF の `y` に変換する際は、下方向に `font_size` ほど補正する必要がある

3. **正しい Y 座標変換式の導出**
   - 縮尺変換: `scale_y = pdf_height / xml_height`
   - XML 上端 `xml_y` を PDF 座標系に変換: `pdf_y_top = pdf_height - (xml_y * scale_y)`
   - baseline 補正: `pdf_y = pdf_y_top - font_size`
   - 既存の `_xml_to_pdf_y()` はこの変換を実装しており、数式的には正しい
   - `pdf_generator.py` の `_xml_to_pdf_y()` にコメントを追加し、座標系と baseline 補正の意図を明記した

4. **テスト追加**
   - `backend/tests/test_pdf.py` に `_xml_to_pdf_y()` の単体テストを 3 件追加した
     - `test_xml_to_pdf_y_top_position`: XML Y=0 が PDF ページ上端（font_size 分下げた位置）になることを確認
     - `test_xml_to_pdf_y_bottom_position`: XML Y=xml_height が PDF ページ下端（-font_size 付近）になることを確認
     - `test_xml_to_pdf_y_with_scaling`: XML と PDF の高さが異なる場合のスケーリングを確認

5. **ローカルテスト結果**
   - `backend/tests/test_pdf.py` の 10 件すべて pass
   - `backend/` 全体の pytest で 26 件すべて pass

6. **Docker 結合テスト結果**
   - `docker compose up -d --build backend` を実行したところ、`python:3.12-slim` のメタデータ取得で `DeadlineExceeded` エラーが発生し、Docker Hub 経由の再ビルドができなかった
   - 回避策として、`backend/Dockerfile.local` を作成し、既存の `book2pdf-backend:latest` イメージをベースにソースコードのみをコピーする形でビルドした
     ```bash
     cd /Users/hisao/Documents/work4/sakura/book2pdf
     docker build --platform linux/amd64 -f backend/Dockerfile.local -t book2pdf-backend:latest backend/
     docker compose up -d backend
     ```
   - backend（:8000/health）と ocr-worker（:8001/health）が正常に起動することを確認
   - 3 ページ画像（1384×1963 px）で ZIP アップロード → OCR → PDF ダウンロードまでの結合テストを実施
     - ジョブ ID: `7a837165-8e0c-44c6-bd29-30abb101bfea`
     - PDF サイズ: 39 MB（3 ページ）
     - PDF ページサイズ: 1384×1963 pt（元画像サイズと一致）
   - OCR 結果 XML と PDF 内のテキスト bbox を比較した結果、Y 座標の変換は正しく機能していることを確認
     - XML Page 1「咸毅成[著]」Y=1712（XML では下端付近）→ PDF y=156（ページ上端付近）に配置（縦書き表紙のレイアウトと一致）
     - XML Page 3「はじめに」Y=310（XML では上端付近）→ PDF y=1555（ページ下部）に配置（通常ページのレイアウトと一致）
   - 目視確認用に PDF ページにテキスト bbox を赤枠で描画した画像を生成し、Preview で開いて目視確認できる状態にした
     - `/tmp/pdf_page1_bbox_overlay.png`
     - `/tmp/pdf_page2_bbox_overlay.png`
     - `/tmp/pdf_page3_bbox_overlay.png`

7. **y 軸問題に関する結論**
   - ソースコードの座標変換式自体に誤りはなかった
   - 問題は主に、XML 座標系（左上原点）と PDF 座標系（左下原点）の関係、および PyMuPDF の baseline 配置の理解が不十分だったことに起因
   - コメントを整理し、単体テストを追加することで、将来の誤解を防ぐ体制を整えた

### 注意事項

- XML 側の座標系が期待と異なる場合、OCR エンジン側の修正も検討する必要がある
- PyMuPDF の `insert_text()` は baseline 配置と仮定しているが、バージョンによって挙動が異なる可能性があるため、実験で確認する
- 目視確認だけでなく、数値的な bbox 比較も行う
- Docker Hub への接続が不安定な場合、`docker compose up -d --build backend` が `DeadlineExceeded` で失敗する
  - この場合、既存の `book2pdf-backend:latest` イメージをベースにした一時的な `Dockerfile.local` を使ってビルドできる
  - ただし、platform は `linux/amd64` を明示的に指定する必要がある
  - 本番運用時は Docker Hub 接続問題の解決を推奨する
- 今回作成した `backend/Dockerfile.local` は一時的なファイルであり、作業完了後に削除することを推奨する
- 作業完了後、`backend/Dockerfile.local` を削除した

---

## 2026-08-13 タスク004003（一部）：OCR 処理性能計測の事前準備

### 目的

backend 004003「OCR 処理性能計測の実施」のうち、ユーザー指示により以下の 2 項目を実施する。

1. `ocr-worker/ndlocr_cli_patches/inference.py` に 1 ページごとの OCR 処理時間 DEBUG ログを追加する
2. `scripts/benchmark_ocr.sh` を ZIP 内の画像ファイル数に依存した汎用ページ数対応に改修する

### 前提

- `ocr-worker/ndlocr_cli_patches/inference.py` に既にページ処理完了の DEBUG ログが存在すること
- `scripts/benchmark_ocr.sh` は 92 ページ固定仕様であること
- ユーザーから「性能計測の実行と結果のドキュメント記録は今回は実施しない」と明確に指示を受けていること

### 実施コマンド

```bash
# 1. ocr-worker パッチファイルのシンタックスチェック
cd /Users/hisao/Documents/work4/sakura/book2pdf
python3 -m py_compile ocr-worker/ndlocr_cli_patches/inference.py

# 2. benchmark スクリプトのシンタックスチェック
bash -n scripts/benchmark_ocr.sh
```

### 結果

- `ocr-worker/ndlocr_cli_patches/inference.py` を修正した
  - `_infer()`（通常 OCR モード）でページ処理開始時と完了時に `page=N` を含む DEBUG ログを出力するようにした
  - `_infer_ruby_only()`（ルビ推定モード）でページ処理開始時と完了時に `page=N` を含む DEBUG ログを出力するようにした
  - 既存の `page_idx` ではなく 1 始まりの `page=N` で統一し、ベンチマークスクリプトでの「ページ N」表示に対応
- `scripts/benchmark_ocr.sh` を修正した
  - 入力 ZIP ファイル名を `benchmark-input.zip` に変更
  - `seq 1 92` のハードコードを廃止し、サンプル画像ディレクトリ内の画像ファイルを `find` で自動収集
  - ZIP 内の画像ファイル数を `unzip -Z1 | wc -l` で自動検出し、0 ページの場合はエラー終了
  - ocr-worker ログ抽出の正規表現を `page=N` 付きの新しい DEBUG ログ形式に合わせて更新
- `backend/docs/tasks.md` の 004003 タスク詳細に実施結果を追記した
- `backend/docs/work_log.md` に本エントリを追記した

### 注意事項

- 今回の変更を反映するには `ocr-worker` イメージを再ビルドする必要がある
  - `docker compose up -d --build ocr-worker`
- 性能計測の実行と結果のドキュメント記録は、ユーザー指示により今回は実施しない
- 実際の性能計測時は、サンプル画像ディレクトリに含まれる画像ファイル数に応じて自動的にページ数が決定される

---

## 2026-09-01 タスク004003：OCR 処理性能計測の実施

### 【実施予定】

- 日時: 2026-09-01
- 目的: 最新コードベース（005001 メモリ最適化パッチ適用後）での OCR 処理性能を計測する
- 前提条件:
  - `test_cases/AI ・LLMの実務でつかえるRAG精度改善/AI ・LLMの実務でつかえるRAG精度改善_trimmed/002.png` 〜 `004.png` が存在すること
  - `docker-compose.yml` の `LOG_LEVEL=DEBUG` が設定されていること
  - `scripts/benchmark_ocr.sh` が汎用ページ数対応になっていること
- 実施予定のコマンド:
  - `docker compose up -d --build`
  - `scripts/benchmark_ocr.sh`
- 想定される結果や注意点:
  - 3 ページ OCR には数分〜十数分かかる可能性がある
  - 初回実行時は ndlocr_cli のモデル初期化に時間がかかる
  - メモリ最適化パッチ（005001）適用後の 1 ページあたり処理時間を確認する

### 【実施実績】

- 2026-09-01: `feature/005002-pdf-e2e-test` ブランチの未コミット変更を `git stash` で一時退避
- 2026-09-01: `main` ブランチを最新化し、`feature/004003-ocr-performance-test` ブランチを作成
- 2026-09-01: `docker compose up -d --build backend ocr-worker` を実行（ビルド約 58 秒）
- 2026-09-01: backend（`http://localhost:8000/health`）および ocr-worker（`http://localhost:8001/health`）が正常応答することを確認
- 2026-09-01: `scripts/benchmark_ocr.sh` を改修し、`BENCHMARK_SAMPLE_DIR` 環境変数でサンプルディレクトリを指定可能にした
- 2026-09-01: テスト用 3 ページ画像を `sample-png/benchmark-004003/` にコピー
- 2026-09-01: `BENCHMARK_SAMPLE_DIR=sample-png/benchmark-004003 ./scripts/benchmark_ocr.sh` を実行
- 2026-09-01: OCR 全体時間 396.407 秒、1 ページあたり平均 OCR 処理時間 125.629 秒、合計処理時間 396.914 秒を計測
- 2026-09-01: 検証結果レポート `test_cases/ocr-results-004003/performance-test-report-004003.md` を作成
- 2026-09-01: `backend/docs/tasks.md` に実施結果とレポートリンクを追記

---

## 2026-09-03 タスク003012：`/ocr` エンドポイントの非同期化

### 目的

`POST /api/jobs/{job_id}/ocr` が ocr-worker への同期 HTTP 呼び出しで 1 時間のタイムアウトまでブロックしていた問題を解消し、リクエスト受付後即座に processing を返すようにする。

### 前提

- backend コンテナが `docker compose` で起動していること
- ocr-worker コンテナが同じネットワークで起動していること
- `localapp/src-tauri/src/commands/backend_api.rs` が `processing` 状態をポーリングして完了を待つ実装であること

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# backend コンテナ再起動
docker compose restart backend

# /ocr の即座返答確認
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/jobs/)
JOB_ID=$(echo "$JOB_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
curl -s -X POST "http://localhost:8000/api/jobs/$JOB_ID/upload" \
  -F "file=@/tmp/003006-backend-ocr-test.zip;type=application/zip"
curl -s -X POST "http://localhost:8000/api/jobs/$JOB_ID/ocr" | python3 -m json.tool

# processing 状態の維持確認（3 分間ポーリング）
for i in 1 2 3 4 5 6; do
  curl -s "http://localhost:8000/api/jobs/$JOB_ID" | python3 -m json.tool
  sleep 30
done
```

### 結果

- `backend/app/routers/jobs.py` の `run_ocr()` を修正
  - ジョブ状態を `PROCESSING` に更新後、`asyncio.create_task(_run_ocr_and_generate_pdf(...))` でバックグラウンドタスクを起動
  - `_run_ocr_and_generate_pdf` 内で `ocr_engine.run()` と `generate_searchable_pdf()` を `asyncio.to_thread` で別スレッド化
  - 処理成功時は `COMPLETED`、例外発生時は `FAILED` に状態更新
- backend コンテナを再起動後、`/ocr` が即座に HTTP 200 で `{"status":"processing"}` を返すことを curl で確認
- `GET /api/jobs/{job_id}` で 3 分間ポーリングし、`processing` 状態が維持されることを確認
- `backend/docs/tasks.md` にタスク003012を追加し、`backend/docs/work_log.md` に本エントリを追記

### 注意事項

- エンドポイントの即座返答を確認したが、OCR 完了までには数十分かかるため、completed になるまでのフルフロー確認は別途実施する
- クライアント側は `processing` 状態を継続ポーリングし、`completed`/`failed` で完了判定する必要がある
- バックグラウンドタスク実行中に backend コンテナが再起動するとジョブ状態は失われる（005001 SQLite 永続化完了後に解消予定）

