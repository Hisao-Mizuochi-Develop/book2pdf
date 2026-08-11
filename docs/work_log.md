# 作業ログ

本ドキュメントは、`backend` / `frontend` / `ocr-worker` / `localapp` を横断するプロジェクト全体のタスク実施にあたり実行したコマンドとその結果を記録したものです。

---

## 2026-08-12 タスク001002：結合テスト手順書の作成

### 目的

`frontend` / `backend` / `ocr-worker` の 3 モジュールを横断した結合テスト手順を `./docs/` にまとめ、今後の運用・確認に再利用できるようにする。

### 前提

- 既に Docker Compose 上で 3 サービスの起動・結合テストが成功していること
- テスト用 ZIP ファイル、backend の `/health`、ocr-worker の `/health`、frontend の HTTP 200 応答が確認済みであること
- `docs/web-ocr-system-plan.md` が既存の全体計画書として存在すること

### 実施コマンド

```bash
# プロジェクトルートに移動
cd /Users/hisao/Documents/work4/sakura/book2pdf

# 新規ドキュメントを作成
cat > docs/integration-test-guide.md <<'EOF'
# 結合テスト手順書
...
EOF

# 全体計画書にリンクを追加（docs/web-ocr-system-plan.md を編集）
# - docs/ フォルダ構成に integration-test-guide.md を追加
# - 関連ドキュメントセクションにリンクを追加

# ./docs/ 用のタスク管理表・作業ログ・注意事項ファイルを作成
cat > docs/tasks.md <<'EOF'
...
EOF
cat > docs/work_log.md <<'EOF'
...
EOF
cat > docs/caveats.md <<'EOF'
...
EOF

# backend/docs/ から誤作成した横断タスク 006001 を削除
# backend/docs/work_log.md から 006001 のエントリを削除

# git 状態確認
git status --short
```

### 結果

- `./docs/integration-test-guide.md` を新規作成した
  - 対象システム、前提条件、テスト用 ZIP 作成、コンテナ起動、ヘルスチェックを記載
  - フロントエンド UI 経由と cURL 経由の 2 パターンの手順を記載
  - 進捗通知（SSE）確認手順も追加
  - トラブルシューティングとして以下を記載
    - backend ソース変更反映には `--build` が必要
    - ocr-worker の `GlobalHydra is already initialized` エラー対応
    - frontend から backend 呼び出し時の CORS 設定
    - Puppeteer/ブラウザでの PDF `ERR_ABORTED` 現象
    - OCR 実行のタイムアウト対応
- `docs/web-ocr-system-plan.md` の「フォルダ・ファイル構成」に `integration-test-guide.md` を追加した
- `.clinerules` の「フォルダ・ドキュメント配置ルール」に `./docs/` 用の `tasks.md` / `work_log.md` / `caveats.md` 配置ルールを追加した
- `./docs/tasks.md` / `./docs/work_log.md` / `./docs/caveats.md` を新規作成した
- `backend/docs/tasks.md` からユースケース 006（横断タスク 006001）を削除し、 `./docs/tasks.md` に移行した
- `backend/docs/work_log.md` から 006001 のエントリを削除し、 `./docs/work_log.md` に移行した

### 注意事項

- `./docs/` 配下の変更は `.clinerules` に基づき、変更箇所をユーザーに提案・許可を得てから実施する必要がある
  - 今回はユーザーからの指摘を受けて実施したため、指示に従って変更を行った
- 結合テスト手順は実行環境（macOS / Docker Desktop）に依存するため、Linux 等では一部コマンドやパスを読み替える必要がある
- CORS 設定は現時点では未実装のため、frontend から backend を直接呼び出す際に追加対応が必要になる可能性がある
