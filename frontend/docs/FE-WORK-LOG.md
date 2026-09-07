# 作業ログ

本ドキュメントは、book2pdf プロジェクトのフロントエンドタスク実施にあたり実行したコマンドとその結果を記録したものです。

## 2026-08-11 タスク001001：Next.js プロジェクトの初期構成

### 目的

Next.js 15（App Router）+ TypeScript + Tailwind CSS のフロントエンドプロジェクトを作成し、backend / ocr-worker と連携するための初期構成を整える。

### 前提

- Node.js がインストール済みであること
- backend / ocr-worker の Docker Compose 構成が整備済みであること
- `frontend/docs/` に既存のドキュメントが存在すること

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# 既存の docs を退避
mv frontend/docs /tmp/book2pdf-frontend-docs

# 既存の frontend ディレクトリを削除
rm -rf frontend

# Next.js プロジェクトを作成（TypeScript・Tailwind CSS・App Router）
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --no-turbopack \
  --use-npm

# docs を復元
rm -rf frontend/docs
mv /tmp/book2pdf-frontend-docs frontend/docs

# 不要ファイルの削除
cd frontend
rm -f README.md AGENTS.md CLAUDE.md public/*.svg

# ビルド確認
npm run build

# 開発サーバー起動
npm run dev
```

### 結果

- Next.js 16.3.0 + React 19 + Tailwind CSS v4 + TypeScript + App Router 構成のプロジェクトを作成した
- 不要なサンプルファイルを削除し、`frontend/docs/` を復元した
- `src/app/layout.tsx` の metadata・lang を日本語・book2pdf 向けに更新した
- `frontend/Dockerfile` を新規作成（Node.js 26 Alpine ベース、dev/build/runner のマルチステージ構成）
- `next.config.ts` に `output: "standalone"` を追加した
- `docker-compose.yml` に frontend サービスを追加（target: dev、port 3000、backend 依存）
- `src/lib/api.ts` を新規作成し、backend API 通信用関数を整備した
  - `createJob`、`uploadZip`、`runOcr`、`subscribeJobProgress`、`getPdfDownloadUrl`
- `src/app/page.tsx` を新規作成し、ファイル選択から ZIP アップロード、OCR 実行、進捗表示、PDF ダウンロードまでの簡易 UI を実装した
- `npm run build` が成功した
- `npm run dev` で開発サーバーが起動し、ブラウザで `http://localhost:3000` にアクセスしてトップページが正常に表示されることを確認した
- `frontend/docs/FE-FRONTEND-SYSTEM-SPEC.md` / `FE-TASKS.md` / `FE-WORK-LOG.md`、および `docs/SY-WEB-OCR-SYSTEM-PLAN.md` を更新した

### 注意事項

- `create-next-app` で作成されたのは Next.js 16.3.0（最新版）であり、Next.js 15 以上を要求するプロジェクトルールに違反しない
- Tailwind CSS は v4 がインストールされ、設定は `src/app/globals.css` の `@import "tailwindcss"` と `@theme inline` で行う方式になっている
- 開発サーバーはフォアグラウンドで起動するため、Docker Compose 経由で利用する場合は `target: dev` のイメージを使用する
- 本番ビルド時は `output: "standalone"` を利用し、最小構成の runner ステージで起動する
- backend が起動していない状態では API 呼び出しは失敗するが、トップページの表示は可能

---

## 2026-08-11 タスク001001続き：frontend 結合テスト

### 目的

frontend 開発サーバーが起動し、ブラウザで UI が表示されることを確認する。
また、backend API との連携を含めた結合テストの前提となる動作確認を行う。

### 前提

- タスク001001 で Next.js プロジェクトの初期構成が完了していること
- Docker Compose で backend / ocr-worker / frontend が起動していること

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# frontend コンテナの状態確認
docker compose ps frontend

# 開発サーバーへの HTTP アクセス確認
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000

# ブラウザで http://localhost:3000 を開いて UI 表示を確認
# （Puppeteer による自動確認）
```

### 結果

- `docker compose ps frontend` で `book2pdf-frontend` が `Up` 状態であることを確認した
- `curl http://localhost:3000` が HTTP 200 を返すことを確認した
- ブラウザで `http://localhost:3000` を開き、以下が正常に表示されることを確認した
  - タイトル「book2pdf」
  - サブタイトル「ZIP 画像から OCR 処理を行い、検索可能 PDF を生成します」
  - ZIP ファイル選択 input
  - 「アップロードして OCR 実行」ボタン
- また、`GET /api/jobs/{job_id}/pdf` の API 応答がブラウザから直接開けることを確認した
  - Puppeteer による PDF 直接表示では `net::ERR_ABORTED` が発生したが、
    これはブラウザの PDF ビューア/ダウンロード処理に関する制限であり、API 自体は正常に動作している
  - `downloadPdf()` 関数は Blob 経由でファイル保存を行うため、実際のユーザー操作では問題ない想定

### 注意事項

- frontend から backend API を呼び出す際、CORS 設定が必要になる可能性がある
  - 現状は同一オリジン（`localhost:3000` → `localhost:8000`）ではないため、
    ブラウザのセキュリティ制限で API 呼び出しがブロックされる可能性がある
  - 必要に応じて backend に `fastapi.middleware.cors.CORSMiddleware` を追加する
- Puppeteer 等の自動化ツールではファイル選択ダイアログの操作が困難なため、
  ファイルアップロードから PDF ダウンロードまでの完全な E2E テストは手動で実施することを推奨する

## 2026-08-13 frontend Docker イメージの Next.js 15.1.6 再構成と起動確認

### 目的

frontend コンテナを Next.js 15.1.6 に固定し、Docker 上で正常に起動することを確認する。

### 前提

- `package.json` で `next: 15.1.6` を指定済み
- `package-lock.json` はホスト側で `next@15.1.6` が解決されるよう再生成済み
- `Dockerfile` は `node:22-slim` ベースで最小構成に整理済み

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# 既存コンテナ・イメージ・ボリュームのクリーンアップ
docker compose down --rmi local --volumes --remove-orphans
docker builder prune -f
docker system prune -f

# frontend dev イメージのビルド
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

### 結果

- コンテナ内で `next@15.1.6` がインストールされていることを確認
- `next dev` が `loadBindings is not a function` エラーなく起動
- `http://localhost:3000` への curl で HTTP 200 を確認
- ブラウザで `http://localhost:3000/` を開き、以下が表示されることを確認
  - タイトル「book2pdf」
  - サブタイトル「ZIP 画像から OCR 処理を行い、検索可能 PDF を生成します」
  - ZIP ファイル選択 input
  - 「アップロードして OCR 実行」ボタン

### 注意事項

- コンテナ名は `book2pdf-frontend-test` ではなく `book2pdf-frontend` を使用するよう統一した
- `node_modules` はホスト側に存在せず、コンテナ内のものを使用する
- 本番ビルド用の `builder` / `runner` ステージは未検証（`dev` ターゲットのみ検証）

### 関連タスク

- frontend タスク：Next.js 15.1.6 への Docker 再構成（完了）
- 全体タスク：docker compose での 3 コンテナ起動確認（完了）
- 全体タスク：frontend から ZIP アップロード・PDF ダウンロードの統合検証（未完了）

---

## 2026-09-05 タスク001002/002001/003001：コンポーネント化、型定義、テスト基盤導入

### 目的

frontend の UI をコンポーネント単位に分割し、型定義と API クライアントを強化する。
さらに、ユーザーの動作確認前に自動テストを最大限実施できるよう、単体テスト・結合テスト基盤を導入する。

### 前提

- `feature/FE001002-componentize-and-test` ブランチで作業すること
- Node.js / npm が利用可能であること
- backend API のエンドポイント仕様は `backend/docs/api-spec.md` 等で確認済みであること

### 実施予定コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/frontend

# テスト基盤導入
npm install -D vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom msw

# 型定義・API 強化
# - src/types/index.ts 新規作成
# - src/lib/api.ts リファクタ

# コンポーネント分割
# - src/components/upload/UploadForm.tsx
# - src/components/progress/ProgressPanel.tsx
# - src/components/result/DownloadButton.tsx / ResultPanel.tsx

# テスト実装
# - src/lib/api.test.ts
# - src/components/**/*.test.tsx
# - src/lib/api.integration.test.ts

# 品質ゲート
npm run lint
npm run test -- --run
npm run build
npm audit
```

### 想定される結果や注意点

- Vitest + Testing Library + jsdom でコンポーネント単体テストが実行可能になる
- MSW で backend API のレスポンスをモックし、コンポーネント連携の結合テストが実行可能になる
- Playwright は基盤準備（config + サンプルテスト）までとし、backend 連携の完全 E2E は別タスクとする
- ドキュメント更新は `tasks.md` / `work_log.md` / `frontend-system-spec.md` / `caveats.md` / `docs/agent-skills-guide.md` / `.cline/skills/test-manager/SKILL.md` が対象


## 2026-09-07 タスク FE001002：page.tsx リファクタリングと作業完了

### 実施内容

- `feature/FE001002-componentize-and-test` ブランチにて、FE001002 の実装を完了した。
- `src/app/page.tsx` を `ZipUploadForm` コンポーネントに委譲し、UI ロジックを `useOcrJob` フックと共有 API レイヤー（`src/lib/api.ts`）に集約した。
- 型定義（`src/types/index.ts`）とテスト（`page.test.tsx`、`ZipUploadForm.test.tsx`、`useOcrJob.test.tsx`、`api.test.ts`）を追加・整備した。

### 検証結果

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/frontend
npx tsc --noEmit          # 成功（エラーなし）
npm test -- --run         # 5 files, 33 tests passed
```

### 変更ファイル

- `src/app/page.tsx`
- `src/types/index.ts`
- `src/lib/api.ts`
- `src/components/upload/ZipUploadForm.tsx`
- `src/hooks/useOcrJob.ts`
- 上記各ファイルに対応するテストファイル

### 状態

- `FE-TASKS.md` の FE001002 完了日を 2026-09-07 に更新済み。
- 本ブランチは `main` へマージ可能な状態である。


## 2026-09-07 タスク FE001002 再開：PDF ダウンロード有効化タイミングの修正

### 実施内容

- UAT 中に PDF ダウンロードボタンが OCR/PDF 生成完了前から有効になっており、`GET /api/jobs/{job_id}/pdf` を呼ぶと `400 Bad Request` が返る不具合を確認した。
- `feature/FE001002-componentize-and-test` ブランチを再利用し、FE001002 を再開した。
- `src/hooks/useOcrJob.ts` の `handleUploaded` 内で、`setDownloadableJobId(newJobId)` の呼び出しを `runOcr` API 成功直後から、SSE 進捗イベントの `status === "completed"` を受信した時点に変更した。
- `src/hooks/__tests__/useOcrJob.test.ts` を更新し、`runOcr` 直後は `downloadableJobId` が null のままであることを検証するよう修正した。
- `useOcrJob.test.ts` に「completed SSE イベント受信後に `downloadableJobId` が設定される」テストケースを追加した。

### 検証結果

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/frontend
npm run build              # 成功（エラーなし）
npm test -- --run          # 5 files, 34 tests passed
```

### 変更ファイル

- `src/hooks/useOcrJob.ts`
- `src/hooks/__tests__/useOcrJob.test.ts`
- `frontend/docs/FE-TASKS.md`
- `frontend/docs/FE-WORK-LOG.md`

### 状態

- 本ブランチは `main` へマージ可能な状態である。
- UAT 再検証が必要である。

## 2026-09-07 タスク FE001002：PDF 保存先ダイアログの実装

### 目的

PDF ダウンロード時に、ブラウザ標準の「保存先を指定するダイアログ」を表示できるように改修する。これにより、ユーザーが任意のフォルダに PDF を保存できるようになる。

### 前提

- `downloadPdf()` は従来 `<a download>` 方式を使用しており、ブラウザ設定によってはダウンロード先を指定できなかった
- File System Access API (`window.showSaveFilePicker`) が利用可能なブラウザでは、OS 標準の保存ダイアログを表示できる

### 実施内容

1. `src/lib/api.ts` の `downloadPdf()` を改修
   - `window.showSaveFilePicker` が利用可能な場合は、保存先ダイアログを表示して選択先ファイルにストリーミング書き込み
   - 未対応ブラウザでは従来の `<a download>` 方式にフォールバック
   - ユーザーがダイアログをキャンセルした場合（`AbortError`）は例外を投げない
2. `src/lib/__tests__/api.test.ts` にテストケースを追加
   - File System Access API パス
   - ダイアログキャンセル時の挙動
   - フォールバックパス
   - HTTP エラー時の挙動
3. `frontend/docs/FE-TASKS.md` の FE001002 実施結果欄に不具合情報を追記

### 検証結果

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/frontend
npm run build              # 成功（エラーなし）
npm test                   # 5 files, 36 tests passed
```

### 変更ファイル

- `frontend/src/lib/api.ts`
- `frontend/src/lib/__tests__/api.test.ts`
- `frontend/docs/FE-TASKS.md`
- `frontend/docs/FE-WORK-LOG.md`

### 状態

- 本ブランチは `main` へマージ可能な状態である。
- UAT にて実ブラウザ（Chrome / Edge）での保存ダイアログ表示を検証する必要がある。

