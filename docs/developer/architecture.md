# アーキテクチャ概要

## 技術スタック

| 分類 | 技術 |
|------|------|
| 実装言語 | Python 3.11 以降 |
| GUI フレームワーク | customtkinter |
| 画面操作・キャプチャ | pyautogui |
| 画像処理 | Pillow (PIL)、OpenCV (cv2) |
| PDF 入出力 | reportlab（生成）、pypdfium2（読み込み） |
| macOS ネイティブ連携 | pyobjc（Quartz / Cocoa / ApplicationServices） |
| ビルド | PyInstaller |
| テスト | pytest |
| 外部 OCR エンジン | NDLOCR-Lite（別途セットアップ） |

設定ファイルは JSON、`requirements.txt` / `pyproject.toml` で依存を管理しています。

## 全体構成

```
app.py                  エントリーポイント (customtkinter の appearance 設定 + mainloop)
├── core/                UI非依存のコアロジック（純粋関数寄り、tkinterに依存しない）
└── ui/                  4タブのGUI（core/ の関数を呼び出すだけで、業務ロジックは持たない）
```

この分離により、`core/` 配下は GUI なしで単体テスト・CLI実行が可能です
（実際 `core/text_reflow.py` は `python -m core.text_reflow` としてCLI実行できます）。

## UI層: タブ間の状態共有

4タブ（キャプチャ / PDF読込 / トリミング / 変換）は独立した `ctk.CTkFrame` サブクラスですが、
`ui/state.py` の `AppState` を介して緩く連携します。

```python
class AppState:
    def __init__(self):
        self.last_capture_folder = ""
        self.last_trim_output_folder = ""
        self._listeners = []

    def add_listener(self, callback): ...
    def notify(self, event, data=None): ...
```

- 各タブは `state.add_listener(self._on_state_change)` で購読する
- 処理完了時に `state.notify("capture_complete", output_folder)` のようにイベント発火
- 受け取ったタブは自分の「入力フォルダ」欄に自動セットする

イベント一覧:

| イベント名 | 発行元 | 用途 |
|-----------|--------|------|
| `capture_complete` | CaptureTab, PdfLoadTab | 出力フォルダをトリミングタブ・変換タブへ伝搬 |
| `trim_complete` | TrimTab | 出力フォルダを変換タブへ伝搬 |

`ui/main_window.py` の `BookCaptureApp` が4タブを生成し、共通の `AppState` と
`config_data`（`core/config.py` からロードした dict）を全タブに配って回るだけの
薄いコンテナになっています。

## Core層: 責務ごとのモジュール分割

「入力源 → 前処理 → OCR → 出力」の一直線パイプラインを、各段階ごとに
独立したモジュールとして実装しています（詳細は
[module-reference.md](module-reference.md)）。

```
入力源:   capture_engine.py (自動キャプチャ) / pdf_extractor.py (PDF→画像)
前処理:   trimmer.py (余白カット) / ocr_preprocess.py (OCR用の拡大・コントラスト調整)
OCR:      ocr_engine.py (NDLOCR-Lite 呼び出し) + text_replacements.py (誤認識の置換)
後処理:   text_reflow.py (段落整形) / chapter_detector.py (章見出し自動検出)
出力:     pdf_builder.py (各種PDF) / markdown_writer.py (Markdown)
```

各段階は「フォルダ・リストを受け取ってフォルダ・リストを返す」関数の集まりで、
tkinter のコールバック（`on_progress`）以外に GUI への依存を持ちません。

## macOS固有層: core/window_utils.py

`core/window_utils.py`（`pyobjc` の Quartz / AppKit）でウィンドウの検出・前面化を行います。
呼び出し側（`capture_engine.py`, `ui/capture_tab.py`）から見た関数シグネチャは
同一に保っており、影響範囲をこの1ファイルに閉じ込めています。

詳細は [macos-port-notes.md](macos-port-notes.md) を参照してください。

## キャプチャエンジンの内部状態遷移

`CaptureEngine`（`core/capture_engine.py`）は以下の状態を持ちます。

- `self._target_hwnd` / `self._target_rect`: キャプチャ対象ウィンドウのID・矩形
- `self._running`: 別スレッド（`threading.Thread`）で動くキャプチャループのフラグ
- ループ内のローカル状態: `turn_methods`（ページめくり方式の候補列）、
  `active_turn_idx`（現在有効な方式のインデックス、一度成功したら固定）

処理フローの詳細は [../diagrams/capture-sequence.md](../diagrams/capture-sequence.md) を参照してください。
