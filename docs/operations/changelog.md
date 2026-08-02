# 変更履歴

Windows専用のオリジナル版から、macOS（Apple Silicon）版への移植過程での変更点です。
バージョン番号ではなく、対応内容ごとに区切って記載します。

## macOS移植（初回）

- `core/window_utils.py`（pyobjc / Quartz・AppKit）を新規作成
  - `find_window`, `get_window_title`, `get_window_rect`,
    `get_window_process_name`, `activate_window`, `get_title` の
    シグネチャを `capture_engine.py`, `ui/capture_tab.py` と整合させて実装
- 依存パッケージに `pyobjc-core`, `pyobjc-framework-Quartz`,
  `pyobjc-framework-Cocoa`, `pyobjc-framework-ApplicationServices` を追加
- venvベースの起動方式を採用（PyInstaller化は見送り。理由は
  [build-distribution.md](build-distribution.md)）

## 不具合修正: ウィンドウ誤検出

- **問題**: `find_window()` がプロセス名不一致でもタイトル部分一致だけで
  無関係なウィンドウ（例: 作業フォルダ名に対象キーワードを含むターミナル）を
  誤って選んでしまうことがあった
- **修正**: `process_name` 指定時は該当プロセスのウィンドウが1件も無ければ
  `None` を返し、タイトルのみでのフォールバックを廃止

## 不具合修正: ウィンドウの誤フルスクリーン化

- **問題**: `activate_window()` の前面化後クリック（`click_position='top_left'`
  等）の座標がmacOSの信号機ボタン（閉じる/しまう/フルスクリーン）と重なっており、
  誤操作でウィンドウが独立Spaceのフルスクリーンに切り替わり、以後見失う不具合があった
- **修正**: `activate_window()` からクリック処理自体を撤廃。
  `NSRunningApplication.activateWithOptions_` のみで前面化・キーボード
  フォーカス委譲が完結することを確認した上での変更

## 機能追加: 権限の事前チェック

- キャプチャ開始前に画面収録・アクセシビリティ権限を確認し、不足時は
  明確なエラーメッセージを表示するように変更
  （`has_screen_recording_access`, `has_accessibility_access` 等を追加）
- キャプチャ中も対象ウィンドウが最前面かを継続監視し、外れた場合は
  安全に停止するように変更

## 不具合修正: ページが進まない（先頭ページの反復キャプチャ）

- **問題1**: ページ変化判定が `np.array_equal`（1ピクセルでも差分があれば
  「変化」）だったため、カーソル点滅等の微小ノイズを誤って「ページ変化」と
  検出し、実質同じページの画像を連番で量産することがあった
- **修正1**: 差分ピクセル比が0.5%を超えた場合のみ「実質的な変化」とみなす
  `_has_meaningful_change()` を導入
- **問題2**: ページめくりキーが対象アプリ/表示モードに効かない場合、
  復旧手段がなかった
- **修正2**: 既定キーで変化が無ければ `space` → `pagedown` → `down` →
  マウスホイールスクロールへ自動エスカレーションする機構を追加
  （`_page_turn_methods()`, `_send_page_turn()`）

## 機能追加: OCRエンジン（NDLOCR-Lite）のmacOS対応確認

- `ndlocr-lite` の `requirements.txt` がmacOS（Apple Silicon）向けの
  `onnxruntime` 条件分岐を既に含んでいたため、無修正でインストール・動作を確認

## 機能追加: 出力形式「画像+テキストPDF」

- `core/pdf_builder.py` に `images_with_text_pdf()` を追加
  （画像ページ→同じページのOCRテキストページ、を全ページ繰り返す見開き型PDF）
- `ui/convert_tab.py` に出力形式の選択肢として追加し、段落整形オプションを
  Markdownと共通で使えるように変更

## ドキュメント整備

- `docs/` 配下に対象者別（ユーザー/開発者/運用/図解）のドキュメント一式を新規作成
