# モジュールリファレンス

`core/` 配下14ファイルと `ui/` 配下7ファイルの役割・主要関数一覧です。
コメントベースではなく、実際のソースを読んだ上でまとめています。

## core/

### window_utils.py（macOS固有）
Quartz / AppKit によるウィンドウ検出・前面化。

- `find_window(title_keyword, exclude_pid=None, process_name=None) -> CGWindowID | None`
  タイトル部分一致＋スコアリングで対象ウィンドウを検索。`process_name` 指定時は
  そのプロセスのウィンドウに限定し、フォールバックしない（誤検出防止）。
- `get_window_title(hwnd)` / `get_window_rect(hwnd)` / `get_window_process_name(hwnd)`
- `activate_window(hwnd, click_position, use_bring_to_top)`
  `NSRunningApplication.activateWithOptions_` でアプリを前面化。**クリックはしない**
  （信号機ボタン誤操作の防止。詳細は [macos-port-notes.md](macos-port-notes.md)）。
  前面化が反映されるまで最大2秒程度リトライ確認する。
- `is_window_frontmost(hwnd)`: 対象アプリが現在最前面かを判定
- `has_screen_recording_access()` / `request_screen_recording_access()`
- `has_accessibility_access()` / `request_accessibility_access()`
- `get_title()`: タイトル入力ダイアログ（tkinter `simpledialog`、プラットフォーム非依存）

### capture_engine.py
プロファイル設定に基づくページ自動キャプチャの本体。

- `CaptureEngine`: `find_target_window()` → `set_target_window()` →
  `activate_target_window()` → `start(save_folder, title)`（別スレッド起動）
- `_grab()`: `PIL.ImageGrab.grab(bbox=self._target_rect, all_screens=True)`
- `_has_meaningful_change(old, new)`: ノイズ除去つき変化判定（差分ピクセル比0.5%閾値）
- `_page_turn_methods()` / `_send_page_turn(method)`: ページめくり方式のエスカレーション
  （`profile.page_turn_key` → space → pagedown → down → scroll）
- `_capture_loop()`: 権限チェック→前面確認→境界検出→ページ変化待ちループ→保存→次ページへ

### boundary_detector.py
- `FullFrameBoundary` / `ManualBoundary`: `create_detector(method, ...)` で選択
- `detect_content_box(im, threshold, padding)`: 4隅の中央値を背景色とみなし、差分から
  コンテンツのバウンディングボックスを検出（トリミングタブの自動検出で使用）
- `detect_margins(im, ...)`: 上記を4辺マージン形式に変換

### capture_profiles.py
- `CaptureProfile`（dataclass）: プロファイルの全フィールド定義
- `BUILTIN_PROFILES`: `kindle`, `google_play`, `rakuten_kobo`, `bookwalker`,
  `dmm_books`, `kinoppy` の6種（Windows版由来。macOS実機検証済みは `kindle` のみ）
- `get_profile()` / `get_all_profile_keys()`: `config.json` のカスタムプロファイルも解決

### pdf_extractor.py
- `extract_pdf_to_images(pdf_path, output_folder, dpi=200, image_format="png")`
  `pypdfium2` でPDFの各ページをレンダリングし連番画像として保存

### trimmer.py
- `trim_margins(im, left, right, top, bottom)`: 単純クロップ
- `process_images(input_folder, output_folder, ...)`: フォルダ一括処理

### ocr_preprocess.py
- `preprocess_image(image, upscale=1.5, enhance_contrast=True, binarize=False, ...)`
  Lanczosアップスケール→グレースケール→autocontrast→（任意で）二値化
- `preprocess_file(src_path, dst_path, ...)`: ファイルI/Oラッパー

### ocr_engine.py
- `NDLOCREngine`: NDLOCR-Lite を `subprocess` 経由で呼び出す唯一のOCRエンジン実装
  - `is_available()`: `ndlocr-lite` コマンド or ディレクトリの存在確認
  - `process_single(image_path, preprocess_opts)`: 一時ディレクトリで前処理→OCR実行→結果collect
- 公開API: `get_available_engines()`, `is_available()`, `process_single()`,
  `process_folder_collect(input_folder, on_progress, preprocess_opts, replacements_opts)`

### text_replacements.py
- `Replacer`: `literal`（文字列置換、長いキー優先）と `regex`（正規表現置換）を保持
- `load_replacer(path)`: `replacements.json` を読み込む。ファイル無し=no-op、壊れたJSON=エラー文言
- `apply_to_results(results, path)`: `[(filename, text), ...]` に一括適用

### text_reflow.py
- `reflow_text(text)`: OCRの改行ノイズを段落に結合（句点/閉じ括弧で区切り、英文はハイフン結合）
- `reflow_markdown(md)`: フロントマター・コードフェンスを保護しつつ本文だけ整形
- `python -m core.text_reflow 入力 出力` としてCLI実行可能

### chapter_detector.py
- `Chapter`（dataclass）: `page_index`, `filename`, `title`, `level`
- `detect_chapters(results)`: 「第◯章」等の強パターン／ヒューリスティックで章見出しを検出
  （詳細な検出ロジックはモジュールdocstring参照）

### markdown_writer.py
- `write_markdown(results, output_path, title, reflow, chapters, embed_images, image_folder)`
  フロントマター付きMarkdown。`embed_images=True` で画像を `<basename>_pages/` にコピーし
  `![p.NNN](path)` を本文前に挿入

### pdf_builder.py
- `images_to_pdf()`: 画像をそのままPDF化
- `images_to_searchable_pdf()`: 画像＋不可視OCRテキスト
- `text_to_pdf()`: OCRテキストのみ（reportlab `SimpleDocTemplate` で自動改ページ）
- `images_with_text_pdf()`: 画像ページ→テキストページの見開き型（macOS版で新規追加）
- 共通: `_chapters_by_filename()`, `_emit_bookmark()`, `_BookmarkFlowable`,
  `_OutlineCanvas`（しおり付きPDFのアウトラインパネル自動オープン）

### config.py
- `DEFAULT_CONFIG`: 初期設定（プロファイル・トリミング既定値・OCRオプション等）
- `load_config()` / `save_config()`: `_deep_merge()` でユーザー設定とデフォルトを非破壊マージ

## ui/

| ファイル | 役割 |
|---------|------|
| `main_window.py` | `KindleShotApp`（`ctk.CTk`サブクラス）。4タブを生成し `AppState`/`config` を配布 |
| `state.py` | `AppState`（タブ間イベント通知） |
| `widgets.py` | `Tooltip`, `LabeledFrame`（`ttk.LabelFrame` 相当をcustomtkinterで自作） |
| `capture_tab.py` | キャプチャタブ。`CaptureEngine` を生成し、進捗をUIスレッドに `root.after()` で反映 |
| `pdf_load_tab.py` | PDF読込タブ。`pdf_extractor.extract_pdf_to_images()` を呼ぶ |
| `trim_tab.py` | トリミングタブ。プレビュー描画・自動検出・`trimmer.process_images()` 呼び出し |
| `convert_tab.py` | 変換タブ。5形式の出力ロジックの分岐と各 `_convert_*()` メソッド |
