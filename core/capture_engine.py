"""キャプチャエンジン

プロファイルの設定に基づいて、任意の電子書籍アプリのページを自動キャプチャする。
"""

import os
import threading
import time

import cv2
import numpy as np
import pyautogui as pag
from PIL import ImageGrab

from .boundary_detector import create_detector
from .window_utils import (
    activate_window,
    find_window,
    get_window_rect,
    has_accessibility_access,
    has_screen_recording_access,
    is_window_frontmost,
    request_accessibility_access,
    request_screen_recording_access,
)

pag.FAILSAFE = False

# 変化とみなす最小しきい値。カーソルの点滅やホバー時のハイライトなど、ごく一部の
# ピクセルだけが変わるノイズを「ページが変わった」と誤検出しないようにする。
_CHANGE_PIXEL_THRESHOLD = 20   # 各ピクセルの輝度差がこれを超えたら「変化」とみなす
_CHANGE_MIN_RATIO = 0.005      # 「変化」ピクセルが全体のこの割合を超えたら実際のページ変化とみなす


def _has_meaningful_change(old, new):
    """ノイズを除いた実質的な画面変化があるかどうかを判定する。"""
    if old.shape != new.shape:
        return True
    diff = cv2.absdiff(old, new)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    changed_ratio = np.count_nonzero(gray > _CHANGE_PIXEL_THRESHOLD) / gray.size
    return changed_ratio > _CHANGE_MIN_RATIO


def _imwrite_unicode(filepath, image):
    """cv2.imwrite の Unicode パス対応版。保存成功なら True を返す。

    Windows ではアンチウイルスや同期ソフトが一時的にファイルをロックすると
    numpy.tofile が "N requested and 0 written" の OSError を送出する。
    呼び出し側でリトライできるよう例外を握り潰して False を返す。
    """
    ext = os.path.splitext(filepath)[1]
    try:
        success, buf = cv2.imencode(ext, image)
        if not success:
            return False
        # 一時ファイル経由で書き出してから rename するとロック競合に強い
        tmp_path = filepath + ".tmp"
        buf.tofile(tmp_path)
        if os.path.exists(filepath):
            os.remove(filepath)
        os.rename(tmp_path, filepath)
        return True
    except OSError:
        try:
            if os.path.exists(filepath + ".tmp"):
                os.remove(filepath + ".tmp")
        except OSError:
            pass
        return False


class CaptureEngine:
    """ページ自動キャプチャエンジン"""

    def __init__(self, profile, on_page_captured=None, on_status=None, on_complete=None,
                 exclude_pid=None):
        """
        Args:
            profile: CaptureProfile インスタンス
            on_page_captured: ページキャプチャ時のコールバック (page_num, filename)
            on_status: ステータス更新時のコールバック (message)
            on_complete: 完了時のコールバック (total_pages, save_dir)
            exclude_pid: ウィンドウ検索時に除外するプロセスID (自アプリ除外用)
        """
        self.profile = profile
        self._on_page = on_page_captured or (lambda *a: None)
        self._on_status = on_status or (lambda *a: None)
        self._on_complete = on_complete or (lambda *a: None)
        self._running = False
        self._running_rewind = False
        self._thread = None
        self._exclude_pid = exclude_pid
        self._target_hwnd = None
        self._target_rect = None  # (left, top, right, bottom)

    def set_target_window(self, hwnd):
        """キャプチャ対象ウィンドウを設定する。"""
        self._target_hwnd = hwnd
        self._target_rect = get_window_rect(hwnd)

    def _grab(self):
        """画面をキャプチャして BGR numpy 配列を返す。対象ウィンドウ設定時はその領域のみ。"""
        bbox = self._target_rect if self._target_rect else None
        # all_screens=True がないと PIL はプライマリモニタしか取得せず、
        # セカンドモニタ上のウィンドウ (bbox が x>=プライマリ幅 など) は
        # 範囲外となり真っ黒画像になる。境界検出が全行で失敗する原因。
        img = ImageGrab.grab(bbox=bbox, all_screens=True)
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    def _page_turn_methods(self):
        """ページめくりに試す方式を優先順に返す。

        プロファイル指定のキー (通常 "right") がまず効くはずだが、電子書籍
        アプリの表示モードによっては反応しないことがある
        (例: ページめくり表示ではなく連続スクロール表示になっている場合)。
        その場合に備えて、スペースキー・PageDown・下スクロールへ自動的に
        フォールバックする。
        """
        methods = [self.profile.page_turn_key]
        for candidate in ("space", "pagedown", "down", "scroll"):
            if candidate not in methods:
                methods.append(candidate)
        return methods

    def _send_page_turn(self, method):
        """指定方式でページめくり操作を送信する。"""
        if method == "scroll":
            rect = self._target_rect
            if rect:
                cx = (rect[0] + rect[2]) // 2
                cy = (rect[1] + rect[3]) // 2
                pag.moveTo(cx, cy)
            pag.scroll(-600)
        else:
            pag.keyDown(method)
            pag.keyUp(method)

    _REVERSE_KEY_MAP = {
        "right": "left", "left": "right",
        "down": "up", "up": "down",
        "pagedown": "pageup", "pageup": "pagedown",
    }

    def _send_page_turn_reverse(self, method):
        """_send_page_turn() の逆方向 (前のページに戻る) 操作を送信する。"""
        if method == "scroll":
            rect = self._target_rect
            if rect:
                cx = (rect[0] + rect[2]) // 2
                cy = (rect[1] + rect[3]) // 2
                pag.moveTo(cx, cy)
            pag.scroll(600)
        elif method == "space":
            # Kindle 等の多くのビューアで Shift+Space は「前のページ」に対応する
            pag.keyDown("shift")
            pag.keyDown("space")
            pag.keyUp("space")
            pag.keyUp("shift")
        else:
            pag.keyDown(self._REVERSE_KEY_MAP.get(method, method))
            pag.keyUp(self._REVERSE_KEY_MAP.get(method, method))

    def rewind_to_start(self, max_attempts=500):
        """現在のページから本の先頭まで、ページを逆方向にめくり続ける。

        「先頭からキャプチャ」モード用。ページ送りと同じ変化検出ロジックを
        逆方向に使い、これ以上戻れなくなった時点（=先頭に到達）で停止する。
        本の長さに上限が無いため、暴走を避ける安全弁として max_attempts を設ける。

        Returns:
            戻したページ数 (int)。
        """
        method = self.profile.page_turn_key
        old = self._grab()
        moved = 0
        stall_count = 0
        self._running_rewind = True

        for _ in range(max_attempts):
            if not self._running_rewind:
                break
            if self._target_hwnd is not None and not is_window_frontmost(self._target_hwnd):
                self._on_status(
                    "エラー: 対象ウィンドウが最前面ではなくなったため、先頭に戻す処理を中断しました。"
                )
                break
            self._send_page_turn_reverse(method)
            time.sleep(self.profile.page_wait)
            try:
                current = self._grab()
            except Exception:
                break

            if _has_meaningful_change(old, current):
                moved += 1
                old = current
                stall_count = 0
                if moved % 10 == 0:
                    self._on_status(f"先頭に戻しています... ({moved}ページ)")
            else:
                stall_count += 1
                # 1回の無変化だけでは判定せず、念のためもう一度だけ確認する
                if stall_count >= 2:
                    break

        self._on_status(f"先頭まで戻しました（{moved}ページ戻りました）" if moved
                         else "すでに先頭付近です")
        return moved

    def find_target_window(self):
        """プロファイルのキーワードでウィンドウを検索する。"""
        return find_window(
            self.profile.window_title_keyword,
            exclude_pid=self._exclude_pid,
            process_name=self.profile.process_name or None,
        )

    def activate_target_window(self, hwnd):
        """対象ウィンドウを前面に出す。"""
        activate_window(
            hwnd,
            click_position=self.profile.click_position,
            use_bring_to_top=self.profile.use_bring_to_top,
        )

    def detect_boundaries(self, image=None):
        """画面をキャプチャして境界を検出する。

        Args:
            image: BGR 画像（None の場合は画面をキャプチャ）

        Returns:
            (left, right) のタプル
        """
        if image is None:
            image = self._grab()

        detector = create_detector(
            self.profile.boundary_method,
            manual_left=self.profile.manual_left,
            manual_right=self.profile.manual_right,
        )
        return detector.detect(image)

    def set_manual_boundaries(self, left, right):
        """手動で境界を設定する。プロファイルの境界検出方式を manual に変更する。"""
        self.profile.boundary_method = "manual"
        self.profile.manual_left = left
        self.profile.manual_right = right

    def capture_preview(self):
        """現在の画面のプレビュー画像と検出境界を返す。

        Returns:
            (image_bgr, left, right) のタプル。エラー時は (None, 0, 0)
        """
        try:
            image = self._grab()
            left, right = self.detect_boundaries(image)
            return image, left, right
        except Exception:
            return None, 0, 0

    def start(self, save_folder, title):
        """別スレッドでキャプチャを開始する。"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop, args=(save_folder, title), daemon=True
        )
        self._thread.start()

    def stop(self):
        """キャプチャを停止する。"""
        self._running = False
        self._running_rewind = False

    def is_running(self):
        return self._running

    def _capture_loop(self, save_folder, title):
        """メインのキャプチャループ"""
        save_dir = os.path.join(save_folder, title)
        os.makedirs(save_dir, exist_ok=True)

        try:
            # 画面収録権限チェック — 権限がないと screencapture がデスクトップの
            # 壁紙だけを返し、ウィンドウの中身が写らないまま無警告で進んでしまう。
            if not has_screen_recording_access():
                request_screen_recording_access()
                self._on_status(
                    "エラー: 画面収録の権限がありません。"
                    "システム設定 > プライバシーとセキュリティ > 画面収録 で、"
                    "このアプリ（またはターミナル）を許可してから再実行してください。"
                )
                self._on_complete(0, save_dir)
                self._running = False
                return

            # アクセシビリティ権限チェック — 権限がないとページめくりキー送信や
            # クリックが例外を出さずに黙って無効化され、ページが変わらないまま
            # 同じ1ページ目を撮り続ける不具合の典型的な原因になる。
            if not has_accessibility_access():
                request_accessibility_access()
                self._on_status(
                    "エラー: アクセシビリティの権限がありません。"
                    "システム設定 > プライバシーとセキュリティ > アクセシビリティ で、"
                    "このアプリ（またはターミナル）を許可してから再実行してください。"
                )
                self._on_complete(0, save_dir)
                self._running = False
                return

            # 対象ウィンドウが実際に最前面にあるか確認する。
            # 前面化が失敗していると、Kindle ではなく手前にある別ウィンドウや
            # デスクトップをそのままキャプチャしてしまう。
            if self._target_hwnd is not None and not is_window_frontmost(self._target_hwnd):
                self._on_status(
                    "エラー: 対象ウィンドウを前面にできませんでした。"
                    "電子書籍アプリを最前面に表示してから再実行してください。"
                )
                self._on_complete(0, save_dir)
                self._running = False
                return

            # 境界検出
            self._on_status("境界を検出中...")
            image = self._grab()
            lft, rht = self.detect_boundaries(image)

            if lft is None or rht is None:
                self._on_status("エラー: 境界を検出できませんでした")
                self._on_complete(0, save_dir)
                self._running = False
                return

            self._on_status(f"境界検出完了: left={lft}, right={rht}")

            # キャプチャ開始 — 実際の画像サイズから old 配列を初期化
            img_h = image.shape[0]
            old = np.zeros((img_h, rht - lft, 3), np.uint8)
            page = 1

            # ページめくり方式の候補。プロファイル指定のキーが効かない場合
            # (例: ページめくり表示ではなく連続スクロール表示になっている場合)、
            # 自動的に次の方式へエスカレーションする。一度有効な方式が見つかったら
            # 以降のページもその方式を使い続ける。
            turn_methods = self._page_turn_methods()
            active_turn_idx = 0

            while self._running:
                if self._target_hwnd is not None and not is_window_frontmost(self._target_hwnd):
                    self._on_status(
                        "エラー: 対象ウィンドウが最前面ではなくなったため停止しました。"
                        "キャプチャ中は他のウィンドウを操作しないでください。"
                    )
                    self._on_complete(page - 1, save_dir)
                    self._running = False
                    return

                filename = f"{page:03d}.png"
                filepath = os.path.join(save_dir, filename)
                start = time.perf_counter()
                exception_retries = 0
                escalations = 0

                # ページ変化を待つ (ノイズを除いた実質的な変化のみを「変化」とみなす)
                page_changed = False
                while self._running:
                    time.sleep(self.profile.page_wait)

                    try:
                        ss = self._grab()
                        ss = ss[:, lft:rht]

                        if _has_meaningful_change(old, ss):
                            page_changed = True
                            break

                        if time.perf_counter() - start > self.profile.timeout_seconds:
                            if escalations < len(turn_methods) - 1:
                                # このページめくり方式では変化しなかった。次の方式を試す。
                                escalations += 1
                                active_turn_idx = escalations
                                self._on_status(
                                    "ページが変化しないため別のページめくり方式"
                                    f"（{turn_methods[active_turn_idx]}）を試します..."
                                )
                                self._send_page_turn(turn_methods[active_turn_idx])
                                start = time.perf_counter()
                                continue
                            # 全方式を試しても変化なし → 最終ページに到達
                            self._on_status(f"キャプチャ完了: {page - 1} ページ")
                            self._on_complete(page - 1, save_dir)
                            self._running = False
                            return
                    except Exception as e:
                        exception_retries += 1
                        if exception_retries >= self.profile.max_retries:
                            self._on_status(f"エラー: {e}")
                            self._on_complete(page - 1, save_dir)
                            self._running = False
                            return
                        continue

                if not page_changed:
                    break

                # 保存（一時的な書き込み失敗をリトライ）
                saved = False
                for attempt in range(1, self.profile.max_retries + 1):
                    if _imwrite_unicode(filepath, ss):
                        saved = True
                        break
                    self._on_status(
                        f"保存失敗 ({attempt}/{self.profile.max_retries}) - 0.5秒後にリトライ: {filename}"
                    )
                    time.sleep(0.5 * attempt)
                if not saved:
                    self._on_status(f"エラー: 保存に失敗しました（リトライ上限）: {filepath}")
                    self._on_complete(page - 1, save_dir)
                    self._running = False
                    return
                old = ss
                elapsed = time.perf_counter() - start
                self._on_page(page, filename)
                self._on_status(f"Page {page} ({elapsed:.2f}秒)")

                page += 1

                # ページめくり (これまでのエスカレーションで確立した方式を使う)
                self._send_page_turn(turn_methods[active_turn_idx])
                time.sleep(0.1)

        except Exception as e:
            self._on_status(f"エラー: {e}")

        total = page - 1
        self._on_complete(total, save_dir)
        self._running = False
