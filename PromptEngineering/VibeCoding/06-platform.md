# 06-platform.md — Windows/macOS プラットフォーム抽象化層

## ゴール

`core/platform/` 配下に Windows/macOS 共通のウィンドウ操作・権限確認 API を実装する。呼び出し側は OS を意識せずに使えるようにする。

## 設計方針

book2pdf は Windows と macOS の両方で動作しなければならない。「まず Windows で作り、後で macOS 対応する」進め方は禁止する。最初から以下の抽象化を前提に設計・実装すること。

```
core/
├── platform/
│   ├── __init__.py       # sys.platform に応じて windows_utils / macos_utils を re-export
│   ├── windows_utils.py  # ctypes + windll による実装
│   └── macos_utils.py    # pyobjc (Quartz/AppKit) による実装
├── capture_engine.py     # platform/ の関数だけを使う。OS 分岐を書かない
```

`core/capture_engine.py` や `ui/capture_tab.py` など呼び出し側は、**OS 判定コードを一切含まない**こと。`core/platform/__init__.py` が `sys.platform` を見て適切なモジュールをインポートし、共通のシグネチャで関数群を提供する。

## ファイル構成

```
core/platform/
├── __init__.py       # sys.platform に応じて re-export
├── windows_utils.py  # ctypes + windll 実装
└── macos_utils.py    # pyobjc (Quartz/Cocoa/ApplicationServices) 実装
```

## 共通インターフェース仕様

`core/platform/__init__.py` は以下の関数を同一シグネチャ・同一意味論で提供する。

`WindowHandle` は OS ごとに異なる型でよい（Windows は `HWND` 整数、macOS は `CGWindowID` 整数）。呼び出し側は不透明な値として扱い、中身を解釈しない。

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
- DPI スケーリング対策として、アプリ起動時に `windll.user32.SetProcessDPIAware()` を呼ぶこと（`GetWindowRect` とスクリーンショットの座標系を一致させるため）

## macOS 実装（macos_utils.py）

- ウィンドウ列挙: `Quartz.CGWindowListCopyWindowInfo`（`kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements`）
- ウィンドウ矩形: `kCGWindowBounds`（**ポイント単位**。Retina でも物理ピクセルではない点に注意）
- ウィンドウ前面化: `NSRunningApplication.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)`。クリック操作は行わない（信号機ボタンの誤操作を防ぐため）
- 前面化後、`NSWorkspace.sharedWorkspace().frontmostApplication()` で実際に切り替わったか確認し、未反映なら短いポーリングでリトライ
- 画面収録権限: `Quartz.CGPreflightScreenCaptureAccess()` / `CGRequestScreenCaptureAccess()`
- アクセシビリティ権限: `ApplicationServices.AXIsProcessTrusted()` / `AXIsProcessTrustedWithOptions()`（`pyobjc-framework-ApplicationServices` の追加インストールが必要）

## スクリーンショット座標系

`PIL.ImageGrab.grab(bbox=..., all_screens=True)` を両 OS で共通使用する。macOS では `bbox` にポイント座標をそのまま渡す。追加のスケール変換は不要（`ImageGrab.grab` は macOS 上で `screencapture` コマンドを内部利用しており、bbox 指定時はその値がそのまま出力ピクセル数になる。全画面取得（`bbox=None`）時のみ Retina の物理解像度になる、という非対称な挙動があるため、実装前に `ImageGrab.grab(bbox=(0,0,400,300))` の出力サイズを確認するテストを書くこと）。

マルチモニタ環境では `all_screens=True` を必ず指定する（指定しないと PIL はプライマリモニタしか取得せず、セカンドモニタ上のウィンドウが真っ黒画像になる）。

## キー送信・クリック

`pyautogui` は両 OS 共通で使えるため、抽象化レイヤーに含めなくてよい。ただし以下の点に注意する。

- macOS では `pyautogui` の内部実装が Quartz イベントを使うため、アクセシビリティ権限が無いと**例外を出さずに黙って失敗する**。必ず事前に権限チェックを行い、失敗時にサイレントに進行しないこと
- ページめくりキーは `right` を既定としつつ、`07-capture.md` のエスカレーション仕様（space→pagedown→down→scroll）を両 OS で共通実装する

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
