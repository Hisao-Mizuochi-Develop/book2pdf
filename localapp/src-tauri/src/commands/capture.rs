/// 画面キャプチャ関連の Tauri コマンド
///
/// `screenshots` crate を使用して画面スクリーンショットを取得し、
/// Base64 エンコードした PNG 画像をフロントエンドに返却する。
///
/// 【プロファイル管理コマンド】
/// - `get_builtin_profiles`: ビルトインプロファイル一覧を JSON で返す
///   フロントエンドの Zustand ストア（profileStore）が起動時に呼び出し、
///   セレクタ UI の選択肢として利用する。
use image::ImageEncoder;
use screenshots::Screen;
use crate::models::capture_profile::{CaptureProfile, ProfileEntry};

/// スクリーンショット結果をフロントエンドに返す構造体
#[derive(serde::Serialize)]
pub struct CaptureResult {
    /// Base64 エンコードされた PNG 画像データ（data URL 用）
    base64: String,
    /// 画像幅（ピクセル）
    width: u32,
    /// 画像高さ（ピクセル）
    height: u32,
}

/// 全画面のスクリーンショットを取得して Base64 PNG として返却する
///
/// # 処理フロー
/// 1. `screenshots::Screen::all()` で全ディスプレイ情報を取得
/// 2. 最初のディスプレイを対象に `capture()` でスクリーンショット取得
/// 3. `to_png()` で PNG 形式のバイト列に変換
/// 4. Base64 エンコードして JSON で返却
///
/// # 戻り値
/// - `Ok(CaptureResult)`: キャプチャ成功時（base64, width, height を含む）
/// - `Err(String)`: キャプチャ失敗時のエラーメッセージ
///
/// # 注意
/// macOS で実行する場合、初回実行時に「画面収録」権限の許可が必要となる
#[tauri::command]
pub fn capture_screen() -> Result<CaptureResult, String> {
    // 接続されている全ディスプレイを取得
    let screens = Screen::all().map_err(|e| format!("ディスプレイ取得エラー: {}", e))?;

    if screens.is_empty() {
        return Err("ディスプレイが見つかりません".to_string());
    }

    // 最初のディスプレイを対象にキャプチャ（メイン画面）
    let screen = &screens[0];
    let image = screen
        .capture()
        .map_err(|e| format!("キャプチャエラー: {}", e))?;

    // PNG 形式のバイト列に変換
    // `screenshots` crate の内部 image バッファから生バイトを取得し、
    // プロジェクト側の `image` crate (0.25.x) で PNG エンコードする
    let png_bytes = {
        let mut buf = Vec::new();
        let encoder = image::codecs::png::PngEncoder::new(&mut buf);
        encoder
            .write_image(
                image.as_raw(),
                image.width(),
                image.height(),
                image::ExtendedColorType::Rgba8,
            )
            .map_err(|e| format!("PNG 変換エラー: {}", e))?;
        buf
    };

    // Base64 エンコード
    let base64 = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, &png_bytes);

    Ok(CaptureResult {
        base64,
        width: image.width(),
        height: image.height(),
    })
}

/// ビルトインプロファイル一覧をフロントエンドに返す
///
/// # 処理フロー
/// 1. `CaptureProfile::builtin_profiles()` で定義済みプロファイルを取得
/// 2. `(String, CaptureProfile)` のタプルを `ProfileEntry` に変換
/// 3. JSON 配列としてフロントエンドに返却
///
/// # 戻り値
/// - `Ok(Vec<ProfileEntry>)`: プロファイル一覧（6件のビルトインプロファイル）
/// - `Err(String)`: 通常発生しないが、Tauri コマンドの型合わせで定義
///
/// # フロントエンドとの連携
/// フロントエンドの `profileStore.fetchProfiles()` がこのコマンドを呼び出し、
/// 取得したプロファイルを `builtinProfiles` state に保存する。
/// 各エントリの `key` フィールドがプロファイルの一意識別子として使用される。
#[tauri::command]
pub fn get_builtin_profiles() -> Result<Vec<ProfileEntry>, String> {
    // ビルトインプロファイル定義を取得して ProfileEntry に変換
    let entries: Vec<ProfileEntry> = CaptureProfile::builtin_profiles()
        .into_iter()
        .map(ProfileEntry::from)
        .collect();

    Ok(entries)
}
