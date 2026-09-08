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


## 2026-09-07 タスク FE001002：PDF 保存先ダイアログの改修（やり直し）

### 目的

`downloadPdf()` 内で `window.showSaveFilePicker` がユーザージェスチャ（クリック）文脈の失効後に呼ばれていたため、ブラウザの保存ダイアログが表示されない不具合を修正する。

### 原因

File System Access API の `showSaveFilePicker` はユーザージェスチャ（ボタンクリック）の文脈内で同期的に呼ぶ必要がある。`fetch` 後に呼ぶとセキュリティコンテキストが失効し、ダイアログが抑制される。

### 実施内容

1. `src/lib/api.ts` の `downloadPdf()` を改修
   - `window.showSaveFilePicker` を `fetch` より先に呼び出し、ファイルハンドルを取得
   - ハンドル取得後に `fetchWithTimeout` で PDF を取得し、`createWritable` → `pipeTo` → `close` で保存
   - フォールバック処理は維持（`showSaveFilePicker` 非対応ブラウザでは `<a download>` 方式）
2. `src/lib/__tests__/api.test.ts` を更新
   - `showSaveFilePicker` が `fetch` より先に呼ばれることを検証するアサーションを追加
   - ダイアログキャンセル時は `fetch` が呼ばれないことを検証
   - File System Access API パスとフォールバックパスの両方で HTTP エラー時の挙動を検証
3. `frontend/docs/FE-TASKS.md` / `FE-WORK-LOG.md` を更新

### 検証結果

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/frontend
npm run build              # 成功（エラーなし）
npm test -- --run          # 5 files, 37 tests passed
```

### 変更ファイル

- `frontend/src/lib/api.ts`
- `frontend/src/lib/__tests__/api.test.ts`
- `frontend/docs/FE-TASKS.md`
- `frontend/docs/FE-WORK-LOG.md`

### 状態

- 本ブランチは `main` へマージ可能な状態である。
- UAT にて実ブラウザ（Chrome / Edge）での保存ダイアログ表示を検証する必要がある。


## 2026-09-08 タスク FE001002：完了・main マージ

### 目的

Phase 4 最終報告書を作成し、ユーザー検収テスト（Gate 3）の承認を取得したうえで、FE001002 を完了させ main ブランチへマージする。

### 実施内容

- Phase 4 最終報告書を作成し、ユーザーに提示
- Gate 3 においてユーザー検収テストの合格承認を取得
- `frontend/docs/FE-TASKS.md` の FE001002 行にタスク完了日付 `2026-09-08` を記入
- `frontend/docs/FE-WORK-LOG.md` に本完了記録を追記
- 未コミット変更を `git add -A && git commit` した
- `main` ブランチへ `git merge --no-ff feature/FE001002-componentize-and-test` を実施
- 完了後、feature ブランチを削除した

### 検証結果

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/frontend
npm run build              # 成功（エラーなし）
npm run test -- --run      # 5 files, 38 tests passed
```

### 変更ファイル

- `frontend/docs/FE-TASKS.md`
- `frontend/docs/FE-WORK-LOG.md`

### 状態

- FE001002 は完了。main ブランチにマージ済み。

## 2026-09-08 タスク FE002001：進捗表示 UI の実装

### 目的

`frontend/src/app/page.tsx` に含まれていた進捗表示部分を `ProgressPanel` コンポーネントに切り出し、単体テストおよび MSW を使用した結合テストを追加する。これにより、進捗表示機能の責務分離と品質担保を行う。

### 前提

- `useOcrJob.ts` で SSE 経由の進捵監視ロジックは既に実装済みであること
- `frontend/src/app/page.tsx` で進捗を表示する UI が既に存在すること
- Vitest + @testing-library/react + jsdom のテスト基盤が導入済みであること

### 実施内容

1. `frontend/src/components/progress/ProgressPanel.tsx` を新規作成
   - `latest`（最新進捗）と `log`（進捗ログ）を受け取る純粋表示コンポーネントとする
   - 進捗パーセンテージのクランプ処理（0〜100）を実装
   - 進捗バー、ステータス、ページ数、メッセージログを表示
2. `frontend/src/components/progress/index.ts` を新規作成
   - `ProgressPanel` を default export する
3. `frontend/src/app/page.tsx` をリファクタリング
   - 進捗表示の JSX を削除
   - `<ProgressPanel latest={latestProgress} log={progressLog} />` として呼び出し
   - ジョブ情報パネルに `data-testid="job-info-panel"` を追加
4. `frontend/src/components/progress/__tests__/ProgressPanel.test.tsx` を新規作成（7 tests）
   - 進捗なし時の表示
   - 進捗表示（プログレスバー・パーセンテージ）
   - ログ表示
   - 100% 超過のクランプ
   - 負値のクランプ
   - total_pages が 0 の場合の安全表示
5. MSW 基盤を新規構築
   - `frontend/src/mocks/handlers.ts`：API モックハンドラ（ジョブ作成、ZIP アップロード、OCR 実行、PDF ダウンロード）
   - `frontend/src/mocks/server.ts`：MSW サーバーインスタンス
   - `frontend/vitest.setup.ts`：MSW サーバーの起動・リセット・停止処理
6. `frontend/src/app/__tests__/page.msw.test.tsx` を新規作成（1 test）
   - EventSource をテスト制御可能なモックに差し替え
   - アップロード → OCR 開始 → SSE 進捗 → ダウンロードボタン表示までの結合フローを検証

### 検証結果

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/frontend
npm run build              # 成功（エラーなし）
npm run test -- --run      # 7 files / 46 tests passed
```

### 変更ファイル

- `frontend/src/components/progress/ProgressPanel.tsx`
- `frontend/src/components/progress/index.ts`
- `frontend/src/components/progress/__tests__/ProgressPanel.test.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/app/__tests__/page.msw.test.tsx`
- `frontend/src/mocks/handlers.ts`
- `frontend/src/mocks/server.ts`
- `frontend/vitest.setup.ts`
- `frontend/docs/FE-TASKS.md`
- `frontend/docs/FE-WORK-LOG.md`

### 状態

- 本ブランチは `main` へマージ可能な状態である。
- ユーザー検収テスト（UAT）は本タスクでは実施しない（単体テスト・結合テストのみ）。
- 【別タスク】FE002001 実装中に `src/lib/api.ts` の `downloadPdf()` における `WritableStream.close()` の重複呼び出し不具合を発見。FE002002 として起票済み。

## 2026-09-08 タスク FE002001：SSE ストリーム終了不具合修正・マージ完了

### 目的

backend の SSE ストリームが `[DONE]` センチネルを送信せず、job 完了時にブラウザ側の `EventSource.onerror` で「進捗接続エラー」が出力されていた不具合を修正し、main ブランチへマージする。

### 実施内容

1. `backend/app/routers/jobs.py`
   - `subscribe_job_events` 内で job 完了（`completed`）または失敗（`failed`）時に `yield "data: [DONE]\n\n"` を送信するよう追加
2. `frontend/src/lib/api.ts`
   - `subscribeJobProgress` に `doneReceived` フラグを追加
   - `[DONE]` センチネル受信後にフラグを立て、`onerror` コールバックをスキップするよう修正
3. `frontend/src/hooks/useOcrJob.ts`
   - 「OCR 処理を開始しました」ログの重複出力を削除
4. `frontend/src/lib/__tests__/api.test.ts`
   - `[DONE]` 受信後の `onerror` 抑制を検証するテストケースを追加
5. ビルド・テスト検証
6. `feature/FE002001-extract-progress-panel` を `main` へ `--no-ff` マージ、feature ブランチを削除

### 検証結果

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/frontend
npm run build              # 成功（エラーなし）
npm run test -- --run      # 7 files / 46 tests passed
```

### 変更ファイル

- `backend/app/routers/jobs.py`
- `frontend/src/lib/api.ts`
- `frontend/src/hooks/useOcrJob.ts`
- `frontend/src/lib/__tests__/api.test.ts`
- `frontend/docs/FE-TASKS.md`
- `frontend/docs/FE-WORK-LOG.md`

### 状態

- FE002001 は完了。main ブランチにマージ済み。

---

## 2026-09-08 FE002002 FE002001 UATバグ対応（起票）

### 目的

- FE002001 の UAT 中に発見された不具合を統合対応する
- SY007010（UAT 派生バグ対応タスク管理ルール）に従い、同じ元タスク由来のバグを 1 つのタスクに集約する

### 統合対象の不具合一覧

1. **downloadPdf() の WritableStream close 重複呼び出し（未修正）**
   - 内容: `pipeTo` の自動 close と `finally` ブロックの手動 close が競合
   - 経緯: FE002001 UAT 中に PDF ダウンロード動作確認時に発見
   - 対応方針: `pipeTo` に `{ preventClose: true }` を指定

2. **backend SSE [DONE] センチネル未送信（FE002001 実施中に修正済み）**
   - 内容・経緯: backend の SSE が `[DONE]` を送信せず、frontend で `onerror` 誤発火。2026-09-08 に backend/frontend 双方を修正

3. **useOcrJob.ts のログ重複出力（FE002001 実施中に修正済み）**
   - 内容・経緯: 「OCR 処理を開始しました」ログが複数回出力されていた。2026-09-08 に削除済み

### 次のアクション

- feature/FE002002-fe002001-uat-bugfix ブランチを作成し、バグ 1 の修正を実施する

---

## 2026-09-08 FE002002 実装（バグ 1 修正）

### 実施内容

- `frontend/src/lib/api.ts` の `streamToWritable` 関数内で `pipeTo(writable)` を `pipeTo(writable, { preventClose: true })` に変更
- これにより `response.body.pipeTo` の完了時に自動 close が抑制され、`finally` ブロックでの `writable.close()` のみが実行されるようになった

### 検証結果

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/frontend
npm run build              # 成功（エラーなし）
npm run test -- --run      # 7 files / 47 tests passed
```

### 変更ファイル

- `frontend/src/lib/api.ts`

### 状態

- バグ 1 の修正完了。バグ 2・3 は FE002001 実施中に既に修正済み。

