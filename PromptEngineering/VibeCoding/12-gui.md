# 12-gui.md — タブベース GUI

## ゴール

4 タブで機能を切り替えられる GUI を提供する。タブ内部のレイアウトは本ドキュメントの「共通 UI ガイドライン」と各タブの「必須要素」に従い、AI コーディングアシスタント が直接実装する。ユーザーへの都度確認は不要（必要に応じて微調整する）。

## 基本構造

```
ui/
├── main_window.py    # BookCaptureApp: 4 タブのメインウィンドウ
├── state.py          # AppState: タブ間状態共有（Observer パターン）
├── capture_tab.py    # キャプチャタブ
├── pdf_load_tab.py   # PDF 読込タブ
├── trim_tab.py       # トリミングタブ
├── convert_tab.py    # 変換タブ
└── widgets.py        # 共通ウィジェット（Tooltip, LabeledFrame 等）
```

## main_window.py

- ウィンドウタイトル: `book2pdf — 電子書籍キャプチャ・OCRツール`
- 初期サイズ: 1024x920 程度（必要に応じて調整可）
- ヘッダーにテーマ切り替え（auto / light / dark）を配置
- 4 タブを追加: `キャプチャ`, `PDF読込`, `トリミング`, `変換`
- 各タブは `ctk.CTkFrame` を継承したクラスとして実装
- ウィンドウを閉じた際に `config.json` にテーマを保存
- 起動時に `ctypes.windll.user32.SetProcessDPIAware()` を呼び出す（Windows のみ）

## state.py

```python
class AppState:
    def __init__(self):
        self.last_capture_folder = ""
        self.last_trim_output_folder = ""
        self._listeners = []

    def add_listener(self, callback):
        self._listeners.append(callback)

    def notify(self, event, data=None):
        for listener in self._listeners:
            listener(event, data)
```

- イベント:
  - `capture_complete`: 画像フォルダのパスを `data` に含める
  - `trim_complete`: トリミング済みフォルダのパスを `data` に含める

## タブ間連携

- `capture_tab.py` と `pdf_load_tab.py` は両方とも `capture_complete` を発行する
- `trim_tab.py` は `capture_complete` を受け取り、入力フォルダを自動設定する
- `trim_tab.py` は `trim_complete` を発行する
- `convert_tab.py` は `capture_complete` と `trim_complete` の両方を受け取り、入力フォルダを自動設定する
- 各タブは他のタブのウィジェットを直接参照しない

## タブ実装の方針

各タブを実装する際は、以下の優先順位でレイアウトを決定する。

1. 必須機能要素を `07-capture.md` / `08-pdf-load.md` / `09-trim.md` / `11-convert.md` から抽出する。
2. 下記「共通 UI ガイドライン」を適用する。
3. 配置は機能グループごとに `LabeledFrame`（または同等のグループ枠）でまとめ、縦に積み重ねる基本形とする。
4. 操作頻度が高い要素は画面上部に、進捗・ログは画面下部に配置する。

### 各タブの必須要素

| タブ | 必須要素 |
|------|---------|
| キャプチャ | プロファイル選択、ウィンドウ検出、ページめくり方向、開始位置、保存設定、開始/停止ボタン、進捗バー、ログ |
| PDF読込 | PDF ファイル選択、出力フォルダ、DPI/形式、実行ボタン、進捗バー、ログ |
| トリミング | 入力/出力フォルダ、4 辺余白入力、自動検出ボタン、プレビュー、実行ボタン、進捗バー |
| 変換 | 入力/出力フォルダ、出力形式選択、OCR オプション、実行ボタン、進捗バー、結果プレビュー |

## 共通 UI ガイドライン

- customtkinter の標準ウィジェットを使用
- ダーク/ライト両テーマで視認性が保たれる配色
- 進捗状況はテキストログ＋プログレスバーで表示
- エラーはユーザーに明確に伝え、サイレントに失敗させない
- 長時間処理は別スレッドで実行し、UI をフリーズさせない

## 完了条件

- アプリがクラッシュせず起動する
- 4 タブの切り替えが正常に動作する
- タブ間で画像フォルダが自動引き継がれる
- 各タブの主要ボタンが機能する
- 共通 UI ガイドラインと各タブの必須要素に従って実装されている
