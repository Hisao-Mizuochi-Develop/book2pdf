# ビルド・配布手順書

## 採用した方式: venvベースの .app ランチャー

kindle2pdf macOS版は、PyInstaller等によるフルスタンドアロン化ではなく、
**venv（仮想環境）を前提とした起動方式**を採用しています。

### 採用理由

- OCR機能（NDLOCR-Lite）が `sys.executable`（実行中のPythonインタプリタ）を
  使ってサブプロセス起動する実装になっており、PyInstallerで凍結すると
  `sys.executable` がフリーズされたバイナリ自身を指してしまい、OCRの
  サブプロセス起動が壊れる
- tkinter/customtkinter・opencv・numpyを含むPyInstallerビルドはmacOSで
  不安定になりやすく、ビルドサイズも数百MB〜1GB超になりがち
- venv方式は元のWindows版（`kindle_env` + `run.bat`）とアーキテクチャが
  同じで、保守しやすい

### 開発機での起動（配布不要な場合）

```bash
cd kindle2pdf_mac
kindle_env/bin/python3 app.py
```

## 他のMacに配布する場合

配布先のMacにも同じセットアップが必要です。[../user/setup.md](../user/setup.md)
の手順をそのまま実行してください。

```bash
brew install python@3.12 python-tk@3.12
cd kindle2pdf_mac
/opt/homebrew/bin/python3.12 -m venv kindle_env
kindle_env/bin/pip install -r requirements.txt
git clone https://github.com/ndl-lab/ndlocr-lite.git   # OCRを使うなら
kindle_env/bin/pip install -r ndlocr-lite/requirements.txt
```

`kindle_env/` フォルダ自体はPythonのフルパスや共有ライブラリへの絶対パス
参照を含むため、**フォルダごとコピーして別Macで使い回すことはできません**。
必ず配布先で `venv` を作り直してください。

## ダブルクリックで起動できるようにする（run.sh / .command）

`run.bat` 相当として、シンプルなシェルスクリプトを用意すると便利です。

```bash
#!/bin/bash
cd "$(dirname "$0")"
kindle_env/bin/python3 app.py
```

これを `run.command` として保存し実行権限を付与すると
（`chmod +x run.command`）、Finderからダブルクリックで起動できます。

## 将来PyInstaller化する場合の注意点

もし将来的にワンファイルの `.app` 化を検討する場合は、以下の対応が
必要になります（未実施）。

1. `core/ocr_engine.py` の `_build_command()` が `sys.executable` を
   使っている箇所を、凍結環境かどうかで分岐させる
   （`sys.frozen` 判定 + 実際のPythonインタプリタパスを別途保持する等）
2. tkinter/customtkinter・opencv・numpy・pyobjc を含むビルドの動作確認
   （`--collect-all` や `--hidden-import` の調整が広範囲に必要になりがち）
3. NDLOCR-Lite自体は同梱せず、初回起動時に別途セットアップさせる設計を
   維持するかどうかの判断（同梱するとビルドサイズが大幅に増える）
