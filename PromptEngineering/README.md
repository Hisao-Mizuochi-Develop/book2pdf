# PromptEngineering

このディレクトリには、熟練したソフトウェアエンジニアの AI コーディングアシスタントに book2pdf を **0 から実装させるためのプロンプト**が含まれています。

## AI にプロンプトを投入する手順

1. **入り口ファイルを読み込ませる**
   まず `./PromptEngineering/README.md`（本ファイル）を AI に読み込ませます。

2. **VibeCoding フェーズを順番に実行する**
   以下のファイルを 1 つずつ AI に渡してください。

   1. 'PromptEngineering/VibeCoding/00-design.md' (see below for file content) — アーキテクチャ・技術選定・設計原則
   2. 'PromptEngineering/VibeCoding/11-pitfalls.md' (see below for file content) — 過去の実装で発生した不具合と回避策
   3. 'PromptEngineering/VibeCoding/12-testing.md' (see below for file content) — テスト戦略と観点
   4. 'PromptEngineering/VibeCoding/13-distribution.md' (see below for file content) — 配布ビルド方針
   5. 'PromptEngineering/VibeCoding/01-setup.md' (see below for file content) — 環境構築、依存導入、run.sh/run.bat
   6. 'PromptEngineering/VibeCoding/02-platform.md' (see below for file content) — Windows/macOS プラットフォーム抽象化層
   7. 'PromptEngineering/VibeCoding/03-capture.md' (see below for file content) — 自動キャプチャエンジン、プロファイル
   8. 'PromptEngineering/VibeCoding/04-pdf-load.md' (see below for file content) — PDF → 画像展開
   9. 'PromptEngineering/VibeCoding/05-trim.md' (see below for file content) — 余白検出、トリミング
   10. 'PromptEngineering/VibeCoding/06-ocr.md' (see below for file content) — OCR 抽象化、NDLOCR-Lite 連携、前後処理
   11. 'PromptEngineering/VibeCoding/07-convert.md' (see below for file content) — 5 出力形式の PDF/Markdown 生成
   12. 'PromptEngineering/VibeCoding/08-gui.md' (see below for file content) — タブベース GUI
   13. 'PromptEngineering/VibeCoding/09-acceptance.md' (see below for file content) — 実機受け入れチェックリスト
   14. 'PromptEngineering/VibeCoding/10-run.md' (see below for file content) — 開発進行プロンプト（マスター指示）

3. **GUI デザインの確認**
   'PromptEngineering/VibeCoding/08-gui.md' (see below for file content) の段階では、熟練したソフトウェアエンジニアの AI コーディングアシスタントが複数案を提示します。ユーザーが選択した案を指示してから次に進んでください。

4. **テストと受け入れ確認**
   各フェーズ終了時は、必ず 'PromptEngineering/VibeCoding/12-testing.md' (see below for file content) の該当単体テストと 'PromptEngineering/VibeCoding/09-acceptance.md' (see below for file content) の該当項目を実施させてください。

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
| 'PromptEngineering/VibeCoding/00-design.md' (see below for file content) | アーキテクチャ、技術選定、設計原則 |
| 'PromptEngineering/VibeCoding/01-setup.md' (see below for file content) | 環境構築、依存導入、run.sh/run.bat |
| 'PromptEngineering/VibeCoding/02-platform.md' (see below for file content) | Windows/macOS プラットフォーム抽象化層 |
| 'PromptEngineering/VibeCoding/03-capture.md' (see below for file content) | 自動キャプチャエンジン、プロファイル |
| 'PromptEngineering/VibeCoding/04-pdf-load.md' (see below for file content) | PDF → 画像展開 |
| 'PromptEngineering/VibeCoding/05-trim.md' (see below for file content) | 余白検出、トリミング |
| 'PromptEngineering/VibeCoding/06-ocr.md' (see below for file content) | OCR 抽象化、NDLOCR-Lite 連携、前後処理 |
| 'PromptEngineering/VibeCoding/07-convert.md' (see below for file content) | 5 出力形式の PDF/Markdown 生成 |
| 'PromptEngineering/VibeCoding/08-gui.md' (see below for file content) | タブベース GUI |
| 'PromptEngineering/VibeCoding/09-acceptance.md' (see below for file content) | 実機受け入れチェックリスト |
| 'PromptEngineering/VibeCoding/10-run.md' (see below for file content) | 開発進行プロンプト（マスター指示） |
| 'PromptEngineering/VibeCoding/11-pitfalls.md' (see below for file content) | 既知の落とし穴と回避策 |
| 'PromptEngineering/VibeCoding/12-testing.md' (see below for file content) | テスト戦略・観点 |
| 'PromptEngineering/VibeCoding/13-distribution.md' (see below for file content) | PyInstaller ローカルビルド手順 |

## 補足

- GUI のタブ内部デザインは 'PromptEngineering/VibeCoding/08-gui.md' (see below for file content) の指示に従い、熟練したソフトウェアエンジニアの AI コーディングアシスタントが複数案を提案しユーザー確認を得てから実装します。
- OCR エンジンの追加・変更については `docs/operations/ocr-engines.md` を参照・更新してください。
- 配布ビルドは macOS の `.app` と Windows の `.exe` に対応しますが、ビルド自体は各 OS 上で行う必要があります。
