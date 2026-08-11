"""OCR 実行 API のテストです。

このファイルでは、ZIP アップロード後の OCR 実行エンドポイントに対する
テストを提供します。
ndlocr_cli はローカル開発環境にインストールされていないため、
モック OCR エンジンを使用して動作を確認します。
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

# モック OCR エンジンを読み込みます
from app.services.ocr_engine import MockOcrEngine


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
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 指定されたファイル名のダミーデータを ZIP に追加します
        for filename in filenames:
            zf.writestr(filename, b"dummy image data")

    # 読み取り位置を先頭に戻します
    buffer.seek(0)

    # 作成した ZIP バッファを呼び出し元に返します
    return buffer


# 実際の OCR エンジンをモックに置き換えるための fixture です
# これにより ndlocr_cli がなくてもテストできます
@pytest.fixture(autouse=True)
def mock_ocr_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    """OCR エンジンをモックに置き換えます。"""
    # create_ocr_engine 関数が常に MockOcrEngine を返すようにします
    monkeypatch.setattr(
        "app.routers.jobs.create_ocr_engine",
        lambda use_mock=False: MockOcrEngine(),
    )


def test_run_ocr_success(client: TestClient) -> None:
    """OCR 実行が成功し、認識結果テキストが取得できることを確認します。"""
    # まずジョブを作成します
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # 画像ファイルを含む ZIP を作成してアップロードします
    zip_buffer = create_zip_buffer(["page1.png", "page2.jpg"])
    response = client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )
    assert response.status_code == 200

    # OCR 実行エンドポイントを呼び出します
    response = client.post(f"/api/jobs/{job_id}/ocr")

    # OCR 処理が成功していることを確認します
    assert response.status_code == 200
    data = response.json()

    # レスポンスに job_id が含まれていることを確認します
    assert data["job_id"] == job_id

    # ジョブ状態が completed であることを確認します
    assert data["status"] == "completed"

    # モック OCR から認識結果テキストが返されていることを確認します
    assert "page1.png" in data["text"]
    assert "page2.jpg" in data["text"]


def test_run_ocr_job_not_found(client: TestClient) -> None:
    """存在しないジョブ ID に対して OCR 実行した場合に 404 エラーになることを確認します。"""
    response = client.post("/api/jobs/00000000-0000-0000-0000-000000000000/ocr")

    # ジョブが見つからないため 404 エラーになります
    assert response.status_code == 404


def test_run_ocr_before_upload(client: TestClient) -> None:
    """ZIP アップロード前に OCR 実行した場合に 400 エラーになることを確認します。"""
    # ジョブを作成します（アップロードは行いません）
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # アップロード前に OCR 実行エンドポイントを呼び出します
    response = client.post(f"/api/jobs/{job_id}/ocr")

    # アップロード前は OCR を実行できないため 400 エラーになります
    assert response.status_code == 400
    assert "ZIP" in response.json()["detail"]


def test_run_ocr_no_images(client: TestClient) -> None:
    """ZIP に画像が含まれていない場合に 400 エラーになることを確認します。"""
    # ジョブを作成します
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # 画像以外のファイルのみ含む ZIP をアップロードします
    zip_buffer = create_zip_buffer(["readme.txt"])
    response = client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("documents.zip", zip_buffer, "application/zip")},
    )
    assert response.status_code == 200

    # OCR 実行エンドポイントを呼び出します
    response = client.post(f"/api/jobs/{job_id}/ocr")

    # 画像ファイルがないため 400 エラーになります
    assert response.status_code == 400
    assert "画像" in response.json()["detail"]


def test_run_ocr_updates_job_status(client: TestClient) -> None:
    """OCR 実行後にジョブ状態が completed に更新されることを確認します。"""
    # ジョブを作成して ZIP をアップロードします
    response = client.post("/api/jobs/")
    job_id = response.json()["job_id"]

    zip_buffer = create_zip_buffer(["page1.png"])
    client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )

    # OCR を実行します
    client.post(f"/api/jobs/{job_id}/ocr")

    # ジョブ状態を取得します
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()

    # 状態が completed に更新されていることを確認します
    assert data["status"] == "completed"
