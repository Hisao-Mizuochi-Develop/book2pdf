"""kindle2pdf — 電子書籍キャプチャツール

電子書籍のスクリーンキャプチャ・トリミング・PDF変換・OCRを
タブベースGUIで操作できる統合ツール。

使い方: python app.py
"""

import customtkinter as ctk
import darkdetect
from PIL import Image

from ui.main_window import KindleShotApp

Image.MAX_IMAGE_PIXELS = 200_000_000


def _resolve_theme(config_theme: str) -> str:
    """設定値と OS 外観を考慮して実際のテーマを決定する。"""
    if config_theme == "dark":
        return "dark"
    if config_theme == "light":
        return "light"
    # auto
    detected = darkdetect.theme()
    return detected.lower() if detected else "light"


def main():
    # テーマ適用（config の general.theme に従う）
    from core.config import load_config
    cfg = load_config()
    theme = _resolve_theme(cfg.get("general", {}).get("theme", "auto"))
    ctk.set_appearance_mode(theme)
    ctk.set_default_color_theme("dark-blue")

    app = KindleShotApp()
    app.mainloop()


def run():
    main()


if __name__ == "__main__":
    run()
