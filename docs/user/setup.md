# セットアップ（macOS版）

book2pdf を Apple Silicon Mac（M1/M2/M3等）で動かすためのセットアップ手順です。

## 必要なもの

- macOS（Apple Silicon 推奨。Intel Macでも動作するはずですが未検証です）
- Python 3.11〜3.13（Homebrewでのインストールを推奨）
- Xcode Command Line Tools（`git` コマンドに必要）

システムの Python（`/usr/bin/python3`）は tkinter が制限されていたり
バージョンが合わなかったりするため、Homebrew で専用の Python を用意します。

## 1. Python と tkinter を用意する

```bash
brew install python@3.12
brew install python-tk@3.12
```

`python-tk@3.12` を忘れると、customtkinter（GUIツールキット）が
「tkinterが見つからない」エラーで起動できません。

## 2. 仮想環境を作成し依存パッケージをインストール

```bash
cd book2pdf_mac
/opt/homebrew/bin/python3.12 -m venv book_env
book_env/bin/pip install --upgrade pip
book_env/bin/pip install -r requirements.txt
```

macOS版では、Windows版の `pywin32` 系の代わりに以下が入ります。

- `pyobjc-core` / `pyobjc-framework-Quartz` / `pyobjc-framework-Cocoa`
  — ウィンドウ検出・前面化・スクリーンショット
- `pyobjc-framework-ApplicationServices`
  — アクセシビリティ権限の確認

## 3. OCRエンジン（NDLOCR-Lite）を導入する（任意）

画像PDF以外の出力形式（テキストPDF・検索可能PDF・Markdown・画像+テキストPDF）を
使う場合のみ必要です。

```bash
git clone https://github.com/ndl-lab/ndlocr-lite.git
book_env/bin/pip install -r ndlocr-lite/requirements.txt
```

NDLOCR-Lite の `requirements.txt` はすでに macOS（Apple Silicon）向けの
`onnxruntime` を条件分岐で指定しているため、追加の修正なしでインストールできます。
GPUは不要で、CPU（onnxruntime）で動作します。

## 4. 起動

```bash
book_env/bin/python3 app.py
```

詳しい操作手順は [quickstart.md](quickstart.md) を、必要な権限については
[permissions.md](permissions.md) を参照してください。

## Windows版との違い（要約）

| 項目 | Windows版 | macOS版 |
|------|-----------|---------|
| ウィンドウ操作 | `ctypes` + `windll`（Win32 API） | `pyobjc`（Quartz / AppKit） |
| 起動権限 | 不要 | 画面収録・アクセシビリティ権限が必要 |
| セットアップ | `setup.bat` | 手動（本ドキュメント）または `docs/operations/build-distribution.md` |
| 実行ファイル | `run.bat` | venv越しに `python3 app.py`、または .app ランチャー |

技術的な変更点の詳細は [../developer/macos-port-notes.md](../developer/macos-port-notes.md) を参照してください。
