# macOS へのインストール方法

本文書では、`book2pdf-mac` を macOS にインストールする 2 つの方法を解説します。

## 方法 A：スタンドアロンアプリとしてインストール（推奨・簡単）

PyInstaller でビルド済みの `.app` バンドルを使用します。Python や仮想環境の知識が不要です。

### 前提条件
- macOS 12 (Monterey) 以降
- Apple Silicon Mac (Intel Mac は別途ビルドが必要)

### 手順

1. **`book2pdf-macos-arm64.tar.gz` をダウンロード**
2. **展開してアプリケーションフォルダに配置**

```bash
# ダウンロードした tar.gz を展開
tar xzf book2pdf-macos-arm64.tar.gz

# アプリケーションフォルダにコピー
cp -R book2pdf.app ~/Applications/
```

または Finder で `book2pdf.app` を **アプリケーションフォルダ** にドラッグ＆ドロップ。

3. **起動**

Finder → アプリケーション → `book2pdf.app` をダブルクリック。

初回起動時に「開発元が未確認のため開けません」と表示された場合：
- **システム設定 → プライバシーとセキュリティ → セキュリティ** の欄に「book2pdf.app」を開くためのボタンが表示されます。そこをクリックして「このまま開く」を選択。

4. **OCR 機能を使う場合（オプション）**

`book2pdf` 本体は NDLOCR-Lite なしでも動作しますが、OCR 機能を使う場合は別途セットアップが必要です。

```bash
# システム Python3 に NDLOCR-Lite の依存をインストール
/usr/bin/python3 -m pip install --user onnxruntime opencv-python torch numpy pillow

# NDLOCR-Lite をアプリ内に配置
git clone https://github.com/ndl-lab/ndlocr-lite.git ~/Applications/book2pdf.app/Contents/Resources/ndlocr-lite
```

---

## 方法 B：開発環境としてインストール（ソースコードから実行）

仮想環境を作成して Python ソースコードから実行します。開発やカスタマイズを行う場合に適しています。

### 前提条件

| 要件 | バージョン |
|------|-----------|
| Python | >= 3.11 |
| Homebrew | インストール済 |
| Git | インストール済 |

### 手順

1. **Homebrew で Python と tkinter をインストール**

```bash
brew install python@3.12 python-tk@3.12
```

2. **リポジトリをクローン**

```bash
git clone git@github.com:Hisao-Mizuochi-Develop/book2pdf.git
cd book2pdf
```

3. **仮想環境を作成して依存パッケージをインストール**

```bash
# 仮想環境作成
/opt/homebrew/bin/python3.12 -m venv book_env

# 有効化
source book_env/bin/activate

# 依存パッケージインストール
pip install -r requirements.txt
```

4. **OCR 機能を使う場合（オプション）**

```bash
# NDLOCR-Lite をクローン
git clone https://github.com/ndl-lab/ndlocr-lite.git

# NDLOCR-Lite の依存をインストール
pip install -r ndlocr-lite/requirements.txt
```

5. **起動**

```bash
book_env/bin/python app.py
```

または仮想環境を有効化して：

```bash
source book_env/bin/activate
python app.py
```

---

## 方法の比較

| 項目 | 方法 A（スタンドアロン） | 方法 B（開発環境） |
|------|----------------------|----------------|
| 必要な知識 | なし（コマンド不要） | Python, pip, venv |
| インストール時間 | 数秒（展開のみ） | 5〜15分（pip install） |
| ディスク容量 | 約 60 MB | 仮想環境含め約 200 MB〜 |
| Python | 不要 | 3.11 以上が必要 |
| カスタマイズ | 不可 | 可能 |
| アップデート | tar.gz を差し替え | `git pull` |
| OCR 機能 | 別途セットアップ必要 | 別途セットアップ必要 |

---

## アンインストール

### 方法 A（スタンドアロン）
```bash
rm -rf ~/Applications/book2pdf.app
```

### 方法 B（開発環境）
```bash
# 仮想環境とリポジトリを削除
rm -rf book2pdf/
```
