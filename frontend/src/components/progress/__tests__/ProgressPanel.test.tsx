import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProgressPanel } from "../ProgressPanel";
import type { ProgressEvent } from "@/types";

/**
 * ProgressPanel 用のテストデータです。
 * 進捗イベントの必須フィールドを揃えたベースオブジェクトを提供します。
 */
function makeProgressEvent(overrides: Partial<ProgressEvent> = {}): ProgressEvent {
  return {
    job_id: "job-123",
    status: "processing",
    progress: 0.5,
    current_page: 1,
    total_pages: 2,
    ...overrides,
  };
}

describe("ProgressPanel", () => {
  it("進捗データもログもない場合は何も描画しない", () => {
    const { container } = render(<ProgressPanel latest={null} log={[]} />);

    expect(container.firstChild).toBeNull();
  });

  it("最新進捗をプログレスバー付きで表示する", () => {
    render(<ProgressPanel latest={makeProgressEvent()} log={[]} />);

    expect(screen.getByText("進捗")).toBeInTheDocument();
    expect(screen.getByText("状態: processing")).toBeInTheDocument();
    expect(screen.getByText("1 / 2 ページ")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();

    const bar = screen.getByTestId("progress-bar");
    expect(bar).toHaveStyle({ width: "50%" });
  });

  it("進捗ログを改行して表示する", () => {
    const log = ["ジョブを作成しました", "OCR 処理を開始しました"];
    render(<ProgressPanel latest={null} log={log} />);

    const logElement = screen.getByTestId("progress-log");
    expect(logElement).toHaveTextContent("ジョブを作成しました");
    expect(logElement).toHaveTextContent("OCR 処理を開始しました");
  });

  it("進捗とログの両方が表示される", () => {
    const log = ["50% 完了"];
    render(<ProgressPanel latest={makeProgressEvent()} log={log} />);

    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByTestId("progress-log")).toHaveTextContent("50% 完了");
  });

  it("progress が 0 未満の場合は 0% にクランプする", () => {
    render(<ProgressPanel latest={makeProgressEvent({ progress: -0.1 })} log={[]} />);

    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getByTestId("progress-bar")).toHaveStyle({ width: "0%" });
  });

  it("progress が 1.0 を超える場合は 100% にクランプする", () => {
    render(<ProgressPanel latest={makeProgressEvent({ progress: 1.5 })} log={[]} />);

    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(screen.getByTestId("progress-bar")).toHaveStyle({ width: "100%" });
  });

  it("total_pages が 0 の場合は安全に表示する", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({ current_page: 0, total_pages: 0 })}
        log={[]}
      />
    );

    expect(screen.getByText("0 / ? ページ")).toBeInTheDocument();
  });
});
