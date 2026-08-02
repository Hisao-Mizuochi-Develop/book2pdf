# PROMPT.md — kindle2pdf ゼロからの実装指示

あなたはClaude Codeです。以下の指示に従い、kindle2pdf をゼロから実装してください。
このディレクトリ（`PromptEngineering/`）には、あなたが従うべき詳細ドキュメントが
揃っています。**実装を始める前に、必ず以下の順序で全ファイルを読み込んでください。**

1. `CLAUDE.md` — コーディング規約・技術選定・アーキテクチャ原則
2. `REQUIREMENTS.md` — 4タブ・全設定項目・5出力形式の詳細機能要件
3. `CROSS_PLATFORM.md` — Windows/macOS両対応のための抽象化レイヤー設計
4. `PITFALLS.md` — 過去の実装で実際に発生した不具合と、その回避策
5. `ACCEPTANCE_TESTS.md` — 完成判定のための実機動作確認チェックリスト

## アプリの一行要約

電子書籍のスクリーンキャプチャ・PDF読込・トリミング・PDF変換・OCRを
1つのGUIアプリ（4タブ: キャプチャ / PDF読込 / トリミング / 変換）で行う、
Windows・macOS両対応の個人学習用ツール。

## 実装の進め方

`CLAUDE.md` の「開発の進め方」セクションに従い、以下の順で実装してください。
**各段階で `ACCEPTANCE_TESTS.md` の該当項目を実機確認してから次に進んでください。**
特にウィンドウ自動操作まわり（キャプチャ機能）は、実機で複数ページの
自動キャプチャが成功することを確認しない限り「完了」と判断しないでください。

1. **プラットフォーム抽象化層**（`core/platform/`）
   `CROSS_PLATFORM.md` の共通インターフェース仕様に従い、Windows実装
   （`ctypes`+`windll`）とmacOS実装（`pyobjc`）を同時並行で設計してください。
   この段階で `PITFALLS.md` の1〜2番（ウィンドウ誤検出、信号機ボタン誤操作）を
   踏まえた実装にしてください。

2. **キャプチャエンジン**（`core/capture_engine.py`）
   `REQUIREMENTS.md` の「キャプチャアルゴリズム」に従って実装してください。
   `PITFALLS.md` の3〜6番（誤ページ判定、ページめくり失敗、画面ロック対策）を
   最初から組み込んでください。実機の電子書籍アプリで6ページ程度の連続
   自動キャプチャが成功し、かつ生成画像が実際に異なるページ内容であることを
   目視確認してください。

3. **画像処理系**（`core/trimmer.py`, `core/boundary_detector.py`,
   `core/pdf_extractor.py`）
   `REQUIREMENTS.md` のタブ2・タブ3の仕様に従ってください。

4. **OCRパイプライン**（`core/ocr_engine.py`, `core/ocr_preprocess.py`,
   `core/text_replacements.py`, `core/text_reflow.py`, `core/chapter_detector.py`）
   OCRエンジンはNDLOCR-Lite（外部リポジトリ、サブプロセス起動）を使用してください。
   `PITFALLS.md` の7番（フリーズ環境での`sys.executable`問題）に留意し、
   将来の配布方式変更に対して脆弱にならない設計にしてください。

5. **出力生成**（`core/pdf_builder.py`, `core/markdown_writer.py`）
   `REQUIREMENTS.md` の5出力形式すべてを実装してください。
   「画像+テキストPDF」（見開き型: 画像ページ→OCRテキストページの繰り返し）を
   含めることを忘れないでください。

6. **GUI**（`ui/` 配下4タブ + `ui/state.py` + `ui/main_window.py`）
   `core/` が固まってから着手してください。`customtkinter` を使用し、
   タブ間の連携は `AppState` の Observer パターンで行ってください
   （直接他タブを参照しないでください）。

7. **最終確認**
   `ACCEPTANCE_TESTS.md` の全項目を、Windows・macOS両方の実機で確認してください。
   実機が片方しか用意できない場合は、その旨を明示した上で、少なくとも
   `core/platform/` の両実装がコードレベルで対称な設計になっていることを
   確認してください。

## 成果物に含めるべきファイル

- `app.py`（エントリーポイント）
- `core/`, `ui/` 一式
- `requirements.txt` / `pyproject.toml`（依存パッケージ、`CLAUDE.md` の技術選定に準拠）
- `config.example.json`（設定ファイルの雛形）
- `README.md`（セットアップ手順・使い方。Windows/macOS両方の手順を含める）
- OS別の起動スクリプト（Windows: `setup.bat`/`run.bat` 相当、macOS: セットアップ手順+
  `run.sh` 等。`CROSS_PLATFORM.md` を踏まえ、venvベースの起動を基本とする）

## 質問がある場合

要件が曖昧な箇所（例: 対応する電子書籍アプリの追加、UIの細かいレイアウト）に
ついては、実装を止めてユーザーに確認してください。ただし
`CROSS_PLATFORM.md` の抽象化設計や `PITFALLS.md` の回避策など、
**過去の実装で既に結論が出ている事項については再度確認を取らず、そのまま
仕様として採用してください。**
