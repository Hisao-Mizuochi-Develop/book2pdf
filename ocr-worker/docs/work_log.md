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
    'submodels/separate_pages_mmdet/models/epoch_180.pth',
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

---

## 2026-08-11 タスク001002続き：結合テストでの GlobalHydra エラー修正

### 目的

backend → ocr-worker 連携の結合テストを実施し、発生した `GlobalHydra` 初期化エラーを修正する。

### 前提

- タスク001002 で ocr-worker HTTP API の実装が完了していること
- backend / ocr-worker / frontend が Docker Compose で起動していること
- テスト用の ZIP ファイル（PNG 画像 2 枚）が用意されていること

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# テスト用 ZIP 作成
mkdir -p /tmp/book2pdf-test
# （2 枚のサンプル画像を /tmp/book2pdf-test/001.png, 002.png として配置）
cd /tmp/book2pdf-test && zip -r sample.zip 001.png 002.png

# frontend 開発サーバー起動確認
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000

# backend 結合テスト（ジョブ作成 → アップロード → OCR）
JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
curl -s -X POST -F "file=@/tmp/book2pdf-test/sample.zip;type=application/zip" \
  "http://localhost:8000/api/jobs/$JOB_ID/upload" | jq .
curl -s --max-time 600 -X POST "http://localhost:8000/api/jobs/$JOB_ID/ocr" | jq .
```

### 結果

- 初回の OCR リクエストは成功したが、2 回目以降のリクエストで以下のエラーが発生した
  - `ValueError: GlobalHydra is already initialized`
- 原因は `ocr-worker/app/main.py` 内で `infer` 関数が `hydra.initialize()` を毎回呼び出していたこと
  - 1 回目は問題ないが、同じ Python プロセス内で 2 回目以降を実行すると衝突する
- 対応として `infer` 関数の先頭で `GlobalHydra.instance().is_initialized()` を確認し、
  既に初期化済みの場合は `clear()` してから `initialize()` するように修正した
- 修正後、backend コンテナと ocr-worker コンテナを再ビルド・再起動した
- 再度結合テストを実施し、複数回の OCR リクエストが正常に完了することを確認した
  - ジョブ状態が `completed` になり、認識テキストがレスポンスに含まれることを確認

### 注意事項

- Hydra の GlobalHydra は同一プロセス内で複数回 `initialize()` できない
- ocr-worker は Uvicorn worker プロセスを使い回すため、リクエストごとに reinitialize が必要
- 将来的に `hydra.compose()` など別の方法に切り替える場合は、この clear/initialize パターンを見直す

---

## 2026-08-12 タスク002001：ocr-worker DEBUG ログ・計測処理の追加

### 目的

性能計測時に ocr-worker 内の OCR 処理所要時間を DEBUG ログで確認できるようにする。

### 前提

- タスク001002 までで ocr-worker HTTP API が実装済みであること
- `ocr-worker/app/main.py` が存在すること
- `docker-compose.yml` で ocr-worker サービスが定義されていること

### 実施コマンド

```bash
# ソース変更は手動で実施
# 以下、変更後のファイル内容確認
cd /Users/hisao/Documents/work4/sakura/book2pdf

git diff -- ocr-worker/app/main.py
git diff -- docker-compose.yml
```

### 結果

- `ocr-worker/app/main.py` に `LOG_LEVEL` 環境変数に応じたロガー設定を追加した
- `POST /ocr` エンドポイントの `infer` 関数の開始・完了・所要時間を DEBUG ログに出力するようにした
- `docker-compose.yml` の ocr-worker サービスに `LOG_LEVEL=DEBUG` を追加した
- `ocr-worker/docs/tasks.md` にタスク 002001 を追記した
- `ocr-worker/docs/work_log.md` に本エントリを追記した

### 注意事項

- `LOG_LEVEL=DEBUG` 時には OCR 処理の詳細な DEBUG ログが出力される
- 本番環境では `LOG_LEVEL=INFO` に設定することを推奨する
- ndlocr_cli 内部のログも `LOG_LEVEL` に応じて増減する可能性があるため、注意が必要

---

## 2026-08-13 タスク004003（一部）：ndlocr_cli ページ処理時間 DEBUG ログの追加

### 目的

backend 004003「OCR 処理性能計測の実施」のうち、ユーザー指示により ocr-worker 側で 1 ページごとの OCR 処理時間を DEBUG ログで出力できるようにする。

### 前提

- `ocr-worker/ndlocr_cli_patches/inference.py` が `ocr-worker/Dockerfile` によって `${PROJECT_DIR}/cli/core/inference.py` にコピーされる構成であること
- `ocr-worker/ndlocr_cli_patches/inference.py` に既に「ページ処理完了」の DEBUG ログが存在すること
- `LOG_LEVEL` 環境変数によって DEBUG ログの出力を切り替えられること

### 実施コマンド

```bash
# シンタックスチェック
cd /Users/hisao/Documents/work4/sakura/book2pdf
python3 -m py_compile ocr-worker/ndlocr_cli_patches/inference.py
```

### 結果

- `ocr-worker/ndlocr_cli_patches/inference.py` を修正した
  - `_infer()`（通常 OCR モード）で `for page_idx, img_path in enumerate(single_outputdir_data['img_list'], start=1)` とし、ページ番号を 1 始まりで扱うようにした
  - ページ処理開始時に `logger.debug(f'[ndlocr_cli] ページ処理開始: page={page_idx}, img_path={img_path}')` を追加
  - ページ処理完了時に `page=N` を含む形式に統一: `logger.debug(f'[ndlocr_cli] ページ処理完了: page={page_idx}, img_path={img_path}, elapsed={elapsed_page:.3f}s')`
  - `_infer_ruby_only()`（ルビ推定モード）でも同様に開始・完了ログに `page=N` を含めるように統一
- `ocr-worker/docs/work_log.md` に本エントリを追記した

### 注意事項

- 本パッチは `ocr-worker/Dockerfile` の `COPY` 命令によってコンテナイメージ構築時に適用される
- したがって、ホスト側の修正を反映するには ocr-worker イメージの再ビルドが必要
  - `docker compose up -d --build ocr-worker`
- DEBUG ログは `LOG_LEVEL=DEBUG` 時にのみ出力される
- 性能計測の実行と結果のドキュメント記録は、ユーザー指示により今回は実施しない

---

## 2026-08-13 タスク003001：ocr-worker OCR 実行時 500 エラーの原因調査・修正

### 目的

backend 経由で OCR 実行時に ocr-worker が 500 Internal Server Error を返す問題の原因を特定し、修正する。

### 前提

- docker compose で backend / ocr-worker / frontend の 3 コンテナが起動済み
- `test_zips/sample_002-004.zip`（002.png, 003.png, 004.png）を作成済み
- backend の `/api/jobs/{job_id}/upload` には `Content-Type: application/zip` を明示すると正常にアップロードできることを確認済み

### 調査計画

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# ocr-worker コンテナ内で /ocr エンドポイントを直接呼び出し
docker compose exec ocr-worker python -c "
import traceback
from app.main import infer
try:
    result = infer('/data/extracted/54302f97-2dba-405d-9950-a141a9761f11', '/data/ocr_output/54302f97-2dba-405d-9950-a141a9761f11')
    print(result)
except Exception as e:
    traceback.print_exc()
"

# ocr-worker ログ確認
docker compose logs --tail 100 ocr-worker
```

### 結果

- `ocr-worker/app/main.py` のエラーハンドリングを改善し、例外発生時に `traceback.format_exc()` で詳細なスタックトレースをログと HTTP レスポンスに含めるようにした
- ocr-worker コンテナ内で直接 `/ocr` 相当の OCR 呼び出しを実行したところ、以下のエラーが発生した
  - `ModuleNotFoundError: No module named 'pkg_resources'`
- 原因は `pytorch_lightning` が import 時に `pkg_resources` を参照しているが、
  `python:3.10-slim` ベースイメージに `setuptools` が含まれていないためだった
- 最初の対応として `ocr-worker/Dockerfile` に `RUN pip install --no-cache-dir setuptools` を追加したが、
  2026-08-13 時点の最新版 `setuptools 84.0.0` では `pkg_resources` が削除されていたため、
  `setuptools==79.0.1` を明示的にインストールするよう修正した
- 以下の手順で修正を反映した
  - `docker compose down ocr-worker`
  - `docker compose up -d --build ocr-worker`
- 再ビルド後、ocr-worker コンテナ内で直接 OCR 実行したところ、3 ページ（002.png, 003.png, 004.png）の OCR が正常に完了した
  - 出力ファイル：`/data/ocr_output/54302f97-2dba-405d-9950-a141a9761f11_20260813054308/input/txt/002_main.txt` など
  - 進捗ファイル：`/data/progress/debug-003001.json` が `status: "completed"`、`progress: 1.0` となった
- backend 経由でも OCR 実行を再検証した
  - ジョブ作成：`curl -s -X POST http://localhost:8000/api/jobs/`
  - ZIP アップロード：`curl -s -X POST -F "file=@test_zips/sample_002-004.zip;type=application/zip" http://localhost:8000/api/jobs/{job_id}/upload`
  - OCR 実行：`curl -s --max-time 1800 -X POST http://localhost:8000/api/jobs/{job_id}/ocr`
  - ジョブ状態：`curl -s http://localhost:8000/api/jobs/{job_id}` が `status: "completed"`、`message: "PDF 生成が完了しました"` を返した
- 再ビルド後のコンテナで `import pkg_resources` が成功することも確認した
  - `DeprecationWarning` は表示されるが、import 自体は成功する

### 発生した事象と対応

| 事象 | 原因 | 対応 |
|---|---|---|
| OCR 実行時に 500 エラー | `pytorch_lightning` が `pkg_resources` を参照するが、コンテナに `setuptools` がなかった | `ocr-worker/Dockerfile` に `setuptools==79.0.1` を追加 |
| `pkg_resources` の `ModuleNotFoundError` | 最新版 `setuptools 84.0.0` では `pkg_resources` が削除されている | バージョンを `79.0.1` に固定 |
| エラーの詳細がログに出ていない | `ocr-worker/app/main.py` の例外処理が `str(e)` のみ | `traceback.format_exc()` でスタックトレースをログ・レスポンスに含める |

### 注意事項

- `setuptools` のバージョン固定を怠ると、将来の `setuptools` 更新で同様の問題が再発する可能性がある
- `pkg_resources` は非推奨 API なので、`pytorch_lightning` 側で `importlib.metadata` などに移行されることを期待する
- 修正内容は `ocr-worker/docs/caveats.md` の「17. `setuptools` のバージョンは 79.0.1 に固定する」「18. エラーハンドリングでトレースバックをログに出力する」にも記録した

---

## 2026-08-13 タスク003002：現状 OCR 認識精度の再測定

### 目的

OCR 精度向上施策を検討する前に、現状の ndlocr_cli（CPU 実行）の認識精度を定量的・定性的に把握する。

### 前提

- タスク 003001 で OCR 実行時の 500 エラーが解消済みであること
- 既存の `benchmark-ocr-003002.zip`（002.png, 003.png, 004.png）が利用可能であること
- Docker Compose で backend / ocr-worker / frontend の 3 コンテナが起動していること

### 測定計画

1. 環境クリーンアップ：コンテナ内 `/data/extracted/*`、`/data/ocr_output/*`、`/data/pdfs/*` と、ホスト側 `/tmp/book2pdf-*` を削除する
2. テスト用 ZIP の確認：`benchmark-ocr-003002.zip` の内容を `unzip -l` で確認する
3. Docker Compose 起動：`docker compose up -d --build` で最新イメージで起動する
4. OCR 実行：backend API から ZIP をアップロードし、backend → ocr-worker 経由で OCR を実行する
5. 成果物取得：ocr-worker 出力の XML ファイル、テキストファイル、backend 生成 PDF をホスト側にコピーする
6. 精度解析：元画像と OCR 結果テキストを比較し、英数字・記号・漢字・異体字などの認識ミスを一覧化する。定量的には CER（Character Error Rate）を算出し、目視確認も併用する
7. ドキュメント記録：測定結果を `ocr-worker/docs/work_log.md` / `ocr-worker/docs/tasks.md` に記録する

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# 1. 環境クリーンアップ
docker compose exec backend sh -c 'rm -rf /data/extracted/* /data/ocr_output/* /data/pdfs/*'
docker compose exec ocr-worker sh -c 'rm -rf /data/ocr_output/* /data/extracted/*'
rm -rf /tmp/book2pdf-*

# 2. テスト用 ZIP の確認
unzip -l benchmark-ocr-003002.zip

# 3. Docker Compose 起動
docker compose up -d --build

# 4. OCR 実行
JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
curl -s -X POST -F "file=@benchmark-ocr-003002.zip;type=application/zip" \
  "http://localhost:8000/api/jobs/$JOB_ID/upload" | jq .
curl -s --max-time 1800 -X POST "http://localhost:8000/api/jobs/$JOB_ID/ocr" | jq .
curl -s "http://localhost:8000/api/jobs/$JOB_ID" | jq .

# 5. 成果物取得
mkdir -p ocr-results-003002/source ocr-results-003002/extracted ocr-results-003002/pdfs
unzip -j benchmark-ocr-003002.zip -d ocr-results-003002/source/
# ジョブ情報から output_dir / pdf_path を確認
curl -s "http://localhost:8000/api/jobs/$JOB_ID" | jq -r '.output_dir'
curl -s "http://localhost:8000/api/jobs/$JOB_ID" | jq -r '.pdf_path'
# 実測時のジョブ情報例
# output_dir: /data/extracted/aca976fb-db10-47f1-847e-97ecf9b38ae5/output_20260813101634
# pdf_path:   /data/pdfs/aca976fb-db10-47f1-847e-97ecf9b38ae5.pdf
docker compose cp "backend:/data/extracted/aca976fb-db10-47f1-847e-97ecf9b38ae5/output_20260813101634" ocr-results-003002/extracted/
docker compose cp "backend:/data/pdfs/aca976fb-db10-47f1-847e-97ecf9b38ae5.pdf" ocr-results-003002/pdfs/
```

### 結果

- ジョブ ID: `aca976fb-db10-47f1-847e-97ecf9b38ae5`
- 測定対象: `benchmark-ocr-003002.zip`（002.png 表紙、003.png 注意書き、004.png 本文）
- OCR 実行は正常に完了し、ジョブ状態が `completed` となった
- 出力ファイルを `ocr-results-003002/` に取得した
  - `ocr-results-003002/extracted/output_20260813101634/input/xml/input.sorted.xml`
  - `ocr-results-003002/extracted/output_20260813101634/input/txt/002_main.txt`
  - `ocr-results-003002/extracted/output_20260813101634/input/txt/003_main.txt`
  - `ocr-results-003002/extracted/output_20260813101634/input/txt/004_main.txt`
  - `ocr-results-003002/pdfs/aca976fb-db10-47f1-847e-97ecf9b38ae5.pdf`
- 認識精度レポートを新規作成した
  - `ocr-results-003002/ocr-accuracy-report-003002.md`
- 主な測定結果
  - 全体文字数: 約 1,327 文字
  - 「〓」出現数: 5 回
  - 明らかな誤認識箇所: 002.png で約 7 箇所、003.png で約 5 箇所、004.png で約 8 箇所
  - 推定文字レベル誤り率（CER 推定）: 約 1〜3%（表紙ページはより高い）
- 主な誤認識パターン
  - 英数字頭文字: G→〓、I→（欠落）、L→l など
  - 記号: ■→K、(→〓、®/™→〓 など
  - 漢字の部品類似: 商→育、題→乃、夫→ヲ、存→右 など
  - 異体字・旧字体: 年→年、理→理 など
  - 語尾・助詞: つ→っ、に→4 など
- 重要な発見
  - XML の `CONF` 値は 0.998〜1.000 と非常に高いが、実際には明らかな誤認識が含まれていた
  - つまり、ndlocr_cli は誤認識結果に対しても高い信頼度を出力する傾向がある

### 注意事項

- 正解テキストがないため、CER は厳密には算出できず、推定値とする
- 目視確認では、英数字・記号・漢字の部品類似誤認識が主要な問題として浮上した
- CONF 値だけを信頼せず、目視確認や後処理による精度向上が必要
- 測定結果の詳細は `ocr-results-003002/ocr-accuracy-report-003002.md` を参照


---

## 2026-08-13 タスク003003：入力画像前処理の効果検証

### 目的

003001 で特定した誤認識パターン（英数字頭文字・記号・漢字部品類似）に対し、入力画像前処理の効果を定量的に検証する。

### 前提

- タスク 003002 で benchmark-ocr-003002.zip（002.png, 003.png, 004.png）の現状認識精度が把握済みであること
- scripts/preprocess_image.py が作成済みであること
- Docker Compose で backend / ocr-worker / frontend の 3 コンテナが起動していること

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# 前処理パターンごとの ZIP 生成
python scripts/preprocess_image.py benchmark-ocr-003002.zip benchmark-ocr-003003-sharpen.zip sharpen_light
python scripts/preprocess_image.py benchmark-ocr-003002.zip benchmark-ocr-003003-sharpen-upscale.zip sharpen_light_upscale_2x
python scripts/preprocess_image.py benchmark-ocr-003002.zip benchmark-ocr-003003-contrast-gamma.zip contrast_gamma
python scripts/preprocess_image.py benchmark-ocr-003002.zip benchmark-ocr-003003-contrast-gamma-sharpen.zip contrast_gamma_sharpen_light

# 各パターンで backend API 経由で OCR を実行
# （ジョブ作成 → ZIP アップロード → OCR 実行 → 成果物取得）
# baseline は 003001 の結果を流用
```

### 結果

- baseline（前処理なし）は 003001 と同一条件のため、本タスクでは再実行せず ocr-results-003002/ の結果を比較基準として使用した
- 前処理 4 パターン（sharpen_light / sharpen_light_upscale_2x / contrast_gamma / contrast_gamma_sharpen_light）で OCR を実行し、結果を ocr-results-003003/ に取得した
- 各パターンの「〓」出現数：
  - baseline: 5
  - sharpen_light: 7
  - sharpen_light_upscale_2x: 3
  - contrast_gamma: 7
  - contrast_gamma_sharpen_light: 6
- 最も効果的だったのは sharpen_light_upscale_2x（2 倍アップスケーリング＋軽度シャープニング）
  - 003.png・004.png でほぼ完全な認識を実現
  - 英数字頭文字欠落・記号置換・小文字化などの誤認識が大幅に改善
- contrast_gamma は逆に文字の濁りやノイズを強調し、記号・英数字の誤認識を増加させる傾向があった
- 精度比較レポートを ocr-results-003003/preprocess-comparison-report-003003.md に作成した

### 注意事項

- baseline は 003001 と同一条件のため再実行せず、結果を流用した
- 前処理による処理時間増加の影響は今回定量的に測定していない
- 表紙ページ（002.png）は元の文字サイズ・デザインの影響から、依然として一部の誤認識が残った
- 詳細な比較結果は ocr-results-003003/preprocess-comparison-report-003003.md を参照

---

## 2026-08-13 タスク003004：config.yml パラメータ調整の効果検証

### 目的

003002 で最も効果的だった `sharpen_light_upscale_2x` 適用済み画像に対し、ndlocr_cli の config.yml パラメータ調整がさらなる精度向上に寄与するかを検証する。

### 前提

- タスク 003003 で `sharpen_light_upscale_2x` が最も効果的だったことが分かっていること
- コンテナ内の config.yml（/opt/ocr-worker/config.yml）を確認済みで、調整可能な閾値は `layout_extraction.score_thr: 0.3` のみであること
- `line_ocr.score_thr` は存在せず、`line_ocr.additional_elements`（柱/ノンブル/ルビの有無）のみ調整可能であること
- Docker Compose で backend / ocr-worker / frontend の 3 コンテナが起動していること

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# 1. コンテナ内 config.yml の内容確認
docker compose exec ocr-worker cat /opt/ocr-worker/config.yml

# 2. オリジナル config.yml のバックアップ作成
docker compose exec ocr-worker cp /opt/ocr-worker/config.yml /tmp/config-original.yml

# 3-1. Pattern A: score_thr 0.2
docker compose exec ocr-worker sed -i "s/score_thr: 0.3/score_thr: 0.2/g" /opt/ocr-worker/config.yml
docker compose exec ocr-worker cat /opt/ocr-worker/config.yml | grep score_thr
# → 確認後、OCR 実行
JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
curl -s -X POST -F "file=@benchmark-ocr-003003-sharpen-upscale.zip;type=application/zip" \
  "http://localhost:8000/api/jobs/$JOB_ID/upload" | jq .
curl -s --max-time 1800 -X POST "http://localhost:8000/api/jobs/$JOB_ID/ocr" | jq .

# 3-2. Pattern B: score_thr 0.1（Pattern A 実行後、さらに変更）
docker compose exec ocr-worker sed -i "s/score_thr: 0.2/score_thr: 0.1/g" /opt/ocr-worker/config.yml
docker compose exec ocr-worker cat /opt/ocr-worker/config.yml | grep score_thr
# → 確認後、OCR 実行

# 3-3. Pattern C: score_thr 0.2 + additional_elements 無効化
docker compose exec ocr-worker cp /tmp/config-original.yml /opt/ocr-worker/config.yml
docker compose exec ocr-worker sed -i "s/score_thr: 0.3/score_thr: 0.2/g" /opt/ocr-worker/config.yml
docker compose exec ocr-worker sed -i "s/  柱: True/  柱: False/g" /opt/ocr-worker/config.yml
docker compose exec ocr-worker sed -i "s/  ノンブル: True/  ノンブル: False/g" /opt/ocr-worker/config.yml
docker compose exec ocr-worker sed -i "s/  ルビ: True/  ルビ: False/g" /opt/ocr-worker/config.yml
docker compose exec ocr-worker cat /opt/ocr-worker/config.yml
# → 確認後、OCR 実行

# 4. 結果を ocr-results-003004/<pattern>/ に保存

# 5. config.yml を元に戻す
docker compose exec ocr-worker cp /tmp/config-original.yml /opt/ocr-worker/config.yml
```

### 結果

#### Pattern A: score_thr 0.2
- ジョブ ID: `4087d086-4b45-4ca2-a1c4-7af8f1f17a9e`
- OCR 完了、成果物を `ocr-results-003004/pattern-a/` に取得

#### Pattern B: score_thr 0.1
- ジョブ ID: `b4cf5a45-4893-45ec-9c78-9be5ccab2144`
- OCR 完了、成果物を `ocr-results-003004/pattern-b/` に取得

#### Pattern C: score_thr 0.2 + additional_elements 無効化
- ジョブ ID: `56f1ec06-16a3-47bc-85bb-804790d43953`
- OCR 完了、成果物を `ocr-results-003004/pattern-c/` に取得

#### 精度比較

| パターン | 「〓」出現数 | 002_main | 003_main | 004_main |
|---|---|---|---|---|
| **baseline** | **3** | 2 | 1 | 0 |
| **pattern A** | **3** | 2 | 1 | 0 |
| **pattern B** | **3** | 2 | 1 | 0 |
| **pattern C** | **3** | 2 | 1 | 0 |

- baseline（003002 の sharpen_light_upscale_2x）と比較して、すべてのパターンで **完全一致**
- `diff` コマンドで `_main.txt`、`_ruby.txt`、`.xml` を比較した結果、**すべてのファイルで差分なし**
- config.yml のパラメータ調整は、少なくとも本テストデータセットにおいては **OCR 精度に影響を与えなかった**

### config.yml 調整が効果を持たなかった理由（推測）

1. **ハードコードされた閾値**: ndlocr_cli のソースコード内部で `score_thr` が固定値でハードコードされており、config.yml の値が参照されていない可能性がある
2. **別の設定ファイルが優先**: モデルの学習済み重みや推論パイプラインが独自のパラメータを持っており、config.yml の値が無視されている可能性がある
3. **該当セクションの未使用**: `layout_extraction.score_thr` は領域検出の閾値だが、使用しているモデルの推論フローではこのパラメータが参照されていない可能性がある
4. **additional_elements の影響範囲**: `line_ocr.additional_elements` の柱/ノンブル/ルビ設定は後処理の出力選択に影響する可能性があるが、`_main.txt` には既に選別済みのテキストが含まれている

### 注意事項

- config.yml の調整は一時的なものであり、テスト完了後に必ず元の値（score_thr: 0.3、柱/ノンブル/ルビ: True）に戻した
- `score_thr` を下げすぎるとノイズや見出し線まで文字として認識するリスクがあるが、本テストでは差分が出なかったため実際の影響は不明
- ndlocr_cli のソースコード（`cli/core/inference.py` や各 submodule）を確認し、config.yml の値が実際にどこで参照されているかを追跡する必要がある
- 精度比較レポートは `ocr-results-003004/config-comparison-report.md` を参照

---

## 003005: OCR精度向上の統合検討と実装修正

- 日時: 2026-08-14（実施中）
- 目的: 003003・003004 の調査結果を統合し、config.yml パラメータ修正・自動前処理統合・表紙残存誤認識対策を実装・動作確認する
- 前提:
  - 003003 で `sharpen_light_upscale_2x` が最も効果的であることが確認済み
  - 003004 で config.yml の `layout_extraction.score_thr` 調整に効果なし（ハードコードと推測）
  - `benchmark-ocr-003002.zip`（002.png, 003.png, 004.png）をテストデータとして使用
  - 作業ディレクトリ: `/Users/hisao/Documents/work4/sakura/book2pdf`

### 実施コマンド

#### 1. config.yml パラメータ無視の原因調査

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# ndlocr_cli ソースを確認
cat ocr-worker/ndlocr_cli_patches/inference.py

# ハードコードされた閾値を検索
docker compose exec ocr-worker grep -rn "score_thr" /opt/ocr-worker/ 2>/dev/null | grep -v __pycache__ | head -40
```

#### 2. 調査結果

- `submodules/ndl_layout/tools/process_textblock.py` と `process.py` に `score_thr: float = 0.3` がハードコードされていることを発見
- config.yml の `layout_extraction.score_thr` は ndl_layout モジュールに渡されていないことが判明
- `ocr-worker/ndlocr_cli_patches/inference.py` に `ConfigPatcher` クラスを追加し、パッチを適用する方針を検討中

#### 3. 実装計画（承認済み）

**修正1: `ocr-worker/ndlocr_cli_patches/inference.py`**
- `ConfigPatcher` クラスを追加
- `__init__` で config.yml 値を取得し、コンテナ内の `process_textblock.py` と `process.py` 内の `score_thr: float = 0.3` を動的に上書き
- `infer()` の初回実行時にパッチを適用

**修正2: `ocr-worker/app/main.py`**
- `PreprocessEngine` クラスを追加し、`sharpen_light_upscale_2x` の自動前処理を実装
- `OcrWorker.__init__` で `PreprocessEngine` インスタンス化
- `infer()` で前処理ON/OFFを制御（デフォルトON、環境変数 `PREPROCESS_ENABLED=false` でOFF）

**修正3: 表紙専用前処理**
- `scripts/preprocess_cover.py` を新規作成
- 002.png に対して 4x アップスケール＋強力シャープニングを適用
- XML の分類結果（表紙ページか本文ページか）を基に、表紙のみ追加前処理を適用

#### 4. 動作確認計画（実施前）

```bash
# コンテナリビルド
docker compose build ocr-worker --no-cache
docker compose up -d ocr-worker

# 前処理ONでOCR実行
docker compose exec backend rm -rf /data/extracted/* /data/ocr_output/* /data/pdfs/*
docker compose exec ocr-worker rm -rf /data/ocr_output/* /data/extracted/*

JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
curl -s -X POST -F "file=@benchmark-ocr-003002.zip;type=application/zip" \
  "http://localhost:8000/api/jobs/$JOB_ID/upload" | jq .
curl -s --max-time 1800 -X POST "http://localhost:8000/api/jobs/$JOB_ID/ocr" | jq .

# 前処理OFFでOCR実行（PREPROCESS_ENABLED=falseを設定して再起動後）
# ...
```

### 調査結果

- `submodules/ndl_layout/tools/process_textblock.py` と `process.py` に `score_thr: float = 0.3` がハードコードされていることを発見
- `InferencerWithCLI` クラスでは `conf_dict`（config.yml から読み込んだ値）を受け取っているが、`score_thr` を推論時に渡していないことが判明
- `LayoutDetector.predict()` は `inference_detector(model, img)` を呼んでおり、`score_thr` キーワード引数を受け取っていない
- `convert_to_xml_string_with_data()` / `convert_to_xml_string2()` もデフォルト引数 `score_thr: float = 0.3` を使用しており、config.yml の値が反映されていない

### 修正内容

**修正1: `ocr-worker/ndlocr_cli_patches/process_textblock.py` を新規作成**

- `InferencerWithCLI.__init__` で `conf_dict.get('score_thr', 0.3)` を `self.score_thr` に保持するように変更
- `inference_with_cli` メソッドで `score_thr` 引数が未指定の場合は `self.score_thr` を使用
- `LayoutDetector.predict()` に `score_thr` キーワード引数を追加し、`inference_detector(model, img, score_thr=score_thr)` を呼び出すように変更
- `convert_to_xml_string_with_data()` / `convert_to_xml_string2()` に `score_thr` を明示的に渡すように変更

**修正2: `ocr-worker/Dockerfile` を更新**

- 既存の `COPY ndlocr_cli_patches/inference.py ...` の下に、新たに `process_textblock.py` をコピーする行を追加
- これにより Docker イメージ構築時にパッチが自動適用される

```dockerfile
# FIX(003005): config.yml の score_thr が無視される問題を修正
# ndl_layout submodule の process_textblock.py をパッチ版で上書きします
COPY ndlocr_cli_patches/process_textblock.py ${PROJECT_DIR}/submodules/ndl_layout/tools/process_textblock.py
```

### 動作確認

- `docker compose build ocr-worker --no-cache` でコンテナをリビルド
- `docker compose up -d ocr-worker` で起動
- コンテナ内 `/opt/ocr-worker/config.yml` の `layout_extraction.score_thr` を一時的に変更し、同一画像で OCR 実行
- 確認結果:
  - score_thr=0.2 と score_thr=0.1 は同一の出力（TEXTBLOCK 数 5）
  - score_thr=0.5 では低 CONF の見出し行が欠落し、TEXTBLOCK 数が 3 に減少
  - config.yml の `layout_extraction.score_thr` が実際に反映されることを定量的に確認

### 結果

- config.yml の `layout_extraction.score_thr` が無視されていた問題を解消
- Docker ビルド時に `process_textblock.py` をパッチ版で上書きすることで、最小限の変更で修正を実現
- 003004 のパラメータ変更が効果を持たなかった原因が、ハードコードされた `score_thr` にあったことを確認
- 本タスクでは score_thr 修正・再検証にスコープを絞り、自動前処理統合と表紙ページ対策は今後のタスクとして保留

### 注意事項

- ndl_layout submodule の修正はパッチファイルによる上書きで行うため、ndlocr_cli 本体のリポジトリは変更しない
- パッチは Docker イメージ構築時に適用される。ホスト側の修正を反映するには ocr-worker イメージの再ビルドが必要
- 将来 ndlocr_cli のバージョンアップで `process_textblock.py` の構造が変わる可能性があるため、パッチ適用後の動作確認が必要
- 前処理の一時ファイルクリーンアップと表紙ページ対策は別タスクで実施する


## 2026-08-14 タスク003005再検証：backend API 経由フルフローでの score_thr 比較

### 目的

タスク 003005 で実施した score_thr 修正・検証を、`.clinerules` 第 10 章に基づき backend API 経由のフルフローで再実施し、backend 生成 PDF を含めた精度比較を行う。

### 前提

- `ocr-worker/ndlocr_cli_patches/process_textblock.py` パッチにより、`layout_extraction.score_thr` が反映される状態であること
- backend / ocr-worker コンテナが `docker compose up -d` で起動していること
- `benchmark-ocr-003002.zip`（002.png, 003.png, 004.png）が存在すること

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# Pattern-A: score_thr=0.2
docker compose exec ocr-worker sed -i 's/^  score_thr: .*/  score_thr: 0.2/' /opt/ocr-worker/config.yml
docker compose exec ocr-worker sed -n '/^layout_extraction:/,/^line_ocr:/p' /opt/ocr-worker/config.yml | grep score_thr
docker compose exec backend sh -c 'rm -rf /data/extracted/* /data/ocr_output/* /data/pdfs/*'
docker compose exec ocr-worker sh -c 'rm -rf /data/ocr_output/* /data/extracted/*'
JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
curl -s -X POST -F "file=@benchmark-ocr-003002.zip;type=application/zip" http://localhost:8000/api/jobs/$JOB_ID/upload | jq .
curl -s --max-time 1800 -X POST http://localhost:8000/api/jobs/$JOB_ID/ocr | jq .
# ポーリング（status=completed まで）
docker compose cp backend:/data/pdfs/$JOB_ID.pdf ocr-results-003005/pattern-a/pdfs/
docker compose cp backend:/data/extracted/$JOB_ID/output_<timestamp> ocr-results-003005/pattern-a/output_<timestamp>

# Pattern-B: score_thr=0.1
docker compose exec ocr-worker sed -i 's/^  score_thr: .*/  score_thr: 0.1/' /opt/ocr-worker/config.yml
# （Pattern-A と同様のフルフロー）

# Pattern-C: score_thr=0.5
docker compose exec ocr-worker sed -i 's/^  score_thr: .*/  score_thr: 0.5/' /opt/ocr-worker/config.yml
# （Pattern-A と同様のフルフロー）
```

### 結果

- Pattern-A: ジョブ `9c09ae26-bc1b-48e8-a0e1-5408ce42a3a6`、status: completed、PDF 22,368,443 bytes
- Pattern-B: ジョブ `a4345c8a-9842-440d-8731-200f7785f059`、status: completed、PDF 22,368,443 bytes
- Pattern-C: ジョブ `068fee0f-6ab1-4dfa-be9a-958568687897`、status: completed、PDF 22,367,788 bytes
- Pattern-A/B の `_main.txt` は `diff` で完全一致
- Pattern-C では 002.png から「咸毅成[著]」と「RAC」が、004.png から「はじめに」が欠落
- PDF 目視確認により、Pattern-C の表紙右下「咸毅成[著]」が欠落していることを確認
- `ocr-results-003005/config-comparison-report-003005.md` を新規作成
- `ocr-results-003005/visual-compare.html`、`visual-compare-pages.html` を作成

### 注意事項

- 各パターン間で `/data/extracted/*`、`/data/ocr_output/*`、`/data/pdfs/*` をクリーンアップしてから実行した
- config.yml の変更は各パターンごとに即時反映される
- Pattern-C のみ異なる結果となり、`score_thr` の変更が backend API フルフローでも反映されていることを確認

---

## 2026-08-14 タスク003006：sharpen_light_upscale_2x 自動前処理の ocr-worker 組み込み

### 【実施予定】

#### 日時

2026-08-14

#### 目的

003003 で最も効果的だった `sharpen_light_upscale_2x` 前処理を ocr-worker 内部で自動適用し、全ページに対して OCR 認識精度を向上させる。

#### 前提

- 003003 で `sharpen_light_upscale_2x` が最も効果的であることが確認済み
- `benchmark-ocr-003002.zip`（002.png, 003.png, 004.png）をテストデータとして使用
- `ocr-worker/app/main.py` には現状前処理機能が存在しない
- Docker Compose で backend / ocr-worker / frontend の 3 コンテナが起動している

#### 実施予定のコマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# ocr-worker/app/main.py への前処理実装
# （Pillow による 2x アップスケール + 軽度シャープニングを追加）

# Pillow インストール確認・追加のため Dockerfile 更新
# ocr-worker/Dockerfile に `pip install --no-cache-dir Pillow` を追加

# コンテナ再構築
docker compose down
docker compose up -d --build

# 前処理 ON（デフォルト）で OCR 実行
docker compose exec backend sh -c 'rm -rf /data/extracted/* /data/ocr_output/* /data/pdfs/*'
docker compose exec ocr-worker sh -c 'rm -rf /data/ocr_output/* /data/extracted/*'
JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
curl -s -X POST -F "file=@benchmark-ocr-003002.zip;type=application/zip" http://localhost:8000/api/jobs/$JOB_ID/upload | jq .
curl -s --max-time 1800 -X POST http://localhost:8000/api/jobs/$JOB_ID/ocr | jq .

# 前処理 OFF で OCR 実行
docker compose exec ocr-worker sed -i 's/PREPROCESS_ENABLED=.*/PREPROCESS_ENABLED=false/' /opt/ocr-worker/.env
# または docker-compose.yml を編集して docker compose up -d し直す
```

#### 想定される結果や注意点

- 前処理 ON の場合、003003 と同等の精度向上（「〓」出現数 5→3 程度）が期待される
- 前処理 OFF の場合、003002 の baseline と同等の結果（「〓」出現数 5）が期待される
- 画像サイズが 2 倍になるため、OCR 処理時間は増加する可能性がある
- ndlocr_cli の `input_root/img/` 構造を維持する必要がある
- 一時ディレクトリの cleanup は try/finally で確実に実施する

### 【実施実績】

#### 実装内容

- `ocr-worker/app/main.py` に前処理関数を追加した
  - `_preprocess_image(img_path: Path, out_path: Path)`: Pillow で画像を 2 倍アップスケール（LANCZOS）し、軽度シャープニング（`ImageFilter.UnsharpMask(radius=2, percent=80, threshold=3)`）を適用する
  - `_preprocess_input_root(input_root: Path, job_id: str) -> Path`: `input_root/img/` 以下の画像を走査し、前処理済み画像を `/tmp/ocr_preprocess/<job_id>/img/` に出力する
  - `run_ocr()` に `PREPROCESS_ENABLED` 分岐を追加し、前処理有効時は一時ディレクトリを OCR 入力に使用する
  - OCR 成功・失敗に関わらず一時ディレクトリを削除する try/finally 構造を実装した
- 環境変数 `PREPROCESS_ENABLED`（デフォルト `true`）で前処理の ON/OFF を制御可能にした
- `ocr-worker/Dockerfile` に `RUN pip install --no-cache-dir Pillow` を追加した
- `docker-compose.yml` の ocr-worker サービスに `PREPROCESS_ENABLED=true` を追加し、デフォルトで前処理が有効になるよう設定した

#### 動作確認（backend API 経由フルフロー）

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# コンテナ再ビルド・再起動
docker compose down
docker compose up -d --build

# 前処理 ON（デフォルト）
docker compose exec backend sh -c 'rm -rf /data/extracted/* /data/ocr_output/* /data/pdfs/*'
docker compose exec ocr-worker sh -c 'rm -rf /data/ocr_output/* /data/extracted/*'
JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
curl -s -X POST -F "file=@benchmark-ocr-003002.zip;type=application/zip" http://localhost:8000/api/jobs/$JOB_ID/upload | jq .
curl -s --max-time 1800 -X POST http://localhost:8000/api/jobs/$JOB_ID/ocr | jq .
# status: completed までポーリング
curl -s http://localhost:8000/api/jobs/$JOB_ID | jq .
# 成果物取得
mkdir -p ocr-results-003006/preprocess-on/pdfs ocr-results-003006/preprocess-on/output
docker compose cp backend:/data/pdfs/$JOB_ID.pdf ocr-results-003006/preprocess-on/pdfs/
OUTPUT_DIR=$(curl -s http://localhost:8000/api/jobs/$JOB_ID | jq -r '.output_dir')
docker compose cp backend:$OUTPUT_DIR ocr-results-003006/preprocess-on/output/

# 前処理 OFF（docker-compose.yml を編集して PREPROCESS_ENABLED=false に変更後、再起動）
docker compose down
# docker-compose.yml の ocr-worker.environment.PREPROCESS_ENABLED を false に変更
docker compose up -d
docker compose exec backend sh -c 'rm -rf /data/extracted/* /data/ocr_output/* /data/pdfs/*'
docker compose exec ocr-worker sh -c 'rm -rf /data/ocr_output/* /data/extracted/*'
JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
curl -s -X POST -F "file=@benchmark-ocr-003002.zip;type=application/zip" http://localhost:8000/api/jobs/$JOB_ID/upload | jq .
curl -s --max-time 1800 -X POST http://localhost:8000/api/jobs/$JOB_ID/ocr | jq .
# status: completed までポーリング
curl -s http://localhost:8000/api/jobs/$JOB_ID | jq .
# 成果物取得
mkdir -p ocr-results-003006/preprocess-off/pdfs ocr-results-003006/preprocess-off/output
docker compose cp backend:/data/pdfs/$JOB_ID.pdf ocr-results-003006/preprocess-off/pdfs/
OUTPUT_DIR=$(curl -s http://localhost:8000/api/jobs/$JOB_ID | jq -r '.output_dir')
docker compose cp backend:$OUTPUT_DIR ocr-results-003006/preprocess-off/output/
```

#### 結果

- 前処理 ON: ジョブ `ec9acd66-563f-41e0-8410-08619208e6e9`、status: completed
  - `002_main.txt`: 「〓」2 個（表紙ページの残存誤認識）
  - `003_main.txt`: 「〓」0 個
  - `004_main.txt`: 「〓」1 個
  - 合計「〓」出現数: 3 個（003003 の `sharpen_light_upscale_2x` と同等）
- 前処理 OFF: ジョブ `e07faa8c-195b-4d36-bc7c-d44e0aa28582`、status: completed
  - `002_main.txt`: 「〓」2 個
  - `003_main.txt`: 「〓」2 個
  - `004_main.txt`: 「〓」1 個
  - 合計「〓」出現数: 5 個（003002 baseline と同等）
- 前処理 ON/OFF で差分が確認でき、ocr-worker 内部の自動前処理が正しく機能していることを確認した
- 処理時間は前処理 ON で約 1.5 倍程度に増加（画像サイズが 2 倍になるため）

#### ドキュメント

- 精度比較レポート `ocr-results-003006/preprocess-integration-report-003006.md` を作成した
- 本エントリを `ocr-worker/docs/work_log.md` に追記した
- `ocr-worker/docs/caveats.md` / `ocr-worker/docs/ocr-worker-system-spec.md` を更新した

### 注意事項

- 前処理を無効にする場合は `docker-compose.yml` の `PREPROCESS_ENABLED` を `false` に変更し、コンテナを再起動する必要がある
- 一時ディレクトリ `/tmp/ocr_preprocess/` は OCR 完了後に cleanup されるが、プロセス強制終了時は残存する可能性がある
- 表紙ページ（002.png）は前処理 ON でも一部誤認識が残存した。これは表紙の特殊なフォント・レイアウトによるもので、別途対策が必要

---

## 2026-08-14 タスク003007：追加前処理（4x アップスケール、局所的二値化、コントラスト強調など）の効果検証

### 目的

003003 で `sharpen_light_upscale_2x`（2倍アップスケール＋軽度シャープニング）が最も効果的だったが、表紙ページなどで残存誤認識があったため、さらに強力な前処理パターンの効果を定量的に検証する。

### 前提

- `sample-png/手を動かしながら学ぶDocker入門_trimmed/001.png` 〜 `010.png`（10枚）を対象とする
- backend / ocr-worker コンテナが起動済みであること
- `docker-compose.yml` の `PREPROCESS_ENABLED=false` を確認済み（ocr-worker 側の自動前処理を OFF にするため）

### 【実施予定】

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# 前処理済み ZIP の作成（003003/003006 のパターン含む）
python scripts/preprocess_image.py --input-zip benchmark-ocr-003007.zip --output-zip benchmark-ocr-003007-baseline-2x.zip --pattern sharpen_light_upscale_2x
python scripts/preprocess_image.py --input-zip benchmark-ocr-003007.zip --output-zip benchmark-ocr-003007-4x-upscale.zip --pattern 4x_upscale
python scripts/preprocess_image.py --input-zip benchmark-ocr-003007.zip --output-zip benchmark-ocr-003007-4x-upscale-sharpen.zip --pattern 4x_upscale_sharpen
python scripts/preprocess_image.py --input-zip benchmark-ocr-003007.zip --output-zip benchmark-ocr-003007-local-binarization.zip --pattern local_binarization
python scripts/preprocess_image.py --input-zip benchmark-ocr-003007.zip --output-zip benchmark-ocr-003007-local-binarization-sharpen.zip --pattern local_binarization_sharpen
python scripts/preprocess_image.py --input-zip benchmark-ocr-003007.zip --output-zip benchmark-ocr-003007-contrast-strong.zip --pattern contrast_strong
python scripts/preprocess_image.py --input-zip benchmark-ocr-003007.zip --output-zip benchmark-ocr-003007-contrast-strong-4x.zip --pattern contrast_strong_4x

# backend API 経由で 7 パターンの OCR フルフローを自動実行
chmod +x scripts/run_003007_ocr.sh
./scripts/run_003007_ocr.sh
```

### 想定される結果や注意点

- 各パターンの OCR 結果と PDF を `ocr-results-003007/<pattern>/` に取得する
- 7 パターンすべての OCR 完了には数時間〜半日程度かかる見込み
- 比較指標は「〓」出現数、明らかな誤認識箇所数、目視確認とする

### 【実施実績】

- 2026-08-14: `scripts/preprocess_image.py` に 7 パターンの前処理を追加（baseline_2x / 4x_upscale / 4x_upscale_sharpen / local_binarization / local_binarization_sharpen / contrast_strong / contrast_strong_4x）
- 2026-08-14: 001.png 〜 010.png を含む `benchmark-ocr-003007.zip` と、7 パターンの前処理済み ZIP を作成
- 2026-08-14: `docker-compose.yml` の `PREPROCESS_ENABLED=false` を確認し、ocr-worker 側の自動前処理を OFF にした
- 2026-08-14: backend API 経由で 7 パターンの OCR フルフロー自動実行スクリプト `scripts/run_003007_ocr.sh` を作成
- 2026-08-14: OCR 自動実行を開始。baseline_2x は完了したが、10ページ処理で backend → ocr-worker 間の HTTP リクエストが 1800秒でタイムアウトする問題が発生
- 2026-08-14: `OCR_WORKER_REQUEST_TIMEOUT` を 3600秒に延長し、backend / ocr-worker コンテナを再起動
- 2026-08-15: `4x_upscale` のみ単独実行し、結果を報告
- 2026-08-15: 残りの `4x_upscale_sharpen`, `local_binarization`, `local_binarization_sharpen`, `contrast_strong`, `contrast_strong_4x` を手動・分割実行方式で続行
- 2026-08-15: すべての 7 パターンの OCR が `completed` となり、PDF および ocr-worker 出力（XML / txt）を `ocr-results-003007/<pattern>/` に取得
- 2026-08-15: `scripts/count_fui_per_page_003007.py` を作成し、各パターン・ページごとの「〓」出現数を集計
- 2026-08-15: 精度比較レポート `ocr-results-003007/additional-preprocess-report-003007.md` を作成

### 主な結果

| パターン | 〓 出現数（total） | 傾向 |
|---|---|---|
| baseline_2x | 194 | 現状の基準 |
| 4x_upscale | 202 | baseline より悪化、ファイルサイズ 279MB と 3倍以上 |
| 4x_upscale_sharpen | 178 | baseline より改善だが、コストに見合わず |
| local_binarization | 135 | 〓 数は最少だが文字潰れによる誤認識が多い |
| local_binarization_sharpen | 135 | local_binarization と同様 |
| contrast_strong | 160 | 一部ページで認識欠落あり |
| contrast_strong_4x | 176 | baseline 並み |

### 手動・分割実行の実コマンド

baseline_2x の 10ページ OCR で backend → ocr-worker 間の HTTP リクエストが 1800秒でタイムアウトしたため、以下の対応と手動・分割実行を実施した。

#### タイムアウト対応

```bash
# backend から ocr-worker への HTTP タイムアウトを 3600秒に延長
# docker-compose.yml の ocr-worker サービス環境変数を変更
sed -i 's/OCR_WORKER_REQUEST_TIMEOUT: 1800/OCR_WORKER_REQUEST_TIMEOUT: 3600/' docker-compose.yml

# backend / ocr-worker コンテナを再起動
docker compose down
docker compose up -d
```

#### 単一パターン手動実行（run_003007_ocr_manual.sh）

10ページ処理では polling ループが `COMPLETED` を検出しても break しない事象があったため、後続パターンは以下の手動スクリプトで 1パターンずつ実行した。

```bash
chmod +x scripts/run_003007_ocr_manual.sh

# 使用例
./scripts/run_003007_ocr_manual.sh 4x_upscale benchmark-ocr-003007-4x-upscale.zip
./scripts/run_003007_ocr_manual.sh 4x_upscale_sharpen benchmark-ocr-003007-4x-upscale-sharpen.zip
./scripts/run_003007_ocr_manual.sh local_binarization benchmark-ocr-003007-local-binarization.zip
./scripts/run_003007_ocr_manual.sh local_binarization_sharpen benchmark-ocr-003007-local-binarization-sharpen.zip
./scripts/run_003007_ocr_manual.sh contrast_strong benchmark-ocr-003007-contrast-strong.zip
./scripts/run_003007_ocr_manual.sh contrast_strong_4x benchmark-ocr-003007-contrast-strong-4x.zip
```

スクリプト内部では以下の流れで backend API を呼び出している。

1. ジョブ作成
   ```bash
   JOB_ID=$(curl -s -X POST http://localhost:8000/api/jobs/ | jq -r '.job_id')
   ```
2. ZIP アップロード
   ```bash
   curl -s -X POST \
     -F "file=@benchmark-ocr-003007-<pattern>.zip;type=application/zip" \
     http://localhost:8000/api/jobs/$JOB_ID/upload
   ```
3. OCR 実行（タイムアウト 3600秒）
   ```bash
   curl -s --max-time 3600 \
     -X POST http://localhost:8000/api/jobs/$JOB_ID/ocr
   ```
4. ジョブ状態ポーリング
   ```bash
   for i in {1..360}; do
     JOB_STATUS=$(curl -s http://localhost:8000/api/jobs/$JOB_ID | jq -r '.status')
     echo "status: $JOB_STATUS"
     [[ "$JOB_STATUS" == "COMPLETED" ]] && break
     [[ "$JOB_STATUS" == "FAILED" ]] && exit 1
     sleep 10
   done
   ```
5. PDF ダウンロード
   ```bash
   curl -s -o ocr-results-003007/<pattern>/pdfs/$JOB_ID.pdf \
     http://localhost:8000/api/jobs/$JOB_ID/pdf
   ```
6. OCR 出力ディレクトリのコピー
   ```bash
   OUTPUT_DIR=$(docker compose exec backend sh -c "ls -d /data/extracted/$JOB_ID/output_* 2>/dev/null" | head -n 1 | tr -d '\r')
   docker compose cp "backend:$OUTPUT_DIR" ocr-results-003007/<pattern>/$(basename "$OUTPUT_DIR")
   ```

#### 残りパターン一括実行（run_003007_ocr_remaining.sh）

単一パターン実行を安定化させた後、残りパターンを一括実行するスクリプトも作成した。

```bash
chmod +x scripts/run_003007_ocr_remaining.sh
./scripts/run_003007_ocr_remaining.sh
```

このスクリプトは `PATTERN_ZIPS` 配列で定義されたパターンを順次実行し、ジョブ作成・アップロード・OCR・ポーリング・PDF 取得・OCR 出力コピーを自動で実施する。

### 注意事項

- 10ページの OCR 処理には 20〜30分を要し、backend → ocr-worker 間の HTTP タイムアウトを 1800秒から 3600秒に延長する必要があった
- local_binarization は OpenCV/scipy 非依存で純粋 numpy の畳み込みを使用したが、文字潰れが発生しやすい
- 4x アップスケール系は PDF ファイルサイズが 279MB と肥大化し、処理時間も長くなる

---

## 2026-08-27 タスク005001：OCR 処理のメモリ使用量安定化

### 【実施予定】

- 日時: 2026-08-27
- 目的: ocr-worker が多ページジョブ（999 ページまで）で OOM（Exit code 137）にならず、ページ数に依存しない一定のメモリ使用量で OCR を完了できるようにする
- 前提条件:
  - `feature/005001-ocr-memory-optimization` ブランチを作成済み
  - ocr-worker コンテナは停止中（OOM により Exited (137)）
  - 原因調査済み：PyTorch Lightning `Trainer.predict()` の繰り返し呼び出し、画像データの `copy.deepcopy`、`LayoutDetector` テンソル累積が複合的なメモリリークの原因
- 実施予定のコマンド:
  ```bash
  # ndlocr_cli_patches/ にパッチファイルを追加
  # Dockerfile に COPY 行を追加
  docker compose build ocr-worker
  docker compose up -d ocr-worker
  docker compose logs -f ocr-worker
  ```
- 変更予定ファイル:
  - `ocr-worker/ndlocr_cli_patches/inference.py`（ページループ内にメモリクリーンアップを追加）
  - `ocr-worker/ndlocr_cli_patches/base_proc.py`（新規：deep copy 抑制）
  - `ocr-worker/ndlocr_cli_patches/line_ocr.py`（新規：推論後キャッシュクリア）
  - `ocr-worker/ndlocr_cli_patches/layout_extraction.py`（新規：deep copy 回避）
  - `ocr-worker/ndlocr_cli_patches/infer_task.py`（新規：predict 後処理）
  - `ocr-worker/Dockerfile`（パッチ COPY 行追加）
  - `ocr-worker/docs/tasks.md`, `ocr-worker/docs/work_log.md`, `ocr-worker/docs/caveats.md`
- 想定される結果や注意点:
  - Docker Desktop のメモリ制限に依存せず、999 ページまで処理可能になることを目指す
  - 各ページ処理後の `gc.collect()` により処理時間が若干増加する可能性がある
  - PyTorch Lightning の Trainer 内部状態をリセットすることで、進捗表示やログ出力に影響が出ないよう注意する

### 【実施実績】

- 2026-08-27: `ocr-worker/ndlocr_cli_patches/base_proc.py` を新規作成
  - `_run_process()` の戻り値を `[input_data.copy()]` に変更し、画像 ndarray の deep copy を回避
  - `_dump_result()` 内の `dump_img` deep copy を除去
- 2026-08-27: `ocr-worker/ndlocr_cli_patches/line_ocr.py` を新規作成
  - `_run_submodule_inference()` 呼び出し後に `trainer.predict_dataloaders = None` と `gc.collect()` を実行
- 2026-08-27: `ocr-worker/ndlocr_cli_patches/layout_extraction.py` を新規作成
  - `output_data = input_data.copy()` に置き換え、dump_img の deep copy を除去
- 2026-08-27: `ocr-worker/ndlocr_cli_patches/infer_task.py` を新規作成
  - `output_data = input_data.copy()` + `output_data['xml'] = copy.deepcopy(input_data['xml'])` に変更
  - 画像データは共有しつつ、xml ツリーだけ独立した deep copy を保持
  - `trainer.predict_dataloaders = None` を try/except で安全に実行
- 2026-08-27: `ocr-worker/ndlocr_cli_patches/inference.py` を修正
  - `_infer()` / `_infer_ruby_only()` のページループに `gc.collect()` と `torch.cuda.empty_cache()` を追加
  - ページ処理開始・完了の DEBUG ログに `page=N` を含める形に統一
- 2026-08-27: `ocr-worker/Dockerfile` にパッチ適用用の COPY 行を追加
  - `base_proc.py` / `line_ocr.py` / `layout_extraction.py` / `infer_task.py` を上書きコピー
- 2026-08-27: `py_compile` で全パッチファイルの構文チェックを実施し、エラーがないことを確認
- 2026-08-27: `docker compose build ocr-worker` が成功し、`docker compose up -d ocr-worker` でコンテナが正常に起動
- 2026-08-27: `curl -s http://localhost:8001/health` が `{"status":"ok"}` を返すことを確認
- 2026-08-27: 3 ページジョブで backend API 経由の OCR フルフローを実行し、`completed` になることを確認
- 2026-08-27: 50 ページジョブを作成・アップロード・OCR 実行
  - `/tmp/test_50_pages.zip` を作成（3 枚のテスト画像を 50 ページ分コピー）
  - `docker stats` でメモリ使用量を 30 秒間隔で記録
  - page 14 時点まで OOM は発生せず、メモリ使用量は 4.3GiB〜4.9GiB / 7.75GiB の範囲で推移
  - 明らかな増加傾向は見られず、ページ数に依存しない一定のメモリ使用量が維持されていることを示唆
- 2026-08-27: 999 ページまでのフルスケールテストは 1 ページあたり約 80〜120 秒かかるため、今回は実施せず別途長時間実行テストとして予定
- 2026-08-27: `ocr-worker/docs/tasks.md` / `ocr-worker/docs/caveats.md` / 本ファイルを更新

---

## 2026-09-01 タスク003008：対象ページに応じた適応的前処理の検討

### 【実施予定】

- 日時: 2026-09-01
- 目的: ページタイプ別（表紙/目次/本文）に最適な前処理パラメータを切り替える方式の実現可能性を調査・判断する
- 前提条件:
  - 003003・003007 の検証レポートが存在すること
  - 前処理パターンごとの効果データが確認できること
- 実施予定のコマンド:
  - 既存レポート `ocr-results-003003/`、`ocr-results-003007/additional-preprocess-report-003007.md` のレビュー
  - 必要に応じて簡易な特徴量分析スクリプトを作成・実行
- 想定される結果や注意点:
  - 実装コスト対効果の判断が中心
  - 表紙は技術書で 1 ページのみのため、一律前処理を維持する方がシンプルな可能性がある
  - 結論として実装しない場合は、その理由を明確に記載する

### 【実施実績】

- 2026-09-01: `ocr-worker/docs/work_log.md` の 003003・003004・003007 の記録をレビュー
- 2026-09-01: 過去の検証結果ディレクトリ（`ocr-results-003003/`、`ocr-results-003007/`）は存在しなかったため、ワークログに記載された定量的データを使用
- 2026-09-01: ページ分類ベース・認識置信度ベース・レイアウト認識結果ベースの 3 方式を実装コスト・処理時間・効果の観点から評価
- 2026-09-01: 検討レポート `test_cases/ocr-results-003008/adaptive-preprocess-report-003008.md` を作成
- 2026-09-01: 結論として「適応的前処理の導入は保留」とし、理由を記載
- 2026-09-01: `ocr-worker/docs/tasks.md` に実施結果とレポートリンクを追記

