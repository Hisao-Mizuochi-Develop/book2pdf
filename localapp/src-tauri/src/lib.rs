/// Book Capture — Tauri v2 アプリケーションのエントリポイント（ライブラリ側）
///
/// `main.rs` から呼び出され、Tauri の WebView ランタイムを初期化して起動する。
/// フロントエンド（React）からの `invoke()` 呼び出しを受け付けるコマンドハンドラを
/// ここで登録することで、Rust 側のネイティブ機能を JavaScript/TypeScript から利用できる。
///
/// 【ファイル構成の意図】
/// - `lib.rs`: Tauri アプリ本体（WebView 起動、コマンド登録）
/// - `main.rs`: エントリポイント（`lib::run()` を呼び出すだけ）
/// この分離により、テスト時に `lib.rs` の関数を直接呼び出しやすくなる。

// サブモジュールの宣言
// Tauri コマンド（フロントエンドから呼び出される関数）
mod commands;
// データモデル（フロントエンドと共有する構造体）
mod models;

/// Tauri アプリケーションを起動する
///
/// # 処理フロー
/// 1. `tauri::Builder::default()` でビルダーを作成
/// 2. `.plugin()` でプラグインを登録（外部リンクをブラウザで開く opener プラグイン）
/// 3. `.invoke_handler()` でフロントエンドから呼び出せるコマンドを登録
/// 4. `.run()` で WebView ウィンドウを起動し、イベントループを開始
///
/// # コマンド登録について
/// `tauri::generate_handler![...]` マクロ内に `#[tauri::command]` 属性を持つ
/// 関数を列挙することで、フロントエンドの `invoke("function_name")` と対応づけられる。
/// 例: `invoke("capture_screen")` → `commands::capture::capture_screen` が呼ばれる
///
/// # panic
/// WebView の初期化に失敗した場合は panic する（継続不可なため expect で終了）。
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // 外部リンクをデフォルトブラウザで開くための公式プラグイン
        .plugin(tauri_plugin_opener::init())
        // フロントエンドから呼び出せるコマンドを登録
        // ここに列挙した関数が `invoke("関数名")` で呼び出される
        .invoke_handler(tauri::generate_handler![
            commands::capture::capture_screen,
            commands::capture::get_builtin_profiles,
            commands::capture::start_continuous_capture,
            commands::capture::stop_continuous_capture,
        ])
        // tauri.conf.json の設定を読み込んでアプリケーションを起動
        .run(tauri::generate_context!())
        // 起動失敗時は致命的エラーなので panic（エラーメッセージを表示して終了）
        .expect("error while running tauri application");
}
