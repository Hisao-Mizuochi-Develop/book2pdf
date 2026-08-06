# 13-distribution.md — 配布ビルド手順

## 方針

- 開発・テスト時は `venv` ベースの `python app.py` / `run.sh` / `run.bat` を使用
- 配布時は PyInstaller を使用し、macOS では `book2pdf.app`、Windows では `book2pdf.exe` を作成
- ビルド自体は各 OS 上で行う必要がある（クロスコンパイルは不可）
- GitHub Actions 等の自動ビルドは現時点では設定しない

## PyInstaller インストール

```bash
pip install pyinstaller
```

## build.spec

Windows / macOS 両方で使える共通 `.spec` ファイルを作成する。OS 固有部分は `sys.platform` で分岐する。

```python
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE, BUNDLE, COLLECT

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.example.json', '.'),
        ('replacements.json', '.'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='book2pdf',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='book2pdf.app',
        icon=None,
        bundle_identifier='com.example.book2pdf',
    )
```

## macOS ビルド手順

```bash
source book_env/bin/activate
python -m PyInstaller build.spec --clean --noconfirm
```

生成物: `dist/book2pdf.app`

### 注意点

- `sys.executable` 問題を避けるため、OCR サブプロセス起動時には venv 内の Python パスを保持する
- 必要に応じて `Info.plist` をカスタマイズ
- 画面収録・アクセシビリティ権限の説明を `Info.plist` の `NSAppleEventsUsageDescription` 等に記載

## Windows ビルド手順

Windows 環境で以下を実行する。

```bat
call book_env\Scripts\activate
python -m PyInstaller build.spec --clean --noconfirm
```

生成物: `dist/book2pdf.exe`

### 注意点

- Windows 上で `.spec` ファイルを実行する
- 同じソースコードを使用するため、macOS とコード変更は不要

## 配布時のファイル構成

```
book2pdf/
├── book2pdf.app   # macOS
├── book2pdf.exe   # Windows
├── config.example.json
├── replacements.json
└── README.md
```

## OCR サブプロセスのパス解決

PyInstaller 凍結時に `sys.executable` がアプリ自身を指す問題を避けるため、以下の対策を講じる。

- venv 起動時: `sys.executable` をそのまま使用
- 凍結時: 同梱または近くに配置した Python インタプリタのパスを別途保持
- `core/ocr_engine.py` 内で「凍結環境かどうか」を判定し、適切なパスを選択

## 完了条件

- macOS で `book2pdf.app` がダブルクリックで起動する
- Windows で `book2pdf.exe` が起動する
- 配布ビルドでもキャプチャ・PDF 読込・トリミング・変換の基本動作が確認できる
