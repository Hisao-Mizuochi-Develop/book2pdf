# macOS移植ノート

Windows専用だった kindle2pdf を Apple Silicon Mac に移植した際の技術的な変更点と、
その理由をまとめます。Windows版のソースを直接参照せず、実装時の判断根拠を
記録する目的のドキュメントです。

## 1. ウィンドウ操作層

`core/window_utils.py` は `pyobjc` の `Quartz` / `AppKit` を用いて
ウィンドウの検出・前面化・権限確認を行います。

| 概念 | macOS API |
|------|-----------|
| ウィンドウ列挙 | `Quartz.CGWindowListCopyWindowInfo` |
| ウィンドウ矩形 | `kCGWindowBounds`（ポイント単位） |
| 前面化 | `NSRunningApplication.activateWithOptions_` |
| プロセス名取得 | `kCGWindowOwnerName` |
| キー/クリック送信 | `pyautogui`（内部は Quartz イベント） |

呼び出し側（`capture_engine.py`, `ui/capture_tab.py`）の関数シグネチャは
同一に保っているため、影響範囲はこの1ファイルの実装のみで完結しています。

## 2. 座標系: Retinaディスプレイのスケーリング

`CGWindowListCopyWindowInfo` が返す座標は**ポイント単位**（論理解像度）です。
`PIL.ImageGrab.grab(bbox=...)` にそのままポイント座標を渡すと、macOSでは
指定した範囲がそのままピクセル数の画像として返るため（内部で `screencapture`
コマンドを呼んでいる）、座標系の食い違いは発生しません。

検証手順（本移植中に実施）:

```python
from PIL import ImageGrab
img = ImageGrab.grab()                       # 例: (3360, 2100) 物理ピクセル (2x Retina)
img2 = ImageGrab.grab(bbox=(0, 0, 400, 300)) # (400, 300) — bboxで指定した値がそのまま出力サイズ
```

そのため `capture_engine.py` は Windows版と同じロジック
（`bbox = get_window_rect(hwnd)` をそのまま `ImageGrab.grab()` に渡す）で
正しく動作します。ただし出力画像はネイティブのRetina解像度（2倍）ではなく
「ポイント解像度（等倍）」になる点に注意してください。OCR用途では通常
十分な解像度ですが、より高解像度が必要な場合は別途スケール変換の実装が必要です。

## 3. `activate_window()` からクリック処理を撤廃

Windows版は `SetForegroundWindow` だけでは前面化が確実でないケースがあるため、
ウィンドウ内をクリックしてフォーカスを確定させていました。

macOSに移植した直後、この踏襲がバグの原因になりました。

- **不具合**: click_position `top_left` のクリック座標
  `(rect.left+60, rect.top+10)` が、macOSウィンドウの信号機ボタン
  （閉じる/しまう/フルスクリーン、概ね `x<80, y<30`）と重なっていた
- **症状**: 緑の「フルスクリーン化」ボタンを誤クリックし、対象アプリが
  独立したSpaceへ切り替わる → 以後 `find_window()` で見失う →
  背後の別ウィンドウやデスクトップを誤ってキャプチャし続ける

**対処**: `NSRunningApplication.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)`
だけでキーボードフォーカスの委譲には十分なことを確認し、クリック処理自体を撤廃。
念のため前面化が反映されたかを最大2秒程度ポーリング確認するリトライを追加。

## 4. 権限チェックの追加（Windowsには存在しない概念）

macOSはプライバシー保護のため、画面収録・アクセシビリティの2権限が
必要です。Windows版には無い概念のため、以下を新規追加しました。

- `has_screen_recording_access()` / `request_screen_recording_access()`
  （`Quartz.CGPreflightScreenCaptureAccess` / `CGRequestScreenCaptureAccess`）
- `has_accessibility_access()` / `request_accessibility_access()`
  （`ApplicationServices.AXIsProcessTrusted` / `AXIsProcessTrustedWithOptions`）
  ※ `pyobjc-framework-ApplicationServices` の追加インストールが必要

`capture_engine.py` の `_capture_loop()` 冒頭でこれらをチェックし、権限が
無ければキャプチャを開始せず明確なエラーメッセージを表示するようにしています。
権限が無いままキー送信・クリックを行っても**例外は出ずに黙って失敗する**ため、
このチェックが無いと「同じページを撮り続ける」不具合の原因がわからず
デバッグが非常に困難になります。

## 5. `find_window()` のスコアリングを厳格化

Windows版は「プロセス名が一致したらスコア加点」という設計で、プロセス名が
不一致でもタイトルの部分一致だけで別ウィンドウを掴めてしまう余地がありました。

移植中の実機テストで、Kindleアプリが閉じている状態にもかかわらず、たまたま
作業ディレクトリ名に "kindle" を含むターミナルのウィンドウタイトル
（`kindle2pdf_mac — -zsh — ...`）を誤って選んでしまう事例を確認しました。

**対処**: `process_name` が指定されている場合、そのプロセス名のウィンドウが
1つも見つからなければ **`None`（見つからない）を返し、タイトルのみでの
フォールバックはしない** 仕様に変更。これにより、無関係ウィンドウを誤って
掴むリスクを排除しています（副作用として、プロセス名の実際の値がmacOS実機と
食い違っているカスタムプロファイルは意図的に「見つからない」扱いになります。
[../user/custom-profiles.md](../user/custom-profiles.md) 参照）。

なお `process_name` の値は `.exe` サフィックスを自動除去して比較するため、
Windows版の値（例: `Kindle.exe`）をそのまま使い回せます。

## 6. ページめくりのフォールバック機構（新規）

実機検証中、「連続スクロール表示のアプリではRightキーが効かず、ページが
進まない」ケースを確認しました。Windows版はページめくりキーが固定で、
効かない場合の対処法が用意されていませんでした。

macOS版では以下を追加しています。

- **変化判定の閾値化**: 1ピクセルでも差分があれば「変化」とみなす
  `np.array_equal` ベースの判定は、カーソル点滅等のノイズで簡単に
  誤検出することが判明。差分ピクセル比が0.5%を超えた場合のみ
  「実質的な変化」とみなす `_has_meaningful_change()` に変更。
- **ページめくり方式の自動エスカレーション**: 既定のキー（通常 `right`）で
  変化がなければ、`space` → `pagedown` → `down` → マウスホイールスクロール
  の順に自動的に切り替えて試行。一度有効な方式が見つかったら、以降の
  ページもその方式を使い続ける（`_page_turn_methods()` / `_send_page_turn()`）。

## 7. OCRエンジン（NDLOCR-Lite）

NDLOCR-Lite自体はもともとmacOS（Apple Silicon）向けの `onnxruntime` 指定を
`requirements.txt` に含んでいたため、追加の修正なしでインストール・動作しました。
GPUなし・CPU（onnxruntime）で1ページあたり約15〜20秒（M-series Mac実測）。

## 8. 未検証の項目

- Intel Mac（Rosetta含む）での動作
- `google_play` / `rakuten_kobo` / `bookwalker` / `dmm_books` / `kinoppy`
  各プロファイルの実アプリでの動作（macOS版でネイティブアプリが存在するか
  自体が未確認のものを含む）
- マルチディスプレイ環境でのキャプチャ精度
