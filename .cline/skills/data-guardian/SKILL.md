---
name: data-guardian
description: |
  Protect and manage mock datasets, test cases, and database migrations for the book2pdf project.
  Forces automated backups before any destructive file or schema mutations.
  Supports both autonomous execution and explicit manual command (`/db`, `/backup`) invocations.
compatibility: SQLite / PostgreSQL Migrations + Mock Data
metadata:
  author: book2pdf-team
  version: "1.0"
---

# data-guardian

## 1. 起動トリガー / コマンド定義
本スキルは、以下のいずれかのタイミングで起動されます。

- **A. 個別呼び出し（スラッシュコマンド）**
  ユーザーがチャット欄に `/db` または `/backup` と直接入力したとき。
- **B. 自律ワークフロー実行時**
  `workflow-runner` の Phase 3 において、`test_cases/` 配下のマークダウン、OCR用の画像・PDFテストデータ、またはデータベースのスキーマやモックデータを変更・上書き（破壊的操作）するとき。

---

## 2. 受付パラメータ (Arguments)
- `action`: [ `backup` (退避) | `restore` (復元) | `dryrun` (検証) ] (必須)
- `target`: 操作対象のファイル群（例: `test_cases/`）

---

## 3. モード別の行動方針 (Execution Modes)
- **ケースA（個別呼び出し）**: 即座に指定されたテストデータやモック環境のバックアップ（または復元）を実行し、バックアップ先のパスを報告して終了する。
- **ケースB（自律実行時）**: **`.clinerules` の「テストデータの変更にはユーザーの承認が必要」ルールと厳密に連動する。** 承認を得た（Actモード）後、変更を加える「1ステップ前」に自動でバックアップを生成する。

---

## 4. 詳細手順 (Instructions)
1. **自動スナップショット**: 破壊的なデータ上書きや削除を行う前に、必ず `tmp/data_backup/` 配下に日付付きで現在の状態を退避させる。
2. **シミュレーション（Dry-run）の義務化**: マイグレーションスクリプト（Python等）を実行する前は、影響を受けるファイル数、データ件数、レコードの差分を計測し、事前に人間に提示する。
3. **データ整合性チェック**: 処理の実行後は、OCRパイプラインのイン・アウト、PDFの出力結果が破損していないかをバイナリサイズやハッシュ値、自動テストで検証する。
