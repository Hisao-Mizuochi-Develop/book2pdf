/// 003006: localapp → backend API 経由で OCR/PDF 生成を実行するコマンド
///
/// ユーザーが選択した「画像フォルダ」または「ZIP ファイル」を backend API に送信し、
/// ndlocr_cli による OCR → 検索可能 PDF 生成 → ダウンロード までを Rust 側で一貫して処理する。
///
/// 【処理フロー】
/// 1. `~/.config/book2pdf/settings.json` から backend URL 等を読み込む
/// 2. 入力が画像フォルダの場合は一時 ZIP を作成（ZIP の場合はそのまま使用）
/// 3. `POST /api/jobs` でジョブを作成
/// 4. `POST /api/jobs/{job_id}/upload` で ZIP を multipart アップロード
/// 5. `POST /api/jobs/{job_id}/ocr` で OCR 実行
/// 6. `GET /api/jobs/{job_id}` で completed/failed になるまでポーリング
/// 7. `GET /api/jobs/{job_id}/pdf` で生成済み PDF をダウンロード
/// 8. 指定された出力パスに PDF を保存し、一時ファイルをクリーンアップ
///
/// 【進捗通知】
/// 各フェーズで `ocr-progress` イベントを emit する。フロントエンドは
/// `listen("ocr-progress")` で受信し、UI に表示する。
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::time::Duration;

use tauri::{AppHandle, Emitter, Runtime};
use tauri_plugin_http::reqwest;
use zip::write::SimpleFileOptions;

use crate::config::AppSettings;

/// OCR 連携の進捗通知用イベント名
const PROGRESS_EVENT: &str = "ocr-progress";

/// 進捗イベントのペイロード。
///
/// フロントエンド側の `backendApiStore` と型を合わせるため、
/// フィールド名は camelCase に変換して送信する。
#[derive(Clone, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct OcrProgressPayload {
    /// 処理フェーズ。
    /// - `"preparing"` : 入力準備中（ZIP 圧縮含む）
    /// - `"creating"`  : ジョブ作成中
    /// - `"uploading"` : ZIP アップロード中
    /// - `"ocr"`       : OCR 実行中
    /// - `"polling"`   : 状態ポーリング中
    /// - `"downloading"`: PDF ダウンロード中
    /// - `"completed"` : 全完了
    /// - `"error"`     : エラー発生
    pub stage: String,

    /// ユーザー向けメッセージ
    pub message: String,

    /// 現在の進捗（ページ数など）。不明時は None
    pub current: Option<u32>,

    /// 総ページ数など。不明時は None
    pub total: Option<u32>,
}

/// `run_backend_ocr` の実行結果。
#[derive(Clone, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BackendOcrResult {
    /// backend 側で発行されたジョブ ID
    pub job_id: String,

    /// 保存された PDF ファイルの絶対パス
    pub output_path: String,
}
/// backend API を使って OCR 済み PDF を生成する Tauri コマンド。
#[tauri::command]
pub async fn run_backend_ocr<R: Runtime>(
    app: AppHandle<R>,
    source_path: String,
    source_type: String,
    output_path: String,
) -> Result<BackendOcrResult, String> {
    let settings = AppSettings::load()?;
    // /ocr エンドポイントはリクエスト受付後即座に processing を返すようになったが、
    // 通信異常時に無限待ちにならないようタイムアウトを明示的に設定しておく。
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(60))
        .build()
        .map_err(|e| format!("HTTP クライアントの作成に失敗しました: {}", e))?;

    let emit_progress = |stage: &str, message: &str, current: Option<u32>, total: Option<u32>| {
        let _ = app.emit(
            PROGRESS_EVENT,
            OcrProgressPayload {
                stage: stage.to_string(),
                message: message.to_string(),
                current,
                total,
            },
        );
    };

    emit_progress("preparing", "入力ファイルを準備中...", None, None);

    // ZIP パス解決：画像フォルダの場合は一時 ZIP を作成
    let (zip_path, temp_dir): (PathBuf, Option<PathBuf>) = if source_type == "zip" {
        let path = PathBuf::from(&source_path);
        if !path.is_file() {
            return Err(format!("ZIP ファイルが見つかりません: {}", source_path));
        }
        (path, None)
    } else {
        let folder = PathBuf::from(&source_path);
        if !folder.is_dir() {
            return Err(format!("画像フォルダが見つかりません: {}", source_path));
        }
        let dir = std::env::temp_dir()
            .join("book2pdf")
            .join(format!("ocr-{}-temp", uuid::Uuid::new_v4()));
        fs::create_dir_all(&dir)
            .map_err(|e| format!("一時ディレクトリの作成に失敗しました: {}", e))?;
        let zip_path = dir.join("images.zip");
        create_zip_from_folder(&folder, &zip_path, &emit_progress)?;
        (zip_path, Some(dir))
    };

    // 1. ジョブ作成
    // FastAPI のルーターは `@router.post("/")` で定義されており、
    // include 時のプレフィックス `/api/jobs` と合わさってフルパスは `/api/jobs/` になる。
    // trailing slash を付けないと 307 リダイレクトが返されるため、明示的に `/` を付与する。
    emit_progress("creating", "OCR ジョブを作成中...", None, None);
    let create_url = format!("{}/api/jobs/", settings.backend_url);
    let create_resp = client
        .post(&create_url)
        .send()
        .await
        .map_err(|e| format!("ジョブ作成リクエストに失敗しました: {}", e))?;

    if !create_resp.status().is_success() {
        return Err(format!(
            "ジョブ作成が失敗しました (HTTP {})",
            create_resp.status()
        ));
    }

    let create_json: serde_json::Value = create_resp
        .json()
        .await
        .map_err(|e| format!("ジョブ作成レスポンスの解析に失敗しました: {}", e))?;
    let job_id = create_json["job_id"]
        .as_str()
        .ok_or_else(|| "job_id がレスポンスに含まれていません".to_string())?
        .to_string();

    // 2. ZIP アップロード
    emit_progress("uploading", "画像 ZIP をアップロード中...", None, None);
    let upload_url = format!("{}/api/jobs/{}/upload", settings.backend_url, job_id);

    // multipart 用にファイル全体をメモリ上に読み込む。
    // 電子書籍のページ画像を想定したサイズなので問題ないが、
    // 将来的に巨大な ZIP を扱う場合はストリーミング読み込みに変更すること。
    let zip_bytes = fs::read(&zip_path).map_err(|e| {
        format!(
            "ZIP ファイルの読み込みに失敗しました ({}): {}",
            zip_path.display(),
            e
        )
    })?;

    let multipart = reqwest::multipart::Form::new().part(
        "file",
        reqwest::multipart::Part::bytes(zip_bytes)
            .file_name("images.zip")
            .mime_str("application/zip")
            .map_err(|e| format!("multipart の MIME 設定に失敗しました: {}", e))?,
    );

    let upload_resp = client
        .post(&upload_url)
        .multipart(multipart)
        .timeout(Duration::from_secs(600))
        .send()
        .await
        .map_err(|e| format!("ZIP アップロードに失敗しました: {}", e))?;

    if !upload_resp.status().is_success() {
        return Err(format!(
            "ZIP アップロードが失敗しました (HTTP {}): {}",
            upload_resp.status(),
            upload_resp
                .text()
                .await
                .unwrap_or_else(|_| "レスポンス本文が取得できません".to_string())
        ));
    }

    let upload_json: serde_json::Value = upload_resp
        .json()
        .await
        .map_err(|e| format!("アップロードレスポンスの解析に失敗しました: {}", e))?;
    let files = upload_json["files"]
        .as_array()
        .ok_or_else(|| "アップロードレスポンスに files がありません".to_string())?;
    let page_count = files.len() as u32;

    emit_progress(
        "uploaded",
        &format!("{} ページをアップロードしました", page_count),
        Some(0),
        Some(page_count),
    );

    // 3. OCR 実行
    // タイムアウトは「ページ数 × 1ページあたりタイムアウト」とする。
    let total_timeout = Duration::from_secs(settings.page_timeout_sec * page_count.max(1) as u64);

    emit_progress(
        "ocr",
        &format!("OCR を実行中（{} ページ）...", page_count),
        Some(0),
        Some(page_count),
    );

    let ocr_url = format!("{}/api/jobs/{}/ocr", settings.backend_url, job_id);
    // backend の /ocr はリクエスト受付後即座に processing を返すようになったため、
    // ここでは応答待ちタイムアウトを短くしておく。実際の OCR 完了までは後続のポーリングで監視する。
    let ocr_resp = client
        .post(&ocr_url)
        .timeout(Duration::from_secs(60))
        .send()
        .await
        .map_err(|e| format!("OCR 実行リクエストに失敗しました: {}", e))?;

    if !ocr_resp.status().is_success() {
        return Err(format!(
            "OCR 実行が失敗しました (HTTP {}): {}",
            ocr_resp.status(),
            ocr_resp
                .text()
                .await
                .unwrap_or_else(|_| "レスポンス本文が取得できません".to_string())
        ));
    }

    // 4. ジョブ状態ポーリング
    let poll_interval = Duration::from_secs(settings.polling_interval_sec);
    let status_url = format!("{}/api/jobs/{}", settings.backend_url, job_id);
    let deadline = std::time::Instant::now() + total_timeout;

    loop {
        if std::time::Instant::now() > deadline {
            return Err(
                "OCR 処理がタイムアウトしました。page_timeout_sec を長くするか、backend/ocr-worker の状態を確認してください。".to_string(),
            );
        }

        tokio::time::sleep(poll_interval).await;

        let status_resp = client
            .get(&status_url)
            .send()
            .await
            .map_err(|e| format!("ジョブ状態の取得に失敗しました: {}", e))?;

        if !status_resp.status().is_success() {
            continue;
        }

        let status_json: serde_json::Value = status_resp
            .json()
            .await
            .map_err(|e| format!("ジョブ状態レスポンスの解析に失敗しました: {}", e))?;
        let status = status_json["status"].as_str().unwrap_or("");

        match status {
            "completed" => break,
            "failed" => {
                let message = status_json["message"]
                    .as_str()
                    .unwrap_or("不明なエラー");
                return Err(format!("OCR 処理が失敗しました: {}", message));
            }
            _ => {
                emit_progress(
                    "polling",
                    &format!("OCR 処理中...（現在の状態: {}）", status),
                    None,
                    Some(page_count),
                );
            }
        }
    }

    // 5. PDF ダウンロード
    emit_progress("downloading", "検索可能 PDF をダウンロード中...", None, None);
    let pdf_url = format!("{}/api/jobs/{}/pdf", settings.backend_url, job_id);
    let pdf_resp = client
        .get(&pdf_url)
        .send()
        .await
        .map_err(|e| format!("PDF ダウンロードに失敗しました: {}", e))?;

    if !pdf_resp.status().is_success() {
        return Err(format!(
            "PDF ダウンロードが失敗しました (HTTP {})",
            pdf_resp.status()
        ));
    }

    let pdf_bytes = pdf_resp
        .bytes()
        .await
        .map_err(|e| format!("PDF データの読み込みに失敗しました: {}", e))?;

    let output = Path::new(&output_path);
    if let Some(parent) = output.parent() {
        fs::create_dir_all(parent).map_err(|e| {
            format!(
                "出力ディレクトリの作成に失敗しました ({}): {}",
                parent.display(),
                e
            )
        })?;
    }

    fs::write(&output_path, pdf_bytes)
        .map_err(|e| format!("PDF の保存に失敗しました ({}): {}", output_path, e))?;

    // 6. クリーンアップ：画像フォルダ入力時に作成した一時 ZIP を削除
    if let Some(temp) = temp_dir {
        let _ = fs::remove_dir_all(temp);
    }

    emit_progress(
        "completed",
        &format!("PDF を保存しました（{} ページ）", page_count),
        Some(page_count),
        Some(page_count),
    );

    Ok(BackendOcrResult {
        job_id,
        output_path,
    })
}

/// 画像フォルダ内の画像ファイルを ZIP 圧縮する。
///
/// 対象拡張子は `.png` / `.jpg` / `.jpeg` で、ファイル名昇順に ZIP エントリを追加する。
/// これにより、連番画像のページ順序が維持される。
fn create_zip_from_folder<F>(
    folder: &Path,
    output_path: &Path,
    emit_progress: &F,
) -> Result<(), String>
where
    F: Fn(&str, &str, Option<u32>, Option<u32>),
{
    let image_extensions = ["png", "jpg", "jpeg"];
    let mut image_files: Vec<PathBuf> = fs::read_dir(folder)
        .map_err(|e| format!("フォルダの読み込みに失敗しました ({}): {}", folder.display(), e))?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.is_file() {
                let ext = path
                    .extension()
                    .and_then(|e| e.to_str())
                    .unwrap_or("")
                    .to_lowercase();
                if image_extensions.contains(&ext.as_str()) {
                    return Some(path);
                }
            }
            None
        })
        .collect();

    image_files.sort();

    if image_files.is_empty() {
        return Err(format!(
            "指定されたフォルダに画像ファイル（.png/.jpg/.jpeg）が見つかりません: {}",
            folder.display()
        ));
    }

    let total = image_files.len() as u32;
    emit_progress(
        "preparing",
        &format!("{} 枚の画像を ZIP 圧縮中...", total),
        Some(0),
        Some(total),
    );

    let zip_file = fs::File::create(output_path).map_err(|e| {
        format!(
            "ZIP ファイルの作成に失敗しました ({}): {}",
            output_path.display(),
            e
        )
    })?;
    let mut zip_writer = zip::ZipWriter::new(zip_file);
    let options = SimpleFileOptions::default().compression_method(zip::CompressionMethod::Deflated);

    for (i, img_path) in image_files.iter().enumerate() {
        let filename = img_path
            .file_name()
            .and_then(|n| n.to_str())
            .ok_or_else(|| format!("不正なファイル名です: {}", img_path.display()))?;

        let bytes = fs::read(img_path).map_err(|e| {
            format!(
                "画像ファイルの読み込みに失敗しました ({}): {}",
                img_path.display(),
                e
            )
        })?;

        zip_writer
            .start_file(filename, options)
            .map_err(|e| format!("ZIP エントリの追加に失敗しました ({}): {}", filename, e))?;
        zip_writer
            .write_all(&bytes)
            .map_err(|e| format!("ZIP への書き込みに失敗しました ({}): {}", filename, e))?;

        emit_progress(
            "preparing",
            &format!("{}/{} ファイルを圧縮中...", i + 1, total),
            Some((i + 1) as u32),
            Some(total),
        );
    }

    zip_writer
        .finish()
        .map_err(|e| format!("ZIP ファイルの finalize に失敗しました: {}", e))?;

    Ok(())
}

