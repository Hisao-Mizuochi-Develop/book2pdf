// Book Capture — Tauri v2 デスクトップアプリケーションのエントリポイント
//
// このファイルは Rust プログラムの最も外側の入り口（エントリポイント）であり、
// OS から直接呼び出される `main` 関数を定義する。
//
// 【なぜ `lib.rs` ではなく `main.rs` なのか】
// Tauri v2 の scaffold では、WebView 本体のロジックを `lib.rs` に分離し、
// `main.rs` からは最小限の記述でその `lib.rs` の `run()` を呼び出す構成になっている。
// これにより、テスト時に `lib.rs` だけを import してテストしやすくなる（テストのための分離）。
//
// 【リリースビルドで黒いコンソール窓を出さない】
// Windows では、Rust のデフォルトではコンソールアプリケーションとしてビルドされ、
// 実行時にコマンドプロンプト（黒い窓）が出てしまう。
// デスクトップ GUI アプリとして振る舞うため、リリースビルド時にのみ
// `#![windows_subsystem = "windows"]` を設定してコンソール出力を抑制する。
// デバッグビルド時は消さない（`not(debug_assertions)` で制限）ことで、
// 開発中の println! デバッグ出力が見えるようにしている。
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

/// プログラムのエントリポイント
///
/// `tauri_app_lib::run()` は、`lib.rs` で定義された `run()` 関数を呼び出す。
/// この中で Tauri の Builder が初期化され、WebView ウィンドウが起動する。
fn main() {
    tauri_app_lib::run()
}
