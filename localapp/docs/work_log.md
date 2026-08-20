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
  - フロントエンド表示確認: サイドバー「電子書籍」選択時に「キャプチャテスト」ボタンが正しく表示される
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
- ブランチ: `feature/002003-continuous-capture` → main にマージ（Fast-forward）
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
- ブランチ: `feature/002004-capture-folder-management`

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
  3. `localapp/src-tauri/src/lib.rs` — シグニチャ変更確認
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
  3. **ProfileEditor.tsx / select.tsx: SelectItem の `textValue` prop 対応 → Base UI 自動レンダリング方式に統合**
     - 原因: @base-ui/react/select の `SelectPrimitive.Item` が `textValue` prop を受け付けない型定義だった
     - 試行: `SelectItem` の型定義を拡張して `textValue` を追加 → JSX側で `<SelectPrimitive.Item textValue={textValue}>` を渡すも、依然として TypeScript エラー
     - 結論: Base UI の `SelectValue` は `SelectItemText` の children を自動認識するため、明示的な `textValue` は不要。呼び出し側（ProfileEditor.tsx）に `textValue` prop を追加しなくても日本語ラベルが正しく表示される
     - 修正: `select.tsx` は元の `...props` 方式に戻し、`ProfileEditor.tsx` は変更なしのままで正常動作
- `cargo check`: コンパイル成功（error 0）
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

## 005001 — ZIP アーカイブ化（Rust バックエンド）

### 【実施予定】

- 日時: 2026-08-18
- 目的: トリミング済み画像フォルダを ZIP アーカイブにまとめる Rust コマンドを実装する
- 前提:
  - feature/005001-zip-archiver ブランチを作成済み
  - reference/localapp/core/pdf_builder.py の画像→ファイル化ロジックを参考にする
  - `zip` crate は既に Cargo.toml に追加済み（002002 で追加）
- 変更内容:
  1. `localapp/src-tauri/src/commands/capture.rs` — `create_zip_archive` コマンド新規追加
     - `zip` crate の `ZipWriter` を使用して画像フォルダを ZIP 化
     - `.png` / `.jpg` / `.jpeg` をファイル名順にソートして格納（`pdf_builder.py` のパターンを踏襲）
     - `Deflate` 圧縮方式で ZIP エントリを追加
     - 20ファイルごとに `zip-progress` 進捗イベントを emit（`pdf_extractor.py` のコールバック方式を参考）
     - 完了後、出力ファイルパスを返却
  2. `localapp/src-tauri/src/lib.rs` — `invoke_handler` に `create_zip_archive` を登録
  3. `cargo check` / `npm run build` でビルド確認
- 実施コマンド:
  1. `cargo check`
  2. `npm run build`
- 想定される結果や注意点:
  - zip crate は既に Cargo.toml に追加済み（002002 scaffold 時に追加）
  - 画像ファイル以外は ZIP に含めない
  - 出力パスに拡張子がない場合は `.zip` を自動付与
  - 大規模フォルダでの非同期処理は将来検討（今回は同期的実装でシンプルに保つ）

### 【実施実績】

- `create_zip_archive` コマンドを `capture.rs` に追加
  - `ZipProgressPayload` struct を定義（`#[derive(Serialize, Clone)]`）
    - `current: usize`, `total: usize`, `message: String`
  - `create_zip_archive(app_handle, folderPath, outputPath)` コマンド
    - `folderPath` の存在確認、存在しなければエラー返却
    - 出力パスに `.zip` 拡張子がない場合は自動付与
    - `std::fs::read_dir()` でフォルダ内ファイルを列挙
    - `.png` / `.jpg` / `.jpeg` を小文字でフィルタ（`file_name.to_lowercase().ends_with(...)`）
    - `files.sort()` でファイル名順にソート
    - `ZipWriter::new(File::create(&output_path)?)` で ZIP ファイル作成
    - 各ファイルを `CompressionMethod::Deflated` でエントリ追加
    - 20ファイルごとに `app_handle.emit("zip-progress", payload)` で進捗通知
    - 完了後、出力ファイルパスを `String` で返却
- `lib.rs` に `commands::capture::create_zip_archive` を `invoke_handler` に登録
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- ブランチ: `feature/005001-zip-archiver`

---

## 005002 — 出力設定・ファイル名設定 UI

### 【実施予定】

- 日時: 2026-08-18
- 目的: ZIP 出力画面の UI を実装し、フォルダ選択ダイアログと ZIP 作成ボタンを追加する
- 前提:
  - 005001（ZIP アーカイブ化 Rust コマンド）が完了していること
  - feature/005002-export-ui ブランチを作成済み（005001 と連続して同一ブランチで実施）
- 変更内容:
  1. `tauri-plugin-dialog` を追加
     - `Cargo.toml`: `tauri-plugin-dialog = "2"`
     - `package.json`: `@tauri-apps/plugin-dialog`
     - `lib.rs`: `.plugin(tauri_plugin_dialog::init())`
     - `capabilities/default.json`: `dialog:allow-open` 権限
  2. `localapp/src/store/exportStore.ts` — Zustand ストア新規作成
  3. `localapp/src/views/ExportView.tsx` — ZIP 出力画面を完全書き換え
- 実施コマンド:
  1. `cargo add tauri-plugin-dialog@2`
  2. `npm install @tauri-apps/plugin-dialog`
  3. `cargo check`
  4. `npm run build`
- 想定される結果や注意点:
  - Tauri v2 の dialog plugin はフォルダ選択とファイル保存の両方をサポート
  - UI レイアウトは Apple HIG 風（白基調・余白多め・控えめな角丸）を維持

### 【実施実績】

- `tauri-plugin-dialog` を追加
  - `cd localapp/src-tauri && cargo add tauri-plugin-dialog@2` で `tauri-plugin-dialog = "2.7.2"` を追加
  - `cd localapp && npm install @tauri-apps/plugin-dialog` でフロントエンド依存を追加
  - `lib.rs` に `.plugin(tauri_plugin_dialog::init())` を追加
  - `capabilities/default.json` に `dialog:allow-open` 権限を追加
- `localapp/src/store/exportStore.ts` を新規作成
  - Zustand ストア: `sourceFolder`, `outputName`（デフォルト "images"）, `outputFolder`, `isCreating`, `progressMessage`, `resultPath`
  - `createZip()`: `invoke("create_zip_archive")` を呼び出し、`listen("zip-progress")` で進捗イベントを受信して `progressMessage` を更新
  - 完了後 `resultPath` に出力ファイルパスを保存
  - `reset()`: 出力設定を初期値に戻す（`sourceFolder` はリセットしない）
- `localapp/src/views/ExportView.tsx` を完全書き換え
  - ヘッダー: ZIP アイコン + 「ZIP 作成」タイトル + 説明文
  - 入力設定セクション: sourceFolder 表示、画像枚数表示
  - 出力設定セクション: 出力ファイル名 `<Input>`、出力先フォルダ選択ボタン（`tauri-plugin-dialog` の `open({ directory: true })`）
  - アクションエリア: ZIP 作成ボタン（disabled 条件: `!sourceFolder || !outputFolder || isCreating || imageCount === 0`）
  - 進捗メッセージ表示（`progressMessage`）
  - 完了後: 出力ファイルパス表示 + 「フォルダを開く」ボタン + リセットボタン
- `cargo check`: 成功（既存の non_snake_case warning 4 つのみ、今回の変更とは無関係）
- `npm run build`: 成功（tsc && vite build ともにエラーなし）
- 005002 と 005003 は同一ブランチ `feature/005001-zip-archiver` で連続実施

---

## 005003 — タブ間自動連携 + 入力フォルダ任意選択

### 【実施予定】

- 日時: 2026-08-18
- 目的: キャプチャタブと ZIP 出力タブの間でフォルダ情報を自動連携し、入力フォルダを任意に選択できるようにする
- 前提:
  - 005002（出力設定 UI）が完了していること
  - feature/005001-zip-archiver ブランチ上で実施（005002 と同一ブランチ）
- 変更内容:
  1. `ExportView.tsx` に `useEffect` で `captureStore.lastCaptureFolder` を監視し、自動的に `sourceFolder` に反映
  2. `sourceFolder` 変更時に `list_capture_images` で画像枚数を取得して表示
  3. 入力設定セクションにフォルダ選択ボタンを追加（ユーザー追加要望）
     - 未設定時は「選択」ボタン、設定済み時は「変更」ボタン
     - `tauri-plugin-dialog` の `open({ directory: true })` を使用
- 実施コマンド:
  1. `npm run build`
  2. `cargo check`
- 想定される結果や注意点:
  - `captureStore.lastCaptureFolder` は連続キャプチャ完了後に保存される
  - ユーザーがキャプチャタブを経由せずに ZIP 作成タブを開いた場合、手動でフォルダを選択できるようにする

### 【実施実績】

- タブ間自動連携を実装
  - `ExportView.tsx` に `useEffect` を追加: `captureStore.lastCaptureFolder` を監視し、変更時に `exportStore.setSourceFolder(lastCaptureFolder)` を実行
  - 連続キャプチャ完了後に ZIP 作成タブを開くと、入力フォルダが自動的に設定される
- 画像枚数取得
  - `sourceFolder` 変更時に `invoke("list_capture_images", { folderPath: sourceFolder })` を実行
  - 取得したファイル配列の `length` を `imageCount` state に保存
  - エラー時は `imageCount = 0`
- 入力フォルダ任意選択ボタンを追加（ユーザー要望）
  - `handleSelectSourceFolder()` 関数を新規追加
    - `open({ directory: true })` でフォルダ選択ダイアログを開く
    - 選択されたフォルダパスを `setSourceFolder(selected)` に設定
    - 画像枚数も即座に取得して表示される（`sourceFolder` useEffect がトリガーされる）
  - sourceFolder 未設定時: 「選択」ボタンを表示（フォルダパス表示エリアの横）
  - sourceFolder 設定済み時: 「変更」ボタンを表示（フォルダパス表示エリアの横）
  - これにより、キャプチャタブを経由せずに既存の画像フォルダから ZIP 作成が可能になった
- `npm run build`: 成功
- `cargo check`: 成功（non_snake_case warning は既存のもの）
- ブランチ: `feature/005001-zip-archiver`（005001〜005003 を同一ブランチで実施）

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

---

## 005001〜005003 — ZIP アーカイブ化・出力設定 UI・タブ間連携

### 【実施予定】

- 日時: 2026-08-18
- 目的: トリミング済み画像フォルダを ZIP アーカイブにまとめる機能を実装する
- 前提:
  - feature/005001-zip-archiver ブランチを作成済み
  - `zip` crate は既に Cargo.toml に追加済み（002002 scaffold 時）
- 変更内容:
  1. `localapp/src-tauri/src/commands/capture.rs` — `create_zip_archive` コマンド新規追加
  2. `localapp/src-tauri/src/lib.rs` — invoke_handler に登録
  3. `tauri-plugin-dialog` 追加（Cargo.toml, package.json, lib.rs, capabilities/default.json）
  4. `localapp/src/store/exportStore.ts` — Zustand ストア新規作成
  5. `localapp/src/views/ExportView.tsx` — ZIP 出力画面を完全書き換え
  6. タブ間連携: `captureStore.lastCaptureFolder` → `exportStore.sourceFolder` 自動反映
  7. ユーザー追加要望: 入力設定セクションに任意フォルダ選択ボタンを追加
- 実施コマンド:
  1. `cargo check`
  2. `npm run build`
  3. `npm run tauri dev`
- 想定される結果や注意点:
  - 画像ファイル以外は ZIP に含めない
  - 出力パスに拡張子がない場合は `.zip` を自動付与
  - `tauri-plugin-dialog` はフォルダ選択とファイル保存の両方をサポート

### 【実施実績】

- 005001: ZIP アーカイブ化（Rust バックエンド）
  - `capture.rs` に `create_zip_archive` コマンドを追加
    - `ZipWriter::new(File::create(output_path)?)` で ZIP ファイルを作成
    - `.png` / `.jpg` / `.jpeg` を小文字でフィルタ、ファイル名順に `sort()`
    - `CompressionMethod::Deflated` でエントリ追加
    - 20ファイルごとに `zip-progress` 進捗イベントを emit
    - 出力パスに `.zip` 拡張子がない場合は自動付与
  - `lib.rs` に `create_zip_archive` を `invoke_handler` に登録
  - `cargo check`: コンパイル成功（エラー0）
  - `npm run build`: ビルド成功

- 005002: 出力設定・ファイル名設定 UI
  - `tauri-plugin-dialog` を追加
    - `Cargo.toml`: `tauri-plugin-dialog = "2.7.2"`
    - `package.json`: `@tauri-apps/plugin-dialog`
    - `lib.rs`: `.plugin(tauri_plugin_dialog::init())`
    - `capabilities/default.json`: `dialog:allow-open` 権限
  - `localapp/src/store/exportStore.ts` を新規作成
    - Zustand ストア: `sourceFolder`, `outputName`, `outputFolder`, `isCreating`, `progressMessage`, `resultPath`
    - `createZip()`: `invoke("create_zip_archive")` + `listen("zip-progress")` で進捗受信
  - `localapp/src/views/ExportView.tsx` を完全書き換え
    - 入力設定セクション（sourceFolder 表示、画像枚数）
    - 出力設定セクション（outputName Input、outputFolder 選択ボタン）
    - ZIP 作成ボタン + 進捗メッセージ + 完了後結果表示 + 「フォルダを開く」ボタン
  - `cargo check`: 成功
  - `npm run build`: 成功

- 005003: タブ間自動連携 + 入力フォルダ任意選択
  - `ExportView.tsx` に `useEffect` で `captureStore.lastCaptureFolder` を監視
    - 連続キャプチャ完了後に ZIP 作成タブを開くと入力フォルダが自動設定される
  - `sourceFolder` 変更時に `list_capture_images` で画像枚数を取得して表示
  - 入力フォルダ任意選択ボタンを追加（ユーザー要望対応）
    - `handleSelectSourceFolder()` で `open({ directory: true })` を使用
    - sourceFolder 未設定時は「選択」ボタン、設定済み時は「変更」ボタン
  - `npm run build`: 成功
  - `cargo check`: 成功

- node_modules 破損修復
  - `npm run tauri dev` 起動時に Babel エラー `yield* (intermediate value) is not iterable` が発生
  - `rm -rf localapp/node_modules localapp/package-lock.json && cd localapp && npm install` で修復
  - `cd localapp/src-tauri && cargo clean` で Rust ビルドキャッシュをクリア
  - 修復後、`cargo check` / `npm run build` ともに成功

- Git コミット・マージ
  - ブランチ: `feature/005001-zip-archiver`
  - コミット: `715ec37` — 005001-005003: ZIP archive command, export UI, tab linkage, tauri-plugin-dialog folder selection
  - main ブランチへ Fast-forward マージ済み

---

## 004001 — 画像フォルダ読み込み・サムネイル一覧 UI

### 【実施予定】

- 日時: 2026-08-18
- 目的: トリミングタブで任意の画像フォルダを読み込み、サムネイル一覧を表示する
- 前提:
  - feature/004001-trim-thumbnails ブランチを作成済み
  - tauri-plugin-dialog は 005002 で追加済み
  - list_capture_images / get_capture_image コマンドは 002004 で実装済み
- 変更内容:
  1. `localapp/src/store/trimStore.ts` — 新規作成（Zustand ストア）
     - folderPath, imageFiles[], selectedImage を管理
     - loadFolder(): list_capture_images で画像一覧を取得
     - selectImage(): プレビュー対象画像を選択
  2. `localapp/src/views/TrimView.tsx` — 改修
     - 「フォルダを選択」ボタンを有効化（disabled 解除）
     - open({ directory: true }) でフォルダ選択ダイアログを開く
     - captureStore.lastCaptureFolder の自動引継ぎを維持
     - CaptureResultGallery を流用してサムネイルグリッド表示
       - トリミング画面用に拡張：選択中画像のハイライト表示
- 実施コマンド:
  1. `cargo check`
  2. `npm run build`
  3. `npm run tauri dev`
- 想定される結果や注意点:
  - フォルダ選択後に画像一覧が即座に表示されること
  - キャプチャタブからの引継ぎと手動選択の両方が正しく動作すること
  - CaptureResultGallery の選択状態は props で制御する

### 【実施実績】

- `localapp/src/store/trimStore.ts` を新規作成
  - Zustand ストア: `folderPath`, `imageFiles[]`, `selectedImage`, `currentImageIndex`, `cropInsets`
  - `loadFolder(folderPath)`: `list_capture_images` コマンドで画像一覧を取得
  - `prevPage()` / `nextPage()`: ページナビゲーション
- `localapp/src/views/TrimView.tsx` を改修
  - 「フォルダを選択」ボタンを有効化（`open({ directory: true })` でフォルダ選択ダイアログを開く）
  - `captureStore.lastCaptureFolder` の自動引継ぎを維持
  - `CaptureResultGallery` を流用してサムネイルグリッドを表示
  - 選択中画像のハイライト表示は未実装（004002 で Before/After プレビューに移行）
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- ブランチ: `feature/004001-trim-thumbnails`

## 004001 (追加) — トリミング入力欄の自由入力＋+/-ボタン実装

### 【実施予定】

- 日時: 2026-08-18
- 目的: 「トリミング」タブと「電子書籍」タブ双方のトリミング値入力欄で、0 削除問題を解消しつつ +/- ボタンも使えるようにする
- 前提:
  - feature/004001-trim-thumbnails ブランチにて実装
  - 前回の TrimView.tsx 改修では、0 削除ができるが +/- ボタンがない状態だった
- 変更内容:
  1. `localapp/src/views/TrimView.tsx` — `type="text" inputMode="numeric"` + onBlur 確定 + カスタム +/- ボタンを追加
  2. `localapp/src/components/capture/ProfileEditor.tsx` — 同様に変更。useState でローカル値を保持し、onBlur で Zustand ストアに確定。カスタム +/- ボタンを追加。
- 実施コマンド:
  1. `npm run build`
  2. `cargo check`
  3. `git add && git commit`
  4. `git merge feature/004001-trim-thumbnails`
- 想定される結果や注意点:
  - 0 削除問題: `type="number"` の実装では、onChange で parseInt → 0 に戻る問題があった。対策として `type="text" inputMode="numeric"` + ローカル state + onBlur で確定する方式を採用。
  - ProfileEditor.tsx では profile 自体が null の可能性があるため、guard clause でチェック
  - +/- ボタンの disabled は `(profile.cropInsets?.side ?? 0) <= 0` で判定

### 【実施実績】

- `localapp/src/views/TrimView.tsx`
  - `import { Minus, Plus }` を追加
  - `handleCropAdjust` 関数を新規追加（delta を加算/減算し、0 未満にクランプ）
  - 4 辺の Input 欄を `type="text" inputMode="numeric"` に変更し、横並びに `-` [入力] `+` ボタンを配置
  - Input 欄: `w-[56px]` に調整し、デザインを統一
- `localapp/src/components/capture/ProfileEditor.tsx`
  - `import { Minus, Plus }` と `useEffect` を追加
  - `cropInputs` ローカル state と `useEffect` 同期ロジックを追加
  - `handleCropInputChange`, `handleCropInputBlur`, `handleCropAdjust` 関数を新規追加
  - トリミング十字レイアウトの 4 辺すべてを `type="text" inputMode="numeric"` + `-` [入力] `+` ボタンに変更
  - `updateCustomProfile` を経由し、Zustand ストアに確定値を保存
- ビルド結果:
  - `npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
  - `cargo check`: コンパイル成功（既存の snake_case 警告 4 件のみ）
- Git:
  - コミット `a964a87`: 「004001: トリミング入力欄に自由入力＋+/-ボタンを実装」（TrimView.tsx）
  - コミット `dea345f`: 「004001: 電子書籍タブのトリミング入力欄に自由入力＋+/-ボタンを実装」（ProfileEditor.tsx）
  - main ブランチに fast-forward マージ完了
- ブランチ: `feature/004001-trim-thumbnails` → `main`

---

## 004002 — Before/After プレビュー表示

### 【実施予定】

- 日時: 2026-08-18
- 目的: オリジナル画像とトリミング後画像を左右に並列表示する
- 前提:
  - feature/004001-trim-thumbnails ブランチ上で実施
  - 004001（画像フォルダ読み込み・サムネイル一覧 UI）が完了していること
- 変更内容:
  1. `localapp/src/store/trimStore.ts` — `originalPreviewImage` state を追加
     - `loadPreview()`: `Promise.all` で `get_capture_image`（元画像）と `apply_crop_preview`（トリミング後）を並列取得
     - ページ切り替え時に両方のプレビューをリセット
  2. `localapp/src/views/TrimView.tsx` — 左右2列グリッドレイアウトに変更
     - 左側: Before（元画像）
     - 右側: After（トリミング後）
     - ナビゲーションボタンで両方の画像が同期して切り替わる
  3. `localapp/src-tauri/src/commands/capture.rs` — `apply_crop_preview` コマンドを新規追加
     - 画像ファイルを読み込み `DynamicImage::crop` でトリミング → PNGエンコード → Base64 返却
  4. `localapp/src-tauri/src/lib.rs` — `apply_crop_preview` を `invoke_handler` に登録
  5. 左右のプレビュー領域に1pxの純粋な青枠線（`border border-[#0000FF]`）を追加し、背景と区別しやすくする
- 実施コマンド:
  1. `cargo check`
  2. `npm run build`
- 想定される結果や注意点:
  - `apply_crop_preview` は `crop_imm` → `to_image` → PNG エンコード → Base64 の流れ
  - `invoke` の返り値型は Rust 側が `String`（Base64 直接返却）のため、`invoke<{ base64: string }>` ではなく `invoke<string>` とする
  - 青枠線はプレビュー背景とページ背景が同色の場合の境界認識を助けるため

### 【実施実績】

- `localapp/src/store/trimStore.ts`
  - `originalPreviewImage: string | null` state を追加（元画像表示用）
  - `loadPreview()`: `Promise.all` で `get_capture_image`（元画像）と `apply_crop_preview`（トリミング後）を並列取得
    - 型修正: `invoke<{ base64: string }>` → `invoke<string>`（Rust 側が `String` を直接返却）
  - `prevPage`, `nextPage`, `goToPage`, `loadFolder` でページ切り替え時に両方のプレビューを `null` にリセット
- `localapp/src/views/TrimView.tsx`
  - 左右2列グリッドレイアウト（`grid-cols-1 md:grid-cols-2`）に変更
  - 左側: Before（元画像）`originalPreviewImage` を表示
  - 右側: After（トリミング後）`previewImage` を表示
  - ナビゲーションボタン（前ページ / 次ページ）で両方の画像が同期して切り替わる
  - 両方のプレビュー領域に1pxの純粋な青枠線（`border border-[#0000FF]`）を追加
    - 理由: プレビューの背景色（`bg-muted/30`）とページ背景が同色の場合、画像の境界が判別しにくいため
- `localapp/src-tauri/src/commands/capture.rs`
  - `apply_crop_preview` コマンドを新規追加
    - 画像ファイルを `image::open()` で読み込み
    - `DynamicImage::crop()` でトリミング適用（`mut img` が必要）
    - PNG エンコード → Base64 返却
- `localapp/src-tauri/src/lib.rs`
  - `commands::capture::apply_crop_preview` を `invoke_handler` に登録
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- ブランチ: `feature/004001-trim-thumbnails`

---

## 003001〜003002 — PDF 読込（PDF 選択・設定 UI + PDF → 画像展開）

### 【実施予定】

- 日時: 2026-08-19
- 目的: 外部 PDF を画像化してトリミングタブに引き継ぐ
- 前提:
  - feature/003001-pdf-import ブランチを作成済み
  - `pdfium-render` crate は 001002 で追加済み
  - `tauri-plugin-dialog` は 005002 で追加済み
- 変更内容:
  1. PDFium `.dylib` ダウンロード・配置
     - macOS arm64 用の PDFium バイナリを公式リポジトリまたは `bblanchon/pdfium-binaries` から取得
     - `localapp/src-tauri/pdfium/` 配下に `libpdfium.dylib` を配置
     - 実行時に `PDFIUM_DYNAMIC_LIBRARY_PATH` 環境変数または `pdfium-render` の自動検出で読み込む
  2. `localapp/src/store/pdfImportStore.ts` — 新規作成（Zustand ストア）
     - `pdfPath`: 選択された PDF ファイルパス
     - `outputFolder`: 出力先フォルダパス
     - `dpi`: DPI 設定（200 / 300 / 400、デフォルト 300）
     - `pageCount`: PDF 総ページ数
     - `estimatedSize`: 推定ファイルサイズ
     - `isConverting`: 変換実行中フラグ
     - `progressMessage`: 進捗メッセージ
     - `setPdfPath()`, `setOutputFolder()`, `setDpi()`, `estimateSize()`, `startConversion()`, `reset()`
  3. `localapp/src/views/PdfImportView.tsx` — 既存ファイルを完全書き換え
     - PDF ファイル選択ボタン（`open({ directory: false })`）
     - 出力フォルダ表示・変更ボタン
     - DPI 選択セグメントコントロール（200 / 300 / 400）
     - ページ数・推定ファイルサイズ表示
     - 「PDF を画像化」ボタン
     - 進捗メッセージ表示
     - 完了後「トリミングへ進む」ボタン
  4. Rust 側コマンド実装
     - `localapp/src-tauri/src/commands/pdf.rs` — 新規作成
       - `extract_pdf_to_images(app_handle, pdfPath, outputFolder, dpi)` コマンド
       - `pdfium-render` で PDF を開き、各ページを PNG レンダリング
       - 10ページごとに `pdf-progress` イベントを emit
       - 出力フォルダが存在しなければ作成
       - 完了後、出力フォルダパスを返却
     - `localapp/src-tauri/src/commands/mod.rs` — `pub mod pdf;` を追加
     - `localapp/src-tauri/src/lib.rs` — `extract_pdf_to_images` を `invoke_handler` に登録
  5. トリミングタブへの自動引き継ぎ
     - 変換完了後、`trimStore.loadFolder(outputFolder)` を呼び出してトリミングタブに遷移
- 実施コマンド:
  1. PDFium `.dylib` ダウンロード・配置
  2. `cd localapp/src-tauri && cargo check`
  3. `cd localapp && npm run build`
  4. `cd localapp && npm run tauri dev`
- 想定される結果や注意点:
  - PDFium は動的ライブラリなので、配布時に `.dylib` をバンドルする必要がある（`tauri.conf.json` の `resources` で設定）
  - ファイルサイズ目安は「ページ幅×高さ（inch）× DPI² × 4（RGBA）」で概算。実際には PNG 圧縮で大幅に小さくなるため「目安」として表示
  - 大きな PDF の場合、メモリ消費に注意。バックグラウンドスレッドで実行し、進捗を定期的に通知する

### 【実施実績】

- 2026-08-20: 進捗インジケーター改善（ユーザー要望対応）
  - ユーザーから「PDFを画像化押下時からPDFのキャプチャーが終わるまで、進行を示すインジケーターを表示できないでしょうか」と指摘
  - 改善方針をユーザーに提示し承認を取得
  - `localapp/src/store/pdfImportStore.ts`
    - `progressMessage` state を追加
    - `extractPdf()` 開始時に `progressMessage: "PDFを読み込んでいます..."` を即座に設定
    - `setProgress()` で `payload.message` もストアに反映
  - `localapp/src/views/PdfImportView.tsx`
    - ボタン押下直後（`isLoading === true`）から進捗エリアを即表示
    - 回転スピナー + ステップメッセージを追加
    - ページ数が判明するまでは不定形プログレス（shimmer アニメーション）を表示
    - ページ数が判明したら確定的な進捗バーに切り替え（`5 / 120 ページ` + パーセント表示）
  - `localapp/src-tauri/src/commands/pdf.rs`
    - PDF オープン直後に `emit_progress(0)` を送信し、total ページ数を即座にフロントエンドに通知
    - 各ページのレンダリング・保存直後に進捗イベントを emit（10ページごとから毎ページに変更）
    - docstring の「10ページごとに進捗イベントを emit」という古い記述を修正
  - ビルド確認
    - `cd localapp/src-tauri && cargo check`: コンパイル成功（error 0）
    - `cd localapp && npm run build`: ビルド成功（tsc && vite build ともにエラーなし）

- `pdfium-render` crate による PDF → 画像展開コマンドを実装
  - `localapp/src-tauri/src/commands/pdf.rs` を新規作成
    - `extract_pdf_to_images(app_handle, pdf_path, output_folder, dpi)` コマンド
    - `Pdfium::bind_to_library()` で `localapp/src-tauri/pdfium/libpdfium.dylib` を動的読み込み
    - 各ページを `scale_page_by_factor(dpi / 72.0)` でレンダリングし PNG 保存
    - 10ページごとに `pdf-progress` イベントを emit
    - 出力フォルダが存在しない場合は `fs::create_dir_all()` で作成
  - `localapp/src-tauri/src/commands/mod.rs` に `pub mod pdf;` を追加
  - `localapp/src-tauri/src/lib.rs` に `commands::pdf::extract_pdf_to_images` を `invoke_handler` に登録
- フロントエンド PDF 読込 UI を実装
  - `localapp/src/store/pdfImportStore.ts` を新規作成
    - `pdfPath`, `outputFolder`, `dpi`, `pageCount`, `estimatedSize`, `isConverting`, `progressMessage` を管理
    - `estimateSize()`: ページサイズ・ページ数・DPI から概算ファイルサイズを計算
    - `startConversion()`: `invoke("extract_pdf_to_images")` を呼び出し、`listen("pdf-progress")` で進捗を受信
    - 変換完了後に `trimStore.loadFolder(outputFolder)` と `navigationStore.setView("trim")` で自動引き継ぎ
  - `localapp/src/views/PdfImportView.tsx` を完全書き換え
    - PDF ファイル選択ボタン（`open({ directory: false })`）
    - 出力フォルダ表示・変更ボタン
    - DPI セグメントコントロール（200 / 300 / 400、デフォルト 300）
    - ページ数・推定ファイルサイズ表示
    - 「PDF を画像化」ボタンと進捗メッセージ表示
    - 完了後「トリミングへ進む」ボタン
- 初回実装時の問題と修正
  - Rust コマンドの引数名を camelCase (`pdf_path`, `output_folder`) に統一
    - 原因: Tauri `invoke` は JS 側キー名と Rust 側引数名が完全一致する必要がある
    - 以前の snake_case 実装ではフロントエンド側で `pdfPath` / `outputFolder` を送信していたためマッチング失敗
- PDFium 動的ライブラリの配置
  - `localapp/src-tauri/pdfium/libpdfium.dylib` を配置（macOS arm64 用）
  - `tauri.conf.json` の `bundle.resources` に `"pdfium/libpdfium.dylib": "pdfium/libpdfium.dylib"` を追加し、アプリバンドル時に同梱
- ビルドエラー解消
  - `npm run build` で PostCSS / Tailwind CSS v4 関連のエラーが発生
    - `LazyResult.registerPostcss is not a function` など
  - 原因: Node.js v26.0.0 と PostCSS / Tailwind v4 の互換性問題、または `node_modules` の破損
  - 対策: `rm -rf localapp/node_modules localapp/package-lock.json && cd localapp && npm install` で再インストール
  - 対策後、`cd localapp && npm run build` が成功
- ビルド確認
  - `cd localapp/src-tauri && cargo check`: コンパイル成功（エラー0）
  - `cd localapp && npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- ブランチ: `feature/003001-pdf-import`

---

## 003002-1 — PDF 読込 進捗インジケーター表示不具合調査・修正

### 【実施予定】

- 日時: 2026-08-20
- 目的: ユーザーから報告された「PDF を画像化」ボタン押下後に進捗インジケーターが表示されない不具合を調査し、修正する
- 前提:
  - 003001〜003002（PDF 読込）の実装は完了している
  - ユーザーが `npm run tauri dev` で動作確認中に「インジケータがでません」とフィードバック
- 調査・変更内容:
  1. `localapp/src-tauri/src/commands/pdf.rs` — 同期コマンドのままでは JavaScript 側がブロッキングされる可能性を確認
  2. `localapp/src/store/pdfImportStore.ts` — `extractPdf()` の呼び出し方式を確認
  3. 必要に応じて:
     - Rust 側 `extract_pdf_to_images` を async コマンド + `tokio::task::spawn_blocking` に変更
     - フロントエンド側で `extractPdf` のコマンド呼び出しをマイクロタスクで実行
- 実施コマンド:
  1. `cd localapp/src-tauri && cargo check`
  2. `cd localapp && npm run build`
  3. `cd localapp && npm run tauri dev`
- 想定される結果や注意点:
  - Tauri の同期コマンド中はフロントエンドのメインスレッドがブロックされ、進捗イベントのリアルタイム受信ができない
  - React 18 の自動バッチングも state 更新のタイミングに影響を与える可能性がある
  - 修正後、ボタン押下直後に進捗エリアが表示され、`pdf-progress` イベントを受信しながら確定プログレスバーが更新される

### 【実施実績】

- 不具合症状の確認
  - ユーザー報告: 「PDF を画像化」ボタン押下後、ボタン文字は変わらず、進捗エリアも表示されない
  - PNG ファイル自体は正常に生成される（処理自体は動作）
  - コンソールエラーは出ていない
- 原因調査
  - Tauri の同期コマンド（`#[tauri::command]`）を呼び出すと、コマンドが完了するまで JavaScript 側のメインスレッドがブロッキングされる
  - その間、Rust 側から `pdf-progress` イベントが emit されても、WebView のメインスレッドがブロックされているため UI 更新が行われない
  - React 18 の自動バッチングにより、イベント受信後の state 更新がコマンド完了までまとめられる可能性もある
- 修正方針の決定
  - Rust 側: `extract_pdf_to_images` を async コマンドに変更し、実際の PDF レンダリング処理を `tokio::task::spawn_blocking` でバックグラウンドスレッドに委譲
  - フロントエンド側: `extractPdf()` 内で `invoke` をマイクロタスクに入れて呼び出し、メインスレッドを解放
- 関連タスク
  - 003002: PDF → 画像展開（Rust バックエンド）

---

## 003002-2 — PDF 読込 Pdfium 二重初期化エラー修正

### 【実施予定】

- 日時: 2026-08-20
- 目的: `extract_pdf_to_images` の async 化後に発生した `PdfiumLibraryBindingsAlreadyInitialized` エラーを修正する
- 前提:
  - 003002-1（進捗インジケーター表示不具合調査・修正）で `extract_pdf_to_images` を async コマンド + `tokio::task::spawn_blocking` に変更済み
  - ユーザーによる動作テストで `PdfiumLibraryBindingsAlreadyInitialized` エラーが発生した
- 調査・変更内容:
  1. `localapp/src-tauri/src/commands/pdf.rs` — エラー発生箇所の確認
  2. async 部での `Pdfium::bind_to_library()` / `Pdfium::new()` を削除
  3. すべての PDFium 処理を `spawn_blocking` 内に移動
- 実施コマンド:
  1. `cd localapp/src-tauri && cargo check`
  2. `cd localapp && npm run build`
  3. `cd localapp && npm run tauri dev`
- 想定される結果や注意点:
  - `pdfium-render` はプロセス内で `bind_to_library()` を1回のみ許可する
  - async 部と `spawn_blocking` 内の両方で初期化すると2重初期化エラーになる
  - ライブラリパス・PDF パス・DPI など必要な情報のみを `spawn_blocking` に渡す

### 【実施実績】

- エラー症状の確認
  - ユーザーによる動作テストで、`extract_pdf_to_images` 実行時に `PdfiumLibraryBindingsAlreadyInitialized` エラーが発生
  - PNG ファイルが生成されず、コマンドが失敗して返却される
- 原因調査
  - `pdfium-render` crate の内部実装を確認したところ、`Pdfium::bind_to_library()` はプロセス内で1回のみ呼び出し可能
  - 現行の `pdf.rs` は async 部で `Pdfium::bind_to_library()` → `Pdfium::new()` を行い、その後 `tokio::task::spawn_blocking` 内で再度 `bind_to_library()` を呼んでいた
  - この2重初期化が `PdfiumLibraryBindingsAlreadyInitialized` エラーの直接的原因
- 修正方針の決定
  - async 部での PDFium 初期化・PDF オープン・ページ数取得を完全に削除
  - async 部では入力ファイル確認・出力フォルダ作成・ライブラリパス解決のみを行う
  - `spawn_blocking` 内で PDFium 初期化 → PDF オープン → ページ数取得 → 進捗 emit(0) → レンダリング・保存 を一貫して実行
- 関連タスク
  - 003002: PDF → 画像展開（Rust バックエンド）
  - 003002-1: PDF 読込 進捗インジケーター表示不具合調査・修正

- ビルド確認
  - `cd localapp/src-tauri && cargo check`: コンパイル成功（error 0、既存の non_snake_case 警告4件のみ）
  - `cd localapp && npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- 2026-08-20: タイムアウトエラー対応（ページ 6 の保存失敗: Operation timed out (os error 60)）
  - 事象: `extract_pdf_to_images` 実行中、6ページ目の PNG 保存で「ページ6の保存に失敗しました: Operation timed out (os error 60)」エラーが発生
  - 原因: `image.save()` 実行時に macOS で一時的なファイルシステムタイムアウト（`ETIMEDOUT`）が発生。画像サイズが大きいページやクラウド同期フォルダ・外部ストレージへの書き込み時に発生しやすい
  - 対応: `localapp/src-tauri/src/commands/pdf.rs` の PNG 保存処理にリトライ機構を追加
    - 最大3回試行（初回 + 再試行2回）
    - 失敗時は1秒待機してから再試行
    - すべての試行が失敗した場合、試行回数・ファイルパスを含む詳細なエラーメッセージを返却
    - コメントでリトライの理由（macOS での一時タイムアウト）を明記
  - 注意点: `spawn_blocking` 自体にデフォルトタイムアウトは存在しないため、タイムアウトは `image.save()` → macOS ファイルシステムの書き込み処理で発生したと判断
- ビルド確認
  - `cd localapp/src-tauri && cargo check`: コンパイル成功（error 0、既存の non_snake_case 警告4件のみ）
  - `cd localapp && npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- 次のステップ
  - ユーザーによる動作テストを実施し、合格判定を得る
  - 合格後、Git コミット・main ブランチマージ・タスク完了記録を実施

