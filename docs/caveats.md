# 全体横断の注意事項

本ドキュメントは、`backend` / `frontend` / `ocr-worker` / `localapp` を横断する、プロジェクト全体に関わる注意事項をまとめたものです。各モジュール固有の注意事項は `<module>/docs/caveats.md` を参照してください。

## 1. Docker Compose 全サービス起動

- `docker compose up -d --build` で全サービスを最新イメージで起動する
  - ソースコード変更後は `--build` を必ず指定すること
  - `docker compose restart` ではホスト側のソース変更がコンテナイメージに反映されない
- 起動後は以下のエンドポイントでヘルスチェックを行う
  - backend: `http://localhost:8000/health`
  - ocr-worker: `http://localhost:8001/health`
  - frontend: `http://localhost:3000`（HTTP 200）

## 2. 結合テストに関する注意事項

- 結合テストの手順は [`docs/integration-test-guide.md`](integration-test-guide.md) にまとめている
- テスト用の ZIP ファイルは画像ファイル（PNG/JPEG）のみを含むようにする
  - 2〜3 ページ分用意すると、複数ページの PDF 生成まで確認しやすい
- OCR 実行は初回推論時にモデル初期化が入るため、数分かかることがある
  - curl では `--max-time 600` など長めのタイムアウトを設定する
  - backend 側の `OCR_WORKER_REQUEST_TIMEOUT` 環境変数も必要に応じて調整する

## 3. コンテナ間連携

- backend と ocr-worker は Docker Compose 上で別コンテナとして動作する
- 両コンテナ間では共有ボリューム `/data/extracted` などを使って画像ファイルを受け渡す
- backend から ocr-worker を呼び出す際の URL は `http://ocr-worker:8000` を使用する
  - Docker Compose のサービス名で名前解決される

## 4. フロントエンドとバックエンドの連携

- frontend（`http://localhost:3000`）から backend（`http://localhost:8000`）を呼び出す際、ブラウザの同一オリジンポリシーによりリクエストがブロックされる場合がある
- 必要に応じて backend に CORS 設定を追加する
  - 現時点では未実装のため、追加対応が必要になる可能性がある
- PDF ダウンロード時に一部のブラウザや Puppeteer で `net::ERR_ABORTED` が発生することがある
  - これはブラウザ側の制限によるもので、API 自体は正常に動作している
  - curl やブラウザのアドレスバーへの直接入力で正常にダウンロードできることを確認する

## 5. ジョブ状態の管理

- 現状のジョブ状態は backend のメモリ内（辞書）で管理されている
- backend コンテナの再起動後は過去のジョブにアクセスできなくなる
- 永続化は `backend/docs/tasks.md` のユースケース 004 で対応予定

## 6. 関連ドキュメント

- 各モジュール固有の注意事項
  - [`backend/docs/caveats.md`](../backend/docs/caveats.md)
  - [`ocr-worker/docs/caveats.md`](../ocr-worker/docs/caveats.md)
- 結合テスト手順
  - [`docs/integration-test-guide.md`](integration-test-guide.md)
