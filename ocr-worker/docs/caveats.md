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

## 16. Hydra の GlobalHydra は同一プロセス内で複数回初期化できない

- `ocr-worker/app/main.py` の `infer` 関数内で `hydra.initialize()` を呼び出している
- 1 回目のリクエストでは問題ないが、Uvicorn worker プロセスが使い回されるため、
  2 回目以降のリクエストで `ValueError: GlobalHydra is already initialized` が発生する
- 回避策として、`GlobalHydra.instance().is_initialized()` で既に初期化済みかを確認し、
  初期化済みの場合は `clear()` してから `initialize()` する
  ```python
  from hydra.core.global_hydra import GlobalHydra

  if GlobalHydra.instance().is_initialized():
      GlobalHydra.instance().clear()
  hydra.initialize(config_path="conf", job_name="ocr", version_base=None)
  ```
- 将来的に `hydra.compose()` などを使う場合は、この reinitialize パターンを見直す

## 17. `setuptools` のバージョンは 79.0.1 に固定する

- `pytorch_lightning` が import 時に `pkg_resources` を参照している
- `python:3.10-slim` のベースイメージでは `setuptools` が含まれていないケースがあるため、明示的にインストールが必要
- ただし、2026-08-13 時点で最新の `setuptools 84.0.0` では `pkg_resources` モジュールが削除されており、
  `ModuleNotFoundError: No module named 'pkg_resources'` が発生する
- そのため、`ocr-worker/Dockerfile` では `setuptools==79.0.1` を明示的にインストールしている
- この固定を怠ると、OCR 実行時に 500 エラーが発生する

## 18. エラーハンドリングでトレースバックをログに出力する

- `ocr-worker/app/main.py` の `run_ocr` では、例外発生時に `traceback.format_exc()` を使って
  スタックトレースをログと HTTP レスポンスの両方に含めている
- これにより、ocr-worker 内で発生したエラーの原因を backend 側やコンテナログから迅速に特定できる

## 19. `config.yml` の `layout_extraction.score_thr` は `process_textblock.py` パッチ適用後に反映される

- ndlocr_cli 標準では、`submodules/ndl_layout/tools/process_textblock.py` / `process.py` に
  `score_thr: float = 0.3` がハードコードされており、`config.yml` の値が無視される
- `ocr-worker/ndlocr_cli_patches/process_textblock.py` を Docker ビルド時に上書きコピーすることで、
  `config.yml` の `layout_extraction.score_thr` が推論に反映されるように修正している
- パッチ適用後は以下の動作となる
  - `InferencerWithCLI.__init__` で `conf_dict.get('score_thr', 0.3)` を保持
  - `LayoutDetector.predict()` で `inference_detector(model, img, score_thr=score_thr)` を呼び出し
  - XML 変換時にも `score_thr` を渡して低 CONF の領域をフィルタリング
- ホスト側でパッチファイルを変更した場合は、`docker compose up -d --build ocr-worker` でイメージを再ビルドすること
- 将来 ndlocr_cli のバージョンアップで `process_textblock.py` の構造が変わった場合、パッチの適用箇所を見直す必要がある

## 20. 自動画像前処理機能（sharpen_light_upscale_2x）

- `POST /ocr` リクエスト受信時、`ocr-worker/app/main.py` が入力画像に対して自動前処理を行う
- 前処理内容は「2 倍アップスケール（LANCZOS 補間）＋軽度シャープニング（UnsharpMask radius=2, percent=80, threshold=3）」
- 前処理は環境変数 `PREPROCESS_ENABLED` で ON/OFF を制御できる
  - デフォルトは `true`（ON）
  - `false` / `0` / `no` / `off` のいずれかを指定すると OFF になる
  - `docker-compose.yml` の `ocr-worker.environment` で設定する
- 前処理済み画像は `/tmp/ocr_preprocess_<job_id>_*/input/img/` という一時ディレクトリに保存される
- OCR 処理の成功・失敗に関わらず、`try ... finally` で一時ディレクトリを削除する
- Pillow の依存が必要であるが、`python:3.10-slim` イメージには標準で含まれていないため、`ocr-worker/Dockerfile` で `python3-pil` を apt-get インストールしている
- 前処理を有効にすると、画像が 2 倍になるため OCR 処理時間が増加する
  - 参考: 3 ページのサンプルで、OFF 時 120〜130 秒に対し、ON 時 180〜190 秒程度（約 1.5 倍）
- 前処理は「〓」のような不明文字の出現を減らす効果があるが、表紙や特殊なレイアウトのページでは誤認識が残ることがある
  - 参考: 3 ページのサンプルで、OFF 時 5 個だった「〓」が ON 時 3 個に減少
- 前処理適用後も座標は ndlocr_cli 内部で前処理済み画像に対して計算されるため、backend 側の座標変換（必要に応じて）で元画像スケールに戻す必要がある

## 21. OCR 処理のメモリ最適化（005001）

- 多ページジョブ（257 ページ以上）で ocr-worker が OOM（Exit code 137）になる問題があった
- 原因は以下の複合的要因だった
  - `base_proc.py` / `infer_task.py` / `layout_extraction.py` で `copy.deepcopy(input_data)` により画像 ndarray が毎ページ複製されていた
  - PyTorch Lightning `Trainer.predict()` をページごとに繰り返し呼び出す際、DataLoader や内部テンソルが累積していた
  - ページループ内でガベージコレクションが行われていなかった
- 対策として `ocr-worker/ndlocr_cli_patches/` に以下のパッチを適用した
  - `base_proc.py`: `_run_process()` の戻り値を `[input_data.copy()]` にし、dump 用画像の deep copy を除去
  - `line_ocr.py`: `_run_submodule_inference()` 後に `trainer.predict_dataloaders = None` と `gc.collect()` を実行
  - `layout_extraction.py`: `input_data.copy()` に置き換え、dump_img の deep copy を除去
  - `infer_task.py`: `input_data.copy()` + `copy.deepcopy(input_data['xml'])` に変更。画像は共有し、xml ツリーだけ独立した deep copy を保持
  - `inference.py`: `_infer()` / `_infer_ruby_only()` のページループに `gc.collect()` と `torch.cuda.empty_cache()` を追加
- 50 ページジョブの検証では page 14 時点まで OOM は発生せず、メモリ使用量は 4.3GiB〜4.9GiB / 7.75GiB で推移した
- 999 ページまでのフルスケールテストは時間がかかるため、別途長時間実行テストとして実施する
- パッチファイルを変更した場合は `docker compose build ocr-worker` でイメージを再ビルドすること
- 将来 ndlocr_cli のバージョンアップで対象ファイルの構造が変わった場合、パッチの適用箇所を見直す必要がある


