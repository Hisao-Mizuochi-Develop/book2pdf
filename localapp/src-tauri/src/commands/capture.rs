/// 画面キャプチャ関連の Tauri コマンド
///
/// `xcap` crate を使用してウィンドウ単位のスクリーンショットを取得し、
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
use crate::models::capture_profile::{CaptureProfile, ProfileEntry, CropInsets};
use xcap::Window;

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
    bookTitle: String,
    startFromBeginning: bool,
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
    let output_dir = create_capture_folder(&bookTitle)?;

    // バックグラウンドスレッドで連続キャプチャループを開始
    // `thread::spawn` を使用して WebView スレッドをブロックしない
    let output_dir_clone = output_dir.clone();
    let app_handle_clone = app_handle.clone();
    let profile_clone = profile.clone();
    thread::spawn(move || {
        run_continuous_capture_loop(
            app_handle_clone,
            profile_clone,
            output_dir_clone,
            stop_flag,
            is_capturing,
            startFromBeginning,
        );
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
    start_from_beginning: bool,
) {
    // enigo 初期化（キー入力シミュレーション用）
    // macOS では初回実行時に Accessibility 権限が必要
    // Enigo::new() は Result を返すため unwrap で初期化失敗時に panic させる
    let mut enigo = Enigo::new(&Settings::default()).unwrap();

    let mut page_num: u32 = 1;
    let mut prev_image: Option<image::RgbaImage> = None;
    // MSE（平均二乗誤差）閾値。環境により調整が必要なため、将来的にプロファイルパラメータ化を検討
    // この値はフルHD画面でアルファチャンネルを含むピクセル差の経験値に基づく
    const MSE_THRESHOLD: f64 = 1000.0;

    // 【002008-1 デバッグ】リトライ回数と待機時間のログ出力用
    eprintln!("[002008-1 DEBUG] 連続キャプチャループ開始: profile={:?}", profile);

    // --- 先頭ページ復帰処理 ---
    // 「先頭ページから」が選択された場合、逆方向ページ送りを連続実行して先頭に戻る。
    // 先頭到達の判定は「スクリーンショットを撮りながらMSE差分を検出」することで行う。
    // 前回画像とほぼ同じ＝「これ以上逆方向にページを変更できない（先頭到達）」と判定。
    if start_from_beginning {
        emit_progress(
            &app_handle,
            0,
            0,
            "page_turn",
            "先頭ページに戻っています...",
            Some(output_dir.clone()),
        );

        // 先頭復帰前に最前面化（キー入力が確実に届くようフォーカスを当てる）
        if !profile.window_title_keyword.is_empty() {
            if let Err(e) = bring_window_to_front(&profile) {
                eprintln!("[002008-2] 先頭復帰: 最前面化失敗 {}", e);
            } else {
                // AppleScript 実行後、ウィンドウが前面に来るまで待機
                thread::sleep(Duration::from_millis(1500));
            }
        }

        let mut prev_reverse_image: Option<image::RgbaImage> = None;
        const MAX_REVERSE_PAGES: u32 = 200;
        // 先頭復帰時のMSE閾値。通常キャプチャより低く設定し、わずかな変化も検出する
        const REVERSE_MSE_THRESHOLD: f64 = 50.0;

        for i in 1..=MAX_REVERSE_PAGES {
            if stop_flag.load(Ordering::SeqCst) {
                break;
            }

            // 逆方向ページ送り
            if let Err(e) = turn_page_reverse(&mut enigo, &profile.page_turn_key) {
                eprintln!("[002008-2] 先頭復帰: ページ送りエラー {}", e);
                break;
            }
            // 画面遷移が安定するまで待機
            thread::sleep(Duration::from_millis(150));

            // 現在画面をキャプチャして変化を確認
            let current_image = match capture_window_image(&profile) {
                Ok(img) => img,
                Err(e) => {
                    eprintln!("[002008-2] 先頭復帰: キャプチャ失敗 {}", e);
                    break;
                }
            };

            // 前回画像と比較。変化がほぼなければ先頭到達と判定
            if let Some(ref prev) = prev_reverse_image {
                let mse = calculate_mse(prev, &current_image);
                if mse < REVERSE_MSE_THRESHOLD {
                    emit_progress(
                        &app_handle,
                        0,
                        0,
                        "page_turn",
                        "先頭ページに到達しました",
                        Some(output_dir.clone()),
                    );
                    break;
                }
            }
            prev_reverse_image = Some(current_image);

            if i % 20 == 0 {
                emit_progress(
                    &app_handle,
                    0,
                    0,
                    "page_turn",
                    &format!("先頭ページに戻っています... ({}ページ戻り)", i),
                    Some(output_dir.clone()),
                );
            }
        }

        // 先頭復帰後、アプリがレンダリングを安定させるため待機
        thread::sleep(Duration::from_millis(500));
    }

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

        // --- 最前面化（002008-1: xcap では非最前面ウィンドウがキャプチャ不可のため常に実行）---
        if !profile.window_title_keyword.is_empty() {
            if let Err(e) = bring_window_to_front(&profile) {
                emit_progress(
                    &app_handle,
                    page_num.saturating_sub(1),
                    page_num,
                    "error",
                    &format!("最前面化エラー: {}", e),
                    Some(output_dir.clone()),
                );
            } else {
                // ウィンドウが前面に来るまで1500ms待機
                // AppleScript 実行後、ウィンドウのレンダリングが完了するまでの時間を確保
                thread::sleep(Duration::from_millis(1500));
            }
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

        // RgbaImage を直接取得（PNG エンコードせずに MSE 比較で使用）
        let mut current_image = match capture_window_image(&profile) {
            Ok(img) => img,
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

        // crop_insets を適用（設定されている場合）
        let insets = &profile.crop_insets;
        if insets.top > 0 || insets.right > 0 || insets.bottom > 0 || insets.left > 0 {
            match apply_crop_insets_to_rgba(&current_image, insets) {
                Ok(cropped) => current_image = cropped,
                Err(e) => {
                    emit_progress(
                        &app_handle,
                        page_num.saturating_sub(1),
                        page_num,
                        "error",
                        &format!("トリミングエラー: {}", e),
                        Some(output_dir.clone()),
                    );
                    is_capturing.store(false, Ordering::SeqCst);
                    break;
                }
            }
        }

        // --- 前回画像との差分検出（MSE方式）---
        if let Some(ref prev) = prev_image {
            let mse = calculate_mse(prev, &current_image);
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

        // --- PNG エンコード & 画像保存 ---
        let image_bytes = match rgba_to_png(&current_image) {
            Ok(bytes) => bytes,
            Err(e) => {
                emit_progress(
                    &app_handle,
                    page_num.saturating_sub(1),
                    page_num,
                    "error",
                    &format!("PNG エンコードエラー: {}", e),
                    Some(output_dir.clone()),
                );
                is_capturing.store(false, Ordering::SeqCst);
                break;
            }
        };

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

        prev_image = Some(current_image);
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
            &format!("{:.2} 秒待機中...", profile.page_wait),
            Some(output_dir.clone()),
        );

        thread::sleep(Duration::from_secs_f64(profile.page_wait));
    }
}

/// PNG バイト列に crop_insets を適用してトリミングする
///
/// `image::load_from_memory` で PNG をデコードし、`imageops::crop_imm` で
/// 指定領域を切り出した後、`to_image()` で `ImageBuffer` に変換し、
/// 再度 PNG エンコードして返す。
///
/// `crop_imm()` の返り値は `SubImage<&RgbaImage>` であり、直接生バイト列を
/// 取得できないため、`to_image()` で所有権付きの `ImageBuffer` に変換してから
/// `as_raw()` を使用する。
///
/// # 引数
/// - `image_bytes`: PNG 形式の生バイト列
/// - `insets`: トリミング量（ピクセル単位）
///
/// # 戻り値
/// - `Ok(Vec<u8>)`: トリミング後の PNG 形式生バイト列
fn apply_crop_insets(image_bytes: &[u8], insets: &CropInsets) -> Result<Vec<u8>, String> {
    let img = image::load_from_memory(image_bytes)
        .map_err(|e| format!("画像デコードエラー: {}", e))?;
    let (width, height) = (img.width(), img.height());

    // トリミング量が画像サイズを超えていないか検証
    if insets.left + insets.right >= width || insets.top + insets.bottom >= height {
        return Err("トリミング量が画像サイズを超えています".to_string());
    }

    let crop_w = width - insets.left - insets.right;
    let crop_h = height - insets.top - insets.bottom;

    let rgba = img.to_rgba8();
    let cropped = image::imageops::crop_imm(&rgba, insets.left, insets.top, crop_w, crop_h);
    // SubImage を ImageBuffer に変換して生バイト列を取得する
    let cropped_img = cropped.to_image();

    let mut buf = Vec::new();
    let encoder = image::codecs::png::PngEncoder::new(&mut buf);
    encoder
        .write_image(
            cropped_img.as_raw(),
            crop_w,
            crop_h,
            image::ExtendedColorType::Rgba8,
        )
        .map_err(|e| format!("PNG エンコードエラー: {}", e))?;

    Ok(buf)
}

/// プロファイル設定に基づいて対象ウィンドウを検索する
///
/// `window_title_keyword` が設定されている場合、部分一致でウィンドウを検索する。
/// `process_name` も設定されている場合は、プロセス名でもフィルタリングする。
/// プロセス名比較時は `.exe` 拡張子を無視し、部分一致（contains）で判定する。
/// これにより Windows（"Kindle.exe"）と macOS（"Kindle"）の両方に対応する。
///
/// # 引数
/// - `profile`: キャプチャプロファイル（ウィンドウ検索設定を含む）
///
/// # 戻り値
/// - `Ok(RgbaImage)`: キャプチャした画像データ（image::RgbaImage）
/// - `Err(String)`: ウィンドウが見つからない場合やキャプチャ失敗時のエラーメッセージ
fn capture_window_image(profile: &CaptureProfile) -> Result<image::RgbaImage, String> {
    // window_title_keyword が設定されていない場合はスクリーンキャプチャにフォールバック
    if profile.window_title_keyword.is_empty() {
        let windows = Window::all()
            .map_err(|e| format!("ウィンドウ一覧取得エラー: {}", e))?;
        let screen = windows.into_iter().next()
            .ok_or("スクリーンが見つかりません".to_string())?;
        return screen.capture_image()
            .map_err(|e| format!("キャプチャエラー: {}", e));
    }

    let keyword_lower = profile.window_title_keyword.to_lowercase();
    const MAX_RETRIES: u32 = 3;

    for attempt in 1..=MAX_RETRIES {
        eprintln!("[002008-1 DEBUG] capture_window_image 試行 {}/{}", attempt, MAX_RETRIES);

        let windows = Window::all()
            .map_err(|e| format!("ウィンドウ一覧取得エラー: {}", e))?;

        if windows.is_empty() {
            eprintln!("[002008-1 DEBUG] 試行 {}/{}: ウィンドウ一覧が空", attempt, MAX_RETRIES);
            if attempt < MAX_RETRIES {
                thread::sleep(Duration::from_millis(500));
                continue;
            }
            return Err("ウィンドウが見つかりません".to_string());
        }

        let target = windows.into_iter().find(|w| {
            let title_matches = w.title().to_lowercase().contains(&keyword_lower);
            if !title_matches {
                return false;
            }
            if !profile.process_name.is_empty() {
                let app_name_lower = w.app_name().to_lowercase();
                let process_query = profile.process_name.to_lowercase()
                    .trim_end_matches(".exe")
                    .to_string();
                app_name_lower.contains(&process_query)
            } else {
                true
            }
        });

        match target {
            Some(window) => {
                let title = window.title();
                let app = window.app_name();
                eprintln!(
                    "[002008-1 DEBUG] 試行 {}/{}: ウィンドウ発見 '{}' (app: {}, {}x{})",
                    attempt, MAX_RETRIES, title, app, window.width(), window.height()
                );
                match window.capture_image() {
                    Ok(img) => {
                        eprintln!(
                            "[002008-1 DEBUG] 試行 {}/{}: キャプチャ成功 ({}x{})",
                            attempt, MAX_RETRIES, img.width(), img.height()
                        );
                        return Ok(img);
                    }
                    Err(e) => {
                        eprintln!(
                            "[002008-1 DEBUG] 試行 {}/{}: キャプチャ失敗 '{}' ({}x{}) : {}",
                            attempt, MAX_RETRIES, title, window.width(), window.height(), e
                        );
                        if attempt < MAX_RETRIES {
                            eprintln!("[002008-1 DEBUG] 500ms 待機後にリトライ");
                            thread::sleep(Duration::from_millis(500));
                            continue;
                        }
                        return Err(format!(
                            "ウィンドウキャプチャエラー: {} (ウィンドウ: '{}', {}x{})",
                            e, title, window.width(), window.height()
                        ));
                    }
                }
            }
            None => {
                eprintln!(
                    "[002008-1 DEBUG] 試行 {}/{}: ウィンドウ '{}' が見つからない",
                    attempt, MAX_RETRIES, keyword_lower
                );
                if attempt < MAX_RETRIES {
                    thread::sleep(Duration::from_millis(500));
                    continue;
                }
                let available_windows: Vec<String> = Window::all()
                    .map_err(|e| format!("ウィンドウ一覧取得エラー: {}", e))?
                    .iter()
                    .map(|w| format!("{} (app: {})", w.title(), w.app_name()))
                    .collect();
                return Err(format!(
                    "'{}' に一致するウィンドウが見つかりません\n見つかったウィンドウ一覧:\n{}",
                    keyword_lower,
                    available_windows.join("\n")
                ));
            }
        }
    }

    // ループを抜けた場合（通常は到達しない）
    Err("ウィンドウキャプチャに失敗しました（リトライ上限に達しました）".to_string())
}

/// 生スクリーンショット画像を PNG バイト列として取得する（ウィンドウ指定キャプチャ + トリミング対応）
///
/// # 処理フロー
/// 1. `xcap::Window::all()` で全ウィンドウを取得
/// 2. `window_title_keyword` が設定されていれば部分一致で対象ウィンドウを検索
/// 3. `process_name` も設定されていればプロセス名でフィルタリング
/// 4. 対象ウィンドウの `capture_image()` でスクリーンショット取得
/// 5. `crop_insets` が設定されていれば内容領域トリミングを適用
///
/// 【002008】xcap crate を使用したウィンドウ指定キャプチャ。
/// `Window::all()` でウィンドウ一覧を取得し、タイトルの部分一致で対象ウィンドウを
/// 特定してから `capture_image()` でキャプチャする。
/// `window_title_keyword` が未設定の場合は全画面キャプチャにフォールバックする。
///
/// # 引数
/// - `profile`: キャプチャプロファイル（ウィンドウ検索・トリミング設定を含む）
///
/// # 戻り値
/// - `Ok(Vec<u8>)`: PNG 形式の生バイト列
fn capture_screen_raw(profile: &CaptureProfile) -> Result<Vec<u8>, String> {
    let image = capture_window_image(profile)?;

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

    // crop_insets が設定されていればトリミング適用
    let insets = &profile.crop_insets;
    if insets.top > 0 || insets.right > 0 || insets.bottom > 0 || insets.left > 0 {
        apply_crop_insets(&buf, insets)
    } else {
        Ok(buf)
    }
}

/// 2枚の RgbaImage 間の平均二乗誤差（MSE）を計算する
///
/// ピクセルごとに RGBA 各チャネルの差分の二乗和を計算し、
/// 総ピクセル数で平均した値を返す。
/// 画像サイズ（幅・高さ）が異なる場合は無限大（`f64::MAX`）を返す。
///
/// # 引数
/// - `prev`: 前回のキャプチャ画像（`image::RgbaImage`）
/// - `curr`: 現在のキャプチャ画像（`image::RgbaImage`）
///
/// # 戻り値
/// - MSE 値（小さいほど画像が類似している）
fn calculate_mse(prev: &image::RgbaImage, curr: &image::RgbaImage) -> f64 {
    if prev.width() != curr.width() || prev.height() != curr.height() {
        // サイズが異なる場合は完全に異なる画像とみなす
        return f64::MAX;
    }
    let prev_pixels = prev.as_raw();
    let curr_pixels = curr.as_raw();
    let sum_sq_diff: f64 = prev_pixels
        .iter()
        .zip(curr_pixels.iter())
        .map(|(a, b)| {
            let diff = (*a as i32) - (*b as i32);
            (diff * diff) as f64
        })
        .sum();
    let pixel_count = (prev.width() * prev.height()) as f64;
    sum_sq_diff / pixel_count
}

/// 指定されたウィンドウを最前面に持ってくる
///
/// ` CaptureProfile#use_bring_to_top` が true の場合に、
/// 連続キャプチャのキャプチャ前に呼び出される。
///
/// # 引数
/// - `profile`: キャプチャプロファイル（`process_name` を使用）
///
/// # 戻り値
/// - `Ok(())`: 最前面化成功
/// - `Err(String)`: 最前面化失敗時のエラーメッセージ
fn bring_window_to_front(profile: &CaptureProfile) -> Result<(), String> {
    if profile.process_name.is_empty() {
        return Err("プロセス名が設定されていません".to_string());
    }
    let process_name = profile.process_name
        .trim_end_matches(".exe")
        .to_string();

    #[cfg(target_os = "macos")]
    {
        let script = format!(
            "tell application \"System Events\" to set frontmost of process \"{}\" to true",
            process_name
        );
        let output = std::process::Command::new("osascript")
            .arg("-e")
            .arg(&script)
            .output()
            .map_err(|e| format!("osascript 実行エラー: {}", e))?;
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("最前面化に失敗: {}", stderr));
        }
        Ok(())
    }

    #[cfg(not(target_os = "macos"))]
    {
        // Windows / Linux では未実装（TODO: SetForegroundWindow API 等を検討）
        Ok(())
    }
}

/// RgbaImage に crop_insets を適用してトリミング後の RgbaImage を返す
///
/// `image::imageops::crop_imm` で指定領域を切り出し、`to_image()` で
/// 所有権付きの `ImageBuffer` に変換して返す。
///
/// # 引数
/// - `image`: トリミング前の `RgbaImage`
/// - `insets`: トリミング量（ピクセル単位）
///
/// # 戻り値
/// - `Ok(RgbaImage)`: トリミング後の `RgbaImage`
/// - `Err(String)`: トリミング量が画像サイズを超えている場合のエラー
fn apply_crop_insets_to_rgba(
    image: &image::RgbaImage,
    insets: &CropInsets,
) -> Result<image::RgbaImage, String> {
    let (width, height) = (image.width(), image.height());

    if insets.left + insets.right >= width || insets.top + insets.bottom >= height {
        return Err("トリミング量が画像サイズを超えています".to_string());
    }

    let crop_w = width - insets.left - insets.right;
    let crop_h = height - insets.top - insets.bottom;

    let cropped = image::imageops::crop_imm(image, insets.left, insets.top, crop_w, crop_h);
    Ok(cropped.to_image())
}

/// RgbaImage を PNG バイト列にエンコードする
///
/// `image::codecs::png::PngEncoder` を使用して `RgbaImage` を
/// PNG 形式の `Vec<u8>` に変換する。
///
/// # 引数
/// - `image`: エンコード対象の `RgbaImage`
///
/// # 戻り値
/// - `Ok(Vec<u8>)`: PNG 形式の生バイト列
/// - `Err(String)`: PNG エンコードエラー時のメッセージ
fn rgba_to_png(image: &image::RgbaImage) -> Result<Vec<u8>, String> {
    let mut buf = Vec::new();
    let encoder = image::codecs::png::PngEncoder::new(&mut buf);
    encoder
        .write_image(
            image.as_raw(),
            image.width(),
            image.height(),
            image::ExtendedColorType::Rgba8,
        )
        .map_err(|e| format!("PNG エンコードエラー: {}", e))?;
    Ok(buf)
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
    let page_key = match key {
        "right" => Key::RightArrow,
        "left" => Key::LeftArrow,
        "space" => Key::Space,
        other => return Err(format!("未対応のページ送りキー: {}", other)),
    };
    enigo
        .key(page_key, Direction::Press)
        .map_err(|e| format!("キー入力エラー(press): {:?}", e))?;
    thread::sleep(Duration::from_millis(50));
    enigo
        .key(page_key, Direction::Release)
        .map_err(|e| format!("キー入力エラー(release): {:?}", e))
}

/// enigo を使用して逆方向のページ送りキーを入力する（先頭ページ復帰用）
///
/// `turn_page` の逆方向キーを入力する。先頭ページに戻る際に使用する。
/// "right" → LeftArrow, "left" → RightArrow
///
/// # 引数
/// - `enigo`: enigo インスタンス
/// - `key`: ページ送りキー文字列（プロファイルから取得）
fn turn_page_reverse(enigo: &mut Enigo, key: &str) -> Result<(), String> {
    let reverse_key = match key {
        "right" => Key::LeftArrow,
        "left" => Key::RightArrow,
        other => return Err(format!("未対応のページ送りキー: {}", other)),
    };
    enigo.key(reverse_key, Direction::Press)
        .map_err(|e| format!("逆方向キー入力エラー(press): {:?}", e))?;
    thread::sleep(Duration::from_millis(50));
    enigo.key(reverse_key, Direction::Release)
        .map_err(|e| format!("逆方向キー入力エラー(release): {:?}", e))
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

/// スクリーンショットを取得して Base64 PNG として返却する
///
/// # 処理フロー
/// 1. `capture_screen_raw()` でウィンドウ指定キャプチャを実行
///    - `xcap::Window::all()` で全ウィンドウを取得
///    - `window_title_keyword` が設定されていれば部分一致で対象ウィンドウを検索
/// 2. PNG 形式にエンコード
/// 3. Base64 エンコードして JSON で返却
///
/// # 戻り値
/// - `Ok(CaptureResult)`: キャプチャ成功時（base64, width, height を含む）
/// - `Err(String)`: キャプチャ失敗時のエラーメッセージ
///
/// # 注意
/// macOS で実行する場合、初回実行時に「画面収録」権限の許可が必要となる
#[tauri::command]
pub fn capture_screen(profile: Option<CaptureProfile>) -> Result<CaptureResult, String> {
    // プロファイルが指定されない場合はデフォルト値（全画面キャプチャ、トリミングなし）
    let profile = profile.unwrap_or_default();

    let png_bytes = capture_screen_raw(&profile)?;

    // Base64 エンコード
    let base64 = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, &png_bytes);

    // PNG バイト列から幅・高さを取得（トリミング後の実際のサイズを反映）
    let (width, height) = image::load_from_memory(&png_bytes)
        .map(|img| (img.width(), img.height()))
        .map_err(|e| format!("画像解析エラー: {}", e))?;

    Ok(CaptureResult {
        base64,
        width,
        height,
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

// ═════════════════════════════════════════════════════════════════════════════
// 005001: ZIP アーカイブ化
// ═════════════════════════════════════════════════════════════════════════════

/// ZIP 作成進捗通知用イベントペイロード
///
/// `app_handle.emit("zip-progress", ZipProgressPayload)` でフロントエンドに送信される。
/// フロントエンド側は `listen("zip-progress")` でこのイベントを受信する。
#[derive(Clone, serde::Serialize)]
pub struct ZipProgressPayload {
    /// 現在処理済みのファイル数
    pub current: u32,
    /// 処理対象の総ファイル数
    pub total: u32,
    /// ユーザー向けメッセージ
    pub message: String,
}

/// 指定フォルダ内の画像ファイルを ZIP アーカイブにまとめる
///
/// # 処理フロー
/// 1. フォルダ内の `.png`/`.jpg`/`.jpeg` ファイルを拡張子フィルタで抽出
/// 2. ファイル名順に `sort()` でソート（`pdf_builder.py: images_to_pdf` と同じパターン）
/// 3. `zip::ZipWriter` で順次 ZIP エントリに追加（`CompressionMethod::Deflated`）
/// 4. 20ファイルごとに `zip-progress` イベントを emit（進捗コールバック方式）
/// 5. 完了後、出力ファイルパスを返却
///
/// # 引数
/// - `app_handle`: Tauri AppHandle（イベント送信に使用）
/// - `folderPath`: 入力画像フォルダの絶対パス
/// - `outputPath`: 出力 ZIP ファイルの絶対パス（`.zip` 拡張子がなければ自動付与）
///
/// # 戻り値
/// - `Ok(String)`: 作成した ZIP ファイルの絶対パス
/// - `Err(String)`: 入力フォルダが存在しない、画像がない、または書き込みエラー時のメッセージ
#[tauri::command]
pub fn create_zip_archive(
    app_handle: tauri::AppHandle,
    folderPath: String,
    outputPath: String,
) -> Result<String, String> {
    use std::io::Write;
    use zip::write::SimpleFileOptions;

    let folder = std::path::Path::new(&folderPath);
    if !folder.is_dir() {
        return Err(format!("指定されたパスはフォルダではありません: {}", folderPath));
    }

    // 対象画像ファイルを抽出（拡張子フィルタ）
    let image_extensions = ["png", "jpg", "jpeg"];
    let mut image_files: Vec<std::path::PathBuf> = std::fs::read_dir(folder)
        .map_err(|e| format!("フォルダ読み込みエラー: {}", e))?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.is_file() {
                let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("").to_lowercase();
                if image_extensions.contains(&ext.as_str()) {
                    return Some(path);
                }
            }
            None
        })
        .collect();

    // ファイル名順でソート（連番画像の順序を維持するため）
    image_files.sort();

    if image_files.is_empty() {
        return Err("指定されたフォルダに画像ファイル（.png/.jpg/.jpeg）が見つかりません".to_string());
    }

    // 出力パスに .zip 拡張子がなければ追加
    let mut output_path = outputPath;
    if !output_path.to_lowercase().ends_with(".zip") {
        output_path.push_str(".zip");
    }

    // 出力先の親フォルダが存在しなければ作成
    if let Some(parent) = std::path::Path::new(&output_path).parent() {
        if !parent.exists() {
            std::fs::create_dir_all(parent)
                .map_err(|e| format!("出力フォルダ作成エラー: {}", e))?;
        }
    }

    let total_files = image_files.len() as u32;

    // ZIP ファイル作成
    let zip_file = std::fs::File::create(&output_path)
        .map_err(|e| format!("ZIP ファイル作成エラー ({}): {}", output_path, e))?;
    let mut zip_writer = zip::ZipWriter::new(zip_file);
    let options = SimpleFileOptions::default()
        .compression_method(zip::CompressionMethod::Deflated);

    for (i, img_path) in image_files.iter().enumerate() {
        let i_u32 = i as u32;
        let filename = img_path.file_name()
            .and_then(|n| n.to_str())
            .ok_or_else(|| format!("不正なファイル名: {}", img_path.display()))?;

        // ファイル読み込み
        let bytes = std::fs::read(img_path)
            .map_err(|e| format!("ファイル読み込みエラー ({}): {}", filename, e))?;

        // ZIP エントリに追加
        zip_writer.start_file(filename, options)
            .map_err(|e| format!("ZIP エントリ追加エラー ({}): {}", filename, e))?;
        zip_writer.write_all(&bytes)
            .map_err(|e| format!("ZIP 書き込みエラー ({}): {}", filename, e))?;

        // 20ファイルごとに進捗イベントを emit（pdf_extractor.py の進捗コールバックパターンを踏襲）
        if (i + 1) % 20 == 0 || i + 1 == image_files.len() {
            let _ = app_handle.emit("zip-progress", ZipProgressPayload {
                current: i_u32 + 1,
                total: total_files,
                message: format!("{}/{} ファイルを圧縮中...", i_u32 + 1, total_files),
            });
        }
    }

    zip_writer.finish()
        .map_err(|e| format!("ZIP ファイルの finalize エラー: {}", e))?;

    // 完了イベントを emit
    let _ = app_handle.emit("zip-progress", ZipProgressPayload {
        current: total_files,
        total: total_files,
        message: format!("ZIP ファイルを作成しました（{} ファイル）", total_files),
    });

    Ok(output_path)
}

/// トリミングを適用したプレビュー画像を生成する
///
/// 指定された画像ファイルを読み込み、上下左右のトリミング値に従って
/// クロップ処理を行った結果を Base64 エンコードされた PNG として返す。
///
/// 処理フロー：
/// 1. 指定パスの画像ファイルを `image::open` で読み込む
/// 2. トリミング後のサイズを計算（元サイズ - トリミング値）
/// 3. `DynamicImage::crop` で切り抜き処理を実行
/// 4. 切り抜いた画像を PNG 形式でメモリバッファに書き込み
/// 5. Base64 エンコードして文字列として返す
///
/// # 引数
/// - `folder_path`: 画像ファイルがあるフォルダの絶対パス
/// - `filename`: 対象画像ファイル名
/// - `top`: 上側トリミング値（ピクセル）
/// - `right`: 右側トリミング値（ピクセル）
/// - `bottom`: 下側トリミング値（ピクセル）
/// - `left`: 左側トリミング値（ピクセル）
///
/// # 戻り値
/// - `Ok(String)`: Base64 エンコードされたトリミング後の PNG 画像データ
/// - `Err(String)`: ファイル読み込みエラーまたは画像処理エラー時のメッセージ
#[tauri::command]
pub fn apply_crop_preview(
    folder_path: String,
    filename: String,
    top: u32,
    right: u32,
    bottom: u32,
    left: u32,
) -> Result<String, String> {
    let filepath = format!("{}/{}", folder_path, filename);

    // 画像ファイルを読み込む
    let mut img = image::open(&filepath)
        .map_err(|e| format!("画像読み込みエラー ({}): {}", filepath, e))?;

    let (orig_width, orig_height) = (img.width(), img.height());

    // トリミング後のサイズを計算
    // 切り取り後の幅 = 元幅 - 左トリミング - 右トリミング
    // 切り取り後の高さ = 元高さ - 上トリミング - 下トリミング
    let x = left;
    let y = top;
    let width = orig_width.saturating_sub(left + right);
    let height = orig_height.saturating_sub(top + bottom);

    // トリミング後のサイズが 0 以下になる場合はエラー
    if width == 0 || height == 0 {
        return Err("トリミング後の画像サイズが0以下になります".to_string());
    }

    // 画像をクロップ（切り抜き）
    let cropped = img.crop(x, y, width, height);

    // クロップ後の画像を PNG 形式でメモリバッファに書き込み
    let mut buffer = Vec::new();
    {
        let mut cursor = std::io::Cursor::new(&mut buffer);
        cropped
            .write_to(&mut cursor, image::ImageFormat::Png)
            .map_err(|e| format!("PNG エンコードエラー: {}", e))?;
    }

    // Base64 エンコードして返す
    let base64 = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, &buffer);
    Ok(base64)
}
