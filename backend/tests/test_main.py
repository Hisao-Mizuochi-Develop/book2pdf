"""FastAPI アプリケーションの基本的な動作確認用テストです。"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# FastAPI のテスト用 HTTP クライアントです
# サーバーを起動せずに API をテストできます
from fastapi.testclient import TestClient

# テスト対象の FastAPI アプリケーションを読み込みます
from app.main import app


# TestClient は FastAPI アプリケーションをテスト用にラップするクライアントです
# 実際に HTTP サーバーを起動せずにエンドポイントを呼び出せます
client = TestClient(app)


def test_health_check() -> None:
    """ヘルスチェックエンドポイントが正常に応答することを確認します。"""
    # /health に GET リクエストを送信します
    response = client.get("/health")

    # HTTP ステータスコードが 200 であることを確認します
    assert response.status_code == 200

    # レスポンスの JSON 本文が期待通りであることを確認します
    assert response.json() == {"status": "ok"}


def test_create_job() -> None:
    """ジョブ作成エンドポイントがジョブ ID を返すことを確認します。"""
    # /api/jobs/ に POST リクエストを送信します
    response = client.post("/api/jobs/")

    # ステータスコードが 200 であることを確認します
    assert response.status_code == 200

    # レスポンス本文を辞書として取得します
    data = response.json()

    # レスポンスに job_id が含まれていることを確認します
    assert "job_id" in data

    # ジョブの初期状態が pending であることを確認します
    assert data["status"] == "pending"


def test_get_job_not_found() -> None:
    """存在しないジョブ ID を指定した場合に 404 エラーになることを確認します。"""
    # 存在しない ID で GET リクエストを送信します
    response = client.get("/api/jobs/not-existing-id")

    # ステータスコードが 404 であることを確認します
    assert response.status_code == 404
