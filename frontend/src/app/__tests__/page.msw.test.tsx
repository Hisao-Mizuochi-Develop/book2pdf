import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "../page";
import { MOCK_JOB_ID } from "@/mocks/handlers";

type MockEventSource = EventSource & {
  simulateMessage: (data: string) => void;
  simulateError: () => void;
  onmessage: ((event: MessageEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
};

describe("Home page MSW integration", () => {
  const mockInstances: MockEventSource[] = [];

  beforeEach(() => {
    mockInstances.length = 0;

    // EventSource をテスト制御可能なモックに差し替えます。
    // これにより、SSE 経由で backend から送信される進捗イベントを
    // テストコードから任意のタイミングで発火できます。
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
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("ZIP アップロードから OCR 完了までの進捗を表示し、PDF ダウンロードボタンが有効になる", async () => {
    render(<Home />);

    // 1. ファイルを選択してアップロードボタンを押す
    const file = new File(["zip"], "pages.zip", { type: "application/zip" });
    await userEvent.upload(screen.getByTestId("zip-file-input"), file);
    await userEvent.click(screen.getByTestId("upload-button"));

    // 2. アップロード完了後、SSE 接続が確立される
    await waitFor(() => {
      expect(mockInstances).toHaveLength(1);
    });

    // 3. SSE 経由で processing 進捗イベントを送信する
    await act(async () => {
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: MOCK_JOB_ID,
          status: "processing",
          progress: 0.5,
          current_page: 1,
          total_pages: 1,
          message: "50% 完了",
        })
      );
    });

    await waitFor(() => {
      expect(screen.getByText("50%")).toBeInTheDocument();
      expect(screen.getByText("状態: processing")).toBeInTheDocument();
      expect(screen.getByText("1 / 1 ページ")).toBeInTheDocument();
    });

    // 4. SSE 経由で completed イベントを送信する
    await act(async () => {
      mockInstances[0].simulateMessage(
        JSON.stringify({
          job_id: MOCK_JOB_ID,
          status: "completed",
          progress: 1.0,
          current_page: 1,
          total_pages: 1,
          message: "PDF 生成が完了しました",
        })
      );
    });

    // 5. PDF ダウンロードボタンが表示される
    await waitFor(() => {
      expect(screen.getByText("PDF をダウンロード")).toBeInTheDocument();
    });
  });
});
