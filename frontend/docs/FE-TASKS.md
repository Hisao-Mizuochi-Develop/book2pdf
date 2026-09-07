# タスク管理

本ファイルは、frontend のタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する
- タスク No は「モジュール識別子（2文字）＋ ユースケースNo（3桁）＋ 通番（3桁）」とする
  - 識別子 `FE` は frontend、`SY` は System/全体設計・仕様等を表す
  - 例：ユースケース001の1番目のタスク → `FE001001`
  - 例：ユースケース002の1番目のタスク → `FE002001`
- 通番は各ユースケース内で 001 から連番で振る

---

## ユースケースNo | 001

ユースケース
ZIP アーカイブをアップロードして OCR ジョブを開始する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| FE001001 | Next.js プロジェクトの初期構成 | 2026-08-11 | 2026-08-11 | 設計 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | Next.js 15 App Router プロジェクトを作成する |  |  |  |
|  | - `npx create-next-app@latest frontend` を実行し、TypeScript・Tailwind CSS・App Router 構成を選択する |  |  |  |
|  | - 作成後、不要なサンプルファイル（`public/` 内の不要物、`src/app/page.tsx` の初期表示内容など）を整理する |  |  |  |
|  | Tailwind CSS を設定する |  |  |  |
|  | - `create-next-app` のオプションで Tailwind CSS を有効化する |  |  |  |
|  | - 必要に応じて `tailwind.config.ts` を確認・調整する |  |  |  |
|  | frontend/Dockerfile を作成する |  |  |  |
|  | - Node.js 公式イメージ（LTS）をベースに、開発用 Dockerfile を作成する |  |  |  |
|  | - 本番用のビルドステージも検討し、最小構成を目指す |  |  |  |
|  | docker-compose.yml に frontend サービスを追加する |  |  |  |
|  | - ポート 3000 をホストにマップする |  |  |  |
|  | - backend サービスへの依存とネットワーク共有を設定する |  |  |  |
|  | API 通信用雛形を作成する |  |  |  |
|  | - `frontend/src/lib/api.ts` を新規作成し、FastAPI エンドポイントを呼び出す関数を整備する |  |  |  |
|  | - 対象エンドポイント: `POST /api/jobs`、`POST /api/jobs/{job_id}/upload`、`POST /api/jobs/{job_id}/ocr`、`GET /api/jobs/{job_id}/events`（SSE）、`GET /api/jobs/{job_id}/pdf` |  |  |  |
|  | トップページの簡易実装を行う |  |  |  |
|  | - `frontend/src/app/page.tsx` にファイル選択 input、ジョブ作成・ZIP アップロード・OCR 実行ボタン、進捗表示エリア、PDF ダウンロードリンクを配置する |  |  |  |
|  | ドキュメントを更新する |  |  |  |
|  | - `frontend/docs/FE-FRONTEND-SYSTEM-SPEC.md` の「フォルダ・ファイル構成」を実態に合わせて更新する |  |  |  |
|  | - `frontend/docs/FE-TASKS.md` に本計画と実施結果を追記する |  |  |  |
|  | - `frontend/docs/FE-WORK-LOG.md` に実行コマンドと結果を記録する |  |  |  |
|  | - `docs/SY-WEB-OCR-SYSTEM-PLAN.md` の frontend 構成も更新する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: `npx create-next-app@latest` で Next.js 16.3.0 + React 19 + Tailwind CSS v4 + TypeScript + App Router 構成のプロジェクトを作成した |  |  |  |
|  | 2026-08-11: 不要なサンプルファイル（README.md, AGENTS.md, CLAUDE.md, public/*.svg）を削除した |  |  |  |
|  | 2026-08-11: `src/app/layout.tsx` の metadata・lang を日本語・book2pdf 向けに更新した |  |  |  |
|  | 2026-08-11: `frontend/Dockerfile` を新規作成（Node.js 26 Alpine ベース、dev/build/runner マルチステージ） |  |  |  |
|  | 2026-08-11: `next.config.ts` に `output: "standalone"` を追加した |  |  |  |
|  | 2026-08-11: `docker-compose.yml` に frontend サービスを追加（target: dev、port 3000、backend 依存） |  |  |  |
|  | 2026-08-11: `src/lib/api.ts` を新規作成し、backend API 通信用関数（createJob, uploadZip, runOcr, subscribeJobProgress, getPdfDownloadUrl）を整備した |  |  |  |
|  | 2026-08-11: `src/app/page.tsx` を新規作成し、ファイル選択から ZIP アップロード、OCR 実行、進捗表示、PDF ダウンロードまでの簡易 UI を実装した |  |  |  |
|  | 2026-08-11: `npm run build` が成功し、`npm run dev` で開発サーバーが起動することを確認した |  |  |  |
|  | 2026-08-11: ブラウザで `http://localhost:3000` にアクセスし、トップページが正常に表示されることを確認した |  |  |  |
|  | 2026-08-11: `frontend/docs/FE-FRONTEND-SYSTEM-SPEC.md` / `FE-TASKS.md` / `FE-WORK-LOG.md`、および `docs/SY-WEB-OCR-SYSTEM-PLAN.md` を更新した |  |  |  |
|  | 2026-08-11: Docker Compose 上の frontend コンテナが `Up` 状態であり、`curl http://localhost:3000` が HTTP 200 を返すことを確認した |  |  |  |
|  | 2026-08-11: Puppeteer による自動確認で、`http://localhost:3000` のトップページにタイトル・サブタイトル・ZIP ファイル選択 input・「アップロードして OCR 実行」ボタンが表示されることを確認した |  |  |  |
|  | 2026-08-11: `GET /api/jobs/{job_id}/pdf` の API 応答がブラウザから直接開けることを確認（Puppeteer の PDF 直接表示はブラウザ制限で `net::ERR_ABORTED` となるが、API 自体は正常動作） |  |  |  |
|  | 2026-08-11: frontend から backend API を呼び出す際の CORS 設定が今後必要になる可能性があることを `frontend/docs/FE-WORK-LOG.md` / `backend/docs/BE-CAVEATS.md` に記録 |  |  |  |
| FE001002 | ZIP アップロード UI の実装 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | backend の POST /api/jobs からジョブ ID を取得する処理を実装する |  |  |  |
|  | 取得したジョブ ID を使って POST /api/jobs/{job_id}/upload に ZIP をアップロードする処理を実装する |  |  |  |
|  | ファイル選択 input、ジョブ ID 表示、アップロード状態表示の UI を作成する |  |  |  |
|  | アップロード後、backend から返却される画像ファイル一覧を表示する |  |  |  |
|  | 2026-09-05 追記：本タスクにコンポーネント化・型定義・テスト基盤導入を含めて実施する |  |  |  |
|  | 2026-09-05 追記：共通型定義を `frontend/src/types/index.ts` に整備する |  |  |  |
|  | 2026-09-05 追記：API クライアントを `frontend/src/lib/api.ts` に集約・型付けし、エラーハンドリングを強化する |  |  |  |
|  | 2026-09-05 追記：`UploadForm` コンポーネントを作成し、ファイル選択・ジョブ作成・ZIP アップロード処理を責務分離する |  |  |  |
|  | 2026-09-05 追記：`ImageList` コンポーネントを作成し、アップロード後の画像ファイル一覧表示を分離する |  |  |  |
|  | 2026-09-05 追記：Vitest + @testing-library/react + jsdom のテスト基盤を導入する |  |  |  |
|  | 2026-09-05 追記：`api.test.ts` / `UploadForm.test.tsx` / `ImageList.test.tsx` の単体テストを実装する |  |  |  |
|  | 2026-09-05 追記：MSW（Mock Service Worker）を使用した API 結合テストを実装する |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-07: `frontend/src/types/index.ts` を新規作成し、Job / UploadResponse / ImageFile / ProgressEvent / OcrResult 等の共通型定義を整備した |  |  |  |
|  | 2026-09-07: `frontend/src/lib/api.ts` をリファクタリングし、各 API エンドポイント呼び出しを型付け・エラーハンドリング強化した。MSW ハンドラも同ファイル内に集約した |  |  |  |
|  | 2026-09-07: `frontend/src/components/upload/ZipUploadForm.tsx` を新規作成し、ファイル選択・ジョブ作成・ZIP アップロード処理を `page.tsx` から分離した |  |  |  |
|  | 2026-09-07: `frontend/src/components/upload/ImageList.tsx` を新規作成し、アップロード後の画像ファイル一覧表示を分離した |  |  |  |
|  | 2026-09-07: `frontend/src/hooks/useOcrJob.ts` を新規作成し、ジョブ作成・アップロード・進捗監視・PDF 取得のロジックを集約した |  |  |  |
|  | 2026-09-07: Vitest + @testing-library/react + jsdom のテスト基盤を導入し、`vitest.config.ts` を設定した |  |  |  |
|  | 2026-09-07: `frontend/src/lib/__tests__/api.test.ts`（14 tests）を実装した |  |  |  |
|  | 2026-09-07: `frontend/src/components/upload/__tests__/ZipUploadForm.test.tsx`（6 tests）を実装した |  |  |  |
|  | 2026-09-07: `frontend/src/components/upload/__tests__/ImageList.test.tsx`（2 tests）を実装した |  |  |  |
|  | 2026-09-07: `frontend/src/hooks/__tests__/useOcrJob.test.ts`（7 tests）を実装した |  |  |  |
|  | 2026-09-07: `frontend/src/app/__tests__/page.test.tsx`（4 tests）を実装した |  |  |  |
|  | 2026-09-07: `npm run test` で 33 tests / 5 test files 全件 PASS を確認した |  |  |  |
|  | 2026-09-07: `npm run build` がエラーなしで完了することを確認した |  |  |  |
|  | 2026-09-07: `page.tsx` をリファクタリングし、ZipUploadForm / ImageList / useOcrJob へ処理を委譲した |  |  |  |
|  | 2026-09-07: UAT 中に PDF ダウンロードボタンが OCR/PDF 生成完了前から有効になっていた不具合を確認し、FE001002 を再開 |
|  | 2026-09-07: `src/hooks/useOcrJob.ts` で `downloadableJobId` の設定を `runOcr` 直後から SSE `status === "completed"` 受信時に変更 |
|  | 2026-09-07: `src/hooks/__tests__/useOcrJob.test.ts` を更新し、completed イベント受信後に `downloadableJobId` が設定されるケースを追加 |
|  | 2026-09-07: `npm run build` が成功し、`npm run test` で 34 tests 全件 PASS を確認した |
|  | 2026-09-07: 【不具合】PDF ダウンロードボタン押下時にブラウザの「保存先を指定するダイアログ」が表示されない |
|  | 2026-09-07: 不具合原因: `downloadPdf()` が `<a download>` 方式で強制ダウンロードしており、ブラウザ設定に依存するため、デフォルトフォルダに黙って保存される |
|  | 2026-09-07: 不具合影響: ユーザーが任意の保存先を選択できず、ダウンロードされたファイルが見つからないと誤認する可能性がある |

---

## ユースケースNo | 002

ユースケース
OCR 処理の進捗をリアルタイムで確認する

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| FE002001 | 進捗表示 UI の実装 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | backend から SSE またはポーリングで進捗を受信する |  |  |  |
|  | 進捗状況をプログレスバーなどで表示する |  |  |  |
|  | 2026-09-05 追記：`ProgressPanel` コンポーネントを作成し、進捗受信と表示を責務分離する |  |  |  |
|  | 2026-09-05 追記：`ProgressPanel.test.tsx` の単体テストを実装する |  |  |  |
|  | 2026-09-05 追記：MSW を使用した進捗通知フローの結合テストを実装する |  |  |  |

---

## ユースケースNo | 003

ユースケース
OCR 完了後に検索可能 PDF をダウンロードする

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| FE003001 | PDF ダウンロード UI の実装 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | OCR 完了後にダウンロードボタンを表示する |  |  |  |
|  | backend から生成された PDF をダウンロードする |  |  |  |
|  | 2026-09-05 追記：`DownloadButton` / `ResultPanel` コンポーネントを作成し、PDF ダウンロード処理を責務分離する |  |  |  |
|  | 2026-09-05 追記：`DownloadButton.test.tsx` / `ResultPanel.test.tsx` の単体テストを実装する |  |  |  |
|  | 2026-09-05 追記：MSW を使用した PDF ダウンロードフローの結合テストを実装する |  |  |  |

---

## ユースケースNo | 004

ユースケース
プロキシ環境でも進捗通知を受け取る

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| FE004001 | 進捗通知方式の切り替え UI の実装 | 2026-08-11 |  | 機能実装 |
|  | タスク詳細 |  |  |  |
|  | SSE とポーリングを切り替えられる設定 UI を作成する |  |  |  |
