# Web OCR/PDF システム OCR Worker 仕様書

本ドキュメントは、電子書籍のページ画像から OCR 処理を行い、検索可能 PDF を生成する Web システムの OCR Worker 仕様をまとめたものです。

## 1. 責務

- ndlocr_cli を Python パッケージとして実行する環境を提供する
- `backend` からの HTTP リクエストを受け付け、指定された画像に対して OCR 処理を行う
- 日本語縦書き・ルビ・複雑な和書レイアウトにも対応した OCR 結果を返す

## 2. 技術選定

| 項目 | 技術 | 理由 |
|---|---|---|
| OCR エンジン | ndlocr_cli | 日本語縦書き・ルビ・複雑レイアウトに強い国立国会図書館製 OCR |
| 言語 | Python | ndlocr_cli が Python パッケージとして提供されている |
| コンテナ | Docker | ndlocr_cli の重い依存環境を隔離し、再現性を保つ |
| API フレームワーク | FastAPI | backend との連携が容易で、非同期処理に対応している |
| 実行方式 | Python パッケージとして `import` し、FastAPI HTTP API 経由で backend から呼び出す | コンテナ分離を保ちつつ、入出力の制御が容易 |

## 3. 入出力

### 入力

- 画像ファイルのパス、または画像が格納されたディレクトリのパス
- 必要に応じて OCR の設定パラメータ（認識対象言語、レイアウト方向など）

### 出力

- OCR 結果（テキスト、座標、信頼度など）
- 出力形式は ndlocr_cli の仕様に従う

## 4. 初期実装範囲

### 4.1 今回の初期実装で採用する方式

| 項目 | 初期実装 |
|---|---|
| 実行方式 | FastAPI HTTP API 経由で backend から画像パスを受け取り、ndlocr_cli を実行する |
| 対応テキスト方向 | 横書きを優先し、縦書きは段階的に対応 |

### 4.2 採用理由

- FastAPI HTTP API：コンテナを分離しつつ、backend からの呼び出しが容易で入出力の制御が容易
- Python パッケージ呼び出し：ndlocr_cli はコンテナ内で import して実行し、実装をシンプルに保つ
- 横書き優先：縦書き対応は高度な処理となるため、まず横書きで動作確認してから段階的に対応する

## 5. 将来の課題・拡張

### 5.1 縦書き・複雑レイアウトの本格対応

- **目標**: 縦書きテキストやルビを含むページでも高精度な OCR 結果を返す
- **理由**: 和書電子書籍への対応範囲を広げるため

## 6. コンテナ構成

### 6.1 ocr-worker コンテナ

- **ベースイメージ**: `python:3.10-slim`
- **目的**: ndlocr_cli を Python パッケージとして実行できる環境を提供する
- **実行方式**: CPU 実行を前提とする
- **主な構成要素**:
  - ndlocr_cli リポジトリの `cli/` と `submodules/`
  - 学習済みモデルファイル（`lab.ndl.go.jp` からダウンロード）
  - PyTorch / mmcv / mmdet（CPU 版）
  - `config.yml`（`device: 'cpu'` に変更済み）
  - KyTea（`ruby_prediction` で使用、ソースからビルド）
- **CPU 化のための主なパッチ**（ビルド時に Dockerfile 内で `sed` を適用）:
  - `config.yml` および各 submodule の `device: 'cuda:0'` を `cpu` に変更
  - mmdet 3.x の `init_detector` 引数順序違いに対応（`device=device` を明示）
  - `text_recognition_lightning` から CPU 非対応の `MeasureTimeCallback` を削除
  - `text_recognition_lightning` の trainer の `accelerator: gpu` を `cpu` に変更

### 6.2 backend コンテナとの連携

- `docker-compose.yml` で `backend` コンテナと `ocr-worker` コンテナを連携する
- 以下の共有ボリュームをマウントし、データを受け渡す
  - `uploads`: アップロードされた ZIP ファイル
  - `extracted`: ZIP 展開後の画像ファイル
  - `ocr_output`: OCR 結果（XML、画像など）
  - `pdfs`: 生成された PDF ファイル
- `ocr-worker` コンテナは起動時に Uvicorn で FastAPI API サーバーを立ち上げる
- backend からは `POST /ocr` エンドポイントを呼び出して OCR を実行する
- ヘルスチェック用の `GET /health` エンドポイントも提供し、
  `docker-compose.yml` の `depends_on` で backend の起動を待たせる

## 7. フォルダ・ファイル構成

### 現時点の構成

```
ocr-worker/                       # OCR Worker ルート
├── app/                          # FastAPI アプリケーションコード
│   └── main.py                   # API エントリポイント（/ocr, /health）
├── docs/                         # ocr-worker 専用ドキュメント
│   ├── ocr-worker-system-spec.md # 本仕様書
│   ├── caveats.md                # 注意事項
│   ├── work_log.md               # 作業ログ
│   └── tasks.md                  # タスク管理表
├── Dockerfile                    # ocr-worker Docker イメージ（CPU 実行用）
└── .dockerignore                 # Docker ビルド除外ファイル（任意）
```

### 補足

- `Dockerfile` はプロジェクトルートの `docker-compose.yml` から参照される
- `app/main.py` は FastAPI アプリケーションであり、ndlocr_cli を import して OCR を実行する
- backend からの呼び出しは HTTP 経由であり、`app/main.py` が入出力を受け持つ

## 8. 注意事項

- ocr-worker に関する注意事項・トラブルシューティングは [caveats.md](./caveats.md) を参照
- 主な注意点として、以下がある
  - 公式 Dockerfile は GPU 用のため、CPU 実行用に自前で Dockerfile を作成している
  - 学習済みモデルのダウンロードにより、Docker ビルドに数十分程度かかる場合がある
  - `config.yml` の `device` 設定を `cpu` に変更している
  - mmdet 3.x の `init_detector` 引数順序の変更に対応している
  - `text_recognition_lightning` の callbacks / trainer を CPU 実行向けに書き換えている
  - KyTea はソースからビルドしてモデルファイルを配置している
