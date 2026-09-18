"""進捗通知（SSE）関連 API のテストです。

このファイルでは、OCR 処理の進捗を Server-Sent Events で配信する
`/api/jobs/{job_id}/events` エンドポイントに対するテストを提供します。

SY002002: ファイルベースの進捗共有を廃止し、backend の in-memory ストアと
ocr-worker REST API ポーリングに移行した後のテストです。

注意:
    `fastapi.testclient.TestClient` 経由の同期ストリーミングでは、
    非同期 generator が yield した chunk がクライアント側に確実に届かない、
    または届くタイミングが不定となりテストが不安定になる現象が確認されました。
    そのため、HTTP ストリームを経由せずに `_progress_event_generator` async generator
    を直接呼び出す形で検証しています。
"""

from __future__ import annotations

import asyncio
import json

import pytest
from app.main import app
from app.routers import jobs as jobs_router
from app.routers.jobs import _merge_progress_data, _progress_event_generator
from app.services import job_manager
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """同期テスト用の HTTP クライアントを提供します。"""
    with TestClient(app) as client:
        yield client


def _parse_event(event_text: str) -> dict | None:
    """SSE 形式のイベント文字列を辞書に変換します。"""
    text = event_text.strip()
    if text.startswith("data: "):
        payload = text.removeprefix("data: ").strip()
        if payload == "[DONE]":
            return None
        return json.loads(payload)
    return None


def _setup_backend_progress(
    job_id: str,
    status: str,
    progress: float = 0.0,
    current_page: int = 0,
    total_pages: int = 0,
    message: str = "",
) -> None:
    """backend の in-memory 進捗ストアにテストデータを登録します。"""
    job_manager.update_progress(
        job_id=job_id,
        status=status,
        progress=progress,
        current_page=current_page,
        total_pages=total_pages,
        message=message,
    )


def test_stream_job_events_not_found(client: TestClient) -> None:
    """存在しないジョブ ID に対して SSE エンドポイントが 404 を返すことを確認します。"""
    response = client.get("/api/jobs/00000000-0000-0000-0000-000000000000/events")
    assert response.status_code == 404
    assert "ジョブが見つかりません" in response.json()["detail"]


@pytest.mark.anyio
@pytest.mark.timeout(5)
async def test_stream_job_events_backend_only(monkeypatch) -> None:
    """ocr-worker への接続がない場合、backend の in-memory データのみでイベントが配信されることを確認します。"""
    monkeypatch.setattr(jobs_router, "_OCR_WORKER_POLL_INTERVAL", 0.05)

    job_id = "test-job-backend-only"

    async def fake_connect_error(self, url, **kwargs):
        import httpx
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "get", fake_connect_error)

    _setup_backend_progress(
        job_id,
        status="processing",
        progress=0.3,
        current_page=1,
        total_pages=5,
        message="backend のみ",
    )

    try:
        events: list[dict] = []
        async for event_text in _progress_event_generator(job_id):
            event = _parse_event(event_text)
            if event is not None:
                events.append(event)
                break

        assert len(events) >= 1
        assert events[0]["status"] == "processing"
        assert events[0]["progress"] == pytest.approx(0.3, abs=0.01)
        assert events[0]["current_page"] == 1
        assert events[0]["total_pages"] == 5
    finally:
        job_manager.delete_progress(job_id)


@pytest.mark.anyio
@pytest.mark.timeout(5)
async def test_stream_job_events_merged(monkeypatch) -> None:
    """backend と ocr-worker のデータが正しくマージされてイベントが配信されることを確認します。"""
    monkeypatch.setattr(jobs_router, "_OCR_WORKER_POLL_INTERVAL", 0.05)

    job_id = "test-job-merged"

    class FakeResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
            self.text = json.dumps(json_data) if json_data is not None else ""

        def json(self):
            return self._json

    async def fake_get(self, url, **kwargs):
        if f"/progress/{job_id}" in url:
            return FakeResponse(
                200,
                {
                    "progress": 0.75,
                    "current_page": 3,
                    "total_pages": 4,
                    "message": "ocr-worker からの進捗",
                },
            )
        return FakeResponse(404, None)

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "get", fake_get)

    _setup_backend_progress(
        job_id,
        status="processing",
        progress=0.1,
        current_page=0,
        total_pages=0,
        message="backend メッセージ",
    )

    try:
        events: list[dict] = []
        async for event_text in _progress_event_generator(job_id):
            event = _parse_event(event_text)
            if event is not None:
                events.append(event)
                break

        # マージルールの検証:
        # - status / timestamp → backend 優先
        # - progress / current_page / total_pages / message → ocr-worker 優先
        assert len(events) >= 1
        assert events[0]["status"] == "processing"  # backend 優先
        assert events[0]["progress"] == pytest.approx(0.75, abs=0.01)  # worker 優先
        assert events[0]["current_page"] == 3  # worker 優先
        assert events[0]["total_pages"] == 4  # worker 優先
        assert events[0]["message"] == "ocr-worker からの進捗"  # worker 優先
    finally:
        job_manager.delete_progress(job_id)


@pytest.mark.anyio
@pytest.mark.timeout(5)
async def test_stream_job_events_worker_404(monkeypatch) -> None:
    """ocr-worker が 404 を返す場合、backend のみのデータでイベントが配信されることを確認します。"""
    monkeypatch.setattr(jobs_router, "_OCR_WORKER_POLL_INTERVAL", 0.05)

    job_id = "test-job-worker-404"

    class FakeResponse:
        def __init__(self, status_code, json_data=None):
            self.status_code = status_code
            self._json = json_data
            self.text = json.dumps(json_data) if json_data is not None else ""

        def json(self):
            return self._json

    async def fake_get(self, url, **kwargs):
        return FakeResponse(404)

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "get", fake_get)

    _setup_backend_progress(
        job_id,
        status="processing",
        progress=0.5,
        current_page=2,
        total_pages=4,
        message="backend のみ（404 フォールバック）",
    )

    try:
        events: list[dict] = []
        async for event_text in _progress_event_generator(job_id):
            event = _parse_event(event_text)
            if event is not None:
                events.append(event)
                break

        assert len(events) >= 1
        assert events[0]["status"] == "processing"
        assert events[0]["progress"] == pytest.approx(0.5, abs=0.01)
        assert events[0]["message"] == "backend のみ（404 フォールバック）"
    finally:
        job_manager.delete_progress(job_id)


@pytest.mark.anyio
@pytest.mark.timeout(5)
async def test_stream_job_events_worker_timeout(monkeypatch) -> None:
    """ocr-worker がタイムアウトする場合、backend のみのデータでイベントが配信されることを確認します。"""
    monkeypatch.setattr(jobs_router, "_OCR_WORKER_POLL_INTERVAL", 0.05)

    job_id = "test-job-worker-timeout"

    async def fake_timeout(self, url, **kwargs):
        import httpx
        raise httpx.TimeoutException("Request timed out")

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "get", fake_timeout)

    _setup_backend_progress(
        job_id,
        status="processing",
        progress=0.6,
        current_page=3,
        total_pages=5,
        message="backend のみ（タイムアウト フォールバック）",
    )

    try:
        events: list[dict] = []
        async for event_text in _progress_event_generator(job_id):
            event = _parse_event(event_text)
            if event is not None:
                events.append(event)
                break
            if event_text == "data: [DONE]\n\n":
                break

        assert len(events) >= 1
        assert events[0]["status"] == "processing"
        assert events[0]["progress"] == pytest.approx(0.6, abs=0.01)
    finally:
        job_manager.delete_progress(job_id)


@pytest.mark.anyio
@pytest.mark.timeout(5)
async def test_stream_job_events_completed(monkeypatch) -> None:
    """ジョブが completed になったら [DONE] シグナルでストリームが終了することを確認します。"""
    monkeypatch.setattr(jobs_router, "_OCR_WORKER_POLL_INTERVAL", 0.05)

    job_id = "test-job-completed"

    async def fake_connect_error(self, url, **kwargs):
        import httpx
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "get", fake_connect_error)

    _setup_backend_progress(
        job_id,
        status="completed",
        progress=1.0,
        current_page=10,
        total_pages=10,
        message="OCR 処理が完了しました",
    )

    try:
        events: list[str] = []
        async for event_text in _progress_event_generator(job_id):
            events.append(event_text)
            if event_text == "data: [DONE]\n\n":
                break

        assert any(e == "data: [DONE]\n\n" for e in events)
    finally:
        job_manager.delete_progress(job_id)


@pytest.mark.anyio
@pytest.mark.timeout(5)
async def test_stream_job_events_failed(monkeypatch) -> None:
    """ジョブが failed になったら [DONE] シグナルでストリームが終了することを確認します。"""
    monkeypatch.setattr(jobs_router, "_OCR_WORKER_POLL_INTERVAL", 0.05)

    job_id = "test-job-failed"

    async def fake_connect_error(self, url, **kwargs):
        import httpx
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "get", fake_connect_error)

    _setup_backend_progress(
        job_id,
        status="failed",
        progress=0.0,
        current_page=5,
        total_pages=10,
        message="OCR 処理に失敗しました",
    )

    try:
        events: list[str] = []
        async for event_text in _progress_event_generator(job_id):
            events.append(event_text)
            if event_text == "data: [DONE]\n\n":
                break

        assert any(e == "data: [DONE]\n\n" for e in events)
    finally:
        job_manager.delete_progress(job_id)


@pytest.mark.anyio
@pytest.mark.timeout(10)
async def test_stream_job_events_heartbeat(monkeypatch) -> None:
    """進捗が更新されない間、ハートビートイベントが送信されることを確認します。"""
    monkeypatch.setattr(jobs_router, "_OCR_WORKER_POLL_INTERVAL", 0.05)
    monkeypatch.setattr(jobs_router, "_HEARTBEAT_INTERVAL", 0.1)

    job_id = "test-job-heartbeat"

    async def delayed_update():
        await asyncio.sleep(0.5)
        _setup_backend_progress(
            job_id,
            status="completed",
            progress=1.0,
            current_page=1,
            total_pages=1,
            message="完了",
        )

    asyncio.create_task(delayed_update())

    async def fake_404(self, url, **kwargs):
        class FakeResponse:
            status_code = 404
            text = ""
        return FakeResponse()

    monkeypatch.setattr(jobs_router.httpx.AsyncClient, "get", fake_404)

    heartbeat_received = False
    events: list[str] = []
    try:
        async for event_text in _progress_event_generator(job_id):
            events.append(event_text)
            if ": keepalive" in event_text:
                heartbeat_received = True
                break

        assert heartbeat_received is True
        assert any(": keepalive" in e for e in events)
    finally:
        job_manager.delete_progress(job_id)


def test_merge_progress_data_prefers_nonempty_message_when_higher_progress_is_empty() -> None:
    """SY002003: 進捗値が大きい側の message が空文字でも、もう一方の非空メッセージを保持します。"""
    backend = {"progress": 0.9, "message": ""}
    worker = {"progress": 0.3, "message": "OCR処理中です（2/3）"}

    merged = _merge_progress_data(backend, worker)

    assert merged["progress"] == 0.9
    assert merged["message"] == "OCR処理中です（2/3）"


def test_merge_progress_data_prefers_worker_per_page_message_over_backend() -> None:
    """SY002003: backend の進捗が大きくても ocr-worker の per-page メッセージを優先します。"""
    backend = {"progress": 0.9, "message": "PDFファイル生成中です"}
    worker = {"progress": 0.3, "message": "OCR処理中です（2/3）"}

    merged = _merge_progress_data(backend, worker)

    assert merged["progress"] == 0.9
    assert merged["message"] == "OCR処理中です（2/3）"


def test_merge_progress_data_worker_higher_progress_empty_message_fallback() -> None:
    """ocr-worker の進捗が大きいが message が空の場合、backend の非空メッセージにフォールバックします。"""
    backend = {"progress": 0.3, "message": "OCR処理を開始しました"}
    worker = {"progress": 0.6, "message": ""}

    merged = _merge_progress_data(backend, worker)

    assert merged["progress"] == 0.6
    assert merged["message"] == "OCR処理を開始しました"
