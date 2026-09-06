# localapp タスク管理表

本ファイルは、localapp のタスクを追記型で管理するものです。
将来の課題も含め、すべて必ず実装することを前提としています。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する
- タスク No は「モジュール識別子（2文字）＋ ユースケースNo（3桁）＋ 通番（3桁）」とする
  - 識別子 `LA` は localapp、`SY` は System/全体設計・仕様等を表す
  - 例：ユースケース001の1番目のタスク → `LA001001`
- 通番は各ユースケース内で 001 から連番で振る

---

## ユースケースNo | LA001

ユースケース
Tauri v2 プロジェクト初期化

電子書籍キャプチャ・トリミング・ZIP 出力アプリの土台となる、Tauri v2 + React + Vite プロジェクトを構築する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| LA001001 | Tauri v2 + React + Vite プロジェクト scaffold 作成 | 2026-08-15 | 2026-08-15 | 実装 |
| LA001002 | Rust 側依存クレートの選定・追加 | 2026-08-15 | 2026-08-15 | 実装 |
| LA001003 | frontend 側依存の選定・追加 | 2026-08-15 | 2026-08-15 | 実装 |
| LA001004 | 開発・ビルド環境整備（tauri.conf.json / scripts 等） | 2026-08-15 | 2026-08-15 | 実装 |

### LA001001 Tauri v2 + React + Vite プロジェクト scaffold 作成

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

### LA001002 Rust 側依存クレートの選定・追加

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

### LA001003 frontend 側依存の選定・追加

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

### LA001004 開発・ビルド環境整備（tauri.conf.json / scripts 等）

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

## ユースケースNo | LA002

ユースケース
画面キャプチャ

電子書籍リーダー画面を検出し、連続してキャプチャして画像フォルダに保存する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| LA002001 | 画面キャプチャ方式調査・実装 | 2026-08-15 | 2026-08-16 | 調査/実装 |
| LA002002 | アプリプロファイル管理 UI | 2026-08-15 | 2026-08-16 | 実装 |
| LA002003 | 連続キャプチャ実行・進捗表示 | 2026-08-15 | 2026-08-16 | 実装 |
| LA002004 | キャプチャ画像のフォルダ管理 | 2026-08-15 | 2026-08-16 | 実装 |
| LA002005 | ウィンドウ指定キャプチャ＋コンテンツ領域自動トリミング | 2026-08-16 | 2026-08-17 | 実装（002008に統合） |
| LA002007 | ウィンドウ指定キャプチャ実装のコンパイルエラー修正 | 2026-08-16 | 2026-08-16 | 不具合修正 |
| LA002008 | ウィンドウ指定キャプチャ実装（xcap crate 版） | 2026-08-16 | 2026-08-17 | 実装 |
| LA002008-1 | 連続キャプチャバグ修正（MSE計算 & 最前面化） | 2026-08-16 | 2026-08-16 | 不具合修正 |
| LA002008-2 | プロファイルUI改善（デフォルト選択・表示・バリデーション） | 2026-08-16 | 2026-08-17 | 改善 |
| LA002008-3 | 連続キャプチャ途中完了バグ修正（MSE同一ページ判定の猶予） | 2026-08-20 | 2026-08-20 | 不具合修正 |
| LA002009 | 連続キャプチャの出力フォルダ指定とトリミング画面への引継ぎ | 2026-08-20 | 2026-08-21 | 実装 |

### LA002001 画面キャプチャ方式調査・実装

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

### LA002002 アプリプロファイル管理 UI

【計画】
- LA002001 で追加した `CaptureView.tsx` にプロファイル選択セレクタを追加
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
- ブランチ: `feature/LA002002-profile-management`

### LA002003 連続キャプチャ実行・進捗表示

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
   - 連続キャプチャ中にアプリを閉じた場合のクリーンアップについては、将来のタスク（LA007001 設定永続化等）で検討
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
- ブランチ: `feature/LA002003-continuous-capture` → main にマージ（Fast-forward）
- コミット: `3bce557` — LA002003: 連続キャプチャ実行・進捗表示 UI 実装

### LA002004 キャプチャ画像のフォルダ管理

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
- ブランチ: `feature/LA002004-capture-folder-management`

### LA002005 ウィンドウ指定キャプチャ＋コンテンツ領域自動トリミング

【計画】

1. **プロファイルにトリミングパラメータ追加**
   - `CaptureProfile` に `crop_insets: Insets { top, right, bottom, left }` を追加
   - Kindle for Mac 用デフォルト値: top=42, right=0, bottom=0, left=0（メニューバー分）
   - `ProfileEditor.tsx` にトリミング値編集UIを追加
   - 他プロファイルは0でデフォルト（既存動作維持）

2. **Rust側: ウィンドウ指定キャプチャ＋トリミング**
   - `use screenshots::Window;` を追加
   - `capture_by_window_title(keyword: &str) -> Result<DynamicImage, String>` 新規実装
   - `Window::all()` でウィンドウ一覧取得 → `title.to_lowercase().contains(keyword)` で部分一致
   - 一致したウィンドウを `capture()` でキャプチャ
   - 一致しなければ `Screen::all()[0].capture()` で全画面にフォールバック
   - `capture_screen()` / `capture_screen_raw()` を `profile: CaptureProfile` を受け取るよう変更
   - キャプチャ後、`crop_insets` を適用して `image::imageops::crop` で切り出し
   - トリミング値が画像範囲を超える場合は自動調整（バリデーション）

3. **シグネチャ変更**
   - `capture_screen(profile: CaptureProfile) -> Result<CaptureResult, String>`
   - `capture_screen_raw(profile: CaptureProfile) -> Result<Vec<u8>, String>`
   - `lib.rs` の `invoke_handler` は変更不要（プロファイルはTauriが自動シリアライズ）

4. **フロントエンド連携**
   - `CaptureView.tsx` の `invoke("capture_screen")` を `invoke("capture_screen", { profile: effectiveProfile })` に変更
   - `start_continuous_capture` は既に `profile` を渡しているため変更不要
   - `ProfileEditor.tsx` にトリミングオフセットの数値入力欄を追加

5. **ビルド・動作確認**
   - `cargo check` → `npm run build` → `npm run tauri dev`
   - Kindle for Mac を開いた状態でキャプチャテスト
   - 書籍コンテンツ部分だけがキャプチャされることを確認（外枠なし）

6. **想定される注意点**
   - `crop_insets` の値は macOS / Windows で異なる可能性がある
   - ユーザーが Kindle アプリの UI レイアウト変更（フルスクリーン等）した場合、トリミング値の調整が必要
   - トリミング後の画像が0pxにならないようバリデーション必須
   - ウィンドウ検索で `to_lowercase()` して大小文字を区別しない

【実施結果】
- 2026-08-16: 実装途中で2つのコンパイルエラーが発生
  1. `use screenshots::Window` → `Window` struct が `screenshots` v0.8.10 でエクスポートされていない
  2. `crop_imm().as_flat_samples()` → `SubImage` に `as_flat_samples()` メソッドが存在しない
- エラー修正は LA002007 として別タスクで対応
- LA002005 の実装内容（ウィンドウ指定キャプチャ＋コンテンツ領域自動トリミング）は LA002008（xcap crate 版）に引き継がれた
- LA002005 と LA002008 の重複解消: LA002005 は LA002007 で全画面キャプチャ + `crop_insets` トリミングに後退し、ウィンドウ指定キャプチャの機能は LA002008 で完全実装された。`crop_insets` 機能自体は LA002007/LA002008 双方で使用されており、LA002005 の計画は実質的に LA002008 に統合されたと判断する

### LA002007 ウィンドウ指定キャプチャ実装のコンパイルエラー修正

【計画】
1. `use screenshots::Window` を削除（`Window` struct は `screenshots` v0.8.10 で存在しない）
2. `capture_by_window_title` 関数を削除（ウィンドウ名検索は現時点で `screenshots` crate では不可）
3. `capture_screen_raw` をシンプル化し、全画面キャプチャ取得後に `crop_insets` でトリミングする方式に統一
4. `apply_crop_insets` で `cropped.as_flat_samples().samples` → `cropped.to_image().as_raw()` に修正（`SubImage` → `ImageBuffer` 変換）
5. `cargo check` でエラー0を確認
6. `npm run build` でフロントエンドビルド確認
7. 【002005の備考】`screenshots` crate でのウィンドウ指定キャプチャは将来 AppleScript 等で拡張を検討

【実施結果】
- `localapp/src-tauri/src/commands/capture.rs`
  - `use screenshots::{Screen, Window};` → `use screenshots::Screen;` に修正
  - `capture_by_window_title` 関数を削除（308〜346行）
  - `capture_screen_raw` をシンプル化：全画面キャプチャ + 任意 crop_insets トリミングに統一
  - `apply_crop_insets` の修正：`cropped.as_flat_samples().samples` → `cropped.to_image().as_raw()`
    - `SubImage<&RgbaImage>` は `as_flat_samples()` を持たない
    - `to_image()` で `ImageBuffer<Rgba<u8>, Vec<u8>>` に変換 → `as_raw()` で `&Vec<u8>` を取得
  - 【LA002005/LA002007】ウィンドウ指定キャプチャについて：将来 AppleScript / xcap crate 等で拡張を検討する旨をコメントで明記
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功（`tsc && vite build` ともにエラーなし）
- ブランチ: `feature/LA002007-window-capture-compile-fix` → main にマージ（Fast-forward）
- コミット: `ddd048b`

### LA002008 ウィンドウ指定キャプチャ実装（xcap crate 版）

【計画】
1. `localapp/src-tauri/Cargo.toml` — `screenshots` を削除、`xcap = "0.3"` を追加
2. `localapp/src-tauri/src/commands/capture.rs` — xcap 版に完全書き換え
   - `use xcap::Window;` に変更
   - `capture_window_image(profile)` — 新規関数：ウィンドウタイトル部分一致 → プロセス名フィルタ → `window.capture_image()`
   - ウィンドウが見つからない場合はエラー返却（利用可能ウィンドウ一覧を含む）
   - `window_title_keyword` が空の場合は全画面キャプチャにフォールバック
   - `capture_screen_raw()` — `capture_window_image()` を呼び出し、PNG エンコード + crop_insets 適用
3. `localapp/src-tauri/src/lib.rs` — シグニチャ変更確認（変更なし）
4. フロントエンド — 変更なし（プロファイル渡しは既存のまま）
5. `cargo check` → `npm run build` → `npm run tauri dev` で動作確認

【実施結果】
- `localapp/src-tauri/Cargo.toml`
  - `cargo remove screenshots` で `screenshots` crate を削除
  - `cargo add xcap` で `xcap = "0.3.3"` を追加
- `localapp/src-tauri/src/commands/capture.rs`
  - `use xcap::Window;` に変更（`screenshots::Screen` を削除）
  - `capture_window_image(profile)` を新規実装
    - `Window::all()` で全ウィンドウ列挙 → タイトル部分一致（`to_lowercase().contains(keyword_lower)`）
    - プロセス名フィルタ：`.exe` 拡張子を除去、`contains()` で部分一致（macOS/Windows 互換）
    - マッチしたウィンドウを `.capture_image()` でキャプチャ（返り値: `image::RgbaImage`）
    - マッチしない場合：エラーメッセージに利用可能ウィンドウ一覧を付与して返却
    - `window_title_keyword` が空の場合：全画面キャプチャにフォールバック（既存動作維持）
  - `capture_screen_raw()` を更新：PNG エンコード前に `capture_window_image()` を呼び出す
  - `apply_crop_insets()` を更新：`crop_imm().to_image().as_raw()` の形式に変更
- 初回テストで Kindle プロファイルの `process_name: "Kindle.exe"` が macOS の `"Kindle"` とマッチしない問題を発見
  - `.trim_end_matches(".exe")` で `.exe` 拡張子を除去する対処を実装
  - `==` から `contains()` に変更して部分一致に対応
- 単発キャプチャテスト（「キャプチャテスト」ボタン）で Kindle ウィンドウのキャプチャに成功
  - Kindle ウィンドウのみがキャプチャされ、外枠が除外されることを確認
- **バグ発見（後続対応予定）**：
  1. 連続キャプチャで1ページしかキャプチャできない（`calculate_mse()` が PNG 圧縮バイト列を比較しているため、ウィンドウキャプチャ後の画像サイズ縮小で MSE < 閾値と誤判定）
  2. 「キャプチャ前に最前面へ持ってくる」が機能しない（`use_bring_to_top: true` フラグがあるが `run_continuous_capture_loop()` に実装がない）
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功
- ブランチ: `feature/LA002008-window-capture-xcap`

### LA002008-1 連続キャプチャバグ修正（MSE計算 & 最前面化）【バグ対応】

【計画】
1. **Bug 1: MSE計算修正**
   - **原因**: `calculate_mse(prev: &[u8], curr: &[u8])` は PNG 圧縮後のバイト列を比較。ウィンドウキャプチャに切り替えたことで画像サイズが縮小し、PNG バイト列の差分が閾値 1000.0 を下回るようになった。これにより「ページ変更なし」と誤判定され連続キャプチャが 1 ページで停止する。
   - **修正案**:
     - `calculate_mse()` のシグネチャを変更: `calculate_mse(prev: &RgbaImage, curr: &RgbaImage) -> f64`
     - ピクセルレベルで RGBA 各チャネルの差分を計算: `(r1−r2)² + (g1−g2)² + (b1−b2)² + (a1−a2)²` の画素数での平均
     - 呼び出し元（`run_continuous_capture_loop`）で `capture_window_image()` の返り値（`RgbaImage`）をそのまま渡すよう変更。これにより PNG エンコード→デコードの無駄も削減できる。
     - MSE 閾値は 1000.0 を維持（フルHD画面での経験値。ウィンドウサイズ変更後の実測で調整が必要なら追記する）。

2. **Bug 2: 最前面化実装**
   - **原因**: `CaptureProfile` に `use_bring_to_top: bool` フィールドはあるが、`run_continuous_capture_loop()` 内で参照・実行されていない。
   - **修正案**:
     - `bring_window_to_front(profile: &CaptureProfile) -> Result<(), String>` 関数を新規作成
     - macOS 実装: `std::process::Command` で `osascript` を実行
       ```applescript
       tell application "System Events" to set frontmost of process "Kindle" to true
       ```
       プロセス名は `profile.process_name` から `.exe` を除去した値を使用する。
     - Windows 実装: `SetForegroundWindow` API または `enigo` の代替機能を検討。当面は `#[cfg(target_os = "macos")]` と `#[cfg(target_os = "windows")]` で分岐し、Windows は TODO コメントを残す。
     - `run_continuous_capture_loop()` のキャプチャ前に、`profile.use_bring_to_top && !profile.window_title_keyword.is_empty()` の場合のみ呼び出し
     - 最前面化後、500ms の待機を入れる（ウィンドウが前面に来るまでの猶予）

3. **ビルド・動作確認**
   - `cargo check` → `npm run build` → `npm run tauri dev`
   - Kindle for Mac を開いた状態で連続キャプチャテスト（10ページ程度）
   - 最前面化フラグ ON/OFF の両方で動作確認

4. **想定される注意点**
   - macOS で `osascript` の実行に Accessibility 権限が必要になる場合がある
   - ウィンドウタイトルがない（`window_title_keyword` が空）の場合は最前面化をスキップ（全画面キャプチャ時に他のアプリを最前面に持ってくる意味がないため）
   - `enigo` crate が既に依存にあり、`SetForegroundWindow` の代替機能があればそちらを利用してもよい

【実施結果】
- 2026-08-16: Bug 1 を修正
  - `calculate_mse()` のシグネチャを変更：`fn calculate_mse(prev: &RgbaImage, curr: &RgbaImage) -> f64`
  - ピクセルレベルで RGBA 各チャネルの差分を計算：`(r1−r2)² + (g1−g2)² + (b1−b2)² + (a1−a2)²` の画素数での平均
  - `run_continuous_capture_loop` で `capture_window_image()` の返り値（`RgbaImage`）をそのまま渡すよう変更。PNG エンコード→デコードの無駄を削減
  - MSE 閾値は 1000.0 を維持
- 2026-08-16: Bug 2 を修正
  - `bring_window_to_front(profile: &CaptureProfile) -> Result<(), String>` 関数を新規作成
  - macOS: `osascript` で `System Events` 経由にプロセスの `frontmost` を設定
    ```applescript
    tell application "System Events" to set frontmost of process "Kindle" to true
    ```
  - `run_continuous_capture_loop()` のキャプチャ前に常に実行（xcap では非最前面ウィンドウがキャプチャ不可のため `use_bring_to_top` フラグは削除）
  - 最前面化後の待機時間を 500ms → 1500ms に延長
- `capture_window_image()` にリトライ機構（最大3回、500ms間隔）を追加
  - 「Failed to copy data」エラー時に自動リトライし成功するケースあり
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功
- **手動テスト結果（2026-08-16）**: 連続キャプチャで Kindle for Mac が最前面に来て、複数ページ取得に成功
  - 以下の追加修正点が発見された（未対応）：
    1. 「クリック位置」は未実装機能なので廃止すべき
    2. プロファイルのデフォルト値を "kindle" に固定すべき
    3. 「ページ送りキー」が変更できない（デフォルト値表示も "right" ではなく "右矢印（→）" のように選択リストと同じ文言にすべき）
    4. 「ウィンドウタイトルキーワード」はビルトインプロファイルでは変更不可なので表示不要
    5. 「プロセス名」はビルトインプロファイルでは変更不可なので表示不要、デフォルト値を "Kindle.exe" → "Kindle" に変更すべき
- `.clinerules` に「コミット前にユーザーのテストと合格判定が必須」を追記
- ブランチ: `feature/LA002008-1-bug-fix`
- 2026-08-17: ユーザーテストで発見された追加バグの修正（第2回修正）
  - **先頭ページ復帰処理の書き換え（MSE差分検出方式）**
    - 原因: 固定200回逆方向ページ送りでは「先頭到達」を検出できない。ユーザー指摘: 「200回の根拠はなんですか？本来は先頭ページに到達するまでが正解です」
    - 修正: capture.rs の先頭復帰処理を完全書き換え
      - `bring_window_to_front` を先頭復帰の「前」に実行（キー入力が確実に届くようフォーカスを当てる）
      - スクリーンショットを撮りながら逆方向ページ送りを繰り返すループ
      - `calculate_mse(prev, curr)` で前回画像と比較。MSE < 50.0 で「これ以上逆方向にページを変更できない（＝先頭到達）」と判定
      - 最大200回の安全上限、20ページごとに進捗イベントをemit
  - **profileStore.ts: builtinProfiles.processName の修正**
    - 原因: `processName: ""`（空文字）で `bring_window_to_front` の osascript が機能しない
    - 修正: `processName: "Kindle"` に変更（Kindle for Mac のプロセス名）
  - **ProfileEditor.tsx / select.tsx: SelectItem textValue 対応 → 不要と判断**
    - Base UI の `SelectPrimitive.Item` が `textValue` prop を受け付けない型定義だった
    - `SelectItem` コンポーネントの型拡張 → JSX 側渡しを試みたが依然 TypeScript エラー
    - 結論: Base UI の `SelectValue` は `SelectItemText` の children を自動認識するため、明示的な `textValue` は不要。呼び出し側に `textValue` を追加せずとも日本語ラベルが正しく表示される
    - 実際: `select.tsx` は元の `...props` 方式に戻し、`ProfileEditor.tsx` は変更なしで正常動作
- `cargo check`: コンパイル成功（error 0）
- `npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- **Git コミットは未実施（ユーザーの合格確認待ち）**

### LA002008-2 プロファイルUI改善（デフォルト選択・表示・バリデーション）

【計画】
1. **デフォルトプロファイル選択を "kindle" に固定**
   - `localapp/src/store/profileStore.ts` — `selectedProfileKey` の初期値を `null` → `"kindle"` に変更
   - これにより起動時に「プロファイルを選択」placeholder の代わりに「Kindle」が即座に選択される
2. **ページ送りキーの SelectValue を日本語表示に変更（base-ui auto-render方式）**
   - `localapp/src/components/capture/ProfileEditor.tsx` — `pageTurnKeyLabelMap` 定数を削除
   - `<SelectValue>{...}</SelectValue>` を `<SelectValue />` に変更（base-ui の自動レンダリングに任せる）
   - SelectItem から `space` / `arrow` を削除し、「右矢印（→）」「左矢印（←）」のみに絞り込み
3. **ページ送り待機時間を数値入力から Select に変更**
   - `localapp/src/components/capture/ProfileEditor.tsx` — `<Input type="number">` を `<Select>` に変更
   - 選択肢は固定値：0.15 / 0.20 / 0.25 / 0.30（秒）
   - `pageWait` の型は float のまま維持（parseFloat で変換）
4. **書籍タイトルバリデーションを追加**
   - `localapp/src/views/CaptureView.tsx` — `handleStartCapture()` に `bookTitle.trim() === ""` チェックを追加
   - 未入力または空白のみの場合は `setError("書籍タイトルを入力してください")` を表示して早期 return
5. **エラーメッセージをボタンの右に移動**
   - `localapp/src/views/CaptureView.tsx` — エラーメッセージの表示位置を変更
   - 連続キャプチャ開始/停止ボタンと同じ flex コンテナ内に配置し、ボタンの右横に表示
6. **「先頭ページから」「現在ページから」スイッチを追加**
   - `localapp/src/views/CaptureView.tsx` — 書籍タイトル入力欄の右にラジオボタンまたは Select スイッチを配置
   - 状態 `startFromBeginning: boolean` を `useState` で管理
   - 「先頭ページから」選択時：連続キャプチャ開始前に先頭ページまでページ送りキーの逆方向を連続入力して復帰
   - 先頭復帰処理: `capture.rs` の `run_continuous_capture_loop` 内で `page_turn_reverse()` を実装し、開始前に一定回数（例: 200回）の逆方向ページ送りを実行
7. **プロファイルエディタのレイアウト変更**
   - `localapp/src/components/capture/ProfileEditor.tsx` — 「ページ送りキー」「ページ待機時間」「コンテンツ領域トリミング」を横一列に配置
   - トリミングの順序を「上・右・下・左」→「右・左・上・下」に変更
   - 各トリミング入力欄の横幅を数字4桁が入る程度（`max-w-[80px]` 等）に縮小
8. **ビルド確認**
   - `cargo check`（Rust コンパイル確認）
   - `npm run build`（フロントエンドビルド確認）
   - `npx tauri build`（リリースビルド + バンドル確認）

【実施結果】
- `profileStore.ts` の修正
  - `selectedProfileKey` の初期値を `null` → `"kindle"` に変更
  - これにより起動時に「プロファイルを選択」ではなく「Kindle」が即座に選択される
- `ProfileEditor.tsx` の修正（第1回実装）
  - `pageTurnKeyLabelMap` 定数を新規追加（right→右矢印（→）, left→左矢印（←）, space→スペース, arrow→矢印キー（左右））
  - `<SelectValue />` を `<SelectValue>{pageTurnKeyLabelMap[...]}</SelectValue>` に変更
  - ページ送り待機時間を `<Input type="number">` から `<Select>` に変更。選択肢は 0.15 / 0.20 / 0.25 / 0.30
  - 不要になった `localPageWait` useState / useEffect を削除
  - `useState`, `useEffect` の import も同時に削除
- `CaptureView.tsx` の修正（第1回実装）
  - `handleStartCapture()` に `bookTitle.trim() === ""` チェックを追加
  - 未入力時は `setError("書籍タイトルを入力してください")` を表示して早期 return
- 第2回実装（2026-08-17）
  1. SelectValue 表示バグ修正
     - `pageTurnKeyLabelMap` を完全に削除
     - `<SelectValue />`（auto-render方式）に変更。base-ui の自動レンダリングで SelectItem の children テキストが正しく表示される
  2. ページ送りキー選択肢を2項目に絞り込み
     - SelectItem から `space` / `arrow` を削除
     - 「右矢印（→）」「左矢印（←）」のみに変更
  3. エラーメッセージをボタンの右に移動
     - `CaptureView.tsx` で連続キャプチャ開始/停止ボタンと同じ flex コンテナ内に `{error && <span>...>}` を配置
     - ボタン群の下にあった独立したエラーブロックを削除
  4. 「先頭ページから」「現在ページから」スイッチ追加
     - `CaptureView.tsx` に `startFromBeginning` state を追加
     - `Switch` + `Label` で「先頭ページから」「現在ページから」を表示
     - `startCapture` に第3引数 `startFromBeginning` を追加
  5. トリミング項目を横一列に配置
     - `ProfileEditor.tsx` のレイアウトを `grid-cols-6` に変更
     - 順序を「右・左・上・下」に変更
     - 各 `<Input>` に `className="max-w-[80px]"` を追加
  6. `capture.rs` で先頭ページ復帰処理実装
     - `run_continuous_capture_loop` に `start_from_beginning: bool` 引数を追加
     - ループ開始前に `turn_page_reverse()` を200回連続実行
     - 20ページごとに進捗イベントを emit
     - 完了後 500ms 待機
  7. `turn_page_reverse()` 関数を新規追加
     - `turn_page()` の逆方向キーを入力（RightArrow ↔ LeftArrow）
- ビルド確認
- `cargo check`: コンパイル成功（`>>>>+++ REPLACE` 混入によるエラーを修正後、エラー0）
- `npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- 2026-08-17: ユーザーテスト結果とバグ修正（3点）
  - テスト結果: ユーザーにテストしてもらい、3点の指摘が発見された
    1. 「先頭ページから」を選択しても、一旦先頭まで戻ってからキャプチャ開始しない
       - 原因: `captureStore.ts` の `invoke("start_continuous_capture", { ... })` でキー名が camelCase (`startFromBeginning`) になっていた
       - Tauri の `invoke` は JS 側のオブジェクトキー名と Rust 側の引数名が**完全一致**する必要がある（自動変換は行われない）
       - Rust 側の引数名は snake_case (`start_from_beginning`) のため、マッピングに失敗して常にデフォルト値（false 相当）として処理されていた
       - 修正: `start_from_beginning: startFromBeginning` に変更
    2. 「Kindle for PC」と書いてあるエリア（ProfileSelector の初期表示）が初期表示で表示されなくなった
       - 原因: `<SelectValue />`（base-ui の auto-render 方式）は `builtinProfiles` 内の対応する `<SelectItem>` の children を自動で探す
       - `fetchProfiles()` が非同期のため初期レンダリング時は `builtinProfiles` が空配列で `SelectItem` が存在せず、placeholder のままになっていた
       - 修正: `selectedProfile = builtinProfiles.find((p) => p.key === selectedProfileKey)` で該当プロファイルを探し、`selectedProfile?.name ?? selectedProfileKey` を `<SelectValue>` の children として手動で渡す
         - 読み込み前は `selectedProfileKey` の値（"kindle"）が表示され、読み込み後は正しい日本語名に切り替わる
    3. 「先頭ページから」スイッチの配置位置が「連続キャプチャ開始」ボタンの左になっている
       - ユーザー要求: スイッチは「連続キャプチャ」の右に配置すること
       - 修正: `CaptureView.tsx` の flex コンテナ内で [スイッチ] → [ボタン] の順を [ボタン] → [スイッチ] に入れ替え
  - 修正後のビルド確認
    - `cargo check`: コンパイル成功（エラー0）
    - `npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
  - 2026-08-17: ProfileEditor.tsx レイアウト再構成（追加修正）
    - 「ページ送りキー」「ページ送り待機時間（秒）」を2列グリッド（`grid-cols-2`）に配置
    - トリミング設定を「取り込み画像トリミング」見出し付きの独立セクションに分離
    - トリミング入力を十字レイアウト（3列グリッド）に再配置
      - Row 1: 空 | 「上 (px)」入力欄 | 空
      - Row 2: 「左 (px)」入力欄 | 中央に「枠」表示 | 「右 (px)」入力欄
      - Row 3: 空 | 「下 (px)」入力欄 | 空
    - 各トリミング入力に `text-center` を追加（中央揃え）
    - トリミング説明文を `text-center` に変更
    - `cargo check`: コンパイル成功（エラー0）
    - `npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
  - 2026-08-17: bookTitle / startFromBeginning 引数名の camelCase 統一修正
    - 原因: `invalid args \`bookTitle\` for command \`start_continuous_capture\`` エラーが発生
    - Tauri の `invoke()` は JS オブジェクトのキー名と Rust コマンドの引数名が完全一致する必要がある
    - フロントエンド（`captureStore.ts`）が `bookTitle` / `startFromBeginning` を送信し、Rust 側（`capture.rs`）が `book_title` / `start_from_beginning` を期待していたためマッチング失敗
    - 修正案: 両方を camelCase に統一（`bookTitle`, `startFromBeginning`）
      - `localapp/src/store/captureStore.ts`: `book_title` → `bookTitle`, `start_from_beginning` → `startFromBeginning`
      - `localapp/src-tauri/src/commands/capture.rs`: 関数シグネチャ・コメント・変数参照を全て camelCase に変更
    - `cargo check`: コンパイル成功（エラー0、non_snake_case 警告2つは想定内）
    - `npm run tauri dev`: 起動成功
    - ユーザーテスト: 「連続キャプチャ開始」ボタンクリックで `bookTitle` エラーが解消されたことを確認

### LA002008-3 連続キャプチャ途中完了バグ修正（MSE同一ページ判定の猶予）

【計画】
1. 不具合の原因調査
   - `run_continuous_capture_loop()` 内の MSE 判定と `page_wait` のタイミングを確認
   - Kindle プロファイルの `page_wait: 0.15` が短すぎる可能性を検証
   - ページ送り直後に `calculate_mse()` が前回画像と同じ（未遷移）状態を検出すると「最終ページ到達」と誤判定する
2. 修正方針
   - MSE による同一ページ判定を「連続2回閾値未満」で確認する方式に変更
   - 1回目は「ページ遷移が追いついていない可能性」として再度ページ送りを試みる
   - 2回連続で MSE < threshold となった場合のみ `completed` とする
   - 実際の最終ページは確実に検出できるよう維持
3. デバッグログ強化
   - 毎回の MSE 値と判定結果をログ出力し、誤判定の確認ができるようにする
4. 変更対象ファイル
   - `localapp/src-tauri/src/commands/capture.rs`
5. ビルド確認
   - `cd localapp/src-tauri && cargo check`
   - `cd localapp && npm run build`
6. 想定される注意点
   - 最大ページ判定は誤検出を防ぎつつ、実際の最終ページは確実に検出できるようにする
   - 必要に応じて page_wait の調整も検討する

【実施結果】
- `localapp/src-tauri/src/commands/capture.rs` を修正
  - `same_page_count: u32` カウンタを導入
  - MSE < `MSE_THRESHOLD`（1000.0）となった場合：
    - 1回目は「ページ遷移が追いついていない可能性」として再度ページ送りを試み、キャプチャ画像は保存せずに破棄
    - 2回連続で同一ページと判定された場合のみ `completed`（最終ページ到達）とする
  - MSE >= threshold の場合は `same_page_count` を 0 にリセット
  - デバッグログを強化：毎回の `page_num`, `mse`, `threshold`, `same_page_count` を `eprintln!` で出力
  - 再ページ送り試行時は `page_turn` ステータスで「ページ遷移を確認中...」をフロントエンドに通知
- ビルド確認
  - `cd localapp/src-tauri && cargo check`: コンパイル成功（error 0、既存の non_snake_case 警告のみ）
  - `cd localapp && npm run build`: ビルド成功（`tsc && vite build` ともにエラーなし）
- 動作テスト: 2026-08-20 ユーザーにて実施、合格判定を取得
- コミット: `LA002008-3: 連続キャプチャ途中完了バグ修正（MSE同一ページ判定の猶予）` (`bd1afd0`)
- ブランチ: `feature/LA002008-3-continuous-capture-premature-completion`

### LA002009 連続キャプチャの出力フォルダ指定とトリミング画面への引継ぎ

【計画】
1. 機能要件
   - 「電子書籍」画面で連続キャプチャの出力フォルダをユーザーが指定できるようにする
   - 未指定時は既存の `~/Pictures/BookCapture/<book_title>/` をデフォルトとして使用
   - 指定したフォルダ情報はキャプチャ完了後、`captureStore.lastCaptureFolder` を通じて「トリミング」画面に自動引き継ぐ
2. 変更対象ファイル
   - `localapp/src/views/CaptureView.tsx`
     - 出力フォルダ選択ボタンを追加（`tauri-plugin-dialog` の `open({ directory: true })`）
     - 選択したフォルダパスをローカル state で保持
     - `startCapture()` 呼び出し時に `outputFolder` を渡す
   - `localapp/src/store/captureStore.ts`
     - `startCapture` のシグネチャを `(profile, bookTitle, startFromBeginning, outputFolder?)` に変更
     - `invoke("start_continuous_capture")` に `outputFolder` を追加
   - `localapp/src-tauri/src/commands/capture.rs`
     - `start_continuous_capture` に `outputFolder: Option<String>` 引数を追加
     - 指定があればそのパスを、なければ `create_capture_folder(&bookTitle)` を使用
     - 指定フォルダが存在しない場合は `create_dir_all` で作成
3. ビルド確認
   - `cd localapp/src-tauri && cargo check`
   - `cd localapp && npm run build`
4. 想定される注意点
   - Tauri の `invoke` は JS 側のキー名と Rust 側の引数名が完全一致する必要がある
   - フォルダ選択は既存の `tauri-plugin-dialog` を流用する
   - トリミング画面への引継ぎは既存の `lastCaptureFolder` 機構を利用する

【実施結果】
- `localapp/src/views/CaptureView.tsx`
  - `outputFolder` 用のローカル state を追加
  - `tauri-plugin-dialog` の `open({ directory: true })` でフォルダ選択ダイアログを表示する `handleSelectOutputFolder()` を追加
  - 選択済みフォルダパスを表示する Input とフォルダ選択ボタンを「書籍タイトル」入力の下に配置
  - `handleStartCapture()` で `startCapture(profile, bookTitle, startFromBeginning, outputFolder)` を呼び出すように変更
- `localapp/src/store/captureStore.ts`
  - `startCapture` のシグネチャを `(profile, bookTitle, startFromBeginning?, outputFolder?)` に変更
  - `invoke("start_continuous_capture")` の引数に `outputFolder` を追加
- `localapp/src-tauri/src/commands/capture.rs`
  - `start_continuous_capture` に `outputFolder: String` 引数を追加（空文字を未指定として扱う）
  - 新規 `resolve_output_folder(book_title, output_folder)` 関数を実装
    - `output_folder` が空の場合は従来通り `Pictures/BookCapture/<book_title>/` を使用
    - 指定がある場合はその配下に `<book_title>` サブフォルダを作成
    - 親フォルダが存在しない場合は `create_dir_all` で作成
    - サブフォルダ名が重複する場合は `_1`, `_2`, ... の連番サフィックスを付与（上限99）
  - 既存 `create_capture_folder` 関数は `resolve_output_folder` に統合され、削除した
- トリミング画面への引継ぎ
  - キャプチャ完了時に `capture-progress` イベントの `captureFolder` が `lastCaptureFolder` に保存される既存機構を利用
  - 追加の連携処理は不要（`TrimView` が `lastCaptureFolder` を自動読み込む）
- ビルド確認
  - `cd localapp/src-tauri && cargo check`: 成功（Tauri コマンド引数の camelCase 命名に関する警告のみ）
  - `cd localapp && npm run build`: 成功（`tsc && vite build` ともにエラーなし）
- 2026-08-21: バグ修正（LA002009-1）— トリミング画面へのフォルダ引継ぎが機能しない問題
  - **事象**: キャプチャ完了後、「トリミング」画面を開いてもキャプチャした画像が自動的に読み込まれない。手動でフォルダを選び直す必要がある。
  - **原因**: Rust 側 `ProgressPayload` に `#[serde(rename_all = "camelCase")]` が欠落していたため、イベントペイロードのフィールド名が snake_case (`capture_folder`) のまま送信されていた。一方、フロントエンドでは `captureFolder` (camelCase) を期待しており、`payload.captureFolder` が `undefined` になっていた結果、`lastCaptureFolder` に値が設定されなかった。
  - **修正**: `localapp/src-tauri/src/commands/capture.rs` の `ProgressPayload` 構造体に `#[serde(rename_all = "camelCase")]` を追加。
    ```rust
    #[derive(Clone, serde::Serialize)]
    #[serde(rename_all = "camelCase")]
    pub struct ProgressPayload {
        pub current: u32,
        pub total: u32,
        pub status: String,
        pub message: String,
        pub capture_folder: Option<String>,
    }
    ```
  - **ビルド確認**
    - `cd localapp/src-tauri && cargo check`: 成功（既存の non_snake_case 警告のみ）
    - `cd localapp && npm run build`: 成功（`tsc && vite build` ともにエラーなし）

### LA002006（将来タスク）ウィンドウ最前面化・クリック自動化

【計画】（検討事項）
- `core-foundation` / `cocoa` crate で macOS ウィンドウ操作
- プロファイルの `bring_to_front` フラグ対応
- `click_position` でキャプチャ前に自動クリック
- ただし macOS の Accessibility/画面収録権限が必要になる可能性

【実施結果】

---
## ユースケースNo | LA003

ユースケース
PDF 読込

外部 PDF を画像化して、トリミングタブに引き継ぐ。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| LA003001 | PDF 選択・設定 UI | 2026-08-15 | 2026-08-19 | 実装 |
| LA003002 | PDF → 画像展開（Rust バックエンド） | 2026-08-15 | 2026-08-19 | 実装 |
| LA003003 | PDF 読込 進捗インジケーター表示不具合調査・修正 | 2026-08-20 | 2026-08-20 | 不具合修正 |
| LA003004 | PDF 読込 Pdfium 二重初期化エラー修正 | 2026-08-20 | 2026-08-20 | 不具合修正 |
| LA003005 | PDF 画面の出力フォルダ自動設定と完了後表示改善 | 2026-08-21 | 2026-08-21 | 実装 |
| LA003006 | PDF → OCR 連携（localapp → backend API） | 2026-09-01 | 2026-09-03 | 実装 |

### LA003006 PDF → OCR 連携（localapp → backend API）

【計画】
- localapp から backend API を呼び出し、OCR → 検索可能 PDF 生成 → ダウンロードまでを自動化する
- Rust 側に `run_backend_ocr` コマンドを実装
  - `~/.config/book2pdf/settings.json` から backend URL を読み込む
  - 入力が画像フォルダの場合は一時 ZIP を作成
  - `POST /api/jobs`、`POST /api/jobs/{job_id}/upload`、`POST /api/jobs/{job_id}/ocr` を順に呼び出す
  - `GET /api/jobs/{job_id}` で completed/failed になるまでポーリング
  - `GET /api/jobs/{job_id}/pdf` で PDF をダウンロードして指定パスに保存
  - 各フェーズで `ocr-progress` イベントを emit
- フロントエンド側で `ocr-progress` イベントを受信し、進捗を表示する
- backend の `/ocr` は OCR 処理に数十分かかるため、リクエストを受け付けたら即座に processing を返すよう改修する
- ビルド確認: `cargo check`、`npx tsc --noEmit`

【実施結果】
- 2026-09-03: backend `/ocr` エンドポイントを非同期化
  - `backend/app/routers/jobs.py` の `run_ocr()` を修正
  - ジョブ状態を `PROCESSING` に更新後、`asyncio.create_task` でバックグラウンドタスクを起動
  - OCR エンジンの `run()` と PDF 生成 `generate_searchable_pdf()` は同期ブロッキング処理なので `asyncio.to_thread` で別スレッド化
  - 処理完了後に `COMPLETED` または `FAILED` に状態更新
  - これにより HTTP タイムアウト（3600s）を回避し、即座に `{"status":"processing"}` を返すようになった
- 2026-09-03: localapp Rust 側の HTTP タイムアウトを調整
  - `localapp/src-tauri/src/commands/backend_api.rs`
  - reqwest クライアント全体に 60 秒タイムアウトを設定
  - `/ocr` リクエスト個別のタイムアウトも 60 秒に短縮（backend は即座に返すため）
  - ポーリングループは `processing` 状態を継続し、`completed`/`failed` で終了するため、今回の改修と両立
- 2026-09-03: backend コンテナ再起動と API 動作確認
  - `docker compose restart backend`
  - `POST /api/jobs`、`POST .../upload`、`POST .../ocr` を curl で実行
  - `/ocr` が即座に HTTP 200 で `{"status":"processing"}` を返すことを確認
  - その後 `GET /api/jobs/{job_id}` で `processing` 状態が維持されることを確認
- ビルド確認
  - `cd localapp/src-tauri && cargo check`: 成功（既存の non_snake_case 警告のみ）
  - `cd localapp && npx tsc --noEmit`: 成功
- 2026-09-03: `run_backend_ocr` のテスタブルなコア分離
  - `localapp/src-tauri/src/commands/backend_api/backend_api_impl.rs` を新規作成
    - `run_backend_ocr_inner`: HTTP/polling/ダウンロードの backend 通信コア
    - `create_zip_from_folder`: 画像フォルダをソートして ZIP 化
  - `localapp/src-tauri/src/commands/backend_api.rs` をリファクタリング
    - Tauri 固有の `AppHandle` / 進捗 emit を薄いラッパーに留める
    - `backend_api_impl::run_backend_ocr_inner` を呼び出すのみ
  - モック backend による結合テストを追加
    - `localapp/src-tauri/tests/mock_backend_server.py`（軽量 Python モックサーバー）
    - `test_cases/testdata/localapp/mock_backend.pdf`（テスト用 PDF）
    - `cargo test backend_api_impl -- --nocapture`: 成功
      - `preparing` → `creating` → `uploading` → `ocr` → `polling` → `downloading` → `completed` の各イベントを確認
      - 出力 PDF ファイルが作成され、内容が空でないことを確認
- 2026-09-03: テスト結果ドキュメントを整理
  - `e2e-runtime-steps.md` の内容を `localapp/test-results/LA003006-backend-ocr-test/README.md` に統合
  - 重複ファイルは削除し、`.clinerules` 第 2.6 章のテスト結果配置ルールに準拠
- 2026-09-03: Python 3.13 互換性修正
  - `localapp/src-tauri/tests/mock_backend_server.py` から削除された `cgi.parse_header` を除去
  - 同機能を持つ `_parse_content_type` を自己完結で実装
  - `cargo test backend_api_impl -- --nocapture` で再合格を確認

### LA003001 PDF 選択・設定 UI

【計画】
- 2026-08-19 実装予定
- PDF ファイル選択ダイアログ（`tauri-plugin-dialog` の `open({ directory: false })` を使用）
- 出力フォルダ設定（自動設定：PDF と同じディレクトリに `<PDF名>_images/` を作成）
- DPI 選択：**200 / 300 / 400**、デフォルト **300**（150 は廃止、PNG のみで JPG は非対応）
- ファイルサイズ目安表示：DPI とページ数から推定 PNG サイズを表示
- 完了後、トリミングタブに自動引き継ぎ
- 変更対象ファイル：
  - `localapp/src/views/PdfImportView.tsx` — 既存ファイルを完全書き換え
  - `localapp/src/store/pdfImportStore.ts` — 新規作成（Zustand ストア）

【実施結果】
- `localapp/src/store/pdfImportStore.ts` を新規作成
  - Zustand ストアで PDF パス、出力フォルダ、DPI、進捗、エラー状態を管理
  - `open()` で PDF ファイル / 出力フォルダを選択
  - `listen("pdf-progress")` で Rust 側からの進捗イベントを受信
  - 変換完了後に `useTrimStore.getState().loadFolder()` と `useNavigationStore.getState().setView("trim")` でトリミングタブへ自動引き継ぎ
- `localapp/src/views/PdfImportView.tsx` を完全書き換え
  - PDF ファイル選択ボタン、出力フォルダ選択ボタン、DPI 選択セグメントコントロール
  - ページ数・推定ファイルサイズ表示
  - 進捗バーとメッセージ表示
  - 完了後「トリミングへ進む」ボタン
- `npm run build`: 成功（`tsc && vite build` ともにエラーなし）
- 2026-08-20: 進捗インジケーター改善（ユーザー要望対応）
  - ユーザー要望: 「PDFを画像化押下時からPDFのキャプチャーが終わるまで、進行を示すインジケーターを表示できないでしょうか」
  - 対応内容:
    - `pdfImportStore.ts`: `progressMessage` state を追加、`extractPdf()` 開始直後に不定形進捗メッセージを設定
    - `PdfImportView.tsx`: ボタン押下直後から進捗エリアを表示。スピナー + メッセージ + 不定形プログレス/確定進捗バーを切り替え
    - `pdf.rs`: PDF オープン直後に `emit_progress(0)` を送信、各ページ保存直後にも進捗イベントを emit
  - `cargo check`: 成功
  - `npm run build`: 成功

### LA003002 PDF → 画像展開（Rust バックエンド）

【計画】
- 2026-08-19 実装予定
- `pdfium-render` crate を使用して PDF をページ画像化
- PDFium `.dylib` をダウンロード・配置（`localapp/src-tauri/pdfium/` または `localapp/public/` 配下）
- バックグラウンドスレッドでレンダリング
- 進捗通知：`pdf-progress` イベントを 10ページごとに emit
- 完了後、トリミングタブに自動引き継ぎ（`trimStore.loadFolder(output_folder)`）
- 変更対象ファイル：
  - `localapp/src-tauri/Cargo.toml` — `pdfium-render` crate を追加
  - `localapp/src-tauri/src/commands/capture.rs` または `localapp/src-tauri/src/commands/pdf.rs` — `extract_pdf_to_images` コマンドを新規追加
  - `localapp/src-tauri/src/commands/mod.rs` — 新規モジュールを公開
  - `localapp/src-tauri/src/lib.rs` — コマンドを `invoke_handler` に登録

【実施結果】
- PDFium 動的ライブラリを `localapp/src-tauri/pdfium/lib/libpdfium.dylib` に配置
  - macOS arm64 用バイナリを `pdfium-mac-arm64.tgz` から展開
  - `tauri.conf.json` の `bundle.resources` に `pdfium/lib/libpdfium.dylib` を追加
- `localapp/src-tauri/src/commands/pdf.rs` を新規作成
  - `extract_pdf_to_images` コマンドを実装
  - `Pdfium::bind_to_library()` で `.dylib` を読み込み
  - `PdfRenderConfig::new().scale_page_by_factor(dpi / 72.0)` で DPI 指定レンダリング
  - `page.render_with_config(&render_config)?.as_image()?.as_rgba8()?.save(...)` で PNG 保存
  - 10 ページごとに `pdf-progress` イベントを emit
- `localapp/src-tauri/src/commands/mod.rs` に `pub mod pdf;` を追加
- `localapp/src-tauri/src/lib.rs` に `commands::pdf::extract_pdf_to_images` を `invoke_handler` に登録
- `cargo check`: 成功（既存ファイルの non_snake_case 警告 4 件のみ）
- 2026-08-20: 進捗イベントの頻度を改善
  - PDF オープン直後に `0 / total` を即座に emit
  - 各ページのレンダリング・保存直後に進捗イベントを emit（10ページごとから毎ページに変更）
  - UI 側で `progressMessage` を表示し、ボタン押下直後から進捗エリアが表示されるよう連携
- 2026-08-20: 進捗インジケーター表示不具合の調査・修正対応
  - **症状**: 「PDF を画像化」ボタン押下後、ボタン下に進捗エリアが表示されない。PNG ファイル自体は正常に生成される。
  - **原因（仮説）**:
    - Tauri の同期コマンド実行中は JavaScript 側のメインスレッドがブロッキング状態になり、`pdf-progress` イベントをリアルタイムで受信できない
    - React 18 の自動バッチングにより、イベント受信時の state 更新がコマンド完了まで遅延する可能性もある
  - **修正方針**:
    - Rust 側 `extract_pdf_to_images` を async コマンド + `tokio::task::spawn_blocking` に変更
    - フロントエンド側で `extractPdf` のコマンド呼び出しをマイクロタスク（例: `Promise.resolve().then()`）で実行し、メインスレッドを解放
    - イベントループの次のティックで `listen` コールバックが動作するよう調整

### LA003004 PDF 読込 Pdfium 二重初期化エラー修正

【計画】
- 2026-08-20 実施
- ユーザーによる動作テストで、`extract_pdf_to_images` の async 化後に `PdfiumLibraryBindingsAlreadyInitialized` エラーが発生したことを確認
- **原因**:
  - `pdfium-render` crate はプロセス内で `Pdfium::bind_to_library()` を1回のみ呼び出し可能
  - async 部で `Pdfium::bind_to_library()` → `Pdfium::new()` を行った後、`tokio::task::spawn_blocking` 内で再度 `bind_to_library()` を呼んでいたため、2重初期化エラーが発生
- **修正方針**:
  - async 部での PDFium 初期化（`Pdfium::bind_to_library()` / `Pdfium::new()`）を完全に削除
  - async 部では入力ファイル確認・出力フォルダ作成・ライブラリパス解決のみを行う
  - ライブラリパス・PDF パス・出力フォルダパス・DPI など「再オープンに必要な情報のみ」を `spawn_blocking` に渡す
  - `spawn_blocking` 内で PDFium 初期化 → PDF オープン → ページ数取得 → 進捗 emit(0) → 各ページレンダリング・保存 を一貫して実行
- 変更対象ファイル:
  - `localapp/src-tauri/src/commands/pdf.rs`
- 実施コマンド:
  - `cd localapp/src-tauri && cargo check`
  - `cd localapp && npm run build`
  - `cd localapp && npm run tauri dev`

【実施結果】
- 2026-08-20: `localapp/src-tauri/src/commands/pdf.rs` を修正
  - async 部での `Pdfium::bind_to_library()` / `Pdfium::new()` / PDF オープン・ページ数取得を削除
  - ライブラリパス・PDF パス・出力フォルダパス・DPI のみを `spawn_blocking` に渡すように変更
  - `render_pdf_pages` 内で PDFium 初期化 → PDF オープン → ページ数取得 → 進捗 emit(0) → レンダリング・保存 を一貫して実行
  - docstring に「`Pdfium::bind_to_library()` はプロセス内で1回のみ」という注意事項を追加
- 2026-08-20: タイムアウトエラー対応（ページ 6 の保存失敗: Operation timed out (os error 60)）
  - 原因: `image.save()` 実行時に macOS で一時的なファイルシステムタイムアウトが発生
  - 対応: PNG 保存処理にリトライ機構を追加（1秒待機、最大3回試行）
  - エラーメッセージを詳細化（試行回数・ファイルパスを含む）
- ビルド確認
  - `cd localapp/src-tauri && cargo check`: コンパイル成功（error 0、既存の non_snake_case 警告4件のみ）
  - `cd localapp && npm run build`: ビルド成功（tsc && vite build ともにエラーなし）

---

### LA003005 PDF 画面の出力フォルダ自動設定と完了後表示改善

【計画】
1. 機能要件
   - 「PDF」画面で PDF ファイル選択時、出力フォルダを自動設定する
   - デフォルト値は `Pictures/BookCapture/<PDFファイル名（拡張子除く）>/`
   - 取り込み完了後、自動的に「トリミング」画面へ遷移しない
   - 完了結果を「電子書籍」と同様に表示し、「フォルダを開く」「トリミングに進む」ボタンを配置
2. 変更対象ファイル
   - `localapp/src-tauri/src/commands/pdf.rs`: `get_pdf_default_output_folder` コマンドを新規追加
   - `localapp/src-tauri/src/lib.rs`: 新規コマンドを `invoke_handler` に登録
   - `localapp/src/store/pdfImportStore.ts`: PDF 選択後のデフォルトフォルダ自動設定、完了後自動遷移の削除、完了結果状態・開く・進むアクションを追加
   - `localapp/src/views/PdfImportView.tsx`: 完了時に `CaptureResultGallery` を表示しボタンを配置
3. ビルド確認
   - `cd localapp/src-tauri && cargo check`
   - `cd localapp && npm run build`
4. 想定される注意点
   - Tauri `invoke` の引数名はフロントエンド・Rust 両方で一致させる（過去に camelCase / snake_case 不整合でバグ発生）
   - 既存の `dirs` crate / `open_capture_folder` / `CaptureResultGallery` を再利用する
   - 「トリミングに進む」ボタンクリック時に `trimStore.loadFolder()` を実行する

【実施結果】
- 2026-08-21: 基本実装完了
  - `localapp/src-tauri/src/commands/pdf.rs` に `get_pdf_default_output_folder` コマンドを新規追加
    - 入力 PDF パスから拡張子除くファイル名を取得
    - `dirs::picture_dir()` 配下の `BookCapture/<stem>/` を返却
  - `localapp/src-tauri/src/lib.rs` に `get_pdf_default_output_folder` を `invoke_handler` に登録
  - `localapp/src/store/pdfImportStore.ts` を改修
    - `selectPdf()` で PDF 選択後、`get_pdf_default_output_folder` を呼び出して `outputFolder` を自動設定
    - `extractPdf()` 完了後の自動遷移を削除
    - 完了結果を `result` 状態に保持（`folderPath`, `imageCount`）
    - 「フォルダを開く」アクション `openOutputFolder()` を追加（`open_capture_folder` 再利用）
    - 「トリミングに進む」アクション `goToTrim()` を追加（`trimStore.loadFolder` + `setView("trim")`）
  - `localapp/src/views/PdfImportView.tsx` を改修
    - 完了後に `CaptureResultGallery` を表示
    - 「フォルダを開く」「トリミングに進む」ボタンを配置
  - ビルド確認
    - `cd localapp/src-tauri && cargo check`: コンパイル成功（既存の non_snake_case 警告のみ）
    - `cd localapp && npm run build`: ビルド成功（`tsc && vite build` ともにエラーなし）
  - ユーザーテスト: 合格判定を取得
- 2026-08-21: 追加要件対応（ユーザー指摘）
  - PDF 取り込み完了後、出力フォルダを「トリミング」画面と「ZIP 出力」の入力フォルダに自動反映
  - `pdfImportStore.ts` の `extractPdf()` 完了処理に以下を追加
    - `await useTrimStore.getState().loadFolder(resultFolder);`
    - `useExportStore.getState().setSourceFolder(resultFolder);`
  - これにより、PDF 画像化後に「トリミング」タブ / 「ZIP 出力」タブを開くと、各画面に画像・フォルダ情報が既に反映されている
  - ビルド確認
    - `cd localapp/src-tauri && cargo check`: コンパイル成功
    - `cd localapp && npm run build`: ビルド成功
  - ユーザーテスト: 合格判定を取得

---
## ユースケースNo | LA004

ユースケース
画像トリミング

キャプチャまたは PDF 展開した画像から余白を削除する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| LA004001 | 画像フォルダ読み込み・サムネイル一覧 UI | 2026-08-15 | 2026-08-18 | 実装 |
| LA004002 | Before/After プレビュー表示 | 2026-08-15 | 2026-08-18 | 実装 |
| LA004003 | 余白自動検出（Rust バックエンド） | 2026-08-15 |  | 実装 |
| LA004004 | 手動余白調整 UI | 2026-08-15 |  | 実装 |
| LA004005 | トリミング一括実行・進捗表示 | 2026-08-15 |  | 実装 |

### LA004001 画像フォルダ読み込み・サムネイル一覧 UI

【計画】
- `tauri-plugin-dialog` で任意の画像フォルダを選択（005002で追加済みのプラグインを流用）
- `trimStore.ts`（新規）を作成し、Zustandで以下を管理
  - `folderPath`: 入力フォルダパス
  - `imageFiles: string[]`: フォルダ内の画像ファイル名一覧
  - `selectedImage: string | null`: プレビュー対象の選択画像ファイル名
  - `loadFolder(folderPath)`: `list_capture_images` コマンドで画像リストを取得
  - `selectImage(filename)`: 選択画像を切り替え
- `TrimView.tsx`（改修）
  - 「フォルダを選択」ボタンを有効化（現状は disabled）
  - `tauri-plugin-dialog` の `open({ directory: true })` でフォルダ選択
  - キャプチャ結果（`captureStore.lastCaptureFolder`）の自動引継ぎを維持
  - `CaptureResultGallery` を流用してサムネイルグリッドを表示
    - トリミング画面用に拡張：選択中画像のハイライト表示
- Rust側：既存の `list_capture_images`, `get_capture_image` で対応（追加コマンド不要）

【実施結果】
- `localapp/src/views/TrimView.tsx`
  - トリミング4辺（上/下/左/右）の入力欄を変更
  - `type="text" inputMode="numeric"` に変更し、自由入力（0削除含む）を可能に
  - onBlur で数値に確定し、`setCropInsets` でストアに反映
  - 各辺に `-` / `+` カスタムボタンを追加し、`handleCropAdjust` で数値を増減（`Math.max(0, ...)` でクランプ）
- `localapp/src/components/capture/ProfileEditor.tsx`
  - 「電子書籍」タブのトリミング4辺も同様に変更
  - `type="text" inputMode="numeric"` + onBlur 確定 + カスタム +/- ボタン
  - `handleCropInputBlur` で `updateCustomProfile` を呼び出してストア更新
  - ローカル state `cropInputs` と `useEffect` で profile.cropInsets 変更時に同期
- 0 削除問題：ブラウザの `type="number"` では onChange で parseInt すると空文字が NaN→0 に戻るため 0 を削除できなかったが、ローカル state + `inputMode="numeric"` + onBlur 確定方式で解消
- `cargo check`：コンパイル成功（エラー0）
- `npm run build`：ビルド成功（エラーなし）
- コミット: `a964a87`, `dea345f`

### LA004002 Before/After プレビュー表示

【計画】
- オリジナル画像とトリミング後画像を左右に並列表示
- ズーム・パン対応
- 現在のファイル名とページ番号表示
- 前へ/次へ ナビゲーション

【実施結果】
- `localapp/src/store/trimStore.ts`
  - `originalPreviewImage: string | null` state を追加（元画像用）
  - `loadPreview()`: `Promise.all` で `get_capture_image`（元画像）と `apply_crop_preview`（トリミング後）を並列取得
  - `prevPage`, `nextPage`, `goToPage` でページ切り替え時に両方のプレビューをリセット
- `localapp/src/views/TrimView.tsx`
  - 左右2列グリッドレイアウト（`grid-cols-1 md:grid-cols-2`）に変更
  - 左側: Before（元画像）`originalPreviewImage` を表示
  - 右側: After（トリミング後）`previewImage` を表示
  - 両方のプレビュー領域に1pxの純粋な青枠線（`border border-[#0000FF]`）を追加し、背景と区別しやすくした
  - ナビゲーションボタン（前ページ / 次ページ）で両方の画像が同期して切り替わる
- `localapp/src-tauri/src/commands/capture.rs`
  - `apply_crop_preview` コマンドを新規追加：画像ファイルを読み込み `DynamicImage::crop` でトリミング → PNGエンコード → Base64 返却
- `localapp/src-tauri/src/lib.rs`
  - `commands::capture::apply_crop_preview` を `invoke_handler` に登録
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功（tsc && vite build ともにエラーなし）
- ブランチ: `feature/LA004001-trim-thumbnails`

### LA004003 余白自動検出（Rust バックエンド）

【計画】
- 複数ページをサンプリングして 4 辺の余白を推定
- 最小マージン（最も保守的な値）を採用
- 安全マージン（係数 + 固定 px）を適用
- 推定結果を UI に反映

【実施結果】

### LA004004 手動余白調整 UI

【計画】
- 左/右/上/下 の数値入力
- Canvas 上でドラッグして範囲を選択
- プレビューのリアルタイム更新
- 微調整ボタン

【実施結果】

### LA004005 トリミング一括実行・進捗表示

【計画】
- 全画像の一括トリミングを Rust 側で実行
- 進捗通知（current/total）
- 出力フォルダ自動生成
- 完了後、ZIP 出力タブに自動引き継ぎ

【実施結果】

---

## ユースケースNo | LA005

ユースケース
ZIP 出力・連携

トリミング済み画像を ZIP アーカイブにまとめる。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| LA005001 | ZIP アーカイブ化（Rust バックエンド） | 2026-08-15 | 2026-08-18 | 実装 |
| LA005002 | 出力設定・ファイル名設定 UI | 2026-08-15 | 2026-08-18 | 実装 |
| LA005003 | タブ間自動連携 | 2026-08-15 | 2026-08-18 | 実装 |
| LA005004 | ZIP 作成進捗インジケーター追加 | 2026-08-20 | 2026-08-20 | 改善 |

### LA005001 ZIP アーカイブ化（Rust バックエンド）

【計画】
1. `localapp/src-tauri/src/commands/capture.rs` に `create_zip_archive` コマンドを新規追加
    - `zip` crate の `ZipWriter` を使用して画像フォルダを ZIP 化
    - 対象ファイル: `.png` / `.jpg` / `.jpeg`（小文字で判定、jpeg は jpg として扱う）
    - ファイル名順に `sort()` でソートしてから ZIP エントリに追加（`pdf_builder.py: images_to_pdf` を参考）
    - 圧縮方式は `zip::CompressionMethod::Deflated`（標準的な圧縮）
    - 20ファイルごとに `zip-progress` 進捗イベントを emit（進捗コールバック方式は `pdf_extractor.py` を参考）
    - 完了後、出力ファイルパスを返却
2. `localapp/src-tauri/src/lib.rs` に `commands::capture::create_zip_archive` を `invoke_handler` に追加
3. `cargo check` でコンパイル確認
4. `npm run build` でフロントエンドビルド確認
5. 想定される注意点
    - 大規模フォルダでの非同期処理は将来検討（今回は同期的実装でシンプルに保つ）
    - 画像ファイル以外はZIPに含めない
    - 出力パスに拡張子がない場合は `.zip` を自動付与

【実施結果】
- `localapp/src-tauri/src/commands/capture.rs` に `create_zip_archive` コマンドを追加
  - `ZipWriter::new(File::create(output_path)?)` で ZIP ファイルを作成
  - `walkdir` の代わりに `std::fs::read_dir()` を使用（依存最小化）
  - `.png` / `.jpg` / `.jpeg` を小文字でフィルタ、ファイル名順に `sort()`
  - `CompressionMethod::Deflated` でエントリ追加
  - 20ファイルごとに `app_handle.emit("zip-progress", ZipProgressPayload { current, total, message })` で進捗通知
  - 出力パスに `.zip` 拡張子がない場合は自動付与
- `localapp/src-tauri/src/lib.rs` に `commands::capture::create_zip_archive` を `invoke_handler` に登録
- `cargo check`: コンパイル成功（エラー0）
- `npm run build`: ビルド成功
- ブランチ: `feature/LA005001-zip-archiver`

### LA005002 出力設定・ファイル名設定 UI

【計画】
1. `tauri-plugin-dialog` を追加
    - `localapp/src-tauri/Cargo.toml`: `tauri-plugin-dialog = "2"` を追加
    - `localapp/package.json`: `@tauri-apps/plugin-dialog` を追加
    - `localapp/src-tauri/src/lib.rs`: `.plugin(tauri_plugin_dialog::init())` を追加
    - `localapp/src-tauri/capabilities/default.json`: `dialog:allow-open` / `dialog:allow-save` 権限を追加
2. `localapp/src/store/exportStore.ts` を新規作成（Zustand ストア）
    - `sourceFolder`: 入力画像フォルダパス
    - `outputName`: 出力 ZIP ファイル名（拡張子除く、デフォルト "images"）
    - `outputFolder`: 出力先フォルダパス
    - `isCreating`: ZIP 作成実行中フラグ
    - `progressMessage`: 進捗メッセージ
    - `setSourceFolder()`, `setOutputName()`, `setOutputFolder()`: セッター
3. `localapp/src/views/ExportView.tsx` を完全書き換え
    - 入力フォルダ表示（captureStore.lastCaptureFolder から自動引継ぎ）
    - 出力ファイル名 `<Input>`
    - 「出力先を選択」ボタン → `tauri-plugin-dialog` のフォルダ選択ダイアログ
    - 「ZIP 作成」ボタン → `invoke("create_zip_archive", { folderPath, outputPath })`
    - `listen("zip-progress")` で進捗を受信して表示
    - 完了後、出力ファイルパス表示 + 「フォルダを開く」ボタン
4. `cargo check` / `npm run build` / `npm run tauri dev`
5. 想定される注意点
    - Tauri v2 の dialog plugin はフォルダ選択とファイル保存の両方をサポート
    - UI レイアウトは Apple HIG 風（白基調・余白多め・控えめな角丸）を維持

【実施結果】
- `tauri-plugin-dialog` を追加
  - `Cargo.toml`: `tauri-plugin-dialog = "2.7.2"` を追加（`cargo add tauri-plugin-dialog@2`）
  - `package.json`: `@tauri-apps/plugin-dialog` を追加（`npm install @tauri-apps/plugin-dialog`）
  - `lib.rs`: `.plugin(tauri_plugin_dialog::init())` を追加
  - `capabilities/default.json`: `dialog:allow-open` 権限を追加
- `localapp/src/store/exportStore.ts` を新規作成
  - Zustand ストア: `sourceFolder`, `outputName`, `outputFolder`, `isCreating`, `progressMessage`, `resultPath`
  - `createZip()`: `invoke("create_zip_archive")` + `listen("zip-progress")` で進捗受信
  - 完了後 `resultPath` に出力ファイルパスを保存
- `localapp/src/views/ExportView.tsx` を完全書き換え
  - 入力設定セクション（sourceFolder 表示、画像枚数）
  - 出力設定セクション（outputName Input、outputFolder 選択ボタン）
  - ZIP 作成ボタン + 進捗メッセージ + 完了後結果表示 + 「フォルダを開く」ボタン
- `cargo check`: 成功（既存の non_snake_case warning のみ）
- `npm run build`: 成功
- LA005002 と LA005003 は連続して実施（同一ブランチで実装）

### LA005003 タブ間自動連携

【計画】
1. `ExportView.tsx` の mount 時に `captureStore.lastCaptureFolder` を監視し、存在すれば `sourceFolder` に自動設定
2. TrimView からの `lastTrimmedFolder` 連携（将来 UC004 完了後に対応するため、exportStore は state で受け渡し可能な構造にしておく）
3. フォルダ設定時に `list_capture_images` で画像枚数を確認して表示
4. 想定される注意点
    - captureStore.lastCaptureFolder は連続キャプチャ完了後に保存されるため、エクスポートタブを開く前にキャプチャが完了している必要がある

【実施結果】
- `ExportView.tsx` に `useEffect` で `captureStore.lastCaptureFolder` の変更を監視
  - `lastCaptureFolder` が変更されると自動的に `exportStore.setSourceFolder()` に反映
  - ユーザーがキャプチャタブで連続キャプチャ完了後、ZIP 作成タブを開くと入力フォルダが自動設定される
- `list_capture_images` コマンドで画像枚数を取得して表示
  - `sourceFolder` 変更時に `invoke("list_capture_images", { folderPath: sourceFolder })` を実行
  - 取得したファイル数を「画像ファイル: X 枚」として表示
- 追加修正（ユーザー要望）: 入力設定セクションに任意フォルダ選択ボタンを追加
  - `ExportView.tsx` の「入力設定」セクションに「変更」/「選択」ボタンを追加
  - `tauri-plugin-dialog` の `open({ directory: true })` でフォルダを選択し `setSourceFolder` に設定
  - sourceFolder が未設定時は「選択」ボタン、設定済み時は「変更」ボタンを表示
  - これにより、キャプチャタブを経由せずに既存の画像フォルダから ZIP 作成が可能になった
- `cargo check`: 成功
- `npm run build`: 成功

### LA005004 ZIP 作成進捗インジケーター追加

【計画】
1. **ユーザー要望**
   - 「ZIP作成」タブで、PDF読込画面（PdfImportView）と同じような実行時の進捗インジケーターを表示したい
   - スピナー、プログレスバー、現在/総数のインデックス表示、パーセンテージ、進捗メッセージを表示する

2. **変更対象ファイル**
   - `localapp/src/store/exportStore.ts`
     - `progressCurrent: number` / `progressTotal: number` の state を追加
     - `ZipProgressPayload` の `current` / `total` も受信して state に反映
     - ZIP 作成開始時に progress 値をリセット
   - `localapp/src/views/ExportView.tsx`
     - `progressCurrent` / `progressTotal` / `progressMessage` を取得
     - PDF読込画面と同様の進捗 UI（スピナー + プログレスバー + カウンタ + パーセント）を追加
     - `isCreating` 中に表示、完了後は既存の `resultPath` 表示に移行

3. **確認事項**
   - Rust 側は既に `zip-progress` イベントで `current` / `total` / `message` を emit しているため、原則としてフロントエンドのみの変更で対応可能
   - `cargo check` / `npm run build` でビルド確認

4. **想定される注意点**
   - `current` や `total` が 0 の場合は不定形プログレスバーを表示（PdfImportView と同じ挙動）
   - パーセンテージは `Math.round((current / total) * 100)` で計算
   - ZIP 作成完了後も一瞬進捗 UI が残る可能性があるため、`isCreating` フラグで制御

【実施結果】
- 2026-08-20: 初回実装
  - `localapp/src/store/exportStore.ts` に `progressCurrent` / `progressTotal` を追加
  - `localapp/src/views/ExportView.tsx` にスピナー・プログレスバー・カウンタ・パーセント表示を追加
  - `cargo check` / `npm run build` に成功
- 2026-08-20: ユーザー動作テストで不合格
  - 症状: 「進捗表示はなく、カーソルがクルクルするだけ」
  - 原因: `create_zip_archive` が同期コマンドで、ZIP 作成中にフロントエンドのメインスレッドがブロックされ、`zip-progress` イベントをリアルタイムで受信できていなかった
  - 修正方針: PDF 読込機能（LA003002）と同様に `async` コマンド + `tokio::task::spawn_blocking` でバックグラウンド実行
- 2026-08-20: Rust 側非同期化対応
  - `localapp/src-tauri/src/commands/capture.rs`
    - `create_zip_archive` を `pub async fn` に変更
    - 実処理を `create_zip_archive_blocking` として分離し、`tokio::task::spawn_blocking` で実行
    - `tokio::sync::mpsc` チャネルで進捗情報を async 部に転送し、`AppHandle::emit("zip-progress", ...)` でフロントエンドに送信
    - 進捗イベントの送信頻度を「20ファイルごと」から「毎ファイル」に変更し、より滑らかな進捗表示を実現
  - `localapp/src-tauri/Cargo.toml`
    - tokio features に `macros` / `sync` を追加
- 2026-08-20: 再テストで合格
  - ZIP 作成時に進捗バー・カウンタ・パーセンテージが正しく表示されることを確認
  - `cargo check`: 成功（non_snake_case 警告のみ）
  - `npm run build`: 成功

---

## ユースケースNo | LA006

ユースケース
モダン GUI デザイン

クリーン＆ミニマルな Apple HIG 風 UI を実装する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| LA006001 | デザインシステム定義 | 2026-08-15 | 2026-08-16 | 実装 |
| LA006002 | サイドバー＋メインレイアウト実装 | 2026-08-15 | 2026-08-15 | 実装 |
| LA006003 | ライトモード対応 + OS 設定連動 | 2026-08-15 | 2026-08-16 | 実装 |
| LA006004 | アプリ名・サイドバー変更 | 2026-08-15 | 2026-08-16 | 実装 |

### LA006004 アプリ名・サイドバー変更

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

### LA006001 デザインシステム定義

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
3. `localapp/docs/LA-LOCALAPP-SPEC.md` のデザイン仕様更新
   - カラーパレット表に Tailwind CSS 変数名と oklch 値を追記
   - フォントに `Geist Variable` を明記
   - タイポグラフィのサイズ指定を rem で明記
4. ビルド確認・起動確認
   - `npm run build`
   - `npm run tauri dev`

【実施結果】
- `localapp/src/index.css` を Apple HIG 風カラーパレットに変更し、各変数に「用途 + 理由」のコメントを付加
- `localapp/src/components/ui/button.tsx` の各 variant・size に詳細な JSDoc コメントを付加
- `localapp/docs/LA-LOCALAPP-SPEC.md` のカラーパレット表を更新（oklch 値・CSS 変数名を追記）
- `.clinerules` 第8章に「初学者向け詳細コメント」ルールを加筆
- `npm run build` でビルド成功
- `npm run tauri dev` で起動確認完了
  - 白基調・余白多め・控えめな角丸のレイアウトが正しく表示されることを確認

### LA006002 サイドバー＋メインレイアウト実装

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

### LA006003 ライトモード対応 + OS 設定連動

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
3. `localapp/docs/LA-LOCALAPP-SPEC.md` にテーマ仕様を追記
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

## ユースケースNo | LA007

ユースケース
設定・永続化

アプリ設定、プロファイル、履歴を永続化する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| LA007001 | アプリ設定ファイル管理 | 2026-08-15 |  | 実装 |
| LA007002 | プロファイル・履歴の永続化 | 2026-08-15 |  | 実装 |

### LA007001 アプリ設定ファイル管理

【計画】
- `dirs::config_dir()` 配下に `config.json` を保存
- 読み書き用 Rust コマンド実装
- デフォルト値管理
- 設定変更時の UI 反映

【実施結果】

### LA007002 プロファイル・履歴の永続化

【計画】
- カスタムプロファイルの保存/読み込み
- 最近使用したフォルダ/ファイル履歴
- 設定 UI からの編集

【実施結果】

---

## ユースケースNo | LA008

ユースケース
PDF作成（Backend API連携）

トリミング済み画像フォルダ/ZIPから、backend API（FastAPI）を経由してOCR処理済みの検索可能PDFを生成する。

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| LA008001 | ローカル画像収集・ZIPアーカイブ化コマンド | 2026-08-22 | 2026-09-01 | 実装 |
| LA008002 | Backend API連携 — ジョブ作成・アップロード・OCR実行 | 2026-08-22 | 2026-09-01 | 実装 |
| LA008003 | Backend API連携 — ジョブ状態ポーリング・PDFダウンロード | 2026-08-22 | 2026-09-01 | 実装 |
| LA008004 | フロントエンド進捗インジケーター統合 | 2026-08-22 | 2026-09-01 | 実装 |
| LA008005 | 完了後「フォルダを開く」ボタン実装 | 2026-08-22 | 2026-09-01 | 実装 |
| LA008006 | backend OCR 連携機能統合テスト | 2026-08-22 |  | 実装 |
| LA008007 | localapp 単体生成 技術調査・選定 | 2026-09-03 |  | 調査 / 設計 |
| LA008008 | 画像結合PDF生成の実装（OCRなし） | 2026-09-03 | 2026-09-04 | 実装 |
| LA008009 | OCRエンジン統合・検索可能PDF生成の実装 | 2026-09-03 | 2026-09-04 | 実装 |
| LA008010 | Tauri invoke 引数修正・エンドツーエンド動作確認 | 2026-09-03 | 2026-09-04 | 実装 / 統合テスト |
| LA008011 | OCR精度向上（Tesseract pre-processing / モデル選定） | 2026-09-04 |  | 改善調査 |
| LA008012 | 透明テキストレイヤー・座標補正 | 2026-09-04 |  | 不具合修正 |

### LA008001 ローカル画像収集・ZIPアーカイブ化コマンド

【計画】
- 対象フォルダ内の `001.png`〜`999.png`（または `.jpg`）を正規表現で収集
- ファイル名の数値部分で昇順ソート
- `zip` crate で一時ZIPファイルを作成（`std::env::temp_dir()` 配下）
- ZIP作成進捗をイベントで送信（当初は `pdf-progress` を検討したが、backend API 連携専用の `ocr-progress` に統一）

【実施結果】
- 2026-09-01: 実装完了
- `localapp/src-tauri/src/commands/backend_api.rs` に `create_zip_from_folder` ヘルパーを実装
- `walkdir` を使用して対象フォルダ内の画像ファイルを収集し、昇順ソートして ZIP に追加
- 一時ディレクトリは `std::env::temp_dir()/book2pdf/ocr-{uuid}-temp/images.zip` に作成
- 処理終了後に一時ディレクトリを削除するクリーンアップ処理も実装
- 進捗イベントは `ocr-progress`（stage: "preparing"）を使用して、既存のローカル PDF 作成機能（`pdf-progress`）と区別

### LA008002 Backend API連携 — ジョブ作成・アップロード・OCR実行

【計画】
- `reqwest` で `POST /api/jobs` でジョブ作成
- `multipart/form-data` で `POST /api/jobs/{id}/upload` にZIPアップロード
- `POST /api/jobs/{id}/ocr` でOCR実行＋PDF生成を開始
- エラーハンドリング（接続エラー、APIエラー、タイムアウト）

【実施結果】
- 2026-09-01: 実装完了
- `tauri-plugin-http` の re-export する `reqwest` を使用
- `multipart/form-data` でファイルアップロードを実現するため、`Cargo.toml` で `tauri-plugin-http` に `multipart`/`json` feature を追加
- 各 API 呼び出しでエラーを `String` 形式で返却し、フロントエンド側で表示

### LA008003 Backend API連携 — ジョブ状態ポーリング・PDFダウンロード

【計画】
- 3秒間隔で `GET /api/jobs/{id}` をポーリング
- `status == "completed"` になったら `GET /api/jobs/{id}/pdf` でPDFバイナリを取得
- ユーザー指定の `outputPath` に書き出し

【実施結果】
- 2026-09-01: 実装完了
- ポーリング間隔は `AppSettings::polling_interval_sec`（デフォルト3秒）で可変
- タイムアウトは `ページ数 × AppSettings::page_timeout_sec` で計算
- `status == "completed"` で `GET /api/jobs/{id}/pdf` を呼び出し、レスポンスバイトを `output_path` に書き出し
- 一時ディレクトリは `fs::remove_dir_all` で確実に削除

### LA008004 フロントエンド進捗インジケーター統合

【計画】
- ZIP作成中：「ZIPを作成中... X / Y ファイル」
- アップロード中：「サーバにアップロード中...」
- OCR実行中：「OCR処理中...（バックエンド側で進捗）」
- PDFダウンロード中：「PDFをダウンロード中...」
- 完了：「PDF作成完了」+ 出力パス表示
- 対象キャプチャ画像数に対する処理数を示すインジケーターを表示

【実施結果】
- 2026-09-01: 実装完了
- `localapp/src/store/backendApiStore.ts` で `ocr-progress` イベントを listen
- `stage` に応じたメッセージを `progressMessage` に設定
- `PdfCreationView.tsx` において、ローカル OCR と backend OCR の進捗を同一のインジケーターで表示
- 処理中は両方のボタンを非活性化し、進捗率を計算してプログレスバーに反映

### LA008005 完了後「フォルダを開く」ボタン実装

【計画】
- 処理完了後、作成されたPDFがあるフォルダを開くボタンを表示
- `open` crate でOSのファイルマネージャーを起動

【実施結果】
- 2026-09-01: 実装完了
- `PdfCreationView.tsx` の既存「フォルダを開く」ボタンを流用
- backend OCR 結果も `resultPdfPath` として格納され、同じく `open_capture_folder` を呼び出して PDF の親フォルダを開く

### LA008006 backend OCR 連携機能実装

【計画】
- LA008001〜LA008005 の個別実装を統合し、backend OCR 連携機能全体としての一貫性を確保する
- エンドツーエンドのフロー統合テスト（フォルダ選択 → ZIP 作成 → ジョブ作成 → アップロード → OCR 実行 → ポーリング → PDF ダウンロード → フォルダを開く）
- エラーハンドリングの網羅性確認（ネットワーク不通、backend ダウン、OCR 失敗、タイムアウト各パターン）
- 設定 UI（タイムアウト値、ポーリング間隔）との連携確認
- ユーザー動作テスト実施・合格判定取得

【実施結果】

### LA008007 localapp 単体生成 技術調査・選定

【計画】
1. **PDF 生成 crate 選定**
   - 候補：`printpdf`（シンプル・画像埋め込み対応）、`pdf-writer`（低レベル制御）、`genpdf`（高レベル抽象）
   - 評価基準：画像埋め込みの容易さ、メモリ効率、ライセンス、A4サイズ指定の容易さ
   - 結論：`printpdf` を採用（理由：シンプルな画像→PDF変換に最適、API学習コストが低い）
2. **OCR エンジン選定**
   - 候補：Tesseract（OSS・日本語対応）、PaddleOCR（精度重視）、EasyOCR
   - 評価基準：日本語認識精度、Rust FFI / CLI 呼び出しの容易さ、ライセンス、バイナリサイズ
3. **画像サイズ扱いの方針決定**
   - A4（210mm × 297mm）に統一し、アスペクト比維持で fit
   - 将来的に「元画像サイズ維持」オプションも追加可能な設計
4. **調査結果のドキュメント化**
   - `localapp/docs/LA-OCR-TECHNOLOGY-SURVEY-LA008007.md` に調査レポートを作成
   - 各候補の評価スコア、採用理由、POC 結果を記載

【実施結果】
- `printpdf` 0.7.0 の画像→A4 PDF 埋め込み POC を実施し成功。正しい API パターンは `Image::try_from(decoder)` + `image.add_to_layer()` + `ImageTransform`
- `image` crate の namespace shadowing（printpdf の `pub mod image`）を解決し、`image_crate` として alias 化
- A4 フィットロジックを確立：10mm マージン、300 DPI px→mm 変換、`ImageTransform` でのセンタリング＋スケーリング
- `tesseract` crate 0.15.2 と `leptess` 0.14.0 を調査し、`leptess` を採用（`get_component_boxes()` で word/line bbox を直接取得可能、hOCR/TSV パース不要）
- backend + ocr-worker 実装との差異を調査・分析。OCR エンジン（ndlocr_cli vs Tesseract）、PDF 生成ライブラリ（PyMuPDF vs printpdf）、座標系処理、アーキテクチャの 4 面で根本的な違いがあることを確認
- 調査レポート `localapp/docs/LA-OCR-TECHNOLOGY-SURVEY-LA008007.md` を作成
- 残課題：
  - `image` crate 0.25.x と `printpdf` 内部の 0.24.x とのデュアルバージョン対応（LA008008 で対応方針確定）
  - LA008009 で `leptess` 統合 POC（画像→OCR→テキストレイヤーPDF）を実施

### LA008008 画像結合PDF生成の実装（OCRなし）

【計画】
1. **Rust コマンド実装**
   - `localapp/src-tauri/src/commands/pdf_generation.rs` を新規作成
   - 処理フロー：画像フォルダ or ZIP 読み込み → ファイル名昇順ソート → PDF ページ生成
   - `printpdf` crate を使用し、各画像を A4 ページに配置
   - 進捗通知：`pdf-progress` イベントで `current` / `total` / `stage` / `message` を emit
2. **画像処理**
   - `image` crate で画像読み込み
   - アスペクト比維持で A4 サイズにフィット（余白は白背景）
3. **UI 統合（最小限）**
   - `PdfCreationView.tsx` に「画像結合 PDF 生成」ボタンを仮追加
   - backend OCR 連携ボタンと並列配置
4. **テスト**
   - Rust 側の単体テスト（画像 → PDF 変換の確認）
   - `cargo check` / `npm run build`

【実施結果】
- 2026-09-04: 実装完了
  - `printpdf = "0.7"`（`embedded_images` feature）と `image_crate`（`image` 0.24.x の別名）を `Cargo.toml` に追加
    - `printpdf` 内部の `image` 0.24.x との互換性確保のため、別名インポート方式を採用
  - `localapp/src-tauri/src/commands/pdf_generation.rs` を新規作成
    - `generate_image_pdf` コマンド（非同期）：入力フォルダまたは ZIP から画像（001-999.png/jpg）を収集・ソート
    - 画像を A4（210mm × 297mm、10mm マージン）にアスペクト比維持でフィットさせ、各画像を独立ページに配置
    - px → mm 変換は 300 DPI 基準で実施
    - 進捗イベント `pdf-creation-progress` を emit（current/total/message）
    - ZIP 入力時は一時フォルダに展開し、処理完了後に自動クリーンアップ
    - `pdf_creation.rs`（検索可能 PDF）とは完全に独立した自己完結モジュール
  - `commands/mod.rs` と `lib.rs` に `pdf_generation::generate_image_pdf` を登録
  - フロントエンド統合
    - `pdfCreationStore.ts` に `generateImagePdf` アクションを追加（`generate_image_pdf` コマンドを invoke、進捗イベントを購読）
    - `PdfCreationView.tsx` のボタンラベルを変更：
      - 「PDF 作成（ローカル）」→「アプリケーションでPDF作成（仮：OCRなし）」
      - 「backend OCR で PDF 作成」→「ウェブサイトで PDF作成」
    - 「アプリケーションでPDF作成」ボタンの onClick を `handleGenerateImagePdf`（`generateImagePdf` 呼び出し）に差し替え
  - `cargo check`（Rust）と `npm run build`（TypeScript + Vite）が正常に完了
  - **2026-09-04（コメント補充）**: `.clinerules` 第8章に基づき、初学者向けの詳細コメントを追加
    - `collect_images_sorted`: 引数・戻り値・命名規約の由来（`capture.rs` 連番撮影との対応）・処理フローを詳細に文書化
    - `extract_zip_to_temp`: 一時フォルダのクリーンアップ責任・戻り値の形式・エラー条件を明記
    - `uuid_v4`: 「UUID v4（RFC 4122）ではない」ことを明確化し、ナノ秒タイムスタンプ簡易実装の理由を説明
    - 定数セクション: `A4_WIDTH_MM` / `A4_HEIGHT_MM` / `MARGIN_MM` / `DPI` それぞれの設計意図（ISO 216 規格・印刷業界標準・トンボ対策など）を記載
    - `create_image_pdf_impl` 内のロジック:
      - `scale.min(1.0)` → 拡大による画質劣化（ボケ・ジャギー）を防ぐ設計方針
      - `scale_x`/`scale_y` 同値設定 → アスペクト比維持の理由
      - `ImageTransform` 各フィールド → PDF 座標系（左下原点）の説明
    - コンパイル確認: `cargo check` 成功（エラー0）
  - **2026-09-04（自動テスト実装）**: Rust 単体テスト 5ケースすべて PASS
    - テストデータ: `test_cases/testdata/localapp/LA003006-backend-ocr-test/`（`002.png`, `003.png`, `004.png`）を流用
    - テストケース:
      1. `collect_images_sorted` — 既存データから画像を正しく昇順ソート
      2. `collect_images_sorted_empty` — 空フォルダでエラー返却
      3. `uuid_v4_unique` — 100回連続呼び出しで全て一意（アトミックカウンターで保証）
      4. `create_image_pdf_impl_page_count` — 画像3枚 → PDF 3ページ（`lopdf` で検証）
      5. `create_image_pdf_impl_file_size` — 生成 PDF が 1KB 以上（空ファイルでないこと）
    - `cargo test pdf_generation`: **5 passed; 0 failed**
    - `lopdf = "0.34"` を `[dev-dependencies]` に追加（PDF 構造検証用）
    - `uuid_v4()` に `AtomicU64` カウンターを追加し、高速連続呼び出しでの一意性を保証
    - テスト結果レポート: `localapp/test-results/LA008008-image-pdf-test/README.md` を作成
    - **localapp フロントエンド（React/Zustand）自動テスト**: vitest/jest 等のテストフレームワーク未導入のため現時点では未実施。将来基盤構築時に `pdfCreationStore.ts` の `generateImagePdf` アクション単体テストを検討

| 項目 | 詳細 |
|---|---|
| 作成ファイル | `localapp/src-tauri/src/commands/pdf_generation.rs` |
| 変更ファイル | `localapp/src-tauri/Cargo.toml`, `localapp/src-tauri/src/commands/mod.rs`, `localapp/src-tauri/src/lib.rs`, `localapp/src/store/pdfCreationStore.ts`, `localapp/src/views/PdfCreationView.tsx` |

### LA008009 OCRエンジン統合・検索可能PDF生成の実装

【計画】
1. **前提：LA008007 の OCR エンジン選定完了**
   - OCR エンジン: `leptess` 0.14.0（Tesseract 5.x + Leptonica の Rust ラッパー）
   - PDF 生成: `printpdf` 0.7.0（LA008008 で実装済み）
   - 座標変換: Tesseract 左上原点(px) → printpdf 左下原点(mm)
2. **環境・依存関係準備**
   - `leptess` crate を `Cargo.toml` に追加
   - `tesseract` 5.5.2 + `jpn.traineddata` は既にインストール済み（brew不要）
   - リンカパス確認: `/opt/homebrew/lib/libtesseract.dylib`
3. **Rust 実装**
   - `src/commands/pdf_searchable.rs` を新規作成（または `pdf_generation.rs` に追加）
   - `generate_searchable_pdf` コマンドを実装
   - フロー: 画像読み込み → `leptess` OCR → `(text, x, y, w, h)[]` 取得 → `printpdf` でテキストレイヤー描画
   - フォント: POC段階ではシステムフォント（ヒラギノ角ゴシック W3）を使用
   - 進捗イベント: `searchable-pdf-progress` を emit（OCR進捗 + PDF生成進捗）
4. **座標変換ロジック**
   - Tesseract bbox (px, 左上原点) → mm 変換
   - printpdf 左下原点へ変換: `pdf_y = page_height_mm - (ocr_y_px / dpi * 25.4) - text_height_mm`
   - A4 へのスケーリング係数を考慮（画像fitスケールと同じ係数を適用）
5. **UI 更新**
   - `PdfCreationView.tsx`: 「検索可能PDF生成（ローカルOCR）」ボタンを有効化
   - `pdfCreationStore.ts`: `generateSearchablePdf` アクション追加
   - 進捗表示: OCR処理中のメッセージ（「OCR処理中: 1/3ページ...」）
6. **テスト**
   - Rust 単体テスト: `leptess` での OCR 結果取得確認
   - PDF 検証: `lopdf` でテキストオブジェクトの存在確認
   - 目視確認: Preview.app以外のビューアでテキスト選択・検索可能か確認

【実施結果】
- 2026-09-04: `cargo add leptess regex` を実行し、OCR エンジンと HOCR パース用正規表現ライブラリを追加
- 2026-09-04: `src/commands/pdf_searchable.rs` を新規作成。コマンド名を `create_searchable_pdf` とし、フロントエンド命名規約に合わせた引数 (`sourcePath`, `sourceType`, `outputPath`) に統一
- 2026-09-04: `leptess::get_component_boxes` はテキスト情報を返さないため、`get_hocr_text(0)` で HOCR HTML を取得し、正規表現で word レベルの bbox + テキストを抽出する `parse_hocr_words` を実装
- 2026-09-04: 座標変換パイプラインを実装: Tesseract px（左上原点）→ mm（DPI=300）→ A4 fit スケーリング → printpdf 左下原点フリップ（`pdf_y = A4_HEIGHT_MM - margin - offset_y - y2_mm`）
- 2026-09-04: テキストレイヤーは黒色（`PdfColor::RGB(0,0,0)`）で描画し、PDF ビューア側の「テキスト表示」設定で可視化可能に。透明色指定は printpdf 0.7.0 の挙動が不安定なため当面黒色で統一
- 2026-09-04: 進捗イベント名を既存フロントエンドリスナーと統一し、`pdf-creation-progress` を emit（`current`, `total`, `message`）
- 2026-09-04: 旧 LA006001 のダミー実装 `pdf_creation.rs` を削除し、`commands/mod.rs` と `lib.rs` からの登録を除去。LA008009 の `pdf_searchable.rs` を正式な検索可能 PDF 生成モジュールとした
- 2026-09-04: `PdfCreationView.tsx` に「アプリケーションで OCR 付き PDF 作成」ボタンを追加し、`pdfCreationStore.createPdf()` を呼び出す `handleCreateSearchablePdf` ハンドラを実装
- 2026-09-04: `pdfCreationStore.ts` の `createPdf` アクションを `invoke('create_searchable_pdf', ...)` で呼び出すよう修正
- 2026-09-04: `cargo check` / `cargo test --lib pdf_searchable` / `npm run build` を実施。HOCR パース・画像収集・UUID 生成の単体テストが pass
- 2026-09-04: `cargo test --lib pdf_searchable -- --ignored` で統合テストを実行。`test_cases/testdata/localapp/LA003006-backend-ocr-test` の 3 枚の PNG から 15MB/3ページの検索可能 PDF を生成。PyMuPDF でテキスト抽出し、各ページにテキストレイヤーが埋め込まれていることを確認（Page 1: 74 chars, Page 2: 567 chars, Page 3: 945 chars）
- 2026-09-04: タスク完了日を 2026-09-04 に設定

### LA008010 Tauri invoke 引数修正・エンドツーエンド動作確認

【計画】
1. **UI 統合**
   - `PdfCreationView.tsx` のボタン配置を整理（backend OCR / 画像結合 PDF / 検索可能 PDF）
   - 各ボタンにツールチップまたは説明文を追加
2. **使い分けガイド**
   - UI 上に簡易的な比較表を表示（速度 vs 精度 vs 機能）
   - 例：backend OCR「高精度・検索可能・処理時間長」/ localapp 画像結合「即時・画像のみ」/ localapp OCR「中精度・ローカル完結」
3. **統合テスト・ユーザーテスト**
   - 各生成パターンのエンドツーエンドテスト
   - ユーザー動作テスト実施・合格判定
4. **ドキュメント更新**
   - `localapp/docs/LA-TASKS.md` 各タスクの完了日付を記入
   - `localapp/docs/LA-WORK-LOG.md` に実施実績を追記

【実施結果】
- 2026-09-04: `create_searchable_pdf` の引数名を camelCase（`sourcePath`, `sourceType`, `outputPath`）に修正。Tauri `invoke` 経由でフロントエンドから正しくパラメータが渡されるようになった
- 2026-09-04: 実機（Apple Silicon Mac）で 3 ページの検索可能 PDF を生成（出力サイズ約 14.5 MB）。生成された PDF でテキスト選択および検索が機能することを目視確認
- 2026-09-04: タスク完了日を 2026-09-04 に設定

### LA008011 OCR精度向上（Tesseract pre-processing / モデル選定）

【計画】
- Tesseract 単体 OCR の認識率を向上させるため、画像前処理（二値化 / ノイズ除去 / 解像度調整）の効果を検証する
- `jpn.traineddata` 以外の学習済みモデル（`jpn_vert`、`best`/`fast` モデル等）との比較を実施する
- backend ndlocr_cli との精度差を定量的に評価し、localapp OCR の使い所を再定義する
- 前処理パラメータとモデルの選定結果を `localapp/docs/LA-CAVEATS.md` に追記する

【実施結果】

### LA008012 透明テキストレイヤー・座標補正

【計画】
- 現在のテキストレイヤーは黒色で描画されているため、PDF ビューアの「テキスト表示」設定がオンの場合に視認性に影響を与える
- `printpdf` 0.7.0 の透明色 / 描画モード挙動を再調査し、背景画像を損なわない透明テキストレイヤー実装を検討する
- Tesseract bbox から PDF 座標への変換誤差（文字の上下位置ズレ等）を目視確認し、必要に応じて基準点補正を行う
- 修正後、実機でテキスト選択・検索・コピーの精度を再検証する

【実施結果】

