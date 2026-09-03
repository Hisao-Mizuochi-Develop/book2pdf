# book2pdf ドキュメントインデックス

本ディレクトリは、`backend` / `frontend` / `ocr-worker` / `localapp` を横断するプロジェクト全体の設計書・決定事項・タスク管理を配置する場所です。各モジュール固有のドキュメントは `<module>/docs/` を参照してください。

## 全体設計・決定事項

| ドキュメント | 内容 |
|---|---|
| [`web-ocr-system-plan.md`](web-ocr-system-plan.md) | プロジェクト全体のシステム構成・アーキテクチャ・処理フロー |
| [`design-decisions.md`](design-decisions.md) | 技術選定の理由と将来の課題 |
| [`coding-conventions.md`](coding-conventions.md) | Python / TypeScript / Rust のコーディング規約 |
| [`progress-notification-spec.md`](progress-notification-spec.md) | 進捗通知方式（SSE / ポーリング）の全体仕様 |

## 運用・手順

| ドキュメント | 内容 |
|---|---|
| [`integration-test-guide.md`](integration-test-guide.md) | Docker Compose 上での結合テスト手順 |
| [`tasks.md`](tasks.md) | プロジェクト全体のタスク管理表 |
| [`work_log.md`](work_log.md) | プロジェクト全体の作業ログ |
| [`caveats.md`](caveats.md) | 全体横断の注意事項 |

## backend ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`backend/docs/backend-system-spec.md`](../backend/docs/backend-system-spec.md) | バックエンド仕様書（API 設計・ジョブ管理・PDF 生成） |
| [`backend/docs/caveats.md`](../backend/docs/caveats.md) | バックエンド固有の注意事項・トラブルシューティング |
| [`backend/docs/tasks.md`](../backend/docs/tasks.md) | バックエンドタスク管理表 |
| [`backend/docs/work_log.md`](../backend/docs/work_log.md) | バックエンド作業ログ |

## frontend ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`frontend/docs/frontend-system-spec.md`](../frontend/docs/frontend-system-spec.md) | フロントエンド仕様書（UI 設計・API 連携） |
| [`frontend/docs/tasks.md`](../frontend/docs/tasks.md) | フロントエンドタスク管理表 |
| [`frontend/docs/work_log.md`](../frontend/docs/work_log.md) | フロントエンド作業ログ |

## ocr-worker ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`ocr-worker/docs/ocr-worker-system-spec.md`](../ocr-worker/docs/ocr-worker-system-spec.md) | OCR Worker 仕様書（ndlocr_cli 実行・コンテナ構成） |
| [`ocr-worker/docs/caveats.md`](../ocr-worker/docs/caveats.md) | ocr-worker 固有の注意事項・トラブルシューティング |
| [`ocr-worker/docs/tasks.md`](../ocr-worker/docs/tasks.md) | ocr-worker タスク管理表 |
| [`ocr-worker/docs/work_log.md`](../ocr-worker/docs/work_log.md) | ocr-worker 作業ログ |

## localapp ドキュメント

| ドキュメント | 内容 |
|---|---|
| [`localapp/docs/localapp-spec.md`](../localapp/docs/localapp-spec.md) | localapp 仕様書（Tauri v2 + Rust + React + Vite） |
| [`localapp/docs/caveats.md`](../localapp/docs/caveats.md) | localapp 固有の注意事項・トラブルシューティング |
| [`localapp/docs/tasks.md`](../localapp/docs/tasks.md) | localapp タスク管理表 |
| [`localapp/docs/work_log.md`](../localapp/docs/work_log.md) | localapp 作業ログ |
