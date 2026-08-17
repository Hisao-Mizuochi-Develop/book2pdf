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

- 2026-08-16: 実装途中で2つのコンパイルエラーが発生
  1. `use screenshots::Window` → `Window` struct が `screenshots` v0.8.10 でエクスポートされていない
  2. `crop_imm().as_flat_samples()` → `SubImage` に `as_flat_samples()` メソッドが存在しない
- エラー修正は 002007 として別タスクで対応

---

## 002008 — ウィンドウ指定キャプチャ実装（xcap crate 版）

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

---

## 002008 — ウィンドウ指定キャプチャ実装（xcap crate 版）

### 【実施予定】

- 日時: 2026-08-16
- 目的: `screenshots` crate（全画面キャプチャのみ）から `xcap` crate（ウィンドウ指定キャプチャ対応）へ切り替え、プロファイルで指定されたアプリウィンドウを直接キャプチャする
- 前提:
  - 002007（コンパイルエラー修正）が完了していること
  - feature/002008-window-capture-xcap ブランチを作成済みであること
  - main ブランチが最新であること
- 変更内容:
  1. `localapp/src-tauri/Cargo.toml` — `screenshots` を削除、`xcap` を追加
  2. `localapp/src-tauri/src/commands/capture.rs` — xcap 版に完全書き換え
     - `find_window_by_title()` — ウィンドウタイトル部分一致検索
     - `capture_screen_raw()` — 対象ウィンドウを `capture_image()` で直接取得
     - `apply_crop_insets()` — xcap キャプチャ後にトリミング適用
  3. `localapp/src-tauri/src/lib.rs` — シグニチャ変更確認（変更なしの想定）
  4. フロントエンド — 変更なし（プロファイル渡しは既存のまま）
- 実施コマンド:
  1. `cargo remove screenshots`
  2. `cargo add xcap`
  3. `cargo check`
  4. `npm run build`
  5. `npm run tauri dev`
- 想定される結果や注意点:
  - macOS で `xcap` は初回「画面収録」権限が必要
  - `Window::all()` のパフォーマンス影響（連続キャプチャ中は毎回全ウィンドウ列挙）
  - ウィンドウタイトルが動的に変わる場合、部分一致検索が失敗する可能性
  - crop_insets は xcap キャプチャ後に適用（ウィンドウ枠は xcap で除外済み）

### 【実施実績】

- `localapp/src-tauri/Cargo.toml`
  - `cargo remove screenshots` で `screenshots` crate を削除（v0.8.10、全画面キャプチャのみ）
  - `cargo add xcap` で `xcap = "0.3.3"` を追加（ウィンドウ指定キャプチャ対応）
- `localapp/src-tauri/src/commands/capture.rs` を xcap 版に完全書き換え
  - `use xcap::Window;` に変更（`screenshots::Screen` を削除）
  - `capture_window_image(profile)` — 新規関数：ウィンドウタイトル部分一致 → プロセス名フィルタ → `window.capture_image()`
    - `Window::all()` で全ウィンドウ列挙 → タイトル部分一致（`to_lowercase().contains(keyword_lower)`）
    - プロセス名フィルタ：`.trim_end_matches(".exe")` で拡張子除去、`contains()` で部分一致（macOS/Windows 互換）
    - マッチしたウィンドウを `.capture_image()` でキャプチャ（返り値: `image::RgbaImage`）
    - `window_title_keyword` が空の場合：エラー返却（フォールバック全画面キャプチャは実装しない方針に変更）
    - マッチしない場合：エラーメッセージに利用可能ウィンドウ一覧（タイトルとプロセス名）を付与して返却
  - `capture_screen_raw()` を更新：PNG エンコード前に `capture_window_image()` を呼び出し、成功時は `RgbaImage` を PNG エンコード + `crop_insets` 適用
  - `apply_crop_insets()` を更新：`crop_imm().to_image().as_raw()` の形式でトリミング後の生バイト列を取得（`SubImage` → `ImageBuffer` 変換）
- 初回テストで Kindle プロファイルの `process_name: "Kindle.exe"` が macOS の `"Kindle"` とマッチしない問題を発見・修正
  - `.trim_end_matches(".exe")` で `.exe` 拡張子を除去する対処を実装
  - `==` から `contains()` に変更して部分一致に対応（プロセス名の完全一致要求を緩和）
- 単発キャプチャテスト（「キャプチャテスト」ボタン）で Kindle ウィンドウのキャプチャに成功
  - Kindle ウィンドウのみがキャプチャされ、メニューバー・ウインドウ枠が除外されることを確認
  - キャプチャ画像に `crop_insets.top: 82` のトリミングが正しく適用されることを確認
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功（`tsc && vite build` ともにエラーなし）
- `npm run tauri dev`: 起動成功
  - 単発キャプチャで Kindle ウィンドウが正しく取得されることを確認
  - プロファイル編集で `window_title_keyword`、`process_name`、`crop_insets` の変更が即座に反映されることを確認
- 連続キャプチャテスト中に2つのバグを発見（詳細は tasks.md 002008-1 欄を参照）
  - Bug 1: 連続キャプチャで1ページしかキャプチャできない → `calculate_mse()` が PNG 圧縮バイト列を比較しているため、ウィンドウキャプチャ後の画像サイズ縮小で MSE < 1000.0 と誤判定され「最終ページ到達」と判断される
  - Bug 2: 「キャプチャ前に最前面へ持ってくる」が機能しない → `use_bring_to_top: true` フラグがあるが `run_continuous_capture_loop()` に一切実装がない
- 002005 と 002008 の重複問題の解消
  - 002005 は「ウィンドウ指定キャプチャ＋コンテンツ領域自動トリミング」を目指したが、`screenshots` crate で `Window` struct が使えず実装途中で断念
  - 002007 でコンパイルエラー修正（全画面キャプチャ + `crop_insets` トリミングに後退）を実施
  - 002008 で `xcap` crate を採用し、当初 002005 で目指した「ウィンドウ指定キャプチャ」を実現
  - tasks.md の 002005 【実施結果】に「実装内容は 002008 に引き継がれた」と明記し、重複を解消
- ブランチ: `feature/002008-window-capture-xcap`

> **注意**: Git コミットはユーザーの合格確認後に実施すること（ユーザー指示）

---

## 002008-1 — 連続キャプチャバグ修正（MSE計算 & 最前面化）【バグ対応】

### 【実施予定】

- 日時: 2026-08-16
- 目的: 連続キャプチャで発見された2つのバグを修正する
- 前提:
  - 002008での単発キャプチャテスト成功後、連続キャプチャテスト中にBug 1・Bug 2を発見済み
  - feature/002008-1-bug-fix ブランチを作成済み
- 変更内容:
  1. `localapp/src-tauri/src/commands/capture.rs` — `calculate_mse()` をピクセルレベル比較に修正、`bring_window_to_front()` を新規実装
  2. `cargo check` / `npm run build`
  3. `npm run tauri dev` で連続キャプチャテスト（Kindle for Mac）
- 想定される結果や注意点:
  - MSE計算が正しく動作し、複数ページの連続キャプチャが可能になる
  - 最前面化により、Kindleが他のウィンドウに隠れていてもキャプチャ可能になる

### 【実施実績】

- `calculate_mse()` の修正
  - シグネチャ変更: `fn calculate_mse(prev: &[u8], curr: &[u8]) -> f64` → `fn calculate_mse(prev: &RgbaImage, curr: &RgbaImage) -> f64`
  - PNG 圧縮バイト列比較 → ピクセルレベル RGBA 差分の二乗和平均に変更
  - `capture_window_image()` の返り値 `RgbaImage` をそのまま MSE 比較に使用し、PNG エンコード→デコードの無駄を削減
- `bring_window_to_front()` の新規実装
  - macOS: `osascript` で `System Events` 経由にプロセスの `frontmost` を設定
  - `profile.process_name` から `.exe` 拡張子を除去して使用
  - 連続キャプチャループ内でキャプチャ前に自動実行
- `capture_window_image()` にリトライ機構（最大3回、500ms間隔）を追加
  - 「Failed to copy data」エラー時に自動リトライ
- 最前面化後の待機時間を 500ms → 1500ms に延長
  - AppleScript 実行後のウィンドウレンダリング完了を確実に待つ
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功

### 【手動テスト結果】

- **2026-08-16 連続キャプチャテスト（Kindle for Mac）**
  - 連続キャプチャで Kindle が最前面に来て、複数ページ取得に成功
  - 以下の追加修正点が発見された：
    1. 「クリック位置」は未実装機能なので廃止すべき
    2. プロファイルのデフォルト値を "kindle" に固定すべき
    3. 「ページ送りキー」が変更できない（デフォルト値表示も "right" ではなく "右矢印（→）" のように選択リストと同じ文言にすべき）
    4. 「ウィンドウタイトルキーワード」はビルトインプロファイルでは変更不可なので表示不要
    5. 「プロセス名」はビルトインプロファイルでは変更不可なので表示不要、デフォルト値を "Kindle.exe" → "Kindle" に変更すべき
- `.clinerules` に「コミット前にユーザーのテストと合格判定が必須」を追記
- ブランチ: `feature/002008-1-bug-fix`
- 2026-08-17: 前回セッションの修正が不完全に反映されていた追加修正（3点）
  1. **capture.rs: 先頭復帰処理をMSE差分検出ベースに完全書き換え**
     - 原因: 固定200回ループでは「先頭到達検出」ができない。ユーザーから「200回の根拠はなんですか？本来は先頭ページに到達するまでが正解です」と指摘
     - 修正内容:
       - `bring_window_to_front` を先頭復帰の「前」に実行（キー入力が確実に届くようフォーカスを当てる）
       - 逆方向ページ送り後にスクリーンショットを撮影し、前回画像とMSE差分を計算するループを構築
       - MSE < 50.0（先頭復帰専用閾値）で「これ以上逆方向にページを変更できない（＝先頭到達）」と判定して終了
       - 最大200回まで（安全上限）、20ページごとに進捗イベントをemit
     - 実装のポイント: `turn_page_reverse` → sleep(150ms) → `capture_window_image` → `calculate_mse(prev, curr)` のループ
  2. **profileStore.ts: builtinProfiles.processName を空文字 → "Kindle" に修正**
     - 原因: `bring_window_to_front` は `profile.process_name` を `osascript` の引数に使用。空文字だと最前面化が機能しない
     - 修正: `processName: "Kindle"` に変更（Kindle for Mac のプロセス名に一致）
  3. **ProfileEditor.tsx: SelectItem の `textValue` prop 対応 → Base UI 自動レンダリング方式に統合**
     - 原因: @base-ui/react/select の `SelectPrimitive.Item` が `textValue` prop を受け付けない型定義だった
     - 試行: `SelectItem` の型定義を拡張して `textValue` を追加 → JSX側で `<SelectPrimitive.Item textValue={textValue}>` を渡すも、依然として TypeScript エラー
     - 結論: Base UI の `SelectValue` は `SelectItemText` の children を自動認識するため、明示的な `textValue` は不要。呼び出し側（ProfileEditor.tsx）に `textValue` prop を追加しなくても日本語ラベルが正しく表示される
     - 修正: `select.tsx` は元の `...props` 方式に戻し、`ProfileEditor.tsx` は変更なしのままで正常動作
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- 2026-08-17: bookTitle / startFromBeginning 引数名の camelCase 統一修正
    - 原因: `invalid args \`bookTitle\` for command \`start_continuous_capture\`` エラーが発生
    - Tauri の `invoke()` は JS オブジェクトのキー名と Rust コマンドの引数名が完全一致する必要がある
    - フロントエンド（`captureStore.ts`）が `bookTitle` / `startFromBeginning` を送信し、Rust 側（`capture.rs`）が `book_title` / `start_from_beginning` を期待していたためマッチング失敗
    - 修正案: 両方を camelCase に統一（`bookTitle`, `startFromBeginning`）
      - `localapp/src/store/captureStore.ts`: `book_title` → `bookTitle`, `start_from_beginning` → `startFromBeginning`
      - `localapp/src-tauri/src/commands/capture.rs`: 関数シグニチャ・コメント・変数参照を全て camelCase に変更
    - `cargo check`: コンパイル成功（エラー0、non_snake_case 警告2つは想定内）
    - `npm run tauri dev`: 起動成功
    - ユーザーテスト: 「連続キャプチャ開始」ボタンクリックで `bookTitle` エラーが解消されたことを確認
- Git コミット・マージ完了
  - ブランチ: `feature/002008-window-capture-xcap`
  - コミット: `34723f6`
  - main ブランチへ Fast-forward マージ済み

---

## 002008-2 — プロファイルUI改善（デフォルト選択・表示・バリデーション）

### 【実施予定】

- 日時: 2026-08-16
- 目的: 002008-1 の手動テストで発見したUI・UX問題を修正する
- 前提:
  - feature/002008-2-profile-ui-fix ブランチを作成済み
- 変更内容:
  1. `localapp/src/store/profileStore.ts` — デフォルト選択を "kindle" に固定
  2. `localapp/src/components/capture/ProfileEditor.tsx` — SelectValue に日本語ラベル表示を追加、pageWait を Input から Select に変更
  3. `localapp/src/views/CaptureView.tsx` — 連続キャプチャ開始前に bookTitle が空の場合はエラー表示
- 実施コマンド:
  1. `cargo check`
  2. `npm run build`
  3. `npx tauri build`
- 想定される結果や注意点:
  - Select の value は string なので、pageWait の float 値は String() で変換してから渡す
  - bookTitle.trim() で空白文字のみの入力も拒否する

### 【実施実績】

- `localapp/src/store/profileStore.ts` を修正
  - `selectedProfileKey` の初期値を `null` → `"kindle"` に変更
  - これにより起動時に「プロファイルを選択」ではなく「Kindle」が即座に選択される
- `localapp/src/components/capture/ProfileEditor.tsx` を修正
  - `pageTurnKeyLabelMap` 定数を新規追加（right→右矢印（→）, left→左矢印（←）, space→スペース, arrow→矢印キー（左右））
  - `<SelectValue />` を `<SelectValue>{pageTurnKeyLabelMap[...]}</SelectValue>` に変更。表示値が raw 値（"right"）ではなく日本語ラベルになることを確認
  - ページ送り待機時間を `<Input type="number">` から `<Select>` に変更。選択肢は 0.15 / 0.20 / 0.25 / 0.30
  - 不要になった `localPageWait` useState / useEffect を削除
  - `useState`, `useEffect` の import も同時に削除
- `localapp/src/views/CaptureView.tsx` を修正
  - `handleStartCapture()` に `bookTitle.trim() === ""` チェックを追加
  - 未入力時は `setError("書籍タイトルを入力してください")` を表示して早期 return
- ビルド確認
  - `cargo check`（src-tauri 内）: コンパイル成功（エラー0）
  - `npm run build`: フロントエンドビルド成功（tsc && vite build ともにエラーなし）
  - `npx tauri build`: リリースビルド + バンドル成功（Book Capture.app, dmg 生成）
- 2026-08-16 追加指摘（未対応、第2回実装で対応予定）
  1. ページ送りキーの SelectValue 表示が崩れる → `<SelectValue />`（auto-render）に修正
  2. ページ送りキー選択肢を「右矢印（→）」「左矢印（←）」のみに絞る → `space`/`arrow` 削除
  3. エラーメッセージを「連続キャプチャ開始」ボタンの右に移動
  4. トリミング領域を「ページ送りキー」「ページ待機時間」と横一列に配置。順序を「右・左・上・下」に変更。入力欄幅縮小
  5. 「先頭ページから」「現在ページから」スイッチ追加（capture.rs で逆方向ページ送りによる先頭復帰を実装）
- 2026-08-17 追加指摘反映（第2回実装）
  - 【ユーザー確認事項】先頭ページへの戻り方式：ページ送りキーの逆方向を連続入力
  - 上記5点の修正を実施完了
- `replace_in_file` で `capture.rs` 235行目の `>>>>+++ REPLACE` 残骸を削除（SEPARATOR記述ミスによる混入）
- `cd localapp/src-tauri && cargo check`: コンパイル成功（Finished dev profile）
- `cd localapp && npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- `>>>>+++ REPLACE` の混入原因: replace_in_file の SEARCH/REPLACE ブロック内に誤って SEPARATOR 文字列が含まれた
- 以後、replace_in_file 実行時に REPLACE 区切り文字が SEARCH/REPLACE ブロック内に含まれていないか二重確認する
- ブランチ: `feature/002008-2-profile-ui-fix`
- 2026-08-17: ユーザーテスト後のバグ修正（3点）
  1. 「先頭ページから」を選択しても先頭に戻らない（機能しない）
     - 原因: `captureStore.ts` の `invoke("start_continuous_capture")` で引数キーが camelCase (`startFromBeginning`) だったが、Rust 側コマンドの引数名は snake_case (`start_from_beginning`)
     - Tauri の `invoke` は引数名の自動変換を行わないため、キー名不一致で `start_from_beginning` が undefined 扱い（= false 相当）になっていた
     - 修正: `start_from_beginning: startFromBeginning` に変更
  2. 「Kindle for PC」エリアが初期表示で表示されない
     - 原因: `<SelectValue />` は auto-render 方式で `builtinProfiles` の `<SelectItem>` children に依存。非同期読み込み前は空配列なので表示テキストが解決できない
     - 修正: `selectedProfile` を `builtinProfiles.find()` で検索し、手動で `displayLabel` を計算して `<SelectValue>{displayLabel}</SelectValue>` に変更
       - `find` の結果がなくても `selectedProfileKey`（"kindle"）がフォールバック表示される
  3. 「先頭ページから」スイッチの配置位置を「連続キャプチャ」の右に変更
     - `CaptureView.tsx` の flex コンテナ内で [スイッチ] → [ボタン] の順を [ボタン] → [スイッチ] に入れ替え
- 修正後ビルド確認
  - `cargo check`: コンパイル成功（エラー0）
  - `npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- 2026-08-17: ProfileEditor.tsx レイアウト再構成（追加修正、ユーザー指示）
  - ページ送り設定とトリミング設定を視覚的に分離
  - ページ送りキー・待機時間を2列グリッドに配置（横一列6項目から分離）
  - トリミング設定に「取り込み画像トリミング」見出し（h4）を追加
  - トリミングの4辺入力を十字レイアウト（3列グリッド）に再配置
    - 上段中央: 「上 (px)」
    - 中段左/中央/右: 「左 (px)」 / 「枠」 / 「右 (px)」
    - 下段中央: 「下 (px)」
  - トリミング入力欄に `text-center` を追加し、数字を中央揃えに
  - トリミング説明文を `text-center` に変更
- Git コミット完了（002008-1/002008-2 統合コミット `34723f6`、main ブランチへ Fast-forward マージ済み）
