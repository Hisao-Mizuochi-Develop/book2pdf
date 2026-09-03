/// Tauri コマンドのルートモジュール
///
/// フロントエンド（React）から `invoke("command_name")` で呼び出される、
/// Rust 側のハンドラ関数をこの `commands/` ディレクトリに配置する。
///
/// 【命名規則】
/// - ファイル名は機能名で分ける（capture.rs = キャプチャ機能）
/// - 各ファイル内には `#[tauri::command]` 属性を付与した公開関数を定義する
/// - フロントエンドで型安全に使うため、構造体の戻り値には serde::Serialize を実装する
///
/// 【lib.rs との連携】
/// lib.rs の `invoke_handler` で `commands::capture::capture_screen` のように
/// `commands::<mod>::<fn>` 形式で登録することで、フロントエンドから呼び出し可能になる。
pub mod capture;
// 003: PDF 読込コマンド
pub mod pdf;
// 006: OCR 済み PDF 作成コマンド
pub mod pdf_creation;
// 008: 画像結合 PDF 生成コマンド（OCR なし）
pub mod pdf_generation;
// 003006: localapp → backend API 連携コマンド
pub mod backend_api;
