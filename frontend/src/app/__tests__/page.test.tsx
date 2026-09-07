import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "../page";
import { useOcrJob } from "@/hooks/useOcrJob";

vi.mock("@/hooks/useOcrJob");

describe("Home page", () => {
  const mockHandleUploaded = vi.fn();
  const mockDownload = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useOcrJob).mockReturnValue({
      jobId: null,
      files: [],
      latestProgress: null,
      progressLog: [],
      result: "",
      error: "",
      isLoading: false,
      downloadableJobId: null,
      handleUploaded: mockHandleUploaded,
      reset: vi.fn(),
      download: mockDownload,
    });
  });

  it("ZIP アップロードフォームが表示される", () => {
    render(<Home />);

    expect(screen.getByText("book2pdf")).toBeInTheDocument();
    expect(screen.getByText("ZIP アップロード")).toBeInTheDocument();
    expect(screen.getByTestId("zip-file-input")).toBeInTheDocument();
  });

  it("アップロード完了後にジョブ情報と進捗が表示される", () => {
    vi.mocked(useOcrJob).mockReturnValue({
      jobId: "job-123",
      files: ["page_001.png", "page_002.png"],
      latestProgress: {
        job_id: "job-123",
        status: "processing",
        progress: 50,
        current_page: 1,
        total_pages: 2,
      },
      progressLog: ["ジョブを作成しました: job-123", "50% 完了"],
      result: JSON.stringify({ text: "ocr result" }, null, 2),
      error: "",
      isLoading: false,
      downloadableJobId: "job-123",
      handleUploaded: mockHandleUploaded,
      reset: vi.fn(),
      download: mockDownload,
    });

    render(<Home />);

    expect(screen.getByText("ジョブ ID: job-123")).toBeInTheDocument();
    expect(screen.getByText("page_001.png")).toBeInTheDocument();
    expect(screen.getByText("page_002.png")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByText(/ocr result/)).toBeInTheDocument();
    expect(screen.getByText("PDF をダウンロード")).toBeInTheDocument();
  });

  it("OCR エラー時にエラーメッセージが表示される", () => {
    vi.mocked(useOcrJob).mockReturnValue({
      jobId: "job-123",
      files: [],
      latestProgress: null,
      progressLog: [],
      result: "",
      error: "OCR 処理に失敗しました",
      isLoading: false,
      downloadableJobId: null,
      handleUploaded: mockHandleUploaded,
      reset: vi.fn(),
      download: mockDownload,
    });

    render(<Home />);

    expect(screen.getByText("OCR 処理に失敗しました")).toBeInTheDocument();
  });

  it("PDF ダウンロードボタンを押すと download が呼ばれる", async () => {
    vi.mocked(useOcrJob).mockReturnValue({
      jobId: "job-123",
      files: [],
      latestProgress: null,
      progressLog: [],
      result: "",
      error: "",
      isLoading: false,
      downloadableJobId: "job-123",
      handleUploaded: mockHandleUploaded,
      reset: vi.fn(),
      download: mockDownload,
    });

    render(<Home />);

    await userEvent.click(screen.getByText("PDF をダウンロード"));

    expect(mockDownload).toHaveBeenCalledTimes(1);
  });
});
