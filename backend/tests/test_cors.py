"""CORS（Cross-Origin Resource Sharing）設定のテストです。

このファイルでは、frontend（localhost:3000）から backend（localhost:8000）へ
クロスオリジンでアクセスした場合の挙動を検証します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# テスト関数や fixture を書くためのライブラリです
import pytest

# FastAPI のテスト用 HTTP クライアントです
# サーバーを起動せずに API をテストできます
from fastapi.testclient import TestClient

# テスト対象の FastAPI アプリケーションを読み込みます
from app.main import app


# FastAPI のテストクライアントを作成します
# 各テスト関数で利用できるように fixture として定義します
@pytest.fixture
def client() -> TestClient:
    """テスト用の HTTP クライアントを提供します。"""
    return TestClient(app)


def test_cors_preflight_returns_200(client: TestClient) -> None:
    """OPTIONS プリフライトリクエストが 200 OK を返すことを確認します。"""
    # ブラウザがクロスオリジンの POST 送信前に送信する OPTIONS リクエストを模倣します
    response = client.options(
        "/api/jobs/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    # プリフライトが成功していることを確認します
    assert response.status_code == 200

    # frontend オリジンからのアクセスが許可されていることを確認します
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    # POST メソッドが許可されていることを確認します
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_cors_headers_in_actual_response(client: TestClient) -> None:
    """実際の POST レスポンスにも CORS ヘッダーが含まれることを確認します。"""
    # frontend オリジンからの POST リクエストを模倣します
    response = client.post(
        "/api/jobs/",
        headers={"Origin": "http://localhost:3000"},
    )

    # ジョブ作成が成功していることを確認します
    assert response.status_code == 200

    # レスポンスに CORS 許可ヘッダーが含まれていることを確認します
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_rejects_unexpected_origin(client: TestClient) -> None:
    """許可していないオリジンからのアクセスは CORS ヘッダーを返さないことを確認します。"""
    # 許可リストに含まれていないオリジンからのリクエストを模倣します
    response = client.options(
        "/api/jobs/",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    # 許可されていないオリジンには allow-origin ヘッダーが設定されません
    # ただし、OPTIONS リクエストそのものは CORSMiddleware が処理するため 200 が返ります
    assert response.headers.get("access-control-allow-origin") is None
