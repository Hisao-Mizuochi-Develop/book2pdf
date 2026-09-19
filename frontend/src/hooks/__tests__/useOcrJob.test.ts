import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useOcrJob } from "../useOcrJob";
import { runOcr, subscribeJobProgress } from "@/lib/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    runOcr: vi.fn(),
    subscribeJobProgress: vi.fn(),
  };
});

type MockEventSource = EventSource & {
  simulateMessage: (data: string) => void;
  simulateError: () => void;
  onmessage: ((event: MessageEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
};

describe("useOcrJob", () => {
  const mockInstances: MockEventSource[] = [];

  beforeEach(() => {
    mockInstances.length = 0;
    vi.stubGlobal(
      "EventSource",
      vi.fn(function (url: string) {
        const instance: MockEventSource = {
          url,
          close: vi.fn(),
          onmessage: null,
          onerror: null,
          simulateMessage(this: MockEventSource, data: string) {
            if (this.onmessage) {
              this.onmessage(new MessageEvent("message", { data }));
            }
          },
          simulateError(this: MockEventSource) {
            if (this.onerror) {
              this.onerror(new Event("error"));
            }
          },
        } as unknown as MockEventSource;
        mockInstances.push(instance);
        return instance;
      }),
    );

    vi.mocked(subscribeJobProgress).mockImplementation((jobId, onMessage, onError, onComplete) => {
      const es = new EventSource(`/api/jobs/${jobId}/events`);
      es.onmessage = (event) => {
        const data = (event as MessageEvent).data;
        if (data === "[DONE]") {
          onComplete();
          es.close();
          return;
        }
        onMessage(data);
      };
      es.onerror = (error) => {
        onError(error as Event);
        es.close();
      };
      return es;
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("初期状態では空の状態を返す", () => {
    const { result } = renderHook(() => useOcrJob());

    expect(result.current.jobId).toBeNull();
    expect(result.current.files).toEqual([]);
    expect(result.current.latestProgress).toBeNull();
    expect(result.current.progressLog).toEqual([]);
    expect(result.current.error).toBe("");
    expect(result.current.isLoading).toBe(false);
    expect(result.current.downloadableJobId).toBeNull();
  });

  it("handleUploaded がジョブ情報を設定し OCR を実行する", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      await result.current.handleUploaded("job-123", ["page_001.png"]);
    });

    expect(result.current.jobId).toBe("job-123");
    expect(result.current.files).toEqual(["page_001.png"]);
    expect(result.current.latestProgress).toBeNull();
    expect(result.current.progressLog).toContain("画像を 1 枚検出しました");
    expect(subscribeJobProgress).toHaveBeenCalledWith(
      "job-123",
      expect.any(Function),
      expect.any(Function),
      expect.any(Function),
    );
    expect(runOcr).toHaveBeenCalledWith("job-123");
    expect(result.current.error).toBe("");
    expect(result.current.downloadableJobId).toBeNull();
    expect(result.current.isLoading).toBe(true);
  });

  it("SSE 進捗イベントを受信すると latestProgress とログが更新される", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      const handlePromise = result.current.handleUploaded("job-123", ["page_001.png"]);
      await new Promise((resolve) => setTimeout(resolve, 0));
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "processing",
          progress: 0.5,
          current_page: 1,
          total_pages: 2,
          message: "50% 完了",
        }),
      );
      await handlePromise;
    });

    await waitFor(() => {
      expect(result.current.latestProgress).toEqual({
        job_id: "job-123",
        status: "processing",
        progress: 0.5,
        current_page: 1,
        total_pages: 2,
        message: "50% 完了",
      });
    });
    expect(result.current.progressLog).toContain("50% 完了");
    expect(result.current.downloadableJobId).toBeNull();
  });

  it("completed SSE イベント受信後に downloadableJobId が設定される", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      const handlePromise = result.current.handleUploaded("job-123", ["page_001.png"]);
      await new Promise((resolve) => setTimeout(resolve, 0));
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "completed",
          progress: 1.0,
          current_page: 2,
          total_pages: 2,
          message: "PDFファイル生成が完了しました",
        }),
      );
      await handlePromise;
    });

    await waitFor(() => {
      expect(result.current.latestProgress?.status).toBe("completed");
    });
    expect(result.current.downloadableJobId).toBe("job-123");
    expect(result.current.progressLog).toContain("PDFファイル生成が完了しました");
  });

  it("SSE エラー時はログに追加し EventSource を閉じる", async () => {
    vi.mocked(runOcr).mockRejectedValueOnce(new Error("OCR failed"));

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      const handlePromise = result.current.handleUploaded("job-123", ["page_001.png"]);
      await new Promise((resolve) => setTimeout(resolve, 0));
      mockInstances[0].simulateError();
      await handlePromise;
    });

    expect(result.current.progressLog).toContain("進捗通知の接続でエラーが発生しました");
    expect(mockInstances[0].close).toHaveBeenCalled();
    expect(result.current.isLoading).toBe(false);
  });

  it("OCR 実行失敗時は error が設定される", async () => {
    vi.mocked(runOcr).mockRejectedValueOnce(new Error("OCR error"));

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      await result.current.handleUploaded("job-123", ["page_001.png"]);
    });

    expect(result.current.error).toBe("OCR error");
    expect(result.current.isLoading).toBe(false);
    expect(result.current.downloadableJobId).toBeNull();
  });

  it("reset で状態が初期化される", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      await result.current.handleUploaded("job-123", ["page_001.png"]);
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.jobId).toBeNull();
    expect(result.current.files).toEqual([]);
    expect(result.current.progressLog).toEqual([]);
    expect(result.current.downloadableJobId).toBeNull();
  });

  it("アンマウント時に EventSource が閉じられる", async () => {
    vi.mocked(runOcr).mockImplementation(() => new Promise(() => {}));

    const { result, unmount } = renderHook(() => useOcrJob());

    act(() => {
      void result.current.handleUploaded("job-123", ["page_001.png"]);
    });

    await waitFor(() => {
      expect(mockInstances).toHaveLength(1);
    });

    unmount();

    expect(mockInstances[0].close).toHaveBeenCalled();
  });

  it("段階的な進捗イベント（0/3 → 1/3 → 2/3 → 3/3）がログに反映される", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      const handlePromise = result.current.handleUploaded("job-123", [
        "page_001.png",
        "page_002.png",
        "page_003.png",
      ]);
      await new Promise((resolve) => setTimeout(resolve, 0));

      const messages = [
        { current_page: 0, message: "OCR 0/3" },
        { current_page: 1, message: "OCR 1/3" },
        { current_page: 2, message: "OCR 2/3" },
        { current_page: 3, message: "OCR 3/3" },
      ];
      for (const item of messages) {
        mockInstances[0].simulateMessage(
          JSON.stringify({
            job_id: "job-123",
            status: "processing",
            progress: item.current_page / 3,
            current_page: item.current_page,
            total_pages: 3,
            message: item.message,
          }),
        );
      }

      await handlePromise;
    });

    await waitFor(() => {
      expect(result.current.latestProgress).toEqual(
        expect.objectContaining({
          job_id: "job-123",
          status: "processing",
          progress: 1,
          current_page: 3,
          total_pages: 3,
          message: "OCR 3/3",
        }),
      );
    });

    expect(result.current.progressLog).toEqual(
      expect.arrayContaining([
        expect.stringContaining("OCR 0/3"),
        expect.stringContaining("OCR 1/3"),
        expect.stringContaining("OCR 2/3"),
        expect.stringContaining("OCR 3/3"),
      ]),
    );
  });

  it("handleCancel は進行中のジョブをキャンセルし状態を更新する", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(null, { status: 204 }));

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      await result.current.handleUploaded("job-123", ["page_001.png"]);
    });

    await act(async () => {
      await result.current.handleCancel();
    });

    expect(fetchSpy).toHaveBeenCalledWith(
      "http://localhost:8000/api/jobs/job-123",
      expect.objectContaining({ method: "DELETE" }),
    );
    expect(result.current.latestProgress).toEqual(
      expect.objectContaining({
        job_id: "job-123",
        status: "cancelled",
        progress: 0,
      }),
    );
    expect(result.current.progressLog).toContain("ジョブをキャンセルしました");
    expect(result.current.downloadableJobId).toBeNull();
    expect(result.current.isLoading).toBe(false);

    fetchSpy.mockRestore();
  });

  it("handleCancel は jobId がない場合に何もしない", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(null, { status: 204 }));

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      await result.current.handleCancel();
    });

    expect(fetchSpy).not.toHaveBeenCalled();

    fetchSpy.mockRestore();
  });

  it("handleCancel が失敗した場合は error にメッセージを設定する", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new Error("cancel failed"));

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      await result.current.handleUploaded("job-123", ["page_001.png"]);
    });

    await act(async () => {
      await result.current.handleCancel();
    });

    expect(result.current.error).toBe("cancel failed");
    expect(result.current.progressLog).toContain("キャンセルに失敗しました: cancel failed");
    expect(result.current.isLoading).toBe(false);

    fetchSpy.mockRestore();
  });

  it("handleUploaded でアップロードタイミングを受け取ると zipUpload と overall が記録される", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);
    const uploadTiming = {
      uploadStart: "2026-09-15T10:00:00.000Z",
      uploadEnd: "2026-09-15T10:00:01.500Z",
      elapsedMs: 1500,
    };

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      await result.current.handleUploaded("job-123", ["page_001.png"], uploadTiming);
    });

    expect(result.current.timingDebug.zipUpload).toEqual({
      start: uploadTiming.uploadStart,
      end: uploadTiming.uploadEnd,
      elapsedMs: uploadTiming.elapsedMs,
    });
    expect(result.current.timingDebug.overall.start).toBe(uploadTiming.uploadStart);
    expect(result.current.timingDebug.overall.end).toBeNull();
    expect(result.current.timingDebug.ocrPages).toHaveLength(1);
    expect(result.current.timingDebug.ocrPages[0]).toMatchObject({
      pageIndex: 0,
      fileName: "page_001.png",
      start: null,
      end: null,
      elapsedMs: null,
    });
  });

  it("OCR 進捗イベントでページ単位のタイミングが追跡される", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);
    const uploadTiming = {
      uploadStart: "2026-09-15T10:00:00.000Z",
      uploadEnd: "2026-09-15T10:00:01.000Z",
      elapsedMs: 1000,
    };

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      const handlePromise = result.current.handleUploaded(
        "job-123",
        ["page_001.png", "page_002.png", "page_003.png"],
        uploadTiming,
      );
      await new Promise((resolve) => setTimeout(resolve, 0));
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "processing",
          progress: 0.33,
          current_page: 1,
          total_pages: 3,
          message: "OCR処理中です（1/3）",
          ocrPages: [
            { pageIndex: 0, fileName: "page_001.png", start: "2026-09-16T12:00:00Z", end: "2026-09-16T12:00:01Z", elapsedMs: 1000 },
            { pageIndex: 1, fileName: "page_002.png", start: "2026-09-16T12:00:01Z", end: null, elapsedMs: null },
            { pageIndex: 2, fileName: "page_003.png", start: null, end: null, elapsedMs: null },
          ],
        }),
      );
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "processing",
          progress: 0.66,
          current_page: 2,
          total_pages: 3,
          message: "OCR処理中です（2/3）",
          ocrPages: [
            { pageIndex: 0, fileName: "page_001.png", start: "2026-09-16T12:00:00Z", end: "2026-09-16T12:00:01Z", elapsedMs: 1000 },
            { pageIndex: 1, fileName: "page_002.png", start: "2026-09-16T12:00:01Z", end: null, elapsedMs: null },
            { pageIndex: 2, fileName: "page_003.png", start: null, end: null, elapsedMs: null },
          ],
        }),
      );
      await handlePromise;
    });

    await waitFor(() => {
      expect(result.current.timingDebug.ocrPages).toHaveLength(3);
    });

    const firstPage = result.current.timingDebug.ocrPages[0];
    expect(firstPage.start).toBe("2026-09-16T12:00:00Z");
    expect(firstPage.end).toBe("2026-09-16T12:00:01Z");
    expect(firstPage.elapsedMs).toBe(1000);

    const secondPage = result.current.timingDebug.ocrPages[1];
    expect(secondPage.start).toBe("2026-09-16T12:00:01Z");
    expect(secondPage.end).toBeNull();
  });

  it("ocrPages ペイロードからページ単位のタイミングがそのまま追跡される", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);
    const uploadTiming = {
      uploadStart: "2026-09-15T10:00:00.000Z",
      uploadEnd: "2026-09-15T10:00:01.000Z",
      elapsedMs: 1000,
    };

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      const handlePromise = result.current.handleUploaded(
        "job-123",
        ["page_001.png", "page_002.png", "page_003.png"],
        uploadTiming,
      );
      await new Promise((resolve) => setTimeout(resolve, 0));
      // プロキシ/中継層で半角括弧に正規化されるケースをシミュレートします
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "processing",
          progress: 0.33,
          current_page: 0,
          total_pages: 3,
          message: "OCR処理中です(1/3)",
          ocrPages: [
            { pageIndex: 0, fileName: "page_001.png", start: "2026-09-16T12:00:00Z", end: "2026-09-16T12:00:01Z", elapsedMs: 1000 },
            { pageIndex: 1, fileName: "page_002.png", start: "2026-09-16T12:00:01Z", end: null, elapsedMs: null },
            { pageIndex: 2, fileName: "page_003.png", start: null, end: null, elapsedMs: null },
          ],
        }),
      );
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "processing",
          progress: 0.66,
          current_page: 1,
          total_pages: 3,
          message: "OCR処理中です(2/3)",
          ocrPages: [
            { pageIndex: 0, fileName: "page_001.png", start: "2026-09-16T12:00:00Z", end: "2026-09-16T12:00:01Z", elapsedMs: 1000 },
            { pageIndex: 1, fileName: "page_002.png", start: "2026-09-16T12:00:01Z", end: null, elapsedMs: null },
            { pageIndex: 2, fileName: "page_003.png", start: null, end: null, elapsedMs: null },
          ],
        }),
      );
      await handlePromise;
    });

    await waitFor(() => {
      expect(result.current.timingDebug.ocrPages).toHaveLength(3);
    });

    const firstPage = result.current.timingDebug.ocrPages[0];
    expect(firstPage.start).toBe("2026-09-16T12:00:00Z");
    expect(firstPage.end).toBe("2026-09-16T12:00:01Z");
    expect(firstPage.elapsedMs).toBe(1000);

    const secondPage = result.current.timingDebug.ocrPages[1];
    expect(secondPage.start).toBe("2026-09-16T12:00:01Z");
    expect(secondPage.end).toBeNull();
  });

  it("PDF 生成開始と完了が検出される", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      const handlePromise = result.current.handleUploaded("job-123", ["page_001.png"]);
      await new Promise((resolve) => setTimeout(resolve, 0));
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "processing",
          progress: 0.8,
          current_page: 1,
          total_pages: 1,
          message: "PDF生成中です",
        }),
      );
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "completed",
          progress: 1,
          current_page: 1,
          total_pages: 1,
          message: "OCR 処理が完了しました",
        }),
      );
      await handlePromise;
    });

    await waitFor(() => {
      expect(result.current.timingDebug.pdfGeneration.start).not.toBeNull();
    });

    expect(result.current.timingDebug.pdfGeneration.end).not.toBeNull();
    expect(result.current.timingDebug.pdfGeneration.elapsedMs).toBeGreaterThanOrEqual(0);
    expect(result.current.timingDebug.overall.end).not.toBeNull();
    expect(result.current.timingDebug.overall.elapsedMs).toBeGreaterThanOrEqual(0);
  });

  it("reset でタイミング情報が初期化される", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);
    const uploadTiming = {
      uploadStart: "2026-09-15T10:00:00.000Z",
      uploadEnd: "2026-09-15T10:00:01.000Z",
      elapsedMs: 1000,
    };

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      await result.current.handleUploaded("job-123", ["page_001.png"], uploadTiming);
    });

    expect(result.current.timingDebug.zipUpload.start).not.toBeNull();

    act(() => {
      result.current.reset();
    });

    expect(result.current.timingDebug.zipUpload).toEqual({
      start: null,
      end: null,
      elapsedMs: null,
    });
    expect(result.current.timingDebug.ocrTotal).toEqual({
      start: null,
      end: null,
      elapsedMs: null,
    });
    expect(result.current.timingDebug.ocrPages).toEqual([]);
    expect(result.current.timingDebug.overall).toEqual({
      start: null,
      end: null,
      elapsedMs: null,
    });
  });

  it("completed 後に processing イベントが来ると overall.end がクリアされる（FE002003 回帰修正）", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      const handlePromise = result.current.handleUploaded("job-123", ["page_001.png"]);
      await new Promise((resolve) => setTimeout(resolve, 0));
      // 完了イベントを送信します
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "completed",
          progress: 1,
          current_page: 1,
          total_pages: 1,
          message: "OCR 処理が完了しました",
        }),
      );
      // ポーリング遅延などで後続の processing イベントが届くケースをシミュレートします
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "processing",
          progress: 0.5,
          current_page: 0,
          total_pages: 1,
          message: "OCR処理中です（1/1）",
        }),
      );
      await handlePromise;
    });

    // processing イベントを受信したため、overall.end はクリアされています。
    expect(result.current.timingDebug.overall.end).toBeNull();
    expect(result.current.timingDebug.overall.elapsedMs).toBeNull();
  });

  it("初回 processing イベントで ocrTotal.start と ocrPages[0].start が ocrPages ペイロードから設定される（SY002003 UAT バグ回帰修正）", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      const handlePromise = result.current.handleUploaded("job-123", ["page_001.png"]);
      await new Promise((resolve) => setTimeout(resolve, 0));
      // ocr-worker はページ処理開始前に current_page = page_idx - 1 を送信する
      // backend 経由で ocrPages も一緒に送信される
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "processing",
          progress: 0.1,
          current_page: 0,
          total_pages: 1,
          message: "OCR処理中です（1/1）",
          timestamp: "2026-09-16T12:00:00.000Z",
          ocrPages: [
            { pageIndex: 0, fileName: "page_001.png", start: "2026-09-16T12:00:00Z", end: null, elapsedMs: null },
          ],
        }),
      );
      await handlePromise;
    });

    // ocrTotal.start が timestamp から設定されること
    expect(result.current.timingDebug.ocrTotal.start).toBe("2026-09-16T12:00:00.000Z");
    // backend から送られた ocrPages の start がそのまま反映されること
    expect(result.current.timingDebug.ocrPages[0].start).toBe("2026-09-16T12:00:00Z");
    expect(result.current.timingDebug.ocrPages[0].elapsedMs).toBeNull();
  });
});
