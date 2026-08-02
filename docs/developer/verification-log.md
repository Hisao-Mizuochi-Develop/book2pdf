# 検証ログ

macOS移植作業中に実施した動作確認の記録です。実行環境は Apple Silicon Mac
（arm64, macOS）、Python 3.12（Homebrew）、Amazon Kindle.app（実アプリ）です。

## 環境構築

- `brew install python@3.12 python-tk@3.12` — customtkinter起動に必須（tkinter同梱）
- `python3.12 -m venv kindle_env` + `pip install -r requirements.txt`
- `pyautogui` インストール時に `pyobjc-core` / `pyobjc-framework-Quartz` /
  `pyobjc-framework-Cocoa` が自動導入されることを確認
- `pyobjc-framework-ApplicationServices` は別途追加インストールが必要だった
  （アクセシビリティ権限チェックに使用）

## ウィンドウ検出・座標系

- `Quartz.CGWindowListCopyWindowInfo` で実際に稼働中のアプリ一覧・タイトル・
  `kCGWindowBounds` を取得できることを確認（画面収録権限が事前に許可されていた
  ターミナルで検証）
- `PIL.ImageGrab.grab()`（bboxなし）: `(3360, 2100)` — Retina物理ピクセル
- `PIL.ImageGrab.grab(bbox=(0,0,400,300))`: `(400, 300)` — bbox値がそのまま
  出力ピクセル数になることを確認（ポイント座標とスクリーンショット座標系が
  一致し、追加のスケール変換が不要と判明）
- 実際にKindleウィンドウを `find_window('kindle', process_name='Kindle.exe')`
  で検出 → `get_window_rect()` で座標取得 → `activate_window()` で前面化 →
  `_grab()` で実際のページ内容（書籍本文）が正しく撮影できることを確認

## 自動キャプチャ（ページめくり）

- `pyautogui.keyDown('right')` / `keyUp('right')` でKindleの実際のページが
  遷移することを、撮影前後の画像差分で確認
- `CaptureEngine` を使った6ページ連続自動キャプチャを複数回実施し、いずれも
  ページ番号が正しく進行すること（616→619ページ等）を撮影画像で目視確認

## 発見した不具合と再現・修正確認

1. **無関係ウィンドウの誤検出**: Kindleが閉じている状態で
   `find_window('kindle', process_name='Kindle.exe')` が、作業ディレクトリ名に
   "kindle" を含むターミナルウィンドウ（`kindle2pdf_mac — -zsh...`）を誤って
   返すことを確認 → プロセス名指定時はフォールバックしない仕様に修正 → 同条件で
   `None` が返ることを確認
2. **信号機ボタンの誤クリック**: `activate_window(click_position='top_left')`
   のクリック座標 `(left+60, top+10)` が実際にmacOSの信号機ボタン付近であり、
   これが原因でKindleが独立フルスクリーンSpaceへ切り替わる（`kCGWindowBounds`
   が `Y=0, Height=1050`＝メニューバー分の考慮なしに変化）ことを、実際に
   発生させて確認 → クリック処理を撤廃 → 6ページ連続キャプチャが安定して
   成功することを再確認
3. **画面ロックによるキャプチャ失敗**: 検証中に実際にMacがアイドルタイムアウトで
   ロックされ、`is_window_frontmost()` が `False`（フロントモストアプリが
   `loginwindow`）になることを確認。`ioreg -n Root -d1 | grep CGSSession` で
   `CGSSessionScreenIsLocked=Yes` を確認し、ロック中は安全にキャプチャが
   停止する（対象外のコンテンツを撮らない）ことを確認
4. **ページめくりが効かない場合の自動復旧**: `page_turn_key` にわざと無効な
   キー（`f15`）を設定してテストし、1回のタイムアウト後に自動で `space`
   キーへエスカレーションし、以降15ページ連続で正しくキャプチャできることを確認

## OCR (NDLOCR-Lite)

- `git clone` + `pip install -r ndlocr-lite/requirements.txt` は
  Apple Silicon向けの `onnxruntime==1.23.2`（`sys_platform == "darwin"` 条件）
  により無修正でインストール成功
- 実際にKindleキャプチャ画像に対して `ocr_engine.process_single()` を実行し、
  約17秒/枚で本文テキストが概ね正しく抽出されることを確認

## PDF生成（画像+テキストPDF, 新機能）

- 6ページのKindleキャプチャ画像 → OCR → `images_with_text_pdf()` で
  15ページのPDF（一部ページのOCRテキストが1ページに収まらず自動改ページ）を生成
- `pypdfium2` でPDFの各ページをレンダリングし、「画像ページ→同じページの
  テキストページ→次の画像ページ→…」の順序が期待通りであることを目視確認

## 未実施の検証

- PyInstaller等によるスタンドアロン `.app` 化（venvベースの起動のみ検証）
- Intel Mac、マルチディスプレイ環境
- Kindle以外のビルトインプロファイル（google_play等）の実アプリでの動作
