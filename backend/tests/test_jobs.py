"""ジョブ関連 API のテストです。

このファイルでは、ジョブ作成、ZIP アップロード、ジョブ状態取得などの
エンドポイントに対するテストを提供します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# テスト用にメモリ上のバイナリストリームを扱うための標準ライブラリです
import io

# JSON のシリアライズに使用します
import json

# ZIP ファイルを作成するための標準ライブラリです
import zipfile

# テスト関数や fixture を書くためのライブラリです
import pytest

# テスト対象の FastAPI アプリケーションを読み込みます
from app.main import app

# ジョブ状態の列挙型を読み込みます
from app.models.job import JobStatus

# FastAPI のテスト用 HTTP クライアントです
# サーバーを起動せずに API をテストできます
from fastapi.testclient import TestClient


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


def test_upload_zip_excludes_macosx_resource_forks(client: TestClient) -> None:
    """macOS のリソースフォーク (__MACOSX/._*) が画像一覧から除外されることを確認します。"""
    # まずジョブを作成します
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # 通常画像に加え、macOS のリソースフォークを含む ZIP を作成します
    zip_buffer = create_zip_buffer(
        [
            "page1.png",
            "page2.png",
            "__MACOSX/._page1.png",
            "__MACOSX/._page2.png",
            "__MACOSX/.DS_Store",
        ]
    )

    # ZIP をアップロードします
    response = client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("macosx.zip", zip_buffer, "application/zip")},
    )

    # アップロードが成功していることを確認します
    assert response.status_code == 200

    # レスポンス本文を辞書として取得します
    data = response.json()

    # __MACOSX 配下のファイルが除外されていることを確認します
    assert sorted(data["files"]) == ["page1.png", "page2.png"]


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

    # SY002002: progress フィールドが含まれていることを確認します
    # ocr-worker へ接続できない場合はデフォルト値になります
    assert "progress" in data
    assert "current_page" in data
    assert "total_pages" in data
    assert data["progress"] == 0.0
    assert data["current_page"] == 0
    assert data["total_pages"] == 0


def test_get_job_not_found(client: TestClient) -> None:
    """存在しないジョブ ID に対して 404 エラーが返ることを確認します。"""
    response = client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "ジョブが見つかりません" in response.json()["detail"]


def test_get_job_with_progress_fallback(client: TestClient, monkeypatch) -> None:
    """ocr-worker へ接続できない場合、progress=0.0 でフォールバックすることを確認します。

    SY002002:
    - get_job() は ocr-worker へ HTTP GET を行いますが、接続エラー時は
      progress=0.0 / current_page=0 / total_pages=0 でフォールバックします。
    """

    import httpx
    from app.routers import jobs as jobs_router

    # ジョブを作成します
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    created_job_id = response.json()["job_id"]

    # ocr-worker への接続を失敗させます
    async def fake_connect_error(self, url, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "get", fake_connect_error)

    # ジョブ状態を取得します
    response = client.get(f"/api/jobs/{created_job_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["job_id"] == created_job_id
    assert data["status"] == "pending"
    # ocr-worker へ接続できない場合、progress フィールドはデフォルト値になります
    assert data["progress"] == 0.0
    assert data["current_page"] == 0
    assert data["total_pages"] == 0


def test_get_job_with_progress_merged(client: TestClient, monkeypatch) -> None:
    """ocr-worker から progress データを取得してマージすることを確認します。

    SY002002:
    - get_job() は ocr-worker の GET /progress/{job_id} をポーリングします
    - progress / current_page / total_pages / message は ocr-worker データを優先します
    - status は backend のフェーズ値を優先します
    """
    from app.routers import jobs as jobs_router

    # ジョブを作成してアップロード状態にします
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    created_job_id = response.json()["job_id"]

    zip_buffer = create_zip_buffer(["page1.png", "page2.png"])
    client.post(
        f"/api/jobs/{created_job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )

    # ocr-worker のレスポンスをモックします
    fake_progress = {
        "job_id": created_job_id,
        "current_page": 2,
        "total_pages": 2,
        "progress": 0.6,
        "status": "processing",
        "message": "OCR処理中です（2/2）",
        "timestamp": "2026-09-13T12:00:00+00:00",
    }

    async def fake_get(self, url, **kwargs):
        class FakeResponse:
            status_code = 200
            text = json.dumps(fake_progress)
            def json(self):
                return fake_progress
        return FakeResponse()

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "get", fake_get)

    # ジョブ状態を取得します
    response = client.get(f"/api/jobs/{created_job_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["job_id"] == created_job_id
    # status は backend のフェーズ値を優先（uploaded）
    assert data["status"] == "uploaded"
    # progress / message は大きい方を優先、current_page / total_pages は ocr-worker 優先
    assert data["progress"] == pytest.approx(0.6, abs=0.01)
    assert data["current_page"] == 2
    assert data["total_pages"] == 2
    assert data["message"] == "OCR処理中です（2/2）"


def test_get_job_prefers_backend_progress_when_larger(client: TestClient, monkeypatch) -> None:
    """backend のフェーズ進捗が ocr-worker より進んでいる場合は backend を優先します。

    SY002003: PDF 生成中/完了時は backend が管理する progress/message を表示するため、
    ocr-worker の per-page 進捗（0.6 など）より backend の値（0.75 / 1.0）を優先します。
    """
    from app.routers import jobs as jobs_router
    from app.services import job_manager

    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    zip_buffer = create_zip_buffer(["page1.png", "page2.png"])
    client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )

    # ocr-worker は最後のページ進捗を返します
    fake_progress = {
        "job_id": job_id,
        "current_page": 2,
        "total_pages": 2,
        "progress": 0.6,
        "status": "processing",
        "message": "OCR処理中です（2/2）",
        "timestamp": "2026-09-13T12:00:00+00:00",
    }

    async def fake_get(self, url, **kwargs):
        class FakeResponse:
            status_code = 200
            text = json.dumps(fake_progress)
            def json(self):
                return fake_progress
        return FakeResponse()

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "get", fake_get)

    # backend が PDF 生成中の進捗を書き込んだ場合
    job_manager.update_progress(
        job_id,
        status="processing",
        progress=0.75,
        current_page=2,
        total_pages=2,
        message="PDFファイル生成中です",
    )

    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    # backend の進捗の方が大きいので backend の message を優先
    assert data["progress"] == pytest.approx(0.75, abs=0.01)
    assert data["message"] == "PDFファイル生成中です"
    # current_page / total_pages は ocr-worker 優先
    assert data["current_page"] == 2
    assert data["total_pages"] == 2

    # backend が完了進捗を書き込んだ場合も backend を優先
    job_manager.update_progress(
        job_id,
        status="completed",
        progress=1.0,
        current_page=2,
        total_pages=2,
        message="PDFファイル生成が完了しました",
    )

    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["progress"] == pytest.approx(1.0, abs=0.01)
    assert data["message"] == "PDFファイル生成が完了しました"


def test_cancel_job_success(client: TestClient, monkeypatch, tmp_path) -> None:
    """進行中のジョブをキャンセルすると、関連リソースが削除されることを確認します。

    SY002002:
    - DELETE /api/jobs/{job_id} は 200 を返します
    - ジョブ・進捗情報は in-memory ストアから削除されます
    - extract_dir / output_dir / pdf_path に紐づくファイルが削除されます
    - ocr-worker へ `POST /cancel/{job_id}` が送信されます
    """
    from app.routers import jobs as jobs_router
    from app.services import job_manager

    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    zip_buffer = create_zip_buffer(["page1.png"])
    client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )

    # ジョブに紐づくファイルを作成します
    extract_dir = tmp_path / "extract"
    extract_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pdf_path = tmp_path / "result.pdf"
    pdf_path.write_text("dummy pdf")

    job_manager.update_job_status(
        job_id, JobStatus.PROCESSING, extract_dir=extract_dir
    )
    job_manager.update_job_with_ocr_result(job_id, output_dir=str(output_dir))
    job_manager.update_job_with_pdf_path(job_id, pdf_path=str(pdf_path))

    # ocr-worker へのキャンセル伝播をモックします
    captured_calls: list[str] = []

    async def fake_post(self, url, **kwargs):
        captured_calls.append(url)

        cancel_response = {"message": "ok", "job_id": job_id}

        class FakeResponse:
            status_code = 200
            text = json.dumps(cancel_response)

            def json(self):
                return cancel_response

        return FakeResponse()

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "post", fake_post)

    response = client.delete(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert "キャンセル" in data["message"]

    # ジョブが削除されていることを確認します
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 404

    # ファイルが削除されていることを確認します
    assert not extract_dir.exists()
    assert not output_dir.exists()
    assert not pdf_path.exists()

    # ocr-worker へキャンセルが伝播していることを確認します
    assert any("/cancel/" in call for call in captured_calls)


def test_cancel_job_not_found(client: TestClient, monkeypatch) -> None:
    """存在しないジョブをキャンセルしようとすると 404 エラーが返ることを確認します。"""
    from app.routers import jobs as jobs_router

    async def fake_post(self, url, **kwargs):
        class FakeResponse:
            status_code = 200
            text = "{}"
        return FakeResponse()

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "post", fake_post)

    response = client.delete("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "見つかりません" in response.json()["detail"]


def test_cancel_job_terminal_state(client: TestClient, monkeypatch) -> None:
    """完了・失敗・キャンセル済みのジョブは再キャンセルできないことを確認します。"""
    from app.routers import jobs as jobs_router
    from app.services import job_manager

    for status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
        response = client.post("/api/jobs/")
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        job_manager.update_job_status(job_id, status)

        async def fake_post(self, url, **kwargs):
            class FakeResponse:
                status_code = 200
                text = "{}"
            return FakeResponse()

        monkeypatch.setattr(jobs_router.httpx.AsyncClient, "post", fake_post)

        response = client.delete(f"/api/jobs/{job_id}")
        assert response.status_code == 400
        assert "キャンセルできません" in response.json()["detail"]


def test_cancel_job_pending(client: TestClient, monkeypatch) -> None:
    """pending 状態のジョブもキャンセル可能であることを確認します。"""
    from app.routers import jobs as jobs_router
    from app.services import job_manager

    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    async def fake_post(self, url, **kwargs):
        class FakeResponse:
            status_code = 200
            text = "{}"
        return FakeResponse()

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "post", fake_post)

    response = client.delete(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["job_id"] == job_id
    assert job_manager.get_job(job_id) is None
