# SY002002 UAT 検証レポート

> タスク: SY002002 コンテナ間進捗通知の REST API 連携方式実装
> 実施日: 2026-09-14
> 実施者: Cline

## 概要

本レポートは、SY002002 の UAT（ユーザー検証テスト）として、以下の連携が正常に動作することを検証した結果です。

- OCR 進捗取得 API（`GET /api/jobs/{job_id}`）
- backend → frontend への SSE 進捗配信（`GET /api/jobs/{job_id}/events`）
- PDF ダウンロード連携（`GET /api/jobs/{job_id}/pdf`）

## 検証環境

- プラットフォーム: macOS（darwin）
- Docker Compose: `docker compose up -d` で backend / ocr-worker / frontend コンテナ起動済み
- テスト画像: `test_cases/AI ・LLMの実務でつかえるRAG精度改善/001.png`（1 枚のみの ZIP）

## 実施手順

1. 1 枚の PNG から ZIP (`sample.zip`) を作成
2. `POST /api/jobs` でジョブ作成
3. `POST /api/jobs/{job_id}/upload` で ZIP アップロード
4. `GET /api/jobs/{job_id}/events` で SSE 接続を開始（バックグラウンドでログ取得）
5. `POST /api/jobs/{job_id}/ocr` で OCR 実行
6. `GET /api/jobs/{job_id}` でポーリングし、`completed` または `failed` になるまで待機
7. `GET /api/jobs/{job_id}/pdf` で PDF ダウンロード

## 実行結果

### ジョブ情報

- job_id: `2a92c602-9955-48cf-a139-d99a8b031773`
- アップロードファイル: `001.png`
- 最終ステータス: `completed`
- 最終メッセージ: `PDF 生成が完了しました`

### SSE 進捗イベント

`/tmp/sy002002_uat2/sse.log` に記録された主要イベントは以下の通りです。

```text
data: {"job_id":"2a92c602-9955-48cf-a139-d99a8b031773","status":"processing","progress":0.0,"current_page":0,"total_pages":1,"message":"OCR 処理を開始しました","timestamp":"2026-09-14T01:02:30.533764+00:00"}

data: {"job_id":"2a92c602-9955-48cf-a139-d99a8b031773","status":"processing","progress":0.1,"current_page":0,"total_pages":1,"message":"OCR 処理を開始します（1/1）","timestamp":"2026-09-14T01:02:30.533764+00:00"}

: keepalive
（中略）

data: {"job_id":"2a92c602-9955-48cf-a139-d99a8b031773","status":"completed","progress":1.0,"current_page":1,"total_pages":1,"message":"OCR 処理が完了しました","timestamp":"2026-09-14T01:04:14.869290+00:00"}

data: [DONE]
```

- `processing` 開始イベントが配信された
- per-page 進捗（`progress: 0.1`）が配信された
- keepalive コメントが維持された
- `completed` イベントが配信された
- 終了マーカー `[DONE]` が配信された

### PDF ダウンロード

- ダウンロード先: `/tmp/sy002002_uat2/out.pdf`
- ファイルサイズ: 18 MB
- ファイル形式: `PDF document, version 1.7, 2 pages`
- 内容確認: 表紙テキストが検索・抽出可能な状態で含まれていることを確認

## 合否判定

| 確認項目 | 結果 |
|---|---|
| ジョブ作成 → アップロード → OCR 実行の一連フロー | PASS |
| SSE 経由で processing / progress / completed イベントが配信される | PASS |
| ポーリングでジョブ状態が `completed` に遷移する | PASS |
| PDF が正常にダウンロードでき、PDF として有効である | PASS |
| ダウンロードした PDF に OCR テキストが含まれる | PASS |

**総合判定: PASS**

## 備考

- 検証スクリプト: `/tmp/sy002002_uat2/run_uat.sh`
- ジョブ ID ファイル: `/tmp/sy002002_uat2/jobid.txt`
- SSE ログ: `/tmp/sy002002_uat2/sse.log`
- ポーリングログ: `/tmp/sy002002_uat2/poll.log`
- ダウンロード PDF: `/tmp/sy002002_uat2/out.pdf`
