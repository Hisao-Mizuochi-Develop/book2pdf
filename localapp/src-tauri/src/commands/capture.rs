/// 画面キャプチャ関連の Tauri コマンド
///
/// `screenshots` crate を使用して画面スクリーンショットを取得し、
/// Base64 エンコードした PNG 画像をフロントエンドに返却する。
///
/// 【プロファイル管理コマンド】
/// - `get_builtin_profiles`: ビルトインプロファイル一覧を JSON で返す
///   フロントエンドの Zustand ストア（profileStore）が起動時に呼び出し、
///   セレクタ UI の選択肢として利用する。
///
/// 【連続キャプチャコマンド】
/// - `start_continuous_capture`: バックグラウンドスレッドで連続キャプチャを開始
/// - `stop_continuous_capture`: 実行中の連続キャプチャを停止
use image::ImageEncoder;
use screenshots::Screen;
use crate::models::capture_profile::{CaptureProfile, ProfileEntry};

// 連続キャプチャ制御用のグローバル状態
// Rust 1.70+ では std::sync::OnceLock で標準化されているため、外部 crate は不要
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, OnceLock};
use std::thread;
use std::time::Duration;
use tauri::Emitter;
use enigo::{Enigo, Key, Keyboard, Settings, Direction};

/// 連続キャプチャの進捗通知用イベントペイロード
///
/// `app_handle.emit("capture-progress", ProgressPayload)` でフロントエンドに送信される。
/// フロントエンド側は `listen("capture-progress")` でこのイベントを受信する。
#[derive(Clone, serde::Serialize)]
pub struct ProgressPayload {
    /// 現在キャプチャ済みのページ数
    pub current: u32,
    /// 予想総ページ数（上限設定時）。未定時は現状のページ数と同値
    pub total: u32,
    /// ステータス種別。フロントエンドで表示切り替えに使用
    /// - `"capturing"` : キャプチャ実行中
    /// - `"page_turn"` : ページ送りキー入力中
    /// - `"waiting"`   : ページ遷移待機中
    /// - `"completed"` : 全ページキャプチャ完了
    /// - `"stopped"`   : ユーザー停止
    /// - `"error"`     : エラー発生
    pub status: String,
    /// ユーザー向けメッセージ（UI にそのまま表示される）
    pub message: String,
    /// キャプチャ画像の保存先フォルダパス（完了時やキャプチャ中に通知）
    pub capture_folder: Option<String>,
}

/// 連続キャプチャの停止フラグ（スレッドセーフ）
///
/// `static` な `OnceLock` で初期化し、アプリ単位で1つだけ存在する。
/// 連続キャプチャ開始時に `false` を設定し、停止コマンドで `true` にする。
/// バックグラウンドスレッドはこのフラグをポーリングして終了判定を行う。
static STOP_FLAG: OnceLock<Arc<AtomicBool>> = OnceLock::new();

/// 連続キャプチャ実行中フラグ
///
/// 同時に複数の連続キャプチャを防止するためのフラグ。
static IS_CAPTURING: OnceLock<Arc<AtomicBool>> = OnceLock::new();

/// 停止フラグを取得または初期化する
///
/// `OnceLock::get_or_init` で初回アクセス時に `Arc<AtomicBool::new(false)>` を生成する。
/// これにより、アプリ起動後の初回キャプチャ開始時に自動的に初期化される。
fn get_stop_flag() -> Arc<AtomicBool> {
    STOP_FLAG.get_or_init(|| Arc::new(AtomicBool::new(false))).clone()
}

/// 実行中フラグを取得または初期化する
fn get_is_capturing() -> Arc<AtomicBool> {
    IS_CAPTURING.get_or_init(|| Arc::new(AtomicBool::new(false))).clone()
}

/// 連続キャプチャを開始する
///
/// # 処理フロー
/// 1. 既存の連続キャプチャが実行中でないことを確認（重複防止）
/// 2. 停止フラグ・実行中フラグを初期化（`false` にリセット）
/// 3. 保存先フォルダを作成（`~/Pictures/BookCapture/<book_title>/`）
/// 4. バックグラウンドスレッドを生成し、キャプチャループを開始
/// 5. 保存先フォルダパスをフロントエンドに返却
///
/// # 引数
/// - `app_handle`: Tauri AppHandle（イベント送信に使用）
/// - `profile`: 選択中のキャプチャプロファイル（ページ送りキー・待機時間を含む）
/// - `book_title`: 出力フォルダ名に使用する書籍タイトル（空欄時は `"untitled"`）
///
/// # 戻り値
/// - `Ok(String)`: キャプチャ画像の保存先フォルダパス
/// - `Err(String)`: 既に実行中、またはフォルダ作成失敗時のエラーメッセージ
#[tauri::command]
pub fn start_continuous_capture(
    app_handle: tauri::AppHandle,
    profile: CaptureProfile,
    book_title: String,
) -> Result<String, String> {
    // 既に実行中かチェック（重複開始を防止）
    let is_capturing = get_is_capturing();
    if is_capturing.load(Ordering::SeqCst) {
        return Err("連続キャプチャは既に実行中です".to_string());
    }
    is_capturing.store(true, Ordering::SeqCst);

    // 停止フラグをリセット
    let stop_flag = get_stop_flag();
    stop_flag.store(false, Ordering::SeqCst);

    // 保存先フォルダを作成
    let output_dir = create_capture_folder(&book_title)?;

    // バックグラウンドスレッドで連続キャプチャループを開始
    // `thread::spawn` を使用して WebView スレッドをブロックしない
    let output_dir_clone = output_dir.clone();
    let app_handle_clone = app_handle.clone();
    thread::spawn(move || {
        run_continuous_capture_loop(app_handle_clone, profile, output_dir_clone, stop_flag, is_capturing);
    });

    // 開始完了をフロントエンドに通知
    let _ = app_handle.emit("capture-progress", ProgressPayload {
        current: 0,
        total: 0,
        status: "capturing".to_string(),
        message: "連続キャプチャを開始しました".to_string(),
        capture_folder: Some(output_dir.clone()),
    });

    Ok(output_dir)
}

/// 連続キャプチャを停止する
///
/// グローバルな停止フラグを `true` に設定し、バックグラウンドスレッドに
/// 終了を指示する。スレッドは次のループイテレーションでこのフラグを検知して終了する。
///
/// # 戻り値
/// - `Ok(())`: 停止指示成功
#[tauri::command]
pub fn stop_continuous_capture() -> Result<(), String> {
    let stop_flag = get_stop_flag();
    stop_flag.store(true, Ordering::SeqCst);
    Ok(())
}

/// 連続キャプチャの実際のループ処理
///
/// バックグラウンドスレッド上で実行される。以下のステップを繰り返す：
/// 1. 停止フラグチェック
/// 2. スクリーンショット取得
/// 3. 前回画像との MSE 差分検出（変化なし＝終了判定）
/// 4. PNG 保存（連番: `001.png`, `002.png`, ...）
/// 5. ページ送りキー入力（enigo）
/// 6. プロファイル設定の待機時間でスリープ
///
/// # 引数
/// - `app_handle`: イベント送信用
/// - `profile`: ページ送りキー・待機時間を含むプロファイル
/// - `output_dir`: 画像保存先フォルダパス
/// - `stop_flag`: 停止フラグ（スレッド間共有）
/// - `is_capturing`: 実行中フラグ（完了時に `false` に戻す）
fn run_continuous_capture_loop(
    app_handle: tauri::AppHandle,
    profile: CaptureProfile,
    output_dir: String,
    stop_flag: Arc<AtomicBool>,
    is_capturing: Arc<AtomicBool>,
) {
    // enigo 初期化（キー入力シミュレーション用）
    // macOS では初回実行時に Accessibility 権限が必要
    // Enigo::new() は Result を返すため unwrap で初期化失敗時に panic させる
    let mut enigo = Enigo::new(&Settings::default()).unwrap();

    let mut page_num: u32 = 1;
    let mut prev_image: Option<Vec<u8>> = None;
    // MSE（平均二乗誤差）閾値。環境により調整が必要なため、将来的にプロファイルパラメータ化を検討
    // この値はフルHD画面でアルファチャンネルを含むピクセル差の経験値に基づく
    const MSE_THRESHOLD: f64 = 1000.0;

    loop {
        // --- 停止フラグチェック ---
        if stop_flag.load(Ordering::SeqCst) {
            emit_progress(
                &app_handle,
                page_num.saturating_sub(1),
                page_num.saturating_sub(1),
                "stopped",
                &format!("キャプチャを停止しました（{} ページ取得）", page_num.saturating_sub(1)),
                Some(output_dir.clone()),
            );
            is_capturing.store(false, Ordering::SeqCst);
            break;
        }

        // --- キャプチャ実行 ---
        emit_progress(
            &app_handle,
            page_num.saturating_sub(1),
            page_num,
            "capturing",
            &format!("{} ページ目をキャプチャ中...", page_num),
            Some(output_dir.clone()),
        );

        let image_bytes = match capture_screen_raw() {
            Ok(bytes) => bytes,
            Err(e) => {
                emit_progress(
                    &app_handle,
                    page_num.saturating_sub(1),
                    page_num,
                    "error",
                    &format!("キャプチャエラー: {}", e),
                    Some(output_dir.clone()),
                );
                is_capturing.store(false, Ordering::SeqCst);
                break;
            }
        };

        // --- 前回画像との差分検出（MSE方式）---
        if let Some(ref prev) = prev_image {
            let mse = calculate_mse(prev, &image_bytes);
            if mse < MSE_THRESHOLD {
                // 変化が少ない＝ページ遷移が発生しなかった＝最終ページ到達と判断
                emit_progress(
                    &app_handle,
                    page_num.saturating_sub(1),
                    page_num.saturating_sub(1),
                    "completed",
                    &format!("全 {} ページのキャプチャが完了しました", page_num.saturating_sub(1)),
                    Some(output_dir.clone()),
                );
                is_capturing.store(false, Ordering::SeqCst);
                break;
            }
        }

        // --- 画像保存 ---
        let filename = format!("{:03}.png", page_num);
        let filepath = std::path::Path::new(&output_dir).join(&filename);
        if let Err(e) = std::fs::write(&filepath, &image_bytes) {
            emit_progress(
                &app_handle,
                page_num.saturating_sub(1),
                page_num,
                "error",
                &format!("保存エラー ({}): {}", filename, e),
                Some(output_dir.clone()),
            );
            is_capturing.store(false, Ordering::SeqCst);
            break;
        }

        // 保存成功を通知
        emit_progress(
            &app_handle,
            page_num,
            page_num,
            "capturing",
            &format!("{} ページ目を保存しました", page_num),
            Some(output_dir.clone()),
        );

        prev_image = Some(image_bytes);
        page_num += 1;

        // --- ページ送り ---
        emit_progress(
            &app_handle,
            page_num.saturating_sub(1),
            page_num,
            "page_turn",
            "ページを送ります...",
            Some(output_dir.clone()),
        );

        if let Err(e) = turn_page(&mut enigo, &profile.page_turn_key) {
            emit_progress(
                &app_handle,
                page_num.saturating_sub(1),
                page_num,
                "error",
                &format!("ページ送りエラー: {}", e),
                Some(output_dir.clone()),
            );
            is_capturing.store(false, Ordering::SeqCst);
            break;
        }

        // --- 待機 ---
        // ページ送り後、アプリがレンダリングを完了するまで待機する
        // 待機時間はプロファイルで設定可能（Kindle: 0.15秒, Google Play: 5.0秒 など）
        emit_progress(
            &app_handle,
            page_num.saturating_sub(1),
            page_num,
            "waiting",
            &format!("{:.1} 秒待機中...", profile.page_wait),
            Some(output_dir.clone()),
        );

        thread::sleep(Duration::from_secs_f64(profile.page_wait));
    }
}

/// 生スクリーンショット画像を PNG バイト列として取得する
///
/// `capture_screen()` とは異なり、Base64 エンコードせず生バイト列を返す。
/// 連続キャプチャ時の差分検出・ファイル保存に使用する。
///
/// # 戻り値
/// - `Ok(Vec<u8>)`: PNG 形式の生バイト列
fn capture_screen_raw() -> Result<Vec<u8>, String> {
    let screens = Screen::all().map_err(|e| format!("ディスプレイ取得エラー: {}", e))?;
    if screens.is_empty() {
        return Err("ディスプレイが見つかりません".to_string());
    }
    let screen = &screens[0];
    let image = screen.capture().map_err(|e| format!("キャプチャエラー: {}", e))?;

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

    Ok(buf)
}

/// 2枚の PNG バイト列間の平均二乗誤差（MSE）を計算する
///
/// ピクセルごとの差分の二乗の平均値を計算する。
/// 画像サイズが異なる場合は無限大（`f64::MAX`）を返す。
///
/// # 引数
/// - `prev`: 前回の PNG バイト列
/// - `curr`: 現在の PNG バイト列
///
/// # 戻り値
/// - MSE 値（小さいほど画像が類似している）
fn calculate_mse(prev: &[u8], curr: &[u8]) -> f64 {
    if prev.len() != curr.len() {
        // サイズが異なる場合は完全に異なる画像とみなす
        return f64::MAX;
    }
    let sum_sq_diff: f64 = prev
        .iter()
        .zip(curr.iter())
        .map(|(a, b)| {
            let diff = (*a as i32) - (*b as i32);
            (diff * diff) as f64
        })
        .sum();
    sum_sq_diff / prev.len() as f64
}

/// enigo を使用してページ送りキーを入力する
///
/// プロファイルで設定された `page_turn_key` に応じてキー入力を実行する。
/// 現在サポートしているキー: `"right"`, `"left"`, `"space"`
///
/// # 引数
/// - `enigo`: enigo インスタンス
/// - `key`: キー文字列（プロファイルから取得）
///
/// # 注意
/// macOS では初回実行時に「システム設定 > プライバシーとセキュリティ > アクセシビリティ」から
/// 本アプリへの権限付与が必要となる場合がある。
///
/// enigo 0.6.1 では `key_click` の代わりに `key(key, Direction::Click)` を使用する。
fn turn_page(enigo: &mut Enigo, key: &str) -> Result<(), String> {
    let result = match key {
        "right" => enigo.key(Key::RightArrow, Direction::Click),
        "left" => enigo.key(Key::LeftArrow, Direction::Click),
        "space" => enigo.key(Key::Space, Direction::Click),
        other => return Err(format!("未対応のページ送りキー: {}", other)),
    };
    result.map_err(|e| format!("キー入力エラー: {:?}", e))
}

/// 進捗イベントをフロントエンドに送信する
///
/// `app_handle.emit("capture-progress", payload)` でフロントエンドの
/// `listen("capture-progress")` リスナーに通知する。
/// 送信失敗時も処理を継続（`_` で結果を無視）。
fn emit_progress(
    app_handle: &tauri::AppHandle,
    current: u32,
    total: u32,
    status: &str,
    message: &str,
    capture_folder: Option<String>,
) {
    let _ = app_handle.emit(
        "capture-progress",
        ProgressPayload {
            current,
            total,
            status: status.to_string(),
            message: message.to_string(),
            capture_folder,
        },
    );
}

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

// ═════════════════════════════════════════════════════════════════════════════
// 002004: キャプチャ画像のフォルダ管理
// ═════════════════════════════════════════════════════════════════════════════

/// キャプチャ画像の保存先フォルダを作成する（重複回避付き）
///
/// `dirs::picture_dir()` で取得した Pictures フォルダ配下に
/// `BookCapture/<book_title>/` フォルダを作成する。
/// 同名フォルダが既存の場合は `_1`, `_2`, ... の連番サフィックスを付与する（上限99）。
///
/// # 引数
/// - `book_title`: 書籍タイトル（`""` 時は `"untitled"` を使用）
///
/// # 戻り値
/// - `Ok(String)`: 作成したフォルダの絶対パス
fn create_capture_folder(book_title: &str) -> Result<String, String> {
    let pictures_dir = dirs::picture_dir().ok_or("Pictures ディレクトリを取得できません")?;
    let folder_name = if book_title.trim().is_empty() {
        "untitled"
    } else {
        book_title.trim()
    };

    // まず元の名前で試行
    let mut output_dir = pictures_dir.join("BookCapture").join(folder_name);
    if !output_dir.exists() {
        std::fs::create_dir_all(&output_dir)
            .map_err(|e| format!("フォルダ作成エラー ({}): {}", output_dir.display(), e))?;
        return Ok(output_dir.to_string_lossy().to_string());
    }

    // 重複している場合は _1, _2, ... を試行（上限99）
    for i in 1..=99 {
        let suffixed_name = format!("{}_{}", folder_name, i);
        output_dir = pictures_dir.join("BookCapture").join(suffixed_name);
        if !output_dir.exists() {
            std::fs::create_dir_all(&output_dir)
                .map_err(|e| format!("フォルダ作成エラー ({}): {}", output_dir.display(), e))?;
            return Ok(output_dir.to_string_lossy().to_string());
        }
    }

    Err("フォルダ名の重複が多すぎます（上限99）。手動で整理してください。".to_string())
}

/// 指定フォルダ内の PNG 画像ファイル一覧を取得する
///
/// ファイル名順にソートして返却する。非 PNG ファイルは除外する。
///
/// # 引数
/// - `folder_path`: 対象フォルダの絶対パス
///
/// # 戻り値
/// - `Ok(Vec<String>)`: PNG 画像ファイル名の配列（例: `["001.png", "002.png"]`）
/// - `Err(String)`: フォルダ読み込みエラー時のメッセージ
#[tauri::command]
pub fn list_capture_images(folder_path: String) -> Result<Vec<String>, String> {
    let path = std::path::Path::new(&folder_path);
    if !path.is_dir() {
        return Err(format!("指定されたパスはフォルダではありません: {}", folder_path));
    }

    let mut entries = std::fs::read_dir(path)
        .map_err(|e| format!("フォルダ読み込みエラー: {}", e))?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.is_file() {
                let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
                if ext.eq_ignore_ascii_case("png") {
                    return path.file_name().and_then(|n| n.to_str()).map(String::from);
                }
            }
            None
        })
        .collect::<Vec<String>>();

    // ファイル名順でソート
    entries.sort();

    Ok(entries)
}

/// 指定パスの画像を Base64 エンコードして返却する
///
/// フロントエンドでのサムネイル表示に使用する。
/// ファイルが大きい場合もそのまま読み込む（将来リサイズ対応を検討）。
///
/// # 引数
/// - `filepath`: 画像ファイルの絶対パス
///
/// # 戻り値
/// - `Ok(String)`: Base64 エンコードされた PNG 画像データ
/// - `Err(String)`: ファイル読み込みエラー時のメッセージ
#[tauri::command]
pub fn get_capture_image(filepath: String) -> Result<String, String> {
    let bytes = std::fs::read(&filepath)
        .map_err(|e| format!("ファイル読み込みエラー ({}): {}", filepath, e))?;
    let base64 = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, &bytes);
    Ok(base64)
}

/// 保存フォルダを OS のファイルマネージャーで開く
///
/// `open` crate を使用して、macOS では Finder、Windows ではエクスプローラー、
/// Linux ではデフォルトのファイルマネージャーでフォルダを開く。
///
/// # 引数
/// - `folder_path`: 開くフォルダの絶対パス
///
/// # 戻り値
/// - `Ok(())`: フォルダを開く指示成功
/// - `Err(String)`: フォルダが存在しない、または開く際のエラー
#[tauri::command]
pub fn open_capture_folder(folder_path: String) -> Result<(), String> {
    let path = std::path::Path::new(&folder_path);
    if !path.is_dir() {
        return Err(format!("指定されたパスはフォルダではありません: {}", folder_path));
    }
    open::that(&folder_path)
        .map_err(|e| format!("フォルダを開けません ({}): {}", folder_path, e))?;
    Ok(())
}

