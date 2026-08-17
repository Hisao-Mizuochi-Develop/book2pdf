/// 電子書籍アプリのキャプチャプロファイル定義
///
/// 各電子書籍リーダーアプリに最適化された設定を管理する。
/// ビルトインプロファイル（Kindle, Google Play Books, 楽天Kobo,
/// BOOK☆WALKER, DMMブックス, Kinoppy）に加え、
/// ユーザーがカスタマイズした値も保持できる。
///
/// 参考: reference/localapp/core/capture_profiles.py の CaptureProfile dataclass
use serde::{Deserialize, Serialize};

/// コンテンツ領域トリミング設定（ピクセル単位）
///
/// ウィンドウ全体のキャプチャから、書籍コンテンツ部分のみを切り出すための
/// 上下左右の余白（インセット）を定義する。
/// 例: Kindle for PC の場合、タイトルバー高さ分の `top` を設定することで
/// 外枠を除いたコンテンツ領域だけを抽出できる。
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct CropInsets {
    /// 上端からのトリミング量（ピクセル）
    pub top: u32,
    /// 右端からのトリミング量（ピクセル）
    pub right: u32,
    /// 下端からのトリミング量（ピクセル）
    pub bottom: u32,
    /// 左端からのトリミング量（ピクセル）
    pub left: u32,
}

/// キャプチャ設定を保持するプロファイル構造体
///
/// すべてのフィールドは既定値を持ち、部分的な上書きが可能。
/// serde の Default 特性により、未指定フィールドは自動的に既定値で埋められる。
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct CaptureProfile {
    /// プロファイルの表示名（UI で選択肢として表示される）
    pub name: String,
    /// ウィンドウタイトルに含まれるキーワード（大文字小文字区別なしで検索）
    pub window_title_keyword: String,
    /// ページ送りに使うキー文字列（"right" / "left" / "space" / "arrow" など）
    pub page_turn_key: String,
    /// ページ送り後の待ち時間（秒）。アプリごとに遷移速度が異なるため調整が必要
    pub page_wait: f64,
    /// 境界検出方式。"full"=全画面（既定） / "manual"=手動クロップ
    pub boundary_method: String,
    /// プロセス名フィルタ（例: "Kindle"）。空欄ならフィルタ無効
    pub process_name: String,
    /// ウィンドウ検索などのタイムアウト時間（秒）
    pub timeout_seconds: f64,
    /// 失敗時の最大再試行回数
    pub max_retries: u32,
    /// コンテンツ領域トリミング設定（外枠除去用）
    pub crop_insets: CropInsets,
}

impl CaptureProfile {
    /// プロファイルキーと struct のマッピングから JSON 用のリストを構築する
    ///
    /// フロントエンドでは `get_builtin_profiles` コマンドでこのリストを受け取り、
    /// セレクタ UI の選択肢として利用する。
    ///
    /// # 戻り値
    /// (キー, CaptureProfile) のタプルベクタ。順序は定義順に保持される。
    pub fn builtin_profiles() -> Vec<(String, CaptureProfile)> {
        [
            (
                "kindle".to_string(),
                CaptureProfile {
                    name: "Kindle for PC".to_string(),
                    window_title_keyword: "kindle".to_string(),
                    page_turn_key: "right".to_string(),
                    page_wait: 0.15,
                    boundary_method: "full".to_string(),
                    process_name: "Kindle".to_string(),
                    timeout_seconds: 5.0,
                    max_retries: 3,
                    crop_insets: CropInsets {
                        // Kindle for PC のタイトルバー高さ（実測値に基づく）
                        // 外枠・メニューバーを除外し書籍コンテンツ部分だけを抽出する
                        top: 82,
                        right: 0,
                        bottom: 0,
                        left: 0,
                    },
                },
            ),
            (
                "google_play".to_string(),
                CaptureProfile {
                    name: "Google Play ブックス".to_string(),
                    window_title_keyword: "Google Play ブックス".to_string(),
                    page_turn_key: "right".to_string(),
                    page_wait: 5.0,
                    boundary_method: "full".to_string(),
                    process_name: "".to_string(),
                    timeout_seconds: 5.0,
                    max_retries: 3,
                    crop_insets: CropInsets::default(),
                },
            ),
            (
                "rakuten_kobo".to_string(),
                CaptureProfile {
                    name: "楽天Kobo".to_string(),
                    window_title_keyword: "Kobo".to_string(),
                    page_turn_key: "right".to_string(),
                    page_wait: 0.5,
                    boundary_method: "full".to_string(),
                    process_name: "Kobo".to_string(),
                    timeout_seconds: 5.0,
                    max_retries: 3,
                    crop_insets: CropInsets::default(),
                },
            ),
            (
                "bookwalker".to_string(),
                CaptureProfile {
                    name: "BOOK☆WALKER".to_string(),
                    window_title_keyword: "BOOK☆WALKER".to_string(),
                    page_turn_key: "right".to_string(),
                    page_wait: 1.0,
                    boundary_method: "full".to_string(),
                    process_name: "BWViewer".to_string(),
                    timeout_seconds: 5.0,
                    max_retries: 3,
                    crop_insets: CropInsets::default(),
                },
            ),
            (
                "dmm_books".to_string(),
                CaptureProfile {
                    name: "DMMブックス".to_string(),
                    window_title_keyword: "DMMブックス".to_string(),
                    page_turn_key: "right".to_string(),
                    page_wait: 0.5,
                    boundary_method: "full".to_string(),
                    process_name: "DMMBooksViewer".to_string(),
                    timeout_seconds: 5.0,
                    max_retries: 3,
                    crop_insets: CropInsets::default(),
                },
            ),
            (
                "kinoppy".to_string(),
                CaptureProfile {
                    name: "Kinoppy".to_string(),
                    window_title_keyword: "Kinoppy".to_string(),
                    page_turn_key: "right".to_string(),
                    page_wait: 0.5,
                    boundary_method: "full".to_string(),
                    process_name: "Kinoppy".to_string(),
                    timeout_seconds: 5.0,
                    max_retries: 3,
                    crop_insets: CropInsets::default(),
                },
            ),
        ]
        .into()
    }
}

/// ビルトインプロファイルの JSON 表現
///
/// `get_builtin_profiles` コマンドでフロントエンドに送信される形式。
/// フロントエンド側で型安全に扱えるよう、各フィールドを明確に定義する。
#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ProfileEntry {
    /// プロファイルの一意キー（例: "kindle"）
    pub key: String,
    /// プロファイルの表示名（例: "Kindle for PC"）
    pub name: String,
    /// ウィンドウタイトルに含まれるキーワード
    pub window_title_keyword: String,
    /// ページ送りキー
    pub page_turn_key: String,
    /// ページ送り後の待ち時間（秒）
    pub page_wait: f64,
    /// 境界検出方式
    pub boundary_method: String,
    /// プロセス名フィルタ
    pub process_name: String,
    /// タイムアウト時間（秒）
    pub timeout_seconds: f64,
    /// 最大再試行回数
    pub max_retries: u32,
    /// コンテンツ領域トリミング設定（外枠除去用）
    pub crop_insets: CropInsets,
}

impl From<(String, CaptureProfile)> for ProfileEntry {
    fn from((key, profile): (String, CaptureProfile)) -> Self {
        Self {
            key,
            name: profile.name,
            window_title_keyword: profile.window_title_keyword,
            page_turn_key: profile.page_turn_key,
            page_wait: profile.page_wait,
            boundary_method: profile.boundary_method,
            process_name: profile.process_name,
            timeout_seconds: profile.timeout_seconds,
            max_retries: profile.max_retries,
            crop_insets: profile.crop_insets,
        }
    }
}
