import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  createJob,
  uploadZip,
  runOcr,
  subscribeJobProgress,
  getPdfDownloadUrl,
  downloadPdf,
} from "../api";

const API_BASE_URL = "http://localhost:8000";

describe("api client", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("createJob", () => {
    it("ジョブ ID を返す", async () => {
      (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        new Response(JSON.stringify({ job_id: "job-123" }), { status: 200 })
      );

      const jobId = await createJob();

      expect(jobId).toBe("job-123");
      expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/jobs/`, {
        method: "POST",
        signal: expect.any(AbortSignal),
      });
    });

    it("HTTP エラー時に例外を投げる", async () => {
      (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        new Response("error", { status: 500, statusText: "Internal Server Error" })
      );

      await expect(createJob()).rejects.toThrow(
        "ジョブの作成に失敗しました: 500 Internal Server Error"
      );
    });
  });

  describe("uploadZip", () => {
    it("アップロードされた画像ファイル名の一覧を返す", async () => {
      const file = new File(["dummy"], "pages.zip", { type: "application/zip" });
      (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        new Response(JSON.stringify({ files: ["page_001.png", "page_002.png"] }), {
          status: 200,
        })
      );

      const files = await uploadZip("job-123", file);

      expect(files).toEqual(["page_001.png", "page_002.png"]);
      expect(fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/jobs/job-123/upload`,
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
          signal: expect.any(AbortSignal),
        })
      );
      const callArgs = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
      const body = callArgs[1].body as FormData;
      expect(body.get("file")).toBe(file);
    });

    it("HTTP エラー時に例外を投げる", async () => {
      const file = new File(["dummy"], "pages.zip", { type: "application/zip" });
      (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        new Response("bad request", { status: 400, statusText: "Bad Request" })
      );

      await expect(uploadZip("job-123", file)).rejects.toThrow(
        "ZIP アップロードに失敗しました: 400 Bad Request"
      );
    });
  });

  describe("runOcr", () => {
    it("OCR 結果を返す", async () => {
      const result = { pages: [{ text: "hello" }] };
      (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        new Response(JSON.stringify(result), { status: 200 })
      );

      const actual = await runOcr("job-123");

      expect(actual).toEqual(result);
      expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/jobs/job-123/ocr`, {
        method: "POST",
        signal: expect.any(AbortSignal),
      });
    });

    it("HTTP エラー時に例外を投げる", async () => {
      (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        new Response("error", { status: 500, statusText: "Internal Server Error" })
      );

      await expect(runOcr("job-123")).rejects.toThrow(
        "OCR 実行に失敗しました: 500 Internal Server Error"
      );
    });
  });

  describe("タイムアウト", () => {
    it("30 秒を超えると AbortError で失敗する", async () => {
      vi.useFakeTimers();
      (fetch as ReturnType<typeof vi.fn>).mockImplementationOnce(
        (_input: RequestInfo | URL, init?: RequestInit) => {
          return new Promise<Response>((_resolve, reject) => {
            const signal = init?.signal;
            if (!signal) {
              reject(new Error("signal is missing"));
              return;
            }
            if (signal.aborted) {
              reject(new DOMException("The operation was aborted.", "AbortError"));
              return;
            }
            signal.addEventListener("abort", () => {
              reject(new DOMException("The operation was aborted.", "AbortError"));
            });
          });
        }
      );

      const promise = createJob();
      vi.advanceTimersByTime(30_001);

      await expect(promise).rejects.toThrow("The operation was aborted.");
      vi.useRealTimers();
    });
  });


  describe("subscribeJobProgress", () => {
    let mockInstances: MockEventSource[];

    interface MockEventSource {
      url: string;
      close: ReturnType<typeof vi.fn>;
      onmessage: ((event: MessageEvent) => void) | null;
      onerror: ((error: Event) => void) | null;
      simulateMessage: (data: string) => void;
      simulateError: () => void;
    }

    beforeEach(() => {
      mockInstances = [];
      vi.stubGlobal(
        "EventSource",
        vi.fn(function (url: string) {
          const instance: MockEventSource = {
            url,
            onmessage: null,
            onerror: null,
            close: vi.fn(),
            simulateMessage(data: string) {
              if (this.onmessage) {
                this.onmessage(new MessageEvent("message", { data }));
              }
            },
            simulateError() {
              if (this.onerror) {
                this.onerror(new Event("error"));
              }
            },
          };
          mockInstances.push(instance);
          return instance;
        })
      );
    });

    afterEach(() => {
      vi.unstubAllGlobals();
    });

    it("指定したジョブのイベントエンドポイントを購読する", () => {
      const onMessage = vi.fn();
      const onError = vi.fn();
      const onComplete = vi.fn();

      subscribeJobProgress("job-123", onMessage, onError, onComplete);

      expect(mockInstances).toHaveLength(1);
      expect(mockInstances[0].url).toBe(`${API_BASE_URL}/api/jobs/job-123/events`);
    });

    it("進捗メッセージを受け取る", () => {
      const onMessage = vi.fn();
      const onError = vi.fn();
      const onComplete = vi.fn();

      subscribeJobProgress("job-123", onMessage, onError, onComplete);
      mockInstances[0].simulateMessage("50% 完了");

      expect(onMessage).toHaveBeenCalledWith("50% 完了");
      expect(onComplete).not.toHaveBeenCalled();
    });

    it("[DONE] を受け取ると完了コールバックを呼び Connection を閉じる", () => {
      const onMessage = vi.fn();
      const onError = vi.fn();
      const onComplete = vi.fn();

      subscribeJobProgress("job-123", onMessage, onError, onComplete);
      const es = mockInstances[0];
      es.simulateMessage("[DONE]");

      expect(onComplete).toHaveBeenCalledTimes(1);
      expect(es.close).toHaveBeenCalledTimes(1);
    });

    it("エラー発生時にエラーコールバックを呼び Connection を閉じる", () => {
      const onMessage = vi.fn();
      const onError = vi.fn();
      const onComplete = vi.fn();

      subscribeJobProgress("job-123", onMessage, onError, onComplete);
      const es = mockInstances[0];
      es.simulateError();

      expect(onError).toHaveBeenCalledTimes(1);
      expect(es.close).toHaveBeenCalledTimes(1);
    });
  });

  describe("getPdfDownloadUrl", () => {
    it("PDF ダウンロード URL を返す", () => {
      expect(getPdfDownloadUrl("job-123")).toBe(`${API_BASE_URL}/api/jobs/job-123/pdf`);
    });
  });

  describe("downloadPdf", () => {
    it("File System Access API 使用時に保存先ダイアログを表示し、選択先に書き込む", async () => {
      const writable = {
        write: vi.fn().mockResolvedValue(undefined),
        close: vi.fn().mockResolvedValue(undefined),
      };
      const handle = {
        createWritable: vi.fn().mockResolvedValue(writable),
      };
      const showSaveFilePickerMock = vi.fn().mockResolvedValue(handle);
      vi.stubGlobal("showSaveFilePicker", showSaveFilePickerMock);

      const blob = new Blob(["pdf"], { type: "application/pdf" });
      const response = new Response(blob, { status: 200 });
      // jsdom 以外の環境では response.body が存在するため、Blob 書き込みパスを検証するために null にします
      Object.defineProperty(response, "body", { value: null });
      (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(response);

      await downloadPdf("job-123", "result.pdf");

      expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/jobs/job-123/pdf`, {
        signal: expect.any(AbortSignal),
      });
      expect(showSaveFilePickerMock).toHaveBeenCalledWith({
        suggestedName: "result.pdf",
        types: [
          {
            description: "PDF ファイル",
            accept: { "application/pdf": [".pdf"] },
          },
        ],
      });
      expect(handle.createWritable).toHaveBeenCalledTimes(1);
      expect(writable.write).toHaveBeenCalledWith(expect.any(Blob));
      expect(writable.close).toHaveBeenCalledTimes(1);
    });

    it("保存ダイアログをキャンセルした場合はエラーを投げない", async () => {
      const abortError = new DOMException("User cancelled", "AbortError");
      const showSaveFilePickerMock = vi.fn().mockRejectedValue(abortError);
      vi.stubGlobal("showSaveFilePicker", showSaveFilePickerMock);

      const blob = new Blob(["pdf"], { type: "application/pdf" });
      (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        new Response(blob, { status: 200 })
      );

      await expect(downloadPdf("job-123", "result.pdf")).resolves.toBeUndefined();
      expect(showSaveFilePickerMock).toHaveBeenCalledTimes(1);
    });

    it("showSaveFilePicker がない環境では <a download> でフォールバックする", async () => {
      vi.stubGlobal("showSaveFilePicker", undefined);

      const createObjectURL = vi.fn(() => "blob:http://localhost/abc");
      const revokeObjectURL = vi.fn();
      vi.stubGlobal("URL", { createObjectURL, revokeObjectURL });

      const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

      const blob = new Blob(["pdf"], { type: "application/pdf" });
      (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        new Response(blob, { status: 200 })
      );

      await downloadPdf("job-123", "result.pdf");

      expect(createObjectURL).toHaveBeenCalledWith(blob);
      expect(clickSpy).toHaveBeenCalledTimes(1);
      expect(revokeObjectURL).toHaveBeenCalledWith("blob:http://localhost/abc");

      clickSpy.mockRestore();
    });

    it("HTTP エラー時に例外を投げる", async () => {
      (fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        new Response("not found", { status: 404, statusText: "Not Found" })
      );

      await expect(downloadPdf("job-123")).rejects.toThrow(
        "PDF のダウンロードに失敗しました: 404 Not Found"
      );
    });
  });
});
