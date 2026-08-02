"""共通UIパーツ"""

import customtkinter as ctk


class Tooltip:
    """ホバー時にテキストを表示するモダンツールチップ。

    ダーク/ライト両対応。角丸・シャドウ風ボーダーで洗練された外観。
    """

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self._tipwindow = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def update_text(self, text):
        self.text = text

    def _show(self, event=None):
        if self._tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        # 外観モードに応じた色
        bg = ("#2b2b2b", "#ffffe0")
        fg = ("#e0e0e0", "#1a1a1a")
        border = ("#404040", "#d4d4a8")
        label = ctk.CTkLabel(
            tw,
            text=self.text,
            justify="left",
            font=ctk.CTkFont(size=11),
            fg_color=bg,
            text_color=fg,
            corner_radius=6,
            padx=10,
            pady=6,
        )
        label.pack()
        self._tipwindow = tw

    def _hide(self, event=None):
        if self._tipwindow:
            self._tipwindow.destroy()
            self._tipwindow = None


class LabeledFrame(ctk.CTkFrame):
    """ttk.LabelFrame 互換のグルーピング枠 (CustomTkinter には標準で無いため自作)。

    使い方は ttk.LabelFrame と同じだが、子要素は self ではなく self.body に対して
    pack/grid する点だけ異なる:

        lf = LabeledFrame(parent, text="設定")
        lf.pack(fill="x")
        ctk.CTkLabel(lf.body, text="...").grid(...)

    body は枠内の通常領域で、grid_columnconfigure 等もここで行う。
    """

    def __init__(self, master, text="", **kwargs):
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", 8)
        super().__init__(master, **kwargs)
        self._title = ctk.CTkLabel(
            self, text=text, font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._title.pack(anchor="w", padx=12, pady=(6, 0))
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=8, pady=(2, 8))

    def configure_title(self, text):
        self._title.configure(text=text)
