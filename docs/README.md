# book2pdf ドキュメントインデックス

本ディレクトリは、`backend` / `frontend` / `ocr-worker` / `localapp` を横断するプロジェクト全体の設計書・決定事項・タスク管理を配置する場所です。各モジュール固有のドキュメントは `<module>/docs/` を参照してください。

## 全体設計・決定事項

| ドキュメント | 内容 |
|---|---|
| [`SY-WEB-OCR-SYSTEM-PLAN.md`](SY-WEB-OCR-SYSTEM-PLAN.md) | プロジェクト全体のシステム構成・アーキテクチャ・処理フロー |
| [`SY-DESIGN-DECISIONS.md`](SY-DESIGN-DECISIONS.md) | 技術選定の理由と将来の課題 |
| [`OT-CODING-CONVENTIONS.md`](OT-CODING-CONVENTIONS.md) | Python / TypeScript / Rust のコーディング規約 |
| [`SY-PROGRESS-NOTIFICATION-SPEC.md`](SY-PROGRESS-NOTIFICATION-SPEC.md) | 進捗通知方式（SSE / ポーリング）の全体仕様 |

## 運用・手順

| ドキュメント | 内容 |
|---|---|
| [`OT-INTEGRATION-TEST-GUIDE.md`](OT-INTEGRATION-TEST-GUIDE.md) | Docker Compose 上での結合テスト手順 |
| [`OT-AGENT-SKILLS-GUIDE.md`](OT-AGENT-SKILLS-GUIDE.md) | Cline AgentSkills の構成定義・各スキル役割・運用方法 |
| [`OT-TASKS.md`](OT-TASKS.md) | プロジェクト全体のタスク管理表 |
| [`OT-WORK-LOG.md`](OT-WORK-LOG.md) | プロジェクト全体の作業ログ |
| [`OT-CAVEATS.md`](OT-CAVEATS.md) | 全体横断の注意事項 |

## backend ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`backend/docs/BE-BACKEND-SYSTEM-SPEC.md`](../backend/docs/BE-BACKEND-SYSTEM-SPEC.md) | バックエンド仕様書（API 設計・ジョブ管理・PDF 生成） |
| [`backend/docs/BE-CAVEATS.md`](../backend/docs/BE-CAVEATS.md) | バックエンド固有の注意事項・トラブルシューティング |
| [`backend/docs/BE-TASKS.md`](../backend/docs/BE-TASKS.md) | バックエンドタスク管理表 |
| [`backend/docs/BE-WORK-LOG.md`](../backend/docs/BE-WORK-LOG.md) | バックエンド作業ログ |

## frontend ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`frontend/docs/FE-FRONTEND-SYSTEM-SPEC.md`](../frontend/docs/FE-FRONTEND-SYSTEM-SPEC.md) | フロントエンド仕様書（UI 設計・API 連携） |
| [`frontend/docs/FE-TASKS.md`](../frontend/docs/FE-TASKS.md) | フロントエンドタスク管理表 |
| [`frontend/docs/FE-WORK-LOG.md`](../frontend/docs/FE-WORK-LOG.md) | フロントエンド作業ログ |

## ocr-worker ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`ocr-worker/docs/OW-OCR-WORKER-SYSTEM-SPEC.md`](../ocr-worker/docs/OW-OCR-WORKER-SYSTEM-SPEC.md) | OCR Worker 仕様書（ndlocr_cli 実行・コンテナ構成） |
| [`ocr-worker/docs/OW-CAVEATS.md`](../ocr-worker/docs/OW-CAVEATS.md) | ocr-worker 固有の注意事項・トラブルシューティング |
| [`ocr-worker/docs/OW-TASKS.md`](../ocr-worker/docs/OW-TASKS.md) | ocr-worker タスク管理表 |
| [`ocr-worker/docs/OW-WORK-LOG.md`](../ocr-worker/docs/OW-WORK-LOG.md) | ocr-worker 作業ログ |

## localapp ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`localapp/docs/LA-LOCALAPP-SPEC.md`](../localapp/docs/LA-LOCALAPP-SPEC.md) | localapp 仕様書（Tauri v2 + Rust + React + Vite） |
| [`localapp/docs/LA-CAVEATS.md`](../localapp/docs/LA-CAVEATS.md) | localapp 固有の注意事項・トラブルシューティング |
| [`localapp/docs/LA-TASKS.md`](../localapp/docs/LA-TASKS.md) | localapp タスク管理表 |
| [`localapp/docs/LA-WORK-LOG.md`](../localapp/docs/LA-WORK-LOG.md) | localapp 作業ログ |
