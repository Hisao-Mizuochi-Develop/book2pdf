# CLAUDE.md — book2pdf 実装規約

このファイルは、book2pdf をゼロから実装する 熟練したソフトウェアエンジニアの AI コーディングアシスタント に対する恒常的な
振る舞い指示です。`PROMPT.md` と併せて読み込ませてください。

## プロジェクトの性質

電子書籍のスクリーンキャプチャ・PDF読込・トリミング・PDF変換・OCR統合ツール。
**Windows と macOS の両方で動作すること**が必須要件です。Linux対応は不要です。

## 技術選定（このバージョンを使うこと）

| 用途 | ライブラリ | 備考 |
|------|-----------|------|
| Python | 3.11〜3.13 | 依存パッケージ（numpy, Pillow, opencv）がこの範囲のみビルド済みwheelを配布 |
| GUI | `customtkinter` | 標準tkinterの上位互換。ダークモード等の見た目を統一しやすい |
| 画像処理 | `opencv-python`, `numpy`, `Pillow` | 画面比較・境界検出はopencv/numpy、画像I/OはPillow |
| PDF生成 | `reportlab` | 日本語CIDフォント（`HeiseiMin-W3`）を使うこと |
| PDF読込 | `pypdfium2` | NDLOCR-Liteとも依存が共通のため統一 |
| 自動操作 | `pyautogui` | キー送信・マウス操作。Windows/macOS両対応 |
| Windows専用 | `ctypes` (`windll`) | Win32 API直叩き（`core/platform/windows_utils.py` に隔離） |
| macOS専用 | `pyobjc-framework-Quartz`, `pyobjc-framework-Cocoa`, `pyobjc-framework-ApplicationServices` | ウィンドウ検出・前面化・権限確認（`core/platform/macos_utils.py` に隔離） |
| OCR | NDLOCR-Lite（外部リポジトリ、サブプロセス起動） | GPUなし・CPU実行前提。`onnxruntime` ベース |

このバージョン選定から外れる場合（新しいライブラリへの置き換え等）は、必ず
理由をコミットメッセージまたはコメントに残すこと。

## アーキテクチャ原則

### 1. core/ と ui/ の分離

```
core/       UI非依存のロジック。tkinter/customtkinterをimportしない
ui/         4タブのGUI。core/の関数を呼ぶだけで業務ロジックを持たない
core/platform/  OS依存コードをここに隔離（詳細はCROSS_PLATFORM.md）
```

`core/` 配下の全モジュールは、GUIなしで単体スクリプトから直接呼び出して
動作確認できる設計にすること（実際に本アプリでは `core/text_reflow.py` が
`python -m core.text_reflow` としてCLI実行できる）。

### 2. 関数インターフェースの統一

- 進捗通知は `on_progress(current: int, total: int, filename: str)` コールバックで統一する
- 処理結果は `(success: bool, message_or_data)` のタプルで返す
- 例外を握りつぶす場合は、呼び出し側にエラーメッセージとして伝播させること
  （サイレントに失敗させない）

### 3. タブ間の状態共有

`ui/state.py` に `AppState` クラスを作り、Observerパターン（`add_listener` /
`notify(event, data)`）でタブ間の連携を行う。直接他タブのウィジェットを
参照するコードを書かないこと。

イベント例:
- `capture_complete`: キャプチャタブ・PDF読込タブの両方が発行する共通イベント
  （どちらも「画像フォルダを用意する」という同じ役割のため）
- `trim_complete`: トリミングタブが発行

### 4. 設定管理

`core/config.py` に `DEFAULT_CONFIG`（dict）を定義し、`config.json` の内容を
非破壊マージ（deep merge）して読み込む。未知のキーは無視し、欠けているキーは
デフォルト値で補う設計にすること（過去バージョンとの互換性を保つため）。

### 5. プラットフォーム分岐

**必ず最初から抽象化すること。** 「まずWindows版を作って後でMac対応する」
というアプローチは取らないこと（このアプローチで作られた過去バージョンは
移植コストが高く、複数の実機デバッグが必要になった）。詳細設計は
`CROSS_PLATFORM.md` を参照。

## コーディングスタイル

- lintは `ruff`（`target-version = "py311"`, `line-length = 100`）
- ルール: `E`, `F`, `W`, `I`（isort）, `UP`（pyupgrade）, `B`（bugbear）, `SIM`
- クオートはダブルクオート、インデントはスペース
- コメントは「なぜそうしたか」だけを書く。「何をしているか」は書かない
  （変数名・関数名で自明にする）
- docstringは日本語で、モジュール冒頭に用途と設計意図を簡潔に書く

## 開発の進め方（推奨順序）

1. `core/platform/` の抽象化レイヤーを最初に設計・実装し、Windows/macOS
   両方で「ウィンドウ検出→前面化→スクリーンショット→キー送信」の
   最小疎通を確認する
2. `core/capture_engine.py`（自動キャプチャの中核ロジック）を実装し、
   実機（実際の電子書籍アプリ）で複数ページの自動キャプチャが成功することを確認
3. `core/trimmer.py`, `core/boundary_detector.py`（トリミング・境界検出）
4. `core/pdf_extractor.py`（PDF読込）
5. `core/ocr_engine.py`, `core/ocr_preprocess.py`, `core/text_replacements.py`,
   `core/text_reflow.py`, `core/chapter_detector.py`（OCRパイプライン）
6. `core/pdf_builder.py`, `core/markdown_writer.py`（出力生成）
7. `ui/` 配下の4タブ（`core/` が固まってから着手する）

各ステップの完了条件は `ACCEPTANCE_TESTS.md` を参照。特にステップ1・2は
実機での動作確認なしに「完了」と判断しないこと（GUI自動操作系のバグは
コードレビューだけでは発見できない）。

## 参照すべき他ファイル

- `PROMPT.md` — 実装を開始するための指示プロンプト本体
- `REQUIREMENTS.md` — 4タブ・全設定項目・5出力形式の詳細仕様
- `CROSS_PLATFORM.md` — Windows/macOS抽象化レイヤーの設計
- `PITFALLS.md` — 過去の実装で実際に発生した不具合と回避策
- `ACCEPTANCE_TESTS.md` — 完成判定のための動作確認チェックリスト
