# 06-platform.md — Windows/macOS プラットフォーム抽象化層

## 併せて参照するドキュメント

本プロンプトと併せて以下の docs/ ファイルを参照してください。

- `docs/developer/macos-port-notes.md`: Windows から macOS への移植時の技術的判断の詳細
- `docs/user/permissions.md`: macOS の画面収録・アクセシビリティ権限の取得手順
- `docs/developer/known-limitations.md`: 既知の制約（Retina 座標系、プロファイル未検証等）

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

既存の `core/window_utils.py` は macOS 用実装としてそのまま流用できるが、**呼び出し側を `core.platform` 抽象化レイヤーに統一するため、以下の再構成を行う**。

```
core/
├── platform/
│   ├── __init__.py       # sys.platform に応じて windows_utils / macos_utils を re-export
│   ├── windows_utils.py  # ctypes + windll による実装（新規作成）
│   └── macos_utils.py    # 既存 core/window_utils.py から移動
├── capture_engine.py     # from core.platform import ... のみを使う
```

実施手順:
1. `mkdir core/platform`
2. `core/window_utils.py` を `core/platform/macos_utils.py` に移動する。
3. 新規に `core/platform/windows_utils.py` を作成する。
4. 新規に `core/platform/__init__.py` を作成し、`sys.platform` 判定で `windows_utils` または `macos_utils` を re-export する。
5. `core/capture_engine.py`、`ui/capture_tab.py` 等の呼び出し側の import を `from core.platform import ...` に置き換える。
6. 古い `core/window_utils.py` は削除する。

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

`core/platform/windows_utils.py` を新規作成し、以下を実装する。

### 依存

- Python 標準 `ctypes`、`ctypes.wintypes`
- サードパーティ不要（pyautogui は呼び出し側が直接使用）

### ウィンドウ検索

1. `EnumWindows` でトップレベルウィンドウを列挙する。
2. 各ウィンドウに対し `IsWindowVisible` で可視ウィンドウのみ対象にする。
3. `GetWindowTextW` でタイトルを取得し、大文字小文字無視で `title_keyword` が含まれるものを候補にする。
4. タイトル部分一致の優先度（score）は以下とする（macOS 版と同一ロジック）:
   - 完全一致または末尾一致: 10
   - 先頭一致: 8
   - 単語区切り一致（空白または `-` の後）: 5
   - 単なる部分一致: 1
5. `process_name` が指定された場合:
   - `GetWindowThreadProcessId` で PID を取得し、`OpenProcess` + `QueryFullProcessImageNameW` または `GetModuleBaseNameW` で実行ファイル名を取得する。
   - 指定された `process_name`（例: `Kindle.exe`）と大文字小文字無視で一致するウィンドウが **1 件もなければ None を返す**。タイトルのみのフォールバックは禁止。
   - 一致するウィンドウが複数あれば score の高いものを返す。

### ウィンドウ矩形・前面化

- `GetWindowRect(hwnd)` で `(left, top, right, bottom)`（スクリーン座標、DPI 非対応ディスプレイでは論理ピクセル）を返す。
- `SetForegroundWindow(hwnd)` で前面化する。
  - 失敗した場合は `AttachThreadInput` トリック（フォアグラウンドウィンドウのスレッド ID と対象ウィンドウのスレッド ID を一時的にアタッチ）を試す。
  - それでも失敗する場合は一時的に `SetWindowPos(hwnd, HWND_TOPMOST, ...)` してから `HWND_NOTOPMOST` に戻すことで前面化を促す。
- `is_window_frontmost(hwnd)` は、フォアグラウンドウィンドウ（`GetForegroundWindow`）が `hwnd` と一致するかで判定する。

### 権限関数

Windows には画面収録権限・入力自動化権限の概念がないため、以下は常に `True` を返す。

```python
def has_screen_capture_access() -> bool: return True
def request_screen_capture_access() -> None: pass
def has_input_automation_access() -> bool: return True
def request_input_automation_access() -> None: pass
```

### DPI スケーリング対策

アプリ起動時（`app.py` または `main_window.py`）に以下を呼び出し、`GetWindowRect` の論理座標と `PIL.ImageGrab.grab(bbox=...)` の座標系を一致させる。

```python
import ctypes
ctypes.windll.user32.SetProcessDPIAware()
```

## マルチディスプレイ環境

マルチディスプレイ環境では `PIL.ImageGrab.grab(bbox=..., all_screens=True)` を必ず指定する。指定しないと PIL はプライマリモニタしか取得せず、セカンドモニタ上のウィンドウが真っ黒画像になる。

ただし、マルチディスプレイ環境でのキャプチャ精度は **未検証** である。基本動作は `all_screens=True` で担保するが、実際の電子書籍アプリを使った検証は `docs/developer/verification-log.md` の対象外となっている。

## macOS 実装（macos_utils.py）

- 既存 `core/window_utils.py` の内容を `core/platform/macos_utils.py` に移動する。
- 以下の関数名を `06-platform.md` の共通インターフェースに合わせて変更する。
  - `has_screen_recording_access` → `has_screen_capture_access`
  - `request_screen_recording_access` → `request_screen_capture_access`
  - `has_accessibility_access` → `has_input_automation_access`
  - `request_accessibility_access` → `request_input_automation_access`

- ウィンドウ列挙: `Quartz.CGWindowListCopyWindowInfo`（`kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements`）
- ウィンドウ矩形: `kCGWindowBounds`（**ポイント単位**。Retina でも物理ピクセルではない点に注意）
- ウィンドウ前面化: `NSRunningApplication.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)`。クリック操作は行わない（信号機ボタンの誤操作を防ぐため）
- 前面化後、`NSWorkspace.sharedWorkspace().frontmostApplication()` で実際に切り替わったか確認し、未反映なら短いポーリングでリトライ
- 画面収録権限: `Quartz.CGPreflightScreenCaptureAccess()` / `CGRequestScreenCaptureAccess()`
- 入力自動化権限: `ApplicationServices.AXIsProcessTrusted()` / `AXIsProcessTrustedWithOptions()`（`pyobjc-framework-ApplicationServices` の追加インストールが必要）

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
- `core/window_utils.py` が存在せず、すべて `core/platform/` 配下に集約されている
