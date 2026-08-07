# 01-design.md — book2pdf 設計・技術選定

## アプリの目的

音声読み上げに対応していない 電子書籍 書籍に対し、目で読みながら耳でも聞けるように、**スクリーンショット連続撮影 → トリミング → OCR → PDF/Markdown 変換**を行う個人学習用ツール。

## 機能概要

- **入力源**: 電子書籍アプリの自動キャプチャ、または既存 PDF からの画像展開
- **加工**: 余白トリミング
- **出力**: 画像 PDF / テキスト PDF / 検索可能 PDF / Markdown / 画像＋テキスト PDF
- **GUI**: 4 タブ構成（キャプチャ / PDF 読込 / トリミング / 変換）
- **対象 OS**: Windows 11 / macOS
  - macOS は Apple Silicon / Intel 両方を対象とする
  - 開発・検証環境は Apple Silicon（Intel Mac は `build-mac.spec` のアーキテクチャ自動判定で対応可能）

## 技術選定（変更禁止）

| 用途 | ライブラリ | 備考 |
|------|-----------|------|
| Python | 3.11〜3.13 | 依存パッケージのビルド済み wheel が安定している範囲 |
| GUI | `customtkinter` | ダークモード対応、tkinter 上位互換 |
| 画像処理 | `opencv-python`, `numpy`, `Pillow` | 画面比較・境界検出は OpenCV/numpy、I/O は Pillow |
| PDF 生成 | `reportlab` | 日本語 CID フォント（HeiseiMin-W3）を使用 |
| PDF 読込 | `pypdfium2` | NDLOCR-Lite と依存が共通 |
| 自動操作 | `pyautogui` | キー送信・マウス操作。Windows/macOS 両対応 |
| Windows 専用 | `ctypes` (`windll`) | `core/platform/windows_utils.py` に隔離 |
| macOS 専用 | `pyobjc-framework-Quartz`, `pyobjc-framework-Cocoa`, `pyobjc-framework-ApplicationServices` | `core/platform/macos_utils.py` に隔離 |
| OCR | NDLOCR-Lite（外部リポジトリ、サブプロセス起動） | GPU 不要、CPU 実行前提。将来のエンジン追加に備えた抽象化も用意 |
| ビルド | PyInstaller | macOS `.app` / Windows `.exe` のスタンドアロン配布。開発時は `venv` + `python app.py` |
| lint | `ruff` | target-version = "py311", line-length = 100 |

技術選定を変更する場合は、必ず理由をコメントまたはコミットメッセージに残すこと。

## アーキテクチャ原則

### core/ と ui/ の分離

```
core/            UI 非依存のロジック。tkinter/customtkinter を import しない
ui/              4 タブの GUI。core/ の関数を呼び出すだけで業務ロジックを持たない
core/platform/   OS 依存コードをここに隔離
```

`core/` 配下の全モジュールは、GUI なしで単体スクリプトまたは `python -m` から直接動作確認できる設計にすること。

### 関数インターフェースの統一

- 進捗通知: `on_progress(current: int, total: int, filename: str)` コールバック
- 処理結果: `(success: bool, message_or_data)` のタプル
- 例外を握りつぶす場合は、必ず呼び出し側にエラーメッセージとして伝播させる

### タブ間の状態共有

`ui/state.py` に `AppState` クラスを作り、Observer パターン（`add_listener` / `notify(event, data)`）で連携する。直接他タブのウィジェットを参照しないこと。

主要イベント:

- `capture_complete`: キャプチャ完了または PDF 展開完了時に発行。画像フォルダのパスを `data` に含める
- `trim_complete`: トリミング完了時に発行。出力フォルダのパスを `data` に含める

### 設定管理

`core/config.py` に `DEFAULT_CONFIG`（dict）を定義し、`config.json` の内容を非破壊 deep merge して読み込む。未知のキーは無視し、欠けているキーはデフォルト値で補完すること。

### プラットフォーム分岐

`core/capture_engine.py` など呼び出し側は OS 判定コードを含まない。`core/platform/__init__.py` が `sys.platform` を見て適切なモジュールを re-export する。

## コーディングスタイル

- lint: `ruff`, target-version = "py311", line-length = 100
- 選択ルール: `E`, `F`, `W`, `I`, `UP`, `B`, `SIM`
- クオート: ダブルクオート
- インデント: スペース 4 つ
- コメントは「なぜそうしたか」のみ。変数名・関数名で「何をしているか」を自明にする
- docstring は日本語で、モジュール冒頭に用途と設計意図を簡潔に書く

## セキュリティ・プライバシー

- 外部ネットワーク通信を行わない（OCR 初回セットアップ時の git clone を除く）
- 画面収録・入力自動化の権限を必要とする旨を README と UI に明記
- キャプチャ中はマウス・キーボード操作が干渉する可能性がある旨を明記
- 設定ファイル `config.json` はバージョン管理対象外とする（`.gitignore` に追加）
