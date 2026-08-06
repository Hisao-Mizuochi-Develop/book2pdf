# 10-run.md — 開発進行プロンプト（マスター指示）

## あなたへの指示

あなたは Cline です。以下の手順に従い、book2pdf を 0 から VibeCoding してください。

## 実装前に必ず読み込むファイル

以下の順序で全ファイルを読み込んでください。

1. `00-design.md` — アーキテクチャ・技術選定・設計原則
2. `11-pitfalls.md` — 過去の実装で発生した不具合と回避策
3. `12-testing.md` — テスト戦略と観点
4. `13-distribution.md` — 配布ビルド方針

## 実装フェーズ

以下の順序で実装を進めてください。各フェーズ終了時は必ず該当するテストと受け入れ確認を行うこと。

### Phase 1: セットアップ

`01-setup.md` に従い、プロジェクト構造と依存関係を構築する。

完了条件:
- `python app.py` で GUI が起動する
- `ruff check .` がパスする
- `pytest tests/test_basic.py` がパスする

### Phase 2: プラットフォーム抽象化層

`02-platform.md` に従い、`core/platform/` を実装する。

完了条件:
- Windows/macOS 両方で共通シグネチャを持つ
- 実機で `find_window` / `activate_window` / `is_window_frontmost` が動作する
- `tests/test_platform.py`（新規作成）がパスする

### Phase 3: キャプチャエンジン

`03-capture.md` に従い、`core/capture_profiles.py`、`core/boundary_detector.py`、`core/capture_engine.py` を実装する。

完了条件:
- 実際の電子書籍アプリで 6 ページ程度の連続自動キャプチャが成功する
- 同一ページが量産されない
- 最前面監視が機能する

### Phase 4: PDF 読込

`04-pdf-load.md` に従い、`core/pdf_extractor.py` と `ui/pdf_load_tab.py` を実装する。

完了条件:
- PDF 展開後に画像フォルダが自動引き継がれる
- DPI/形式指定が反映される

### Phase 5: トリミング

`05-trim.md` に従い、`core/trimmer.py` と `ui/trim_tab.py` を実装する。

完了条件:
- 自動検出で安全マージン付きの余白が提示される
- before/after プレビューが正しい

### Phase 6: OCR パイプライン

`06-ocr.md` に従い、OCR 関連モジュールを実装する。

完了条件:
- NDLOCR-Lite 未導入時の警告が表示される
- 前処理・置換・段落整形・章検出が機能する

### Phase 7: 変換・出力

`07-convert.md` に従い、`core/pdf_builder.py` と `core/markdown_writer.py` を実装する。

完了条件:
- 5 出力形式すべてが正常に生成される
- 各形式の受け入れ条件を満たす

### Phase 8: GUI

`08-gui.md` に従い、4 タブ GUI を実装する。

- 各タブ実装前に、Cline は 2〜3 パターンのデザイン案をユーザーに提示する
- ユーザーが選択したデザイン案に基づいて実装する
- タブ間連携は `AppState` の Observer パターンで行う

完了条件:
- アプリが正常に起動・動作する
- タブ間でフォルダが自動引き継がれる

### Phase 9: 最終確認

- `09-acceptance.md` の全項目を実機で確認する
- `ruff check .` と `pytest` を実行する
- `13-distribution.md` に従って配布ビルドを作成する

## 開発中の留意事項

- 不明点があれば、実装を止めてユーザーに確認すること
- 静的解析（ruff）は各フェーズ終了時に必ず実行すること
- 実機確認が必要なフェーズ（特に Phase 2, 3）は、コードレビューだけで「完了」としないこと
- GUI の詳細なレイアウトはユーザー確認を経てから実装すること
- OCR エンジンの追加・変更は `docs/operations/ocr-engines.md` に反映すること

## テストコマンド

```bash
ruff check .
ruff format --check .
pytest tests/ -q
```
