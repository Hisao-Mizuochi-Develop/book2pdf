"""FastAPI アプリケーションのエントリポイントです。

このファイルは Web サーバーを起動するためのメイン処理を提供します。
各機能は routers ディレクトリに分割して実装し、ここではそれらをアプリに登録します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# FastAPI のメインクラスを読み込みます
# Web アプリケーションの本体（エンドポイント登録・リクエスト処理など）を提供します
from fastapi import FastAPI

# CORS（Cross-Origin Resource Sharing）を制御するミドルウェアです
# ブラウザから別オリジン（frontend）へのアクセスを許可するために使用します
from fastapi.middleware.cors import CORSMiddleware

# routers パッケージから API ルーターをインポートします
# APIRouter を使うことで、エンドポイントを機能ごとに分割できます
from app.routers import jobs

# ログ出力のための標準ライブラリです
# アプリケーション全体のログレベルを環境変数 LOG_LEVEL から設定します
import logging
import os

# アプリケーション全体のログレベルを設定します
# uvicorn 起動前に設定することで、各モジュールの DEBUG ログも出力されます
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# FastAPI のアプリケーションインスタンスを作成します
# title は API ドキュメントに表示される名前です
app = FastAPI(title="book2pdf Web OCR API")

# CORS ミドルウェアをアプリケーションに追加します
# frontend（localhost:3000）から backend（localhost:8000）へのクロスオリジン要求を許可します
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# jobs ルーターをアプリケーションに登録します
# prefix="/api/jobs" で、jobs ルーターのエンドポイント URL が /api/jobs/... になります
app.include_router(jobs.router, prefix="/api/jobs")


# ヘルスチェック用のエンドポイントです
# サーバーが正常に起動しているかを簡単に確認するために使います
@app.get("/health")
def health_check() -> dict[str, str]:
    """サーバーの稼働状態を確認するためのシンプルなエンドポイントです。"""
    return {"status": "ok"}
