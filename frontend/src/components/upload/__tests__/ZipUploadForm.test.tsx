import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ZipUploadForm } from "../ZipUploadForm";
import { createJob, uploadZip } from "@/lib/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    createJob: vi.fn(),
    uploadZip: vi.fn(),
  };
});

describe("ZipUploadForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("初期状態ではアップロードボタンが無効化されている", () => {
    render(<ZipUploadForm onUploaded={vi.fn()} />);

    expect(screen.getByTestId("upload-button")).toBeDisabled();
    expect(screen.getByTestId("status-message")).toHaveTextContent(
      "ZIP ファイルを選択してアップロードしてください。",
    );
  });

  it("ファイル未選択で送信するとエラーを表示する", async () => {
    render(<ZipUploadForm onUploaded={vi.fn()} />);

    const form = screen.getByTestId("upload-button").closest("form");
    expect(form).toBeInTheDocument();
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(screen.getByTestId("status-message")).toHaveTextContent(
        "ZIP ファイルを選択してください。",
      );
    });
  });

  it("ファイルを選択するとアップロードボタンが有効になる", async () => {
    render(<ZipUploadForm onUploaded={vi.fn()} />);

    const file = new File(["dummy"], "pages.zip", { type: "application/zip" });
    await userEvent.upload(screen.getByTestId("zip-file-input"), file);

    expect(screen.getByTestId("upload-button")).toBeEnabled();
  });

  it("ジョブ作成に失敗するとエラーを表示する", async () => {
    vi.mocked(createJob).mockRejectedValueOnce(new Error("作成失敗"));

    render(<ZipUploadForm onUploaded={vi.fn()} />);

    const file = new File(["dummy"], "pages.zip", { type: "application/zip" });
    await userEvent.upload(screen.getByTestId("zip-file-input"), file);
    await userEvent.click(screen.getByTestId("upload-button"));

    await waitFor(() => {
      expect(screen.getByTestId("status-message")).toHaveTextContent("作成失敗");
    });
  });

  it("ZIP アップロードに失敗するとエラーを表示する", async () => {
    vi.mocked(createJob).mockResolvedValueOnce("job-123");
    vi.mocked(uploadZip).mockRejectedValueOnce(new Error("アップロード失敗"));

    render(<ZipUploadForm onUploaded={vi.fn()} />);

    const file = new File(["dummy"], "pages.zip", { type: "application/zip" });
    await userEvent.upload(screen.getByTestId("zip-file-input"), file);
    await userEvent.click(screen.getByTestId("upload-button"));

    await waitFor(() => {
      expect(screen.getByTestId("status-message")).toHaveTextContent("アップロード失敗");
    });
  });

  it("正常フローで onUploaded が呼ばれる", async () => {
    vi.mocked(createJob).mockResolvedValueOnce("job-123");
    vi.mocked(uploadZip).mockResolvedValueOnce(["page_001.png", "page_002.png"]);
    const onUploaded = vi.fn();

    render(<ZipUploadForm onUploaded={onUploaded} />);

    const file = new File(["dummy"], "pages.zip", { type: "application/zip" });
    await userEvent.upload(screen.getByTestId("zip-file-input"), file);
    await userEvent.click(screen.getByTestId("upload-button"));

    await waitFor(() => {
      expect(onUploaded).toHaveBeenCalledWith("job-123", ["page_001.png", "page_002.png"]);
    });
    expect(screen.getByText("page_001.png")).toBeInTheDocument();
    expect(screen.getByText("page_002.png")).toBeInTheDocument();
    expect(screen.getByTestId("status-message")).toHaveTextContent("アップロードが完了しました。");
  });
});
