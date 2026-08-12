# book2pdf backend 用 Dockerfile
# Python 3.12 ベースの軽量イメージを使用します
FROM python:3.12-slim

# 作業ディレクトリを /app に設定します
WORKDIR /app

# まず requirements.txt だけをコピーして依存関係をインストールします
# これにより、ソースコードの変更時にも依存関係のレイヤーがキャッシュされます
COPY requirements.txt .

# 日本語フォント（Noto Sans CJK）をインストールします
# PDF 生成時に日本語テキストを正しく埋め込めるようにするため必要です
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# pip を最新化し、requirements.txt に記載されたパッケージをインストールします
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコンテナにコピーします
COPY app/ ./app/

# コンテナが待ち受けるポートを明示します
# FastAPI のデフォルトポートは 8000 です
EXPOSE 8000

# コンテナ起動時に Uvicorn で FastAPI アプリケーションを起動します
# --host 0.0.0.0 で外部からのアクセスを受け入れます
# --port 8000 で待ち受けるポートを指定します
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
