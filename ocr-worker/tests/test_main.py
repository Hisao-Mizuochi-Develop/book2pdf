"""ocr-worker のキャンセル・クリーンアップ・進捗 API をテストします。

SY002002: ジョブのキャンセル、進捗データの削除、キャンセル済みジョブの
結果破棄を中心に検証します。
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


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


def test_run_ocr_discards_result_when_cancelled(
    client: TestClient,
    progress_reporter: Any,
    tmp_path: Any,
) -> None:
    """キャンセル済みのジョブは /ocr 完了後に結果を破棄することを確認します。

    SY002002: 協調的キャンセルにより、OCR 処理完了後に cancelled レスポンスを
    返し、進捗ストアも cancelled 状態で更新されます。
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
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "キャンセル" in data["message"]
    assert data["text"] == ""
    assert data["output_dir"] == ""

    # 進捗が cancelled 状態で記録されていることを確認します
    progress_response = client.get(f"/progress/{job_id}")
    assert progress_response.status_code == 200
    assert progress_response.json()["status"] == "cancelled"


def test_run_ocr_completes_when_not_cancelled(
    client: TestClient,
    progress_reporter: Any,
    tmp_path: Any,
) -> None:
    """キャンセルされていないジョブは /ocr が正常完了することを確認します。"""
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
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "テスト認識結果" in data["text"]
    assert data["output_dir"] == str(output_root)

    progress_response = client.get(f"/progress/{job_id}")
    assert progress_response.status_code == 200
    assert progress_response.json()["status"] == "completed"
    assert progress_response.json()["progress"] == 1.0
