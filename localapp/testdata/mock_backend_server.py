#!/usr/bin/env python3
"""localapp 結合テスト用の軽量 mock backend。

実際の backend /ocr の非同期動作を再現し、固定の PDF を即座に返す。
"""
import argparse
import json
import os
import sys
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def _parse_content_type(header_value: str) -> tuple[str, dict[str, str]]:
    """Content-Type ヘッダーをメディアタイプとパラメータに分解する。

    Python 3.13 で削除された `cgi.parse_header` の代替実装。
    `multipart/form-data; boundary=----WebKitFormBoundary...` のような値を扱う。
    """
    parts = [p.strip() for p in header_value.split(";")]
    media_type = parts[0] if parts else ""
    params: dict[str, str] = {}
    for param in parts[1:]:
        if "=" not in param:
            continue
        key, value = param.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        params[key] = value
    return media_type, params


class MockBackendHandler(BaseHTTPRequestHandler):
    """backend API の主要エンドポイントを模倣するハンドラ。"""

    pdf_path: str = "mock_backend.pdf"
    poll_count: dict[str, int] = {}
    completed_after: int = 2

    def log_message(self, fmt: str, *args) -> None:
        # テスト出力を騒がしくしないよう標準エラーにのみ簡潔に出力
        print(f"[mock-backend] {fmt % args}", file=sys.stderr)

    def _send_json(self, status: int, body: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/jobs/":
            job_id = f"mock-job-{uuid.uuid4()}"
            self.poll_count[job_id] = 0
            self._send_json(200, {"job_id": job_id})
            return

        if self.path.endswith("/upload"):
            # multipart を最低限パースし、ファイル数だけ数える
            content_type = self.headers.get("Content-Type", "")
            _, options = _parse_content_type(content_type)
            boundary = options.get("boundary", "").encode()
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)

            files = []
            if boundary:
                for part in body.split(b"--" + boundary):
                    if b'Content-Disposition:' in part and b'filename=' in part:
                        # ファイル名を抽出
                        header, _ = part.split(b"\r\n\r\n", 1)
                        disp = header.decode("utf-8", errors="ignore")
                        if "filename=\"" in disp:
                            fname = disp.split('filename="')[1].split('"')[0]
                            if fname:
                                files.append(fname)

            self._send_json(200, {"status": "uploaded", "files": files})
            return

        if self.path.endswith("/ocr"):
            self._send_json(200, {"status": "processing"})
            return

        self._send_json(404, {"error": "not found"})

    def do_GET(self) -> None:  # noqa: N802
        if "/api/jobs/" in self.path and self.path.endswith("/pdf"):
            pdf = Path(self.pdf_path)
            if not pdf.is_absolute():
                pdf = Path(__file__).parent / pdf
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Length", str(pdf.stat().st_size))
            self.end_headers()
            self.wfile.write(pdf.read_bytes())
            return

        if "/api/jobs/" in self.path:
            # /api/jobs/{job_id}
            parts = self.path.strip("/").split("/")
            if len(parts) >= 3:
                job_id = parts[2]
                count = self.poll_count.get(job_id, 0)
                self.poll_count[job_id] = count + 1
                if count >= self.completed_after:
                    self._send_json(200, {"status": "completed", "message": ""})
                else:
                    self._send_json(200, {"status": "processing", "message": ""})
                return

        self._send_json(404, {"error": "not found"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18000)
    parser.add_argument("--pdf-path", default="mock_backend.pdf")
    parser.add_argument("--completed-after", type=int, default=2)
    args = parser.parse_args()

    MockBackendHandler.pdf_path = args.pdf_path
    MockBackendHandler.completed_after = args.completed_after
    server = HTTPServer(("127.0.0.1", args.port), MockBackendHandler)
    print(f"Mock backend listening on http://127.0.0.1:{args.port}", file=sys.stderr)
    server.serve_forever()


if __name__ == "__main__":
    main()
