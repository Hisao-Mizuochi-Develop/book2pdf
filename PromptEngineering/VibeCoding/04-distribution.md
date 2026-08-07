# 04-distribution.md — 配布ビルド手順

## 方針

- 開発・テスト時は `venv` ベースの `python app.py` / `run.sh` / `run.bat` を使用
- 配布時は PyInstaller を使用し、macOS では `book2pdf.app`、Windows では `book2pdf.exe` を作成
  - ただし `docs/operations/build-distribution.md` にもある通り、開発・自分用運用では venv 起動を推奨する
  - PyInstaller はエンドユーザー配布時の選択肢として位置づける
- ビルド自体は各 OS 上で行う必要がある（クロスコンパイルは不可）
- GitHub Actions 等の自動ビルドは現時点では設定しない

## 併せて参照するドキュメント

本プロンプトと併せて以下の docs/ ファイルを参照してください。

- `docs/operations/pyinstaller-build.md`: PyInstaller ビルドの詳細、OCR サブプロセスの `sys.executable` 問題への対処
- `docs/operations/build-distribution.md`: venv ベースの起動方式と配布方針の背景

## PyInstaller インストール

```bash
pip install pyinstaller
```

## build-mac.spec / build-win.spec

OS ごとに専用の `.spec` ファイルを用意する。両ファイルは `core/` / `ui/` 以下のローカルモジュールを自動収集する共通関数 `collect_local_imports()` を含む。

### build-mac.spec（macOS 用）

- `platform.machine()` で Apple Silicon (`arm64`) / Intel (`x86_64`) を自動判定
- `BOOK2PDF_CODESIGN_ID` 環境変数でコードサイン Identity を切り替え可能
- `argv_emulation=True` で macOS のファイル open ダイアログ等に対応
- `BUNDLE` で `book2pdf.app` を生成

### build-win.spec（Windows 用）

- macOS 専用フレームワーク (`Quartz`, `Cocoa`, `ApplicationServices`, `objc`) を `excludes` に指定
- `console=False` で GUI として起動
- `BUNDLE` は含まず、`EXE` + `COLLECT` で `dist/book2pdf/book2pdf.exe` を生成

### ローカルモジュール収集

両 `.spec` に以下の関数を含め、動的 import やサブパッケージが漏れないようにする。

```python
def collect_local_imports():
    imports = []
    base_dir = os.path.abspath(SPECPATH)
    for pkg in ("ui", "core"):
        pkg_path = os.path.join(base_dir, pkg)
        if not os.path.isdir(pkg_path):
            continue
        imports.append(pkg)
        for root, _dirs, files in os.walk(pkg_path):
            if "__pycache__" in root:
                continue
            rel = os.path.relpath(root, base_dir).replace(os.sep, ".")
            for f in files:
                if f.endswith(".py") and f != "__init__.py":
                    imports.append(rel + "." + f[:-3])
    return imports
```

## macOS ビルド手順

```bash
source book_env/bin/activate
python -m PyInstaller build-mac.spec --clean --noconfirm
```

生成物: `dist/book2pdf.app`

### アーキテクチャ

- Apple Silicon Mac: `target_arch="arm64"` でビルド
- Intel Mac: `target_arch="x86_64"` でビルド
- `build-mac.spec` 内で `platform.machine()` から自動判定される

### コードサイン

ローカルテストでは署名なしでも起動可能（Gatekeeper 警告が出る場合は「システム設定 → プライバシーとセキュリティ → このまま開く」）。
配布時は Developer ID でコードサインすることを推奨する。

```bash
export BOOK2PDF_CODESIGN_ID="Developer ID Application: Your Name (TEAM_ID)"
python -m PyInstaller build-mac.spec --clean --noconfirm
```

### 注意点

- `sys.executable` 問題を避けるため、OCR サブプロセス起動時には venv 内の Python パスを保持する
- 凍結環境ではシステムの `python3` を使用するフォールバックを `core/ocr_engine.py` に実装する
- 必要に応じて `Info.plist` をカスタマイズ
- 画面収録・アクセシビリティ権限の説明を `Info.plist` の `NSAppleEventsUsageDescription` 等に記載

## Windows ビルド手順

Windows 環境で以下を実行する。

```bat
call book_env\Scripts\activate
python -m PyInstaller build-win.spec --clean --noconfirm
```

生成物: `dist/book2pdf/book2pdf.exe`

### 注意点

- Windows 上で `build-win.spec` を実行する
- 同じソースコードを使用するため、macOS とコード変更は不要
- Windows では `Quartz`/`Cocoa`/`ApplicationServices`/`objc` を除外済み
- DPI スケーリング対策として、起動時に `SetProcessDPIAware()` を呼び出す（`12-gui.md` 参照）

## 配布時のファイル構成

```
book2pdf/
├── book2pdf.app          # macOS
├── book2pdf/             # Windows フォルダ
│   └── book2pdf.exe
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
  - Apple Silicon / Intel 両方でビルドできる
  - 必要に応じて Developer ID コードサインを適用できる
- Windows で `dist/book2pdf/book2pdf.exe` が起動する
- 配布ビルドでもキャプチャ・PDF 読込・トリミング・変換の基本動作が確認できる
