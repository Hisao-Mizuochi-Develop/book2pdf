# 注意事項・留意点

本ドキュメントは、book2pdf プロジェクトのバックエンド（Web OCR/PDF システム）に関するタスク実施中に発生した注意すべき事象を記録したものです。

環境差異、トラブルシューティング、回避策などを時系列で追記していきます。

---

## 2026-08-11 Python 3.9.6 での型注釈記法の互換性

### 事象

ローカル開発環境の Python 3.9.6 で `pytest` を実行したところ、以下のエラーが発生した。

```
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

### 原因

Python 3.10 で導入された新しい型注釈記法（例：`dict | None`、`list[str]`）が、Python 3.9.6 ではそのままでは使用できない。

### 対応

各 Python ファイルの先頭に以下の import を追加した。

```python
from __future__ import annotations
```

これにより、型注釈を文字列として遅延評価できるようになり、Python 3.9.6 でも新しい記法が使用可能になった。

### 備考

- Docker コンテナ内では `python:3.11-slim` を使用するため、本番環境ではこの問題は発生しない
- ただし、ローカル開発環境と Docker 環境で Python バージョンが異なるため、型注釈の互換性には引き続き注意が必要

---

## 2026-08-11 Python 3.12 へのバージョンアップと関連する警告

### 事象

`backend/.venv` と `backend/Dockerfile` を Python 3.12 にバージョンアップした後、`pytest` を実行すると以下の警告が出力された。

```
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

### 原因

`fastapi.testclient` / `starlette.testclient` の組み合わせにおいて、現在の `httpx` バージョンが非推奨とされたため。これはライブラリ間の互換性に関する警告であり、テスト自体は pass する。

### 対応

現時点ではテストが pass するため、対応は保留としている。必要に応じて以下のいずれかを検討する。

- `httpx2` への移行
- テストクライアントの実装見直し

### 備考

- Python 3.12 に移行したことで、`from __future__ import annotations` がなくても `dict | None` などの新しい型注釈が使えるようになった
- 既存コードの `from __future__ import annotations` は互換性を保つため、そのまま残しても問題ない
- ローカル開発環境と Docker 環境の Python バージョンは、3.12 で統一された

---

## 2026-08-11 ZIP 展開後の一時ディレクトリの寿命管理

### 事象

タスク001002 で ZIP ファイルを一時ディレクトリに展開し、OCR 処理完了まで画像ファイルを保持する必要が生じた。

### 原因

メモリ内ジョブ管理を採用しているため、展開後のファイルもプロセス内で保持する必要がある。`tempfile.TemporaryDirectory` は参照がなくなると自動削除されるため、ジョブ情報と紐づけて保持する必要がある。

### 対応

`app/services/job_manager.py` のジョブ情報に `temp_dir` フィールドを追加し、`tempfile.TemporaryDirectory` オブジェクトを保持するようにした。ジョブが `COMPLETED` または `FAILED` に遷移する際に明示的にクリーンアップする設計を今後検討する。

### 備考

- 現時点ではプロセス再起動で一時ディレクトリとジョブ状態が失われる
- ジョブ状態の SQLite 永続化（004001）に合わせて、ファイルパスの永続化や共有ストレージの検討が必要

---

## 2026-08-11 ndlocr_cli のローカル未インストールとモック実行

### 事象

タスク001003 で ndlocr_cli を Python パッケージとして import しようとしたところ、ローカル開発環境ではインストールされていないため import エラーが発生する。

### 原因

`backend/requirements.txt` では `ndlocr_cli` がコメントアウトされており、仮想環境にはインストールされていない。さらに ndlocr_cli は pip パッケージとして公開されておらず、GitHub リポジトリのクローンと submodule 取得が必要なため、単純な `pip install` では完結しない。

### 対応

`app/services/ocr_engine.py` にて、以下の設計とした。

- `BaseOcrEngine` という抽象クラスを定義し、OCR エンジンの実装を差し替え可能にする
- `NdloCrOcrEngine` を実装し、ndlocr_cli の `OcrInferrer` を呼び出す
- `MockOcrEngine` を実装し、ndlocr_cli が利用できない環境でも動作確認できるようにする
- `create_ocr_engine()` は、`ndlocr_cli` の import 成功状況または `use_mock` 引数に応じて適切なエンジンを返す

### 備考

- 本番環境や `ocr-worker` コンテナでは、ndlocr_cli とその submodule が正しく構築された状態で `NdloCrOcrEngine` が選択される想定
- `NdloCrOcrEngine` は ndlocr_cli の single 形式入力（`input_root/img/`）を作成し、`OcrInferrer(cfg).run()` を実行する
- OCR 結果のテキストは、出力ディレクトリ以下の `txt` ディレクトリから `.txt` ファイルを収集して連結している
- 実際の ndlocr_cli 動作確認は、`ocr-worker` コンテナ構築後に実施する

---

## 2026-08-11 backend と ocr-worker の連携に関する注意点

### 事象 1：ローカル pytest で共有ボリューム `/data/extracted` が存在しない

`backend/tests/conftest.py` を作成する前は、テスト実行時に `EXTRACT_BASE_DIR` が `/data/extracted` のままとなり、
ローカル環境に該当ディレクトリがないために ZIP 展開テストが失敗していた。

### 原因 1

`backend/app/core/config.py` の `Settings` クラスが `EXTRACT_BASE_DIR` 環境変数から
共有ボリュームのパスを読み込んでおり、テスト環境では未設定のためデフォルト値 `/data/extracted` が使われていた。

### 対応 1

`backend/tests/conftest.py` を作成し、`pytest_configure` フックで一時ディレクトリを
`EXTRACT_BASE_DIR` 環境変数に設定するようにした。
これにより、テストモジュールの import より前に環境変数が上書きされる。

```python
@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    tmp_dir = tempfile.mkdtemp(prefix="book2pdf-test-")
    os.environ["EXTRACT_BASE_DIR"] = tmp_dir
```

### 事象 2：curl で ZIP アップロード時に「ZIP ファイルをアップロードしてください」と返される

### 原因 2

curl の `-F` オプションでファイルを指定しても、ファイル名や Content-Type が正しく渡らない場合、
FastAPI の `content_type` チェックで `application/zip` と判定されないことがある。

### 対応 2

curl ではファイル名と Content-Type を明示的に指定する。

```bash
curl -s -X POST \
  -F "file=@sample.zip;type=application/zip" \
  http://localhost:8000/api/jobs/{job_id}/upload
```

### 事象 3：OCR 実行でタイムアウトが発生する

### 原因 3

ndlocr_cli の初回推論時はモデルの初期化などに時間がかかり、デフォルトの短いタイムアウトでは
処理が完了する前に通信が切れてしまう。

### 対応 3

curl では `--max-time 600` など、長めのタイムアウトを設定する。
backend 側の `OCR_WORKER_REQUEST_TIMEOUT` も必要に応じて調整する。

### 備考

- backend コンテナから ocr-worker コンテナへは、Docker Compose のサービス名を使って
  `http://ocr-worker:8000` でアクセスする
- ocr-worker 内の Uvicorn はポート 8000 でリッスンしており、ホスト側には 8001 番で公開されている
  - backend からは 8000 番、ホストブラウザ・curl からは 8001 番を使用する
- ZIP 展開後の一時ディレクトリは `job_manager` の `temp_dir` に保持され、
  OCR 処理完了まで削除されない
  - ただし backend プロセス再起動時に失われるため、将来の永続化対応時に設計を見直す

