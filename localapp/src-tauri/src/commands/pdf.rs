/// PDF 読込関連の Tauri コマンド
///
/// `pdfium-render` crate + PDFium 動的ライブラリ（libpdfium.dylib）を使用して、
/// PDF ファイルの各ページを PNG 画像にレンダリングする。
///
/// 【ユースケース 003 — PDF 読込】
/// - `extract_pdf_to_images`: PDF を画像化して出力フォルダに保存
///
/// 【PDFium 動的ライブラリの扱い】
/// 開発時: `src-tauri/pdfium/lib/libpdfium.dylib`
/// 配布時: Tauri の `bundle.resources` により app バンドル内に含まれる。
///         実行時に `current_exe` からの相対パスで検索する。
use pdfium_render::prelude::*;
use std::fs;
use std::path::{Path, PathBuf};
use tauri::Emitter;

/// PDF ファイルパスからデフォルトの出力フォルダパスを計算する
///
/// # 処理概要
/// 選択された PDF ファイル名から拡張子を除いた名前をフォルダ名とし、
/// ユーザーの Pictures ディレクトリ配下の `BookCapture/<basename>/` を
/// デフォルトの出力先として返却する。
///
/// 例: `/Users/xxx/Downloads/sample.pdf` → `/Users/xxx/Pictures/BookCapture/sample`
///
/// # 引数
/// - `pdf_path`: 入力 PDF ファイルの絶対パス
///
/// # 戻り値
/// 成功時: デフォルト出力フォルダの絶対パス
/// 失敗時: エラーメッセージ（String）
#[tauri::command]
pub fn get_pdf_default_output_folder(pdf_path: String) -> Result<String, String> {
    // PDF ファイルパスからファイル名（拡張子除く）を取得
    let path = Path::new(&pdf_path);
    let stem = path
        .file_stem()
        .ok_or_else(|| "PDF ファイル名が取得できません".to_string())?
        .to_string_lossy()
        .to_string();

    if stem.is_empty() {
        return Err("PDF ファイル名が空です".to_string());
    }

    // ユーザーの Pictures ディレクトリを取得
    let pictures_dir = dirs::picture_dir()
        .ok_or_else(|| "Pictures フォルダが取得できません".to_string())?;

    // BookCapture/<stem> を構築
    let output_folder = pictures_dir.join("BookCapture").join(stem);

    Ok(output_folder.to_string_lossy().to_string())
}


/// PDF → 画像変換の進捗通知用イベントペイロード
///
/// `app_handle.emit("pdf-progress", PdfProgressPayload)` でフロントエンドに送信される。
/// フロントエンド側は `listen("pdf-progress")` でこのイベントを受信する。
#[derive(Clone, serde::Serialize)]
pub struct PdfProgressPayload {
    /// 現在処理済みのページ数
    pub current: usize,
    /// PDF の総ページ数
    pub total: usize,
    /// ユーザー向けメッセージ
    pub message: String,
}

/// PDF の各ページを PNG 画像に展開する（非同期コマンド）
///
/// # 処理フロー
/// 1. 入力 PDF ファイルの存在確認
/// 2. 出力フォルダを作成（存在しなければ）
/// 3. PDFium 動的ライブラリのパスを解決
/// 4. バックグラウンドスレッド内で PDFium 初期化 → PDF オープン → ページ数取得
/// 5. PDF オープン直後・各ページ保存直後に `pdf-progress` イベントを emit
/// 6. 各ページを指定 DPI でレンダリングし PNG 保存
/// 7. 完了後、出力フォルダパスを返却
///
/// Tauri の同期コマンドでは JavaScript 側メインスレッドがブロッキングされ、
/// `pdf-progress` イベントをリアルタイムに受信できないため、
/// async コマンド + `tokio::task::spawn_blocking` でバックグラウンドスレッド上で
/// レンダリングを実行する。
///
/// 【pdfium-render の初期化に関する注意】
/// `Pdfium::bind_to_library()` はプロセス内で1回のみ呼び出し可能。
/// async 部で `bind_to_library()` した後、`spawn_blocking` 内で再度呼ぶと
/// `PdfiumLibraryBindingsAlreadyInitialized` エラーになる。
/// そのため、ライブラリパス等の情報のみを `spawn_blocking` に渡し、
/// バックグラウンドスレッド内でまとめて初期化からレンダリングまでを行う。
///
/// # 引数
/// - `app_handle`: Tauri アプリハンドラ（進捗イベント emit 用）
/// - `pdf_path`: 入力 PDF ファイルの絶対パス
/// - `output_folder`: 出力先フォルダの絶対パス
/// - `dpi`: レンダリング解像度（200 / 300 / 400）
///
/// # 戻り値
/// 成功時: 出力フォルダの絶対パス
/// 失敗時: エラーメッセージ（String）
#[tauri::command]
pub async fn extract_pdf_to_images(
    app_handle: tauri::AppHandle,
    pdf_path: String,
    output_folder: String,
    dpi: f32,
) -> Result<String, String> {
    // 入力ファイルの存在確認
    if !Path::new(&pdf_path).is_file() {
        return Err(format!("PDFファイルが見つかりません: {}", pdf_path));
    }

    // 出力フォルダを作成（存在しなければ）
    if let Err(e) = fs::create_dir_all(&output_folder) {
        return Err(format!("出力フォルダの作成に失敗しました: {}", e));
    }

    // PDFium 動的ライブラリのパスを解決
    let library_path = resolve_pdfium_library_path()?;

    // 以降の重いレンダリング処理をバックグラウンドスレッドに委譲する。
    // pdfium-render の `Pdfium::bind_to_library()` はプロセス内で1回のみ呼び出し可能なため、
    // ライブラリパス・PDF パス・DPI・ページ数など「再オープンに必要な情報のみ」を
    // スレッドに渡し、バックグラウンドスレッド内で Pdfium インスタンスを作成して
    // レンダリングを行う。
    let app_handle_for_render = app_handle.clone();
    let pdf_path_for_render = pdf_path.clone();
    let output_folder_path = PathBuf::from(output_folder);

    let result = tokio::task::spawn_blocking(move || {
        render_pdf_pages(
            app_handle_for_render,
            library_path,
            pdf_path_for_render,
            output_folder_path,
            dpi,
        )
    })
    .await
    .map_err(|e| format!("バックグラウンド処理の待機中にエラーが発生しました: {}", e))?;

    result
}

/// PDF ページのレンダリング・保存処理を実行する（バックグラウンドスレッド用）
///
/// # 処理概要
/// バックグラウンドスレッド内で PDFium を初期化し、PDF をオープンしてから
/// 各ページをレンダリング・PNG 保存する。
/// `Pdfium::bind_to_library()` はプロセス内で1回のみ呼び出し可能なため、
/// この関数内でまとめて初期化 → レンダリングを完結させる。
///
/// # 引数
/// - `app_handle`: Tauri アプリハンドラ（進捗イベント emit 用）
/// - `library_path`: PDFium 動的ライブラリのパス
/// - `pdf_path`: 入力 PDF ファイルの絶対パス
/// - `output_folder_path`: 出力先フォルダのパス
/// - `dpi`: レンダリング解像度
///
/// # 戻り値
/// 成功時: 出力フォルダの絶対パス
/// 失敗時: エラーメッセージ（String）
fn render_pdf_pages(
    app_handle: tauri::AppHandle,
    library_path: PathBuf,
    pdf_path: String,
    output_folder_path: PathBuf,
    dpi: f32,
) -> Result<String, String> {
    // PDFium 動的ライブラリからバインディングを作成
    // bind_to_library は指定パスの .dylib / .so / .dll を読み込み、
    // Box<dyn PdfiumLibraryBindings> を返す。
    // プロセス内で1回のみ呼び出し可能なため、本関数内で最初に1回だけ実行する。
    let bindings = Pdfium::bind_to_library(&library_path).map_err(|e| {
        format!(
            "PDFiumライブラリの読み込みに失敗しました ({}): {}",
            library_path.display(),
            e
        )
    })?;

    // Pdfium インスタンスを初期化
    let pdfium = Pdfium::new(bindings);

    // PDF 文書を開き、総ページ数を取得する
    let document = pdfium
        .load_pdf_from_file(&pdf_path, None)
        .map_err(|e| format!("PDFファイルの読み込みに失敗しました: {}", e))?;

    let page_count = document.pages().len() as usize;
    if page_count == 0 {
        return Err("PDFにページが含まれていません".to_string());
    }

    // PDF オープン直後に最初の進捗通知を送信。
    // フロントエンドはこれを受けて total ページ数を表示し、確定的な進捗バーに切り替える。
    let _ = app_handle.emit(
        "pdf-progress",
        PdfProgressPayload {
            current: 0,
            total: page_count,
            message: format!("0 / {} ページを画像化中", page_count),
        },
    );

    // 進捗通知用クロージャ
    // 各ページのレンダリング直後に呼び出し、フロントエンドに滑らかに進捗を反映する。
    let emit_progress = |current: usize| {
        let _ = app_handle.emit(
            "pdf-progress",
            PdfProgressPayload {
                current,
                total: page_count,
                message: format!("{} / {} ページを画像化中", current, page_count),
            },
        );
    };

    // 各ページをレンダリング
    for (index, page) in document.pages().iter().enumerate() {
        let page_number = index + 1;

        // PDF の標準解像度は 72 DPI。
        // scale_page_by_factor(dpi / 72.0) で指定 DPI に応じた倍率でレンダリングする。
        let scale_factor = dpi / 72.0;
        let render_config = PdfRenderConfig::new()
            .scale_page_by_factor(scale_factor)
            .render_form_data(true)
            .use_lcd_text_rendering(true);

        let bitmap = page
            .render_with_config(&render_config)
            .map_err(|e| format!("ページ {} のレンダリングに失敗しました: {}", page_number, e))?;

        // PNG 形式で保存
        // as_image() は Result<DynamicImage, PdfiumError> を返すため ? で展開する。
        let output_path = output_folder_path.join(format!("{:03}.png", page_number));
        let image = bitmap
            .as_image()
            .map_err(|e| format!("ページ {} の画像データ取得に失敗しました: {}", page_number, e))?;

        let rgba_image = image
            .as_rgba8()
            .ok_or_else(|| format!("ページ {} のRGBA画像データ取得に失敗しました", page_number))?;

        // 保存処理をリトライ付きで実行する。
        // 画像サイズが大きいページや、クラウド同期フォルダへの書き込み時に
        // macOS で "Operation timed out (os error 60)" が発生するケースがあるため、
        // 1秒待機して最大2回まで再試行する。
        let mut save_error: Option<image::ImageError> = None;
        for attempt in 0..3 {
            match rgba_image.save(&output_path) {
                Ok(()) => {
                    save_error = None;
                    break;
                }
                Err(e) => {
                    save_error = Some(e);
                    if attempt < 2 {
                        std::thread::sleep(std::time::Duration::from_secs(1));
                    }
                }
            }
        }

        if let Some(e) = save_error {
            return Err(format!(
                "ページ {} の保存に失敗しました（3回試行）: {}（ファイルパス: {}）",
                page_number,
                e,
                output_path.display()
            ));
        }

        // 各ページの保存直後に進捗通知を送信。
        // 大量のページがある場合も、毎ページ emit することで UI に滑らかに反映される。
        emit_progress(page_number);
    }

    // 出力フォルダの絶対パスを文字列で返す
    match output_folder_path.canonicalize() {
        Ok(absolute_path) => Ok(absolute_path.to_string_lossy().to_string()),
        Err(_) => Ok(output_folder_path.to_string_lossy().to_string()),
    }
}

/// PDFium 動的ライブラリのパスを解決する
///
/// 以下の順序で探索する：
/// 1. 環境変数 `PDFIUM_DYNAMIC_LIBRARY_PATH`
/// 2. 実行ファイルのディレクトリから `../Resources/pdfium/lib/libpdfium.dylib`（app bundle 配布時）
/// 3. 開発時の相対パス `src-tauri/pdfium/lib/libpdfium.dylib`
fn resolve_pdfium_library_path() -> Result<PathBuf, String> {
    // 1. 環境変数が設定されていれば優先
    if let Ok(env_path) = std::env::var("PDFIUM_DYNAMIC_LIBRARY_PATH") {
        let path = PathBuf::from(env_path);
        if path.exists() {
            return Ok(path);
        }
    }

    // 2. 実行ファイルのディレクトリから相対パスを探索
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            // app bundle 配布時の典型的なパス
            let bundle_candidate = exe_dir
                .join("../Resources/pdfium/lib/libpdfium.dylib")
                .canonicalize()
                .unwrap_or_else(|_| exe_dir.join("../Resources/pdfium/lib/libpdfium.dylib"));
            if bundle_candidate.exists() {
                return Ok(bundle_candidate);
            }

            // 開発時: cargo run では target/debug/ に実行ファイルがある
            let dev_candidate = exe_dir
                .join("../../pdfium/lib/libpdfium.dylib")
                .canonicalize()
                .unwrap_or_else(|_| exe_dir.join("../../pdfium/lib/libpdfium.dylib"));
            if dev_candidate.exists() {
                return Ok(dev_candidate);
            }
        }
    }

    // 3. カレントディレクトリからの相対パス
    let current_dir_candidate = PathBuf::from("pdfium/lib/libpdfium.dylib");
    if current_dir_candidate.exists() {
        return Ok(current_dir_candidate);
    }

    Err("PDFiumライブラリ（libpdfium.dylib）が見つかりません。開発時は localapp/src-tauri/pdfium/lib/ に配置してください。".to_string())
}
