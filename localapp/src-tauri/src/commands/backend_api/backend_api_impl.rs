/// `run_backend_ocr` の backend 通信コアを切り出した実装モジュール。
///
/// Tauri の `AppHandle` や設定読み込みに依存しないため、
/// モック backend を使った結合テストから直接呼び出すことができる。
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::time::Duration;

use tauri_plugin_http::reqwest;
use zip::write::SimpleFileOptions;

use super::BackendOcrResult;

/// backend API を使って OCR 済み PDF を生成するコア処理。
///
/// # Args
/// - `source_path`: 入力画像フォルダまたは ZIP ファイルのパス
/// - `source_type`: `"folder"` または `"zip"`
/// - `output_path`: 出力 PDF の保存先パス
/// - `backend_url`: backend API のベース URL（末尾スラッシュなし）
/// - `page_timeout_sec`: 1 ページあたりのタイムアウト（ポーリング全体の deadline 計算用）
/// - `polling_interval_sec`: ジョブ状態ポーリング間隔（秒）
/// - `client`: 既に構築済みの reqwest クライアント
/// - `emit_progress`: 進捗通知用コールバック
pub async fn run_backend_ocr_inner<F>(
    source_path: String,
    source_type: String,
    output_path: String,
    backend_url: String,
    page_timeout_sec: u64,
    polling_interval_sec: u64,
    client: &reqwest::Client,
    mut emit_progress: F,
) -> Result<BackendOcrResult, String>
where
    F: FnMut(&str, &str, Option<u32>, Option<u32>),
{
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
            return Err(format!(
                "指定されたフォルダが存在しません: {}",
                source_path
            ));
        }

        let temp = std::env::temp_dir().join(format!(
            "book2pdf_backend_ocr_{}",
            uuid::Uuid::new_v4()
        ));
        fs::create_dir_all(&temp).map_err(|e| {
            format!(
                "一時ディレクトリの作成に失敗しました ({}): {}",
                temp.display(),
                e
            )
        })?;

        let zip_file = temp.join("input.zip");
        create_zip_from_folder(&folder, &zip_file, &mut emit_progress)?;
        (zip_file, Some(temp))
    };

    // 1. ジョブ作成
    emit_progress("creating", "backend にジョブを作成中...", None, None);
    let create_url = format!("{}/api/jobs/", backend_url);
    let create_resp = client
        .post(&create_url)
        .send()
        .await
        .map_err(|e| format!("ジョブ作成リクエストに失敗しました: {}", e))?;
    if !create_resp.status().is_success() {
        return Err(format!(
            "ジョブ作成に失敗しました (HTTP {}): {}",
            create_resp.status(),
            create_resp.text().await.unwrap_or_default()
        ));
    }
    let create_body: serde_json::Value = create_resp
        .json()
        .await
        .map_err(|e| format!("ジョブ作成レスポンスの解析に失敗しました: {}", e))?;
    let job_id = create_body["job_id"]
        .as_str()
        .ok_or_else(|| "ジョブ ID が見つかりません".to_string())?
        .to_string();

    // 2. ZIP アップロード
    emit_progress(
        "uploading",
        &format!("ZIP をアップロード中（job_id: {}）...", job_id),
        None,
        None,
    );
    let upload_url = format!("{}/api/jobs/{}/upload", backend_url, job_id);
    let zip_bytes = fs::read(&zip_path).map_err(|e| {
        format!(
            "ZIP ファイルの読み込みに失敗しました ({}): {}",
            zip_path.display(),
            e
        )
    })?;
    let part = reqwest::multipart::Part::bytes(zip_bytes)
        .file_name("input.zip")
        .mime_str("application/zip")
        .map_err(|e| format!("multipart の構築に失敗しました: {}", e))?;
    let form = reqwest::multipart::Form::new().part("file", part);
    let upload_resp = client
        .post(&upload_url)
        .multipart(form)
        .timeout(Duration::from_secs(600))
        .send()
        .await
        .map_err(|e| format!("ZIP アップロードに失敗しました: {}", e))?;
    if !upload_resp.status().is_success() {
        return Err(format!(
            "ZIP アップロードに失敗しました (HTTP {}): {}",
            upload_resp.status(),
            upload_resp.text().await.unwrap_or_default()
        ));
    }
    let upload_body: serde_json::Value = upload_resp
        .json()
        .await
        .map_err(|e| format!("アップロードレスポンスの解析に失敗しました: {}", e))?;
    let files = upload_body["files"]
        .as_array()
        .ok_or_else(|| "アップロードされたファイル一覧が見つかりません".to_string())?;
    let page_count = files.len() as u32;
    emit_progress(
        "uploading",
        &format!("{} ページのアップロードが完了しました", page_count),
        Some(page_count),
        Some(page_count),
    );

    // 3. OCR 実行リクエスト（非同期受付）
    emit_progress("ocr", "OCR 処理を開始中...", Some(0), Some(page_count));
    let ocr_url = format!("{}/api/jobs/{}/ocr", backend_url, job_id);
    let ocr_resp = client
        .post(&ocr_url)
        .timeout(Duration::from_secs(60))
        .send()
        .await
        .map_err(|e| format!("OCR 開始リクエストに失敗しました: {}", e))?;
    if !ocr_resp.status().is_success() {
        return Err(format!(
            "OCR 開始に失敗しました (HTTP {}): {}",
            ocr_resp.status(),
            ocr_resp.text().await.unwrap_or_default()
        ));
    }
    let ocr_body: serde_json::Value = ocr_resp
        .json()
        .await
        .map_err(|e| format!("OCR 開始レスポンスの解析に失敗しました: {}", e))?;
    let initial_status = ocr_body["status"].as_str().unwrap_or("unknown");
    if initial_status != "processing" && initial_status != "completed" {
        return Err(format!(
            "OCR 開始後の予期しない状態です: {}",
            initial_status
        ));
    }

    // 4. ポーリング
    emit_progress("polling", "OCR 完了を待機中...", Some(0), Some(page_count));
    let job_url = format!("{}/api/jobs/{}", backend_url, job_id);
    let total_timeout =
        Duration::from_secs(page_timeout_sec.max(1) as u64 * page_count.max(1) as u64);
    let deadline = std::time::Instant::now() + total_timeout;
    let poll_interval = Duration::from_secs(polling_interval_sec.max(1) as u64);

    loop {
        if std::time::Instant::now() > deadline {
            return Err(
                "OCR 処理がタイムアウトしました。page_timeout_sec を長くするか、backend/ocr-worker の状態を確認してください。"
                    .to_string(),
            );
        }

        let job_resp = client
            .get(&job_url)
            .send()
            .await
            .map_err(|e| format!("ジョブ状態の取得に失敗しました: {}", e))?;
        if !job_resp.status().is_success() {
            return Err(format!(
                "ジョブ状態の取得に失敗しました (HTTP {}): {}",
                job_resp.status(),
                job_resp.text().await.unwrap_or_default()
            ));
        }
        let job_body: serde_json::Value = job_resp
            .json()
            .await
            .map_err(|e| format!("ジョブ状態レスポンスの解析に失敗しました: {}", e))?;
        let status = job_body["status"].as_str().unwrap_or("unknown");

        match status {
            "completed" => {
                emit_progress(
                    "polling",
                    "OCR が完了しました。PDF をダウンロードします...",
                    Some(page_count),
                    Some(page_count),
                );
                break;
            }
            "failed" => {
                let msg = job_body["message"].as_str().unwrap_or("不明なエラー");
                return Err(format!("OCR 処理が失敗しました: {}", msg));
            }
            "processing" => {
                emit_progress(
                    "polling",
                    &format!("OCR 処理中...（status: {}）", status),
                    Some(0),
                    Some(page_count),
                );
            }
            other => {
                emit_progress(
                    "polling",
                    &format!("待機中...（status: {}）", other),
                    Some(0),
                    Some(page_count),
                );
            }
        }

        tokio::time::sleep(poll_interval).await;
    }

    // 5. PDF ダウンロード
    emit_progress(
        "downloading",
        "生成された PDF をダウンロード中...",
        Some(page_count),
        Some(page_count),
    );
    let pdf_url = format!("{}/api/jobs/{}/pdf", backend_url, job_id);
    let pdf_resp = client
        .get(&pdf_url)
        .send()
        .await
        .map_err(|e| format!("PDF ダウンロードに失敗しました: {}", e))?;
    if !pdf_resp.status().is_success() {
        return Err(format!(
            "PDF ダウンロードに失敗しました (HTTP {}): {}",
            pdf_resp.status(),
            pdf_resp.text().await.unwrap_or_default()
        ));
    }
    let pdf_bytes = pdf_resp
        .bytes()
        .await
        .map_err(|e| format!("PDF レスポンスボディの読み込みに失敗しました: {}", e))?;
    if pdf_bytes.is_empty() {
        return Err("ダウンロードされた PDF が空です".to_string());
    }

    let output_path_buf = PathBuf::from(&output_path);
    let parent = output_path_buf
        .parent()
        .ok_or_else(|| format!("出力パスに親ディレクトリがありません: {}", output_path))?;
    fs::create_dir_all(parent).map_err(|e| {
        format!(
            "出力ディレクトリの作成に失敗しました ({}): {}",
            parent.display(),
            e
        )
    })?;

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
    emit_progress: &mut F,
) -> Result<(), String>
where
    F: FnMut(&str, &str, Option<u32>, Option<u32>),
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
    let options =
        SimpleFileOptions::default().compression_method(zip::CompressionMethod::Deflated);

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



#[cfg(test)]
mod tests {
    use super::run_backend_ocr_inner;
    use std::fs;
    use std::path::PathBuf;
    use std::process::{Child, Command};
    use std::time::Duration;
    use std::net::{SocketAddr, TcpStream};
    use tauri_plugin_http::reqwest;

    const MOCK_PORT: u16 = 18001;
    const MOCK_SERVER_SCRIPT: &str = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../testdata/mock_backend_server.py"
    );

    /// 結合テスト用のモック backend サーバーを起動する。
    ///
    /// # Panics
    /// サーバーが 10 秒以内に応答しない場合は panic する。
    fn start_mock_server() -> Child {
        let child = Command::new("python3")
            .arg(MOCK_SERVER_SCRIPT)
            .arg("--port")
            .arg(MOCK_PORT.to_string())
            .spawn()
            .expect("モック backend サーバーの起動に失敗しました");

        // サーバーが TCP ポートを開くまで短時間ポーリングする
        let addr: SocketAddr = format!("127.0.0.1:{}", MOCK_PORT)
            .parse()
            .expect("無効なソケットアドレスです");
        for _ in 0..100 {
            if TcpStream::connect_timeout(&addr, Duration::from_millis(100)).is_ok() {
                return child;
            }
            std::thread::sleep(Duration::from_millis(100));
        }
        panic!("モック backend サーバーが 10 秒以内に起動しませんでした");
    }

    /// 1 枚のダミー画像を含む一時フォルダを作成する。
    fn create_dummy_image_folder() -> PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "book2pdf_backend_ocr_test_{}",
            uuid::Uuid::new_v4()
        ));
        fs::create_dir_all(&dir).expect("テスト用フォルダの作成に失敗しました");
        // ZIP 圧縮対象は拡張子のみチェックするため、PNG として有効でなくてもよい
        fs::write(dir.join("001.png"), b"dummy image bytes")
            .expect("ダミー画像の書き込みに失敗しました");
        dir
    }

    #[tokio::test]
    async fn test_backend_ocr_inner_with_mock_server() {
        let mut child = start_mock_server();

        let input_dir = create_dummy_image_folder();
        let output_path = std::env::temp_dir()
            .join(format!("book2pdf_output_{}.pdf", uuid::Uuid::new_v4()));
        let mut events: Vec<(String, String, Option<u32>, Option<u32>)> = Vec::new();

        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(10))
            .build()
            .unwrap();

        let result = run_backend_ocr_inner(
            input_dir.to_string_lossy().to_string(),
            "folder".to_string(),
            output_path.to_string_lossy().to_string(),
            format!("http://127.0.0.1:{}", MOCK_PORT),
            60,
            1,
            &client,
            |stage, message, current, total| {
                events.push((stage.to_string(), message.to_string(), current, total));
            },
        )
        .await;

        let _ = child.kill();

        assert!(
            result.is_ok(),
            "run_backend_ocr_inner が失敗しました: {:?}",
            result.err()
        );
        let result = result.unwrap();
        assert!(
            !result.job_id.is_empty(),
            "job_id が空です"
        );
        assert_eq!(result.output_path, output_path.to_string_lossy());
        assert!(
            output_path.exists(),
            "出力 PDF が作成されていません: {}",
            output_path.display()
        );
        let meta = fs::metadata(&output_path).expect("PDF メタデータの取得に失敗しました");
        assert!(meta.len() > 0, "出力 PDF が空です");

        // completed イベントが発行されていることを確認
        assert!(
            events.iter().any(|(stage, _, _, _)| stage == "completed"),
            "completed イベントが発行されていません: {:?}",
            events
        );

        // クリーンアップ
        let _ = fs::remove_dir_all(&input_dir);
        let _ = fs::remove_file(&output_path);
    }
}
