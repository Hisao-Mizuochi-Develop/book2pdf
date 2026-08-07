# 06-platform.md — Windows/macOS プラットフォーム抽象化層

## ゴール

`core/platform/` 配下に Windows/macOS 共通のウィンドウ操作・権限確認 API を実装する。呼び出し側は OS を意識せずに使えるようにする。

## ファイル構成

```
core/platform/
├── __init__.py       # sys.platform に応じて re-export
├── windows_utils.py  # ctypes + windll 実装
└── macos_utils.py    # pyobjc (Quartz/Cocoa/ApplicationServices) 実装
```

## 共通インターフェース

`core/platform/__init__.py` は以下の関数を共通シグネチャで提供する。

```python
from typing import Any

WindowHandle = Any


def find_window(
    title_keyword: str,
    exclude_pid: int | None = None,
    process_name: str | None = None,
) -> WindowHandle | None:
    """タイトル部分一致でウィンドウを検索する。

    process_name が指定された場合、そのプロセス名のウィンドウが 1 件も
    見つからなければ None を返すこと。タイトルのみのフォールバックは禁止。
    """


def get_window_title(hwnd: WindowHandle) -> str: ...
def get_window_rect(hwnd: WindowHandle) -> tuple[int, int, int, int]: ...  # (left, top, right, bottom)
def get_window_process_name(hwnd: WindowHandle) -> str: ...


def activate_window(
    hwnd: WindowHandle,
    click_position: str = "center",
    use_bring_to_top: bool = False,
) -> None:
    """ウィンドウを前面化する。

    クリック操作を伴う場合、OS 標準のウィンドウ制御 UI（macOS の信号機ボタン等）
    に重ならない座標を使うこと。可能なら前面化 API のみで完結させる。
    """


def is_window_frontmost(hwnd: WindowHandle) -> bool: ...


def has_screen_capture_access() -> bool: ...
def request_screen_capture_access() -> None: ...
def has_input_automation_access() -> bool: ...
def request_input_automation_access() -> None: ...
```

## Windows 実装（windows_utils.py）

- `ctypes.windll.user32` の `EnumWindows`, `GetWindowTextW`, `GetWindowRect`, `SetForegroundWindow` 等を使用
- `SetForegroundWindow` が確実でないケースに備え、`AttachThreadInput` トリックや `HWND_TOPMOST` / `HWND_NOTOPMOST` の一時切り替えでフォールバックしてよい
- 画面収録・入力自動化の権限は概念自体が無いため、`has_*_access()` は常に `True` を返す
- DPI スケーリング対策として、アプリ起動時に `windll.user32.SetProcessDPIAware()` を呼ぶ

## macOS 実装（macos_utils.py）

- ウィンドウ列挙: `Quartz.CGWindowListCopyWindowInfo`（`kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements`）
- ウィンドウ矩形: `kCGWindowBounds`（ポイント単位）
- ウィンドウ前面化: `NSRunningApplication.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)`。クリック操作は行わない
- 前面化後、`NSWorkspace.sharedWorkspace().frontmostApplication()` で実際に切り替わったか確認し、未反映なら短いポーリングでリトライ
- 画面収録権限: `Quartz.CGPreflightScreenCaptureAccess()` / `CGRequestScreenCaptureAccess()`
- アクセシビリティ権限: `ApplicationServices.AXIsProcessTrusted()` / `AXIsProcessTrustedWithOptions()`

## スクリーンショット座標系

`PIL.ImageGrab.grab(bbox=..., all_screens=True)` を両 OS で共通使用する。macOS では `bbox` にポイント座標をそのまま渡す。追加のスケール変換は不要。

マルチモニタ環境では `all_screens=True` を必ず指定する。

## 完了条件

- `core/platform/` の各関数が両 OS で同じシグネチャを持つ
- 以下のワンショットスクリプトが実機で動作する

```python
from core.platform import find_window, get_window_rect, activate_window, is_window_frontmost

hwnd = find_window("kindle", process_name="Kindle.exe")  # Windows 例
# hwnd = find_window("kindle", process_name="Kindle")    # macOS 例
assert hwnd is not None
rect = get_window_rect(hwnd)
print("rect:", rect)
activate_window(hwnd)
assert is_window_frontmost(hwnd)
```

- 対象アプリが起動していない状態で `find_window(..., process_name=...)` は `None` を返す
- `activate_window()` 実行後、対象ウィンドウがフルスクリーン化・最小化・閉じていない
- `get_window_rect()` の座標をそのまま `ImageGrab.grab(bbox=...)` に渡すと、対象ウィンドウの中身が写る
