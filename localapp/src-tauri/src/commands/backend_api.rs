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
///
/// タイムアウトや待機時間を指定するための標準ライブラリ読み込み
/// HTTP リクエストタイムアウトやポーリング間隔に使用する
use std::time::Duration;

/// Tauri のアプリケーションハンドル・イベント発射・ランタイム抽象化を読み込み
/// AppHandle: アプリ全体の操作（リソースパス解決等）
/// Emitter: フロントエンドへのイベント送信
/// Runtime: Tauri ランタイムの抽象（テスト時にモック可能にするため）
use tauri::{AppHandle, Emitter, Runtime};
/// Tauri の HTTP プラグインが提供する reqwest クライアントを読み込み
/// backend API への HTTP リクエスト（POST/GET）を送信するために使用する
use tauri_plugin_http::reqwest;
/// アプリケーション設定（backend URL・タイムアウト値等）のデータモデルを読み込み
/// `~/.config/book2pdf/settings.json` の読み書きに使用する
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

mod backend_api_impl;

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
        .timeout(Duration::from_secs(settings.http_client_timeout_sec))
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

    backend_api_impl::run_backend_ocr_inner(
        source_path,
        source_type,
        output_path,
        settings.backend_url,
        settings.page_timeout_sec,
        settings.polling_interval_sec,
        settings.upload_timeout_sec,
        settings.ocr_request_timeout_sec,
        settings.poll_request_timeout_sec,
        &client,
        emit_progress,
    )
    .await
}

