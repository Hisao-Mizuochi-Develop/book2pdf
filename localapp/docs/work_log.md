# localapp 作業ログ

## 006004 — アプリ名・サイドバー項目変更

### 【実施予定】

- 日時: 2026-08-16
- 目的: アプリ名とサイドバーの表示順・ラベルを変更する
- 前提: 006001 が完了していること
- 変更内容:
  1. アプリ名 `book2pdf` → `BoockCapture`
     - `tauri.conf.json`: productName, windows.title
     - `Sidebar.tsx`: ロゴテキスト
  2. サイドバー表示順・ラベル変更
     - 1: `電子書籍`（capture）
     - 2: `PDF`（pdf）
     - 3: `トリミング`（trim）
     - 4: `ZIP作成`（export）
- 実施コマンド:
  1. `npm run build`（ビルド確認）
  2. `npm run tauri dev`（表示確認）

### 【実施実績】

- `localapp/src-tauri/tauri.conf.json` を修正
  - `productName` を `book2pdf` → `BoockCapture` → `Book Capture` に変更
  - `windows.title` を `book2pdf` → `BoockCapture` → `Book Capture` に変更
- `localapp/src/components/layout/Sidebar.tsx` を修正
  - ロゴテキストを `book2pdf` → `Book Capture` に変更
  - navItems のラベルを変更
    - `キャプチャ` → `電子書籍`
    - `PDF読込` → `PDF`
    - `ZIP出力` → `ZIP作成`
  - navItems の並び順を変更
    - 変更前: キャプチャ → トリミング → PDF読込 → ZIP出力
    - 変更後: 電子書籍 → PDF → トリミング → ZIP作成
- `npm run build` でビルド成功
- `npm run tauri dev` で起動確認
  - ウィンドウタイトルが「Book Capture」に変更されていることを確認
  - サイドバーのロゴが「Book Capture」に変更されていることを確認
  - サイドバー項目が「電子書籍 / PDF / トリミング / ZIP作成」の順で正しく表示されることを確認

## 006001 — デザインシステム定義

### 【実施予定】

- 日時: 2026-08-16
- 目的: Apple HIG 風のカラーパレット・タイポグラフィ・コンポーネントスタイルを定義し文書化する
- 前提: 006002（サイドバー＋メインレイアウト実装）が完了していること
- 実施コマンド:
  1. `npm run build`（ビルド確認）
  2. `npm run tauri dev`（スタイル反映確認）
- 変更対象:
  - `localapp/src/index.css` — CSS 変数（カラー・角丸）の調整
  - `localapp/src/components/ui/button.tsx` — バリアント・サイズのコメント追加
  - `localapp/docs/localapp-spec.md` — カラーパレット表、タイポグラフィ情報の更新
- 想定される結果や注意点:
  - Tailwind v4 の oklch カラースケールを Apple HIG に近づける
  - 各 CSS 変数に「用途 + 理由」のコメントを付加（初学者向け可読性）
  - shadcn/ui Button コンポーネントの各バリアントに詳細な JSDoc コメント

### 【実施実績】

- `localapp/src/index.css` — Apple HIG 風カラーパレットに変更
  - `--primary` を oklch(0.588 0.194 257.1)（#007AFF 相当）に変更
  - `--foreground` を oklch(0.225 0 0)（#1D1D1F 相当）に変更
  - `--muted-foreground` を oklch(0.53 0 0)（#6E6E73 相当）に変更
  - `--border` を oklch(0.853 0 0)（#D2D2D7 相当）に変更
  - `--sidebar` を oklch(0.97 0 0)（#F5F5F7 相当）に変更
  - `--destructive` を oklch(0.63 0.22 30)（#FF3B30 相当）に変更
  - `--radius` を 0.5rem に変更（より控えめな角丸）
  - 各変数に「用途 + Apple HIG 対応色」のコメントを付加
- `localapp/src/components/ui/button.tsx` — 各 variant・size に JSDoc コメントを付加
  - variant（default, outline, secondary, ghost, destructive, link）に用途・見た目コメント
  - size（default, xs, sm, lg, icon, icon-xs, icon-sm, icon-lg）に高さ・適用場面コメント
  - buttonVariants 関数と Button コンポーネントにも概要コメント
- `localapp/docs/localapp-spec.md` — デザイン仕様を更新
  - カラーパレット表に Tailwind CSS 変数名と oklch 値を追記
  - フォントに `Geist Variable` を明記
- `.clinerules` — 第8章に「初学者向け詳細コメント」ルールを加筆
  - 「すべてのソースコードには初学者にも可読性がよくなるように、各変数・関数・クラス・複雑なロジックに『用途+デザイン意図』のコメントを付けることを基本とする」を追記
- `npm run build` でビルド成功（CSS ファイル 24.97 kB）
- `npm run tauri dev` で起動確認
  - 白基調・余白多め・控えめな角丸の Apple HIG 風レイアウトが正しく表示されることを確認

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


