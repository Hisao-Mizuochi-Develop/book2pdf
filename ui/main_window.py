"""メインウィンドウ

4タブ構成（キャプチャ / PDF読込 / トリミング / 変換）のメインウィンドウ。
キャプチャ・PDF読込はどちらも「画像フォルダの入力源」として機能する。
"""

import customtkinter as ctk

from core.config import load_config, save_config
from ui.capture_tab import CaptureTab
from ui.convert_tab import ConvertTab
from ui.pdf_load_tab import PdfLoadTab
from ui.state import AppState
from ui.trim_tab import TrimTab


class BookCaptureApp(ctk.CTk):
    """メインアプリケーションウィンドウ"""

    def __init__(self):
        super().__init__()
        self.title("book2pdf — 電子書籍キャプチャ・OCRツール")
        self.geometry("1024x920")

        self.config_data = load_config()
        # NOTE: tk.Tk / ctk.CTk は state() メソッドを持つので self.state を上書きすると壊れる
        self.app_state = AppState()

        # --- ヘッダー: テーマ切り替え ---
        self._build_header()

        # 4タブ構成
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=8, pady=8)

        capture_frame = self.tabview.add(" キャプチャ ")
        pdf_frame = self.tabview.add(" PDF読込 ")
        trim_frame = self.tabview.add(" トリミング ")
        convert_frame = self.tabview.add(" 変換 ")

        self.capture_tab = CaptureTab(capture_frame, self.app_state, self.config_data)
        self.capture_tab.pack(fill="both", expand=True)

        self.pdf_load_tab = PdfLoadTab(pdf_frame, self.app_state, self.config_data)
        self.pdf_load_tab.pack(fill="both", expand=True)

        self.trim_tab = TrimTab(trim_frame, self.app_state, self.config_data)
        self.trim_tab.pack(fill="both", expand=True)

        self.convert_tab = ConvertTab(convert_frame, self.app_state, self.config_data)
        self.convert_tab.pack(fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_header(self):
        """タイトルバー下のヘッダー領域（テーマ切り替えボタン）。"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 0))

        # 右寄せのテーマ切り替え
        self._theme_var = ctk.StringVar(
            value=self.config_data.get("general", {}).get("theme", "auto")
        )
        self._theme_btn = ctk.CTkSegmentedButton(
            header,
            values=["auto", "light", "dark"],
            variable=self._theme_var,
            command=self._on_theme_changed,
            width=200,
        )
        self._theme_btn.pack(side="right")

        # ラベル
        ctk.CTkLabel(header, text="テーマ:").pack(side="right", padx=(16, 6))

    def _on_theme_changed(self, value):
        """テーマ切り替え。選択値を ctk に反映し config に保存する。"""
        ctk.set_appearance_mode(value)
        self.config_data.setdefault("general", {})["theme"] = value
        save_config(self.config_data)

    def _on_close(self):
        self.destroy()
