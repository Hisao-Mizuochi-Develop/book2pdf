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

上記コマンドで `backend` / `ocr-worker` / `frontend` の 3 サービスがすべて起動します。初回または backend / ocr-worker / frontend のソースコードを変更した後は、必ず `--build` を指定してください。`docker compose restart` だけでは、ホスト側のソース変更がコンテナイメージに反映されません。

初回ビルド時は frontend の `npm install` に時間がかかるため、コンテナ起動から `http://localhost:3000` が応答するまで 1 〜 2 分ほどかかることがあります。`docker compose ps` や `docker compose logs -f frontend` で状態を確認してください。

### 4.2 サービス起動確認

```bash
# backend ヘルスチェック
curl -s http://localhost:8000/health
# 期待結果: {"status":"ok"}

# ocr-worker ヘルスチェック
curl -s http://localhost:8001/health
# 期待結果: {"status":"ok"}

# frontend 起動確認（初回は 1 〜 2 分ほど待つことがあります）
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# 期待結果: 200

# frontend コンテナの状態確認
docker compose ps
# 期待結果: book2pdf-frontend の STATUS が healthy または Up になっている
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

## 7. 性能テスト

性能テストは `scripts/benchmark_ocr.sh` を実行して行います。

### 7.1 目的

OCR 処理のボトルネックを特定し、以下の工程時間を定量化します。

- Docker Compose 起動時間
- ジョブ作成時間
- ZIP アップロード時間
- OCR 全体時間
- 1 ページごとの OCR 処理時間
- 1 ページあたり平均 OCR 処理時間
- PDF 生成時間
- PDF ダウンロード時間
- 合計処理時間

### 7.2 入力データ

- **サンプル画像**: `sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/001.png` 〜 `010.png`
- **入力 ZIP**: `/tmp/book2pdf-benchmark/benchmark-input-10pages.zip`
- **ページ数**: 10 ページ固定

### 7.3 実行手順

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
./scripts/benchmark_ocr.sh
```

### 7.4 結果の確認

実行後、以下のファイルに結果が出力されます。

- `/tmp/book2pdf-benchmark/results.csv`
- `/tmp/book2pdf-benchmark/results.txt`

`results.csv` と `results.txt` には、以下の項目がすべて出力されます。

- Docker Compose 起動時間
- ジョブ作成時間
- ZIP アップロード時間
- OCR 全体時間
- 1 ページあたり平均 OCR 処理時間
- ZIP 解凍時間（ログ）
- PDF 生成時間（ログ）
- PDF ダウンロード時間
- 合計処理時間

CSV の例:

```csv
item,seconds
Docker Compose 起動時間,12.345
ジョブ作成時間,0.012
ZIP アップロード時間,0.234
OCR 全体時間,123.456
1 ページあたり平均 OCR 処理時間,11.234
ZIP 解凍時間（ログ）,0.056
PDF 生成時間（ログ）,0.789
PDF ダウンロード時間,0.045
合計処理時間,136.681
```

`results.txt` には、上記 CSV 内容に加えて、1 ページごとの OCR 処理時間も時系列で記録されます。

### 7.5 注意事項

- 初回実行時は ndlocr_cli のモデル初期化に時間がかかるため、OCR 全体時間が長めに出ることがあります
- `LOG_LEVEL=DEBUG` が設定されていることを確認してください（`docker-compose.yml`）
- 性能テスト終了後、入力 ZIP や展開画像、OCR 出力は自動的に削除されます

### 7.6 性能テスト結果

本節は、`scripts/benchmark_ocr.sh` を使用して実際に性能テストを実施した結果を記録したものです。

#### 実行環境

- 日時: 2026-08-12
- 実行方式: Docker Compose（`backend` / `ocr-worker` / `frontend` を別コンテナとして分離）
- 実行環境: CPU 実行（GPU 未使用）
- 入力データ: 10 ページ分の PNG 画像
  - `sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/001.png` 〜 `010.png`
  - 入力 ZIP: `/tmp/book2pdf-benchmark/benchmark-input-10pages.zip`

#### 計測結果サマリー（修正後）

| 項目 | 時間（秒） |
|---|---|---|
| Docker Compose 起動時間 | 0.147 |
| ジョブ作成時間 | 0.053 |
| ZIP アップロード時間 | 0.111 |
| OCR 全体時間 | 1115.677 |
| 1 ページあたり平均 OCR 処理時間 | 110.806 |
| ZIP 解凍時間（ログ） | 0.024 |
| PDF 生成時間（ログ） | 0.332 |
| PDF ダウンロード時間 | 0.057 |
| 合計処理時間 | 1116.045 |

- OCR 全体時間は約 18 分 36 秒でした
- 1 ページあたりの平均 OCR 処理時間は約 110.8 秒でした
- ZIP 解凍・PDF 生成はいずれも 1 秒未満で完了しました

#### 個別ページの OCR 処理時間

今回の実行では、OCR 処理開始時刻以降の ocr-worker ログのみを対象としたため、10 ページ分の OCR 処理時間が正しく抽出されました。

| ページ | 処理時間（秒） |
|---|---|
| 1 | 98.213 |
| 2 | 109.110 |
| 3 | 103.367 |
| 4 | 124.505 |
| 5 | 103.464 |
| 6 | 88.248 |
| 7 | 85.691 |
| 8 | 135.683 |
| 9 | 171.684 |
| 10 | 88.091 |

#### 個別ページの OCR 処理時間の統計

| 統計 | 値（秒） |
|---|---|
| 最大値 | 171.684 |
| 最小値 | 85.691 |
| 中央値 | 103.416 |
| 平均 | 110.806 |

#### 計測上の注意点

- 初回実行時は ndlocr_cli のモデル初期化に時間がかかるため、OCR 全体時間が長めに出ることがあります
- 2 回目以降の実行でも、CPU 負荷やコンテナの状態により処理時間は変動します
- 性能テストスクリプトは `LOG_LEVEL=DEBUG` の設定を前提としています

#### 既知の問題

- 2026-08-12 時点で以下の問題を修正済みです
  - `scripts/benchmark_ocr.sh` の backend ログ抽出パターンが実際のログ形式と一致していないため、ZIP 解凍時間と PDF 生成時間が `N/A` となっていた問題
  - `docker compose logs` が ocr-worker の全ログを対象としていたため、1 ページごとの OCR 処理時間に過去の実行分が混在していた問題

## 8. 終了処理

テスト完了後、コンテナを停止・削除する場合は以下を実行してください。

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
docker compose down
```

ボリュームも含めて完全に削除する場合は `-v` を追加してください。

```bash
docker compose down -v
```

## 9. 関連ドキュメント

- [`backend/docs/backend-system-spec.md`](../backend/docs/backend-system-spec.md)
- [`backend/docs/caveats.md`](../backend/docs/caveats.md)
- [`frontend/docs/frontend-system-spec.md`](../frontend/docs/frontend-system-spec.md)
- [`frontend/docs/work_log.md`](../frontend/docs/work_log.md)
- [`ocr-worker/docs/ocr-worker-system-spec.md`](../ocr-worker/docs/ocr-worker-system-spec.md)
- [`ocr-worker/docs/caveats.md`](../ocr-worker/docs/caveats.md)
