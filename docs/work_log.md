# 作業ログ

本ドキュメントは、book2pdf プロジェクトの複数モジュールにまたがる全体横断の作業ログです。

## 2026-08-13 frontend Docker イメージ再構成・docker compose 起動確認

### 目的

frontend コンテナの Next.js 15.1.6 への統一と、docker compose による backend / ocr-worker / frontend の 3 コンテナ起動確認を行う。

### 前提

- frontend の `package.json` / `package-lock.json` / `Dockerfile` は前段階で Next.js 15.1.6 向けに整理済み
- ocr-worker の Dockerfile は PyTorch インストール部分で `--index-url` を使用しており、ビルドエラーが発生していた

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# 既存コンテナ・イメージ・ボリュームのクリーンアップ
docker compose down --rmi local --volumes --remove-orphans
docker builder prune -f
docker system prune -f

# frontend dev イメージの単体ビルド
cd frontend
docker build --no-cache --target dev -t book2pdf-frontend-dev .

# コンテナ内の next バージョン確認
docker run --rm -it book2pdf-frontend-dev:latest \
  cat /app/node_modules/next/package.json | grep '"version"'
# -> "version": "15.1.6"

# 単体起動確認
docker run -d --name book2pdf-frontend -p 3000:3000 book2pdf-frontend-dev:latest

# 起動ログ確認
docker logs --tail 50 book2pdf-frontend
# -> ▲ Next.js 15.1.6
# -> Ready in 1487ms

# ヘルスチェック
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# -> 200
```

### ocr-worker Dockerfile 修正

`ocr-worker/Dockerfile` の PyTorch インストール部分を以下のように修正した。

修正前：
```dockerfile
RUN pip install --no-cache-dir \
    torch==2.0.1+cpu \
    torchvision==0.15.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu
```

修正後：
```dockerfile
RUN pip install --upgrade "pip<24.1" setuptools wheel \
    && pip install --no-cache-dir \
        torch==2.0.1+cpu \
        torchvision==0.15.2+cpu \
        --extra-index-url https://download.pytorch.org/whl/cpu
```

修正理由：
- `--index-url` を使うと PyTorch 以外の依存パッケージも PyTorch の index から解決しようとし、メタデータ名の大文字小文字不一致で失敗する
- pip 24.1 以降では `pytorch-lightning==1.6.5` のメタデータ（`torch (>=1.8.*)`）が拒否されるため、`pip<24.1` を使用

### docker compose 起動確認

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
docker compose up -d --build
```

結果：
- `book2pdf-frontend`（Next.js 15.1.6）が `health: starting` で起動
- `book2pdf-backend` が起動
- `book2pdf-ocr-worker` が起動

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/jobs/
# -> 405 （POST 専用のため OK）
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/docs
# -> 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# -> 200
```

### テスト用 ZIP 作成

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
mkdir -p test_zips
cd test_zips
zip -j sample_002-004.zip \
  ../sample-png/AI\ ・LLMの実務でつかえるRAG精度改善_trimmed/002.png \
  ../sample-png/AI\ ・LLMの実務でつかえるRAG精度改善_trimmed/003.png \
  ../sample-png/AI\ ・LLMの実務でつかえるRAG精度改善_trimmed/004.png
```

### 結果

- frontend の Docker イメージが Next.js 15.1.6 で正常に起動することを確認
- docker compose で 3 コンテナが同時に起動することを確認
- `http://localhost:3000` にブラウザでアクセス可能
- ZIP アップロード API は `Content-Type: application/zip` を明示すると正常に動作
- OCR 実行 API は ocr-worker 内部で 500 エラーが発生（詳細なトレースバックは取得中）

### 注意事項

- ocr-worker の 500 エラーは、モデルロードまでは成功しているが、その後の推論処理で失敗している可能性がある
- 詳細なエラーを取得するためには、ocr-worker コンテナ内で直接デバッグが必要
- 本件は `backend/docs/work_log.md` および `ocr-worker/docs/work_log.md` でも追記予定

### 関連タスク

- frontend タスク：Next.js 15.1.6 への Docker 再構成（完了）
- backend タスク：ocr-worker 500 エラーの原因調査（未完了）
- 全体タスク：frontend から ZIP アップロード・PDF ダウンロードの統合検証（未完了）
