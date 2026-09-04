/// 検索可能 PDF 生成コマンド（ユースケース 008009 — OCR 付きテキストレイヤー PDF）
///
/// `generate_searchable_pdf` コマンドで以下の処理を行う：
/// 1. 入力（フォルダ or ZIP）から画像ファイル（001-999.png/jpg）を収集・ソート
/// 2. 各画像を `leptess`（Tesseract 5.x の Rust ラッパー）で OCR 処理
/// 3. OCR 結果（word レベルのバウンディングボックス + テキスト）を取得
/// 4. `printpdf` で各画像を A4 ページに配置し、その上に透明テキストレイヤーを描画
/// 5. 進捗イベント `pdf-creation-progress` を emit して UI に反映
///
/// 【OCR エンジンについて】
/// `leptess` 0.14.0（Tesseract 5.x + Leptonica）を使用。
/// 008007 で選定。精度は backend の ndlocr_cli（深層学習ベース）に劣るが、
/// ローカル完結・オフライン動作・追加サーバー不要という利点がある。
///
/// 【座標変換の設計】
/// - Tesseract: 画像の左上を原点 (0,0)、右下方向に座標が増加（px 単位）
/// - printpdf: ページの左下を原点 (0,0)、右上方向に座標が増加（mm 単位）
/// - 変換手順:
///   1. Tesseract bbox (px) → mm 換算（1 inch = 25.4 mm = 300 px）
///   2. A4 fit スケーリング（画像が描画領域に収まるよう縮小・拡大）
///   3. 左下原点への反転: `pdf_y = page_height - margin - scaled_y`
///
/// 【フォントについて】
/// POC 段階では macOS システムフォント「ヒラギノ角ゴシック W3」を使用。
/// TTC（TrueType Collection）形式のため、`printpdf` の対応状況により
/// 後続タスク（008010）で Noto Sans JP（TTF・オープンソース）への切り替えを検討。

// ファイルパス操作用の標準ライブラリ
// 入力フォルダ・画像ファイル・出力先パスの検証・操作用
use std::path::{Path, PathBuf};
// ファイル作成・バッファ書き出しの標準ライブラリ
// 生成した PDF バイナリをディスクに保存するために使用
use std::fs::File;
// バッファ付き Writer（I/O 効率化）
// PDF バイナリの書き出し時に使用
use std::io::BufWriter;

// PDF 生成ライブラリ（008007 で選定、008008 で実装済み）
// A4 ドキュメント作成・画像埋め込み・テキスト描画・レイヤー操作用
use printpdf::*;
// Tauri のイベント発射（emit）トレイト
// `AppHandle<R>::emit()` を呼び出すためにトレイトをスコープに入れる
use tauri::Emitter;

// leptess: Tesseract 5.x + Leptonica の Rust ラッパー（008007 で選定）
// 画像→OCR→(テキスト, バウンディングボックス) の直接取得用
use leptess::LepTess;
// regex: HOCR テキストから bbox + テキストを抽出するための正規表現ライブラリ
// 008009: leptess の get_component_boxes はテキスト情報を返さないため、
// get_hocr_text で HOCR HTML を取得し、正規表現で word レベルのテキストと座標をパースする
use regex::Regex;

/// 検索可能 PDF 生成の進捗通知用イベントペイロード
///
/// `app_handle.emit("pdf-creation-progress", SearchablePdfProgressPayload)` で
/// フロントエンドに送信される。フロントエンド側は
/// `listen("pdf-creation-progress")` でこのイベントを受信する。
#[derive(Clone, serde::Serialize)]
pub struct SearchablePdfProgressPayload {
    /// 現在処理済みのページ数
    pub current: u32,
    /// 処理対象の総ページ数
    pub total: u32,
    /// ユーザー向けメッセージ
    pub message: String,
}

// === 定数（008008 の pdf_generation.rs と同一値） ===

/// A4 用紙の幅（ISO 216 規格）
const A4_WIDTH_MM: f64 = 210.0;
/// A4 用紙の高さ（ISO 216 規格）
const A4_HEIGHT_MM: f64 = 297.0;
/// ページ四辺のマージン（トンボ・裁ち落とし対策）
const MARGIN_MM: f64 = 10.0;
/// 印刷業界標準の解像度（px → mm 換算の基準）
const DPI: f64 = 300.0;
/// 1 インチ = 25.4 mm（px → mm 換算に使用）
const MM_PER_INCH: f64 = 25.4;

/// フォントファイルパス（macOS システムフォント）
///
/// ヒラギノ角ゴシック W3 は日本語表示に対応したゴシック体フォント。
/// TTC（TrueType Collection）形式のため、`printpdf` のフォントパーサーが
/// 対応していない場合は 008010 で Noto Sans JP TTF への切り替えが必要。
const FONT_PATH: &str = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc";

/// Tesseract 言語設定（日本語）
///
/// `jpn.traineddata` が `/opt/homebrew/share/tessdata/` にインストール済み。
/// `None` を指定すると環境変数 `TESSDATA_PREFIX` またはデフォルトパスを参照。
const TESS_LANG: &str = "jpn";

// =============================================================================
// Tauri コマンド
// =============================================================================

/// 画像フォルダ/ZIP から OCR 付き検索可能 PDF を生成する（Tauri コマンド）
///
/// # 引数
/// - `app` — Tauri のAppHandle（イベント emit に使用）
/// - `sourcePath` — 画像フォルダまたは ZIP ファイルのパス
/// - `sourceType` — `"folder"` または `"zip"`
/// - `outputPath` — 生成PDFの出力先ファイルパス（フルパス）
///
/// # 命名について
/// Tauri v2 の `invoke()` は JS 側のキー名と Rust 側の引数名を完全一致で紐付ける。
/// フロントエンドが camelCase (`sourcePath`, `sourceType`, `outputPath`) で送信するため、
/// Rust 側も同じ名前を使用する。`#[allow(non_snake_case)]` で命名規約警告を抑制する。
///
/// # 戻り値
/// - `Ok(String)` — 生成されたPDFファイルのフルパス
/// - `Err(String)` — エラーメッセージ
#[allow(non_snake_case)]
#[tauri::command]
pub async fn create_searchable_pdf(
    app: tauri::AppHandle,
    sourcePath: String,
    sourceType: String,
    outputPath: String,
) -> Result<String, String> {
    let input = Path::new(&sourcePath);
    let out_path = Path::new(&outputPath);

    // ZIP の場合は一時フォルダに展開
    let temp_dir: Option<PathBuf>;
    let source_folder: PathBuf;

    if sourceType.to_lowercase() == "zip" ||
        input.extension().map(|e| e == "zip").unwrap_or(false)
    {
        temp_dir = Some(extract_zip_to_temp(input).map_err(|e| e.to_string())?);
        source_folder = temp_dir.as_ref().unwrap().clone();
    } else {
        temp_dir = None;
        source_folder = input.to_path_buf();
    }

    // 画像収集・ソート
    let images = collect_images_sorted(&source_folder).map_err(|e| e.to_string())?;

    // 出力先ディレクトリが存在しない場合は作成
    if let Some(parent) = out_path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }

    // PDF 生成（内部関数）
    create_searchable_pdf_impl(&app, &images, out_path)
        .map_err(|e| e.to_string())?;

    // 一時フォルダのクリーンアップ（ZIP入力時のみ）
    if let Some(temp) = temp_dir {
        let _ = std::fs::remove_dir_all(temp);
    }

    Ok(out_path.to_string_lossy().to_string())
}

// =============================================================================
// 内部実装
// =============================================================================

/// 検索可能 PDF 生成の核心ロジック
///
/// 各ページについて:
/// 1. `leptess` で OCR 実行 → word レベルの bbox + テキストを取得
/// 2. `printpdf` で A4 ページ作成 → 画像配置 + 透明テキストレイヤー描画
fn create_searchable_pdf_impl<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    image_paths: &[PathBuf],
    output_path: &Path,
) -> Result<(), Box<dyn std::error::Error>> {
    let total = image_paths.len();
    let doc = PdfDocument::empty("Searchable PDF");

    // システムフォントを読み込み（PDF に埋め込む）
    let font_data = std::fs::read(FONT_PATH)?;
    let font = doc.add_external_font(font_data.as_slice())?;

    for (i, img_path) in image_paths.iter().enumerate() {
        // --- 進捗通知: OCR 開始 ---
        let _ = app.emit(
            "pdf-creation-progress",
            SearchablePdfProgressPayload {
                current: i as u32 + 1,
                total: total as u32,
                message: format!("OCR 処理中: {}/{} ページ", i + 1, total),
            },
        );

        // --- OCR 処理（HOCR 方式） ---
        let mut lt = LepTess::new(None, TESS_LANG)?;
        lt.set_image(
            img_path
                .to_str()
                .ok_or("画像パスの文字列変換に失敗しました")?,
        )?;

        // HOCR テキストを取得（HTML 形式、各 word に bbox 属性付き）
        let hocr = lt.get_hocr_text(0)?;

        // HOCR から word レベルの (x1, y1, x2, y2, text) を抽出
        let words = parse_hocr_words(&hocr);

        // --- 画像サイズ・スケーリング計算 ---
        let img = image_crate::open(img_path)?;
        let img_width_px = img.width() as f64;
        let img_height_px = img.height() as f64;

        let img_width_mm = img_width_px / DPI * MM_PER_INCH;
        let img_height_mm = img_height_px / DPI * MM_PER_INCH;

        let scale_x = (A4_WIDTH_MM - 2.0 * MARGIN_MM) / img_width_mm;
        let scale_y = (A4_HEIGHT_MM - 2.0 * MARGIN_MM) / img_height_mm;
        // 画像が描画領域にフィットするスケール（縦横比を維持）
        let scale = scale_x.min(scale_y);

        // --- ページ作成 ---
        let (page_idx, layer_idx) =
            doc.add_page(
                Mm(A4_WIDTH_MM as f32),
                Mm(A4_HEIGHT_MM as f32),
                "Layer1",
            );
        let layer = doc.get_page(page_idx).get_layer(layer_idx);

        // --- 画像配置（008008 と同じロジック） ---
        let img_w_mm = img_width_mm * scale;
        let img_h_mm = img_height_mm * scale;
        let offset_x = (A4_WIDTH_MM - img_w_mm) / 2.0;
        let offset_y = (A4_HEIGHT_MM - img_h_mm) / 2.0;

        // printpdf 0.7 の Image::from_dynamic_image を使用して PNG/JPEG 両対応
        // image_crate は image 0.24.x の別名（Cargo.toml で定義）
        let image = Image::from_dynamic_image(&img);

        let transform = ImageTransform {
            translate_x: Some(Mm(offset_x as f32)),
            translate_y: Some(Mm(offset_y as f32)),
            scale_x: Some(scale as f32),
            scale_y: Some(scale as f32),
            rotate: None,
            dpi: Some(DPI as f32),
        };
        image.add_to_layer(layer.clone(), transform);

        // --- テキストレイヤー描画 ---
        let text_layer = doc.get_page(page_idx).add_layer("text_layer");

        // テキストを「不可視」に設定（画像の上に選択可能なゴーストテキストを配置）
        text_layer.set_text_rendering_mode(TextRenderingMode::Invisible);

        for (ocr_x1, ocr_y1, ocr_x2, ocr_y2, text) in &words {
            // px → mm → A4 fit スケール適用
            let x1_mm = *ocr_x1 as f64 / DPI * MM_PER_INCH * scale;
            let y1_mm = *ocr_y1 as f64 / DPI * MM_PER_INCH * scale;
            // x2_mm は現在の座標計算では直接使用しないが、HOCR bbox の右端を表す
            // 将来の拡張（例: 文字詰め調整）で利用可能なため計算を残す
            let _x2_mm = *ocr_x2 as f64 / DPI * MM_PER_INCH * scale;
            let y2_mm = *ocr_y2 as f64 / DPI * MM_PER_INCH * scale;

            // printpdf 座標系（左下原点）への変換
            let pdf_x = MARGIN_MM + offset_x + x1_mm;
            // y2 は Tesseract の下辺（大きい値）= PDF の上側に近い
            let pdf_y = A4_HEIGHT_MM - MARGIN_MM - offset_y - y2_mm;

            let text_h_mm = y2_mm - y1_mm;
            // フォントサイズ: テキストの高さに近づける（1 mm = 2.83464567 pt）
            let font_size_pt = text_h_mm * 2.83464567;
            // 最小フォントサイズを確保（極端に小さいと選択不能になりやすい）
            let font_size_pt = font_size_pt.max(3.0);

            text_layer.set_font(&font, font_size_pt as f32);
            text_layer.begin_text_section();
            text_layer.set_text_cursor(Mm(pdf_x as f32), Mm(pdf_y as f32));
            text_layer.write_text(text, &font);
            text_layer.end_text_section();
        }
    }

    // --- 進捗通知: 保存中 ---
    let _ = app.emit(
        "pdf-creation-progress",
        SearchablePdfProgressPayload {
            current: total as u32,
            total: total as u32,
            message: "PDF を保存中...".to_string(),
        },
    );

    doc.save(&mut BufWriter::new(File::create(output_path)?))?;
    Ok(())
}

// =============================================================================
// ヘルパー関数（008008 pdf_generation.rs と同一・類似実装）
// =============================================================================

/// 指定フォルダ内の画像ファイル（001-999.png/jpg）を収集し、ファイル名の数字順で昇順ソートして返す
///
/// # 引数
/// - `folder` — 画像ファイルを走査する対象フォルダのパス
///
/// # 戻り値
/// - `Ok(Vec<PathBuf>)` — ソート済みの画像パスリスト
/// - `Err(...)` — フォルダ読み込み失敗、または画像が1枚も見つからない場合
///
/// # 命名規約の由来
/// ファイル名を `u32` にパースしてソートしている。これは `capture.rs` の
/// 連番撮影機能で「001.png」「002.png」…と命名される前提に対応している。
fn collect_images_sorted(
    folder: &Path,
) -> Result<Vec<PathBuf>, Box<dyn std::error::Error>> {
    let mut images = Vec::new();
    for entry in std::fs::read_dir(folder)? {
        let entry = entry?;
        let path = entry.path();
        if let Some(ext) = path.extension() {
            let ext = ext.to_string_lossy().to_lowercase();
            if ext == "png" || ext == "jpg" || ext == "jpeg" {
                images.push(path);
            }
        }
    }
    // ファイル名の数字部分でソート（001.png < 002.png < ... < 010.png）
    images.sort_by(|a, b| {
        let a_num = a
            .file_stem()
            .and_then(|s| s.to_str())
            .and_then(|s| s.parse::<u32>().ok())
            .unwrap_or(0);
        let b_num = b
            .file_stem()
            .and_then(|s| s.to_str())
            .and_then(|s| s.parse::<u32>().ok())
            .unwrap_or(0);
        a_num.cmp(&b_num)
    });
    if images.is_empty() {
        return Err("指定フォルダに画像ファイル（.png/.jpg/.jpeg）が見つかりません".into());
    }
    Ok(images)
}

/// ZIP ファイルを一時フォルダに展開し、そのフォルダパスを返す
///
/// # 処理フロー
/// 1. システムの一時ディレクトリに `bc-XXXXXXXX` という名前の一意なフォルダを作成
/// 2. ZIP ファイルをそのフォルダに展開
/// 3. 呼び出し元に展開フォルダの `PathBuf` を返す
///
/// # クリーンアップ責任
/// 呼び出し元が処理完了後に `std::fs::remove_dir_all(temp_dir)` で削除すること。
fn extract_zip_to_temp(
    zip_path: &Path,
) -> Result<PathBuf, Box<dyn std::error::Error>> {
    let temp_dir = std::env::temp_dir().join(format!("bc-{}", uuid_v4()));
    std::fs::create_dir_all(&temp_dir)?;

    let file = File::open(zip_path)?;
    let mut archive = zip::ZipArchive::new(file)?;
    archive.extract(&temp_dir)?;

    Ok(temp_dir)
}

/// 一意なファイル名・フォルダ名用の簡易 ID 生成
///
/// # 注意: UUID v4（RFC 4122）ではない
/// 本来の UUID v4 はランダムな 128 bit だが、本実装では以下を理由に簡易版を採用：
/// - PDF 出力ファイル名での衝突回避が主目的で、セキュリティ要件がない
/// - ナノ秒精度タイムスタンプ + アトミックカウンターで実用上の一意性を確保
/// - `uuid` crate を利用しないことで依存を減らす
///
/// ただしテストでの高速連続呼び出しでは、同一ナノ秒内の衝突リスクがあるため
/// `AtomicU64` カウンターで確実に一意性を保証している。
fn uuid_v4() -> String {
    use std::sync::atomic::{AtomicU64, Ordering};
    use std::time::{SystemTime, UNIX_EPOCH};
    static COUNTER: AtomicU64 = AtomicU64::new(0);
    let ts = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos() as u64;
    let count = COUNTER.fetch_add(1, Ordering::SeqCst);
    format!("{:x}{:08x}", ts, count)
}

/// HOCR テキストをパースして word レベルの (x1, y1, x2, y2, text) を抽出する
///
/// Tesseract の HOCR 出力は以下のような HTML 形式をとる：
/// ```html
/// <span class='ocrx_word' id='word_1_1' title='bbox 100 200 150 220; x_wconf 95'>テキスト</span>
/// ```
///
/// 本関数は正規表現で `<span class='ocrx_word' ...>` を検索し、
/// `title` 属性から bbox 座標、タグ内部からテキストを抽出する。
///
/// 【正規表現の設計】
/// - `class='ocrx_word'`:  word レベルの要素を特定
/// - `title='bbox (\d+) (\d+) (\d+) (\d+)`: 4つの整数で x1, y1, x2, y2 をキャプチャ
/// - `>([^<]+)</span>`: タグ内部のテキストを取得（`>` から `</span>` まで）
///
/// # Arguments
/// * `hocr` — Tesseract の `get_hocr_text(0)` で取得した HOCR HTML 文字列
///
/// # Returns
/// Vec<(x1, y1, x2, y2, text)> — 左上→右下の bbox 座標とテキストのリスト
fn parse_hocr_words(hocr: &str) -> Vec<(i32, i32, i32, i32, String)> {
    // 正規表現をコンパイル
    // NOTE: lazy_static でキャッシュすべきだが、本関数の呼び出し回数はページ数に比例し
    // 数十〜数百回程度なので、毎回コンパイルしても実用上問題ない
    let re = Regex::new(
        r#"<span class='ocrx_word'[^>]*title='bbox (\d+) (\d+) (\d+) (\d+)[^']*'[^>]*>([^<]+)</span>"#
    )
    .expect("HOCR パース用正規表現のコンパイルに失敗しました");

    let mut results = Vec::new();
    for cap in re.captures_iter(hocr) {
        // unwrap_or(0) は万が一正規表現がマッチしない場合のフォールバック
        // HOCR の仕様上、マッチしたキャプチャは必ず存在する
        let x1 = cap[1].parse::<i32>().unwrap_or(0);
        let y1 = cap[2].parse::<i32>().unwrap_or(0);
        let x2 = cap[3].parse::<i32>().unwrap_or(0);
        let y2 = cap[4].parse::<i32>().unwrap_or(0);
        let text = cap[5].trim().to_string();
        results.push((x1, y1, x2, y2, text));
    }
    results
}

// =============================================================================
// テストモジュール
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    /// `collect_images_sorted` が既存テストデータの 3 枚を正しく昇順ソートすることを検証
    #[test]
    fn test_collect_images_sorted_existing_data() {
        // cargo test は src-tauri ディレクトリから実行されるため、
        // プロジェクトルート（localapp）からの相対パスでテストデータにアクセスする
        let folder = Path::new("../testdata/003006-backend-ocr-test");
        let images = collect_images_sorted(folder).unwrap();
        assert_eq!(images.len(), 3);
        let stems: Vec<_> = images
            .iter()
            .map(|p| p.file_stem().unwrap().to_string_lossy().to_string())
            .collect();
        assert_eq!(stems, vec!["002", "003", "004"]);
    }

    /// 空フォルダで `collect_images_sorted` がエラーを返すことを確認
    #[test]
    fn test_collect_images_sorted_empty() {
        let empty = Path::new("testdata/does-not-exist-008009");
        let result = collect_images_sorted(empty);
        assert!(result.is_err());
    }

    /// `uuid_v4` が 100 回連続で一意な値を生成することを確認
    #[test]
    fn test_uuid_v4_unique() {
        let mut ids = std::collections::HashSet::new();
        for _ in 0..100 {
            ids.insert(uuid_v4());
        }
        assert_eq!(ids.len(), 100, "uuid_v4 が重複しています");
    }

    /// HOCR パース関数の基本動作を確認
    #[test]
    fn test_parse_hocr_words() {
        let hocr = r#"<span class='ocrx_word' id='word_1_1' title='bbox 100 200 150 220; x_wconf 95'>テスト</span>"#;
        let words = parse_hocr_words(hocr);
        assert_eq!(words.len(), 1);
        assert_eq!(words[0], (100, 200, 150, 220, "テスト".to_string()));
    }

    /// 実際のテストデータで検索可能 PDF を生成する統合テスト
    ///
    /// 本テストは `leptess` + `jpn.traineddata` + システムフォントを必要とする。
    /// 環境に応じて `--ignored` または手動実行することを想定している。
    /// 生成された PDF は `target/test-output/searchable-*.pdf` に保存される。
    #[test]
    #[ignore = "OCR 実行に時間がかかり、環境依存が大きいため手動実行用"]
    fn test_create_searchable_pdf_impl_integration() {
        // `App::app_handle()` を呼び出すために Manager トレイトをスコープに入れる
        use tauri::Manager;
        let app = tauri::test::mock_app();
        let app_handle = app.app_handle();

        // cargo test は src-tauri ディレクトリから実行されるため、
        // プロジェクトルート（localapp）からの相対パスでテストデータにアクセスする
        let input_dir = Path::new("../testdata/003006-backend-ocr-test");
        let images = collect_images_sorted(input_dir).expect("画像収集に失敗");
        assert!(!images.is_empty(), "テスト画像が見つかりません");

        let out_dir = Path::new("target/test-output");
        std::fs::create_dir_all(out_dir).expect("出力ディレクトリ作成に失敗");
        let out_path = out_dir.join(format!("searchable-{}.pdf", uuid_v4()));

        create_searchable_pdf_impl(app_handle, &images, &out_path)
            .expect("検索可能 PDF 生成に失敗");

        assert!(out_path.exists(), "PDF ファイルが生成されていません");
        let metadata = std::fs::metadata(&out_path).expect("メタデータ取得に失敗");
        assert!(metadata.len() > 0, "PDF ファイルが空です");
    }
}
