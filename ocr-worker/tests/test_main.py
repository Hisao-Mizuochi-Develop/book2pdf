"""ocr-worker のキャンセル・クリーンアップ・進捗 API をテストします。

SY002002: ジョブのキャンセル、進捗データの削除、キャンセル済みジョブの
結果破棄を中心に検証します。
"""

from __future__ import annotations

import time
from typing import Any

from fastapi.testclient import TestClient


def _poll_result(client: TestClient, job_id: str, expected_status: int, timeout: float = 5.0) -> Any:
    """バックグラウンド OCR タスクが完了するまで GET /result をポーリングします。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/result/{job_id}")
        if response.status_code == expected_status:
            return response
        if response.status_code not in (202,):
            return response
        time.sleep(0.05)
    return client.get(f"/result/{job_id}")


def test_health_check(client: TestClient) -> None:
    """ヘルスチェックエンドポイントが正常応答を返すことを確認します。"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cancel_ocr_marks_job_as_cancelled(
    client: TestClient,
    progress_reporter: Any,
) -> None:
    """POST /cancel/{job_id} がキャンセルマークを設定することを確認します。"""
    job_id = "job-cancel-1"

    response = client.post(f"/cancel/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert "キャンセル" in data["message"]

    assert progress_reporter.is_cancelled(job_id) is True


def test_delete_progress_removes_data_and_cancel_mark(
    client: TestClient,
    progress_reporter: Any,
) -> None:
    """DELETE /progress/{job_id} が進捗とキャンセルマークを削除することを確認します。"""
    job_id = "job-delete-1"

    # 進捗データとキャンセルマークを事前に作成します
    progress_reporter.write_progress(job_id, 1, 2, "テスト進捗")
    progress_reporter.mark_cancelled(job_id)
    assert progress_reporter.get_progress(job_id) is not None
    assert progress_reporter.is_cancelled(job_id) is True

    response = client.delete(f"/progress/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert "削除" in data["message"]

    assert progress_reporter.get_progress(job_id) is None
    assert progress_reporter.is_cancelled(job_id) is False


def test_get_progress_returns_404_when_missing(client: TestClient) -> None:
    """存在しないジョブの進捗取得で 404 が返ることを確認します。"""
    response = client.get("/progress/non-existent-job")
    assert response.status_code == 404
    assert "見つかりません" in response.json()["detail"]


def test_get_progress_returns_stored_data(
    client: TestClient,
    progress_reporter: Any,
) -> None:
    """GET /progress/{job_id} が保存された進捗データを返すことを確認します。"""
    job_id = "job-progress-1"
    progress_reporter.write_progress(job_id, 1, 2, "1/2 完了")

    response = client.get(f"/progress/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["current_page"] == 1
    assert data["total_pages"] == 2
    assert data["status"] == "processing"
    assert "1/2 完了" in data["message"]


def test_run_ocr_returns_accepted_and_result_when_cancelled(
    client: TestClient,
    progress_reporter: Any,
    tmp_path: Any,
) -> None:
    """BE009001: キャンセル済みジョブは /ocr 受理後、結果取得で失敗応答を返します。

    SY002002: 協調的キャンセルにより、OCR 処理完了後に結果ストアは failed 状態、
    進捗ストアは cancelled 状態で更新されます。
    """
    job_id = "job-ocr-cancel"
    progress_reporter.mark_cancelled(job_id)

    # input_root/img/ 以下にダミー画像を配置します
    input_root = tmp_path / "input"
    img_dir = input_root / "img"
    img_dir.mkdir(parents=True)
    (img_dir / "page.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    output_root = tmp_path / "output"
    output_root.mkdir()

    response = client.post(
        "/ocr",
        json={
            "input_root": str(input_root),
            "output_root": str(output_root),
            "job_id": job_id,
            "enable_progress": True,
        },
    )
    # BE009001: /ocr は即座に 202 Accepted を返します
    assert response.status_code == 202
    data = response.json()
    assert data["job_id"] == job_id
    assert "開始" in data["message"]

    # バックグラウンドタスク完了後、GET /result は failed 状態を返します
    result_response = _poll_result(client, job_id, expected_status=500)
    assert result_response.status_code == 500
    assert "キャンセル" in result_response.json()["detail"]

    # 進捗が cancelled 状態で記録されていることを確認します
    progress_response = client.get(f"/progress/{job_id}")
    assert progress_response.status_code == 200
    assert progress_response.json()["status"] == "cancelled"


def test_run_ocr_returns_accepted_and_result_when_not_cancelled(
    client: TestClient,
    progress_reporter: Any,
    tmp_path: Any,
) -> None:
    """BE009001: キャンセルされていないジョブは /ocr 受理後、結果取得で正常応答を返します。"""
    job_id = "job-ocr-complete"

    input_root = tmp_path / "input"
    img_dir = input_root / "img"
    img_dir.mkdir(parents=True)
    (img_dir / "page.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    output_root = tmp_path / "output"
    output_root.mkdir()
    # テキスト収集のために txt ファイルを配置します
    txt_dir = output_root / "txt"
    txt_dir.mkdir()
    (txt_dir / "page.txt").write_text("テスト認識結果", encoding="utf-8")

    response = client.post(
        "/ocr",
        json={
            "input_root": str(input_root),
            "output_root": str(output_root),
            "job_id": job_id,
            "enable_progress": True,
        },
    )
    # BE009001: /ocr は即座に 202 Accepted を返します
    assert response.status_code == 202
    data = response.json()
    assert data["job_id"] == job_id
    assert "開始" in data["message"]

    # バックグラウンドタスク完了後、GET /result は結果を返します
    result_response = _poll_result(client, job_id, expected_status=200)
    assert result_response.status_code == 200
    result_data = result_response.json()
    assert "テスト認識結果" in result_data["text"]
    assert result_data["output_dir"] == str(output_root)

    progress_response = client.get(f"/progress/{job_id}")
    assert progress_response.status_code == 200
    assert progress_response.json()["status"] == "completed"
    assert progress_response.json()["progress"] == 1.0


def test_get_result_returns_processing(
    client: TestClient,
) -> None:
    """BE009001: 処理中のジョブに対して GET /result/{job_id} は 202 を返します。"""
    import app.result_store as result_store

    job_id = "job-result-processing"
    result_store.init_result(job_id)

    response = client.get(f"/result/{job_id}")
    assert response.status_code == 202
    assert "処理中" in response.json()["detail"]


def test_run_ocr_with_ruby_only_returns_accepted_and_result(
    client: TestClient,
    tmp_path: Any,
) -> None:
    """SY002003: ruby_only=True のジョブでも per-page 進捗が completed 状態で更新されることを確認します。"""
    job_id = "job-ocr-ruby-only"

    input_root = tmp_path / "input"
    img_dir = input_root / "img"
    img_dir.mkdir(parents=True)
    (img_dir / "page.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    output_root = tmp_path / "output"
    output_root.mkdir()
    txt_dir = output_root / "txt"
    txt_dir.mkdir()
    (txt_dir / "page.txt").write_text("テスト認識結果", encoding="utf-8")

    response = client.post(
        "/ocr",
        json={
            "input_root": str(input_root),
            "output_root": str(output_root),
            "job_id": job_id,
            "enable_progress": True,
            "ruby_only": True,
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["job_id"] == job_id
    assert "開始" in data["message"]

    # バックグラウンドタスク完了後、GET /result は結果を返します
    result_response = _poll_result(client, job_id, expected_status=200)
    assert result_response.status_code == 200
    result_data = result_response.json()
    assert "テスト認識結果" in result_data["text"]
    assert result_data["output_dir"] == str(output_root)

    # 進捗が completed 状態で記録されていることを確認します
    progress_response = client.get(f"/progress/{job_id}")
    assert progress_response.status_code == 200
    assert progress_response.json()["status"] == "completed"
    assert progress_response.json()["progress"] == 1.0


def test_get_result_returns_404_when_missing(client: TestClient) -> None:
    """BE009001: 存在しないジョブに対して GET /result/{job_id} は 404 を返します。"""
    response = client.get("/result/non-existent-job")
    assert response.status_code == 404
    assert "見つかりません" in response.json()["detail"]
