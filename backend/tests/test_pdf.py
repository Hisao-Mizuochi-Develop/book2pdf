"""検索可能 PDF 生成とダウンロード API のテストです。

このファイルでは、OCR 結果の XML 解析、検索可能 PDF の生成、
および PDF ダウンロードエンドポイントに対するテストを提供します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
from __future__ import annotations

# メモリ上のバイナリストリームを扱うための標準ライブラリです
import io

# 一時ディレクトリを作成するための標準ライブラリです
import tempfile

# ZIP ファイルを作成するための標準ライブラリです
import zipfile

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
from pathlib import Path

# pytest の fixture や型ヒント用です
import pytest

# FastAPI のテスト用 HTTP クライアントです
from fastapi.testclient import TestClient

# PyMuPDF: 生成された PDF を検証するために使用します
import fitz

# 異体字を正規字体に統一するための標準ライブラリです
# PDF から抽出したテキストも正規化して比較します
import unicodedata

# テスト対象の FastAPI アプリケーションを読み込みます
from app.main import app

# モック OCR エンジンを読み込みます
from app.services.ocr_engine import MockOcrEngine

# OCR 結果の XML 解析サービスを読み込みます
from app.services.xml_parser import find_sorted_xml, parse_sorted_xml

# 検索可能 PDF 生成サービスを読み込みます
from app.services.pdf_generator import (
    _xml_to_pdf_y,
    generate_searchable_pdf,
)


# FastAPI のテストクライアントを作成します
@pytest.fixture
def client() -> TestClient:
    """テスト用の HTTP クライアントを提供します。"""
    return TestClient(app)


# 実際の OCR エンジンをモックに置き換えるための fixture です
@pytest.fixture(autouse=True)
def mock_ocr_engine_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    """OCR エンジンをモックに置き換えます。"""
    monkeypatch.setattr(
        "app.routers.jobs.create_ocr_engine",
        lambda use_mock=False: MockOcrEngine(),
    )


def create_test_zip_buffer(filenames: list[str]) -> io.BytesIO:
    """テスト用の ZIP ファイルをメモリ上に作成します。

    Args:
        filenames: ZIP に含めるファイル名の一覧

    Returns:
        メモリ上の ZIP ファイルバッファ
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in filenames:
            zf.writestr(filename, b"dummy image data")
    buffer.seek(0)
    return buffer


def create_sorted_xml(output_dir: Path, image_name: str, text: str) -> Path:
    """OCR 結果の .sorted.xml ファイルを作成します。

    Args:
        output_dir: OCR 結果のルートディレクトリ
        image_name: ページ画像のファイル名
        text: ページに含める認識テキスト

    Returns:
        作成された XML ファイルのパス
    """
    # XML ファイルを格納するディレクトリを作成します
    xml_dir = output_dir / "xml"
    xml_dir.mkdir(parents=True, exist_ok=True)

    # XML ファイルのパスを作成します
    xml_path = xml_dir / f"{image_name}.sorted.xml"

    # シンプルな XML 内容を作成します
    xml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<OCRDATASET>\n'
        f'  <PAGE HEIGHT="842" WIDTH="595" IMAGENAME="{image_name}">\n'
        f'    <LINE TYPE="テキスト" X="50" Y="100" WIDTH="400" HEIGHT="20" STRING="{text}" ORDER="1" />\n'
        '  </PAGE>\n'
        '</OCRDATASET>\n'
    )

    # XML ファイルを書き込みます
    xml_path.write_text(xml_content, encoding="utf-8")
    return xml_path


def test_parse_sorted_xml() -> None:
    """XML 解析サービスが .sorted.xml を正しく解析できることを確認します。"""
    # 一時ディレクトリを作成します
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "output"
        xml_path = create_sorted_xml(
            output_dir,
            image_name="page1.png",
            text="テストテキスト",
        )

        # XML ファイルを解析します
        pages = parse_sorted_xml(xml_path)

        # 1 ページ解析されていることを確認します
        assert len(pages) == 1

        # ページ情報を確認します
        page = pages[0]
        assert page.image_name == "page1.png"
        assert page.width == 595
        assert page.height == 842

        # テキスト行情報を確認します
        assert len(page.lines) == 1
        line = page.lines[0]
        assert line.text == "テストテキスト"
        assert line.x == 50
        assert line.y == 100
        assert line.width == 400
        assert line.height == 20


def test_find_sorted_xml() -> None:
    """OCR 出力ディレクトリから .sorted.xml が見つかることを確認します。"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "output"
        create_sorted_xml(
            output_dir,
            image_name="page1.png",
            text="テスト",
        )

        # XML ファイルを検索します
        found = find_sorted_xml(output_dir)

        # XML ファイルが見つかっていることを確認します
        assert found is not None
        assert found.name == "page1.png.sorted.xml"


def test_generate_searchable_pdf() -> None:
    """検索可能 PDF が生成され、テキストを含むことを確認します。"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "output"
        extract_dir = Path(tmp_dir) / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)

        # ダミーの画像ファイルを作成します（中身は空でも構いません）
        (extract_dir / "page1.png").write_bytes(b"dummy image data")

        # XML ファイルを作成します
        create_sorted_xml(
            output_dir,
            image_name="page1.png",
            text="検索可能PDF",
        )

        # PDF 出力用の一時ディレクトリを設定します
        pdf_output_dir = Path(tmp_dir) / "pdfs"
        import os
        os.environ["PDF_OUTPUT_DIR"] = str(pdf_output_dir)

        # PDF を生成します
        pdf_path = generate_searchable_pdf(
            job_id="test-job",
            output_dir=output_dir,
            extract_dir=extract_dir,
        )

        # PDF ファイルが生成されていることを確認します
        assert pdf_path.exists()

        # PyMuPDF で PDF を開いてテキストを抽出します
        doc = fitz.open(str(pdf_path))
        try:
            assert len(doc) == 1
            page = doc[0]
            extracted_text = page.get_text()
            assert "検索可能PDF" in extracted_text
        finally:
            doc.close()


def test_generate_searchable_pdf_normalizes_variant_characters() -> None:
    """異体字が正規字体に正規化されて PDF に埋め込まれることを確認します。

    ndlocr_cli は旧字体・異体字を認識することがあり、
    そのまま PDF に埋め込むとテキスト検索時にヒットしません。
    本実装では NFKC 正規化を適用し、異体字を正規字体に統一します。
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "output"
        extract_dir = Path(tmp_dir) / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)

        # ダミーの画像ファイルを作成します
        (extract_dir / "page1.png").write_bytes(b"dummy image data")

        # XML に異体字「索」（U+F92A）を含めます
        # 正規字体は「索」（U+7D22）です
        variant_text = "図書館の探\uf92a"
        create_sorted_xml(
            output_dir,
            image_name="page1.png",
            text=variant_text,
        )

        # PDF 出力用の一時ディレクトリを設定します
        pdf_output_dir = Path(tmp_dir) / "pdfs"
        import os
        os.environ["PDF_OUTPUT_DIR"] = str(pdf_output_dir)

        # PDF を生成します
        pdf_path = generate_searchable_pdf(
            job_id="test-variant-job",
            output_dir=output_dir,
            extract_dir=extract_dir,
        )

        # PDF ファイルが生成されていることを確認します
        assert pdf_path.exists()

        # PyMuPDF で PDF を開いてテキストを抽出します
        doc = fitz.open(str(pdf_path))
        try:
            assert len(doc) == 1
            page = doc[0]
            extracted_text = page.get_text()
            # 抽出テキストを NFKC 正規化して正規字体で比較します
            normalized_extracted = unicodedata.normalize("NFKC", extracted_text)
            assert "図書館の探索" in normalized_extracted
            # 異体字そのものは含まれていないことを確認します
            assert "\uf92a" not in normalized_extracted
        finally:
            doc.close()


def test_download_pdf(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """OCR 完了後に PDF ダウンロード API で PDF を取得できることを確認します。"""
    # ジョブを作成します
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # 画像ファイルを含む ZIP をアップロードします
    zip_buffer = create_test_zip_buffer(["page1.png"])
    response = client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )
    assert response.status_code == 200

    # OCR 実行後に XML を作成する処理を差し込んだモックエンジンを返すようにします
    original_run = MockOcrEngine.run

    def patched_run(self, image_files, work_dir, job_id=None):
        result = original_run(self, image_files, work_dir, job_id)
        # MockOcrEngine が作成した output ディレクトリに XML を作成します
        create_sorted_xml(
            result.output_dir,
            image_name="page1.png",
            text="ダウンロードテスト",
        )
        return result

    class PatchedMockOcrEngine(MockOcrEngine):
        """OCR 実行後に XML を作成するモックエンジンです。"""

        def run(self, image_files, work_dir, job_id=None):
            return patched_run(self, image_files, work_dir, job_id)

    monkeypatch.setattr(
        "app.routers.jobs.create_ocr_engine",
        lambda use_mock=False: PatchedMockOcrEngine(),
    )

    # OCR を実行します（この中で PDF 生成も行われます）
    response = client.post(f"/api/jobs/{job_id}/ocr")
    assert response.status_code == 200

    # PDF ダウンロード API を呼び出します
    response = client.get(f"/api/jobs/{job_id}/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # PDF ダウンロード時のファイル名は {job_id}_YYYYMMDD_HHMMSS.pdf の形式です
    content_disposition = response.headers["content-disposition"]
    assert f'filename="{job_id}_' in content_disposition
    assert content_disposition.endswith('.pdf"')

    # ダウンロードした内容が PDF 形式であることを確認します
    content = response.content
    assert content.startswith(b"%PDF")


def test_download_pdf_job_not_found(client: TestClient) -> None:
    """存在しないジョブ ID で PDF ダウンロードすると 404 エラーになることを確認します。"""
    response = client.get("/api/jobs/00000000-0000-0000-0000-000000000000/pdf")
    assert response.status_code == 404


def test_download_pdf_before_completion(client: TestClient) -> None:
    """OCR 完了前に PDF ダウンロードすると 400 エラーになることを確認します。"""
    # ジョブを作成して ZIP をアップロードします（OCR は実行しません）
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    zip_buffer = create_test_zip_buffer(["page1.png"])
    response = client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )
    assert response.status_code == 200

    # OCR 完了前に PDF ダウンロードを試みます
    response = client.get(f"/api/jobs/{job_id}/pdf")
    assert response.status_code == 400


def test_download_pdf_not_generated(client: TestClient) -> None:
    """PDF が生成されていない状態でダウンロードすると 400 エラーになることを確認します。"""
    # ジョブを作成して ZIP をアップロードします
    response = client.post("/api/jobs/")
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    zip_buffer = create_test_zip_buffer(["page1.png"])
    response = client.post(
        f"/api/jobs/{job_id}/upload",
        files={"file": ("images.zip", zip_buffer, "application/zip")},
    )
    assert response.status_code == 200

    # OCR を実行します（MockOcrEngine は XML を作成しないため PDF 生成は失敗します）
    response = client.post(f"/api/jobs/{job_id}/ocr")
    assert response.status_code == 200

    # PDF が生成されていないため 400 エラーになります
    response = client.get(f"/api/jobs/{job_id}/pdf")
    assert response.status_code == 400


def test_xml_to_pdf_y_bottom_position() -> None:
    """XML の Y=xml_height が PDF のページ下端に相当することを確認します。"""
    # XML の Y=xml_height はページ下端を表す
    # PDF 座標系でも下端が y=pdf_height 付近になる
    # baseline 補正（font_size 分下げる）を考慮すると、
    # pdf_y = pdf_height + font_size となる
    pdf_y = _xml_to_pdf_y(
        xml_y=842.0,
        xml_height=842.0,
        pdf_height=842.0,
        font_size=12.0,
    )
    assert pdf_y == 842.0 + 12.0


def test_xml_to_pdf_y_top_position() -> None:
    """XML の Y=0 が PDF のページ上端に相当することを確認します。"""
    # XML の Y=0 はページ上端を表す
    # PDF 座標系では上端に近いほど y 値が大きくなる
    # baseline 補正（font_size 分下げる）を考慮すると、
    # pdf_y = font_size となる
    pdf_y = _xml_to_pdf_y(
        xml_y=0.0,
        xml_height=842.0,
        pdf_height=842.0,
        font_size=12.0,
    )
    assert pdf_y == 12.0


def test_xml_to_pdf_y_with_scaling() -> None:
    """XML と PDF の高さが異なる場合のスケーリングを確認します。"""
    # XML 高さ 1000、PDF 高さ 500 の場合、scale_y = 0.5
    # XML の Y=100 は PDF 上で下端から 50 の位置に相当
    # baseline 補正（font_size=10）を足すと pdf_y = 50 + 10 = 60
    pdf_y = _xml_to_pdf_y(
        xml_y=100.0,
        xml_height=1000.0,
        pdf_height=500.0,
        font_size=10.0,
    )
    assert pdf_y == 60.0
