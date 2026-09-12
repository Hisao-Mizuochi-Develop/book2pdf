"""進捗通知（SSE）関連 API のテストです。

このファイルでは、OCR 処理の進捗を Server-Sent Events で配信する
`/api/jobs/{job_id}/events` エンドポイントに対するテストを提供します。

注意:
    `fastapi.testclient.TestClient` 経由の同期ストリーミングでは、
    非同期 generator が yield した chunk がクライアント側に確実に届かない、
    または届くタイミングが不定となりテストが不安定になる現象が確認されました。
    そのため、HTTP ストリームを経由せずに `_progress_event_generator` async generator
    を直接呼び出す形で検証しています。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# JSON 形式の進捗ファイルを読み書きするための標準ライブラリです
import json

# テストを実行するためのマーカーです
import pytest

# FastAPI アプリを同期的にテストするためのクライアントです
from fastapi.testclient import TestClient

# テスト対象の FastAPI アプリケーションを読み込みます
from app.main import app

# SSE 配信用の進捗イベントジェネレータを読み込みます
from app.routers.jobs import _progress_event_generator

# 進捗ファイルの保存先ディレクトリを上書きするためにルーターモジュールを読み込みます
from app.routers import jobs as jobs_router


@pytest.fixture
def client() -> TestClient:
    """同期テスト用の HTTP クライアントを提供します。"""
    with TestClient(app) as client:
        yield client


def _write_progress_file(
    progress_dir,
    job_id: str,
    status: str,
    progress: float,
    current_page: int = 0,
    total_pages: int = 0,
    message: str = "",
) -> None:
    """テスト用の進捗ファイルを作成します。

    Args:
        progress_dir: 進捗ファイルを保存するディレクトリ
        job_id: ジョブ ID
        status: ジョブの状態文字列
        progress: 進捗率
        current_page: 現在処理中のページ番号
        total_pages: 処理対象の総ページ数
        message: 補足メッセージ
    """
    progress_file = progress_dir / f"{job_id}.json"
    data = {
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "current_page": current_page,
        "total_pages": total_pages,
        "message": message,
        "timestamp": "2026-01-01T00:00:00+00:00",
    }
    progress_file.write_text(json.dumps(data), encoding="utf-8")


def _parse_event(event_text: str) -> dict:
    """SSE 形式のイベント文字列を辞書に変換します。

    Args:
        event_text: "data: {...}" 形式のイベント文字列

    Returns:
        イベントの内容を表す辞書
    """
    return json.loads(event_text.removeprefix("data: ").strip())


def test_stream_job_events_not_found(client: TestClient) -> None:
    """存在しないジョブ ID に対して SSE エンドポイントが 404 を返すことを確認します。"""
    response = client.get("/api/jobs/00000000-0000-0000-0000-000000000000/events")

    assert response.status_code == 404
    assert "ジョブが見つかりません" in response.json()["detail"]


@pytest.mark.anyio
@pytest.mark.timeout(5)
async def test_stream_job_events(monkeypatch, tmp_path) -> None:
    """SSE で進捗イベントが配信され、完了でストリームが終了することを確認します。"""
    # テスト用の進捗ディレクトリを作成します
    progress_dir = tmp_path / "progress"
    progress_dir.mkdir()

    # ルーターモジュールの進捗ディレクトリを一時ディレクトリに差し替えます
    monkeypatch.setattr(jobs_router, "_PROGRESS_DIR", progress_dir)

    # ルーターモジュールのポーリング間隔を短く差し替えます
    monkeypatch.setattr(jobs_router, "_POLL_INTERVAL", 0.05)

    job_id = "test-job-stream-completed"

    # 最初の進捗ファイルを processing 状態で作成します
    _write_progress_file(
        progress_dir,
        job_id,
        status="processing",
        progress=0.0,
        current_page=0,
        total_pages=10,
        message="OCR 処理を開始しました",
    )

    # 進捗イベントジェネレータを直接非同期イテレーションします
    events: list[dict] = []
    async for event_text in _progress_event_generator(job_id):
        event = _parse_event(event_text)
        events.append(event)

        # processing イベントを受信したら、進捗ファイルを completed に更新します
        if event["status"] == "processing":
            _write_progress_file(
                progress_dir,
                job_id,
                status="completed",
                progress=1.0,
                current_page=10,
                total_pages=10,
                message="OCR 処理が完了しました",
            )

        # completed イベントを受信したらループを終了します
        if event["status"] == "completed":
            break

    # 2 つの進捗イベントが配信されていることを確認します
    assert len(events) == 2

    # 1 つ目のイベントが processing 状態であることを確認します
    assert events[0]["job_id"] == job_id
    assert events[0]["status"] == "processing"
    assert events[0]["progress"] == 0.0
    assert events[0]["current_page"] == 0
    assert events[0]["total_pages"] == 10

    # 2 つ目のイベントが completed 状態であることを確認します
    assert events[1]["job_id"] == job_id
    assert events[1]["status"] == "completed"
    assert events[1]["progress"] == 1.0
    assert events[1]["current_page"] == 10
    assert events[1]["total_pages"] == 10


@pytest.mark.anyio
@pytest.mark.timeout(5)
async def test_stream_job_events_failed(monkeypatch, tmp_path) -> None:
    """failed 状態の進捗イベントを受信するとストリームが終了することを確認します。"""
    # テスト用の進捗ディレクトリを作成します
    progress_dir = tmp_path / "progress"
    progress_dir.mkdir()

    # ルーターモジュールの進捗ディレクトリを一時ディレクトリに差し替えます
    monkeypatch.setattr(jobs_router, "_PROGRESS_DIR", progress_dir)

    # ルーターモジュールのポーリング間隔を短く差し替えます
    monkeypatch.setattr(jobs_router, "_POLL_INTERVAL", 0.05)

    job_id = "test-job-stream-failed"

    # 進捗ファイルを failed 状態で作成します
    _write_progress_file(
        progress_dir,
        job_id,
        status="failed",
        progress=0.0,
        current_page=0,
        total_pages=5,
        message="OCR 処理に失敗しました",
    )

    # 進捗イベントジェネレータを直接非同期イテレーションします
    events: list[dict] = []
    async for event_text in _progress_event_generator(job_id):
        event = _parse_event(event_text)
        events.append(event)

        if event["status"] == "failed":
            break

    # failed イベントが 1 つ配信されていることを確認します
    assert len(events) == 1
    assert events[0]["status"] == "failed"
    assert events[0]["message"] == "OCR 処理に失敗しました"


@pytest.mark.anyio
@pytest.mark.timeout(5)
async def test_stream_job_events_heartbeat(monkeypatch, tmp_path) -> None:
    """長時間進捗が変化しない場合にハートビートが送信されることを確認します。"""
    # テスト用の進捗ディレクトリを作成します
    progress_dir = tmp_path / "progress"
    progress_dir.mkdir()

    # ルーターモジュールの進捗ディレクトリを一時ディレクトリに差し替えます
    monkeypatch.setattr(jobs_router, "_PROGRESS_DIR", progress_dir)

    # ルーターモジュールのポーリング間隔を短く差し替えます
    monkeypatch.setattr(jobs_router, "_POLL_INTERVAL", 0.05)

    # ハートビート間隔を短く差し替えます（テスト用に 0.3 秒）
    monkeypatch.setattr(jobs_router, "_HEARTBEAT_INTERVAL", 0.3)

    job_id = "test-job-heartbeat"

    # 進捗ファイルを processing 状態で作成します
    _write_progress_file(
        progress_dir,
        job_id,
        status="processing",
        progress=0.33,
        current_page=1,
        total_pages=3,
        message="OCR 処理中です",
    )

    # 進捗イベントジェネレータを直接非同期イテレーションします
    events: list[str] = []
    heartbeat_received = False

    async for event_text in _progress_event_generator(job_id):
        events.append(event_text)

        # ハートビート（SSE コメント行）を受信したか確認します
        if ": keepalive" in event_text:
            heartbeat_received = True
            break

    # ハートビートが受信されたことを確認します
    assert heartbeat_received is True
    assert any(": keepalive" in e for e in events)


@pytest.mark.anyio
@pytest.mark.timeout(5)
async def test_stream_job_events_atomic_write(monkeypatch, tmp_path) -> None:
    """原子書き込み後に進捗ファイルが正しく読み取れることを確認します。"""
    # テスト用の進捗ディレクトリを作成します
    progress_dir = tmp_path / "progress"
    progress_dir.mkdir()

    # ルーターモジュールの進捗ディレクトリを一時ディレクトリに差し替えます
    monkeypatch.setattr(jobs_router, "_PROGRESS_DIR", progress_dir)

    # ルーターモジュールのポーリング間隔を短く差し替えます
    monkeypatch.setattr(jobs_router, "_POLL_INTERVAL", 0.05)

    job_id = "test-job-atomic"

    # _write_progress を呼び出して進捗ファイルを作成します
    jobs_router._write_progress(
        job_id=job_id,
        status="processing",
        progress=0.66,
        current_page=2,
        total_pages=3,
        message="原子書き込みテスト",
    )

    # 進捗ファイルが存在することを確認します
    progress_file = progress_dir / f"{job_id}.json"
    assert progress_file.exists()

    # 内容が正しいことを確認します
    content = progress_file.read_text(encoding="utf-8")
    data = json.loads(content)
    assert data["status"] == "processing"
    assert data["progress"] == 0.66
    assert data["current_page"] == 2
    assert data["total_pages"] == 3
    assert data["message"] == "原子書き込みテスト"

    # 一時ファイルが残っていないことを確認します
    temp_file = progress_dir / f"{job_id}.json.tmp"
    assert not temp_file.exists()

    # 進捗イベントジェネレータが正しく読み取れることを確認します
    events: list[dict] = []
    async for event_text in _progress_event_generator(job_id):
        event = _parse_event(event_text)
        events.append(event)
        if event["status"] == "processing":
            break

    assert len(events) >= 1
    assert events[0]["progress"] == 0.66


def test_worker_update_progress_writes_per_page_progress(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """ocr-worker の progress_reporter.write_progress がページ単位の進捗ファイルを正しく書き込むことを確認します。

    OW004001: ocr-worker の inference.py 内で各ページ処理後に進捗ファイルを書き込み、
    backend の SSE ストリームが実際の処理進捗を返すことができるようにします。
    """
    import json
    from ndlocr_cli_patches.progress_reporter import write_progress

    # 進捗ファイルの出力先を一時ディレクトリに向けます
    progress_dir = tmp_path / "progress"
    monkeypatch.setenv("PROGRESS_DIR", str(progress_dir))

    job_id = "test-ow-001"

    # 1/3 ページ目の進捗を書き込みます
    write_progress(
        job_id=job_id,
        current_page=1,
        total_pages=3,
        message="OCR 処理中です（1/3）",
    )

    progress_file = progress_dir / f"{job_id}.json"
    assert progress_file.exists(), "進捗ファイルが作成されていません"

    data = json.loads(progress_file.read_text(encoding="utf-8"))
    assert data["status"] == "processing"
    assert data["progress"] == pytest.approx(0.27, abs=0.01)
    assert data["current_page"] == 1
    assert data["total_pages"] == 3
    assert data["message"] == "OCR 処理中です（1/3）"
    assert "timestamp" in data

    # 一時ファイルが残っていないことを確認します
    assert not (progress_dir / f"{job_id}.json.tmp").exists()

    # job_id が未設定の場合は何も書き込まれないことを確認します
    write_progress(job_id=None, current_page=1, total_pages=3, message="no-job")
    assert not (progress_dir / "None.json").exists()
