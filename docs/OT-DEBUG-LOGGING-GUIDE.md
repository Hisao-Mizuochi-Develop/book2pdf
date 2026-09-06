# デバッグログ確認ガイド

本ドキュメントでは、book2pdf システムの各コンポーネントにおけるデバッグログの設定方法・確認方法をまとめます。

---

## 1. backend コンテナ

### 1.1 ログ設定

`backend/app/main.py` で Python の標準 `logging` モジュールを使って設定しています。

```python
# backend/app/main.py (line 26-30)
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

環境変数 `LOG_LEVEL` でログレベルを制御します。`docker-compose.yml` では `DEBUG` に設定されています。

### 1.2 ログ確認コマンド

```bash
# backend のログをリアルタイムで確認
docker compose logs backend -f

# 直近 50 行を表示
docker compose logs backend --tail=50

# 過去のログを時系列で表示
docker compose logs backend --timestamps
```

### 1.3 DEBUG ログ出力箇所

`backend/app/routers/jobs.py` で以下の `logger.debug()` 呼び出しがあります。

| 行 | 内容 |
|----|------|
| 220 | OCR エンドポイント処理開始：`job_id=%s` |
| 282-286 | OCR エンドポイント処理完了：`job_id=%s, elapsed=%.3fs, avg_per_page=%.3fs` |
| 342-346 | PDF ダウンロード要求でファイル不在：`job_id=%s, pdf_path=%s` |
| 353-358 | PDF ダウンロード返却：`job_id=%s, pdf_path=%s, size=%d bytes` |

出力例：
```
2025-01-15 08:30:25 [DEBUG] app.routers.jobs: OCR エンドポイント処理を開始します: job_id=abc123
2025-01-15 08:35:42 [DEBUG] app.routers.jobs: OCR エンドポイント処理が完了しました: job_id=abc123, elapsed=317.234s, avg_per_page=15.861s
```

---

## 2. ocr-worker コンテナ

### 2.1 ログ設定

`ocr-worker/app/main.py` で同様に `logging` モジュールを使用しています。

```python
# ocr-worker/app/main.py (line 63-67)
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

### 2.2 ログ確認コマンド

```bash
# ocr-worker のログをリアルタイムで確認
docker compose logs ocr-worker -f

# 直近 50 行を表示
docker compose logs ocr-worker --tail=50

# エラーログのみ抽出
docker compose logs ocr-worker | grep "ERROR"
```

### 2.3 DEBUG ログ出力箇所

`ocr-worker/app/main.py` で以下のログがあります。

| 行 | レベル | 内容 |
|----|--------|------|
| 240-243 | DEBUG | 前処理開始：`src=%s, dst=%s` |
| 258-262 | DEBUG | 前処理完了：`processed_count=%d, dst_root=%s` |
| 372 | DEBUG | 前処理適用：`job_id=%s` |
| 378 | DEBUG | 前処理無効：`job_id=%s` |
| 427 | DEBUG | OCR 処理開始：`job_id=%s, total_pages=%d` |
| 436-441 | DEBUG | OCR 処理完了：`job_id=%s, elapsed=%.3fs, avg_per_page=%.3fs` |
| 475 | ERROR | エラー発生時のトレースバック |
| 498-501 | DEBUG | 一時ディレクトリ削除 |

出力例：
```
2025-01-15 08:30:30 [DEBUG] __main__: 前処理を適用します: job_id=abc123
2025-01-15 08:30:32 [DEBUG] __main__: 前処理が完了しました: processed_count=20, dst_root=/tmp/ocr_preprocess_abc123_xxx/input
2025-01-15 08:30:32 [DEBUG] __main__: OCR 処理を開始します: job_id=abc123, total_pages=20
2025-01-15 08:35:40 [DEBUG] __main__: OCR 処理が完了しました: job_id=abc123, elapsed=308.123s, avg_per_page=15.406s
```

---

## 3. frontend コンテナ

### 3.1 ログ確認方法

Next.js 開発サーバーのログはコンテナ標準出力に出力されます。

```bash
# frontend のログをリアルタイムで確認
docker compose logs frontend -f

# エラーと警告のみ抽出
docker compose logs frontend | grep -E "(error|warning|Error|Warning)"
```

### 3.2 ブラウザ側ログ

ブラウザの開発者ツール（F12）→ Console タブで確認できます。

---

## 4. localapp（Tauri）

### 4.1 Rust 側のログ確認

Tauri アプリ起動時のターミナル経由で確認します。`localapp/src-tauri/src/commands/` 内では `println!()` でデバッグ出力しています。

```bash
# Tauri アプリを起動npm run tauri dev
```

**主要な出力箇所** (`pdf_creation.rs`)：
| 行 | 内容 |
|----|------|
| invoke 直後 | `PDF【job_id={}】作成開始` |
| create_job 後 | `DEBUG: job_id = {}` |
| upload ZIP 後 | `DEBUG: upload response = {}` |
| OCR invoke 後 | `DEBUG: OCR response = {}` |
| get_job レスポンス | `DEBUG: get_job response = status={:?}` |
| 完了時 | `PDF作成完了: {}` |
| エラー時 | `PDF作成エラー: {}` |

### 4.2 JavaScript 側のログ確認

ブラウザ DevTools（Tauri 内蔵 WebView の場合は右クリック → 検証）で確認します。

`localapp/src/store/pdfCreationStore.ts` で以下の `console.log`/`console.error` があります：
- `createPdfFromFolder` 開始時：`【PDF作成開始】folder_path={}``
- ZIP 作成完了後：`【ZIP作成完了】zip_path={}`
- `create_job` レスポンス受信時：`【create_job】job_id={}`
- ZIP アップロード完了後：`【upload】status={}`
- OCR 実行完了後：`【ocr】status={}`
- `get_job` ポーリング時：`【get_job】status={:?}`
- `get_job` 異常レスポンス時：`【get_job】error={}`
- 3回エラー時：`【get_job】3回エラーで停止`
- PDF ダウンロード完了後：`【download】status={}`
- PDF 保存完了後：`PDF ファイル保存成功: pdf_path={}`
- 全体エラー時：`PDF 作成全体エラー: error={}`

`localapp/src/views/PdfCreationView.tsx` で以下のログがあります：
- PDF 作成ボタン押下時：`handleCreatePdf 開始`
- バリデーションエラー時：`handleCreatePdf バリデーションエラー`
- 処理完了後：`handleCreatePdf 完了`

---

## 5. ログレベルの変更方法

### 5.1 Docker Compose 環境

`docker-compose.yml` の各サービスの `environment` セクションで `LOG_LEVEL` を変更します。

```yaml
services:
  backend:
    environment:
      - LOG_LEVEL=DEBUG  # DEBUG / INFO / WARNING / ERROR

  ocr-worker:
    environment:
      - LOG_LEVEL=DEBUG  # DEBUG / INFO / WARNING / ERROR
```

変更後、コンテナを再起動します：
```bash
docker compose up -d --force-recreate
```

### 5.2 一時的に変更する場合（再起動不要）

```bash
# backend のログレベルを一時的に DEBUG に変更
docker compose exec backend python -c "import logging; logging.getLogger().setLevel(logging.DEBUG)"
```

### 5.3 ログレベルの設定値

| レベル | 出力内容 |
|--------|----------|
| `DEBUG` | 開発時の詳細情報（処理時間、中間状態など） |
| `INFO` | 通常運用時の情報（処理開始・完了など） |
| `WARNING` | 警告（非推奨機能の使用など） |
| `ERROR` | エラー（例外発生時など） |
| `CRITICAL` | 致命的エラー |

---

## 6. よくあるトラブルシューティング

### 6.1 ログが出ない場合

| チェック項目 | 確認方法 |
|------------|----------|
| コンテナが起動しているか | `docker compose ps` |
| ログレベルが `DEBUG` か | `docker compose exec backend env \| grep LOG_LEVEL` |
| uvicorn のログ設定が上書きしていないか | `docker compose logs backend \| head -n 5` |
| ファイルパスや行番号が最新か | コードを確認 |

### 6.2 コンテナが起動しない場合

```bash
# ビルドし直して起動
docker compose down
docker compose up -d --build

# 起動ログを確認
docker compose logs backend --tail=100
```

### 6.3 ocr-worker の OCR エラーを調べる

```bash
# エラーログを抽出
docker compose logs ocr-worker --tail=100 \| grep -E "(ERROR\|Failed\|Exception)"

# 進捗ファイルを確認
ls -la /var/lib/docker/volumes/book2pdf_progress/_data/
```

### 6.4 進捗ファイルの確認方法

ocr-worker は `/data/progress/{job_id}.json` に進捗を書き込みます。

```bash
# backend / ocr-worker のいずれかで確認
docker compose exec backend ls -la /data/progress
docker compose exec backend cat /data/progress/{job_id}.json
```

出力例：
```json
{
  "job_id": "abc123",
  "status": "processing",
  "progress": 0.5,
  "current_page": 10,
  "total_pages": 20,
  "message": "OCR 処理中...",
  "timestamp": "2025-01-15T08:33:10+00:00"
}
```

---

## 7. まとめ

| コンポーネント | ログ確認コマンド | 主な出力内容 |
|------------|--------------|-----------|
| backend | `docker compose logs backend -f` | OCR エンドポイント処理時間、PDF ダウンロード情報 |
| ocr-worker | `docker compose logs ocr-worker -f` | 前処理状況、OCR 処理時間、エラートレース |
| frontend | `docker compose logs frontend -f` | Next.js ビルド情報、ランタイムエラー |
| localapp Rust | `npm run tauri dev` のターミナル | API 通信状況、PDF 作成進捗 |
| localapp JS | ブラウザ DevTools | UI イベント、ストア状態変化 |

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-08-26 | 初版作成 |
