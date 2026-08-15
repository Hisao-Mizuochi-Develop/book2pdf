# localapp 作業ログ

## 001001 — Tauri v2 + React + Vite プロジェクト scaffold 作成

### 【実施予定】

- 日時: 2026-08-15
- 目的: localapp の土台となる Tauri v2 + React + Vite プロジェクトを構築する
- 前提: Node.js, npm, cargo, rust がインストール済みであること
- 実施コマンド:
  1. `cd /Users/hisao/Documents/work4/sakura/book2pdf/localapp`
  2. `npm create tauri-app@latest . -- --template react-ts --manager npm`
  3. `npm install`
  4. `npm run tauri dev`
- 想定される結果や注意点:
  - `src/` と `src-tauri/` が生成される
  - `npm run tauri dev` でデスクトップウィンドウが起動する
  - 既存の `docs/` ディレクトリは保持する（scaffold 展開時に削除されたため再作成済み）

### 【実施実績】

- scaffold 展開時に `localapp/docs/` が空になったため、3 ファイルを再作成
- 再作成ファイル:
  - `localapp/docs/localapp-spec.md`
  - `localapp/docs/tasks.md`
  - `localapp/docs/work_log.md`
- `npm install` を実行し、依存関係を解決（73 packages、vulnerabilities 0）
- Rust 側クレートを追加：`image`, `zip`, `pdfium-render`, `serde_json`, `dirs`, `thiserror`
- Tailwind CSS v4 + `@tailwindcss/vite` を導入、`vite.config.ts` にプラグインと path alias 設定を追加
- `tsconfig.json` に `baseUrl` と `@/*` の path alias を追加
- `src/index.css` を新規作成し Tailwind v4 用ベーススタイルを設定
- shadcn/ui 初期化（`components.json`、`src/components/ui/button.tsx`、`src/lib/utils.ts` 生成）
- フロントエンド依存を追加：`zustand`, `lucide-react`
- `src/App.css` を削除し、`src/App.tsx` を最小構成に整理
- `tauri.conf.json` のウィンドウ設定を調整（title: `book2pdf`, size: 1200x800, min: 900x600, center: true）
- `npm run tauri dev` でビルド成功、デスクトップウィンドウが起動

## 006002 — サイドバー＋メインレイアウト実装

### 【実施予定】

- 日時: 2026-08-15
- 目的: サイドバーナビゲーションとメインレイアウトを実装し、4 機能タブの切り替えを確認する
- 前提: 001001〜001004 の環境構築が完了していること
- 実施コマンド:
  1. `npm run build`（ビルド確認）
  2. `npm run tauri dev`（起動確認）
- 想定される結果や注意点:
  - サイドバーに 4 機能アイコン＋ラベルが垂直配置される
  - アクティブタブが視覚的に示される（背景色 + 左端アクセントライン）
  - メインエリアに各タブのコンテンツが表示される

### 【実施実績】

- `src/store/navigationStore.ts` を新規作成（Zustand store、`currentView`: capture/trim/pdf/export）
- `src/components/layout/Sidebar.tsx` を新規作成
  - 幅 200px、白背景、薄い右ボーダー
  - lucide-react アイコン＋日本語ラベルで 4 機能を垂直配置
  - アクティブ状態：背景 `#F5F5F7`、左端 3px のアクセントライン（`before` 疑似要素）
- `src/components/layout/MainLayout.tsx` を新規作成（Sidebar + main の 2 カラムレイアウト）
- `src/views/CaptureView.tsx`, `TrimView.tsx`, `PdfImportView.tsx`, `ExportView.tsx` を新規作成（各タブのプレースホルダー）
- `src/App.tsx` を更新し、Zustand の `currentView` に応じて View を切り替える実装を追加
- `vite.config.ts` の `@/` path alias を `path.resolve(__dirname, "./src")` に修正
- `@types/node` を追加し、`tsconfig.node.json` に `types: ["node"]` を設定
- `npm run build` でビルド成功
- `npm run tauri dev` で起動確認
  - サイドバーに 4 機能（キャプチャ / トリミング / PDF読込 / ZIP出力）が正しく表示される
  - 各タブをクリックするとメインエリアのコンテンツが切り替わる
  - アクティブタブの視覚的表示（背景色 + 左端アクセントライン）が正しく動作


