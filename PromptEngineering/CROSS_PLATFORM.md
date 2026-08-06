# CROSS_PLATFORM.md — Windows/macOS抽象化レイヤー設計

book2pdf は Windows と macOS の両方で動作しなければならない。
「まずWindowsで作り、後でmacOS対応する」進め方は禁止する。最初から
以下の抽象化を前提に設計・実装すること。

## 設計方針

```
core/
├── platform/
│   ├── __init__.py       # sys.platform に応じて windows_utils / macos_utils を re-export
│   ├── windows_utils.py  # ctypes + windll による実装
│   └── macos_utils.py    # pyobjc (Quartz/AppKit) による実装
├── capture_engine.py     # platform/ の関数だけを使う。OS分岐を書かない
```

`core/capture_engine.py` や `ui/capture_tab.py` など呼び出し側は、
**OS判定コードを一切含まない**こと。`core/platform/__init__.py` が
`sys.platform` を見て適切なモジュールをインポートし、共通のシグネチャで
以下の関数群を提供する。

## 共通インターフェース仕様

両OS実装で、以下の関数を同一シグネチャ・同一意味論で提供すること。

```python
def find_window(title_keyword: str, exclude_pid: int | None = None,
                 process_name: str | None = None) -> WindowHandle | None:
    """タイトル部分一致でウィンドウを検索する。

    process_name が指定された場合、そのプロセスのウィンドウが1件も
    見つからなければ None を返すこと（タイトルのみのフォールバックは禁止。
    理由は PITFALLS.md の「ウィンドウ誤検出」を参照）。
    """

def get_window_title(hwnd: WindowHandle) -> str: ...
def get_window_rect(hwnd: WindowHandle) -> tuple[int, int, int, int]: ...  # (left, top, right, bottom)
def get_window_process_name(hwnd: WindowHandle) -> str: ...

def activate_window(hwnd: WindowHandle, click_position: str = "center",
                     use_bring_to_top: bool = False) -> None:
    """ウィンドウを前面化する。

    実装がクリック操作を伴う場合、OS標準のウィンドウ制御UI
    （macOSの信号機ボタン等）に絶対に重ならない座標を使うこと。
    可能なら前面化APIのみで完結させ、クリックを行わない実装を優先する
    （詳細は PITFALLS.md）。
    """

def is_window_frontmost(hwnd: WindowHandle) -> bool: ...

def get_title() -> str:
    """タイトル入力ダイアログ（tkinter simpledialog等、OS非依存の実装でよい）"""

# OS依存の権限確認（Windowsは常にTrueを返してよい）
def has_screen_capture_access() -> bool: ...
def request_screen_capture_access() -> None: ...
def has_input_automation_access() -> bool: ...
def request_input_automation_access() -> None: ...
```

`WindowHandle` はOSごとに異なる型でよい（Windowsは `HWND` 整数、macOSは
`CGWindowID` 整数）。呼び出し側は不透明な値として扱い、中身を解釈しない。

## Windows実装（windows_utils.py）

- `ctypes.windll.user32` の `EnumWindows`, `GetWindowTextW`, `GetWindowRect`,
  `SetForegroundWindow` 等を使用
- `SetForegroundWindow` が確実でないケースに備え、`AttachThreadInput` トリックや
  `HWND_TOPMOST`/`HWND_NOTOPMOST` の一時切り替えでフォールバックしてよい
- 画面収録・入力自動化の権限は概念自体が無いため、`has_*_access()` は
  常に `True` を返してよい
- DPIスケーリング対策として、アプリ起動時に
  `windll.user32.SetProcessDPIAware()` を呼ぶこと（`GetWindowRect` と
  スクリーンショットの座標系を一致させるため）

## macOS実装（macos_utils.py）

- ウィンドウ列挙: `Quartz.CGWindowListCopyWindowInfo`
  （`kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements`）
- ウィンドウ矩形: `kCGWindowBounds`（**ポイント単位**。Retinaでも物理ピクセル
  ではない点に注意）
- ウィンドウ前面化: `NSRunningApplication.activateWithOptions_
  (NSApplicationActivateIgnoringOtherApps)`。**クリック操作は行わないこと**
  （信号機ボタンの誤操作を防ぐため。PITFALLS.md参照）
- 前面化後、`NSWorkspace.sharedWorkspace().frontmostApplication()` で
  実際に切り替わったかを確認し、未反映なら短いポーリングでリトライすること
- 画面収録権限: `Quartz.CGPreflightScreenCaptureAccess()` /
  `CGRequestScreenCaptureAccess()`
- アクセシビリティ権限: `ApplicationServices.AXIsProcessTrusted()` /
  `AXIsProcessTrustedWithOptions()`（`pyobjc-framework-ApplicationServices`
  の追加インストールが必要）

## スクリーンショット取得の注意（座標系）

`PIL.ImageGrab.grab(bbox=..., all_screens=True)` を両OSで共通使用してよいが、
**macOSでは `bbox` にポイント座標をそのまま渡すこと。** 追加のスケール変換は
不要（`ImageGrab.grab` はmacOS上で `screencapture` コマンドを内部利用しており、
bbox指定時はその値がそのまま出力ピクセル数になる。全画面取得(`bbox=None`)時のみ
Retinaの物理解像度になる、という非対称な挙動があるため、実装前に
`ImageGrab.grab(bbox=(0,0,400,300))` の出力サイズを確認するテストを書くこと）。

マルチモニタ環境では `all_screens=True` を必ず指定すること
（指定しないとPILはプライマリモニタしか取得せず、セカンドモニタ上の
ウィンドウが真っ黒画像になる）。

## キー送信・クリック

`pyautogui` は両OS共通で使えるため、抽象化レイヤーに含めなくてよい。
ただし以下の点に注意する。

- macOSでは `pyautogui` の内部実装が Quartz イベントを使うため、
  アクセシビリティ権限が無いと**例外を出さずに黙って失敗する**。
  必ず事前に権限チェックを行い、失敗時にサイレントに進行しないこと
- ページめくりキーは `right` を既定としつつ、`REQUIREMENTS.md` の
  エスカレーション仕様（space→pagedown→down→scroll）を両OSで共通実装する

## 実装順序の推奨

1. `core/platform/macos_utils.py` と `windows_utils.py` を同時に書き始め、
   関数シグネチャの整合を都度確認する（片方だけ先に作り込むと後で
   インターフェースのズレに気づきにくい）
2. 各OS実装ごとに、実機で以下を単体確認してから `capture_engine.py` に着手する:
   - `find_window()` が対象アプリを正しく検出できるか
   - `activate_window()` 実行後もウィンドウが正常な状態（フルスクリーン化・
     最小化していない）を保っているか
   - `get_window_rect()` の座標をそのまま `ImageGrab.grab(bbox=...)` に渡して
     実際にウィンドウの中身が写るか（デスクトップや別ウィンドウでないか）
