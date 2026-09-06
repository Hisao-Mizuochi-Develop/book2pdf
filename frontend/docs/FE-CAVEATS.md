# frontend 注意事項

本ドキュメントは、book2pdf プロジェクトの frontend（Next.js + TypeScript + Tailwind CSS）に関する環境差異、トラブルシューティング、回避策をまとめたものです。

---

## 1. Next.js / React / Tailwind CSS のバージョンと構成

- `create-next-app` 実行時にインストールされるのは執筆時点の最新版（Next.js 16.x / React 19 等）となることがあります。本プロジェクトでは **Next.js 15.1.6** に固定しているため、`package.json` / `package-lock.json` / `Dockerfile` を変更する場合は必ず 15.1.6 系に収めてください。
- Tailwind CSS は **v4** がインストールされます。v4 では `tailwind.config.ts` ではなく `src/app/globals.css` の `@import "tailwindcss"` と `@theme inline` で設定を行います。
- 本番ビルド時は `next.config.ts` の `output: "standalone"` を利用し、最小構成の `runner` ステージで起動します。

## 2. Docker / Docker Compose 上の開発

- 初回ビルド時は frontend の `npm install` に時間がかかるため、コンテナ起動から `http://localhost:3000` が応答するまで **1 〜 2 分**ほどかかることがあります。
- ホスト側の `node_modules` は存在せず、コンテナ内の `node_modules` を使用します。ホストで `npm install` すると OS ネイティブ依存（`sharp` 等）の不一致が発生する可能性があるため避けてください。
- `docker compose restart` だけでは、ホスト側のソース変更がコンテナイメージに反映されません。`package.json` や `Dockerfile` を変更した場合は `docker compose up -d --build` を実行してください。
- 開発サーバーはフォアグラウンドで起動するため、Docker Compose では `Dockerfile` の **`target: dev`** を使用してください。

## 3. 開発サーバーと backend 依存

- `npm run dev` で起動する開発サーバーは backend API への依存を持ちません。backend が停止していても **トップページの表示は可能**です。
- ただし、ZIP アップロード、OCR 実行、PDF ダウンロードなどの機能は backend API を呼び出すため、backend が起動していないと失敗します。
- frontend（`localhost:3000`）から backend（`localhost:8000`）へ API を呼び出す際、同一オリジンではないため **CORS 設定が必要になることがあります**。必要に応じて backend に `fastapi.middleware.cors.CORSMiddleware` を追加してください。

## 4. ブラウザ・自動化テストの制限

- ブラウザによっては PDF 直接表示時に `net::ERR_ABORTED` が発生する場合があります。これはブラウザ側の制限であり、API 自体は正常に動作しています。`downloadPdf()` 関数は Blob 経由でファイル保存を行うため、実際のユーザー操作では問題ありません。
- Puppeteer 等の自動化ツールではファイル選択ダイアログの操作が困難なため、ファイルアップロードから PDF ダウンロードまでの完全な E2E テストは手動で実施することを推奨します。

## 5. コンテナ・イメージに関するその他の留意点

- コンテナ名は `book2pdf-frontend` を使用するよう統一しました。
- `builder` / `runner` ステージは開発用途の `dev` ターゲットのみ検証しており、本番ビルド用イメージは別途検証が必要です。
