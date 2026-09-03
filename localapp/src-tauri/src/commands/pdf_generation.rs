/// 画像結合 PDF 生成コマンド（ユースケース 008 — OCR なしの単純結合）
///
/// `generate_image_pdf` コマンドで以下の処理を行う：
/// 1. 入力（フォルダ or ZIP ファイル）から画像（001-999.png/jpg）を収集
/// 2. ZIP の場合は一時フォルダに展開し、処理完了後に削除
/// 3. `printpdf` crate を使用し、各画像を A4 ページにアスペクト比維持で配置
/// 4. 進捗イベント `pdf-creation-progress` を emit して UI に反映
///
/// 【独立性について】
/// 本ファイルは `pdf_creation.rs`（検索可能 PDF）と完全に独立している。
/// 画像収集・ZIP 展開のロジックは両ファイルで重複しているが、
/// localapp と backend/ocr-worker の独立性を担保するため、
/// 共通モジュール化は行わず、各自完結の実装とする。
///
/// 【座標系の設計】
/// - A4 サイズ: 210 mm × 297 mm
/// - マージン: 10 mm（四方向）
/// - 画像 px → mm 変換: 300 DPI を前提（1 inch = 25.4 mm = 300 px）
/// - アスペクト比維持、センタリング配置

// ファイルパス操作用の標準ライブラリ
// 入力フォルダ・ZIPファイル・出力先パスの検証・操作用
use std::path::{Path, PathBuf};
// ファイル作成・バッファ書き出しの標準ライブラリ
// 生成した PDF バイナリをディスクに保存するために使用
use std::fs::File;
// バッファ付き Writer（I/O 効率化）
// PDF バイナリの書き出し時に使用
use std::io::BufWriter;
// バイト列を Read トレートとして扱うための構造体
// printpdf の Image decoder にバイト列を渡すために使用
use std::io::Cursor;
// PDF 生成ライブラリ（008007 で選定）
// A4 ドキュメント作成・画像埋め込み・レイヤー操作用
use printpdf::*;
// Tauri のイベント発射（emit）機能
// フロントエンドに進捗イベントを送信するために使用
use tauri::Emitter;

/// PDF 生成の進捗通知用イベントペイロード
///
/// `app_handle.emit("pdf-creation-progress", PdfGenerationProgressPayload)` で
/// フロントエンドに送信される。フロントエンド側は
/// `listen("pdf-creation-progress")` でこのイベントを受信する。
#[derive(Clone, serde::Serialize)]
pub struct PdfGenerationProgressPayload {
    /// 現在処理済みのページ数
    pub current: u32,
    /// 処理対象の総ページ数
    pub total: u32,
    /// ユーザー向けメッセージ
    pub message: String,
}

/// 001-999 の範囲の画像ファイルを収集して昇順で返す
fn collect_images_sorted(folder: &Path) -> Result<Vec<PathBuf>, String> {
    let entries = std::fs::read_dir(folder)
        .map_err(|e| format!("ディレクトリ読み込みエラー: {}", e))?;

    let mut image_files: Vec<PathBuf> = Vec::new();

    for entry in entries {
        let entry = entry.map_err(|e| format!("エントリ読み込みエラー: {}", e))?;
        let path = entry.path();
        if path.is_file() {
            if let Some(ext) = path.extension() {
                let ext_lower = ext.to_string_lossy().to_lowercase();
                if ext_lower == "png" || ext_lower == "jpg" || ext_lower == "jpeg" {
                    if let Some(stem) = path.file_stem() {
                        let stem_str = stem.to_string_lossy();
                        if stem_str.chars().all(|c| c.is_ascii_digit()) {
                            image_files.push(path);
                        }
                    }
                }
            }
        }
    }

    image_files.sort_by(|a, b| {
        let a_stem = a.file_stem().unwrap().to_string_lossy();
        let b_stem = b.file_stem().unwrap().to_string_lossy();
        let a_num = a_stem.parse::<u32>().unwrap_or(0);
        let b_num = b_stem.parse::<u32>().unwrap_or(0);
        a_num.cmp(&b_num)
    });

    if image_files.is_empty() {
        return Err("001-999 の画像ファイルが見つかりません".to_string());
    }

    Ok(image_files)
}

/// ZIP ファイルを一時フォルダに展開する
fn extract_zip_to_temp(zip_path: &str) -> Result<PathBuf, String> {
    let zip_file = File::open(zip_path)
        .map_err(|e| format!("ZIP ファイルオープンエラー: {}", e))?;
    let mut archive = zip::ZipArchive::new(zip_file)
        .map_err(|e| format!("ZIP アーカイブ読み込みエラー: {}", e))?;

    let temp_dir = std::env::temp_dir()
        .join(format!("book2pdf_pdf_gen_{}", uuid_v4()));
    std::fs::create_dir_all(&temp_dir)
        .map_err(|e| format!("一時ディレクトリ作成エラー: {}", e))?;

    for i in 0..archive.len() {
        let mut file = archive.by_index(i)
            .map_err(|e| format!("ZIP エントリ読み込みエラー: {}", e))?;
        let outpath = temp_dir.join(file.name());

        if file.is_dir() {
            std::fs::create_dir_all(&outpath)
                .map_err(|e| format!("ディレクトリ作成エラー: {}", e))?;
        } else {
            if let Some(parent) = outpath.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|e| format!("親ディレクトリ作成エラー: {}", e))?;
            }
            let mut outfile = File::create(&outpath)
                .map_err(|e| format!("ファイル作成エラー: {}", e))?;
            std::io::copy(&mut file, &mut outfile)
                .map_err(|e| format!("ファイル書き込みエラー: {}", e))?;
        }
    }

    Ok(temp_dir)
}

/// UUID v4 風の一意な文字列を生成（一時フォルダ名用）
fn uuid_v4() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let ts = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    format!("{:x}", ts)
}

/// A4 ページサイズ（mm）
const A4_WIDTH_MM: f32 = 210.0;
const A4_HEIGHT_MM: f32 = 297.0;
/// ページマージン（mm）
const MARGIN_MM: f32 = 10.0;
/// DPI（px → mm 変換用）
const DPI: f32 = 300.0;

/// 画像ファイルベクターから A4 PDF を生成する
fn create_image_pdf_impl(
    image_files: &[PathBuf],
    output_path: PathBuf,
    progress_tx: &tokio::sync::mpsc::Sender<PdfGenerationProgressPayload>,
) -> Result<String, String> {
    let total = image_files.len() as u32;

    // A4 ドキュメントを作成（最初のページも同時に作成される）
    let (doc, page1, layer1) = PdfDocument::new(
        "Image Combined PDF",
        Mm(A4_WIDTH_MM),
        Mm(A4_HEIGHT_MM),
        "Layer 1",
    );

    let mut current_page = page1;
    let mut current_layer = layer1;

    for (i, img_path) in image_files.iter().enumerate() {
        let current = (i + 1) as u32;

        // 進捗通知
        let _ = progress_tx.try_send(PdfGenerationProgressPayload {
            current,
            total,
            message: format!("{}/{} ページを処理中...", current, total),
        });

        // 画像ファイルをバイト列として読み込み
        let image_bytes = std::fs::read(img_path)
            .map_err(|e| format!("画像読み込みエラー ({}): {}", img_path.display(), e))?;
        let mut cursor = Cursor::new(&image_bytes);

        // 拡張子からフォーマットを判定し decoder を作成
        let ext = img_path
            .extension()
            .and_then(|e| e.to_str())
            .unwrap_or("png")
            .to_lowercase();

        let image = match ext.as_str() {
            "png" => {
                let decoder = image_crate::codecs::png::PngDecoder::new(&mut cursor)
                    .map_err(|e| format!("PNG decode error ({}): {}", img_path.display(), e))?;
                Image::try_from(decoder)
                    .map_err(|e| format!("printpdf Image from PNG error ({}): {:?}", img_path.display(), e))?
            }
            "jpg" | "jpeg" => {
                let decoder = image_crate::codecs::jpeg::JpegDecoder::new(&mut cursor)
                    .map_err(|e| format!("JPEG decode error ({}): {}", img_path.display(), e))?;
                Image::try_from(decoder)
                    .map_err(|e| format!("printpdf Image from JPEG error ({}): {:?}", img_path.display(), e))?
            }
            _ => {
                return Err(format!(
                    "未対応の画像形式: {} (ファイル: {})",
                    ext,
                    img_path.display()
                ));
            }
        };

        // printpdf の Image から画像サイズ（px）を取得
        let img_w_px = image.image.width.0 as f32;
        let img_h_px = image.image.height.0 as f32;

        // px → mm 変換（300 DPI 基準）
        let img_w_mm = img_w_px * 25.4 / DPI;
        let img_h_mm = img_h_px * 25.4 / DPI;

        // マージンを考慮した最大配置領域
        let max_w = A4_WIDTH_MM - MARGIN_MM * 2.0;
        let max_h = A4_HEIGHT_MM - MARGIN_MM * 2.0;

        // アスペクト比維持でフィットするスケールを計算
        let scale_x = max_w / img_w_mm;
        let scale_y = max_h / img_h_mm;
        let scale = scale_x.min(scale_y).min(1.0);

        let final_w = img_w_mm * scale;
        let final_h = img_h_mm * scale;

        // センタリング
        let x = MARGIN_MM + (max_w - final_w) / 2.0;
        let y = MARGIN_MM + (max_h - final_h) / 2.0;

        // 現在のページのレイヤーに画像を配置
        let layer = doc.get_page(current_page).get_layer(current_layer);
        image.add_to_layer(
            layer.clone(),
            ImageTransform {
                translate_x: Some(Mm(x)),
                translate_y: Some(Mm(y)),
                scale_x: Some(scale as f32),
                scale_y: Some(scale as f32),
                ..Default::default()
            },
        );

        // 最後の画像でなければ次のページを追加
        if i < image_files.len() - 1 {
            let (next_page, next_layer) = doc.add_page(
                Mm(A4_WIDTH_MM),
                Mm(A4_HEIGHT_MM),
                "Layer 1",
            );
            current_page = next_page;
            current_layer = next_layer;
        }
    }

    // PDF を保存
    let file = File::create(&output_path)
        .map_err(|e| format!("PDF ファイル作成エラー: {}", e))?;
    let mut writer = BufWriter::new(file);
    doc.save(&mut writer)
        .map_err(|e| format!("PDF 保存エラー: {:?}", e))?;

    // 完了通知
    let _ = progress_tx.try_send(PdfGenerationProgressPayload {
        current: total,
        total,
        message: format!("PDF ファイルを作成しました（{} ページ）", total),
    });

    Ok(output_path.to_string_lossy().to_string())
}

/// 画像結合 PDF を生成する（非同期コマンド）
///
/// # 処理フロー
/// 1. ZIP の場合は一時フォルダに展開
/// 2. 画像ファイル（001-999）を収集して昇順ソート
/// 3. バックグラウンドスレッドで画像→PDF 統合処理を実行
/// 4. 進捗イベントをリアルタイムに emit
/// 5. 一時フォルダをクリーンアップ（ZIP の場合）
/// 6. 作成された PDF パスを返却
#[allow(non_snake_case)]
#[tauri::command]
pub async fn generate_image_pdf(
    app_handle: tauri::AppHandle,
    sourcePath: String,
    sourceType: String,
    outputPath: String,
) -> Result<String, String> {
    // Step 1: 入力ソースの解決
    let (work_folder, is_temp_folder): (PathBuf, bool) = if sourceType == "zip" {
        let temp = extract_zip_to_temp(&sourcePath)?;
        (temp, true)
    } else {
        (PathBuf::from(&sourcePath), false)
    };

    // Step 2: 画像ファイルを収集
    let image_files = collect_images_sorted(&work_folder)?;
    let total_files = image_files.len() as u32;

    // 進捗通知の初期送信
    let _ = app_handle.emit(
        "pdf-creation-progress",
        PdfGenerationProgressPayload {
            current: 0,
            total: total_files,
            message: format!("画像ファイル {} 枚を検出しました", total_files),
        },
    );

    // Step 3: バックグラウンドスレッドで PDF 作成
    let (progress_tx, mut progress_rx) =
        tokio::sync::mpsc::channel::<PdfGenerationProgressPayload>(32);
    let output_path_clone = PathBuf::from(&outputPath);
    let image_files_clone = image_files.clone();

    let pdf_task = tokio::task::spawn_blocking(move || {
        create_image_pdf_impl(&image_files_clone, output_path_clone, &progress_tx)
    });

    // 進捗イベントを非同期に受信して emit
    let progress_forward = async {
        while let Some(payload) = progress_rx.recv().await {
            let _ = app_handle.emit("pdf-creation-progress", payload);
        }
    };

    let (pdf_result, _) = tokio::join!(pdf_task, progress_forward);

    // Step 4: 一時フォルダのクリーンアップ
    if is_temp_folder {
        let _ = std::fs::remove_dir_all(&work_folder);
    }

    pdf_result.map_err(|e| format!("PDF 作成スレッドでエラーが発生しました: {}", e))?
}
