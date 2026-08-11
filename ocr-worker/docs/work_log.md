# 作業ログ

本ドキュメントは、book2pdf プロジェクトの ocr-worker タスク実施にあたり実行したコマンドとその結果を記録したものです。

---

## 2026-08-11 タスク001001：ndlocr_cli 実行環境の Docker コンテナ化

### 目的

ndlocr_cli を Python パッケージとして実行できる Docker コンテナ（ocr-worker）を構築する。

### 前提

- Docker Desktop がインストール済みであること
- プロジェクト全体で CPU 実行を前提としていること
- backend タスク 001001〜001003 が完了済みであること

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/ocr-worker

# ndlocr_cli リポジトリのファイル構成を確認
curl -sL https://api.github.com/repos/ndl-lab/ndlocr_cli/contents/ | jq -r '.[] | "\(.type) \(.path)"'

# .gitmodules を確認
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/.gitmodules

# requirements.txt を確認
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/requirements.txt

# XML 出力形式を確認
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/ndlocr-xmlformat.md

# 公式 Dockerfile を確認
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/docker/Dockerfile

# 推論コードを確認
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/cli/core/inference.py | head -n 120
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/cli/core/utils.py | head -n 200

# dockerbuild.sh を確認（モデルダウンロード URL の確認）
curl -sL https://raw.githubusercontent.com/ndl-lab/ndlocr_cli/master/docker/dockerbuild.sh

# 各 submodule の requirements.txt を確認
curl -sL https://raw.githubusercontent.com/ndl-lab/text_recognition_lightning/master/requirements.txt
curl -sL https://raw.githubusercontent.com/ndl-lab/ruby_prediction/master/requirements.txt
curl -sL https://raw.githubusercontent.com/ndl-lab/reading_order/master/requirements.txt

# Docker Desktop の状態確認
docker version --format '{{.Server.Version}}'
docker images --format '{{.Repository}}:{{.Tag}}'
docker ps --format '{{.Names}}\t{{.Status}}'
```

### 結果

- GitHub API 経由で ndlocr_cli リポジトリの構成を把握した
  - `cli/`：Python パッケージ
  - `submodules/`：推論に必要な submodule（separate_pages_mmdet, deskew_HT, ndl_layout, text_recognition_lightning, reading_order, ruby_prediction）
  - `docker/`：公式 Dockerfile（CUDA ベース）
  - `config.yml`：推論設定ファイル
  - `ndlocr-xmlformat.md`：XML 出力形式の仕様
- ndlocr_cli の XML 出力形式を確認した
  - ルート要素は `<OCRDATASET>`
  - ページごとに `<PAGE HEIGHT="..." WIDTH="..." IMAGENAME="...">`
  - テキスト行は `<LINE TYPE="..." X="..." Y="..." WIDTH="..." HEIGHT="..." STRING="..." ORDER="..." />`
  - 座標は左上原点
- 公式 Dockerfile は `nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04` ベースの GPU 用であることが分かった
- `dockerbuild.sh` から学習済みモデルのダウンロード URL を取得した
  - `resnet-orient2.ckpt`
  - `rf_author/model.pkl`
  - `rf_title/model.pkl`
  - `ndl_retrainmodel.pth`
  - `epoch_180.pth`
- CPU 実行用の `ocr-worker/Dockerfile` を新規作成した
  - `python:3.10-slim` ベース
  - PyTorch CPU 版をインストール
  - mmcv / mmdet CPU 版をインストール
  - モデルファイルを wget でダウンロード
  - `config.yml` の `device: 'cuda:0'` を `device: 'cpu'` に書き換え
- プロジェクトルートに `docker-compose.yml` を新規作成した
  - `backend` と `ocr-worker` コンテナを定義
  - 共有ボリューム（uploads, extracted, ocr_output, pdfs）を設定
- Docker Desktop が起動していることを確認した
  - Docker サーバー v29.6.2
  - book2pdf 関連のイメージ・コンテナはまだ未作成

### 注意事項

- Docker ビルドは PyTorch / mmcv / mmdet / モデルダウンロードを含むため、**数十分程度かかる可能性がある**
- 公式 Dockerfile は GPU 用なので、CPU 実行用に自前で Dockerfile を組み立てた
- モデルファイルは `lab.ndl.go.jp` から毎回ダウンロードするため、ビルド時間の大部分を占める
- `inference.py` は実行時に `submodules/` 以下を `sys.path.append` するため、コンテナ内のディレクトリ構造を正しく再現する必要がある

---

## 2026-08-11 タスク001001続き：コンテナビルド・動作確認

### 目的

作成した `ocr-worker/Dockerfile` が正しくビルドされ、ndlocr_cli が CPU 環境で実行できることを確認する。

### 前提

- 上記の Dockerfile / docker-compose.yml が作成済みであること
- サンプル画像 `data/uploads/sample/test.png` がホスト側に配置済みであること

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# コンテナのビルドと起動
docker compose down ocr-worker
docker compose build ocr-worker
docker compose up -d ocr-worker

# コンテナ内で import テスト
docker compose exec ocr-worker python -c "from cli.core import OcrInferrer; print('OK')"

# init_detector の CPU 動作確認
docker compose exec ocr-worker python -u -c "
import sys
sys.path.insert(0, '/opt/ocr-worker')
from submodules.separate_pages_mmdet.inference_divide import GutterDetector
det = GutterDetector(
    'submodules/separate_pages_mmdet/models/cascade_rcnn_r50_fpn_1x_ndl_1024.py',
    'submodules/separate_pages_mmdet/models/epoch_180.pth',
    'cpu'
)
print('OK')
"

# サンプル画像で OCR 実行
docker compose exec ocr-worker rm -rf /data/ocr_output/sample
docker compose exec ocr-worker python /opt/ocr-worker/main.py infer \
  /data/uploads/sample/test.png /data/ocr_output/sample -x -s f -c /opt/ocr-worker/config.yml

# 出力確認
docker compose exec ocr-worker ls -laR /data/ocr_output/sample
docker compose exec ocr-worker head -50 /data/ocr_output/sample/test/xml/test.sorted.xml
```

### 結果

- コンテナのビルド・起動に成功した
- `from cli.core import OcrInferrer` の import に成功した
- `GutterDetector` 経由で `init_detector` が CPU で動作することを確認した
- サンプル画像 `/data/uploads/sample/test.png` に対して OCR を実行し、正常に完了した
- 出力ファイルが生成された
  - `/data/ocr_output/sample/test/xml/test.sorted.xml`
  - `/data/ocr_output/sample/test/txt/test_main.txt`
  - `/data/ocr_output/sample/test/txt/test_ruby.txt`
  - `/data/ocr_output/sample/test/txt/test_cap.txt`
- XML 出力から、サンプル画像内のテキスト「Hello worud128」「Hello worlud 123」が検出された

### 発生した事象と対応

| 事象 | 原因 | 対応 |
|---|---|---|
| `init_detector` が `cuda:0` を要求 | mmdet 3.x の引数順序変更により `device` が無視されていた | `init_detector(config, checkpoint, device=device)` に sed で書き換え |
| `RuntimeError: Tried to instantiate dummy base class Event` | `text_recognition_lightning` の `MeasureTimeCallback` が `torch.cuda.Event` を使用 | `infer.yaml` から `measure_time.yaml` を削除 |
| `GPUAccelerator can not run on your system` | `text_recognition_lightning` の trainer が `accelerator: gpu` | `default.yaml` の `accelerator: gpu` を `cpu` に変更 |
| `Could not open model file /usr/local/share/kytea/model.bin` | KyTea の Python バインディングのみではモデルファイルが不足 | KyTea 0.4.7 をソースからビルド・インストール |
| `make: not found` | Dockerfile に `make` が含まれていなかった | apt-get で `make` を追加 |

### 注意事項

- 各種対応は `ocr-worker/Dockerfile` に sed やパッケージ追加として記録済み
- 今後 ndlocr_cli 側のバージョンアップで sed の対象行が変わる可能性があるため、ビルド時のエラーを確認すること
- サンプル画像は手書き風のテキストを含んでおり、OCR 誤認識（`Hello world` → `Hello worud` など）が発生する可能性がある

---

## 2026-08-11 タスク001002：ocr-worker HTTP API の実装

### 目的

ocr-worker コンテナ内に FastAPI ベースの HTTP API を実装し、
backend コンテナから画像パスを受け取って OCR 処理を実行し、結果を返せるようにする。

### 前提

- タスク001001 で ocr-worker コンテナが CPU 実行可能な状態であること
- backend から ocr-worker の `/ocr` エンドポイントを呼び出す実装が必要

### 実施コマンド

```bash
# ocr-worker アプリケーションの作成
cd /Users/hisao/Documents/work4/sakura/book2pdf
mkdir -p ocr-worker/app
cat > ocr-worker/app/main.py << 'EOF'
...（省略）...
EOF

# Dockerfile の修正（FastAPI / Uvicorn 対応）
vi ocr-worker/Dockerfile

# docker-compose.yml の修正（共有ボリューム・ヘルスチェック対応）
vi docker-compose.yml

# コンテナの再ビルド・再起動
docker compose down
docker compose build --no-cache ocr-worker
docker compose up -d

# ヘルスチェック確認
curl -s http://localhost:8001/health

# backend 側からの OCR テスト
curl -s -X POST http://localhost:8000/api/jobs/ | jq
curl -s -X POST \
  -F "file=@/tmp/book2pdf-test/sample.zip;type=application/zip" \
  http://localhost:8000/api/jobs/{job_id}/upload | jq
curl -s --max-time 600 \
  -X POST http://localhost:8000/api/jobs/{job_id}/ocr | jq
```

### 結果

- `ocr-worker/app/main.py` を新規作成
  - `POST /ocr` エンドポイントを実装
  - リクエスト：画像パス（backend 側の共有ボリュームパス）
  - レスポンス：`text`（認識テキスト）、`success`、`error`
- `ocr-worker/Dockerfile` を更新
  - `app/main.py` をコピー
  - `fastapi`、`uvicorn`、`python-multipart` を追加
  - 起動コマンドを `uvicorn app.main:app --host 0.0.0.0 --port 8000` に変更
- `docker-compose.yml` を更新
  - `ocr-worker` に `/data/uploads` と `/data/extracted` の共有ボリュームを追加
  - backend から ocr-worker サービス名による通信ができるようにネットワーク設定を確認
  - `backend` に `OCR_WORKER_URL=http://ocr-worker:8000` 環境変数を追加
  - `ocr-worker` にヘルスチェックを追加
  - `backend` の `depends_on` に `ocr-worker` の `condition: service_healthy` を追加
- `ocr-worker` コンテナを再ビルド・再起動
- `http://localhost:8001/health` で `{"status":"ok"}` を確認
- backend からサンプル画像 2 枚を ZIP アップロードし、`POST /api/jobs/{job_id}/ocr` を実行
- ジョブ状態が `completed` になり、OCR テキストがレスポンスに含まれることを確認

### 注意事項

- `POST /ocr` へ渡す画像パスは、backend と ocr-worker の両方からアクセス可能な
  共有ボリューム上のパスである必要がある
- ocr-worker 内の Uvicorn はポート 8000 でリッスンしており、
  Docker Compose 上ではホストの 8001 番にマップされている
  - backend 側からは `http://ocr-worker:8000` でアクセスする
- 初回の ndlocr_cli 推論時はモデルの初期化などにより時間がかかる
- 大きな画像や多数のページを処理する場合はタイムアウト設定に注意

