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
| 002001 | 画面キャプチャ方式調査・実装 | 2026-08-15 | 2026-08-16 | 調査/実装 |
| 002002 | アプリプロファイル管理 UI | 2026-08-15 | 2026-08-16 | 実装 |
| 002003 | 連続キャプチャ実行・進捗表示 | 2026-08-15 | 2026-08-16 | 実装 |
| 002004 | キャプチャ画像のフォルダ管理 | 2026-08-15 | 2026-08-16 | 実装 |

### 002001 画面キャプチャ方式調査・実装

【計画】
1. Tauri v2 標準API・プラグイン調査
   - `tauri-plugin-screenshot` の有無確認
   - なければ Rust crate 方式を採用
2. 候補 crate の調査・選定
   - `screenshots` crate: macOS / Windows / Linux 対応、画面・領域指定キャプチャ可能
   - `xcap` crate: クロスプラットフォーム、ウィンドウ指定キャプチャ対応
   - 比較要件: ウィンドウ指定キャプチャ、連続キャプチャ性能、ビルド安定性
3. 実装（変更対象ファイル）
   - `localapp/src-tauri/Cargo.toml`
     - `screenshots` crate を追加
   - `localapp/src-tauri/src/commands/capture.rs`（新規作成）
     - 単発スクリーンショット取得コマンド `capture_screen` を実装
     - 全画面キャプチャ（`screenshots::Screen::all()` → `capture()`）
     - PNG 形式でバイト列を返却（`image::DynamicImage` → `write_to`）
     - Base64 エンコードしてフロントエンドに返却
   - `localapp/src-tauri/src/commands/mod.rs`（新規作成）
     - `pub mod capture;`
   - `localapp/src-tauri/src/lib.rs`
     - `mod commands;` を追加
     - `commands::capture::capture_screen` を `invoke_handler` に登録
   - `localapp/src-tauri/capabilities/default.json`
     - `screenshots` crate はTauri標準権限外のネイティブ処理なので変更なし
   - `localapp/src/views/CaptureView.tsx`
     - 「キャプチャテスト」ボタンを追加
     - `invoke("capture_screen")` で取得し `<img>` に表示
4. フロントエンド側にテスト用 UI を実装
   - `CaptureView.tsx` に「キャプチャテスト」ボタンを追加
   - 取得した画像を一時表示して動作確認
5. ビルド・動作確認
   - `cargo check` で Rust 側コンパイル確認
   - `npm run tauri dev` で単発キャプチャ動作確認
   - 取得した画像が指定フォルダに保存されることを確認

【実施結果】
- `screenshots` crate v0.8.10 を `Cargo.toml` に追加
- `base64` crate v0.23.1 を追加（Base64エンコード用）
- `src-tauri/src/commands/capture.rs` を新規作成
  - `capture_screen` コマンド: 全画面キャプチャ → PNGエンコード → Base64返却
  - `screenshots::Screen::all()` → `capture()` → `image::PngEncoder` でPNG化
  - `image::ImageEncoder` トレイトをインポートして `write_image()` を使用
  - Base64 エンコードしてフロントエンドに返却
- `src-tauri/src/commands/mod.rs` を新規作成（`pub mod capture;`）
- `src-tauri/src/lib.rs` を更新
  - `mod commands;` を追加
  - `greet` コマンドを削除し、新規コマンドとして `commands::capture::capture_screen` を登録
- `src/views/CaptureView.tsx` を更新
  - 「キャプチャテスト」ボタン追加（shadcn/ui Button + lucide-react Cameraアイコン）
  - `invoke<CaptureResult>("capture_screen")` でRustコマンドを呼び出し
  - 結果を `data:image/png;base64,...` 形式で `<img>` に表示
  - エラーハンドリング、ローディング状態を実装
- `cargo check`: コンパイル成功
- `npm run build`: ビルド成功（`tsc && vite build` ともにエラーなし）
- `npm run tauri dev`: 起動成功
  - フロントエンド表示確認: サイドバー「電子書籍」選択時に「キャプチャテスト」ボタンが正しく表示される
  - 注意: `invoke` API は Tauri WebView 内でのみ動作するため、ブラウザ直接アクセスでのキャプチャ実行は不可（想定内の制限）
- `src-tauri/tauri.conf.json` / `capabilities/default.json` は変更なし
  - `screenshots` crate は Tauri 標準権限外のネイティブ処理のため

### 002002 アプリプロファイル管理 UI

【計画】
- 002001 で追加した `CaptureView.tsx` にプロファイル選択セレクタを追加
- Rust側に `CaptureProfile` struct（参考: `capture_profiles.py`）を定義し、`get_builtin_profiles` コマンドを実装
- Zustandストアで選択状態を管理
- Kindle / BookWalker / カスタム のプロファイル選択 UI
- ページ送り方向（右/左）、待機時間の設定
- ウィンドウタイトルキーワード、プロセス名の編集
- プロファイルの保存/複製/リセット

【実施結果】
- Rust 側（詳細コメント付きで実装）
  - `localapp/src-tauri/src/models/capture_profile.rs` — 新規作成
    - `CaptureProfile` struct: ウィンドウタイトル、ページ送りキー、待機時間などのフィールド
    - `ProfileEntry` struct: フロントエンド向け JSON 表現、`key` フィールド付き
    - 6 つのビルトインプロファイルを定義（kindle, google_play, rakuten_kobo, bookwalker, dmm_books, kinoppy）
    - `From<(String, CaptureProfile)> for ProfileEntry` を実装
  - `localapp/src-tauri/src/models/mod.rs` — 新規作成（`pub mod capture_profile;`）
  - `localapp/src-tauri/src/commands/capture.rs` — `get_builtin_profiles` コマンド追加
    - `CaptureProfile::builtin_profiles()` → `ProfileEntry::from()` → JSON 配列を返却
  - `localapp/src-tauri/src/lib.rs` — `get_builtin_profiles` を `invoke_handler` に登録
  - `localapp/src-tauri/src/main.rs` — 詳細コメントを追加
  - `localapp/src-tauri/src/commands/mod.rs` — 詳細コメントを追加
- フロントエンド側
  - `localapp/src/store/profileStore.ts` — 新規作成（Zustand ストア）
    - `builtinProfiles`, `customProfiles`, `selectedProfileKey` を管理
    - `fetchProfiles()`: Rust `get_builtin_profiles` を呼び出して初期化
    - `selectProfile()`, `updateCustomProfile()`, `resetProfile()`, `getEffectiveProfile()`
  - `localapp/src/components/capture/ProfileSelector.tsx` — 新規作成
    - shadcn/ui Select を使用したドロップダウン型セレクタ
    - `builtinProfiles` から選択肢を動的生成
  - `localapp/src/components/capture/ProfileEditor.tsx` — 新規作成
    - ページ送りキー、待機時間、ウィンドウタイトル、プロセス名、クリック位置、最前面化フラグの編集 UI
    - 「デフォルトに戻す」ボタンで `resetProfile()` を呼び出し
    - 2 カラムグリッドレイアウトでフォームを配置
  - `localapp/src/views/CaptureView.tsx` — リファクタ
    - `ProfileSelector` + `ProfileEditor` + キャプチャテスト UI を統合
    - `useEffect` で `fetchProfiles()` を呼び出し、起動時にプロファイルを取得
    - セクション分割: キャプチャ設定（上段）/ キャプチャテスト（下段）
  - 既存ファイルへの丁寧なコメント追加
    - `App.tsx`, `navigationStore.ts`, `MainLayout.tsx`, `Sidebar.tsx`
- ビルド確認
  - `cargo check`: 成功（unused import warning のみ）
  - `npm run build`: 成功（`tsc && vite build` ともにエラーなし）
- マージ日: 2026-08-16
- ブランチ: `feature/002002-profile-management`

### 002003 連続キャプチャ実行・進捗表示

【計画】

1. **Rust 側依存クレート追加**
   - `localapp/src-tauri/Cargo.toml` に以下を追加：
     - `tokio` — 非同期ランタイム（バックグラウンドスレッド操作用、特に `tokio::time::sleep` で待機制御）
     - `enigo` — OS間共通のキー入力シミュレーション（ページ送り用。macOSではAccessibility権限が必要）
   - `cargo check` で依存解決とコンパイル確認

2. **Rust 側連続キャプチャコマンド実装**
   - `localapp/src-tauri/src/commands/capture.rs` に以下を追加：
     - `ProgressPayload` 構造体 — 進捗通知用イベントペイロード
       - `current: u32` — 現在のキャプチャ枚数
       - `total: u32` — 予想総ページ数（または設定上限）
       - `status: String` — "capturing" / "page_turn" / "waiting" / "completed" / "stopped"
       - `message: String` — ユーザー向けメッセージ（"12 / 200 ページ キャプチャ完了" など）
     - `start_continuous_capture(app_handle, profile)` コマンド — 連続キャプチャを開始
       - バックグラウンドスレッド（`std::thread::spawn` または `tauri::async_runtime::spawn`）でループ実行
       - 「キャプチャ → 画像差分検出（MSE方式）→ ページ送り（enigo）→ 待機」 のループ
       - `Arc<AtomicBool>` で停止フラグをスレッドセーフに共有
       - `app_handle.emit()` で `ProgressPayload` をフロントエンドへ送信
       - 画像変化検出は Mean Squared Error（平均二乗誤差）方式で閾値判定
         - 前回キャプチャ画像と今回キャプチャ画像のピクセル差を計算
         - 閾値未満＝変化なし＝ページ送り失敗と判断、リトライ処理
       - 画像は一時フォルダに PNG 形式で保存（連番: `001.png`, `002.png`, ...）
         - 保存先: `dirs::picture_dir()` 配下の `BookCapture/<タイトル>/`（タイトルは設定可能にする、未設定なら `untitled`）
     - `stop_continuous_capture()` コマンド — 連続キャプチャを停止
       - `Arc<AtomicBool>` の停止フラグを `true` に設定
       - 実行中スレッドがフラグを検知して安全に終了
   - `localapp/src-tauri/src/lib.rs` — 新規コマンドを `invoke_handler` に登録

3. **フロントエンド進捗表示 UI 実装**
   - `localapp/src/store/captureStore.ts`（新規作成）— 連続キャプチャ状態を Zustand で管理
     - `isCapturing: boolean` — 実行中フラグ
     - `progress: { current: number; total: number; status: string; message: string } | null` — 進捗情報
     - `logs: string[]` — キャプチャログ一覧
     - `captureFolder: string | null` — 結果画像保存先パス
     - `startCapture() / stopCapture()` — Rust コマンドを呼び出し
     - `addLog(message)` — ログ追加
     - `reset()` — 状態リセット
   - `localapp/src/components/capture/CaptureProgress.tsx`（新規作成）— 進捗表示専用コンポーネント
     - shadcn/ui `Progress` コンポーネントで進捗バー
     - ステータステキスト（`message` フィールドを表示）
     - スクロール可能なログ一覧（`logs` を時系列で表示）
   - `localapp/src/views/CaptureView.tsx` — 連続キャプチャ UI を統合
     - 「連続キャプチャ開始」ボタン（実行中は disabled）
     - 「停止」ボタン（未実行時は disabled）
     - `CaptureProgress` コンポーネントを配置
     - `listen("capture-progress")` で Rust 側からの進捗イベントを受信
     - キャプチャ完了後、保存先フォルダパスを表示

4. **コマンド登録・ビルド確認**
   - `localapp/src-tauri/src/lib.rs` — `start_continuous_capture`, `stop_continuous_capture` を `invoke_handler` に追加
   - `cargo check` — Rust 側コンパイル確認
   - `npm run build` — フロントエンドビルド確認
   - `npm run tauri dev` — 起動確認（連続キャプチャボタン表示、プログレスバー表示）

5. **想定される注意点**
   - macOS で `enigo` を使用する場合、初回実行時に「アクセシビリティ」権限の許可が必要になる
   - 画像差分検出の MSE 閾値は環境（解像度・明るさ）により変動するため、調整可能なパラメータとして実装する
   - `tauri::Emitter` のイベント名はフロントエンドの `listen()` と一致させる必要がある
   - 連続キャプチャ中にアプリを閉じた場合のクリーンアップについては、将来のタスク（007001 設定永続化等）で検討
   - `screenshots` crate + `tokio` の組み合わせでブロッキング処理の扱いに注意（`spawn_blocking` の検討）

【実施結果】
- 計画①: enigo crate を追加（tokio は不要だったため追加せず→`std::thread::spawn`で対応）
  - `cargo add enigo` で enigo v0.6.1 を追加
- 計画②: Rust 側連続キャプチャコマンド実装完了
  - `localapp/src-tauri/src/commands/capture.rs` に `ProgressPayload`, `start_continuous_capture`, `stop_continuous_capture`, `run_continuous_capture_loop`, `capture_screen_raw`, `calculate_mse`, `turn_page`, `emit_progress`, `create_capture_folder` を実装
  - `std::sync::OnceLock<Arc<AtomicBool>>` でグローバル停止フラグ・実行中フラグを管理
  - バックグラウンドスレッドでキャプチャループを実行（`std::thread::spawn`）
  - `tauri::Emitter` を use して `app_handle.emit("capture-progress", payload)` で進捗通知
  - MSE 閾値 1000.0 で画像差分検出（フルHD画面での経験値）
  - 保存先: `dirs::picture_dir()/BookCapture/<book_title>/`（連番 `001.png` ~）
- capture.rs コンパイルエラー修正（7 errors → 0）
  - `use tauri::Emitter;` を追加（emit メソッド用）
  - `Enigo::new(&Settings::default()).unwrap()` に修正（enigo 0.6.1 API対応）
  - `turn_page` を `key_click` → `key(key, Direction::Click)` に変更（enigo 0.6.1 API対応）
  - `use enigo::{Enigo, Key, Keyboard, Settings, Direction};` に変更（Keyboard trait が必要）
- 計画③: フロントエンド実装完了
  - `captureStore.ts` — Zustand ストア + `listen("capture-progress")` イベントリスナー
  - `CaptureProgress.tsx` — ステータスバッジ + 進捗バー + メッセージ表示（Apple HIG 風配色）
  - `CaptureView.tsx` — 書籍タイトル入力 + 連続キャプチャ開始/停止ボタン + 進捗表示統合
- 計画④: ビルド確認完了
  - `cargo check`: エラー0（unused import warning 1個のみ、別ファイル）
  - `npm run build`: 成功（`tsc && vite build` ともにエラーなし）
- ブランチ: `feature/002003-continuous-capture` → main にマージ（Fast-forward）
- コミット: `3bce557` — 002003: 連続キャプチャ実行・進捗表示 UI 実装

### 002004 キャプチャ画像のフォルダ管理

【計画】

1. **Rust 側: フォルダ管理強化・画像一覧コマンド**
   - `create_capture_folder()` に同名フォルダ重複回避を追加
     - `BookCapture/<book_title>/` が既存の場合 → `BookCapture/<book_title>_1/`, `_2/` ... と連番サフィックスを付与（上限99）
   - `list_capture_images` コマンドを新規追加
     - 指定フォルダパス内の PNG 画像ファイル一覧を取得
     - ファイル名順でソートして返却（`["001.png", "002.png", ...]`）
   - `get_capture_image` コマンドを新規追加
     - 指定パスの画像を Base64 エンコードして返却（サムネイル表示用）
   - `open_capture_folder` コマンドを新規追加
     - `open` crate で保存フォルダを OS のファイルマネージャーで開く

2. **フロントエンド: キャプチャ結果表示 UI**
   - `CaptureView.tsx` に「キャプチャ結果」セクションを追加
     - キャプチャ完了後、保存フォルダパスと画像枚数を表示
     - 保存フォルダを開くボタン、トリミングタブへ遷移するボタン
   - `CaptureResultGallery.tsx`（新規作成）
     - 保存フォルダ内の画像サムネイル一覧をグリッド表示
     - `list_capture_images` → `get_capture_image` で画像を取得して表示

3. **フロントエンド: トリミングタブ連携**
   - `captureStore.ts` に完了状態のキャプチャ結果情報を保持（completed/stopped 時）
     - `lastCaptureFolder: string | null`
     - `lastCaptureImageCount: number`
   - `CaptureView.tsx` に「トリミングへ進む」ボタンを追加（完了時のみ表示）
     - クリックで `navigationStore.setView("trim")` でトリミングタブに遷移
   - `TrimView.tsx` にキャプチャ結果の自動引き継ぎ対応
     - `captureStore.lastCaptureFolder` が存在する場合、自動的にフォルダを読み込んでサムネイル一覧を表示
     - 「キャプチャ結果を読み込む」ボタンで手動読み込みも可能

4. **コマンド登録・ビルド確認**
   - `lib.rs` に `list_capture_images`, `get_capture_image`, `open_capture_folder` を invoke_handler に追加
   - `cargo check`
   - `npm run build`
   - `npm run tauri dev`

5. **想定される注意点**
   - フォルダ名の重複回避で無限ループにならないよう上限（99）を設ける
   - 画像一覧取得時、非画像ファイルを除外する
   - Base64 エンコードで大きな画像のメモリ消費に注意（必要に応じてリサイズ対応を将来検討）
   - macOS で `open` crate でフォルダを開く

【実施結果】
- 計画①: Rust 側フォルダ管理・画像取得コマンド実装完了
  - `localapp/src-tauri/Cargo.toml` に `open` crate v5.3.0 を追加
  - `create_capture_folder()`: 同名フォルダ重複回避を実装（`_1` 〜 `_99` サフィックス付与、上限 99）
  - `list_capture_images(folder_path)`: 指定フォルダ内の PNG 画像一覧をファイル名順で返却
  - `get_capture_image(filepath)`: 指定画像を読み込み、Base64 エンコードして返却
  - `open_capture_folder(folder_path)`: `open` crate で OS ファイルマネージャーを起動
  - `lib.rs` に `list_capture_images`, `get_capture_image`, `open_capture_folder` を `invoke_handler` に登録
- 計画②: フロントエンド キャプチャ結果表示 UI 実装完了
  - `captureStore.ts` — `lastCaptureFolder`, `lastCaptureImageCount`, `setLastCaptureResult` を追加
    - `setProgress` の terminal state（completed / stopped / error）時に自動保存するよう更新
  - `CaptureResultGallery.tsx` — 新規作成
    - 先頭 10 枚まで `get_capture_image` でサムネイルを Base64 読み込み
    - グリッドレイアウトでサムネイル表示（ホバー時にページ番号オーバーレイ）
    - 「フォルダを開く」「トリミングへ進む」ボタン
  - `CaptureView.tsx` — 「キャプチャ結果」セクションを追加
    - `lastCaptureFolder && !isContinuousCapturing` の条件で表示
    - 「フォルダを開く」→ `open_capture_folder` コマンド呼び出し
    - 「トリミングへ進む」→ `navigationStore.setView("trim")` でタブ遷移
- 計画③: トリミングタブ連携実装完了
  - `TrimView.tsx` — `captureStore.lastCaptureFolder` を監視し、存在時に自動で `CaptureResultGallery` を表示
  - キャプチャ結果なしの場合はプレースホルダメッセージを表示
- 計画④: ビルド確認完了
  - `cargo check`: コンパイル成功（error 0）
  - `npm run build`: ビルド成功（`tsc && vite build` ともにエラーなし）
  - `npm run tauri dev`: 起動成功
    - 連続キャプチャ完了後、結果セクションにフォルダパスとサムネイルが表示されることを確認
    - 「トリミングへ進む」ボタンでトリミングタブに遷移し、同じサムネイルが表示されることを確認
- ブランチ: `feature/002004-capture-folder-management`

---

## ユースケース 003 — PDF 読込

外部 PDF を画像化して、トリミングタブに引き継ぐ。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 003001 | PDF 選択・設定 UI | 2026-08-15 |  | 実装 |
| 003002 | PDF → 画像展開（Rust バックエンド） | 2026-08-15 |  | 実装 |

### 003001 PDF 選択・設定 UI

【計画】
- PDF ファイル選択ダイアログ
- 出力フォルダ設定（自動設定含む）
- DPI（150/200/300/400）と形式（PNG/JPG）選択
- 設定の保存/リセット

【実施結果】

### 003002 PDF → 画像展開（Rust バックエンド）

【計画】
- `pdfium-render` 等で PDF をページ画像化
- バックグラウンド実行
- 進捗通知
- 完了後、トリミングタブに自動引き継ぎ

【実施結果】

---

## ユースケース 004 — 画像トリミング

キャプチャまたは PDF 展開した画像から余白を削除する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 004001 | 画像フォルダ読み込み・サムネイル一覧 UI | 2026-08-15 |  | 実装 |
| 004002 | Before/After プレビュー表示 | 2026-08-15 |  | 実装 |
| 004003 | 余白自動検出（Rust バックエンド） | 2026-08-15 |  | 実装 |
| 004004 | 手動余白調整 UI | 2026-08-15 |  | 実装 |
| 004005 | トリミング一括実行・進捗表示 | 2026-08-15 |  | 実装 |

### 004001 画像フォルダ読み込み・サムネイル一覧 UI

【計画】
- 入力フォルダ選択ダイアログ
- 画像ファイル一覧をサムネイルグリッドで表示
- 並び替え（ファイル名順）
- 前工程からの自動入力対応

【実施結果】

### 004002 Before/After プレビュー表示

【計画】
- オリジナル画像とトリミング後画像を左右に並列表示
- ズーム・パン対応
- 現在のファイル名とページ番号表示
- 前へ/次へ ナビゲーション

【実施結果】

### 004003 余白自動検出（Rust バックエンド）

【計画】
- 複数ページをサンプリングして 4 辺の余白を推定
- 最小マージン（最も保守的な値）を採用
- 安全マージン（係数 + 固定 px）を適用
- 推定結果を UI に反映

【実施結果】

### 004004 手動余白調整 UI

【計画】
- 左/右/上/下 の数値入力
- Canvas 上でドラッグして範囲を選択
- プレビューのリアルタイム更新
- 微調整ボタン

【実施結果】

### 004005 トリミング一括実行・進捗表示

【計画】
- 全画像の一括トリミングを Rust 側で実行
- 進捗通知（current/total）
- 出力フォルダ自動生成
- 完了後、ZIP 出力タブに自動引き継ぎ

【実施結果】

---

## ユースケース 005 — ZIP 出力・連携

トリミング済み画像を ZIP アーカイブにまとめる。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 005001 | ZIP アーカイブ化（Rust バックエンド） | 2026-08-15 |  | 実装 |
| 005002 | 出力設定・ファイル名設定 UI | 2026-08-15 |  | 実装 |
| 005003 | タブ間自動連携 | 2026-08-15 |  | 実装 |

### 005001 ZIP アーカイブ化（Rust バックエンド）

【計画】
- `zip` crate を用いて画像フォルダを ZIP 化
- ファイル名順で格納
- 保存ダイアログ連携

【実施結果】

### 005002 出力設定・ファイル名設定 UI

【計画】
- 出力先選択、ファイル名入力
- 保存前に上書き確認
- 前工程からの自動入力対応

【実施結果】

### 005003 タブ間自動連携

【計画】
- キャプチャ完了 → トリミング入力に自動設定
- トリミング完了 → ZIP 出力に自動設定
- 状態管理（Zustand）で連携

【実施結果】

---

## ユースケース 006 — モダン GUI デザイン

クリーン＆ミニマルな Apple HIG 風 UI を実装する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| 006001 | デザインシステム定義 | 2026-08-15 | 2026-08-16 | 実装 |
| 006002 | サイドバー＋メインレイアウト実装 | 2026-08-15 | 2026-08-15 | 実装 |
| 006003 | ライトモード対応 + OS 設定連動 | 2026-08-15 | 2026-08-16 | 実装 |
| 006004 | アプリ名・サイドバー変更 | 2026-08-15 | 2026-08-16 | 実装 |

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
