"""macOS ウィンドウユーティリティ

ウィンドウの検索・活性化、ダイアログ表示など macOS 固有の操作を提供する。
core.win32_utils (Windows版) と同じ関数シグネチャを維持した macOS 版。

window handle (hwnd) には CGWindowID (int) を用いる。

前提:
- ウィンドウタイトル・一覧の取得には「画面収録」権限が必要
  (システム設定 > プライバシーとセキュリティ > 画面収録 で
  ターミナル / Python / このアプリを許可する)
- キー送信・クリックの自動操作 (pyautogui) には「アクセシビリティ」権限が必要
"""

import datetime
import time
from tkinter import simpledialog

import pyautogui as pag
import Quartz
from AppKit import NSApplicationActivateIgnoringOtherApps, NSRunningApplication, NSWorkspace

pag.FAILSAFE = False


def has_screen_recording_access():
    """画面収録権限が付与されているか判定する。"""
    try:
        return bool(Quartz.CGPreflightScreenCaptureAccess())
    except AttributeError:
        # 古い pyobjc/Quartz には無いことがあるため、その場合は判定不能として True 扱い
        return True


def request_screen_recording_access():
    """画面収録権限の許可ダイアログを表示させる (未許可時に一度だけ有効)。"""
    try:
        Quartz.CGRequestScreenCaptureAccess()
    except AttributeError:
        pass


def has_accessibility_access():
    """アクセシビリティ権限 (合成キー入力・クリックの送信に必要) が付与されているか判定する。

    権限が無いと pyautogui の keyDown/keyUp や click は例外を出さずに
    黙って何も起こさない。ページめくりキーが効かず同じページを撮り続ける
    不具合の典型的な原因になるため、キャプチャ開始前に必ず確認する。
    """
    try:
        from ApplicationServices import AXIsProcessTrusted
        return bool(AXIsProcessTrusted())
    except ImportError:
        return True


def request_accessibility_access():
    """アクセシビリティ権限の許可ダイアログを表示させる。"""
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions
        AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": True})
    except ImportError:
        pass


def _list_windows():
    """オンスクリーンの通常ウィンドウ一覧を返す (CGWindowListCopyWindowInfo の生データ)。"""
    options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
    info = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
    return info or []


def _normalize_process_name(name):
    """プロセス名比較用に正規化する（小文字化のみ）。"""
    if not name:
        return ""
    return name.strip().lower()


def find_window(title_keyword, exclude_pid=None, process_name=None):
    """指定キーワードを含むウィンドウタイトルの CGWindowID を返す。見つからなければ None。

    Args:
        title_keyword: ウィンドウタイトルに含まれるキーワード (大文字小文字を区別しない)
        exclude_pid: 除外するプロセスID (自アプリのウィンドウを除外するために使用)
        process_name: アプリ名フィルタ (例: "Kindle" や "Kindle.exe")。指定されている場合、
            このオーナー名を持つウィンドウが1つも見つからなければ None を返す
            (タイトルのみでの誤検出を防ぐため、フォールバックしない)。
    """
    keyword_lower = title_keyword.lower()
    proc_target = _normalize_process_name(process_name)

    all_candidates = []   # (score, window_id, title, owner_name)
    proc_candidates = []  # all_candidates のうち owner_name が process_name と一致するもの

    for win in _list_windows():
        layer = win.get("kCGWindowLayer", 0)
        if layer != 0:
            continue  # メニューバーやドックなど通常ウィンドウ以外を除外

        pid = win.get("kCGWindowOwnerPID")
        if exclude_pid is not None and pid == exclude_pid:
            continue

        title = win.get("kCGWindowName", "") or ""
        if not title:
            continue
        title_lower = title.lower()
        if keyword_lower not in title_lower:
            continue

        # スコアリング: 完全一致・末尾一致を優先 (Windows版と同じ方針)
        score = 1
        if title_lower.endswith(keyword_lower) or title_lower == keyword_lower:
            score = 10
        elif title_lower.startswith(keyword_lower):
            score = 8
        elif f" {keyword_lower}" in title_lower or f"- {keyword_lower}" in title_lower:
            score = 5

        owner_name = win.get("kCGWindowOwnerName", "") or ""
        window_id = win.get("kCGWindowNumber")
        entry = (score, window_id, title, owner_name)
        all_candidates.append(entry)
        if proc_target and _normalize_process_name(owner_name) == proc_target:
            proc_candidates.append(entry)

    # プロセス名が指定されている場合は、そのプロセスのウィンドウに限定して探す。
    # タイトルだけが偶然一致する無関係なウィンドウ (例: ターミナルの作業フォルダ名) を
    # 誤って掴んでしまうのを避けるため、ここではタイトルのみでのフォールバックはしない。
    if proc_target:
        if not proc_candidates:
            return None
        proc_candidates.sort(key=lambda x: x[0], reverse=True)
        return proc_candidates[0][1]

    if not all_candidates:
        return None

    all_candidates.sort(key=lambda x: x[0], reverse=True)
    return all_candidates[0][1]


def _find_window_info(window_id):
    """window_id に対応する CGWindowList の情報 dict を返す。見つからなければ None。"""
    info = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionIncludingWindow, window_id
    )
    if not info:
        return None
    return info[0]


def get_window_title(hwnd):
    """ウィンドウハンドルからタイトルを取得する。"""
    info = _find_window_info(hwnd)
    if not info:
        return ""
    return info.get("kCGWindowName", "") or ""


def get_window_rect(hwnd):
    """ウィンドウの矩形座標 (left, top, right, bottom) を返す。"""
    info = _find_window_info(hwnd)
    if not info:
        return (0, 0, 0, 0)
    bounds = info.get("kCGWindowBounds", {})
    left = int(bounds.get("X", 0))
    top = int(bounds.get("Y", 0))
    width = int(bounds.get("Width", 0))
    height = int(bounds.get("Height", 0))
    return (left, top, left + width, top + height)


def get_window_process_name(hwnd):
    """ウィンドウハンドルからオーナーアプリ名を取得する。"""
    info = _find_window_info(hwnd)
    if not info:
        return ""
    return info.get("kCGWindowOwnerName", "") or ""


def activate_window(hwnd, click_position='center', use_bring_to_top=False):
    """ウィンドウを前面 (フォアグラウンド) に出す。

    macOS には Windows の SetForegroundWindow に相当する「特定ウィンドウ単体」の
    前面化APIが無いため、ウィンドウを所有するアプリ全体をアクティブ化する。

    Windows版はキーボードフォーカスを確実に対象アプリへ移すためにクリックしていたが、
    macOS では activateWithOptions_ だけでキーボードイベントの送信先が対象アプリに
    切り替わるため、ウィンドウ内をクリックする必要はない。むしろクリック位置が
    ウィンドウ左上の信号機ボタン (閉じる/しまう/フルスクリーン) に重なると、
    誤操作でウィンドウが閉じたり独立 Space のフルスクリーンに切り替わってしまい
    (実際に発生した不具合)、以後ウィンドウを検出できなくなる。そのため
    click_position はカーソル移動先の参考程度に留め、クリックは行わない。
    """
    info = _find_window_info(hwnd)
    pid = info.get("kCGWindowOwnerPID") if info else None

    if pid is not None:
        running_app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
        if running_app is not None:
            running_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

        # アクティブ化が実際に反映されるまで少し待って確認する。
        # うまく前面化できていない場合は再試行し、対象と異なるアプリの
        # 画面をそのままキャプチャしてしまう事態を防ぐ。
        for _ in range(10):
            time.sleep(0.2)
            frontmost = NSWorkspace.sharedWorkspace().frontmostApplication()
            if frontmost is not None and frontmost.processIdentifier() == pid:
                break
        else:
            if running_app is not None:
                running_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                time.sleep(0.5)

    rect = get_window_rect(hwnd)
    if click_position == 'center':
        x = rect[0] + (rect[2] - rect[0]) // 2
        y = rect[1] + (rect[3] - rect[1]) // 2
    else:
        x = rect[0] + 100
        y = rect[1] + 60

    pag.moveTo(x, y)
    time.sleep(0.5)


def is_window_frontmost(hwnd):
    """対象ウィンドウのオーナーアプリが現在最前面かどうかを返す。"""
    info = _find_window_info(hwnd)
    if not info:
        return False
    pid = info.get("kCGWindowOwnerPID")
    frontmost = NSWorkspace.sharedWorkspace().frontmostApplication()
    return frontmost is not None and pid is not None and frontmost.processIdentifier() == pid


def get_title():
    """タイトル入力ダイアログを表示する。空白の場合は現在の時刻を返す。"""
    default_title = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    tt = simpledialog.askstring('タイトルを入力', 'タイトルを入力して下さい(空白の場合現在の時刻)')
    # キャンセル時は None、空入力時は '' が返る。どちらも現在時刻にフォールバックする。
    return tt if tt else default_title
