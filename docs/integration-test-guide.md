# 結合テスト手順書

本ドキュメントは、`frontend` / `backend` / `ocr-worker` の各モジュールを横断して行う結合テストの手順をまとめたものです。Docker Compose 上で 3 サービスを起動し、ZIP アップロードから OCR 実行、検索可能 PDF ダウンロードまでの一連の流れを検証します。

## 1. 対象システム

- `frontend`: Next.js 16 製の Web UI
- `backend`: FastAPI 製のジョブ管理・PDF 生成サービス
- `ocr-worker`: ndlocr_cli を Python パッケージとして動かす OCR 実行サービス

## 2. 前提条件

- Docker Desktop などの Docker エンジンが起動していること
- `docker compose` コマンドが使用できること
- テスト用の ZIP ファイルが用意できていること（後述の「3.1 テスト用 ZIP ファイルの作成」を参照）
- 各モジュールのドキュメントを併せて確認しておくこと
  - [`backend/docs/backend-system-spec.md`](../backend/docs/backend-system-spec.md)
  - [`frontend/docs/frontend-system-spec.md`](../frontend/docs/frontend-system-spec.md)
  - [`ocr-worker/docs/ocr-worker-system-spec.md`](../ocr-worker/docs/ocr-worker-system-spec.md)

## 3. テスト準備

### 3.1 テスト用 ZIP ファイルの作成

OCR 対象となるページ画像を ZIP アーカイブにまとめます。以下は macOS の例です。

```bash
# テスト用画像を格納するディレクトリを作成
mkdir -p /tmp/book2pdf-test-images

# 任意の PNG/JPEG 画像をコピー（ここでは例として sample_*.png を使用）
cp sample_*.png /tmp/book2pdf-test-images/

# ZIP ファイルを作成
cd /tmp/book2pdf-test-images
zip -r /tmp/book2pdf-test.zip .
```

画像は 2〜3 ページ分用意すると、複数ページの PDF 生成まで確認しやすくなります。

### 3.2 プロジェクトルートへの移動

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
```

## 4. 環境構築

### 4.1 コンテナのビルドと起動

```bash
docker compose up -d --build
```

初回または backend / ocr-worker / frontend のソースコードを変更した後は、必ず `--build` を指定してください。`docker compose restart` だけでは、ホスト側のソース変更がコンテナイメージに反映されません。

### 4.2 サービス起動確認

```bash
# backend ヘルスチェック
curl -s http://localhost:8000/health
# 期待結果: {"status":"ok"}

# ocr-worker ヘルスチェック
curl -s http://localhost:8001/health
# 期待結果: {"status":"ok"}

# frontend 起動確認
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# 期待結果: 200
```

## 5. 結合テスト手順

### 5.1 フロントエンド UI 経由で実施する場合

1. ブラウザで `http://localhost:3000` を開く
2. トップページに「book2pdf」「電子書籍画像から検索可能 PDF を作成」というタイトルとサブタイトル、「ファイルを選択」input、「アップロードして OCR 実行」ボタンが表示されることを確認する
3. 「ファイルを選択」から `/tmp/book2pdf-test.zip` を選択する
4. 「アップロードして OCR 実行」ボタンをクリックする
5. 進捗表示エリアにジョブ ID、OCR 進捗、PDF 生成状況が表示されることを確認する
6. OCR 完了後、「PDF をダウンロード」リンクが表示されたらクリックする
7. 2 ページ分の検索可能 PDF がダウンロードされることを確認する

ブラウザによっては PDF 直接表示時に `net::ERR_ABORTED` が発生する場合があります。これはブラウザ側の制限によるもので、API 自体は正常に動作しています。その場合は「5.2 cURL 経由で実施する場合」で PDF ダウンロードを確認してください。

### 5.2 cURL 経由で API を直接確認する場合

#### ステップ 1: ジョブ作成

```bash
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/jobs)
JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job_id')
echo "$JOB_ID"
```

#### ステップ 2: ZIP アップロード

```bash
curl -s -X POST \
  -F "file=@/tmp/book2pdf-test.zip;type=application/zip" \
  http://localhost:8000/api/jobs/$JOB_ID/upload
```

期待結果: `status` が `UPLOADED` で、画像ファイル一覧が `files` に含まれる JSON が返る。

#### ステップ 3: OCR 実行

```bash
curl -s --max-time 600 \
  -X POST http://localhost:8000/api/jobs/$JOB_ID/ocr
```

ndlocr_cli の初回推論時はモデル初期化に時間がかかるため、`--max-time 600` など長めのタイムアウトを設定してください。

期待結果: `status` が `COMPLETED` となり、OCR 結果のテキストや XML パスが含まれる JSON が返る。

#### ステップ 4: PDF ダウンロード

```bash
curl -s -o /tmp/book2pdf-result.pdf \
  http://localhost:8000/api/jobs/$JOB_ID/pdf

# ファイルサイズを確認
ls -lh /tmp/book2pdf-result.pdf

# PDF のページ数を確認（PyMuPDF が使える場合）
python - <<'PY'
import fitz
doc = fitz.open('/tmp/book2pdf-result.pdf')
print('pages:', len(doc))
PY
```

期待結果: HTTP 200 で `application/pdf` が返り、2 ページ以上の PDF がダウンロードされる。

#### ステップ 5: 進捗通知の確認（任意）

```bash
curl -s --max-time 60 \
  http://localhost:8000/api/jobs/$JOB_ID/events
```

SSE 形式で進捗イベントが配信されます。OCR 処理中に実行すると、`processing`、`completed` などの進捗が確認できます。

## 6. トラブルシューティング

### 6.1 `GET /api/jobs/{job_id}/pdf` が 404 エラーを返す

backend コンテナイメージに最新のソースが反映されていない可能性があります。

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
docker compose up -d --build backend
```

### 6.2 2 回目以降の OCR リクエストで `GlobalHydra is already initialized` エラーが発生する

`ocr-worker/app/main.py` で `GlobalHydra.instance().is_initialized()` を確認し、初期化済みの場合は `clear()` してから `initialize()` するように修正済みです。修正後は ocr-worker コンテナを再ビルド・再起動してください。

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
docker compose up -d --build ocr-worker
```

### 6.3 frontend から backend API を呼び出す際に CORS エラーが発生する

frontend（`http://localhost:3000`）から backend（`http://localhost:8000`）を呼び出す際、ブラウザの同一オリジンポリシーによりリクエストがブロックされる場合があります。backend に以下のような CORS 設定を追加することを検討してください。

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

### 6.4 PDF ダウンロードでブラウザが `ERR_ABORTED` を返す

Puppeteer や一部のブラウザでは、API から直接返される PDF に対して `net::ERR_ABORTED` が発生することがあります。これはブラウザ側の制限によるものです。curl やブラウザのアドレスバーに直接 `http://localhost:8000/api/jobs/$JOB_ID/pdf` を入力することで、正常にダウンロードできることを確認してください。

### 6.5 OCR 実行でタイムアウトが発生する

ndlocr_cli の初回推論時はモデル初期化に時間がかかります。curl では `--max-time 600`、backend 側の `OCR_WORKER_REQUEST_TIMEOUT` 環境変数も必要に応じて調整してください。

## 7. 終了処理

テスト完了後、コンテナを停止・削除する場合は以下を実行してください。

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
docker compose down
```

ボリュームも含めて完全に削除する場合は `-v` を追加してください。

```bash
docker compose down -v
```

## 8. 関連ドキュメント

- [`backend/docs/backend-system-spec.md`](../backend/docs/backend-system-spec.md)
- [`backend/docs/caveats.md`](../backend/docs/caveats.md)
- [`frontend/docs/frontend-system-spec.md`](../frontend/docs/frontend-system-spec.md)
- [`frontend/docs/work_log.md`](../frontend/docs/work_log.md)
- [`ocr-worker/docs/ocr-worker-system-spec.md`](../ocr-worker/docs/ocr-worker-system-spec.md)
- [`ocr-worker/docs/caveats.md`](../ocr-worker/docs/caveats.md)
