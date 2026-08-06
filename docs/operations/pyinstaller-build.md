# PyInstaller スタンドアロン .app ビルド手順

本文書では、**PyInstaller** を使用して `book2pdf` を macOS の `.app` バンドル（ダブルクリック起動可能なアプリ）にビルドする手順を解説します。

## 1. 背景

通常、本ツールは Python 仮想環境 (`book_env/`) 前提で動作しますが、\`pyinstaller\` を実行すると、仮想環境や Python インストールを不要にできます。最終的に出力される `dist/book2pdf.app` は、macOS の **アプリケーションフォルダにドラッグ＆ドロップ** するだけで配置できます。

### 採用理由
- 配布先に Python をインストールさせる手間を省く
- Finder からダブルクリックで起動可能

### 制約
- **NDLOCR-Lite は同梱しません**（torch + ONNX Runtime 等を含めるとサイズが数GBに達するため）
- OCR 機能は、アプリ起動後にユーザーが NDLOCR-Lite を別途セットアップした場合に有効になります
- NDLOCR-Lite 未インストール時はアプリが正常に起動し、OCR 関連タブが無効化されます

## 2. 前提条件

| 要件 | バージョン |
|------|-----------|
| Python | >= 3.11 |
| macOS | >= 12 (Monterey) |
| Homebrew | インストール済 |

`pyinstaller` のインストール（仮想環境内、またはグローバルにインストール済みの Python で実行）：

```bash
pip install pyinstaller
```

## 3. ocr_engine.py の修正（必須）

PyInstaller で凍結（freeze）したアプリは、`sys.executable` が凍結されたバイナリ自身（`book2pdf`）を指します。これは Python スクリプトを実行できず、NDLOCR-Lite のサブプロセス (`ocr.py`) 起動に失敗します。

### 修正箇所

`core/ocr_engine.py` の `_build_command()` メソッド（105行目周辺）を修正します。

```python
    def _build_command(self, input_path, output_dir, use_system):
        if use_system:
            cmd = ["ndlocr-lite"]
        else:
            ndlocr_dir = self._find_dir()
            if not ndlocr_dir:
                raise RuntimeError("ndlocr-lite が見つかりません")
            # PyInstaller 凍結環境では sys.executable が凍結バイナリ自身になる
            # その場合はシステムの python3 を探して使う
            python_exe = self._get_python_executable()
            cmd = [python_exe, os.path.join(ndlocr_dir, "src", "ocr.py")]

        if os.path.isdir(input_path):
            cmd.extend(["--sourcedir", input_path])
        else:
            cmd.extend(["--sourceimg", input_path])
        cmd.extend(["--output", output_dir])
        return cmd
```

そして、`_get_python_executable()` メソッドを追加します。

```python
    def _get_python_executable(self):
        """PyInstaller 凍結環境で sys.executable が凍結バイナリになった場合の回避。"""
        if getattr(sys, "frozen", False):
            # 凍結中 → システムの python3 を探す
            found = shutil.which("python3")
            if found:
                return found
            # /usr/bin/python3 は macOS に同梱されている
            if os.path.exists("/usr/bin/python3"):
                return "/usr/bin/python3"
            raise RuntimeError(
                "PyInstaller 凍結環境でシステムの python3 が見つかりません。"
                "NDLOCR-Lite を使用するには /usr/bin/python3 が必要です。"
            )
        return sys.executable
```

これにより、メインアプリ自体は PyInstaller 化されていても、OCR サブプロセスはシステムにインストールされた Python を使用して実行されます。

## 4. PyInstaller .spec ファイル

プロジェクトルートに `build-mac.spec` を作成します。

```python
# build-mac.spec
import PyInstaller.config as pyi_config
pyi_config.CONF["workpath"] = "./build"  # 中間ファイルの出力先

# PyInstaller 5.13+ では 2-pass ビルド推奨
block_cipher = None

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("config.example.json", "."),
        ("replacements.json", "."),
        ("README.md", "."),
        # NDLOCR-Lite を同梱する場合は以下を追加
        # ("ndlocr-lite", "ndlocr-lite"),
    ],
    hiddenimports=[
        "customtkinter",
        "PIL._tkinter_finder",
        "cv2",
        "numpy.core._dtype_ctypes",
        "pyobjc.compat",
        "Quartz",
        "Cocoa",
        "ApplicationServices",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # サイズ削減のため不要なパッケージを除外
        "matplotlib",
        "pytest",
    ],
    cipher=block_cipher,
    noarchive=False,
)

# collect-all で巨大パッケージをまとめてバンドル
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="book2pdf",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUIアプリとして起動
    disable_windowed_traceback=False,
    argv_emulation=True,  # macOS の argv emulation を有効化
    target_arch="arm64",  # Apple Silicon
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="book2pdf",
)

app = BUNDLE(
    coll,
    name="book2pdf.app",
    icon=None,
    bundle_identifier="com.hisao.book2pdf",
    info_plist={
        "LSBackgroundOnly": False,
        "NSHighResolutionCapable": True,
    },
)
```

### .spec のポイント

| 設定 | 説明 |
|------|------|
| `console=False` | ターミナルウィンドウを表示せず GUI で起動 |
| `argv_emulation=True` | macOS でファイル開くダイアログ等に対応 |
| `target_arch="arm64"` | Apple Silicon 用 (Intel Mac では `x86_64`) |
| `codesign_identity=None` | コードサイン未設定。配布時には Developer ID 推奨 |

## 5. ビルド実行

プロジェクトルートで以下を実行します。

```bash
# 仮想環境を有効化（pyinstaller をインストールしている環境）
source book_env/bin/activate

# 1回目（Analyze + Collect）
pyinstaller build-mac.spec --clean
```

ビルドが完了すると以下が生成されます。

```
dist/
├── book2pdf.app/          ← 完成品（Finder からドラッグ＆ドロッフ可能）
└── book2pdf/              ← 通常のフォルダ（中身確認用、不要なら削除）
```

`book2pdf.app` を **アプリケーションフォルダ `/Applications/`** にドラッグ＆ドロップして配置します。

## 6. 動作確認

1. Finder → アプリケーションフォルダ → `book2pdf.app` をダブルクリック
2. 初回は「開発元が未確認のため開けません」が出る場合は **システム設定 → プライバシーとセキュリティ → このまま開く**
3. アプリのウィンドウが表示されることを確認
4. NDLOCR-Lite 未インストール時は OCR タブが無効化されていることを確認

## 7. トラブルシューティング

### ビルド時にエラーが出る

```bash
# 中間ファイルをクリーンして再ビルド
pyinstaller build-mac.spec --clean --noconfirm
```

### アプリ起動時に「開発元が未確認」

```bash
# コマンドラインから Gatekeeper を一時的に回避してテスト
xattr -cr /Applications/book2pdf.app
```

（配布時には公式に Developer ID でコードサインが必要）

### OCR 機能が動かない

`book2pdf` 自体は起動しますが、OCR は **システム Python3 + NDLOCR-Lite** が必要です。ターミナルで以下を実行してください。

```bash
# システム Python3 に NDLOCR-Lite 依存をインストール
/usr/bin/python3 -m pip install --user onnxruntime opencv-python torch numpy pillow

git clone https://github.com/ndl-lab/ndlocr-lite.git /Applications/book2pdf.app/Contents/Resources/ndlocr-lite
```

NDLOCR-Lite のパス解決は `core/ocr_engine.py` の `_find_dir()` が `ndlocr-lite/` サブフォルダを自動検索します。

## 8. 配布時の注意点

| 項目 | 推奨 |
|------|------|
| コードサイン | Apple Developer ID でコードサイン（ないと Gatekeeper でブロック） |
| 公証 (Notarization) | 配布時には Apple の公証も推奨 |
| アーキテクチャ | arm64 (Apple Silicon) と x86_64 (Intel) の Universal 化はボリューム増大のため、別ビルド推奨 |
