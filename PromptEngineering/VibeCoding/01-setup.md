# 01-setup.md — 環境構築・プロジェクトセットアップ

## ゴール

book2pdf を開発・実行できる環境を構築し、最初に動作確認できる状態にする。

## 手順

### 1. Python バージョン確認

```bash
python --version
```

3.11〜3.13 の範囲内であること。範囲外の場合は pyenv などで切り替える。

### 2. 仮想環境作成

```bash
python -m venv book_env
source book_env/bin/activate  # macOS
# book_env\Scripts\activate  # Windows
```

### 3. 依存パッケージインストール

`pyproject.toml` と `requirements.txt` を作成する。`requirements.txt` は `pyproject.toml` から生成する。

```bash
pip install uv
uv pip compile pyproject.toml -o requirements.txt
pip install -r requirements.txt
```

### 4. pyproject.toml の内容

```toml
[project]
name = "book2pdf"
version = "0.1.0"
description = "電子書籍のスクリーンキャプチャ・PDF読込・トリミング・PDF変換・OCR統合ツール"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }

dependencies = [
    "pyautogui>=0.9.54",
    "opencv-python>=4.11,<4.14",
    "numpy==2.2.2",
    "Pillow==12.1.1",
    "reportlab==4.2.5",
    "pypdfium2==4.30.0",
    "customtkinter>=5.2.2",
    "pyobjc-framework-Quartz>=10.0",
    "pyobjc-framework-Cocoa>=10.0",
    "pyobjc-framework-ApplicationServices>=10.0",
]

[dependency-groups]
dev = [
    "ruff>=0.15",
    "uv>=0.11",
    "pytest>=9.0",
]

[tool.ruff]
target-version = "py311"
line-length = 100
extend-exclude = ["book_env", "ndlocr-lite", "__pycache__"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM"]
ignore = ["E501", "E402"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 5. ディレクトリ構成作成

```
book2pdf/
├── app.py
├── pyproject.toml
├── requirements.txt
├── config.example.json
├── replacements.json
├── run.sh
├── run.bat
├── README.md
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── platform/
│       ├── __init__.py
│       ├── windows_utils.py
│       └── macos_utils.py
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── state.py
│   ├── capture_tab.py
│   ├── pdf_load_tab.py
│   ├── trim_tab.py
│   ├── convert_tab.py
│   └── widgets.py
├── tests/
│   └── test_basic.py
└── docs/
    └── operations/
        └── ocr-engines.md
```

### 6. 設定ファイル雛形

`config.example.json` を作成する。内容は `core/config.py` の `DEFAULT_CONFIG` と整合させる。

### 7. 起動スクリプト

#### macOS / Linux: run.sh

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"
source book_env/bin/activate
python app.py
```

#### Windows: run.bat

```bat
@echo off
cd /d "%~dp0"
call book_env\Scripts\activate
python app.py
```

### 8. lint 動作確認

```bash
ruff check .
ruff format --check .
```

### 9. 最小動作確認

```bash
python -c "import customtkinter; print('customtkinter OK')"
python -c "import cv2; print('opencv OK')"
python -c "from core.platform import find_window; print('platform OK')"
```

### 10. NDLOCR-Lite のセットアップ（OCR を使う場合）

NDLOCR-Lite は外部リポジトリとして `ndlocr-lite/` 以下に clone する。

```bash
git clone https://github.com/ndl-lab/ndlocr-lite.git
```

その後、NDLOCR-Lite の README に従い依存をインストールする。アプリ側は NDLOCR-Lite の `main.py` をサブプロセスで呼び出すだけとし、改造しない。

## 完了条件

- `python app.py` で GUI が起動する（この時点ではタブが空でもよい）
- `ruff check .` がパスする
- `tests/test_basic.py` がパスする
