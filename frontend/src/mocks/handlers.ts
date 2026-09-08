// フロントエンドテスト用の MSW ハンドラ群です。
// backend API への HTTP リクエストをモックし、結合テストで実際の fetch レイヤーを検証します。

import { http, HttpResponse } from "msw";

/**
 * テスト用のジョブ ID です。
 */
export const MOCK_JOB_ID = "job-msw-123";

/**
 * テスト用のアップロード済み画像ファイル名一覧です。
 */
export const MOCK_FILES = ["page_001.png"];

/**
 * MSW リクエストハンドラ群です。
 */
export const handlers = [
  /**
   * ジョブ作成 API のモックです。
   */
  http.post("*/api/jobs/", () => {
    return HttpResponse.json({ job_id: MOCK_JOB_ID, status: "pending" });
  }),

  /**
   * ZIP アップロード API のモックです。
   */
  http.post(`*/api/jobs/${MOCK_JOB_ID}/upload`, () => {
    return HttpResponse.json({
      job_id: MOCK_JOB_ID,
      status: "uploaded",
      files: MOCK_FILES,
    });
  }),

  /**
   * OCR 実行 API のモックです。
   */
  http.post(`*/api/jobs/${MOCK_JOB_ID}/ocr`, () => {
    return HttpResponse.json({ text: "ocr result" });
  }),

  /**
   * PDF ダウンロード API のモックです。
   */
  http.get(`*/api/jobs/${MOCK_JOB_ID}/pdf`, () => {
    return new HttpResponse(new Blob(["pdf"], { type: "application/pdf" }), {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
      },
    });
  }),
];
