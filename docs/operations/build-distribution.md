# ビルド・配布手順書

## 配布方式の選択肢

book2pdf macOS版には、以下の 2 つの配布・起動方式があります。

| 方式 | 用途 | 説明 |
|------|------|------|
| venv ベース起動 | 開発・自分用運用 | `book_env/` を作成し `python app.py` で起動。安定していて保守しやすい |
| PyInstaller スタンドアロン | エンドユーザー配布 | `.app` バンドルとして配布。コードサインが必要 |

開発・テスト時は原則 **venv ベースの起動** を推奨します。配布時には
`docs/operations/pyinstaller-build.md` に記載の PyInstaller ビルドを使用します。

### venv 方式を推奨する理由

- OCR機能（NDLOCR-Lite）が `sys.executable`（実行中のPythonインタプリタ）を
  使ってサブプロセス起動する実装になっており、PyInstallerで凍結すると
  `sys.executable` がフリーズされたバイナリ自身を指してしまい、OCRの
  サブプロセス起動が壊れる
  - ただし `core/ocr_engine.py` で `sys.frozen` 判定によりシステムの `python3` を
    使うフォールバックを実装済みのため、PyInstaller 化も可能
- tkinter/customtkinter・opencv・numpyを含むPyInstallerビルドはmacOSで
  不安定になりやすく、ビルドサイズも数百MB〜1GB超になりがち
- venv方式は元のWindows版（`book_env` + `run.bat`）とアーキテクチャが
  同じで、保守しやすい

### 開発機での起動（配布不要な場合）

```bash
cd book2pdf_mac
book_env/bin/python3 app.py
```

## 他のMacに配布する場合

配布先のMacにも同じセットアップが必要です。[../user/setup.md](../user/setup.md)
の手順をそのまま実行してください。

```bash
brew install python@3.12 python-tk@3.12
cd book2pdf_mac
/opt/homebrew/bin/python3.12 -m venv book_env
book_env/bin/pip install -r requirements.txt
git clone https://github.com/ndl-lab/ndlocr-lite.git   # OCRを使うなら
book_env/bin/pip install -r ndlocr-lite/requirements.txt
```

`book_env/` フォルダ自体はPythonのフルパスや共有ライブラリへの絶対パス
参照を含むため、**フォルダごとコピーして別Macで使い回すことはできません**。
必ず配布先で `venv` を作り直してください。

## ダブルクリックで起動できるようにする（run.sh / .command）

`run.bat` 相当として、シンプルなシェルスクリプトを用意すると便利です。

```bash
#!/bin/bash
cd "$(dirname "$0")"
book_env/bin/python3 app.py
```

これを `run.command` として保存し実行権限を付与すると
（`chmod +x run.command`）、Finderからダブルクリックで起動できます。

## スタンドアロン .app ビルド（PyInstaller）

`docs/operations/pyinstaller-build.md` に、PyInstaller で `.app` 化する
手順をまとめています。以下の対応は実施済みです。

- [x] `core/ocr_engine.py` の `_build_command()` を `sys.frozen` 判定で
  分岐させ、凍結環境ではシステムの `python3` を使用するよう修正済み
- [x] `build-mac.spec` を作成し、customtkinter・PIL・cv2・numpy・pyobjc
  を含むビルドが成功（サイズ約 60 MB）
- [x] `build-mac.spec` は `platform.machine()` で Apple Silicon / Intel を自動判定
- [x] NDLOCR-Lite は同梱せず、未インストール時は OCR タブが無効化される

ビルド済み `.app` は `dist/book2pdf.app` に出力されます。
配布時には Gatekeeper 回避のためのコードサイン（Developer ID）が必要です。

Intel Mac でビルドする場合、通常は `build-mac.spec` の自動判定で `x86_64` が
選択されます。強制的に指定する場合は `.spec` 内の `target_arch` を編集してください。
