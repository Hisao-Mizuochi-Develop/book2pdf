# backend 単体テストガイド

> 最終更新: 2026/09/18

---

## 概要

本文書は、`backend` モジュールの単体テストをローカル環境で実行する手順と、テストに関する注意事項をまとめたものです。

本プロジェクトの backend は **FastAPI** で実装されており、テストフレームワークとして **pytest** を使用しています。

---

## 前提条件

| 項目 | 推奨バージョン | 備考 |
|---|---|---|
| Python | **3.12.x** | backend の Dockerfile は `python:3.12-slim` ベース |
| pip | 26.x 以降 | 仮想環境内で使用 |
| 仮想環境 | venv | システム Python への直接インストールは推奨しない |

本番の Docker コンテナは Python 3.12 で動作するため、ローカルでのテストも **Python 3.12** を使用することが原則です。

---

## 仮想環境のセットアップ

Homebrew などでインストールした Python 3.12 は、PEP 668 によりシステム全体への直接パッケージインストールがブロックされています。そのため、必ず仮想環境を作成してください。

### 1. 作業ディレクトリへ移動

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/backend
```

### 2. Python 3.12 の仮想環境を作成

```bash
python3.12 -m venv .venv312
```

作成後、`backend/.venv312/` ディレクトリが生成されます。

### 3. 仮想環境を有効化

```bash
source .venv312/bin/activate
```

有効化後、`python --version` で 3.12.x であることを確認します。

```bash
python --version
# Python 3.12.13
```

---

## 依存関係のインストール

仮想環境を有効化した状態で、`requirements.txt` をインストールします。

```bash
pip install -r requirements.txt
```

主な依存関係は以下の通りです。

| パッケージ | 用途 |
|---|---|
| `fastapi` | Web フレームワーク |
| `uvicorn[standard]` | ASGI サーバー |
| `pydantic` / `pydantic-settings` | データバリデーション・設定管理 |
| `python-multipart` | マルチパートフォームデータのパース |
| `pymupdf` | PDF 生成 |
| `pytest` | テストフレームワーク |
| `pytest-anyio` | 非同期テスト用プラグイン |
| `pytest-timeout` | テストタイムアウト制御 |
| `httpx` | TestClient で使用される HTTP クライアント |

---

## テストの実行

### 全テストを実行

```bash
python -m pytest
```

または短縮出力で実行する場合：

```bash
python -m pytest -q
```

### 特定のテストファイルのみ実行

```bash
python -m pytest tests/test_jobs.py
```

### 特定のテスト関数のみ実行

```bash
python -m pytest tests/test_jobs.py::test_create_job
```

---

## テストファイルの構成

`backend/tests/` 配下に以下のテストファイルが配置されています。

| ファイル | 対象 |
|---|---|
| `test_main.py` | アプリケーション全体のルートエンドポイント |
| `test_jobs.py` | ジョブ管理 API（`/jobs`） |
| `test_ocr.py` | OCR 処理 API（`/ocr`） |
| `test_pdf.py` | PDF 生成 API（`/pdf`） |
| `test_progress.py` | 進捗通知 API（`/progress`） |
| `test_cors.py` | CORS 設定 |
| `conftest.py` | テスト全体の共通設定 |

---

## テスト設定（conftest.py）

`tests/conftest.py` では、以下の共通設定を行っています。

- テスト用の一時ディレクトリを作成し、`EXTRACT_BASE_DIR` および `PDF_OUTPUT_DIR` 環境変数に設定
- テスト終了時に一時ディレクトリを削除
- `ocr-worker` モジュールへのパスを追加し、ndlocr_cli 関連のパッチを利用可能にする

この設定により、ローカル環境に `/data/extracted` や `/data/output` などの本番用ディレクトリがなくてもテストが実行できます。

---

## トラブルシューティング

### `No module named 'pydantic_settings'`

**原因**: 仮想環境に `pydantic-settings` がインストールされていない、または誤った Python バージョンで実行している。

**対処**:

```bash
source .venv312/bin/activate
pip install -r requirements.txt
```

### `pip install` が失敗する（PEP 668）

**原因**: システム Python に直接インストールしようとしている。

**対処**: 必ず仮想環境を作成してからインストールしてください。

### `python3` が Python 3.14 を指している

**原因**: macOS の `python3` が Python 3.14 にリンクされている。

**対処**: `python3.12` コマンドを使用するか、仮想環境を `python3.12 -m venv` で作成してください。

---

## Docker 環境でのテスト実行

ローカル環境ではなく、本番に近い Docker 環境でテストを実行することも可能です。

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

docker compose run --rm backend python -m pytest
```

Docker 環境では `python:3.12-slim` ベースのイメージが使用されるため、ローカル環境との Python バージョン差異を気にする必要がありません。

---

## 注意事項

- **Python 3.14 は使用しない**: 本番環境と異なるバージョンであり、ライブラリ互換性のリスクがあります。必ず Python 3.12 を使用してください。
- **仮想環境は git 管理外**: `.venv312/` は `.gitignore` に登録されており、リポジトリには含めません。必要に応じて再作成してください。
- **テスト用ディレクトリの自動削除**: `conftest.py` はテスト終了時に一時ディレクトリを削除します。テスト失敗時に中身を確認したい場合は、一時ディレクトリのパスをログなどで確認してください。

---

## 関連ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`BE-BACKEND-SYSTEM-SPEC.md`](BE-BACKEND-SYSTEM-SPEC.md) | バックエンド全体仕様 |
| [`BE-TASKS.md`](BE-TASKS.md) | backend タスク管理表 |
| [`BE-WORK-LOG.md`](BE-WORK-LOG.md) | backend 作業ログ |
| [`BE-CAVEATS.md`](BE-CAVEATS.md) | backend 固有の注意事項 |
| [`SY-INTEGRATION-TEST-GUIDE.md`](../../docs/SY-INTEGRATION-TEST-GUIDE.md) | Docker Compose 上での結合テスト手順 |
