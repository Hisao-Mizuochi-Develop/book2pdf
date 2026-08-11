"""開発用のエントリポイントです。

このファイルを直接実行することで、ローカル開発環境で Uvicorn を起動できます。
Docker 環境では Dockerfile の CMD を使用します。
"""

from __future__ import annotations

# Uvicorn は ASGI サーバーとして FastAPI を実行するためのツールです
import uvicorn

from app.core.config import settings


if __name__ == "__main__":
    # Uvicorn を使って FastAPI アプリケーションを起動します
    # reload=True にすると、ソースコードの変更時に自動で再起動します
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
