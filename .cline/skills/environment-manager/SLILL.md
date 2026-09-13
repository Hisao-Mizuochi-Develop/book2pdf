---
name: environment-manager
description: |
  Manage Docker containers, npm packages, and python virtual environments for the book2pdf project.
  Automatically detects lockfile/requirements changes and builds clean isolated environments.
  Supports both autonomous execution and explicit manual command (`/env`, `/rebuild`) invocations.
compatibility: Docker Compose + Node.js + Python venv
metadata:
  author: book2pdf-team
  version: "1.0"
---

# environment-manager

## 1. 起動トリガー / コマンド定義
本スキルは、以下のいずれかのタイミングで起動されます。

- **A. 個別呼び出し（スラッシュコマンド）**
  ユーザーがチャット欄に `/env` または `/rebuild` と直接入力したとき。
- **B. 自律ワークフロー実行時**
  `workflow-runner` の Phase 1/Phase 3 において、`package.json`, `requirements.txt`, `Cargo.toml`, `docker-compose.yml` などの変更を検知し、環境の再構築やコンテナログの監視が必要と判断されたとき。

---

## 2. 受付パラメータ (Arguments)
- `action`: [ `rebuild` (再ビルド) | `install` (依存解消) | `logs` (ログ確認) ] (必須)
- `target`: [ `backend` | `frontend` | `localapp` | `ocr-worker` | `all` ]

---

## 3. モード別の行動方針 (Execution Modes)
- **ケースA（個別呼び出し）**: 4フェーズの計画確認をスキップし、対象モジュールの環境構築・ログ確認を即座に実行（Act）し、成否を1行で報告する。
- **ケースB（自律実行時）**: Actモードへの移行後にのみコンテナの操作を実行する。依存ファイルの変更時は自動的に人間へ環境の再ビルド計画（Gate 2）を提示する。

---

## 4. 詳細手順 (Instructions)
1. **依存関係変更の自動検知**: `requirements.txt` や `package.json` を変更した際は、テスト実行前に必ずバックグラウンドで依存解消コマンドを実行すること。
2. **コンテナビルド制御**: `ocr-worker` や `backend` のコンテナ構成が変わった場合は、`docker compose up --build -d <サービス名>` を実行してクリーンな状態を保つ。
3. **ランタイムログの監視**: 環境起動後は `docker compose logs --tail=50` やアプリケーションの標準エラー出力を自動巡回し、起動直後のクラッシュや接続エラー（FastAPI ↔ ndlocr_cli 等の疎通不全）が 0 件であることをセルフチェックする。
