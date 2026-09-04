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
// PDF 生成ライブラリ（LA008007 で選定）
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

/// 指定フォルダ内の画像ファイル（001-999.png/jpg）を収集し、ファイル名の数字順で昇順ソートして返す
///
/// # 引数
/// - `folder` — 画像ファイルを走査する対象フォルダのパス
///
/// # 戻り値
/// - `Ok(Vec<PathBuf>)` — ソート済みの画像ファイルパスのベクター。ファイル名の数字部分（001, 002 …）で昇順に並ぶ
/// - `Err(String)` — フォルダ読み込み失敗時、または該当する画像ファイルが1枚も存在しない場合
///
/// # 「001-999」の命名規約について
/// この命名規約は `capture.rs`（連番スクリーンショット撮影）で採用されたルールと対応している。
/// 撮影時に `001.png`, `002.png` … のように連番でファイルが作成されるため、
/// そのままのファイル名でページ順を自動認識できる。拡張子は `.png`, `.jpg`, `.jpeg` のいずれかを受け付ける。
///
/// # 処理の流れ
/// 1. `std::fs::read_dir` でフォルダ内のエントリを列挙
/// 2. ファイル名が「数字のみ（001〜999）」かつ拡張子が PNG/JPEG のものをフィルタ
/// 3. `parse::<u32>()` で数値化し、`cmp` で昇順ソート
/// 4. 該当ファイルがなければエラーを返す（空の PDF は意味を持たないため）
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

/// ZIP ファイル（*.zip）をシステムの一時フォルダ内に展開し、展開先のフォルダパスを返す
///
/// # 引数
/// - `zip_path` — 展開対象の ZIP ファイルの絶対パス文字列
///
/// # 戻り値
/// - `Ok(PathBuf)` — 展開されたファイル群が格納された一時フォルダのパス
///   パス形式: `{システム一時フォルダ}/book2pdf_pdf_gen_{一意文字列}/`
/// - `Err(String)` — ZIP ファイルが開けない、または ZIP アーカイブの読み込みに失敗した場合
///
/// # 注意：呼び出し側のクリーンアップ責任
/// 本関数は一時フォルダを**作成するだけ**であり、自動削除は行わない。
/// 呼び出し側（`generate_image_pdf`）で `remove_dir_all` を呼び出し、
/// PDF 生成完了後に必ず一時フォルダを削除すること。そうしないとユーザーのディスクにゴミが残る。
///
/// # 処理の流れ
/// 1. `File::open` で ZIP ファイルをオープン
/// 2. `zip::ZipArchive::new` で ZIP 構造を解析
/// 3. `temp_dir().join()` で一意な一時フォルダ名を生成（`uuid_v4` で命名）
/// 4. `create_dir_all` でフォルダを作成
/// 5. ZIP 内の各ファイルを順次展開し、一時フォルダに書き出し
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

/// 一意なファイル名用文字列を生成する（一時フォルダ名の命名用）
///
/// # 本関数は「UUID v4（RFC 4122）ではない」ことに注意
/// 関数名が `uuid_v4` だが、実体はナノ秒精度のタイムスタンプを16進数文字列化したもの。
/// 暗号学的な一意性やグローバルな衝突耐性は不要で、
/// 同一ユーザーの同一実行環境内で一時フォルダ名が重複しないことが目的のためこの簡易実装としている。
///
/// # 戻り値の形式
/// `{:x}` フォーマットされた UNIX EPOCH からの経過ナノ秒値
/// 例: `16a3b4c5d6e7f890`
fn uuid_v4() -> String {
    use std::sync::atomic::{AtomicU64, Ordering};
    use std::time::{SystemTime, UNIX_EPOCH};

    // 同じナノ秒内に連続で呼ばれた場合も一意性を保証するため、
    // 呼び出し回数をアトミックカウンターでインクリメントして付与する
    static COUNTER: AtomicU64 = AtomicU64::new(0);

    let ts = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let count = COUNTER.fetch_add(1, Ordering::SeqCst);
    format!("{:x}_{:x}", ts, count)
}

/// A4 用紙サイズ（幅）
///
/// ISO 216 で定義された A4 用紙の幅 210 mm。
/// 印刷機関が標準的に対応する用紙サイズを採用し、
/// PDF のページサイズを固定することで、どの環境でも同じ見た目を保証する。
const A4_WIDTH_MM: f32 = 210.0;

/// A4 用紙サイズ（高さ）
///
/// ISO 216 で定義された A4 用紙の高さ 297 mm。
/// スクリーンショット等の横長画像が来た場合は、縦置きの A4 にアスペクト比維持で中心配置する。
const A4_HEIGHT_MM: f32 = 297.0;

/// ページ余白（mm）
///
/// 四方向に 10 mm の余白を設ける。
/// 余白がないと見た目が窮屈になり、かつ印刷時にトンボ（裁ち落とし）により画像が欠けるリスクがあるため、
/// 最低限の余白を設けることをプロジェクトのデザイン方針として定めている。
const MARGIN_MM: f32 = 10.0;

/// 画像解像度（DPI: dots per inch）
///
/// 300 DPI は電子書籍スキャンや印刷業界の標準解像度。
/// スクリーンショットの 96 DPI とは異なり、印刷品質を想定して高解像度を採用する。
/// この値を使って「画像のピクセル数 → mm サイズ」に変換する（1 inch = 25.4 mm = 300 px）。
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

        // マージンを考慮した最大配置領域（余白込みの実際に画像が置ける領域）
        let max_w = A4_WIDTH_MM - MARGIN_MM * 2.0;
        let max_h = A4_HEIGHT_MM - MARGIN_MM * 2.0;

        // アスペクト比維持でフィットするスケールを計算
        // scale_x = 横方向に収めるために必要な倍率（縮小: <1、拡大: >1）
        // scale_y = 縦方向に収めるために必要な倍率
        let scale_x = max_w / img_w_mm;
        let scale_y = max_h / img_h_mm;
        // 縦横のうち小さい方を採用 → 両方の領域に収まるようにする（はみ出し防止）
        // 元画像より拡大（scale > 1）しても A4 にフィットさせる。
        // なぜ拡大を許容するのか：電子書籍の閲覧を優先し、低解像度のソース画像でも
        // PDF 上で極端に小さく表示されるのを防ぐため。画質はソースに依存する。
        let scale = scale_x.min(scale_y);

        let final_w = img_w_mm * scale;
        let final_h = img_h_mm * scale;

        // センタリング：配置可能領域の中央に画像の中心を合わせる
        // 計算式の意味：余白 +（余白を除いた領域 - 実際の画像サイズ）/ 2
        let x = MARGIN_MM + (max_w - final_w) / 2.0;
        let y = MARGIN_MM + (max_h - final_h) / 2.0;

        // 現在のページのレイヤーに画像を配置
        let layer = doc.get_page(current_page).get_layer(current_layer);
        image.add_to_layer(
            layer.clone(),
            ImageTransform {
                // translate_x / translate_y: PDF 座標系（左下が原点）での配置位置（mm）
                // x は左からの距離、y は下からの距離を指定する
                translate_x: Some(Mm(x)),
                translate_y: Some(Mm(y)),
                // scale_x / scale_y: アスペクト比維持のため両方同じ値を設定
                // 異なる値を設定すると画像が縦横に伸び縮みしてしまう
                scale_x: Some(scale as f32),
                scale_y: Some(scale as f32),
                // 回転・スキューは使用しないためデフォルト値
                ..Default::default()
            },
        );

        // 最後の画像でなければ次のページを追加（1画像 = 1ページ）
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

// ────────────────────────────────────────────────
// 単体テスト
// ────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    /// テスト用データフォルダのパスを取得する
    ///
    /// `CARGO_MANIFEST_DIR`（Cargo.toml のあるディレクトリ）から
    /// `../../test_cases/testdata/localapp/LA003006-backend-ocr-test/` への絶対パスを返す。
    fn test_data_dir() -> PathBuf {
        let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        manifest_dir
            .join("..")
            .join("..")
            .join("test_cases")
            .join("testdata")
            .join("localapp")
            .join("LA003006-backend-ocr-test")
    }

    /// 【テスト1】既存テストデータから画像を正しく収集・ソートできること
    ///
    /// テストデータ `LA003006-backend-ocr-test/` 内の `002.png`, `003.png`, `004.png` を
    /// ファイル名順に昇順で収集することを確認する。
    /// 非画像ファイル・非数字ファイル名が混在していても除外されることを兼ねて確認する。
    #[tokio::test]
    async fn test_collect_images_sorted_with_existing_data() {
        let dir = test_data_dir();
        let result = collect_images_sorted(&dir);
        assert!(result.is_ok(), "画像収集に失敗しました: {:?}", result.err());

        let images = result.unwrap();
        assert_eq!(images.len(), 3, "3枚の画像が検出されるべき");

        // ファイル名順に 002, 003, 004 となっていることを確認
        let stems: Vec<String> = images
            .iter()
            .map(|p| p.file_stem().unwrap().to_string_lossy().to_string())
            .collect();
        assert_eq!(stems, vec!["002", "003", "004"]);
    }

    /// 【テスト2】画像が存在しないフォルダでエラーが返ること
    ///
    /// 空の一時フォルダを作成し、`collect_images_sorted` を呼び出す。
    /// 該当画像がないため `Err` が返されることを確認する。
    #[tokio::test]
    async fn test_collect_images_sorted_empty() {
        let temp_dir = std::env::temp_dir().join(format!("test_empty_{}", uuid_v4()));
        fs::create_dir_all(&temp_dir).unwrap();

        let result = collect_images_sorted(&temp_dir);
        assert!(result.is_err(), "空フォルダではエラーが返されるべき");

        // クリーンアップ
        let _ = fs::remove_dir_all(&temp_dir);
    }

    /// 【テスト3】uuid_v4 が一意な値を生成すること
    ///
    /// 100回連続で呼び出し、全ての値が異なることを確認する。
    /// タイムスタンプベースの実装なので、同じナノ秒内に呼ばれても
    /// 基本衝突しないことを検証する。
    #[tokio::test]
    async fn test_uuid_v4_unique() {
        let mut values = Vec::new();
        for _ in 0..100 {
            values.push(uuid_v4());
        }

        let unique_count = values.iter().collect::<std::collections::HashSet<_>>().len();
        assert_eq!(
            unique_count, 100,
            "100回の呼び出しで全て異なる値が生成されるべき"
        );
    }

    /// 【テスト4】create_image_pdf_impl が正しいページ数の PDF を生成すること
    ///
    /// テストデータ `LA003006-backend-ocr-test/` の3枚の画像を使い、
    /// PDF を生成後、`lopdf` でページ数が3であることを確認する。
    #[tokio::test]
    async fn test_create_image_pdf_impl_page_count() {
        let dir = test_data_dir();
        let image_files = collect_images_sorted(&dir).expect("画像収集失敗");
        assert_eq!(image_files.len(), 3);

        // 出力先（一時ファイル）
        let output_path = std::env::temp_dir().join(format!("test_pdf_{}.pdf", uuid_v4()));

        // 進捗通知用チャンネル（テストでは内容は確認しない）
        let (tx, _rx) = tokio::sync::mpsc::channel::<PdfGenerationProgressPayload>(32);

        // PDF 生成実行
        let result = create_image_pdf_impl(&image_files, output_path.clone(), &tx);
        assert!(result.is_ok(), "PDF 生成に失敗: {:?}", result.err());

        // lopdf でページ数を検証
        let doc = lopdf::Document::load(&output_path).expect("PDF 読み込み失敗");
        let pages = doc.get_pages();
        assert_eq!(
            pages.len(),
            3,
            "画像3枚 → PDF 3ページであるべき"
        );

        // クリーンアップ
        let _ = fs::remove_file(&output_path);
    }

    /// 【テスト5】create_image_pdf_impl が空でない PDF を生成すること
    ///
    /// ファイルサイズが 1KB 以上であることを確認し、
    /// 実際に画像データが含まれていることを間接的に検証する。
    #[tokio::test]
    async fn test_create_image_pdf_impl_file_size() {
        let dir = test_data_dir();
        let image_files = collect_images_sorted(&dir).expect("画像収集失敗");

        let output_path = std::env::temp_dir().join(format!("test_pdf_size_{}.pdf", uuid_v4()));
        let (tx, _rx) = tokio::sync::mpsc::channel::<PdfGenerationProgressPayload>(32);

        let result = create_image_pdf_impl(&image_files, output_path.clone(), &tx);
        assert!(result.is_ok(), "PDF 生成に失敗: {:?}", result.err());

        let metadata = fs::metadata(&output_path).expect("メタデータ取得失敗");
        let file_size = metadata.len();
        assert!(
            file_size > 1024,
            "PDF ファイルサイズが 1KB 以上であるべき。実際: {} bytes",
            file_size
        );

        // クリーンアップ
        let _ = fs::remove_file(&output_path);
    }
}
