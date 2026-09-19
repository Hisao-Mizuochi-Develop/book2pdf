# book2pdf ドキュメントインデックス

本リポジトリの各種ドキュメントへの入口です。
システム全体の設計書、運用手順、各モジュールの仕様・タスク・作業ログを下記から参照してください。

> 最終更新: 2026/09/19

---

## 全体設計・決定事項

| ドキュメント | 内容 |
|---|---|
| [`SY-WEB-OCR-SYSTEM-PLAN.md`](SY-WEB-OCR-SYSTEM-PLAN.md) | プロジェクト全体のシステム構成・アーキテクチャ・処理フロー |
| [`SY-DESIGN-DECISIONS.md`](SY-DESIGN-DECISIONS.md) | 技術選定の理由と将来の課題 |
| [`PJ-CODING-CONVENTIONS.md`](PJ-CODING-CONVENTIONS.md) | Python / TypeScript / Rust のコーディング規約 |
| [`SY-PROGRESS-NOTIFICATION-SPEC.md`](SY-PROGRESS-NOTIFICATION-SPEC.md) | 進捗通知方式（SSE / ポーリング）の全体仕様 |
| [`SY-CAVEATS.md`](SY-CAVEATS.md) | 全体横断の注意事項 |
| [`SY-CONTAINER-3LAYER-ARCHITECTURE.md`](SY-CONTAINER-3LAYER-ARCHITECTURE.md) | コンテナ3層構造設計書 |
| [`SY-CONTAINER-PROGRESS-API-DESIGN.md`](SY-CONTAINER-PROGRESS-API-DESIGN.md) | コンテナ間進捗通知のREST API連携方式設計書 |
| [`SY-SSE-PROGRESS-DELIVERY-GUIDE.md`](SY-SSE-PROGRESS-DELIVERY-GUIDE.md) | 進捗配信 SSE 解説書 |
| [`SY-STORAGE-MIGRATION-GUIDE.md`](SY-STORAGE-MIGRATION-GUIDE.md) | 共有ファイルシステム代替方針（AWS 移行時） |

## 運用・手順・ガイド

| ドキュメント | 内容 |
|---|---|
| [`SY-INTEGRATION-TEST-GUIDE.md`](SY-INTEGRATION-TEST-GUIDE.md) | Docker Compose 上での結合テスト手順 |
| [`PJ-AGENT-SKILLS-GUIDE.md`](PJ-AGENT-SKILLS-GUIDE.md) | Cline AgentSkills の構成定義・各スキル役割・運用方法 |
| [`SY-BOOK2PDF_AGENT_SKILLS_MANUAL.md`](SY-BOOK2PDF_AGENT_SKILLS_MANUAL.md) | Agent Skills 操作マニュアル |
| [`OW-OCR-PREPROCESSING-GUIDE.md`](OW-OCR-PREPROCESSING-GUIDE.md) | OCR 前処理・画像サイズ制御ガイド |
| [`SY-DEBUG-LOGGING-GUIDE.md`](SY-DEBUG-LOGGING-GUIDE.md) | デバッグログの設定・確認方法 |

## タスク管理・作業ログ・注意事項

| ドキュメント | 内容 |
|---|---|
| [`OT-TASKS.md`](OT-TASKS.md) | 機能・性能以外のタスク管理表 |
| [`OT-WORK-LOG.md`](OT-WORK-LOG.md) | 機能・性能以外の作業ログ |
| [`PJ-CAVEATS.md`](PJ-CAVEATS.md) | プロジェクト運用・ガバナンス固有の注意事項 |
| [`PJ-TASKS.md`](PJ-TASKS.md) | プロジェクト運用・ガバナンスタスク管理表 |
| [`PJ-WORK-LOG.md`](PJ-WORK-LOG.md) | プロジェクト運用・ガバナンス作業ログ |
| [`SY-TASKS.md`](SY-TASKS.md) | 全体設計・横断タスク管理表 |
| [`SY-WORK-LOG.md`](SY-WORK-LOG.md) | 全体設計・横断作業ログ |
| [`backend/docs/BE-CAVEATS.md`](../backend/docs/BE-CAVEATS.md) | backend 固有の注意事項 |
| [`backend/docs/BE-TASKS.md`](../backend/docs/BE-TASKS.md) | backend タスク管理表 |
| [`backend/docs/BE-WORK-LOG.md`](../backend/docs/BE-WORK-LOG.md) | backend 作業ログ |
| [`frontend/docs/FE-CAVEATS.md`](../frontend/docs/FE-CAVEATS.md) | frontend 固有の注意事項 |
| [`frontend/docs/FE-TASKS.md`](../frontend/docs/FE-TASKS.md) | frontend タスク管理表 |
| [`frontend/docs/FE-WORK-LOG.md`](../frontend/docs/FE-WORK-LOG.md) | frontend 作業ログ |
| [`ocr-worker/docs/OW-CAVEATS.md`](../ocr-worker/docs/OW-CAVEATS.md) | ocr-worker 固有の注意事項 |
| [`ocr-worker/docs/OW-TASKS.md`](../ocr-worker/docs/OW-TASKS.md) | ocr-worker タスク管理表 |
| [`ocr-worker/docs/OW-WORK-LOG.md`](../ocr-worker/docs/OW-WORK-LOG.md) | ocr-worker 作業ログ |
| [`localapp/docs/LA-CAVEATS.md`](../localapp/docs/LA-CAVEATS.md) | localapp 固有の注意事項 |
| [`localapp/docs/LA-TASKS.md`](../localapp/docs/LA-TASKS.md) | localapp タスク管理表 |
| [`localapp/docs/LA-WORK-LOG.md`](../localapp/docs/LA-WORK-LOG.md) | localapp 作業ログ |

## Cline Agent Skills

| スキル | 内容 |
|---|---|
| [`.cline/skills/code-generator/SKILL.md`](../.cline/skills/code-generator/SKILL.md) | プロジェクトの言語別コーディング規約に沿ったコード生成 |
| [`.cline/skills/file-modifier/SKILL.md`](../.cline/skills/file-modifier/SKILL.md) | 既存 Markdown ファイルの修正（`replace_in_file` のみ許可） |
| [`.cline/skills/task-manager/SKILL.md`](../.cline/skills/task-manager/SKILL.md) | タスク管理表・作業ログの運用ルール |
| [`.cline/skills/test-manager/SKILL.md`](../.cline/skills/test-manager/SKILL.md) | テストデータ配置・backend API 検証・検証レポート作成 |
| [`.cline/skills/workflow-runner/SKILL.md`](../.cline/skills/workflow-runner/SKILL.md) | タスク実行の 4 フェーズワークフローと Git 運用 |

## backend ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`backend/docs/BE-BACKEND-SYSTEM-SPEC.md`](../backend/docs/BE-BACKEND-SYSTEM-SPEC.md) | バックエンド仕様書（FastAPI + ndlocr_cli） |
| [`backend/docs/BE-UNIT-TEST-GUIDE.md`](../backend/docs/BE-UNIT-TEST-GUIDE.md) | backend 単体テスト実行手順・環境構築ガイド |
| [`backend/docs/BE007001-report.md`](../backend/docs/BE007001-report.md) | BE007001 最終報告書 |

## frontend ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`frontend/docs/FE-FRONTEND-SYSTEM-SPEC.md`](../frontend/docs/FE-FRONTEND-SYSTEM-SPEC.md) | フロントエンド仕様書（UI 設計・API 連携） |

## ocr-worker ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`ocr-worker/docs/OW-OCR-WORKER-SYSTEM-SPEC.md`](../ocr-worker/docs/OW-OCR-WORKER-SYSTEM-SPEC.md) | OCR worker 仕様書（ndlocr_cli 実行・コンテナ構成） |

## localapp ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`localapp/docs/LA-LOCALAPP-SPEC.md`](../localapp/docs/LA-LOCALAPP-SPEC.md) | localapp 仕様書（Tauri v2 + Rust + React + Vite） |
| [`localapp/docs/LA-BUILD-GUIDE.md`](../localapp/docs/LA-BUILD-GUIDE.md) | 開発・ビルド・起動手順 |
| [`localapp/docs/LA-OCR-TECHNOLOGY-SURVEY-LA008007.md`](../localapp/docs/LA-OCR-TECHNOLOGY-SURVEY-LA008007.md) | localapp 単体 OCR→PDF 技術調査レポート |
| [`localapp/docs/LA-TIMEOUT-INVESTIGATION-REPORT-OT003001.md`](../localapp/docs/LA-TIMEOUT-INVESTIGATION-REPORT-OT003001.md) | backend OCR 連携時タイムアウト調査報告書 |
