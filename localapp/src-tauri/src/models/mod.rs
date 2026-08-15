/// データモデル定義のルートモジュール
///
/// フロントエンドと共有する型や、ビジネスロジックで使用する構造体を定義する。
/// 各サブモジュールは serde の Serialize/Deserialize を実装し、
/// Tauri の invoke コマンド経由で JSON として双方向通信できることを前提とする。
pub mod capture_profile;
