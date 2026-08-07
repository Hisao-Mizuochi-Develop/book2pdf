# PromptEngineering

このディレクトリには、熟練したソフトウェアエンジニアの AI コーディングアシスタントに book2pdf を **0 から実装させるためのプロンプト**が含まれています。

## AI にプロンプトを投入する手順

VibeCoding プロンプトを以下の順番で 1 つずつ AI に渡してください。

1. 'PromptEngineering/VibeCoding/00-master.md' (see below for file content) — 開発進行プロンプト（マスター指示）
2. 'PromptEngineering/VibeCoding/01-design.md' (see below for file content) — book2pdf 設計・技術選定
3. 'PromptEngineering/VibeCoding/02-pitfalls.md' (see below for file content) — 既知の落とし穴と回避策
4. 'PromptEngineering/VibeCoding/03-testing.md' (see below for file content) — テスト戦略・観点
5. 'PromptEngineering/VibeCoding/04-distribution.md' (see below for file content) — 配布ビルド手順
6. 'PromptEngineering/VibeCoding/05-setup.md' (see below for file content) — 環境構築・プロジェクトセットアップ
7. 'PromptEngineering/VibeCoding/06-platform.md' (see below for file content) — Windows/macOS プラットフォーム抽象化層
8. 'PromptEngineering/VibeCoding/07-capture.md' (see below for file content) — 自動キャプチャエンジン
9. 'PromptEngineering/VibeCoding/08-pdf-load.md' (see below for file content) — PDF 読込・画像展開
10. 'PromptEngineering/VibeCoding/09-trim.md' (see below for file content) — トリミング・余白検出
11. 'PromptEngineering/VibeCoding/10-ocr.md' (see below for file content) — OCR パイプライン
12. 'PromptEngineering/VibeCoding/11-convert.md' (see below for file content) — 変換・出力生成
13. 'PromptEngineering/VibeCoding/12-gui.md' (see below for file content) — タブベース GUI
14. 'PromptEngineering/VibeCoding/13-acceptance.md' (see below for file content) — 完成判定チェックリスト

## 注意点

- 'PromptEngineering/VibeCoding/12-gui.md' (see below for file content) の段階では、熟練したソフトウェアエンジニアの AI コーディングアシスタントが複数案を提示します。ユーザーが選択した案を指示してから次に進んでください。
- 各フェーズ終了時は、必ず 'PromptEngineering/VibeCoding/03-testing.md' (see below for file content) の該当単体テストと 'PromptEngineering/VibeCoding/13-acceptance.md' (see below for file content) の該当項目を実施させてください。
- OCR エンジンの追加・変更については `docs/operations/ocr-engines.md` を参照・更新してください。
- 配布ビルドは macOS の `.app` と Windows の `.exe` に対応しますが、ビルド自体は各 OS 上で行う必要があります。

---

## ファイル一覧

### 全体プロンプト（参考）

| ファイル | 内容 |
|---------|------|
| `PROMPT.md` | ゼロからの実装指示（マスタープロンプト） |
| `CLAUDE.md` | コーディング規約・技術選定・アーキテクチャ原則 |
| `REQUIREMENTS.md` | 4 タブ・全設定項目・5 出力形式の詳細機能要件 |
| `CROSS_PLATFORM.md` | Windows/macOS 両対応の抽象化レイヤー設計 |
| `PITFALLS.md` | 過去の実装で発生した不具合と回避策 |
| `ACCEPTANCE_TESTS.md` | 完成判定のための実機動作確認チェックリスト |

### VibeCoding プロンプト

| ファイル | 内容 |
|---------|------|
| 'PromptEngineering/VibeCoding/00-master.md' (see below for file content) | 開発進行プロンプト（マスター指示） |
| 'PromptEngineering/VibeCoding/01-design.md' (see below for file content) | book2pdf 設計・技術選定 |
| 'PromptEngineering/VibeCoding/02-pitfalls.md' (see below for file content) | 既知の落とし穴と回避策 |
| 'PromptEngineering/VibeCoding/03-testing.md' (see below for file content) | テスト戦略・観点 |
| 'PromptEngineering/VibeCoding/04-distribution.md' (see below for file content) | 配布ビルド手順 |
| 'PromptEngineering/VibeCoding/05-setup.md' (see below for file content) | 環境構築・プロジェクトセットアップ |
| 'PromptEngineering/VibeCoding/06-platform.md' (see below for file content) | Windows/macOS プラットフォーム抽象化層 |
| 'PromptEngineering/VibeCoding/07-capture.md' (see below for file content) | 自動キャプチャエンジン |
| 'PromptEngineering/VibeCoding/08-pdf-load.md' (see below for file content) | PDF 読込・画像展開 |
| 'PromptEngineering/VibeCoding/09-trim.md' (see below for file content) | トリミング・余白検出 |
| 'PromptEngineering/VibeCoding/10-ocr.md' (see below for file content) | OCR パイプライン |
| 'PromptEngineering/VibeCoding/11-convert.md' (see below for file content) | 変換・出力生成 |
| 'PromptEngineering/VibeCoding/12-gui.md' (see below for file content) | タブベース GUI |
| 'PromptEngineering/VibeCoding/13-acceptance.md' (see below for file content) | 完成判定チェックリスト |
