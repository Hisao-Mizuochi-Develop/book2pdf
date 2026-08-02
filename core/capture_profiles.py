"""キャプチャプロファイル定義

各電子書籍アプリ向けの設定をプロファイルとして管理する。
ビルトインプロファイル（Kindle, Google Play Books, 楽天Kobo,
BOOK☆WALKER, DMMブックス, Kinoppy）に加え、
ユーザーがカスタムプロファイルを作成・保存できる。
"""

from dataclasses import asdict, dataclass


@dataclass
class CaptureProfile:
    """キャプチャ設定のプロファイル"""
    name: str = ""
    window_title_keyword: str = ""
    page_turn_key: str = "right"
    fullscreen_wait: float = 5.0
    page_wait: float = 0.5
    boundary_method: str = "full"  # "full"(全画面・既定) | "manual"(手動クロップ)
    # l_margin/r_margin は旧自動検出方式の名残。現在は未使用 (互換のため残置)。
    l_margin: int = 1
    r_margin: int = 1
    # 手動境界 (boundary_method="manual" のときに使用)。ウィンドウ相対の左右ピクセル座標。
    manual_left: int = 0
    manual_right: int = 0
    click_position: str = "center"  # "center" | "top_left"
    use_bring_to_top: bool = False
    process_name: str = ""  # プロセス名フィルタ (例: "Kindle.exe"、空欄なら無効)
    timeout_seconds: float = 5.0
    max_retries: int = 3

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        # 未知のキーを無視して安全にインスタンス化
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


# ビルトインプロファイル
BUILTIN_PROFILES = {
    "kindle": CaptureProfile(
        name="Kindle for PC",
        window_title_keyword="kindle",
        page_wait=0.15,
        boundary_method="full",
        click_position="top_left",
        process_name="Kindle",
    ),
    "google_play": CaptureProfile(
        name="Google Play ブックス",
        window_title_keyword="Google Play ブックス",
        page_wait=5.0,
        boundary_method="full",
        click_position="center",
        use_bring_to_top=True,
    ),
    "rakuten_kobo": CaptureProfile(
        name="楽天Kobo",
        window_title_keyword="Kobo",
        page_wait=0.5,
        boundary_method="full",
        click_position="center",
        process_name="Kobo",
    ),
    "bookwalker": CaptureProfile(
        name="BOOK☆WALKER",
        window_title_keyword="BOOK☆WALKER",
        page_wait=1.0,
        boundary_method="full",
        click_position="center",
        process_name="BWViewer",
    ),
    "dmm_books": CaptureProfile(
        name="DMMブックス",
        window_title_keyword="DMMブックス",
        page_wait=0.5,
        boundary_method="full",
        click_position="center",
        process_name="DMMBooksViewer",
    ),
    "kinoppy": CaptureProfile(
        name="Kinoppy",
        window_title_keyword="Kinoppy",
        page_wait=0.5,
        boundary_method="full",
        click_position="center",
        process_name="Kinoppy",
    ),
}


def get_profile(profile_key, config=None):
    """プロファイルキーからプロファイルを取得する。

    config が指定されていればカスタムプロファイルも検索する。
    """
    if profile_key in BUILTIN_PROFILES:
        return BUILTIN_PROFILES[profile_key]
    if config and "capture" in config and "profiles" in config["capture"]:
        profile_data = config["capture"]["profiles"].get(profile_key)
        if profile_data:
            return CaptureProfile.from_dict(profile_data)
    return None


def get_all_profile_keys(config=None):
    """利用可能なすべてのプロファイルキーを返す。"""
    keys = list(BUILTIN_PROFILES.keys())
    if config and "capture" in config and "profiles" in config["capture"]:
        for key in config["capture"]["profiles"]:
            if key not in keys:
                keys.append(key)
    return keys
