# 進捗通知方式仕様書

本ドキュメントは、book2pdf プロジェクトにおける OCR 処理ジョブの進捗通知方式（SSE とポーリング）を定義したものです。`frontend`、`backend`、`localapp` の各モジュールが共通して参照します。

## 1. 目的

OCR 処理は 1 ページあたり数分〜数十分かかる長時間処理です。ユーザーに対して適切な進捗を表示し、処理が完了したこと・失敗したことを通知する仕組みが必要です。

本プロジェクトでは、リアルタイム性を重視した **Server-Sent Events (SSE)** を第一方式とし、SSE が利用できない環境（プロキシ・タイムアウト制限・WebView 制限など）のために **HTTP ポーリング** をフォールバック方式として提供します。

## 2. 対象モジュールと責務

| モジュール | 責務 |
|---|---|
| `backend` | ジョブ状態管理、SSE エンドポイント配信、`GET /api/jobs/{job_id}` による状態問い合わせ |
| `frontend` | ブラウザ上で SSE 接続、フォールバックとしてポーリング、進捗 UI 表示 |
| `localapp` | Tauri 環境で backend API をポーリング、`ocr-progress` イベントをフロントエンドへ中継 |

## 3. 方式の比較

| 項目 | SSE | ポーリング |
|---|---|---|
| リアルタイム性 | 高い（サーバーからプッシュ） | 低い（クライアントが問い合わせ） |
| プロキシ環境 | 一部で切断・遅延の可能性 | 一般的に安定 |
| 実装コスト | やや高い | 低い |
| 使用例 | Web ブラウザ（proxy なし） | Web ブラウザ（proxy あり）、Tauri localapp |

## 4. ジョブ状態遷移

```
pending → uploaded → processing → completed
                           ↓
                         failed
```

| 状態 | 意味 |
|---|---|
| `pending` | ジョブ作成直後、ファイル未アップロード |
| `uploaded` | ZIP ファイルアップロード完了、OCR 未実行 |
| `processing` | OCR 処理実行中（/backend /ocr 非同期実行中） |
| `completed` | OCR と PDF 生成が完了 |
| `failed` | 処理中にエラーが発生 |

## 5. SSE 方式

### 5.1 エンドポイント

```
GET /api/jobs/{job_id}/events
```

### 5.2 イベント形式

```text
event: progress
data: {"stage": "ocr", "message": "OCR 処理中...", "progress_percent": 45}

```

### 5.3 イベント種別

| event 名 | 用途 |
|---|---|
| `progress` | 処理段階・進捗パーセント・メッセージ |
| `completed` | ジョブ完了。PDF ダウンロード可能 |
| `failed` | ジョブ失敗。エラーメッセージを含む |

### 5.4 イベントデータスキーマ

```json
{
  "stage": "ocr",
  "message": "OCR 処理中...",
  "progress_percent": 45,
  "job_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "timestamp": "2026-09-03T10:00:00Z"
}
```

### 5.5 エラーハンドリング

- SSE 接続が切断された場合、クライアントは自動的に再接続を試みる
- 一定回数の再接続失敗後、自動的にポーリング方式に切り替える
- 接続中に `failed` イベントを受信した場合、進捗表示を停止しエラーメッセージを表示

## 6. ポーリング方式

### 6.1 エンドポイント

```
GET /api/jobs/{job_id}
```

### 6.2 レスポンス例

```json
{
  "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "processing",
  "message": "OCR 処理を実行中です",
  "files": ["002.png", "003.png", "004.png"],
  "created_at": "2026-09-03T09:00:00Z",
  "updated_at": "2026-09-03T09:05:00Z"
}
```

### 6.3 ポーリング間隔

| 状態 | 推奨間隔 | 理由 |
|---|---|---|
| `processing` | 5 秒〜10 秒 | サーバー負荷とリアルタイム性のバランス |
| `pending` / `uploaded` | 2 秒 | 早期段階では短くして応答性を確保 |
| 完了直後 | 即座に取得 | `completed`/`failed` を検知したらポーリング停止 |

### 6.4 最大ポーリング時間

- 設定ファイル `~/.config/book2pdf/settings.json` の `page_timeout_sec`（1 ページあたりのタイムアウト）に基づく
- 計算式: `推定最大時間 = ページ数 × page_timeout_sec`
- デフォルト: `page_timeout_sec = 600`（10 分/ページ）
- 推定最大時間を超えても `completed`/`failed` に至らない場合、クライアントはユーザーに対して「タイムアウトしました。backend の状態を確認してください」と表示する

## 7. 各モジュールの実装指針

### 7.1 backend

- `GET /api/jobs/{job_id}/events` は `StreamingResponse` で SSE を返す
- 進捗情報は `/data/progress/{job_id}.json` またはジョブステータスを参照する
- `GET /api/jobs/{job_id}` は通常の JSON レスポンスを返す
- 両方のエンドポイントで同一のジョブ状態を参照し、整合性を保つ

### 7.2 frontend

- まず SSE (`EventSource`) で接続を試行する
- SSE 接続失敗・切断時は自動的に `GET /api/jobs/{job_id}` へのポーリングに切り替える
- ユーザー設定または環境検出で「常にポーリングを使用」モードを提供してもよい
- 進捗表示コンポーネントは SSE/ポーリングの差異を吸収し、統一されたイベントオブジェクトを受け取る

### 7.3 localapp

- Tauri の WebView 内では `EventSource` が使えない、または不安定な場合がある
- 原則として `GET /api/jobs/{job_id}` へのポーリングを使用する
- Rust 側 (`backend_api_impl.rs`) がポーリングを実行し、`ocr-progress` イベントをフロントエンドに emit する
- フロントエンド (`backendApiStore.ts`) は `ocr-progress` イベントを購読し、進捗 UI を更新する

## 8. 設定項目

`~/.config/book2pdf/settings.json`（localapp）および frontend の設定 UI で以下をユーザーが変更可能にする。

```json
{
  "backend_url": "http://localhost:8000",
  "polling_interval_sec": 5,
  "page_timeout_sec": 600,
  "http_client_timeout_sec": 60,
  "upload_timeout_sec": 600,
  "ocr_request_timeout_sec": 60,
  "poll_request_timeout_sec": 10,
  "prefer_sse": true
}
```

| キー | 型 | デフォルト | 説明 |
|---|---|---|---|
| `backend_url` | string | `http://localhost:8000` | backend API のベース URL |
| `polling_interval_sec` | integer | `5` | ポーリング間隔（秒） |
| `page_timeout_sec` | integer | `600` | 1 ページあたりのタイムアウト（秒） |
| `http_client_timeout_sec` | integer | `60` | HTTP クライアント全体のデフォルトタイムアウト（秒） |
| `upload_timeout_sec` | integer | `600` | ZIP アップロード時の個別タイムアウト（秒） |
| `ocr_request_timeout_sec` | integer | `60` | OCR 実行依頼の個別タイムアウト（秒） |
| `poll_request_timeout_sec` | integer | `10` | ジョブ状態取得の個別タイムアウト（秒） |
| `prefer_sse` | boolean | `true` | frontend で SSE を優先して試行するか |

## 9. 今後の拡張

- WebSocket 方式の検討（双方向通信が必要になった場合）
- 進捗の詳細化（ページ単位の進捗、処理段階ごとの予測残り時間）
- ジョブ一覧画面での複数ジョブ進捗表示

## 10. 関連ドキュメント

- `backend/docs/backend-system-spec.md` — backend 側の実装詳細
- `frontend/docs/frontend-system-spec.md` — frontend 側の実装詳細
- `localapp/docs/localapp-spec.md` — localapp 側の実装詳細
- `docs/web-ocr-system-plan.md` — 全体アーキテクチャ
