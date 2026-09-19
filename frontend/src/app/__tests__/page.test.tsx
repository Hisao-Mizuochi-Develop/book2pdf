import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "../page";
import { useOcrJob } from "@/hooks/useOcrJob";
import { downloadPdf } from "@/lib/api";

vi.mock("@/hooks/useOcrJob");
vi.mock("@/lib/api");

const defaultTimingDebug = {
  zipUpload: { start: null, end: null, elapsedMs: null },
  ocrTotal: { start: null, end: null, elapsedMs: null },
  ocrPages: [] as { pageIndex: number; fileName: string; start: string | null; end: string | null; elapsedMs: number | null }[],
  pdfGeneration: { start: null, end: null, elapsedMs: null },
  overall: { start: null, end: null, elapsedMs: null },
};

describe("Home page", () => {
  const mockHandleUploaded = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useOcrJob).mockReturnValue({
      jobId: null,
      files: [],
      latestProgress: null,
      progressLog: [],
      error: "",
      isLoading: false,
      downloadableJobId: null,
      timingDebug: defaultTimingDebug,
      handleUploaded: mockHandleUploaded,
      handleCancel: vi.fn(),
      reset: vi.fn(),
    });
  });

  it("ZIP アップロードフォームが表示される", () => {
    render(<Home />);
    expect(screen.getByText("book2pdf")).toBeInTheDocument();
    expect(screen.getByText("ZIP アップロード")).toBeInTheDocument();
    expect(screen.getByTestId("zip-file-input")).toBeInTheDocument();
  });

  it("アップロード完了後に進捗とダウンロードボタンが表示される", () => {
    vi.mocked(useOcrJob).mockReturnValue({
      jobId: "job-123",
      files: ["page_001.png", "page_002.png"],
      latestProgress: {
        job_id: "job-123",
        status: "processing",
        progress: 0.5,
        current_page: 1,
        total_pages: 2,
      },
      progressLog: ["ジョブを作成しました: job-123", "50% 完了"],
      error: "",
      isLoading: false,
      downloadableJobId: "job-123",
      timingDebug: defaultTimingDebug,
      handleUploaded: mockHandleUploaded,
      handleCancel: vi.fn(),
      reset: vi.fn(),
    });
    render(<Home />);
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByText("PDFをダウンロード")).toBeInTheDocument();
    expect(screen.getByTestId("download-button")).toBeDisabled();
  });

  it("OCR エラー時に進捗パネル内のエラー表示エリアにメッセージが表示される", () => {
    vi.mocked(useOcrJob).mockReturnValue({
      jobId: "job-123",
      files: [],
      latestProgress: null,
      progressLog: [],
      error: "OCR 処理に失敗しました",
      isLoading: false,
      downloadableJobId: null,
      timingDebug: defaultTimingDebug,
      handleUploaded: mockHandleUploaded,
      handleCancel: vi.fn(),
      reset: vi.fn(),
    });
    render(<Home />);
    const errorLine = screen.getByTestId("progress-error-line");
    expect(errorLine).toHaveTextContent("OCR 処理に失敗しました");
  });

  it("PDF ダウンロードボタンを押すと showSaveFilePicker と downloadPdf が呼ばれる", async () => {
    const handle = { createWritable: vi.fn() };
    const showSaveFilePickerMock = vi.fn().mockResolvedValue(handle);
    vi.stubGlobal("showSaveFilePicker", showSaveFilePickerMock);
    vi.mocked(downloadPdf).mockResolvedValue(undefined);
    const mockReset = vi.fn();
    vi.mocked(useOcrJob).mockReturnValue({
      jobId: "job-123",
      files: [],
      latestProgress: {
        job_id: "job-123",
        status: "completed",
        progress: 1.0,
        current_page: 1,
        total_pages: 1,
      },
      progressLog: [],
      error: "",
      isLoading: false,
      downloadableJobId: "job-123",
      timingDebug: defaultTimingDebug,
      handleUploaded: mockHandleUploaded,
      handleCancel: vi.fn(),
      reset: mockReset,
    });
    render(<Home />);
    await userEvent.click(screen.getByText("PDFをダウンロード"));
    expect(showSaveFilePickerMock).toHaveBeenCalledTimes(1);
    expect(showSaveFilePickerMock).toHaveBeenCalledWith({
      suggestedName: "job-123.pdf",
      types: [{ description: "PDF ファイル", accept: { "application/pdf": [".pdf"] } }],
    });
    expect(downloadPdf).toHaveBeenCalledWith("job-123", undefined, handle);
    expect(mockReset).toHaveBeenCalledTimes(1);
  });

  it("処理中に進捗パネルにキャンセルボタンが表示され、クリックすると handleCancel が呼ばれる", async () => {
    const mockHandleCancel = vi.fn();
    vi.mocked(useOcrJob).mockReturnValue({
      jobId: "job-123",
      files: ["page_001.png"],
      latestProgress: {
        job_id: "job-123",
        status: "processing",
        progress: 0.5,
        current_page: 1,
        total_pages: 2,
        message: "OCR 処理中",
      },
      progressLog: [],
      error: "",
      isLoading: true,
      downloadableJobId: null,
      timingDebug: defaultTimingDebug,
      handleUploaded: mockHandleUploaded,
      handleCancel: mockHandleCancel,
      reset: vi.fn(),
    });
    render(<Home />);
    const cancelButton = screen.getByTestId("cancel-button");
    expect(cancelButton).toBeInTheDocument();
    expect(cancelButton).toHaveTextContent("処理をキャンセル");
    await userEvent.click(cancelButton);
    expect(mockHandleCancel).toHaveBeenCalledTimes(1);
  });
});