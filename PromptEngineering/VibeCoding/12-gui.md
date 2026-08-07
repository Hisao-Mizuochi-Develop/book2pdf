# 12-gui.md — タブベース GUI

## ゴール

4 タブで機能を切り替えられる GUI を提供する。タブ内部の詳細なレイアウトは 熟練したソフトウェアエンジニアの AI コーディングアシスタント が提案し、ユーザー確認を得てから実装する。

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

## デザイン提案フロー

各タブを実装する前に、熟練したソフトウェアエンジニアの AI コーディングアシスタント は以下を行う。

1. タブに必要な機能要素を `03-capture.md` 〜 `07-convert.md` から抽出する
2. 2〜3 パターンの UI デザイン案（配置案・ラベル案）をテキストまたは簡易図で提示する
3. ユーザーが 1 つを選択する（または修正指示を出す）
4. 確定したデザインに基づいて実装する

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
- ユーザーが承認したデザイン案に基づいて実装されている
