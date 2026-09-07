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
    expect(result.current.result).toBe("");
    expect(result.current.error).toBe("");
    expect(result.current.isLoading).toBe(false);
    expect(result.current.downloadableJobId).toBeNull();
  });

  it("handleUploaded がジョブ情報を設定し OCR を実行する", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce({ text: "ocr result" });

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      await result.current.handleUploaded("job-123", ["page_001.png"]);
    });

    expect(result.current.jobId).toBe("job-123");
    expect(result.current.files).toEqual(["page_001.png"]);
    expect(result.current.progressLog).toContain("ジョブを作成しました: job-123");
    expect(result.current.progressLog).toContain("画像を 1 枚検出しました");
    expect(subscribeJobProgress).toHaveBeenCalledWith(
      "job-123",
      expect.any(Function),
      expect.any(Function),
      expect.any(Function),
    );
    expect(runOcr).toHaveBeenCalledWith("job-123");
    expect(result.current.result).toBe(JSON.stringify({ text: "ocr result" }, null, 2));
    expect(result.current.downloadableJobId).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it("SSE 進捗イベントを受信すると latestProgress とログが更新される", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce({ text: "done" });

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      const handlePromise = result.current.handleUploaded("job-123", ["page_001.png"]);
      await new Promise((resolve) => setTimeout(resolve, 0));
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "processing",
          progress: 50,
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
        progress: 50,
        current_page: 1,
        total_pages: 2,
        message: "50% 完了",
      });
    });
    expect(result.current.progressLog).toContain("50% 完了");
    expect(result.current.downloadableJobId).toBeNull();
  });

  it("completed SSE イベント受信後に downloadableJobId が設定される", async () => {
    vi.mocked(runOcr).mockResolvedValueOnce({ text: "done" });

    const { result } = renderHook(() => useOcrJob());

    await act(async () => {
      const handlePromise = result.current.handleUploaded("job-123", ["page_001.png"]);
      await new Promise((resolve) => setTimeout(resolve, 0));
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: "job-123",
          status: "completed",
          progress: 100,
          current_page: 2,
          total_pages: 2,
          message: "PDF 生成が完了しました",
        }),
      );
      await handlePromise;
    });

    await waitFor(() => {
      expect(result.current.latestProgress?.status).toBe("completed");
    });
    expect(result.current.downloadableJobId).toBe("job-123");
    expect(result.current.progressLog).toContain("PDF 生成が完了しました");
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
    vi.mocked(runOcr).mockResolvedValueOnce({ text: "done" });

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
    expect(result.current.result).toBe("");
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
});
