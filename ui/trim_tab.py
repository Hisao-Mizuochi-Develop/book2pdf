"""トリミングタブ

フォルダ選択 → プレビュー（before/after）→ 余白調整 → 実行
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

from core.boundary_detector import detect_margins
from core.config import save_config
from core.trimmer import process_images, trim_margins
from ui.widgets import LabeledFrame


class TrimTab(ctk.CTkFrame):
    """トリミングタブ: フォルダ選択 → プレビュー → 余白調整 → 実行"""

    def __init__(self, parent, state, config):
        super().__init__(parent, fg_color="transparent")
        self.state = state
        self.config = config
        state.add_listener(self._on_state_change)
        self._build_ui()

    def _on_state_change(self, event, data):
        if event == "capture_complete" and data:
            self.input_var.set(data)
            # 出力フォルダを自動設定
            self.output_var.set(data + "_trimmed")

    def _build_ui(self):
        # --- フォルダ選択 ---
        folder_frame = LabeledFrame(self, text="フォルダ設定")
        folder_frame.pack(fill="x", padx=10, pady=5)
        folder_frame.body.grid_columnconfigure(1, weight=1)

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()

        ctk.CTkLabel(folder_frame.body, text="入力:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ctk.CTkEntry(folder_frame.body, textvariable=self.input_var).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ctk.CTkButton(folder_frame.body, text="参照", width=80, command=lambda: self._browse("input")).grid(row=0, column=2, padx=5, pady=2)

        ctk.CTkLabel(folder_frame.body, text="出力:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ctk.CTkEntry(folder_frame.body, textvariable=self.output_var).grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ctk.CTkButton(folder_frame.body, text="参照", width=80, command=lambda: self._browse("output")).grid(row=1, column=2, padx=5, pady=2)

        # --- 余白設定 ---
        margin_frame = LabeledFrame(self, text="余白（ピクセル）")
        margin_frame.pack(fill="x", padx=10, pady=5)

        margin_inner = ctk.CTkFrame(margin_frame.body, fg_color="transparent")
        margin_inner.pack(padx=5, pady=5)

        trim_config = self.config.get("trim", {})
        self.left_var = tk.StringVar(value=str(trim_config.get("left_margin", 0)))
        self.right_var = tk.StringVar(value=str(trim_config.get("right_margin", 0)))
        self.top_var = tk.StringVar(value=str(trim_config.get("top_margin", 0)))
        self.bottom_var = tk.StringVar(value=str(trim_config.get("bottom_margin", 0)))

        for col, (label, var) in enumerate([
            ("左:", self.left_var), ("右:", self.right_var),
            ("上:", self.top_var), ("下:", self.bottom_var),
        ]):
            ctk.CTkLabel(margin_inner, text=label).grid(row=0, column=col * 2, padx=5)
            ctk.CTkEntry(margin_inner, textvariable=var, width=80).grid(row=0, column=col * 2 + 1)

        ctk.CTkButton(margin_inner, text="自動検出", command=self._auto_detect_margins).grid(
            row=0, column=8, padx=10,
        )
        ctk.CTkButton(margin_inner, text="デフォルトとして保存", command=self._save_default_margins).grid(
            row=0, column=9, padx=10,
        )

        # 自動検出の使い方の説明 (ギリギリを攻めないようにする方針を明示)
        ctk.CTkLabel(
            margin_frame.body,
            text=(
                "※「自動検出」はやや余裕を持たせた値を入力します。"
                "プレビューで確認しながら、各辺の値を増やしてコンテンツへ寄せてください。"
            ),
            text_color=("gray35", "gray70"),
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 4))

        # --- アクションボタン ---
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=5)

        self.preview_btn = ctk.CTkButton(action_frame, text="プレビュー", command=self._show_preview)
        self.preview_btn.pack(side="left", padx=5)

        self.trim_btn = ctk.CTkButton(action_frame, text="トリミング実行", command=self._run_trim)
        self.trim_btn.pack(side="left", padx=5)

        # --- 進捗 ---
        progress_frame = LabeledFrame(self, text="進捗")
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.status_var = tk.StringVar(value="待機中")

        self.progress_bar = ctk.CTkProgressBar(progress_frame.body)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(progress_frame.body, textvariable=self.status_var).pack(padx=10, pady=2)

        # --- プレビューエリア ---
        preview_lf = LabeledFrame(self, text="プレビュー")
        preview_lf.pack(fill="both", expand=True, padx=10, pady=5)

        preview_grid = ctk.CTkFrame(preview_lf.body, fg_color="transparent")
        preview_grid.pack(fill="both", expand=True)
        preview_grid.grid_rowconfigure(0, weight=1)
        preview_grid.grid_columnconfigure(0, weight=1)
        preview_grid.grid_columnconfigure(1, weight=1)

        # 画像表示は tk.Label のまま (ImageTk.PhotoImage との相性が良い)
        self.original_label = tk.Label(preview_grid, text="オリジナル")
        self.original_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.trimmed_label = tk.Label(preview_grid, text="トリミング後")
        self.trimmed_label.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # ナビゲーション
        nav_frame = ctk.CTkFrame(preview_lf.body, fg_color="transparent")
        nav_frame.pack(fill="x", padx=5, pady=2)
        nav_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(nav_frame, text="◀ 前へ", width=80, command=lambda: self._change_preview(-1)).grid(row=0, column=0, padx=5)
        self.filename_label = ctk.CTkLabel(nav_frame, text="")
        self.filename_label.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(nav_frame, text="次へ ▶", width=80, command=lambda: self._change_preview(1)).grid(row=0, column=2, padx=5)

        self._preview_index = 0
        self._preview_files = []
        self._original_pil = None
        self._trimmed_pil = None

        preview_grid.bind("<Configure>", self._redraw_preview)

    def _browse(self, target):
        folder = filedialog.askdirectory()
        if folder:
            if target == "input":
                self.input_var.set(folder)
            else:
                self.output_var.set(folder)

    def _get_margins(self):
        try:
            return (int(self.left_var.get()), int(self.right_var.get()),
                    int(self.top_var.get()), int(self.bottom_var.get()))
        except ValueError:
            messagebox.showerror("エラー", "余白の値は整数で入力してください。")
            return None

    # 自動検出時に元の検出値から残す割合 (1.0 未満で外側に余白を残す)。
    # 章タイトルや図版で攻めすぎるのを防ぐため、ユーザが微調整しやすい
    # 「ゆるめのクロップ」を初期値として入れる。
    _AUTO_DETECT_SAFETY_RATIO = 0.8
    # さらに最低でもこの分は引いて、確実に外側に余白を残す。
    _AUTO_DETECT_SAFETY_PIXELS = 8

    def _auto_detect_margins(self):
        """入力フォルダの先頭数枚をサンプリングして 4 辺の余白を自動推定する。

        単一ページだけ見ると章タイトル行や図版で過剰に内側を切ってしまうので、
        複数枚の検出結果のうち**最小マージン (= 最も保守的なクロップ)** を採用する。
        さらに、ギリギリを攻めすぎないよう各辺に安全マージン (係数 + 固定px) を適用し、
        ユーザが手動で値を増やして寄せていくフローに合わせる。
        """
        input_folder = self.input_var.get()
        if not input_folder:
            messagebox.showerror("エラー", "入力フォルダを選択してください。")
            return
        try:
            files = sorted([
                f for f in os.listdir(input_folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))
            ])
        except FileNotFoundError:
            messagebox.showerror("エラー", f"フォルダが見つかりません:\n{input_folder}")
            return
        if not files:
            messagebox.showerror("エラー", "画像ファイルが見つかりません。")
            return

        # サンプル枚数: 先頭・中央・末尾から最大 5 枚
        n = len(files)
        idxs = sorted({0, n // 4, n // 2, 3 * n // 4, n - 1})[:5]
        results = []
        for i in idxs:
            try:
                with Image.open(os.path.join(input_folder, files[i])) as img:
                    m = detect_margins(img)
            except Exception:
                continue
            if m is not None:
                results.append(m)

        if not results:
            messagebox.showerror("エラー", "余白を検出できませんでした。")
            return

        # 各辺ごとに最小値を採用 (=コンテンツを切り落とさない方向に倒す)
        raw_left = min(r[0] for r in results)
        raw_right = min(r[1] for r in results)
        raw_top = min(r[2] for r in results)
        raw_bottom = min(r[3] for r in results)

        # ユーザの「ギリギリを攻めず、そこから狭めていく」運用に合わせ、
        # 検出値より小さい値を入れて外側に余白を残す。
        def _relax(v: int) -> int:
            return max(0, min(int(v * self._AUTO_DETECT_SAFETY_RATIO),
                              v - self._AUTO_DETECT_SAFETY_PIXELS))

        left = _relax(raw_left)
        right = _relax(raw_right)
        top = _relax(raw_top)
        bottom = _relax(raw_bottom)

        self.left_var.set(str(left))
        self.right_var.set(str(right))
        self.top_var.set(str(top))
        self.bottom_var.set(str(bottom))

        # プレビュー読み込み済みなら再描画
        if self._preview_files:
            self._load_preview_image()
        else:
            messagebox.showinfo(
                "自動検出",
                f"余白を検出しました（やや余裕を持たせた値）。\n"
                f"左={left}, 右={right}, 上={top}, 下={bottom}\n"
                f"（{len(results)}/{len(idxs)} ページの最小値から安全マージンを差し引き）\n\n"
                f"プレビューを確認しながら、必要に応じて値を増やして寄せてください。",
            )

    def _save_default_margins(self):
        margins = self._get_margins()
        if margins is None:
            return
        left, right, top, bottom = margins
        self.config["trim"]["left_margin"] = left
        self.config["trim"]["right_margin"] = right
        self.config["trim"]["top_margin"] = top
        self.config["trim"]["bottom_margin"] = bottom
        save_config(self.config)
        messagebox.showinfo("保存", "デフォルトトリミング余白を保存しました。")

    # --- プレビュー ---

    def _show_preview(self):
        input_folder = self.input_var.get()
        if not input_folder:
            messagebox.showerror("エラー", "入力フォルダを選択してください。")
            return

        margins = self._get_margins()
        if margins is None:
            return

        try:
            self._preview_files = sorted([
                f for f in os.listdir(input_folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))
            ])
        except FileNotFoundError:
            messagebox.showerror("エラー", f"フォルダが見つかりません:\n{input_folder}")
            return

        if not self._preview_files:
            messagebox.showerror("エラー", "画像ファイルが見つかりません。")
            return

        self._preview_index = 0
        self._load_preview_image()

    def _load_preview_image(self):
        input_folder = self.input_var.get()
        if not self._preview_files:
            return

        margins = self._get_margins()
        if margins is None:
            return

        left, right, top, bottom = margins
        filename = self._preview_files[self._preview_index]
        filepath = os.path.join(input_folder, filename)

        with Image.open(filepath) as img:
            self._original_pil = img.copy()
            self._trimmed_pil = trim_margins(img, left, right, top, bottom)

        self.filename_label.configure(
            text=f"{filename} ({self._preview_index + 1}/{len(self._preview_files)})"
        )
        self._redraw_preview()

    def _redraw_preview(self, event=None):
        if not self._original_pil or not self._trimmed_pil:
            return
        max_w = max(10, self.original_label.winfo_width() - 10)
        max_h = max(10, self.original_label.winfo_height() - 10)

        for pil_img, label in [
            (self._original_pil, self.original_label),
            (self._trimmed_pil, self.trimmed_label),
        ]:
            img = pil_img.copy()
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label.configure(image=photo)
            label.image = photo

    def _change_preview(self, delta):
        if not self._preview_files:
            return
        new_idx = self._preview_index + delta
        if 0 <= new_idx < len(self._preview_files):
            self._preview_index = new_idx
            self._load_preview_image()

    # --- トリミング実行 ---

    def _run_trim(self):
        input_folder = self.input_var.get()
        output_folder = self.output_var.get()
        margins = self._get_margins()

        if not input_folder or not output_folder:
            messagebox.showerror("エラー", "入力フォルダと出力フォルダを指定してください。")
            return
        if margins is None:
            return

        left, right, top, bottom = margins
        self.progress_bar.set(0)
        self.status_var.set("開始中...")
        self.trim_btn.configure(state="disabled")
        self.preview_btn.configure(state="disabled")

        root = self.winfo_toplevel()

        def on_progress(current, total, filename):
            ratio = current / total if total else 0
            root.after(0, lambda: self.progress_bar.set(ratio))
            root.after(0, lambda: self.status_var.set(f"{current}/{total}"))

        def thread():
            success, message = process_images(
                input_folder, output_folder, left, right, top, bottom,
                on_progress=on_progress,
            )

            def done():
                if success:
                    self.state.last_trim_output_folder = output_folder
                    self.state.notify("trim_complete", output_folder)
                    messagebox.showinfo("完了", message)
                else:
                    messagebox.showerror("エラー", message)
                self.trim_btn.configure(state="normal")
                self.preview_btn.configure(state="normal")
                self.status_var.set("完了" if success else "エラー")

            root.after(0, done)

        threading.Thread(target=thread, daemon=True).start()
