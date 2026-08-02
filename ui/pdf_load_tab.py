"""PDF読込タブ

外部PDF（自前キャプチャでないPDF）を画像化して
トリミング/変換タブに引き継ぐためのタブ。

キャプチャタブと並ぶ「入力源」のタブで、
出力フォルダは state.last_capture_folder に格納されて
トリミング・変換タブに自動連携される。
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.pdf_extractor import extract_pdf_to_images
from ui.widgets import LabeledFrame


class PdfLoadTab(ctk.CTkFrame):
    """PDF読込タブ: PDFファイル → 画像フォルダ展開"""

    def __init__(self, parent, state, config):
        super().__init__(parent, fg_color="transparent")
        self.state = state
        self.config = config
        self._build_ui()

    def _build_ui(self):
        # --- 入力PDF ---
        input_frame = LabeledFrame(self, text="入力PDF")
        input_frame.pack(fill="x", padx=10, pady=5)
        input_frame.body.grid_columnconfigure(1, weight=1)

        self.pdf_path_var = tk.StringVar()
        ctk.CTkLabel(input_frame.body, text="PDFファイル:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(input_frame.body, textvariable=self.pdf_path_var).grid(
            row=0, column=1, padx=5, pady=3, sticky="ew",
        )
        ctk.CTkButton(input_frame.body, text="参照", width=80, command=self._browse_pdf).grid(
            row=0, column=2, padx=5, pady=3,
        )

        # --- 出力設定 ---
        output_frame = LabeledFrame(self, text="出力設定")
        output_frame.pack(fill="x", padx=10, pady=5)
        output_frame.body.grid_columnconfigure(1, weight=1)

        self.output_folder_var = tk.StringVar()
        ctk.CTkLabel(output_frame.body, text="出力フォルダ:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(output_frame.body, textvariable=self.output_folder_var).grid(
            row=0, column=1, padx=5, pady=3, sticky="ew",
        )
        ctk.CTkButton(output_frame.body, text="参照", width=80, command=self._browse_output).grid(
            row=0, column=2, padx=5, pady=3,
        )

        # DPI / 形式
        opts = ctk.CTkFrame(output_frame.body, fg_color="transparent")
        opts.grid(row=1, column=0, columnspan=3, padx=5, pady=3, sticky="w")

        ctk.CTkLabel(opts, text="DPI:").pack(side="left", padx=(5, 2))
        self.dpi_var = tk.StringVar(value="200")
        ctk.CTkComboBox(
            opts, variable=self.dpi_var,
            values=["150", "200", "300", "400"], width=80,
        ).pack(side="left", padx=2)

        ctk.CTkLabel(opts, text="形式:").pack(side="left", padx=(15, 2))
        self.format_var = tk.StringVar(value="png")
        ctk.CTkRadioButton(opts, text="PNG", variable=self.format_var, value="png").pack(side="left", padx=4)
        ctk.CTkRadioButton(opts, text="JPG", variable=self.format_var, value="jpg").pack(side="left", padx=4)

        ctk.CTkLabel(
            opts, text_color=("gray35", "gray70"),
            text="（高DPIほど高画質・OCR精度↑だが画像サイズも大きくなります）",
        ).pack(side="left", padx=10)

        # --- アクション ---
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=5)

        self.run_btn = ctk.CTkButton(action_frame, text="画像に展開", command=self._run_extract)
        self.run_btn.pack(side="left", padx=5)

        # --- 進捗 ---
        progress_frame = LabeledFrame(self, text="進捗")
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.status_var = tk.StringVar(value="待機中")

        self.progress_bar = ctk.CTkProgressBar(progress_frame.body)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(progress_frame.body, textvariable=self.status_var).pack(padx=10, pady=2)

        # --- ログ ---
        log_frame = LabeledFrame(self, text="ログ")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = ctk.CTkTextbox(log_frame.body, height=180, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

    def _browse_pdf(self):
        path = filedialog.askopenfilename(
            title="PDFファイルを選択",
            filetypes=[("PDF", "*.pdf"), ("すべて", "*.*")],
        )
        if not path:
            return
        self.pdf_path_var.set(path)
        # 出力フォルダ未設定なら自動設定（PDFと同階層に <名前>_pages）
        if not self.output_folder_var.get():
            base_dir = os.path.dirname(path)
            stem = os.path.splitext(os.path.basename(path))[0]
            self.output_folder_var.set(os.path.join(base_dir, f"{stem}_pages"))

    def _browse_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder_var.set(folder)

    def _log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _run_extract(self):
        pdf_path = self.pdf_path_var.get().strip()
        output_folder = self.output_folder_var.get().strip()

        if not pdf_path:
            messagebox.showerror("エラー", "PDFファイルを選択してください。")
            return
        if not output_folder:
            messagebox.showerror("エラー", "出力フォルダを指定してください。")
            return

        try:
            dpi = int(self.dpi_var.get())
        except ValueError:
            messagebox.showerror("エラー", "DPI は整数で指定してください。")
            return
        image_format = self.format_var.get()

        self.progress_bar.set(0)
        self.status_var.set("展開中...")
        self.run_btn.configure(state="disabled")

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._log(f"PDF: {pdf_path}")
        self._log(f"出力: {output_folder}")
        self._log(f"DPI={dpi}, 形式={image_format}")

        root = self.winfo_toplevel()

        def on_progress(current, total, filename):
            ratio = current / total if total else 0
            root.after(0, lambda: self.progress_bar.set(ratio))
            root.after(0, lambda: self.status_var.set(f"{current}/{total}"))

        def thread():
            success, message = extract_pdf_to_images(
                pdf_path, output_folder, dpi=dpi,
                image_format=image_format, on_progress=on_progress,
            )

            def done():
                self.run_btn.configure(state="normal")
                if success:
                    self.status_var.set("完了")
                    self._log(f"展開完了: {message}")
                    self.state.last_capture_folder = output_folder
                    self.state.notify("capture_complete", output_folder)
                    messagebox.showinfo(
                        "完了",
                        f"PDFを画像に展開しました。\n"
                        f"出力先: {output_folder}\n\n"
                        f"トリミングタブに引き継がれました。",
                    )
                else:
                    self.status_var.set("エラー")
                    self._log(f"エラー: {message}")
                    messagebox.showerror("エラー", message)

            root.after(0, done)

        threading.Thread(target=thread, daemon=True).start()
