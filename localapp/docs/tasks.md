# localapp タスク管理表

本ファイルは、localapp のタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する

---

## ユースケース 001 — Tauri v2 プロジェクト初期化

電子書籍キャプチャ・トリミング・ZIP 出力アプリの土台となる、Tauri v2 + React + Vite プロジェクトを構築する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 001001 | Tauri v2 + React + Vite プロジェクト scaffold 作成 | 2026-08-15 | 2026-08-15 | 実装 |
| 001002 | Rust 側依存クレートの選定・追加 | 2026-08-15 | 2026-08-15 | 実装 |
| 001003 | frontend 側依存の選定・追加 | 2026-08-15 | 2026-08-15 | 実装 |
| 001004 | 開発・ビルド環境整備（tauri.conf.json / scripts 等） | 2026-08-15 | 2026-08-15 | 実装 |

### 001001 Tauri v2 + React + Vite プロジェクト scaffold 作成

【計画】
- `cargo create-tauri-app` または手動で `localapp/` 配下に Tauri v2 プロジェクトを構築する
- ディレクトリ構成: `src/`（React + Vite）, `src-tauri/`（Rust）
- TypeScript 設定、`index.html`、`main.tsx` の整備
- 初回起動確認

【実施結果】
- `npm create tauri-app@latest . -- --template react-ts --manager npm` で scaffold 展開
- 展開時に既存の `localapp/docs/` が空になったため、3 ファイルを再作成
- `src/` と `src-tauri/` が生成された
- `npm install` 実行済み（vulnerabilities 0）
- `npm run tauri dev` で起動確認済み

### 001002 Rust 側依存クレートの選定・追加

【計画】
- 画像処理: `image`
- ZIP 圧縮: `zip`
- PDF 展開: `pdfium-render` または同等の crate
- 設定・パス: `serde_json`, `dirs`
- エラーハンドリング: `thiserror`
- `Cargo.toml` に追加し、ビルドが通ることを確認

【実施結果】
- `cargo add image zip pdfium-render serde_json dirs thiserror` を実行
- 全クレートが `Cargo.toml` / `Cargo.lock` に追加された
- `npm run tauri dev` のビルドで問題なくコンパイルされた

### 001003 frontend 側依存の選定・追加

【計画】
- Tailwind CSS v4
- shadcn/ui
- lucide-react（アイコン）
- Zustand（状態管理）
- `package.json` に追加し、開発サーバ起動確認

【実施結果】
- `npm install -D tailwindcss @tailwindcss/vite` を実行
- `src/index.css` を新規作成し、`@import "tailwindcss"` で Tailwind v4 有効化
- `vite.config.ts` に `@tailwindcss/vite` プラグインと `@/` path alias を追加
- `tsconfig.json` に `baseUrl` と `@/*` の path alias を追加
- `npx shadcn@latest init` を実行し shadcn/ui 初期化完了
- `npm install zustand lucide-react` を実行
- `src/App.css` を削除し、`src/App.tsx` を最小構成に整理
- `npm run tauri dev` でフロントエンドが正常に表示された

### 001004 開発・ビルド環境整備（tauri.conf.json / scripts 等）

【計画】
- `tauri.conf.json` のウィンドウサイズ・タイトル・権限を調整
- `package.json` scripts（`dev`, `build`, `tauri dev`, `tauri build`）を整備
- Tauri v2 capabilities の設定
- 開発時のホットリロード確認

【実施結果】
- `tauri.conf.json` の `app.windows` を調整
  - title: `book2pdf`
  - size: 1200x800
  - minWidth/minHeight: 900x600
  - center: true
- `package.json` の `scripts` は scaffold 既定のままで問題なし（`dev`, `build`, `preview`, `tauri`）
- 開発時ホットリロードは Vite 既定のままで動作
- `npm run tauri dev` でウィンドウが中央に表示され、タイトルが `book2pdf` となった

---

## ユースケース 002 — 画面キャプチャ

電子書籍リーダー画面を検出し、連続してキャプチャして画像フォルダに保存する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 002001 | 画面キャプチャ方式調査・実装 | 2026-08-15 |  | 調査/実装 |
| 002002 | アプリプロファイル管理 UI | 2026-08-15 |  | 実装 |
| 002003 | 連続キャプチャ実行・進捗表示 | 2026-08-15 |  | 実装 |
| 002004 | キャプチャ画像のフォルダ管理 | 2026-08-15 |  | 実装 |

### 002001 画面キャプチャ方式調査・実装

【計画】
- Tauri screenshot プラグインの調査
- macOS / Windows / Linux 対応のキャプチャ方法を選定
- Rust 側で対象ウィンドウ検出とスクリーンショット取得のコマンドを実装
- 単発キャプチャの動作確認

【実施結果】

### 002002 アプリプロファイル管理 UI

【計画】
- Kindle / BookWalker / カスタム のプロファイル選択 UI
- ページ送り方向（右/左）、待機時間の設定
- ウィンドウタイトルキーワード、プロセス名の編集
- プロファイルの保存/複製/リセット

【実施結果】

### 002003 連続キャプチャ実行・進捗表示

【計画】
- キャプチャ → ページ送り → 画像変化検出 のループ実装
- バックグラウンド実行（Rust 側で非同期）
- 進捗バー、ステータステキスト、ログ表示
- 停止ボタン

【実施結果】

### 002004 キャプチャ画像のフォルダ管理

【計画】
- タイトル名で出力フォルダ作成
- 連番 PNG 保存
- キャプチャ完了後、トリミングタブに自動引き継ぎ

【実施結果】

---

## ユースケース 003 — 画像トリミング

キャプチャまたは PDF 展開した画像から余白を削除する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 003001 | 画像フォルダ読み込み・サムネイル一覧 UI | 2026-08-15 |  | 実装 |
| 003002 | Before/After プレビュー表示 | 2026-08-15 |  | 実装 |
| 003003 | 余白自動検出（Rust バックエンド） | 2026-08-15 |  | 実装 |
| 003004 | 手動余白調整 UI | 2026-08-15 |  | 実装 |
| 003005 | トリミング一括実行・進捗表示 | 2026-08-15 |  | 実装 |

### 003001 画像フォルダ読み込み・サムネイル一覧 UI

【計画】
- 入力フォルダ選択ダイアログ
- 画像ファイル一覧をサムネイルグリッドで表示
- 並び替え（ファイル名順）
- 前工程からの自動入力対応

【実施結果】

### 003002 Before/After プレビュー表示

【計画】
- オリジナル画像とトリミング後画像を左右に並列表示
- ズーム・パン対応
- 現在のファイル名とページ番号表示
- 前へ/次へ ナビゲーション

【実施結果】

### 003003 余白自動検出（Rust バックエンド）

【計画】
- 複数ページをサンプリングして 4 辺の余白を推定
- 最小マージン（最も保守的な値）を採用
- 安全マージン（係数 + 固定 px）を適用
- 推定結果を UI に反映

【実施結果】

### 003004 手動余白調整 UI

【計画】
- 左/右/上/下 の数値入力
- Canvas 上でドラッグして範囲を選択
- プレビューのリアルタイム更新
- 微調整ボタン

【実施結果】

### 003005 トリミング一括実行・進捗表示

【計画】
- 全画像の一括トリミングを Rust 側で実行
- 進捗通知（current/total）
- 出力フォルダ自動生成
- 完了後、ZIP 出力タブに自動引き継ぎ

【実施結果】

---

## ユースケース 004 — ZIP 出力・連携

トリミング済み画像を ZIP アーカイブにまとめる。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 004001 | ZIP アーカイブ化（Rust バックエンド） | 2026-08-15 |  | 実装 |
| 004002 | 出力設定・ファイル名設定 UI | 2026-08-15 |  | 実装 |
| 004003 | タブ間自動連携 | 2026-08-15 |  | 実装 |

### 004001 ZIP アーカイブ化（Rust バックエンド）

【計画】
- `zip` crate を用いて画像フォルダを ZIP 化
- ファイル名順で格納
- 保存ダイアログ連携

【実施結果】

### 004002 出力設定・ファイル名設定 UI

【計画】
- 出力先選択、ファイル名入力
- 保存前に上書き確認
- 前工程からの自動入力対応

【実施結果】

### 004003 タブ間自動連携

【計画】
- キャプチャ完了 → トリミング入力に自動設定
- トリミング完了 → ZIP 出力に自動設定
- 状態管理（Zustand）で連携

【実施結果】

---

## ユースケース 005 — PDF 読込

外部 PDF を画像化して、トリミングタブに引き継ぐ。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 005001 | PDF 選択・設定 UI | 2026-08-15 |  | 実装 |
| 005002 | PDF → 画像展開（Rust バックエンド） | 2026-08-15 |  | 実装 |

### 005001 PDF 選択・設定 UI

【計画】
- PDF ファイル選択ダイアログ
- 出力フォルダ設定（自動設定含む）
- DPI（150/200/300/400）と形式（PNG/JPG）選択
- 設定の保存/リセット

【実施結果】

### 005002 PDF → 画像展開（Rust バックエンド）

【計画】
- `pdfium-render` 等で PDF をページ画像化
- バックグラウンド実行
- 進捗通知
- 完了後、トリミングタブに自動引き継ぎ

【実施結果】

---

## ユースケース 006 — モダン GUI デザイン

クリーン＆ミニマルな Apple HIG 風 UI を実装する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 006001 | デザインシステム定義 | 2026-08-15 | 2026-08-16 | 実装 |
| 006002 | サイドバー＋メインレイアウト実装 | 2026-08-15 | 2026-08-15 | 実装 |
| 006003 | ライトモード対応 + OS 設定連動 | 2026-08-15 | 2026-08-16 | 実装 |
| 006004 | マイクロインタラクション実装 | 2026-08-15 | 2026-08-16 | 実装 |

### 006004 アプリ名・サイドバー変更

【計画】
- アプリ名 `book2pdf` → `Book Capture`
- サイドバー項目変更
  1. `電子書籍`（capture）
  2. `PDF`（pdf）
  3. `トリミング`（trim）
  4. `ZIP作成`（export）

【実施結果】
- `tauri.conf.json`: productName、windows.title を `Book Capture` に変更
- `Sidebar.tsx`: ロゴテキストを `Book Capture` に変更
- `Sidebar.tsx`: navItems のラベルと並び順を変更
  - `キャプチャ` → `電子書籍`
  - `PDF読込` → `PDF`
  - `ZIP出力` → `ZIP作成`
  - 順序: 電子書籍 → PDF → トリミング → ZIP作成
- `npm run build` でビルド成功
- `npm run tauri dev` で起動確認完了


### 006001 デザインシステム定義

【計画】
1. `localapp/src/index.css` の CSS 変数調整
   - `--primary` を `#007AFF` 相当の oklch に変更（暗いモノクロ → Apple HIG 風鮮やかな青）
   - `--foreground` を `#1D1D1F` 相当の oklch に変更（黒 → ソフトブラック）
   - `--muted-foreground` を `#6E6E73` 相当の oklch に変更（中間灰 → セカンダリテキスト色）
   - `--border` を `#D2D2D7` 相当の oklch に変更（ライト灰 → 区切り線色）
   - `--sidebar` を `#F5F5F7` 相当の oklch に変更（白 → サイドバー背景色）
   - `--destructive` を `#FF3B30` 相当の oklch に変更（赤 → エラー/警告色）
   - `--radius` を 0.5rem に変更（0.625rem → より控えめな角丸）
   - 各変数に「用途 + Apple HIG 対応色」の `/* コメント */` を付加
2. `localapp/src/components/ui/button.tsx` のコメント強化
   - 各 variant（default, outline, secondary, ghost, destructive, link）に JSDoc コメント
   - 各 size（default, xs, sm, lg, icon...）に JSDoc コメント
   - `buttonVariants` 関数と `Button` コンポーネントにも概要コメント
3. `localapp/docs/localapp-spec.md` のデザイン仕様更新
   - カラーパレット表に Tailwind CSS 変数名と oklch 値を追記
   - フォントに `Geist Variable` を明記
   - タイポグラフィのサイズ指定を rem で明記
4. ビルド確認・起動確認
   - `npm run build`
   - `npm run tauri dev`

【実施結果】
- `localapp/src/index.css` を Apple HIG 風カラーパレットに変更し、各変数に「用途 + 理由」のコメントを付加
- `localapp/src/components/ui/button.tsx` の各 variant・size に詳細な JSDoc コメントを付加
- `localapp/docs/localapp-spec.md` のカラーパレット表を更新（oklch 値・CSS 変数名を追記）
- `.clinerules` 第8章に「初学者向け詳細コメント」ルールを加筆
- `npm run build` でビルド成功
- `npm run tauri dev` で起動確認完了
  - 白基調・余白多め・控えめな角丸のレイアウトが正しく表示されることを確認

### 006002 サイドバー＋メインレイアウト実装

【計画】
- 左サイドバーに 4 機能のアイコン+ラベル配置
- アクティブ状態の視覚表現
- 右メインエリアの可変レイアウト
- レスポンシブ対応（最低ウィンドウサイズ 960x700 想定）
- Zustand で現在のビュー状態を管理

【実施結果】
- `src/store/navigationStore.ts` を新規作成（`currentView`: capture/trim/pdf/export）
- `src/components/layout/Sidebar.tsx` を新規作成
  - 幅 200px、白背景・薄いボーダー右線
  - 4 機能を lucide-react アイコン＋日本語ラベルで垂直配置
  - アクティブ状態：背景 `#F5F5F7`、左端 3px アクセントライン
- `src/components/layout/MainLayout.tsx` を新規作成（Sidebar + main の 2 カラム）
- `src/views/CaptureView.tsx`, `TrimView.tsx`, `PdfImportView.tsx`, `ExportView.tsx` を新規作成
- `src/App.tsx` を更新し、Zustand の `currentView` に応じて View を切り替え
- `vite.config.ts` の `@/` path alias を `path.resolve(__dirname, "./src")` に修正
- `@types/node` を追加し、`tsconfig.node.json` に `types: ["node"]` を設定
- `npm run build` でビルド成功
- `npm run tauri dev` でサイドバー＋メインエリアのレイアウトを確認

### 006003 ライトモード対応 + OS 設定連動

【計画】
- ライトモードを基本テーマとする
- OS の外観モード変更を検出して自動切り替え（将来のダークモード対応の土台）
- テーマ切り替え用のユーティリティ実装

具体的内容:
1. `localapp/src/index.css` にダークモード用 CSS 変数を追加
   - `@media (prefers-color-scheme: dark)` でダークモード時の色変数を定義
   - ダークモードは Apple HIG 風のダークテーマを想定（控えめな暗色）
2. `localapp/src/main.tsx` に OS 外観モード変更リスナーを実装
   - `window.matchMedia('(prefers-color-scheme: dark)')` を監視
   - 変更時に `document.documentElement.setAttribute('data-theme', ...)` を設定
   - 将来的に手動切り替えを入れる際の土台とする
3. `localapp/docs/localapp-spec.md` にテーマ仕様を追記
   - ライト/ダークモードのカラーパレット表
4. ビルド・起動確認

【実施結果】
- `localapp/src/index.css` の `.dark` ブロックコメントを更新
  - 「将来のダークモード対応の土台」→「OS の外観モード設定に連動して有効化される」に変更
  - `main.tsx` の `initTheme()` との連携を明記
- `localapp/src/main.tsx` に `initTheme()` 関数を追加
  - `window.matchMedia("(prefers-color-scheme: dark)")` で OS 外観モードを取得
  - 初回反映：`applyTheme(darkModeQuery.matches)` でページ読み込み時に即座にテーマ適用
  - 継続監視：`addEventListener("change")` で OS 設定変更をリアルタイムで検出
  - `.dark` クラスを `document.documentElement` に付与/除去してダークモード切り替え
  - React レンダリングより先に実行し、画面ちらつきを防止
  - 各処理に「なぜそのように実装したか」の詳細コメントを付加
- 当初の計画では `data-theme` 属性方式を検討していたが、`@custom-variant dark (&:is(.dark *))` と `.dark` クラスの組み合わせに変更
  - Tailwind CSS v4 のカスタムバリアント構文に最適な方式
  - 理由を追記
- `npm run build` でビルド成功（`tsc && vite build` ともにエラーなし）
- `npm run tauri dev` で起動確認
  - macOS ライトモード時：白基調の UI が正しく表示される
  - macOS ダークモード時：`html.dark` が付与されダークテーマ変数が適用される
  - システム設定を切り替えるとリアルタイムでテーマが追随することを確認

### 006004 マイクロインタラクション実装

【計画】
- ボタンホバー/アクティブ効果
- 画面切り替え時のフェードアニメーション
- トースト通知（成功/エラー/情報）
- プログレス表示アニメーション

【実施結果】

---

## ユースケース 007 — 設定・永続化

アプリ設定、プロファイル、履歴を永続化する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 007001 | アプリ設定ファイル管理 | 2026-08-15 |  | 実装 |
| 007002 | プロファイル・履歴の永続化 | 2026-08-15 |  | 実装 |

### 007001 アプリ設定ファイル管理

【計画】
- `dirs::config_dir()` 配下に `config.json` を保存
- 読み書き用 Rust コマンド実装
- デフォルト値管理
- 設定変更時の UI 反映

【実施結果】

### 007002 プロファイル・履歴の永続化

【計画】
- カスタムプロファイルの保存/読み込み
- 最近使用したフォルダ/ファイル履歴
- 設定 UI からの編集

【実施結果】
