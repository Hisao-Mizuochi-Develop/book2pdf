# localapp 作業ログ

## 002001 — 画面キャプチャ方式調査・実装

### 【実施予定】

- 日時: 2026-08-16
- 目的: Tauri v2 でスクリーンショット取得方式を調査し、単発キャプチャコマンドを実装する
- 前提:
  - feature/002001-screenshot-research ブランチを作成済み
  - reference/localapp (Python版) のキャプチャ機能を参考にする
- 変更内容:
  1. `localapp/src-tauri/Cargo.toml` — `screenshots`, `base64` crate を追加
  2. `localapp/src-tauri/src/commands/capture.rs` — 新規作成、`capture_screen` コマンド実装
  3. `localapp/src-tauri/src/commands/mod.rs` — 新規作成、モジュール公開
  4. `localapp/src-tauri/src/lib.rs` — `greet` コマンド削除、`capture_screen` を登録
  5. `localapp/src/views/CaptureView.tsx` — キャプチャテストボタン＋画像表示を追加
- 実施コマンド:
  1. `cargo check`（Rust 側コンパイル確認）
  2. `npm run build`（フロントエンドビルド確認）
  3. `npm run tauri dev`（起動確認）
- 想定される結果や注意点:
  - `screenshots` crate は Tauri 標準権限外のネイティブ処理なので capabilities は変更不要
  - `image` crate の `PngEncoder` で PNG エンコード、`base64` crate でエンコードして返却
  - `invoke` API は Tauri WebView 内でのみ動作する（ブラウザ直接アクセスではエラー）

### 【実施実績】

- `screenshots` crate v0.8.10 と `base64` crate v0.23.1 を `Cargo.toml` に追加
- `localapp/src-tauri/src/commands/capture.rs` を新規作成
  - `capture_screen` コマンドを実装
  - `Screen::all()` でディスプレイ一覧を取得し、最初の画面をキャプチャ
  - PNG エンコード時、`image::PngEncoder` + `ImageEncoder::write_image()`を使用
    - `to_png()` メソッドが存在しない → `PngEncoder` + `write_image()` に変更して解決
    - `write_image()` が見つからない → `use image::ImageEncoder;` トレイトインポートで解決
  - Base64 エンコードしてフロントエンドに返却する `CaptureResult` struct を定義
- `localapp/src-tauri/src/commands/mod.rs` を新規作成（`pub mod capture;`）
- `localapp/src-tauri/src/lib.rs` を更新
  - `mod commands;` を追加
  - デフォルトの `greet` コマンドを削除
  - `invoke_handler` に `commands::capture::capture_screen` を登録
- `localapp/src/views/CaptureView.tsx` を更新
  - 「キャプチャテスト」ボタンを追加（shadcn/ui Button + lucide-react Camera アイコン）
  - `invoke<CaptureResult>("capture_screen")` でRustコマンドを呼び出し
  - 取得した画像を `data:image/png;base64,...` で `<img>` に表示
  - エラーハンドリング（try-catch）、ローディング状態（useState）を実装
- `cargo check`: コンパイル成功
- `npm run build`: ビルド成功（`tsc && vite build` ともにエラーなし）
- `npm run tauri dev`: 起動成功
  - フロントエンド表示確認: サイドバー「電子書籍」選択時に「キャプチャテスト」ボタンが正しく表示
  - 注意: `invoke` API は Tauri WebView 内でのみ動作するため、ブラウザ直接アクセスでのキャプチャ実行は不可（想定内の制限）

---

## 002002 — アプリプロファイル管理 UI

### 【実施予定】

- 日時: 2026-08-16
- 目的: 電子書籍アプリごとのプロファイルを Rust 側で定義し、フロントエンドで選択・編集できるようにする
- 前提:
  - 002001（画面キャプチャ方式調査・実装）が完了していること
  - feature/002002-profile-management ブランチを作成済み
- 変更内容:
  1. `localapp/src-tauri/src/models/capture_profile.rs` — 新規作成、`CaptureProfile` struct + ビルトインプロファイル
  2. `localapp/src-tauri/src/models/mod.rs` — 新規作成、モジュール公開
  3. `localapp/src-tauri/src/commands/capture.rs` — `get_builtin_profiles` コマンド追加
  4. `localapp/src-tauri/src/lib.rs` — 新規コマンドを invoke_handler に登録
  5. `localapp/src/store/profileStore.ts` — 新規作成、Zustand ストア
  6. `localapp/src/components/capture/ProfileSelector.tsx` — 新規作成、セレクタ UI
  7. `localapp/src/components/capture/ProfileEditor.tsx` — 新規作成、編集 UI
  8. `localapp/src/views/CaptureView.tsx` — 各種コンポーネントを統合
- 実施コマンド:
  1. `cargo check`
  2. `npm run build`
  3. `npm run tauri dev`
- 想定される結果や注意点:
  - `CaptureProfile` の JSON シリアライズは `serde` を使用
  - `ProfileEntry` はフロントエンド向けに `key` を含む構造にする
  - プロファイルの変更はメモリ上のみ保持（永続化は将来タスク）

### 【実施実績】

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

---

## 002003 — 連続キャプチャ実行・進捗表示

### 【実施予定】

- 日時: 2026-08-16
- 目的: プロファイルに基づいて連続キャプチャを自動実行し、進捗を UI に表示する
- 前提:
  - 002002（アプリプロファイル管理 UI）が完了していること
  - feature/002003-continuous-capture ブランチを作成済み
- 変更内容:
  1. `localapp/src-tauri/Cargo.toml` — `enigo` crate を追加（ページ送りキー入力用）
  2. `localapp/src-tauri/src/commands/capture.rs` — 連続キャプチャコマンド群を追加
  3. `localapp/src/store/captureStore.ts` — 連続キャプチャ状態を管理する Zustand ストア
  4. `localapp/src/components/capture/CaptureProgress.tsx` — 進捗表示 UI
  5. `localapp/src/views/CaptureView.tsx` — 連続キャプチャ UI を統合
- 実施コマンド:
  1. `cargo add enigo`
  2. `cargo check`
  3. `npm run build`
  4. `npm run tauri dev`
- 想定される結果や注意点:
  - `enigo` crate は macOS で Accessibility 権限が必要
  - バックグラウンドスレッドでのキャプチャループを実装
  - MSE（平均二乗誤差）によるページ遷移検出
  - 画像保存先: `dirs::picture_dir()/BookCapture/<書籍タイトル>/`

### 【実施実績】

- `cargo add enigo` で enigo v0.6.1 を追加
- `localapp/src-tauri/src/commands/capture.rs` に以下を実装
  - `ProgressPayload` — 進捗通知用イベントペイロード（current, total, status, message, capture_folder）
  - `start_continuous_capture()` — 連続キャプチャ開始コマンド
  - `stop_continuous_capture()` — 連続キャプチャ停止コマンド
  - `run_continuous_capture_loop()` — バックグラウンドスレッドでのキャプチャループ
    - 「キャプチャ → MSE差分検出 → PNG保存 → ページ送り（enigo）→ 待機」のループ
    - `std::sync::OnceLock<Arc<AtomicBool>>` でグローバル停止フラグ・実行中フラグを管理
    - MSE 閾値 1000.0 でページ遷移判定
    - `tauri::Emitter` で `capture-progress` イベントをフロントエンドに送信
  - `capture_screen_raw()` — 生スクリーンショット取得（PNGバイト列）
  - `calculate_mse()` — 2枚のPNG間の平均二乗誤差を計算
  - `turn_page()` — enigo でページ送りキー入力（right/left/space）
  - `emit_progress()` — 進捗イベント送信ヘルパー
  - `create_capture_folder()` — 保存先フォルダ作成（BookCapture/<タイトル>/）
- コンパイルエラー修正（7 errors → 0）
  - `use tauri::Emitter;` を追加
  - `Enigo::new(&Settings::default()).unwrap()`, `key(key, Direction::Click)` に修正
  - `use enigo::{Enigo, Key, Keyboard, Settings, Direction};` に変更
- `localapp/src/store/captureStore.ts` — Zustand ストア + `listen("capture-progress")` イベントリスナー
- `localapp/src/components/capture/CaptureProgress.tsx` — ステータスバッジ + 進捗バー + メッセージ表示
- `localapp/src/views/CaptureView.tsx` — 書籍タイトル入力 + 連続キャプチャ開始/停止ボタン
- `cargo check`: エラー0
- `npm run build`: 成功
- ブランチ: `feature/002003-continuous-capture` → main マージ
- コミット: `3bce557`

---

## 002004 — キャプチャ画像のフォルダ管理

### 【実施予定】

- 日時: 2026-08-16
- 目的: キャプチャ結果をフォルダで管理し、画像一覧表示・フォルダを開く・トリミングタブ連携を実現する
- 前提:
  - 002003（連続キャプチャ実行・進捗表示）が完了していること
  - feature/002004-capture-folder-management ブランチを作成済みであること
- 変更内容:
  1. `localapp/src-tauri/Cargo.toml` — `open` crate を追加（フォルダを OS で開くため）
  2. `localapp/src-tauri/src/commands/capture.rs` — `create_capture_folder()` に重複回避を追加、`list_capture_images`, `get_capture_image`, `open_capture_folder` コマンドを新規追加
  3. `localapp/src-tauri/src/lib.rs` — 新規コマンドを invoke_handler に登録
  4. `localapp/src/store/captureStore.ts` — `lastCaptureFolder`, `lastCaptureImageCount` を追加
  5. `localapp/src/views/CaptureView.tsx` — キャプチャ結果セクション（フォルダ表示・サムネイル・トリミング遷移ボタン）を追加
  6. `localapp/src/components/capture/CaptureResultGallery.tsx` — 新規作成（画像サムネイルグリッド）
  7. `localapp/src/views/TrimView.tsx` — キャプチャ結果の自動引き継ぎ対応
- 実施コマンド:
  1. `cargo check`（Rust 側コンパイル確認）
  2. `npm run build`（フロントエンドビルド確認）
  3. `npm run tauri dev`（起動確認）
- 想定される結果や注意点:
  - `open` crate でフォルダを開く際、OS ごとのコマンド差異を吸収する
  - Base64 エンコードのメモリ消費に注意（大きな画像の場合）
  - フォルダ名重複回避で無限ループにならないよう上限（99）を設ける

### 【実施実績】

- `localapp/src-tauri/Cargo.toml` — `open` crate v5.3.0 を追加
  - フォルダを OS のファイルマネージャーで開くために使用
- `localapp/src-tauri/src/commands/capture.rs` — フォルダ管理・画像取得コマンドを追加
  - `create_capture_folder()`: 同名フォルダ重複回避を実装（`_1` 〜 `_99` サフィックス付与、上限 99）
  - `list_capture_images(folder_path)`: 指定フォルダ内の PNG 画像一覧をファイル名順で返却
  - `get_capture_image(filepath)`: 指定画像を読み込み、Base64 エンコードして返却（サムネイル表示用）
  - `open_capture_folder(folder_path)`: `open` crate で OS ファイルマネージャーを起動
- `localapp/src-tauri/src/lib.rs` — 新規コマンド `list_capture_images`, `get_capture_image`, `open_capture_folder` を `invoke_handler` に登録
- `localapp/src/store/captureStore.ts` — キャプチャ結果状態を追加
  - `lastCaptureFolder: string | null` — 最後のキャプチャ保存フォルダパス
  - `lastCaptureImageCount: number` — 最後のキャプチャ画像枚数
  - `setLastCaptureResult(folder, count)` — 完了時に状態を保存するアクション
  - `setProgress` の terminal state（completed / stopped / error）時に `lastCaptureFolder` / `lastCaptureImageCount` を自動保存するよう更新
- `localapp/src/components/capture/CaptureResultGallery.tsx` — 新規作成
  - マウント時に `list_capture_images` で画像一覧を取得し、先頭 10 枚まで `get_capture_image` でサムネイルを Base64 読み込み
  - グリッドレイアウトでサムネイル表示（ホバー時にページ番号オーバーレイ）
  - 「フォルダを開く」「トリミングへ進む」ボタンを配置
- `localapp/src/views/CaptureView.tsx` — キャプチャ結果セクションを追加
  - `lastCaptureFolder && !isContinuousCapturing` の条件で `CaptureResultGallery` を表示
  - 「フォルダを開く」→ `open_capture_folder` コマンド呼び出し
  - 「トリミングへ進む」→ `navigationStore.setView("trim")` でタブ遷移
- `localapp/src/views/TrimView.tsx` — キャプチャ結果自動引き継ぎ対応
  - `captureStore.lastCaptureFolder` を監視し、存在時に自動で `CaptureResultGallery` を表示
  - キャプチャ結果なしの場合はプレースホルダメッセージを表示
- ビルド確認
  - `cargo check`: コンパイル成功（error 0）
  - `npm run build`: ビルド成功（`tsc && vite build` ともにエラーなし）
  - `npm run tauri dev`: 起動成功
    - 連続キャプチャ完了後、結果セクションにフォルダパスとサムネイルが表示されることを確認
    - 「トリミングへ進む」ボタンでトリミングタブに遷移し、同じサムネイルが表示されることを確認
- ブランチ: `feature/002004-capture-folder-management` → main にマージ（Fast-forward）
- コミット: `b7c9946` — 002004: キャプチャ画像のフォルダ管理実装

---

## 002005 — ウィンドウ指定キャプチャ＋コンテンツ領域自動トリミング

### 【実施予定】

- 日時: 2026-08-16
- 目的: プロファイルで指定されたウィンドウのみをキャプチャし、外枠を除外して書籍コンテンツ部分だけを切り出す
- 前提:
  - 002004（キャプチャ画像のフォルダ管理）が完了していること
  - feature/002005-window-capture ブランチを作成済みであること
- 変更内容:
  1. `localapp/src-tauri/src/models/capture_profile.rs` — `crop_insets: Insets { top, right, bottom, left }` を追加
  2. `localapp/src-tauri/src/commands/capture.rs` — `capture_by_window_title()` を新規実装、`capture_screen()` / `capture_screen_raw()` をプロファイル受け取りに変更
  3. `localapp/src-tauri/src/lib.rs` — シグネチャ変更確認
  4. `localapp/src/components/capture/ProfileEditor.tsx` — トリミング値編集 UI を追加
  5. `localapp/src/views/CaptureView.tsx` — `capture_screen` 呼び出し時にプロファイルを渡すよう変更
- 実施コマンド:
  1. `cargo check`
  2. `npm run build`
  3. `npm run tauri dev`
- 想定される結果や注意点:
  - `screenshots::Window` API でウィンドウ指定キャプチャ
  - `crop_insets` は macOS/Windows で異なる可能性があるためプロファイルで設定可能にする
  - トリミング後の画像が0pxにならないようバリデーション必須
  - Kindle for Mac のタイトルバー・ツールバー高さは約42px（環境による可能性あり）

### 【実施実績】

（実装後に追記）

---

## 002007 — ウィンドウ指定キャプチャ実装のコンパイルエラー修正

### 【実施予定】

- 日時: 2026-08-16
- 目的: 002005 の実装中に発生した 2 つのコンパイルエラーを修正する
- 前提:
  - feature/002005-window-capture ブランチ上で 002005 の変更がステージングされていない状態
  - 002005 の実装途上で `cargo check` にて 2 エラーが発生済み
- 変更内容:
  1. `localapp/src-tauri/src/commands/capture.rs`
     - `use screenshots::Window` を削除
     - `capture_by_window_title` 関数を削除
     - `capture_screen_raw` をシンプル化（全画面キャプチャ + crop_insets トリミング方式に統一）
     - `apply_crop_insets` で `SubImage::to_image().as_raw()` を使用
  2. `localapp/docs/tasks.md` — 002007 タスク追加
- 実施コマンド:
  1. `cargo check`
  2. `npm run build`
- 想定される結果や注意点:
  - `screenshots` v0.8.10 には `Window` struct がエクスポートされていない（`Screen` のみ）
  - `SubImage<&RgbaImage>` は `as_flat_samples()` を持たない → `to_image()` で `ImageBuffer` に変換が必要
  - ウィンドウ指定キャプチャは将来 xcap / AppleScript 等で拡張を検討

### 【実施実績】

- feature/002007-window-capture-compile-fix ブランチを作成（002005 ブランチから派生）
- `localapp/src-tauri/src/commands/capture.rs` を修正
  - `use screenshots::{Screen, Window};` → `use screenshots::Screen;`
  - `capture_by_window_title` 関数を削除（308〜346行、ウィンドウ名検索は `screenshots` crate では不可）
  - `capture_screen_raw` をシンプル化：引数 `profile: Option<CaptureProfile>` → `profile: &CaptureProfile`
    - 全画面キャプチャ取得後、`crop_insets` があればトリミング、なければそのまま返却
  - `apply_crop_insets` の `SubImage` 処理を修正
    - `cropped.as_flat_samples().samples` → `cropped.to_image().as_raw()`
    - `SubImage<&RgbaImage>` は `as_flat_samples()` メソッドを持たない
    - `to_image()` で所有権を持つ `ImageBuffer<Rgba<u8>, Vec<u8>>` に変換 → `as_raw()` で `&Vec<u8>` を取得
  - 【002005/002007】ウィンドウ指定キャプチャについてのコメントを追加
    - `screenshots` crate v0.8.10 では `Window` struct がエクスポートされていない
    - 将来の拡張として AppleScript、`core-foundation`、`xcap` crate 等を検討する旨を記載
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功（`tsc && vite build` ともにエラーなし）
- ブランチ: `feature/002007-window-capture-compile-fix` → main にマージ（Fast-forward）
- コミット: `ddd048b`

