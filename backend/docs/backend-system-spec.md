# Web OCR/PDF システム バックエンド 仕様書

本ドキュメントは、電子書籍のページ画像から OCR 処理を行い、検索可能 PDF を生成する Web システムのバックエンド仕様をまとめたものです。

## 1. プロジェクト概要

- **目的**: 電子書籍のページ画像（ZIP アーカイブ）から OCR 処理を行い、検索可能 PDF を生成する
- **学習目的**: Next.js / FastAPI / Docker / Rust / Tauri の習得
- **方針**: 既存の `old/` フォルダのソースコード・ドキュメントは一切参照せず、スクラッチで開発する

## 2. システム全体構成

本プロジェクトは以下の 2 つのシステムで構成されます。

| システム | 用途 | 技術スタック |
|---|---|---|
| ローカルスタンドアローンアプリ | 電子書籍画面のキャプチャ＋不要部分のトリミング | Tauri v2 + Rust + React + Vite |
| Web OCR/PDF システム | ZIP 画像 → OCR → 検索可能 PDF 生成 | Next.js 15 + FastAPI + Docker + ndlocr_cli |

各システムの選定理由や非機能要件などの詳細は `docs/design-decisions.md` を参照してください。

## 3. Web システムの技術選定

| レイヤー | 技術 | 理由 |
|---|---|---|
| フロントエンド | Next.js 15 App Router | モダン Web 技術の学習、SSR/SSG/Route Handlers の実践 |
| バックエンド | FastAPI | Python 製 OCR ライブラリとの親和性が高い、非同期処理が得意 |
| OCR | ndlocr_cli | 日本語縦書き・ルビ・複雑レイアウトに強い国立国会図書館製 OCR |
| PDF 生成 | PyMuPDF（候補） | 画像背景＋透明テキストレイヤーの検索可能 PDF 作成に向いている |
| コンテナ | Docker + Docker Compose | 環境の再現性、OS 依存の排除 |

## 4. コンテナ構成

FastAPI と ndlocr_cli は別コンテナとして分離します。コンテナ間の連携は、プロジェクトルートの `docker-compose.yml` で定義します。

```
frontend コンテナ: Next.js
backend コンテナ:   FastAPI + ZIP 展開 + ジョブ管理 + PDF 生成
ocr-worker コンテナ: ndlocr_cli（Python パッケージとして import）
```

### 共有ボリューム

`backend` と `ocr-worker` は以下の Docker ボリュームを共有します。

- `/data/uploads`: アップロードされた ZIP
- `/data/extracted`: 展開された画像
- `/data/ocr_output`: OCR 結果
- `/data/pdfs`: 生成された PDF
- `/data/progress`: 進捗通知用 JSON ファイル（backend と ocr-worker で共有）

### コンテナ連携

- `backend` コンテナがジョブを受け付け、ZIP 展開・ジョブ管理・PDF 生成を行う
- OCR 処理は `ocr-worker` コンテナ内の FastAPI HTTP API を通じて ndlocr_cli で実行する
- `ocr-worker` コンテナは起動時に Uvicorn で API サーバーを立ち上げ、
  `POST /ocr` リクエストを待ち受ける
- backend から ocr-worker へは Docker Compose サービス名を使って `http://ocr-worker:8000` でアクセスする
- OCR 処理の進捗は `/data/progress/{job_id}.json` に書き出され、
  backend の `GET /api/jobs/{job_id}/events` で SSE 形式で配信される

## 5. 処理フロー

1. ユーザーが ZIP アーカイブをブラウザからアップロード
2. FastAPI が ZIP を保存して展開
3. ジョブ ID を発行し、ジョブ状態を管理
4. FastAPI が `ocr-worker` コンテナ経由で ndlocr_cli を呼び出して OCR 実行
5. OCR 処理中、`ocr-worker` が `/data/progress/{job_id}.json` に進捗を書き出す
6. backend が進捗ファイルをポーリングし、SSE でブラウザに配信する
7. OCR 結果を取得し、検索可能 PDF を生成
8. ユーザーが PDF をダウンロード

## 6. PDF 仕様

- **形式**: 検索可能 PDF
- **背景**: 元のページ画像をそのまま配置
- **テキストレイヤー**: OCR 結果の座標情報を使用し、元画像と同じレイアウトに透明テキストを配置
- **フォントサイズ**: バウンディングボックスの高さから概算して近いサイズに調整
- **縦書き**: 横書きと同等の精度を目指す（段階的に対応）

## 7. OCR 実行形式

- **方式**: Python パッケージとして `import` して関数を呼び出す
- **理由**: FastAPI 側のコードがシンプルになり、入出力の制御が容易

## 8. 初期実装範囲

### 8.1 今回の初期実装で採用する方式

| 項目 | 初期実装 |
|---|---|---|
| ジョブ状態管理 | **メモリ内（辞書）** |
| 進捗通知 | **Server-Sent Events (SSE)** |

### 8.2 採用理由

- メモリ内管理：実装がシンプルで、学習初期に集中できる
- SSE：リアルタイム性があり、FastAPI との相性が良い

## 9. 将来の課題・拡張

以下は今回の初期実装では対応せず、次のステップで検討・実装する課題として記録します。

### 9.1 ジョブ状態の永続化

- **目標**: SQLite に永続化
- **理由**: プロセス再起動後もジョブ状態を保持し、複数 worker 間での状態共有を可能にする

### 9.2 進捗通知方式の見直し

- **目標**: フロントエンドのポーリング方式も検討
- **理由**: プロキシ環境やタイムアウト設定によって SSE が不安定になる場合への対応

## 10. フォルダ・ファイル構成

```
backend/                          # バックエンドルート
├── Dockerfile                    # バックエンド Docker イメージ定義
├── requirements.txt              # Python 依存パッケージ一覧
├── run.py                        # 開発用 Uvicorn 起動スクリプト
```

なお、プロジェクトルートには `docker-compose.yml` が配置されており、`backend` コンテナと `ocr-worker` コンテナをまとめて起動します。

```
/Users/hisao/Documents/work4/sakura/book2pdf/
├── docker-compose.yml            # backend / ocr-worker 連携定義
├── backend/
│   └── ...
└── ocr-worker/
    └── ...
```

### backend 配下の詳細

```
backend/
├── Dockerfile                    # バックエンド Docker イメージ定義
├── requirements.txt              # Python 依存パッケージ一覧
├── run.py                        # 開発用 Uvicorn 起動スクリプト
├── app/                          # アプリケーションコード
│   ├── __init__.py               # app パッケージの初期化
│   ├── main.py                   # FastAPI アプリケーション本体
│   ├── core/                     # 設定・共通処理
│   │   ├── __init__.py           # core サブパッケージの初期化
│   │   └── config.py             # pydantic-settings による設定管理
│   ├── models/                   # Pydantic モデル
│   │   ├── __init__.py           # models サブパッケージの初期化
│   │   └── job.py                # OCR ジョブ関連モデル
│   ├── routers/                  # API エンドポイント
│   │   ├── __init__.py           # routers サブパッケージの初期化
│   │   └── jobs.py               # ジョブ関連 API ルーター
│   └── services/                 # ビジネスロジック
│       ├── __init__.py           # services サブパッケージの初期化
│       ├── job_manager.py        # メモリ内ジョブ状態管理
│       ├── zip_extractor.py      # ZIP 展開・画像抽出
│       └── ocr_engine.py         # ndlocr_cli ラッパー・OCR 実行
├── docs/                         # backend 専用ドキュメント
│   ├── backend-system-spec.md    # 本仕様書
│   ├── caveats.md                # タスク実施中の注意事項
│   ├── work_log.md               # タスク作業ログ
│   └── tasks.md                  # タスク管理表
└── tests/                        # テストコード
    ├── __init__.py               # tests パッケージの初期化
    ├── conftest.py               # pytest 用共通設定（EXTRACT_BASE_DIR 上書きなど）
    ├── test_main.py              # 基本動作確認用テスト
    ├── test_jobs.py              # ジョブ・ZIP アップロード関連テスト
    ├── test_ocr.py               # OCR 実行関連テスト
    └── test_progress.py          # SSE 進捗通知関連テスト
```

## 11. 性能テスト

### 11.1 目的

OCR 処理のボトルネックを特定し、各工程の処理時間を定量化するための性能テストです。

### 11.2 入力データ

- **サンプル画像**: `sample-png/AI ・LLMの実務でつかえるRAG精度改善_trimmed/001.png` 〜 `010.png`
- **入力 ZIP**: `/tmp/book2pdf-benchmark/benchmark-input-10pages.zip`
- **ページ数**: 10 ページ固定

### 11.3 計測対象

| 順番 | 項目 | 取得方法 |
|---|---|---|
| 1 | Docker Compose 起動時間 | スクリプト内で `docker compose up -d` 〜 ヘルスチェック 200 までを計測 |
| 2 | ジョブ作成時間 | `POST /api/jobs` の応答時間を計測 |
| 3 | ZIP アップロード時間 | `POST /api/jobs/{job_id}/upload` の応答時間を計測 |
| 4 | OCR 全体時間 | `POST /api/jobs/{job_id}/ocr` 〜 ジョブ状態が `completed` になるまでを計測 |
| 5 | 1 ページごとの OCR 処理時間 | `ocr-worker` の DEBUG ログから抽出 |
| 6 | 1 ページあたり平均 OCR 処理時間 | 1 ページごとの OCR 処理時間の平均を算出 |
| 7 | PDF 生成時間 | `backend` の DEBUG ログから抽出 |
| 8 | PDF ダウンロード時間 | `GET /api/jobs/{job_id}/pdf` の応答時間を計測 |
| 9 | 合計処理時間 | 上記工程時間の合計 |

### 11.4 ログ取得元

- **backend DEBUG ログ**: ZIP 解凍時間、`pdf_generator.py` の PDF 生成時間
- **ocr-worker DEBUG ログ**: `ndlocr_cli` の 1 ページごとの OCR 処理時間

### 11.5 出力

- `/tmp/book2pdf-benchmark/results.csv`
- `/tmp/book2pdf-benchmark/results.txt`

### 11.6 実行方法

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
./scripts/benchmark_ocr.sh
```

### 11.7 クリーンアップ

性能テスト終了後、以下を削除します。

- 入力 ZIP ファイル
- 展開されたページ画像（`/data/extracted/{job_id}/`）
- OCR 出力（`/data/ocr_output/{job_id}/`）
- ダウンロードされた PDF ファイル

## 12. 注意事項

- ndlocr_cli は公式 Docker スクリプトがあるが、今回は自分で Dockerfile を組み立てる
  - `ocr-worker` 用 Dockerfile の詳細は `../ocr-worker/docs/caveats.md` を参照
- CPU 実行のため、OCR 処理には時間がかかることを想定
- ndlocr_cli の import パスや関数 signature はリポジトリの実際のコードを確認する必要がある
- 縦書き PDF 生成は高度な処理となるため、まず横書きで動作確認してから段階的に対応する
- タスク実施中に発生した注意すべき事象は [`caveats.md`](./caveats.md) に記録している。随時参照すること。
- 2026-08-11: `ocr-worker` コンテナのビルドとサンプル画像での OCR 実行に成功した
  - 詳細は `../ocr-worker/docs/work_log.md` および `../ocr-worker/docs/caveats.md` を参照
