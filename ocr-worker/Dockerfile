# NDLOCR CLI を Python パッケージとして実行するための ocr-worker コンテナです。
# 本プロジェクトは CPU 実行を前提とするため、PyTorch / mmcv / mmdet は CPU 版を使用します。

FROM python:3.10-slim

# コンテナ内の作業ディレクトリを設定します
ENV PROJECT_DIR=/opt/ocr-worker
WORKDIR ${PROJECT_DIR}

# 日本語ロケールを設定します
# ndlocr_cli のログや入出力で日本語を正しく扱うためです
ENV LANG=ja_JP.UTF-8
ENV LANGUAGE=ja_JP:ja
ENV LC_ALL=ja_JP.UTF-8
ENV TZ=Asia/Tokyo

# 必要なシステムパッケージをインストールします
# git: submodule 含むリポジトリ取得に使用
# wget: 学習済みモデルのダウンロードに使用
# libgl1 / libglib2.0-0: OpenCV 実行に必要
# gcc / g++ / make: Python パッケージおよび KyTea のビルドに必要
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        wget \
        ca-certificates \
        libgl1-mesa-dev \
        libglib2.0-0 \
        gcc \
        g++ \
        make \
        locales \
    && locale-gen ja_JP.UTF-8 \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# ndlocr_cli リポジトリを submodule 含めてクローンします
# inference.py は submodules/ 以下を sys.path に追加するため、同じ階層構造が必要です
RUN git clone --recursive https://github.com/ndl-lab/ndlocr_cli.git ${PROJECT_DIR}

# 公式 dockerbuild.sh と同じ URL から学習済みモデルをダウンロードします
# これらのモデルは OCR 処理に必要です
RUN mkdir -p ${PROJECT_DIR}/submodules/text_recognition_lightning/models/rf_author \
    && mkdir -p ${PROJECT_DIR}/submodules/text_recognition_lightning/models/rf_title \
    && wget -nc https://lab.ndl.go.jp/dataset/ndlocr_v2/text_recognition_lightning/resnet-orient2.ckpt \
        -O ${PROJECT_DIR}/submodules/text_recognition_lightning/models/resnet-orient2.ckpt \
    && wget -nc https://lab.ndl.go.jp/dataset/ndlocr_v2/text_recognition_lightning/rf_author/model.pkl \
        -O ${PROJECT_DIR}/submodules/text_recognition_lightning/models/rf_author/model.pkl \
    && wget -nc https://lab.ndl.go.jp/dataset/ndlocr_v2/text_recognition_lightning/rf_title/model.pkl \
        -O ${PROJECT_DIR}/submodules/text_recognition_lightning/models/rf_title/model.pkl \
    && wget -nc https://lab.ndl.go.jp/dataset/ndlocr_v2/ndl_layout/ndl_retrainmodel.pth \
        -O ${PROJECT_DIR}/submodules/ndl_layout/models/ndl_retrainmodel.pth \
    && wget -nc https://lab.ndl.go.jp/dataset/ndlocr_v2/separate_pages_mmdet/epoch_180.pth \
        -O ${PROJECT_DIR}/submodules/separate_pages_mmdet/models/epoch_180.pth

# PyTorch CPU 版をインストールします
# 公式 Dockerfile は CUDA 版を使用していますが、本プロジェクトは CPU 実行を前提とします
# torchtext / torchaudio は画像処理で不要なため、torch と torchvision のみインストールします
# --extra-index-url を使用し、PyTorch 固有パッケージのみ PyTorch index から取得します
# pip を先にアップグレードして、メタデータ名の大文字小文字不一致による解決失敗を回避します
RUN pip install --upgrade "pip<24.1" setuptools wheel \
    && pip install --no-cache-dir \
        torch==2.0.1+cpu \
        torchvision==0.15.2+cpu \
        --extra-index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir torchtext==0.15.2

# ndlocr_cli の Python 依存パッケージをインストールします
RUN pip install --no-cache-dir -r ${PROJECT_DIR}/requirements.txt

# OpenMMLab 関連パッケージを CPU 版でインストールします
RUN pip install --no-cache-dir mmdet==3.1.0 \
    && pip install --no-cache-dir mmcv==2.0.1 \
        -f https://download.openmmlab.com/mmcv/dist/cpu/torch2.0/index.html

# ruby_prediction の追加依存をインストールします
RUN pip install --no-cache-dir -r ${PROJECT_DIR}/submodules/ruby_prediction/requirements.txt

# ocr-worker HTTP API 用のパッケージをインストールします
# FastAPI で /ocr エンドポイントを提供し、backend からの HTTP 呼び出しに応答します
RUN pip install --no-cache-dir fastapi uvicorn httpx

# ruby_prediction が参照する KyTea のモデルファイルを配置します
# 公式 Dockerfile と同様に KyTea をソースからビルド・インストールすることで
# /usr/local/share/kytea/model.bin が生成されます
RUN wget -q http://www.phontron.com/kytea/download/kytea-0.4.7.tar.gz \
    && tar xzf kytea-0.4.7.tar.gz \
    && cd kytea-0.4.7 \
    && ./configure \
    && make -j$(nproc) \
    && make install \
    && ldconfig \
    && cd .. \
    && rm -rf kytea-0.4.7 kytea-0.4.7.tar.gz

# 設定ファイル・ソースコードを CPU 実行用に書き換えます
# layout_extraction.device だけでなく、各 submodule やプロセス内のハードコードされた cuda:0 も cpu に変更します
RUN sed -i "s/device: 'cuda:0'/device: 'cpu'/g" ${PROJECT_DIR}/config.yml \
    && sed -i "s/device = 'cuda:0'/device = 'cpu'/g" ${PROJECT_DIR}/cli/procs/page_separation.py \
    && sed -i "s/device: str = 'cuda:0'/device: str = 'cpu'/g" ${PROJECT_DIR}/submodules/ndl_layout/tools/process_textblock.py \
    && sed -i "s/device: str = 'cuda:0'/device: str = 'cpu'/g" ${PROJECT_DIR}/submodules/ndl_layout/tools/process.py \
    && sed -i "s/device='cuda:0'/device='cpu'/g" ${PROJECT_DIR}/submodules/separate_pages_mmdet/inference_divide.py \
    && sed -i "s/device = 'cuda'/device = 'cpu'/g" ${PROJECT_DIR}/submodules/ndl_layout/models/cascade_mask_rcnn_convnext-t_p4_w7_fpn_giou_4conv1f_fp16_ms-crop_3x_coco.py \
    && sed -i "s/device = 'cuda'/device = 'cpu'/g" ${PROJECT_DIR}/submodules/separate_pages_mmdet/models/cascade_rcnn_r50_fpn_1x_ndl_1024.py \
    && sed -i "s/device = 'cuda'/device = 'cpu'/g" ${PROJECT_DIR}/submodules/separate_pages_mmdet/configs/ndl/cascade_rcnn_r50_fpn_1x_ndl_1024.py

# mmdet 3.x の init_detector は引数順序が (config, checkpoint, palette, device) です
# ndlocr_cli は mmdet 2.x を想定して init_detector(config, checkpoint, device) と呼んでいるため
# device が palette 引数に渡され、実際の device はデフォルトの cuda:0 のままになります
# これを回避するため、device をキーワード引数で渡すように修正します
RUN sed -i "s/init_detector(config, checkpoint, device)/init_detector(config, checkpoint, device=device)/g" \
    ${PROJECT_DIR}/submodules/separate_pages_mmdet/inference_divide.py \
    ${PROJECT_DIR}/submodules/ndl_layout/tools/process.py \
    ${PROJECT_DIR}/submodules/ndl_layout/tools/process_textblock.py

# text_recognition_lightning の infer.yaml は CPU 非対応の MeasureTimeCallback を読み込みます
# このコールバックは処理時間計測専用で OCR 結果に影響しないため、callbacks から除外します
RUN sed -i '/- measure_time.yaml/d' ${PROJECT_DIR}/submodules/text_recognition_lightning/configs/infer.yaml

# text_recognition_lightning のデフォルト trainer は accelerator: gpu です
# CPU 実行を前提とするため、accelerator: cpu に変更します
RUN sed -i 's/accelerator: gpu/accelerator: cpu/g' ${PROJECT_DIR}/submodules/text_recognition_lightning/configs/trainer/default.yaml

# ndlocr_cli にページごとの OCR 処理時間 DEBUG ログを追加します
# オリジナルの cli/core/inference.py は logging を使用していないため、修正版を上書きします
COPY ndlocr_cli_patches/inference.py ${PROJECT_DIR}/cli/core/inference.py

# ocr-worker アプリケーションのソースコードをコピーします
COPY app/ ${PROJECT_DIR}/app/

# コンテナ起動時に FastAPI サーバーを起動します
# backend コンテナから HTTP で OCR 実行をリクエストできるようにします
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
