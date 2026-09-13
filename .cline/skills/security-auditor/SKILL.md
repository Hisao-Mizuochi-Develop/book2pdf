---
name: security-auditor
description: |
  Audit security risks, environment variables, and leaked secrets for the book2pdf project.
  Blocks git commits automatically if API keys, passwords, or hardcoded tokens are found in staging area.
  Supports both autonomous execution and explicit manual command (`/audit`, `/secret-check`) invocations.
compatibility: Git Staging Static Analysis
metadata:
  author: book2pdf-team
  version: "1.0"
---

# security-auditor

## 1. 起動トリガー / コマンド定義
本スキルは、以下のいずれかのタイミングで起動されます。

- **A. 個別呼び出し（スラッシュコマンド）**
  ユーザーがチャット欄に `/audit` または `/secret-check` と直接入力したとき。
- **B. 自律ワークフロー実行時**
  `branch-manager` による `git commit` 操作の直前ゲート（検証タイミング）、または新規コード生成時のセキュリティ静的解析を行うとき。

---

## 2. 受付パラメータ (Arguments)
- `action`: [ `stage` (ステージング監査) | `scan` (コードスキャン) ] (必須)

---

## 3. モード別の行動方針 (Execution Modes)
- **ケースA（個別呼び出し）**: 4フェーズフローをスキップし、現在のGitの変更差分（`git diff --cached`）に対してセキュリティ監査を即座に実行し、脆弱性やシークレットの有無を報告する。
- **ケースB（自律実行時）**: **「Git操作前の選択式確認（コミット前）」の直前に完全自動でトリガーされる。** 監査でリスクが発見された場合、ユーザーの「A. はい」という同意があっても強制的にコミットをブロック（中断）する。

---

## 4. 詳細手順 (Instructions)
1. **シークレット漏洩の絶対阻止**: ステージングされたコードやタスク表、ログの中に、`sk-`、`AI_API_KEY`、パスワード文字列、生のIPアドレス、ローカル環境以外の絶対パスなどがハードコードされていないか全行スキャンする。
2. **環境変数（.env）への自動退避**: 機密情報がコード内で発見された場合は、即座に修正計画を立て、`.env` への定義移動と `.gitignore` への登録が正しくなされているかを確認・実装する。
3. **脆弱な関数の検出**: Pythonの `eval()` やシェルコマンドの生の文字列結合など、インジェクションに繋がる危険なコード生成を検知した場合は警告し、安全な代替実装に書き換える。
