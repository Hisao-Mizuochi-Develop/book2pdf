"""OCR 実行 API のテストです。

このファイルでは、ZIP アップロード後の OCR 実行エンドポイントに対する
テストを提供します。
ndlocr_cli はローカル開発環境にインストールされていないため、
モック OCR エンジンを使用して動作を確認します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# JSON 形式のデータを扱うための標準ライブラリです
import json

# テスト用にメモリ上のバイナリストリームを扱うための標準ライブラリです
import io

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
from pathlib import Path

# 一時ファイルを作成するための標準ライブラリです
import tempfile

# ポーリング待機に使用する標準ライブラリです
import time

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
    """テスト用の HTTP クライアントを提供します。

    TestClient をコンテキストマネージャとして使用することで、
    バックグラウンドタスク（asyncio.create_task など）が
    正しくスケジュールされ、実行されるようになります。
    """
    with TestClient(app) as client:
        yield client


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


@pytest.fixture
def mock_pdf_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    """検索可能 PDF 生成をモックに置き換えます。

    MockOcrEngine は sorted XML を作成しないため、実際の PDF 生成は失敗します。
    この fixture で PDF 生成をモックすることで、OCR 成功 → PDF 成功 → COMPLETED
    というフロー全体をテストできます。
    """
    mock_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    mock_pdf.write(b"%PDF-1.4\n")
    mock_pdf.close()

    def mock_generate(job_id: str, output_dir: Path, extract_dir: Path) -> Path:
        return Path(mock_pdf.name)

    monkeypatch.setattr(
        "app.routers.jobs.generate_searchable_pdf",
        mock_generate,
    )


def _wait_for_terminal_status(client: TestClient, job_id: str, timeout_sec: float = 2.0) -> dict:
    """ジョブが完了または失敗の終端状態になるまでポーリングします。

    Args:
        client: テスト用 HTTP クライアント
        job_id: 対象ジョブ ID
        timeout_sec: 最大待機時間（秒）

    Returns:
        ジョブ状態の JSON（辞書）
    """
    end_time = time.time() + timeout_sec
    while time.time() < end_time:
        response = client.get(f"/api/jobs/{job_id}")
        data = response.json()
        if data["status"] in ("completed", "failed"):
            return data
        time.sleep(0.05)
    # タイムアウト時は最後に取得した状態を返します
    return data


def test_run_ocr_success(client: TestClient, mock_pdf_generator: None) -> None:
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

    # OCR 処理が正常に開始されたことを確認します
    assert response.status_code == 200
    data = response.json()

    # レスポンスに job_id が含まれていることを確認します
    assert data["job_id"] == job_id

    # エンドポイントは即座に PROCESSING を返します（非同期処理のため）
    assert data["status"] == "processing"

    # バックグラウンドタスクの完了を待ちます
    data = _wait_for_terminal_status(client, job_id)

    # 最終的に completed に遷移していることを確認します
    assert data["status"] == "completed"

    # モック OCR から認識結果テキストが保存されていることを確認します
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


def test_run_ocr_updates_job_status(
    client: TestClient,
    mock_pdf_generator: None,
) -> None:
    """OCR・PDF 生成完了後にジョブ状態が completed に更新されることを確認します。"""
    # ジョブを作成して ZIP をアップロードします
    response = client.post("/api/jobs/")
    job_id = response.json()["job_id"]

    zip_buffer = create_zip_buffer(["page1.png"])
    client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )

    # OCR を実行します（非同期でバックグラウンドタスクが開始されます）
    response = client.post(f"/api/jobs/{job_id}/ocr")
    assert response.status_code == 200

    # バックグラウンドタスクの完了を待ちます
    data = _wait_for_terminal_status(client, job_id)

    # 状態が completed に更新されていることを確認します
    assert data["status"] == "completed"


def test_run_ocr_writes_staged_progress(
    client: TestClient,
    mock_pdf_generator: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """OCR・PDF 生成完了後に段階的進捗ファイルが書き込まれることを確認します（3/3）。"""
    from app.routers import jobs as jobs_router

    # 進捗ファイルの保存先をテスト用一時ディレクトリに差し替えます
    progress_dir = tmp_path / "progress"
    monkeypatch.setattr(jobs_router, "_PROGRESS_DIR", progress_dir)

    # ジョブを作成して ZIP をアップロードします
    response = client.post("/api/jobs/")
    job_id = response.json()["job_id"]

    zip_buffer = create_zip_buffer(["page1.png"])
    client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )

    # OCR を実行します
    response = client.post(f"/api/jobs/{job_id}/ocr")
    assert response.status_code == 200

    # バックグラウンドタスクの完了を待ちます
    data = _wait_for_terminal_status(client, job_id)
    assert data["status"] == "completed"

    # 進捗ファイルが書き込まれていることを確認します
    progress_file = progress_dir / f"{job_id}.json"
    assert progress_file.exists(), "進捗ファイルが作成されていません"

    progress_data = json.loads(progress_file.read_text(encoding="utf-8"))
    assert progress_data["status"] == "completed"
    assert progress_data["progress"] == 1.0
    # current_page は実際の画像枚数に等しい（テストは 1 枚のアップロード）
    assert progress_data["current_page"] == 1
    assert progress_data["total_pages"] == 1
    assert progress_data["message"] == "PDF 生成が完了しました"


def test_ocr_engine_sends_disable_progress(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """RemoteNdloCrOcrEngine が ocr-worker に enable_progress=False を送信することを確認します。"""
    from app.services.ocr_engine import RemoteNdloCrOcrEngine
    import httpx

    captured_payload: dict | None = None

    def mock_post(url: str, **kwargs) -> httpx.Response:
        nonlocal captured_payload
        captured_payload = kwargs.get("json")
        # ダミーの正常レスポンスを返します
        return httpx.Response(
            status_code=200,
            json={"success": True, "text": "mock", "output_dir": "/tmp", "message": ""},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", mock_post)

    engine = RemoteNdloCrOcrEngine(worker_url="http://dummy:8001")
    dummy_image = tmp_path / "test.png"
    dummy_image.write_bytes(b"\x89PNG\r\n\x1a\n")
    engine.run(
        image_files=[str(dummy_image)],
        work_dir=tmp_path,
        job_id="test-job-id",
    )

    assert captured_payload is not None, "リクエストボディが送信されていません"
    assert captured_payload.get("enable_progress") is False, "enable_progress=False が含まれていません"
    assert captured_payload.get("job_id") == "test-job-id"
