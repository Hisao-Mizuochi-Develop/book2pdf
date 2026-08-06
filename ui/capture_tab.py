"""キャプチャタブ

プロファイル選択 → ウィンドウ検出 → キャプチャ実行 → 保存先表示
"""

import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

from core.capture_engine import CaptureEngine
from core.capture_profiles import (
    BUILTIN_PROFILES,
    CaptureProfile,
    get_all_profile_keys,
)
from core.config import save_config
from core.window_utils import (
    get_title,
    get_window_process_name,
    get_window_rect,
    get_window_title,
)
from ui.widgets import LabeledFrame, Tooltip


class CaptureTab(ctk.CTkFrame):
    """キャプチャタブ: プロファイル選択 → ウィンドウ検出 → キャプチャ実行"""

    def __init__(self, parent, state, config):
        super().__init__(parent, fg_color="transparent")
        self.state = state
        self.config = config
        self._running = False
        self._capture_engine = None
        self._build_ui()

    def _build_ui(self):
        # --- プロファイル選択 ---
        profile_frame = LabeledFrame(self, text="プロファイル選択")
        profile_frame.pack(fill="x", padx=10, pady=5)

        row0 = ctk.CTkFrame(profile_frame.body, fg_color="transparent")
        row0.pack(fill="x", padx=5, pady=5)
        row0.grid_columnconfigure(1, weight=1)

        self.profile_var = tk.StringVar(
            value=self.config["capture"].get("active_profile", "kindle")
        )
        profile_keys = get_all_profile_keys(self.config)

        ctk.CTkLabel(row0, text="アプリ:").grid(row=0, column=0, padx=5, pady=3, sticky="e")

        self.profile_info = tk.StringVar(value="")
        profile_inner = ctk.CTkFrame(row0, fg_color="transparent")
        profile_inner.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        self.profile_combo = ctk.CTkComboBox(
            profile_inner, variable=self.profile_var,
            values=profile_keys, state="readonly", width=180,
            command=self._on_profile_changed,
        )
        self.profile_combo.pack(side="left", padx=5)
        ctk.CTkLabel(profile_inner, textvariable=self.profile_info).pack(side="left", padx=5)

        ctk.CTkLabel(row0, text="ページめくり:").grid(row=0, column=2, padx=(20, 5), pady=3, sticky="e")
        self.page_turn_var = tk.StringVar(value="right")
        page_turn_frame = ctk.CTkFrame(row0, fg_color="transparent")
        page_turn_frame.grid(row=0, column=3, padx=5, pady=3, sticky="w")
        ctk.CTkRadioButton(page_turn_frame, text="→ 右 (通常)", variable=self.page_turn_var, value="right").pack(side="left", padx=3)
        ctk.CTkRadioButton(page_turn_frame, text="← 左 (漫画)", variable=self.page_turn_var, value="left").pack(side="left", padx=3)

        # --- 開始位置 + 待機時間（下段） ---
        row1 = ctk.CTkFrame(profile_frame.body, fg_color="transparent")
        row1.pack(fill="x", padx=5, pady=(0, 5))
        row1.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row1, text="開始位置:").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        start_pos_frame = ctk.CTkFrame(row1, fg_color="transparent")
        start_pos_frame.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        self.start_position_var = tk.StringVar(value="beginning")
        start_pos_begin_rb = ctk.CTkRadioButton(
            start_pos_frame, text="先頭ページから", variable=self.start_position_var, value="beginning"
        )
        start_pos_begin_rb.pack(side="left", padx=3)
        start_pos_current_rb = ctk.CTkRadioButton(
            start_pos_frame, text="現在ページから", variable=self.start_position_var, value="current"
        )
        start_pos_current_rb.pack(side="left", padx=3)
        Tooltip(
            start_pos_current_rb,
            "「先頭ページから」を選ぶと、キャプチャ開始前に本を先頭ページまで自動で"
            "戻してから撮影を始めます（本の長さによっては時間がかかります）。\n"
            "「現在ページから」は今表示しているページからそのまま撮影します。",
        )

        # 待機時間（page_wait）入力 — 詳細設定にも同じ変数を共有
        ctk.CTkLabel(row1, text="待機時間(秒):").grid(row=0, column=2, padx=(20, 5), pady=3, sticky="e")
        self.page_wait_var = tk.StringVar(value="0.15")
        page_wait_entry = ctk.CTkEntry(row1, textvariable=self.page_wait_var, width=70)
        page_wait_entry.grid(row=0, column=3, padx=5, pady=3, sticky="w")
        Tooltip(
            page_wait_entry,
            self._build_page_wait_tooltip(),
        )

        self._on_profile_changed()

        # --- 詳細設定（折りたたみ） ---
        self._build_detail_settings()

        # --- 保存設定 ---
        save_frame = LabeledFrame(self, text="保存設定")
        save_frame.pack(fill="x", padx=10, pady=5)
        save_frame.body.grid_columnconfigure(1, weight=1)

        self.title_var = tk.StringVar()
        self.save_folder_var = tk.StringVar()

        ctk.CTkLabel(save_frame.body, text="タイトル:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(save_frame.body, textvariable=self.title_var).grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        ctk.CTkButton(save_frame.body, text="入力", width=80, command=self._input_title).grid(row=0, column=2, padx=5, pady=3)

        ctk.CTkLabel(save_frame.body, text="フォルダ:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(save_frame.body, textvariable=self.save_folder_var).grid(row=1, column=1, padx=5, pady=3, sticky="ew")
        ctk.CTkButton(save_frame.body, text="参照", width=80, command=self._select_folder).grid(row=1, column=2, padx=5, pady=3)

        # --- アクションボタン ---
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=5)

        self.start_btn = ctk.CTkButton(action_frame, text="キャプチャ開始", command=self._start_capture)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ctk.CTkButton(action_frame, text="停止", command=self._stop_capture, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        # --- 進捗 & ログ ---
        progress_frame = LabeledFrame(self, text="進捗")
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.status_var = tk.StringVar(value="待機中")

        self.progress_bar = ctk.CTkProgressBar(progress_frame.body)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(progress_frame.body, textvariable=self.status_var).pack(padx=10, pady=2)

        log_frame = LabeledFrame(self, text="ログ")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = ctk.CTkTextbox(log_frame.body, height=140, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

    def _build_detail_settings(self):
        """詳細設定の折りたたみセクション"""
        self._detail_visible = False

        toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggle_frame.pack(fill="x", padx=10, pady=(0, 2))
        self._detail_toggle_btn = ctk.CTkButton(
            toggle_frame, text="▶ 詳細設定", width=120, command=self._toggle_details,
        )
        self._detail_toggle_btn.pack(side="left")

        self._detail_frame = LabeledFrame(self, text="プロファイル詳細設定")

        fields = ctk.CTkFrame(self._detail_frame.body, fg_color="transparent")
        fields.pack(fill="x", padx=5, pady=5)

        profile_data = self._get_profile_data()

        self.window_keyword_var = tk.StringVar(value=profile_data.get("window_title_keyword", ""))
        # page_wait_var は _build_ui の row0 で既に作成済み。値だけ反映する。
        self.page_wait_var.set(str(profile_data.get("page_wait", 0.5)))
        _bm = profile_data.get("boundary_method", "full")
        self.boundary_var = tk.StringVar(value=_bm if _bm == "manual" else "full")
        self.process_name_var = tk.StringVar(value=profile_data.get("process_name", ""))

        ctk.CTkLabel(fields, text="ウィンドウタイトル:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(fields, textvariable=self.window_keyword_var, width=240).grid(row=0, column=1, padx=5, pady=3)

        ctk.CTkLabel(fields, text="プロセス名:").grid(row=0, column=2, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(fields, textvariable=self.process_name_var, width=140).grid(row=0, column=3, padx=5, pady=3)

        ctk.CTkLabel(fields, text="待機時間(秒):").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        ctk.CTkEntry(fields, textvariable=self.page_wait_var, width=100).grid(row=1, column=1, padx=5, pady=3, sticky="w")

        ctk.CTkLabel(fields, text="取り込み範囲:").grid(row=1, column=2, padx=5, pady=3, sticky="w")
        boundary_combo = ctk.CTkComboBox(
            fields, variable=self.boundary_var,
            values=["full", "manual"], state="readonly", width=140,
        )
        boundary_combo.grid(row=1, column=3, padx=5, pady=3)
        Tooltip(
            boundary_combo,
            "full: ウィンドウ全体を取り込む（既定）。余白の調整は後段のトリミングタブで行う。\n"
            "manual: 「手動領域選択」で指定した左右範囲だけを取り込む。",
        )

        # カスタムプロファイル操作
        btn_frame = ctk.CTkFrame(self._detail_frame.body, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(btn_frame, text="領域プレビュー", width=120, command=self._show_preview).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="手動領域選択", width=120, command=self._manual_select).pack(side="left", padx=5)

        ctk.CTkFrame(btn_frame, width=2, fg_color=("gray70", "gray35")).pack(side="left", fill="y", padx=8, pady=4)

        self._custom_name_var = tk.StringVar()
        ctk.CTkLabel(btn_frame, text="名前:").pack(side="left", padx=2)
        ctk.CTkEntry(btn_frame, textvariable=self._custom_name_var, width=140).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="複製して保存", width=120, command=self._duplicate_profile).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="上書き保存", width=120, command=self._save_profile).pack(side="left", padx=5)

    def _build_page_wait_tooltip(self):
        """ページ変化検出のポーリング間隔の説明文を組み立てる。"""
        lines = [
            "ページ変化検出のポーリング間隔（秒）。",
            "短いほど次ページへ素早く進むが、描画途中を",
            "誤検知して同じページを2回保存することがある。",
            "",
            "各プロファイルのデフォルト:",
        ]
        for key, prof in BUILTIN_PROFILES.items():
            lines.append(f"  {prof.name} ({key}): {prof.page_wait} 秒")
        return "\n".join(lines)

    def _toggle_details(self):
        if self._detail_visible:
            self._detail_frame.pack_forget()
            self._detail_toggle_btn.configure(text="▶ 詳細設定")
        else:
            # 保存設定の前に挿入
            self._detail_frame.pack(fill="x", padx=10, pady=2,
                                    after=self._detail_toggle_btn.master)
            self._detail_toggle_btn.configure(text="▼ 詳細設定")
        self._detail_visible = not self._detail_visible

    # --- プロファイル ---

    def _get_profile_data(self):
        key = self.profile_var.get()
        profile = BUILTIN_PROFILES.get(key)
        config_data = self.config["capture"]["profiles"].get(key, {})
        if config_data:
            return config_data
        if profile:
            return profile.to_dict()
        return {}

    def _on_profile_changed(self, value=None):
        key = self.profile_var.get()
        profile = BUILTIN_PROFILES.get(key)
        profile_data = self.config["capture"]["profiles"].get(key, {})

        if profile:
            self.profile_info.set(f"({profile.name})")
            self.page_turn_var.set(profile_data.get("page_turn_key", profile.page_turn_key))
        else:
            self.profile_info.set(f"({profile_data.get('name', key)})")
            self.page_turn_var.set(profile_data.get("page_turn_key", "right"))

        # 詳細設定を更新
        data = self._get_profile_data()
        # page_wait_var は row0 で先に作られているので常に更新
        if hasattr(self, 'page_wait_var'):
            self.page_wait_var.set(str(data.get("page_wait", 0.5)))
        if hasattr(self, 'window_keyword_var'):
            self.window_keyword_var.set(data.get("window_title_keyword", ""))
            _bm = data.get("boundary_method", "full")
            self.boundary_var.set(_bm if _bm == "manual" else "full")
            self.process_name_var.set(data.get("process_name", ""))

    def _get_current_profile(self):
        key = self.profile_var.get()
        profile_data = self.config["capture"]["profiles"].get(key, {})
        base = BUILTIN_PROFILES.get(key, CaptureProfile())

        # 詳細設定が開いている場合はそのフィールドの値を優先
        if self._detail_visible:
            return CaptureProfile(
                name=profile_data.get("name", base.name) or key,
                window_title_keyword=self.window_keyword_var.get() or base.window_title_keyword,
                page_turn_key=self.page_turn_var.get(),
                fullscreen_wait=float(profile_data.get("fullscreen_wait", base.fullscreen_wait)),
                page_wait=float(self.page_wait_var.get() or base.page_wait),
                boundary_method=self.boundary_var.get() or base.boundary_method,
                l_margin=profile_data.get("l_margin", base.l_margin),
                r_margin=profile_data.get("r_margin", base.r_margin),
                manual_left=profile_data.get("manual_left", base.manual_left),
                manual_right=profile_data.get("manual_right", base.manual_right),
                click_position=profile_data.get("click_position", base.click_position),
                use_bring_to_top=profile_data.get("use_bring_to_top", base.use_bring_to_top),
                timeout_seconds=float(profile_data.get("timeout_seconds", base.timeout_seconds)),
                max_retries=int(profile_data.get("max_retries", base.max_retries)),
                process_name=self.process_name_var.get() or base.process_name,
            )

        # 詳細設定が閉じていても row0 の page_wait_var は常に有効
        try:
            page_wait_val = float(self.page_wait_var.get())
        except (ValueError, AttributeError):
            page_wait_val = float(profile_data.get("page_wait", base.page_wait))

        return CaptureProfile(
            name=profile_data.get("name", base.name) or key,
            window_title_keyword=profile_data.get("window_title_keyword", base.window_title_keyword),
            page_turn_key=self.page_turn_var.get(),
            fullscreen_wait=float(profile_data.get("fullscreen_wait", base.fullscreen_wait)),
            page_wait=page_wait_val,
            boundary_method=profile_data.get("boundary_method", base.boundary_method),
            l_margin=profile_data.get("l_margin", base.l_margin),
            r_margin=profile_data.get("r_margin", base.r_margin),
            manual_left=profile_data.get("manual_left", base.manual_left),
            manual_right=profile_data.get("manual_right", base.manual_right),
            click_position=profile_data.get("click_position", base.click_position),
            use_bring_to_top=profile_data.get("use_bring_to_top", base.use_bring_to_top),
            timeout_seconds=float(profile_data.get("timeout_seconds", base.timeout_seconds)),
            max_retries=int(profile_data.get("max_retries", base.max_retries)),
            process_name=profile_data.get("process_name", base.process_name),
        )

    def _save_profile(self):
        key = self.profile_var.get()
        profile = self._get_current_profile()
        self.config["capture"]["profiles"][key] = profile.to_dict()
        self.config["capture"]["active_profile"] = key
        save_config(self.config)
        messagebox.showinfo("保存", f"プロファイル '{key}' の設定を保存しました。")

    def _duplicate_profile(self):
        new_key = self._custom_name_var.get().strip()
        if not new_key:
            messagebox.showerror("エラー", "カスタムプロファイル名を入力してください。")
            return
        profile = self._get_current_profile()
        profile.name = new_key
        self.config["capture"]["profiles"][new_key] = profile.to_dict()
        save_config(self.config)
        # コンボボックス更新
        keys = get_all_profile_keys(self.config)
        self.profile_combo.configure(values=keys)
        self.profile_var.set(new_key)
        self._on_profile_changed()
        messagebox.showinfo("保存", f"プロファイル '{new_key}' を作成しました。")

    def _refresh_profile_list(self):
        keys = get_all_profile_keys(self.config)
        self.profile_combo.configure(values=keys)

    # --- 領域プレビュー / 手動選択 ---

    def _show_preview(self):
        profile = self._get_current_profile()
        engine = CaptureEngine(profile, exclude_pid=os.getpid())
        hwnd = engine.find_target_window()
        if hwnd is None:
            messagebox.showerror("エラー", f"ウィンドウが見つかりません: {profile.window_title_keyword}")
            return

        engine.activate_target_window(hwnd)
        time.sleep(1)

        image, left, right = engine.capture_preview()
        if image is None:
            messagebox.showerror("エラー", "プレビューの取得に失敗しました")
            return

        import cv2
        preview_img = image.copy()
        if left is not None:
            cv2.line(preview_img, (left, 0), (left, preview_img.shape[0]), (0, 255, 0), 2)
        if right is not None:
            cv2.line(preview_img, (right, 0), (right, preview_img.shape[0]), (0, 255, 0), 2)

        rgb = cv2.cvtColor(preview_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        pil_img.thumbnail((780, 450), Image.Resampling.LANCZOS)

        preview_win = ctk.CTkToplevel(self)
        preview_win.title("キャプチャ領域プレビュー")
        preview_win.geometry("820x520")

        photo = ImageTk.PhotoImage(pil_img)
        label = tk.Label(preview_win, image=photo)
        label.image = photo
        label.pack(padx=10, pady=10)

        info = f"検出範囲: x={left} ~ {right} (幅: {right - left}px)" if left and right else "境界を検出できませんでした"
        ctk.CTkLabel(preview_win, text=info).pack(pady=5)

    def _manual_select(self):
        import cv2

        # 対象ウィンドウをキャプチャして、その画像上で左右をドラッグ選択する。
        # 全画面スクショではなくウィンドウ画像を使うことで、(1) セカンドモニタ
        # でも正しく取得でき (all_screens 対応済みの _grab を経由)、(2) 選択座標が
        # そのままウィンドウ相対のクロップ座標になり座標系のズレが起きない。
        profile = self._get_current_profile()
        engine = CaptureEngine(profile, exclude_pid=os.getpid())
        hwnd = engine.find_target_window()
        if hwnd is None:
            messagebox.showerror("エラー", f"ウィンドウが見つかりません: {profile.window_title_keyword}")
            return

        engine.activate_target_window(hwnd)
        time.sleep(1)
        engine.set_target_window(hwnd)
        image = engine._grab()
        if image is None or image.size == 0:
            messagebox.showerror("エラー", "ウィンドウのキャプチャに失敗しました")
            return

        win_w = image.shape[1]
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_full = Image.fromarray(rgb)

        # 大きなウィンドウは画面に収まるよう縮小して表示する
        max_w, max_h = 1100, 720
        scale = min(max_w / pil_full.width, max_h / pil_full.height, 1.0)
        disp_w, disp_h = int(pil_full.width * scale), int(pil_full.height * scale)
        disp = pil_full.resize((disp_w, disp_h), Image.Resampling.LANCZOS)

        select_win = ctk.CTkToplevel(self)
        select_win.title("手動領域選択")
        select_win.attributes("-topmost", True)

        canvas = tk.Canvas(select_win, width=disp_w, height=disp_h,
                           cursor="crosshair", highlightthickness=0)
        canvas.pack(padx=8, pady=(8, 4))

        photo = ImageTk.PhotoImage(disp)
        canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.image = photo

        ctk.CTkLabel(
            select_win, text="ドラッグして左右の範囲を選択 / Esc でキャンセル"
        ).pack(pady=(0, 8))

        start_x = [0]
        rect_id = [None]

        def on_press(event):
            start_x[0] = event.x

        def on_drag(event):
            if rect_id[0]:
                canvas.delete(rect_id[0])
            rect_id[0] = canvas.create_rectangle(
                start_x[0], 0, event.x, disp_h, outline="lime", width=3,
            )

        def on_release(event):
            # 表示座標 → ウィンドウ実ピクセル座標へ逆変換し、範囲内にクランプ
            left = int(min(start_x[0], event.x) / scale)
            right = int(max(start_x[0], event.x) / scale)
            left = max(0, min(left, win_w))
            right = max(0, min(right, win_w))
            if right - left < 5:
                messagebox.showwarning("手動選択", "選択範囲が狭すぎます。やり直してください。")
                return
            select_win.destroy()
            self.boundary_var.set("manual")
            key = self.profile_var.get()
            if key not in self.config["capture"]["profiles"]:
                self.config["capture"]["profiles"][key] = self._get_current_profile().to_dict()
            self.config["capture"]["profiles"][key]["boundary_method"] = "manual"
            self.config["capture"]["profiles"][key]["manual_left"] = left
            self.config["capture"]["profiles"][key]["manual_right"] = right
            save_config(self.config)
            messagebox.showinfo(
                "手動選択",
                f"キャプチャ領域を設定しました: left={left}, right={right} "
                f"(ウィンドウ幅 {win_w}px 基準)",
            )

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        select_win.bind("<Escape>", lambda e: select_win.destroy())

    # --- ヘルパー ---

    def _input_title(self):
        title = get_title()
        if title:
            self.title_var.set(title)

    def _select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_folder_var.set(folder)

    def _log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # --- キャプチャ実行 ---

    def _start_capture(self):
        title = self.title_var.get()
        save_folder = self.save_folder_var.get()

        if not title:
            messagebox.showerror("エラー", "タイトルを入力してください。")
            return
        if not save_folder:
            messagebox.showerror("エラー", "保存先フォルダを選択してください。")
            return

        profile = self._get_current_profile()
        start_from_beginning = self.start_position_var.get() == "beginning"
        self._running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._log("キャプチャを開始します")

        threading.Thread(
            target=self._capture_thread,
            args=(profile, title, save_folder, start_from_beginning),
            daemon=True,
        ).start()

    def _stop_capture(self):
        self._running = False
        if self._capture_engine:
            self._capture_engine.stop()
        self._log("停止リクエスト送信...")

    def _capture_thread(self, profile, title, save_folder, start_from_beginning=False):
        root = self.winfo_toplevel()
        done_event = threading.Event()
        result = {"total_pages": 0, "save_dir": ""}

        def on_page(page, filename):
            root.after(0, lambda: self._log(f"Page {page}: {filename}"))
            root.after(0, lambda: self.status_var.set(f"キャプチャ中... Page {page}"))

        def on_status(msg):
            root.after(0, lambda: self._log(msg))
            root.after(0, lambda: self.status_var.set(msg))

        def on_complete(total, save_dir):
            result["total_pages"] = total
            result["save_dir"] = save_dir
            done_event.set()

        engine = CaptureEngine(profile, on_page, on_status, on_complete,
                               exclude_pid=os.getpid())
        self._capture_engine = engine

        hwnd = engine.find_target_window()
        if hwnd is None:
            root.after(0, lambda: self._on_capture_done(
                False, f"ウィンドウが見つかりません: {profile.window_title_keyword}"))
            return

        win_title = get_window_title(hwnd)
        win_exe = get_window_process_name(hwnd)
        root.after(0, lambda: self._log(f'検出ウィンドウ: "{win_title}" ({win_exe})'))

        engine.set_target_window(hwnd)
        engine.activate_target_window(hwnd)

        import pyautogui as pag
        rect = get_window_rect(hwnd)
        pag.moveTo((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)
        time.sleep(profile.fullscreen_wait)

        if start_from_beginning and self._running:
            root.after(0, lambda: self._log("先頭ページまで戻しています..."))
            root.after(0, lambda: self.status_var.set("先頭に戻しています..."))
            engine.rewind_to_start()
            if not self._running:
                self._capture_engine = None
                return

        engine.start(save_folder, title)

        while not done_event.is_set():
            if not self._running:
                engine.stop()
                done_event.wait(timeout=5)
                break
            done_event.wait(timeout=0.5)

        self._capture_engine = None
        save_dir = result["save_dir"]
        total = result["total_pages"]

        if total == 0:
            root.after(0, lambda: self._on_capture_done(False, "キャプチャされたページがありません"))
        else:
            # 共有状態を更新
            self.state.last_capture_folder = save_dir
            self.state.notify("capture_complete", save_dir)
            root.after(0, lambda: self._on_capture_done(
                True, f"キャプチャ完了: {total} ページ\n保存先: {save_dir}"))

    def _on_capture_done(self, success, message):
        self._running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._log(message)

        if success:
            self.status_var.set("完了")
            messagebox.showinfo("キャプチャ完了", message)
        else:
            self.status_var.set("エラー / 中断")
            messagebox.showerror("中断", message)
