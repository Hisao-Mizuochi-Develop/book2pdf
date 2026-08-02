"""変換タブ

フォルダ選択 → 出力形式（画像PDF / テキストPDF / 検索可能PDF / Markdown）→ 実行
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core import ocr_engine
from core.chapter_detector import detect_chapters
from core.pdf_builder import (
    images_to_pdf,
    images_to_searchable_pdf,
    images_with_text_pdf,
    text_to_pdf,
)
from ui.widgets import LabeledFrame

# 置換辞書ファイル (replacements.json) が無いときに書き出す初期テンプレ。
# 本ごとの誤認識癖を覚えていく中心ファイルなので、自由にコメント (_ で始まるキー) や
# ルールを足せるよう実例を入れておく。
_DEFAULT_REPLACEMENTS_JSON = '''{
  "_comment": "OCR誤認識の置換辞書。'literal' は単純な文字列置換、'regex' は正規表現置換。",
  "_usage": "_で始まるキーは無視されます。本ごとの癖を覚えたら追加してください。",
  "literal": {
    "゠": "ー",
    "—": "ー"
  },
  "regex": [
    {"_comment": "数字に挟まれた大文字 O は 0 の誤認識として扱う", "pattern": "(?<=\\\\d)O(?=\\\\d)", "replace": "0"},
    {"_comment": "数字に挟まれた l (小文字エル) は 1 の誤認識として扱う", "pattern": "(?<=\\\\d)l(?=\\\\d)", "replace": "1"}
  ]
}
'''


class ConvertTab(ctk.CTkFrame):
    """変換タブ: 画像PDF / OCR→テキストPDF / OCR→検索可能PDF / OCR→Markdown"""

    def __init__(self, parent, state, config):
        super().__init__(parent, fg_color="transparent")
        self.state = state
        self.config = config
        state.add_listener(self._on_state_change)
        self._build_ui()

    def _on_state_change(self, event, data):
        if event in ("capture_complete", "trim_complete") and data:
            self.input_var.set(data)

    def _build_ui(self):
        # --- 入力フォルダ ---
        folder_frame = LabeledFrame(self, text="入力")
        folder_frame.pack(fill="x", padx=10, pady=5)
        folder_frame.body.grid_columnconfigure(1, weight=1)

        self.input_var = tk.StringVar()
        ctk.CTkLabel(folder_frame.body, text="画像フォルダ:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(folder_frame.body, textvariable=self.input_var).grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        ctk.CTkButton(folder_frame.body, text="参照", width=80, command=self._browse_input).grid(row=0, column=2, padx=5, pady=3)

        # --- 出力形式 ---
        format_frame = LabeledFrame(self, text="出力形式")
        format_frame.pack(fill="x", padx=10, pady=5)

        self.format_var = tk.StringVar(value="image_pdf")

        formats = [
            ("image_pdf", "画像PDF（画像をそのままPDFに）"),
            ("text_pdf", "テキストPDF（OCR → テキストのみ、軽量）"),
            ("searchable_pdf", "検索可能PDF（画像 + 不可視OCRテキスト）"),
            ("markdown", "Markdown（OCR → .mdファイル）"),
            ("image_text_pdf", "画像+テキストPDF（画像ページ→OCRテキストページの見開き）"),
        ]
        for i, (value, text) in enumerate(formats):
            ctk.CTkRadioButton(
                format_frame.body, text=text, variable=self.format_var, value=value,
                command=self._on_format_changed,
            ).grid(row=i, column=0, padx=10, pady=2, sticky="w")

        # OCRエンジン情報 (NDLOCR-Lite 固定)
        self._build_ocr_engine_section(format_frame.body, start_row=len(formats))

        # OCR 前処理オプション (画像PDF以外で機能)
        self._build_preprocess_section(format_frame.body, start_row=len(formats) + 2)

        # OCR 後処理: 置換辞書 (画像PDF以外で機能)
        self._build_replacements_section(format_frame.body, start_row=len(formats) + 4)

        # 章しおり (PDF出力時のみ機能)
        self._build_bookmarks_section(format_frame.body, start_row=len(formats) + 6)

        # 段落整形オプション (Markdown 出力時のみ機能)
        self._build_reflow_section(format_frame.body, start_row=len(formats) + 8)

        # --- 出力設定 ---
        output_frame = LabeledFrame(self, text="出力")
        output_frame.pack(fill="x", padx=10, pady=5)
        output_frame.body.grid_columnconfigure(1, weight=1)

        self.output_var = tk.StringVar()
        ctk.CTkLabel(output_frame.body, text="出力先:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(output_frame.body, textvariable=self.output_var).grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        ctk.CTkButton(output_frame.body, text="参照", width=80, command=self._browse_output).grid(row=0, column=2, padx=5, pady=3)

        self.filename_var = tk.StringVar()
        ctk.CTkLabel(output_frame.body, text="ファイル名:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(output_frame.body, textvariable=self.filename_var).grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        # --- アクションボタン ---
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=5)

        self.run_btn = ctk.CTkButton(action_frame, text="変換実行", command=self._run_convert)
        self.run_btn.pack(side="left", padx=5)

        # --- 進捗 ---
        progress_frame = LabeledFrame(self, text="進捗")
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.status_var = tk.StringVar(value="待機中")

        self.progress_bar = ctk.CTkProgressBar(progress_frame.body)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(progress_frame.body, textvariable=self.status_var).pack(padx=10, pady=2)

        # --- OCR結果プレビュー ---
        result_frame = LabeledFrame(self, text="結果")
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.result_text = ctk.CTkTextbox(result_frame.body, height=120, wrap="word", state="disabled")
        self.result_text.pack(fill="both", expand=True, padx=4, pady=4)

        self._on_format_changed()

    def _build_ocr_engine_section(self, parent, start_row):
        """OCR エンジン情報を表示する (NDLOCR-Lite 固定)。"""
        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray70", "gray35"))
        sep.grid(row=start_row, column=0, sticky="ew", padx=10, pady=5)

        engine_frame = ctk.CTkFrame(parent, fg_color="transparent")
        engine_frame.grid(row=start_row + 1, column=0, padx=10, pady=2, sticky="w")

        engines = ocr_engine.get_available_engines()
        engine = engines[0] if engines else None

        ctk.CTkLabel(engine_frame, text="OCRエンジン:").pack(side="left", padx=(0, 5))
        if engine and engine.get("available"):
            text = engine.get("description", "NDLOCR-Lite")
            color = ("gray35", "gray75")
        else:
            text = "（NDLOCR-Lite が見つかりません — README を参照してください）"
            color = ("#b00020", "#ff6b6b")
        ctk.CTkLabel(engine_frame, text=text, text_color=color).pack(side="left")

    def _build_preprocess_section(self, parent, start_row):
        """OCR 前処理オプション (Lanczos アップスケール・コントラスト強調)。

        画像PDF以外（OCR を回す形式）で有効。
        """
        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray70", "gray35"))
        sep.grid(row=start_row, column=0, sticky="ew", padx=10, pady=5)

        # コントロール行 + 補足説明行を縦に並べるためのコンテナ
        pp_section = ctk.CTkFrame(parent, fg_color="transparent")
        pp_section.grid(row=start_row + 1, column=0, padx=10, pady=2, sticky="ew")

        pp_frame = ctk.CTkFrame(pp_section, fg_color="transparent")
        pp_frame.pack(anchor="w")

        pp_cfg = self.config.get("ocr", {}).get("preprocess", {})

        self.pp_enabled_var = tk.BooleanVar(value=bool(pp_cfg.get("enabled", True)))
        self.pp_enabled_check = ctk.CTkCheckBox(
            pp_frame,
            text="OCR前処理を有効化",
            variable=self.pp_enabled_var,
            command=self._on_preprocess_changed,
        )
        self.pp_enabled_check.pack(side="left")

        ctk.CTkLabel(pp_frame, text="倍率:").pack(side="left", padx=(15, 2))
        self.pp_upscale_var = tk.StringVar(value=str(pp_cfg.get("upscale", 1.5)))
        self.pp_upscale_combo = ctk.CTkComboBox(
            pp_frame,
            variable=self.pp_upscale_var,
            values=["1.0", "1.5", "2.0"],
            width=80,
            command=lambda _v=None: self._on_preprocess_changed(),
        )
        self.pp_upscale_combo.pack(side="left", padx=2)

        self.pp_contrast_var = tk.BooleanVar(value=bool(pp_cfg.get("enhance_contrast", True)))
        self.pp_contrast_check = ctk.CTkCheckBox(
            pp_frame,
            text="コントラスト強調",
            variable=self.pp_contrast_var,
            command=self._on_preprocess_changed,
        )
        self.pp_contrast_check.pack(side="left", padx=(15, 0))

        ctk.CTkLabel(
            pp_frame, text_color=("gray35", "gray70"),
            text="（Kindle のアンチエイリアス文字に効きやすい / OCR 時のみ）",
        ).pack(side="left", padx=10)

        # 倍率の意味と選び方を補足する説明 (コントロール行の直下に配置)
        ctk.CTkLabel(
            pp_section,
            text=(
                "※倍率は OCR にかける前に画像を Lanczos で拡大する係数です。"
                "1.0=拡大なし / 1.5=推奨 (低解像度キャプチャ向け) / 2.0=さらに丁寧（処理時間は伸びます）。"
            ),
            text_color=("gray35", "gray70"),
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

    def _on_preprocess_changed(self):
        """前処理オプションの変更を config に保存する。"""
        from core.config import save_config
        try:
            upscale = float(self.pp_upscale_var.get())
        except ValueError:
            upscale = 1.5
        ocr_cfg = self.config.setdefault("ocr", {})
        pp_cfg = ocr_cfg.setdefault("preprocess", {})
        pp_cfg["enabled"] = bool(self.pp_enabled_var.get())
        pp_cfg["upscale"] = upscale
        pp_cfg["enhance_contrast"] = bool(self.pp_contrast_var.get())
        save_config(self.config)

    def _get_preprocess_opts(self):
        """OCR 呼び出し時に渡す preprocess_opts を組み立てる。"""
        pp_cfg = self.config.get("ocr", {}).get("preprocess", {})
        try:
            upscale = float(self.pp_upscale_var.get())
        except (AttributeError, ValueError):
            upscale = float(pp_cfg.get("upscale", 1.5))
        return {
            "enabled": bool(self.pp_enabled_var.get()) if hasattr(self, "pp_enabled_var") else bool(pp_cfg.get("enabled", True)),
            "upscale": upscale,
            "enhance_contrast": bool(self.pp_contrast_var.get()) if hasattr(self, "pp_contrast_var") else bool(pp_cfg.get("enhance_contrast", True)),
            "binarize": bool(pp_cfg.get("binarize", False)),
            "binarize_threshold": int(pp_cfg.get("binarize_threshold", 180)),
        }

    def _build_replacements_section(self, parent, start_row):
        """OCR 後処理: 置換辞書 (replacements.json) のオン/オフと辞書編集導線。"""
        from core import text_replacements

        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray70", "gray35"))
        sep.grid(row=start_row, column=0, sticky="ew", padx=10, pady=5)

        rep_frame = ctk.CTkFrame(parent, fg_color="transparent")
        rep_frame.grid(row=start_row + 1, column=0, padx=10, pady=2, sticky="w")

        rep_cfg = self.config.get("ocr", {}).get("replacements", {})
        self._replacements_default_path = text_replacements.default_path()
        self._replacements_path = rep_cfg.get("path") or self._replacements_default_path

        self.rep_enabled_var = tk.BooleanVar(value=bool(rep_cfg.get("enabled", True)))
        ctk.CTkCheckBox(
            rep_frame,
            text="置換辞書を適用",
            variable=self.rep_enabled_var,
            command=self._on_replacements_changed,
        ).pack(side="left")

        ctk.CTkButton(
            rep_frame, text="辞書を編集", width=100,
            command=self._open_replacements_file,
        ).pack(side="left", padx=(15, 4))

        ctk.CTkLabel(
            rep_frame, text_color=("gray35", "gray70"),
            text=f"（{os.path.basename(self._replacements_path)} / OCR 時のみ）",
        ).pack(side="left", padx=10)

    def _on_replacements_changed(self):
        from core.config import save_config
        ocr_cfg = self.config.setdefault("ocr", {})
        rep_cfg = ocr_cfg.setdefault("replacements", {})
        rep_cfg["enabled"] = bool(self.rep_enabled_var.get())
        save_config(self.config)

    def _open_replacements_file(self):
        """置換辞書ファイルを OS 既定エディタで開く。無ければ作ってから開く。"""
        path = self._replacements_path
        if not os.path.exists(path):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(_DEFAULT_REPLACEMENTS_JSON)
            except OSError as e:
                messagebox.showerror("エラー", f"辞書ファイルを作成できません: {e}")
                return
        try:
            os.startfile(path)  # noqa: SIM115 (Windows 既定アプリで開く)
        except OSError as e:
            messagebox.showerror("エラー", f"辞書ファイルを開けません: {e}\nパス: {path}")

    def _get_replacements_opts(self):
        return {
            "enabled": bool(self.rep_enabled_var.get()) if hasattr(self, "rep_enabled_var") else True,
            "path": self._replacements_path if hasattr(self, "_replacements_path") else "",
        }

    def _build_bookmarks_section(self, parent, start_row):
        """PDF 出力時に章しおり (アウトライン) を埋め込むかのトグル。"""
        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray70", "gray35"))
        sep.grid(row=start_row, column=0, sticky="ew", padx=10, pady=5)

        bm_frame = ctk.CTkFrame(parent, fg_color="transparent")
        bm_frame.grid(row=start_row + 1, column=0, padx=10, pady=2, sticky="w")

        bm_cfg = self.config.get("ocr", {}).get("chapter_bookmarks", {})
        self.bookmarks_var = tk.BooleanVar(value=bool(bm_cfg.get("enabled", True)))
        ctk.CTkCheckBox(
            bm_frame,
            text="章を自動検出してしおりを埋め込む",
            variable=self.bookmarks_var,
            command=self._on_bookmarks_changed,
        ).pack(side="left")

        ctk.CTkLabel(
            bm_frame, text_color=("gray35", "gray70"),
            text="（PDF 出力時のみ / 「第◯章」「Chapter N」等を抽出）",
        ).pack(side="left", padx=10)

    def _on_bookmarks_changed(self):
        from core.config import save_config
        ocr_cfg = self.config.setdefault("ocr", {})
        bm_cfg = ocr_cfg.setdefault("chapter_bookmarks", {})
        bm_cfg["enabled"] = bool(self.bookmarks_var.get())
        save_config(self.config)

    def _detect_chapters_if_enabled(self, results):
        """しおり機能が有効なら章検出を行い、結果を返す。"""
        if not getattr(self, "bookmarks_var", None) or not self.bookmarks_var.get():
            return None
        return detect_chapters(results)

    def _build_reflow_section(self, parent, start_row):
        """段落整形 + 画像併記 (Markdown 出力時のみ機能)。"""
        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray70", "gray35"))
        sep.grid(row=start_row, column=0, sticky="ew", padx=10, pady=5)

        reflow_frame = ctk.CTkFrame(parent, fg_color="transparent")
        reflow_frame.grid(row=start_row + 1, column=0, padx=10, pady=2, sticky="w")

        ocr_cfg = self.config.get("ocr", {})
        self.reflow_var = tk.BooleanVar(
            value=bool(ocr_cfg.get("reflow_paragraphs", True))
        )
        self.reflow_check = ctk.CTkCheckBox(
            reflow_frame,
            text="段落を自動整形 (Markdown出力時のみ)",
            variable=self.reflow_var,
        )
        self.reflow_check.pack(side="left")

        md_cfg = ocr_cfg.get("markdown", {})
        self.embed_images_var = tk.BooleanVar(
            value=bool(md_cfg.get("embed_images", False))
        )
        self.embed_images_check = ctk.CTkCheckBox(
            reflow_frame,
            text="ページ画像を併記",
            variable=self.embed_images_var,
            command=self._on_embed_images_changed,
        )
        self.embed_images_check.pack(side="left", padx=(15, 0))

    def _on_embed_images_changed(self):
        from core.config import save_config
        ocr_cfg = self.config.setdefault("ocr", {})
        md_cfg = ocr_cfg.setdefault("markdown", {})
        md_cfg["embed_images"] = bool(self.embed_images_var.get())
        save_config(self.config)

    def _on_format_changed(self):
        """出力形式変更時、段落整形・画像併記オプションの有効/無効を切り替える。"""
        fmt = self.format_var.get()
        is_md = fmt == "markdown"
        # 段落整形は Markdown と 画像+テキストPDF の両方で使う
        supports_reflow = fmt in ("markdown", "image_text_pdf")
        if hasattr(self, "reflow_check"):
            self.reflow_check.configure(state="normal" if supports_reflow else "disabled")
        # 「ページ画像を併記」は Markdown 内に画像リンクを埋め込むかどうかのオプションで、
        # 画像+テキストPDF では常に画像ページを出力するため対象外
        if hasattr(self, "embed_images_check"):
            self.embed_images_check.configure(state="normal" if is_md else "disabled")

    def _browse_input(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_var.set(folder)

    def _browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_var.set(path)

    def _set_result(self, text):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")

    def _run_convert(self):
        input_folder = self.input_var.get()
        output_folder = self.output_var.get()
        filename = self.filename_var.get()
        fmt = self.format_var.get()

        if not input_folder:
            messagebox.showerror("エラー", "画像フォルダを選択してください。")
            return
        if not output_folder:
            messagebox.showerror("エラー", "出力先を選択してください。")
            return
        if not filename:
            messagebox.showerror("エラー", "ファイル名を入力してください。")
            return

        self.progress_bar.set(0)
        self.status_var.set("開始中...")
        self.run_btn.configure(state="disabled")

        root = self.winfo_toplevel()

        def on_progress(current, total, fname):
            ratio = current / total if total else 0
            root.after(0, lambda: self.progress_bar.set(ratio))
            root.after(0, lambda: self.status_var.set(f"{current}/{total} ({fname})"))

        def thread():
            success = False
            message = ""

            try:
                if fmt == "image_pdf":
                    success, message = self._convert_image_pdf(
                        input_folder, output_folder, filename, on_progress,
                    )
                elif fmt == "text_pdf":
                    success, message = self._convert_text_pdf(
                        input_folder, output_folder, filename, on_progress, root,
                    )
                elif fmt == "searchable_pdf":
                    success, message = self._convert_searchable_pdf(
                        input_folder, output_folder, filename, on_progress, root,
                    )
                elif fmt == "markdown":
                    success, message = self._convert_markdown(
                        input_folder, output_folder, filename, on_progress, root,
                    )
                elif fmt == "image_text_pdf":
                    success, message = self._convert_image_text_pdf(
                        input_folder, output_folder, filename, on_progress, root,
                    )
            except Exception as e:
                success = False
                message = f"エラー: {e}"

            def done():
                if success:
                    messagebox.showinfo("完了", message)
                    self._set_result(message)
                else:
                    messagebox.showerror("エラー", message)
                    self._set_result(f"エラー: {message}")
                self.run_btn.configure(state="normal")
                self.status_var.set("完了" if success else "エラー")

            root.after(0, done)

        threading.Thread(target=thread, daemon=True).start()

    def _convert_image_pdf(self, input_folder, output_folder, filename, on_progress):
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        return images_to_pdf(input_folder, output_folder, filename, on_progress)

    def _convert_text_pdf(self, input_folder, output_folder, filename, on_progress, root):
        root.after(0, lambda: self.status_var.set("OCR処理中..."))

        success, results = ocr_engine.process_folder_collect(
            input_folder, on_progress=on_progress,
            preprocess_opts=self._get_preprocess_opts(),
            replacements_opts=self._get_replacements_opts(),
        )
        if not success:
            return False, results

        root.after(0, lambda: self.status_var.set("PDF生成中..."))
        root.after(0, lambda: self.progress_bar.set(0))

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        output_path = os.path.join(output_folder, filename)
        chapters = self._detect_chapters_if_enabled(results)
        return text_to_pdf(results, output_path, on_progress=on_progress, chapters=chapters)

    def _convert_searchable_pdf(self, input_folder, output_folder, filename, on_progress, root):
        root.after(0, lambda: self.status_var.set("OCR処理中..."))

        success, results = ocr_engine.process_folder_collect(
            input_folder, on_progress=on_progress,
            preprocess_opts=self._get_preprocess_opts(),
            replacements_opts=self._get_replacements_opts(),
        )
        if not success:
            return False, results

        root.after(0, lambda: self.status_var.set("検索可能PDF生成中..."))
        root.after(0, lambda: self.progress_bar.set(0))

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        output_path = os.path.join(output_folder, filename)
        chapters = self._detect_chapters_if_enabled(results)
        return images_to_searchable_pdf(
            input_folder, results, output_path,
            on_progress=on_progress, chapters=chapters,
        )

    def _convert_image_text_pdf(self, input_folder, output_folder, filename, on_progress, root):
        root.after(0, lambda: self.status_var.set("OCR処理中..."))

        success, results = ocr_engine.process_folder_collect(
            input_folder, on_progress=on_progress,
            preprocess_opts=self._get_preprocess_opts(),
            replacements_opts=self._get_replacements_opts(),
        )
        if not success:
            return False, results

        root.after(0, lambda: self.status_var.set("画像+テキストPDF生成中..."))
        root.after(0, lambda: self.progress_bar.set(0))

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        output_path = os.path.join(output_folder, filename)
        chapters = self._detect_chapters_if_enabled(results)
        reflow = bool(self.reflow_var.get())
        return images_with_text_pdf(
            input_folder, results, output_path,
            on_progress=on_progress, chapters=chapters, reflow=reflow,
        )

    def _convert_markdown(self, input_folder, output_folder, filename, on_progress, root):
        root.after(0, lambda: self.status_var.set("OCR処理中..."))

        success, results = ocr_engine.process_folder_collect(
            input_folder, on_progress=on_progress,
            preprocess_opts=self._get_preprocess_opts(),
            replacements_opts=self._get_replacements_opts(),
        )
        if not success:
            return False, results

        root.after(0, lambda: self.status_var.set("Markdown生成中..."))

        if not filename.lower().endswith(".md"):
            filename += ".md"
        output_path = os.path.join(output_folder, filename)

        from core.markdown_writer import write_markdown
        reflow = bool(self.reflow_var.get())
        embed_images = bool(self.embed_images_var.get())
        chapters = self._detect_chapters_if_enabled(results)
        success, message = write_markdown(
            results, output_path, title=filename.replace(".md", ""),
            reflow=reflow,
            chapters=chapters,
            embed_images=embed_images,
            image_folder=input_folder if embed_images else None,
        )
        if not success:
            return success, message

        notes = []
        if reflow:
            notes.append("段落を自動整形しました。")
        if chapters:
            notes.append(f"章見出しを {len(chapters)} 件挿入しました。")
        if embed_images:
            notes.append("ページ画像を併記しました。")
        if notes:
            message += "\n" + "\n".join(notes)
        return True, message
