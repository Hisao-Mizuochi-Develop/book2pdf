"""ジョブ関連 API のテストです。

このファイルでは、ジョブ作成、ZIP アップロード、ジョブ状態取得などの
エンドポイントに対するテストを提供します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# テスト用にメモリ上のバイナリストリームを扱うための標準ライブラリです
import io

# ZIP ファイルを作成するための標準ライブラリです
import zipfile

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


def create_zip_buffer(filenames: list[str]) -> io.BytesIO:
    """テスト用の ZIP ファイルをメモリ上に作成します。

    Args:
        filenames: ZIP に含めるファイル名の一覧

    Returns:
        メモリ上の ZIP ファイルバッファ
    """
    # メモリ上にバイナリデータを書き込むためのバッファを作成します
    buffer = io.BytesIO()

    # ZIP ファイルを書き込みモードで開きます
    # ZIP_DEFLATED は通常の圧縮方式です
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 指定されたファイル名のダミーデータを ZIP に追加します
        for filename in filenames:
            zf.writestr(filename, b"dummy image data")

    # 読み取り位置を先頭に戻します
    # これをしないと、後から read したときに空になってしまいます
    buffer.seek(0)

    # 作成した ZIP バッファを呼び出し元に返します
    return buffer


def test_upload_zip_success(client: TestClient) -> None:
    """ZIP アップロードが成功し、画像ファイル一覧が取得できることを確認します。"""
    # まずジョブを作成します
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # 画像ファイルを含む ZIP を作成します
    zip_buffer = create_zip_buffer(["page1.png", "page2.jpg", "readme.txt"])

    # ZIP をアップロードします
    response = client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )

    # アップロードが成功していることを確認します
    assert response.status_code == 200

    # レスポンス本文を辞書として取得します
    data = response.json()

    # レスポンスの job_id がアップロード対象と一致することを確認します
    assert data["job_id"] == job_id

    # ジョブ状態が uploaded に更新されていることを確認します
    assert data["status"] == "uploaded"

    # 画像ファイルのみが抽出され、かつソートされていることを確認します
    assert sorted(data["files"]) == ["page1.png", "page2.jpg"]


def test_upload_zip_job_not_found(client: TestClient) -> None:
    """存在しないジョブ ID にアップロードした場合に 404 エラーが返ることを確認します。"""
    zip_buffer = create_zip_buffer(["page1.png"])

    response = client.post(
        "/api/jobs/00000000-0000-0000-0000-000000000000/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )

    assert response.status_code == 404
    assert "ジョブが見つかりません" in response.json()["detail"]


def test_upload_invalid_file_type(client: TestClient) -> None:
    """ZIP 以外のファイルをアップロードした場合に 400 エラーが返ることを確認します。"""
    # まずジョブを作成します
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # PNG ファイルをそのままアップロードします
    response = client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("image.png", io.BytesIO(b"dummy"), "image/png")},
    )

    assert response.status_code == 400
    assert "ZIP ファイル" in response.json()["detail"]


def test_upload_zip_no_images(client: TestClient) -> None:
    """ZIP に画像ファイルが含まれていない場合、空のファイル一覧が返ることを確認します。"""
    # まずジョブを作成します
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # 画像以外のファイルのみ含む ZIP を作成します
    zip_buffer = create_zip_buffer(["readme.txt", "document.pdf"])

    response = client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("documents.zip", zip_buffer, "application/zip")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["files"] == []


def test_get_job_after_upload(client: TestClient) -> None:
    """アップロード後にジョブ状態を取得できることを確認します。"""
    # ジョブを作成して ZIP をアップロードします
    response = client.post("/api/jobs/")
    job_id = response.json()["job_id"]

    zip_buffer = create_zip_buffer(["page1.png"])
    client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )

    # ジョブ状態を取得します
    response = client.get(f"/api/jobs/{job_id}")

    # 状態取得が成功していることを確認します
    assert response.status_code == 200

    # レスポンス本文を辞書として取得します
    data = response.json()

    # 取得したジョブ ID が一致することを確認します
    assert data["job_id"] == job_id

    # ジョブ状態が uploaded であることを確認します
    assert data["status"] == "uploaded"

    # 画像ファイル一覧が期待通りであることを確認します
    assert data["files"] == ["page1.png"]
