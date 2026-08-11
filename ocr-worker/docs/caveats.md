# 注意事項

本ドキュメントは、book2pdf プロジェクトの ocr-worker における環境差異、トラブルシューティング、回避策などをまとめたものです。

---

## 1. ndlocr_cli の公式 Dockerfile は GPU 用である

- ndlocr_cli 公式リポジトリの `docker/Dockerfile` は `nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04` をベースにしている
- 本プロジェクトは CPU 実行を前提としているため、公式 Dockerfile はそのまま利用できない
- そのため、`python:3.10-slim` ベースの CPU 実行用 Dockerfile を自前で作成している

## 2. PyTorch / mmcv / mmdet は CPU 版を使用する

- 公式 Dockerfile では GPU 用の PyTorch / mmcv / mmdet がインストールされる
- CPU 実行を前提とするため、以下を明示的に指定している
  - `torch==2.0.1+cpu`
  - `torchvision==0.15.2+cpu`
  - `mmcv==2.0.1 -f https://download.openmmlab.com/mmcv/dist/cpu/torch2.0/`
  - `mmdet==3.1.0`
- GPU 版が混在すると実行時に CUDA 関連のエラーが発生する可能性がある

## 3. 学習済みモデルのダウンロードに時間がかかる

- ndlocr_cli の学習済みモデルは `lab.ndl.go.jp` からダウンロードする
- モデルファイルは合計で数百 MB〜数 GB に及ぶ可能性がある
- Dockerfile のビルド時に毎回ダウンロードするため、**ビルドには数十分程度かかる場合がある**
- ビルド時間を短縮したい場合は、モデルファイルをホスト側にキャッシュし、`COPY` でコピーする方式を検討できる

## 4. `config.yml` の `device` 設定を `cpu` に変更する

- ndlocr_cli の `config.yml` では、デフォルトで `device: 'cuda:0'` が指定されている
- CPU 実行のため、Dockerfile 内で `sed` を使って `device: 'cpu'` に書き換えている
- 書き換えを忘れると、実行時に `CUDA error` や `No CUDA GPUs are available` エラーが発生する

## 5. `submodules/` のディレクトリ構造を正しく再現する

- `cli/core/inference.py` は実行時に `submodules/` 以下のパスを `sys.path.append` してモジュールを読み込む
- そのため、リポジトリの `submodules/` ディレクトリ構造をコンテナ内で正しく再現する必要がある
- 公式 README に従って `--recursive` オプション付きで clone するか、各 submodule を個別に clone する

## 6. XML 出力形式

- ndlocr_cli の推論結果は XML 形式で出力される
- 出力形式の詳細は、ndlocr_cli リポジトリの `ndlocr-xmlformat.md` を参照
- 主な要素は以下の通り
  - ルート要素：`<OCRDATASET>`
  - ページ要素：`<PAGE HEIGHT="..." WIDTH="..." IMAGENAME="...">`
  - テキスト行要素：`<LINE TYPE="..." X="..." Y="..." WIDTH="..." HEIGHT="..." STRING="..." ORDER="..." />`
- 座標は左上原点で、ページ画像に対する絶対座標

## 7. mmdet 3.x で `init_detector` の引数順序が変わっている

- ndlocr_cli は mmdet 2.x を想定して `init_detector(config, checkpoint, device)` と呼んでいる
- インストールしている mmdet 3.1.0 ではシグネチャが `init_detector(config, checkpoint, palette, device, ...)` に変更されている
- そのままでは `device` が `palette` 引数として解釈され、実際の `device` はデフォルトの `cuda:0` のままになる
- 回避策として、Dockerfile 内で `init_detector(config, checkpoint, device)` を `init_detector(config, checkpoint, device=device)` に書き換えている

## 8. `text_recognition_lightning` のコールバックは CPU 非対応

- `text_recognition_lightning/configs/infer.yaml` の callbacks に含まれる `MeasureTimeCallback` は `torch.cuda.Event` を使う
- CPU 環境では `RuntimeError: Tried to instantiate dummy base class Event` が発生する
- このコールバックは処理時間計測専用で OCR 結果に影響しないため、Dockerfile 内で `infer.yaml` から削除している

## 9. `text_recognition_lightning` の trainer 設定を CPU に変更する

- `text_recognition_lightning/configs/trainer/default.yaml` では `accelerator: gpu` が指定されている
- CPU 環境では `GPUAccelerator can not run on your system` エラーが発生する
- Dockerfile 内で `accelerator: gpu` を `accelerator: cpu` に書き換えている

## 10. KyTea のモデルファイルはソースビルドで配置する

- `ruby_prediction` で使用する KyTea の Python バインディング（Mykytea）だけをインストールしても、モデルファイル `/usr/local/share/kytea/model.bin` は含まれない
- 公式 Dockerfile と同様に KyTea 0.4.7 をソースからビルド・インストールすることでモデルファイルを生成している
- KyTea のビルドには `make` が必要なため、apt-get で `make` をインストールしている

## 11. 起動時の待機状態（変更済み）

- 以前は `command: ["tail", "-f", "/dev/null"]` で待機状態を維持していた
- タスク001002で FastAPI HTTP API を実装したため、
  現在は `ocr-worker/Dockerfile` の `CMD` で `uvicorn app.main:app --host 0.0.0.0 --port 8000` を実行している
- コンテナ起動時に自動的に API サーバーが立ち上がり、backend からのリクエストを待機する

## 12. FastAPI / Uvicorn の追加

- `ocr-worker` コンテナは、backend からの HTTP リクエストを受け付けるため、
  FastAPI と Uvicorn をインストールしている
- 必要なパッケージは `ocr-worker/Dockerfile` の `pip install` に追加済み
  - `fastapi`
  - `uvicorn[standard]`
  - `python-multipart`
- API エントリポイントは `ocr-worker/app/main.py` にある

## 13. `/ocr` エンドポイントの入力パスは共有ボリューム上である必要がある

- `POST /ocr` は、backend から共有ボリューム `/data/extracted` 上の画像パスを受け取る
- このパスは backend コンテナと ocr-worker コンテナの両方からアクセス可能である必要がある
- `docker-compose.yml` で両コンテナに同じボリュームマウントを定義している

## 14. ヘルスチェックエンドポイントの追加

- `ocr-worker/app/main.py` に `GET /health` を追加した
- レスポンスは `{"status":"ok"}`
- `docker-compose.yml` の `healthcheck` で利用し、backend の `depends_on` に
  `condition: service_healthy` を指定することで、ocr-worker の準備が完了してから backend が起動する

## 15. ポート番号の扱い

- ocr-worker 内の Uvicorn はポート 8000 でリッスンしている
- `docker-compose.yml` ではホスト側の 8001 番にマップしている
  - backend コンテナからは `http://ocr-worker:8000` でアクセスする
  - ホスト側の curl やブラウザからは `http://localhost:8001` でアクセスする

