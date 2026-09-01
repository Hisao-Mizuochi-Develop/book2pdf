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

---

## 2026-08-11 SSE 進捗通知の実装と検証

### 事象 1：ocr-worker から backend へ進捗を伝える方法

backend と ocr-worker が別コンテナのため、OCR 処理中の進捗を backend に伝える仕組みが必要だった。

### 原因 1

ocr-worker は HTTP リクエストに対して同期的に OCR 処理を返すだけで、
処理中の細かい進捗を backend に通知する手段がなかった。

### 対応 1

`docker-compose.yml` に `/data/progress` 共有ボリュームを追加し、
ocr-worker が `/data/progress/{job_id}.json` に進捗を書き出す方式とした。
backend は同じファイルをポーリングし、`GET /api/jobs/{job_id}/events` で SSE 形式に変換して配信する。

現状の実装では、OCR 処理の開始時・完了時・失敗時に進捗ファイルを更新する。
ndlocr_cli の内部処理段階に合わせた細かい進捗取得は、今後の改善課題として残している。

### 事象 2：テスト時に `/data/progress` ディレクトリが書き込みできない

### 原因 2

`app/routers/jobs.py` の `_PROGRESS_DIR` が `/data/progress` に固定されており、
ローカルの pytest 環境では該当ディレクトリが存在しないか書き込み権限がない。

### 対応 2

`_PROGRESS_DIR` を `PROGRESS_DIR` 環境変数で上書きできるようにした。
テストでは `monkeypatch` を使って一時ディレクトリに差し替える。

```python
_PROGRESS_DIR = Path(os.environ.get("PROGRESS_DIR", "/data/progress"))
```

また、進捗ファイルのポーリング間隔 `_POLL_INTERVAL` も `PROGRESS_POLL_INTERVAL` 環境変数で調整できるようにし、
`backend/tests/conftest.py` で 0.05 秒に短縮してテストを高速化している。

### 備考

- SSE は `fastapi.responses.StreamingResponse`（`media_type="text/event-stream"`）を使用して実装した
- プロキシ環境やタイムアウト設定によって SSE が不安定になる場合は、
  別途ポーリング方式（005001）への切り替えを検討する
- フロントエンドでの進捗バー表示は、タスク002002 として別途対応する

---

## 2026-08-11 `fastapi.testclient.TestClient` 経由の SSE テストの不安定性

### 事象

`tests/test_progress.py` において、`TestClient` + `StreamingResponse` を使った
HTTP ストリーム経由の SSE テストを実装したところ、テストが停止したり
最初の進捗イベントがクライアント側に届かず失敗したりする現象が発生した。

### 原因

`TestClient`（`starlette.testclient.TestClient`）は内部的に同期的な `httpx` ストリームを使用するが、
これが非同期 generator から yield された chunk を確実に消費・受信できない場合がある。
特に `iter_text()` を開始する前に generator が yield してしまうと、
イベントが欠落し、テストがタイムアウトまたは失敗する。

`httpx.AsyncClient` + `ASGITransport` による非同期 HTTP ストリームでも、
chunk の受信タイミングが不定となり安定したテストが書けないことも確認した。

### 対応

SSE イベントを生成する async generator 関数 `_progress_event_generator` を
`app/routers/jobs.py` から直接 import し、`async for` でイテレーションする形に
テストを変更した。これにより HTTP レイヤー（`StreamingResponse` / `TestClient`）を
介さずに、SSE 配信の核心部分（進捗ファイルポーリングとイベント yield ロジック）を
安定して検証できるようになった。

HTTP エンドポイント `GET /api/jobs/{job_id}/events` 自体の動作確認は、
存在しないジョブに対する 404 応答テスト（`test_stream_job_events_not_found`）でカバーしている。

### 備考

- `_progress_event_generator` のみを直接テストしても、`StreamingResponse` による
  HTTP 配信部分は未カバーとなる。ただし FastAPI / Starlette の標準機能を使用しており、
  フレームワーク側の挙動を信頼するのが現実的である
- 本番環境での SSE 配信動作は、Docker コンテナ起動後に実際のブラウザや curl で確認する
- `test_progress.py` 内に「なぜ HTTP ストリームを経由しないか」を説明するコメントを残している

---

## 2026-08-11 backend コンテナのソース変更反映には再ビルドが必要

### 事象

タスク003001の結合テストで、`GET /api/jobs/{job_id}/pdf` エンドポイントが 404 エラー（`{"detail":"Not Found"}`）を返した。
また、`http://localhost:8000/openapi.json` のエンドポイント一覧にも `/api/jobs/{job_id}/pdf` が含まれていなかった。

### 原因

ホスト側の `backend/app/routers/jobs.py` には `download_pdf` 関数が実装されていたが、
実行中の backend コンテナイメージにはその変更が反映されていなかった。
Docker イメージは `docker compose up` 時点のソースで固定されており、
その後のホスト側ソース変更は自動的には反映されない。

### 対応

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
docker compose up -d --build backend
```

`--build` を指定して backend イメージを再ビルドし、コンテナを再起動したところ、
新しいエンドポイントが反映され、PDF ダウンロードが正常に動作した。

### 備考

- `docker compose restart backend` ではソース変更は反映されない
- コード変更後は `--build` を使うか、イメージを削除してから再作成する必要がある
  - `docker compose rm -f backend && docker compose up -d --build backend`
- backend のジョブ状態は現在メモリ内で管理されているため、再起動後は過去のジョブにアクセスできなくなる
  - 永続化は別タスク（004001）で対応予定

---

## 2026-08-11 frontend から backend API を呼び出す際の CORS 設定

### 事象

frontend（`http://localhost:3000`）から backend（`http://localhost:8000`）の API を呼び出す際、
ブラウザの同一オリジンポリシーによりリクエストがブロックされる可能性がある。

### 原因

開発環境では frontend と backend が別々のオリジン（ポート 3000 と 8000）で動作しているため、
ブラウザは Cross-Origin Resource Sharing（CORS）のプリフライトリクエストを送信する。
backend で CORS 許可設定が行われていない場合、`fetch` が失敗する。

### 対応

現状の結合テストでは API 自体の動作を cURL とブラウザ直接アクセスで確認しているが、
frontend からの実際の API 呼び出しを安定させるため、backend に `CORSMiddleware` を追加することを推奨する。

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

本番環境では `allow_origins` を適切なドメインに制限すること。

### 備考

- 同一オリジン配置（リバースプロキシ等）を採用する場合は CORS 設定が不要になる
- Next.js の API Route 経由で backend を呼び出す方式も検討できる

---

## 2026-08-12 PDF 白紙問題：OCR 結果 XML の画像名と元画像が一致しない

### 事象

3 ページ画像（002.png, 003.png, 004.png）で OCR/PDF 生成を実行したところ、生成された PDF が白紙（背景画像なし、テキストのみの極小 PDF）になった。

### 原因

ndlocr_cli の OCR 結果 XML（`.sorted.xml`）の `image_name` 属性が `002_L.jpg` のようになっており、元画像ファイル名（`002.png`）と以下の点で一致しなかった。

- `_L` / `_R` というサフィックスが付いている
- 拡張子が `.jpg` になっている（元画像は `.png`）

`backend/app/services/pdf_generator.py` の `_find_image_path()` は完全一致を要求していたため、該当する元画像が見つからず、背景画像なしで PDF が生成されていた。

### 対応

`backend/app/services/pdf_generator.py` の `_find_image_path()` を修正し、画像名から `_L` / `_R` サフィックスを除去した上で、拡張子を無視して stem（ファイル名本体）一致で元画像を探すようにした。

```python
# 例: "002_L.jpg" → "002" とし、extract_dir 内の "002.png" を発見する
```

修正後、backend イメージを `docker compose up -d --build backend` で再ビルド・再起動し、3 ページとも背景画像が配置されたことを確認した。

### 備考

- 背景画像が配置されない場合、PDF サイズは 1,445 バイト程度しかない（テキストのみの極小 PDF）
- 正常に背景画像が配置されると、3 ページで約 5.6 MB 程度の PDF になる
- ndlocr_cli の XML 出力は、入力画像のファイル名と拡張子を変更した形で `image_name` を出力する場合があるため、今後も stem 一致方式を維持する
- backend コードを変更した後は必ず `--build` オプションを付けてイメージを再ビルドすること
  - `docker compose restart backend` ではホスト側のソース変更が反映されない

---

## 2026-08-12 PDF 透明テキストレイヤーの配置・文字化け問題

### 事象

PDF 白紙問題を修正した後、3 ページのうち Page 2, 3 の透明テキストがページ左上に偏り、かつ文字列が「・」の繰り返しで表示される問題が発生した。

### 確認したこと

- 元画像サイズは 664×942 ピクセル、PDF ページサイズは 664×942 pt で一致
- PDF 内テキスト抽出（PyMuPDF `get_text('dict')`）の結果
  - Page 2: `························` bbox=(108.0, 86.4, 248.1, 115.3)
  - Page 3: `······························!` bbox=(97.0, 73.8, 234.9, 95.8)
- Page 1 は PyMuPDF では検出できなかったが、PDF ビューアでは視覚的にレイアウト通りに配置されていた

### 原因（仮説）

- OCR 結果 XML の LINE 座標（X, Y, WIDTH, HEIGHT）と PDF 座標系の変換に問題がある可能性がある
- 縦書きテキストや句読点が「・」として認識・描画されている可能性がある
- 埋め込みフォントの関係で、認識文字列が「・」にフォールバックされている可能性がある
- 文字の bbox 高さ（28.9 pt, 22 pt）が XML の LINE HEIGHT（11〜12）より大きいため、フォントサイズ計算ロジックにも見直しが必要

### 対応（未実施）

以下のタスクとして切り出し、別途調査・修正を実施予定。

- 003004: PDF 透明テキスト配置ズレの調査
- 003005: OCR 結果 XML の可視化検証
- 003006: 縦書き・特殊文字の PDF 描画対応

### 備考

- 透明テキストは PDF ビューアでは選択可能だが、PyMuPDF のテキスト抽出では検出できない場合がある
- 1 ページ目が正常に見える場合でも、テキスト抽出で確認できるわけではないため、目視確認と機械的な抽出結果を併用して評価する

---

## 2026-08-12 PDF 透明テキストの配置ズレと OCR 認識精度に関する調査結果

### 事象

PDF 白紙問題とフォント fallback 問題を修正した後、以下の問題が残っていた。

1. 透明テキストの位置が元画像の文字位置と大きくずれている
2. PDF ページ画像の文言と透明テキストの内容が一致しない（例：`RAG` → `RAC`、`Improving` → `mproving`）

### 原因

#### 配置ズレ

- OCR 結果 XML のページサイズと PDF ページサイズ（元画像サイズ）が異なる
  - XML ページサイズ：Page 1: 698×965、Page 2: 686×958、Page 3: 666×943
  - PDF ページサイズ（元画像サイズ）：664×942
- 現在の `pdf_generator.py` は XML 座標を PDF 座標にそのまま使っており、スケール変換が未実装
- これにより、座標値が 3〜5% ずつずれ、テキスト位置が元画像の文字位置と一致しなくなっている

#### 内容の差異

- PDF 透明テキストの内容は OCR 結果 XML の `STRING` 属性と完全に一致
- つまり、PDF 生成処理（xml_parser.py → pdf_generator.py）はテキスト内容を正しく受け渡している
- PDF ページ画像の文言との差異は、OCR エンジン（ndlocr_cli）の認識ミスに起因
  - 具体例：
    - `RAG` → `RAC`
    - `Improving` → `mproving`（先頭 I の欠落）
    - `GPT-4` → `〓PT-4`
    - `LLM` → `〓lm`
    - `前処理` → `K前処理`（チェックマークの誤認識）
    - `年` / `理` / `利` などが異体字（年 / 理 / 利）に変換されている

### 対応

- 配置ズレについてはタスク 003007 で XML → PDF の座標スケーリングを実装する
- OCR 認識精度については、ndlocr_cli 側のモデル・前処理・推論パラメータを調査し、別途改善策を検討する

### 備考

- XML → PDF のスケール変換式
  - `scale_x = pdf_width / xml_width`
  - `scale_y = pdf_height / xml_height`
  - `pdf_x = xml_x * scale_x`
  - `pdf_y = pdf_height - (xml_y + xml_height) * scale_y`
- 異体字変換（年→年 など）は、Unicode 正規化（NFKC など）で是正できる可能性がある
  - ただし、OCR エンジンが元の字形を誤認識している場合（G→C、I→空白 など）は正規化では解消できない
- OCR 認識精度の改善は、ndlocr_cli の学習済みモデルの特性に依存するため、前処理（画像解像度向上・二値化・ノイズ除去）や推論パラメータ調整から検討する

---

## 2026-08-12 003007 XML → PDF 座標スケーリング実装後の確認と留意点

### 事象

タスク 003007 で `xml_parser.py` / `pdf_generator.py` に座標スケーリングを実装した後、以下を確認した。

1. PDF ページサイズは元画像サイズ（664×942）と一致
2. PyMuPDF で抽出したテキスト bbox の x 座標は、XML 座標 × `scale_x`（= pdf_width / xml_width）と一致
3. ただし、y 座標は PyMuPDF の `insert_text()` が baseline 基準で配置するため、XML 座標からの単純なスケーリング値とは完全には一致しない
4. 透明テキストを緑色半透明に変更したため、PDF 上でテキストレイヤーの視認性が向上した

### 原因

- XML 座標系は左上原点、PDF 座標系は左下原点であるため、y 座標は反転が必要
- PyMuPDF の `insert_text()` はテキストの baseline（文字下端）を指定座標に合わせて配置する
- そのため、XML の `Y`（文字上端）をそのまま使うと、テキストが実際の文字上端より下にずれて配置される
- スケーリング変換式
  - `scale_x = pdf_width / xml_width`
  - `scale_y = pdf_height / xml_height`
  - `pdf_x = xml_x * scale_x`
  - `pdf_y = pdf_height - (xml_y + xml_line_height) * scale_y`

### 対応

- `OcrPage` に `xml_width` / `xml_height` を追加し、PDF 生成時にスケーリング係数を計算するようにした
- `_insert_text_line()` で X、Y、幅、高さ、フォントサイズをスケーリングするようにした
- 目視確認用にテキスト色を緑色（`color=(0, 1, 0)`、`fill_opacity=0.5`）に変更

### 備考

- 緑色半透明テキストはデバッグ用途であり、本番運用時は `color=(0, 0, 0)`、`fill_opacity=0` に戻す必要がある
- y 座標の微妙なずれ（baseline 補正）については、必要に応じて `pdf_y` に `baseline_offset` を加える調整を検討する
  - 例：`pdf_y -= font_size * descent_ratio`
- OCR 認識ミス（`RAG` → `RAC`、`Improving` → `mproving`、`GPT-4` → `〓PT-4` など）は OCR エンジン側の問題であり、backend 側の修正では解消できない
- 認識精度改善は `ocr-worker` 側のモデル・前処理・推論パラメータ調整が必要

## 14. OCR 性能計測に関する注意事項（004003）

- `scripts/benchmark_ocr.sh` の `SAMPLE_DIR` は `PROJECT_ROOT` と結合して使用されるため、絶対パスを指定するとパスが二重になる
- 2026-09-01 に `BENCHMARK_SAMPLE_DIR` 環境変数で上書き可能にしたが、相対パス（`sample-png/...`）を指定することを推奨する
- 3 ページの OCR 処理でも約 6 分半（396 秒）かかるため、テスト時の HTTP タイムアウト設定に注意する
- 性能計測スクリプトは実行完了後に `/data/extracted/{job_id}` と `/data/ocr_output/{job_id}` を削除するが、`/data/pdfs/{job_id}.pdf` は削除しない
- 詳細は `ocr-results-004003/performance-test-report-004003.md` を参照

