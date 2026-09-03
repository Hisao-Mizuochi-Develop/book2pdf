/// 003006: localapp の実行時設定を管理するモジュール
///
/// `~/.config/book2pdf/settings.json`（macOS では `~/Library/Application Support/book2pdf/settings.json`）
/// に backend API 接続先やタイムアウト値を永続化する。
/// 設定ファイルが存在しない場合はデフォルト値を返し、必要に応じて新規作成する。
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

/// アプリケーション設定を表す構造体。
///
/// フロントエンド・Rust 両方で同一のキー名を使うため、serde の camelCase 変換は行わない。
/// ユーザーが直接編集することを想定し、JSON キーは Rust のフィールド名と同じ snake_case とする。
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    /// backend API のベース URL（例: http://localhost:8000）
    pub backend_url: String,

    /// ocr-worker API のベース URL（例: http://localhost:8001）
    ///
    /// 現時点の localapp → backend 連携では直接使わないが、診断・将来的な用途のため保持する。
    pub ocr_worker_url: String,

    /// Web フロントエンドのベース URL（例: http://localhost:3000）
    ///
    /// 現時点では localapp 内では直接アクセスしないが、設定UIでの表示・今後の拡張用。
    pub frontend_url: String,

    /// OCR 処理の1ページあたりタイムアウト（秒）。
    ///
    /// ndlocr_cli は CPU 実行で1ページあたり数十秒〜数百秒かかることがあるため、
    /// 全体タイムアウトは「ページ数 × page_timeout_sec」で計算する。
    pub page_timeout_sec: u64,

    /// ジョブ状態ポーリング間隔（秒）
    pub polling_interval_sec: u64,

    /// HTTP クライアント全体のタイムアウト（秒）。
    ///
    /// reqwest クライアントのデフォルトタイムアウト。個別の API 呼び出しで
    /// この値を上書きしない限り適用される。
    pub http_client_timeout_sec: u64,

    /// ZIP アップロード時の個別タイムアウト（秒）。
    ///
    /// 大容量 ZIP ファイルのアップロードに時間がかかるため、
    /// 通常の HTTP タイムアウトより長めに設定する。
    pub upload_timeout_sec: u64,

    /// OCR 実行依頼（`POST /ocr`）の個別タイムアウト（秒）。
    ///
    /// backend はリクエスト受付後即座にレスポンスを返すが、
    /// 通信異常時の無限待ち防止のためタイムアウトを設定する。
    pub ocr_request_timeout_sec: u64,

    /// ジョブ状態取得（`GET /api/jobs/{job_id}`）の個別タイムアウト（秒）。
    ///
    /// ポーリング中の 1 リクエストあたりのタイムアウト。接続失敗時は
    /// 指数関数的バックオフでリトライするため、この値は短めでよい。
    pub poll_request_timeout_sec: u64,
}

impl Default for AppSettings {
    /// 初回起動時や設定ファイル欠損時に使用するデフォルト値。
    ///
    /// backend/ocr-worker は Docker Compose で localhost:8000/8001 に公開される前提。
    fn default() -> Self {
        Self {
            backend_url: "http://localhost:8000".to_string(),
            ocr_worker_url: "http://localhost:8001".to_string(),
            frontend_url: "http://localhost:3000".to_string(),
            page_timeout_sec: 600,
            polling_interval_sec: 5,
            http_client_timeout_sec: 60,
            upload_timeout_sec: 600,
            ocr_request_timeout_sec: 60,
            poll_request_timeout_sec: 10,
        }
    }
}

impl AppSettings {
    /// 設定ファイルを保存するディレクトリ（`~/.config/book2pdf` 相当）を返す。
    pub fn config_dir() -> Result<PathBuf, String> {
        dirs::config_dir()
            .ok_or_else(|| "設定ディレクトリが取得できません".to_string())
            .map(|dir| dir.join("book2pdf"))
    }

    /// 設定ファイルのフルパスを返す。
    pub fn settings_path() -> Result<PathBuf, String> {
        Self::config_dir().map(|dir| dir.join("settings.json"))
    }

    /// 設定ファイルを読み込む。存在しない場合はデフォルト値を返す。
    pub fn load() -> Result<Self, String> {
        let path = Self::settings_path()?;

        if !path.exists() {
            // ファイルがなければデフォルト値を返す（保存は呼び出し側が行う）
            return Ok(Self::default());
        }

        let content = fs::read_to_string(&path).map_err(|e| {
            format!(
                "設定ファイルの読み込みに失敗しました ({}): {}",
                path.display(),
                e
            )
        })?;

        let settings: AppSettings = serde_json::from_str(&content).map_err(|e| {
            format!(
                "設定ファイルの JSON 解析に失敗しました ({}): {}",
                path.display(),
                e
            )
        })?;

        Ok(settings)
    }

    /// 設定ファイルに保存する。
    pub fn save(&self) -> Result<(), String> {
        let dir = Self::config_dir()?;
        fs::create_dir_all(&dir).map_err(|e| {
            format!(
                "設定ディレクトリの作成に失敗しました ({}): {}",
                dir.display(),
                e
            )
        })?;

        let path = dir.join("settings.json");
        let content = serde_json::to_string_pretty(self)
            .map_err(|e| format!("設定の JSON シリアライズに失敗しました: {}", e))?;

        fs::write(&path, content).map_err(|e| {
            format!(
                "設定ファイルの書き込みに失敗しました ({}): {}",
                path.display(),
                e
            )
        })?;

        Ok(())
    }
}

/// フロントエンドから呼び出される Tauri コマンド：設定を読み込む。
#[tauri::command]
pub fn load_settings() -> Result<AppSettings, String> {
    AppSettings::load()
}

/// フロントエンドから呼び出される Tauri コマンド：設定を保存する。
#[tauri::command]
pub fn save_settings(settings: AppSettings) -> Result<(), String> {
    settings.save()
}
