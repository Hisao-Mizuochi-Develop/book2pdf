# 全体横断の注意事項

## Docker Compose 結合テストに関する注意事項

- 初回ビルド時は frontend の `npm install` に時間がかかるため、コンテナ起動から `http://localhost:3000` が応答するまで 1 〜 2 分ほどかかることがあります
- `docker compose restart` だけでは、ホスト側のソース変更がコンテナイメージに反映されません。ソース変更後は `docker compose up -d --build` を実行してください
- ブラウザによっては PDF 直接表示時に `net::ERR_ABORTED` が発生する場合があります。これはブラウザ側の制限によるもので、API 自体は正常に動作しています
- OCR 実行時は ndlocr_cli のモデル初期化に時間がかかるため、cURL などで `--max-time 600` など長めのタイムアウトを設定してください
- 性能テストは `LOG_LEVEL=DEBUG` の設定を前提としています

## 進捗通知のポーリング

- localapp では、プロキシ環境や接続の不安定さを考慮し、SSE より HTTP ポーリングを優先して使用する
- ポーリング間隔は原則 1 秒とし、1 リクエストあたりのタイムアウトは 10 秒とする
- `GET /api/jobs/{job_id}` の接続に失敗した場合は、最大 3 回まで 1 秒 / 2 秒 / 4 秒の指数関数的バックオフでリトライする
- リトライ前には「ジョブ状態の取得を再試行します」という進捗メッセージを UI に通知し、ユーザーに一過性の通信エラーであることを伝える
- バックエンド側の進捗通知は現状 `JobResponse` の拡張で対応しており、将来的に専用の `/progress` エンドポイントを検討してもよい
- 詳細なプロトコルやペイロード形式は [`docs/SY-PROGRESS-NOTIFICATION-SPEC.md`](SY-PROGRESS-NOTIFICATION-SPEC.md) を参照
