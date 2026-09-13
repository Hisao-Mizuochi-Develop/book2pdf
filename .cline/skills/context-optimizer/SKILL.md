---
name: context-optimizer
description: |
  Optimize and cleanse LLM token context length for the book2pdf project.
  Prevents token overflow and reasoning loops by generating internal summaries and clearing dead history.
  Supports both autonomous execution and explicit manual command (`/context`, `/clean`) invocations.
compatibility: VS Code + Cline
metadata:
  author: book2pdf-team
  version: "1.0"
---

# context-optimizer

## 1. 起動トリガー / コマンド定義
本スキルは、以下のいずれかのタイミングで起動されます。

- **A. 個別呼び出し（スラッシュコマンド）**
  ユーザーがチャット欄に `/context` または `/clean` と直接入力したとき。
- **B. 自律ワークフロー実行時**
  会話履歴が著しく長くなったとき、同じエラーで3回以上再試行に失敗（無限ループ化の予兆）したとき、あるいは巨大な外部仕様書（Tauri v2やNext.js 15）のクロールが必要となったとき。

---

## 2. 受付パラメータ (Arguments)
- `action`: [ `clean` (記憶の整理) | `summarize` (中間要約) | `prune` (巨大ファイルの排除) ] (必須)

---

## 3. モード別の行動方針 (Execution Modes)
- **ケースA（個別呼び出し）**: 承認フローをスキップし、即座にこれまでの会話の「中間要約」を生成してトークン消費を圧縮し、現在のトークン状態を報告して終了する。
- **ケースB（自律実行時）**: AI自身が「思考の迷子」を検知した際、進捗状況の自己チェックポイントを作成し、不必要な巨大ログやバイナリの読み込みをコンテキストから自発的に排除（prune）する。

---

## 4. 詳細手順 (Instructions)
1. **トークンのクレンジング**: 同じファイルに対する無駄な `read_files` の連打を防止し、読み込み履歴から直近の差分のみを記憶に留める。
2. **外部ドキュメントのピンポイント抽出**: `fetch_web_content` 等でNext.js 15やTauri v2の外部ドキュメントを調べる際は、丸ごと読み込まずに必要なコードサンプルと引数仕様のみをスクラップしてコンテキストに注入する。
3. **ループ脱出マトリックス**: ループが検出された場合、直前の3回の思考ログを強制要約し、「なぜ失敗したか」の仮説を3つ書き出して人間への相談プロンプトを再構成する。
