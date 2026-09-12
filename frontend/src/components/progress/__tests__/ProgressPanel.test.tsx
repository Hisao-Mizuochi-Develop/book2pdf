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
  it("進捗データがない場合は何も描画しない", () => {
    const { container } = render(<ProgressPanel latest={null} />);

    expect(container.firstChild).toBeNull();
  });

  it("最新進捗をプログレスバー付きで表示する", () => {
    render(<ProgressPanel latest={makeProgressEvent()} />);

    expect(screen.getByText("進捗")).toBeInTheDocument();
    expect(screen.getByText("状態: processing")).toBeInTheDocument();
    expect(screen.getByText("1 / 2 ページ")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();

    const bar = screen.getByTestId("progress-bar");
    expect(bar).toHaveStyle({ width: "50%" });
  });

  it("progress が 0 未満の場合は 0% にクランプする", () => {
    render(<ProgressPanel latest={makeProgressEvent({ progress: -0.1 })} />);

    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getByTestId("progress-bar")).toHaveStyle({ width: "0%" });
  });

  it("progress が 1.0 を超える場合は 100% にクランプする", () => {
    render(<ProgressPanel latest={makeProgressEvent({ progress: 1.5 })} />);

    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(screen.getByTestId("progress-bar")).toHaveStyle({ width: "100%" });
  });

  it("total_pages が 0 の場合は安全に表示する", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({ current_page: 0, total_pages: 0 })}
      />
    );

    expect(screen.getByText("0 / ? ページ")).toBeInTheDocument();
  });

  it("段階的なステップ表示がレンダリングされる", () => {
    render(<ProgressPanel latest={makeProgressEvent({ progress: 0.5 })} />);

    expect(screen.getByTestId("progress-stages")).toBeInTheDocument();
    expect(screen.getByText("アップロード")).toBeInTheDocument();
    expect(screen.getByText("OCR 処理")).toBeInTheDocument();
    expect(screen.getByText("PDF 生成")).toBeInTheDocument();
    expect(screen.getByText("完了")).toBeInTheDocument();
  });

  it("progress < 0.33 の場合はステップ1がアクティブ", () => {
    render(<ProgressPanel latest={makeProgressEvent({ progress: 0.1 })} />);

    const dot0 = screen.getByTestId("stage-dot-0");
    expect(dot0).toHaveClass("bg-primary", "ring-2");
  });

  it("0.33 <= progress < 0.66 の場合はステップ2がアクティブ", () => {
    render(<ProgressPanel latest={makeProgressEvent({ progress: 0.5 })} />);

    const dot0 = screen.getByTestId("stage-dot-0");
    const dot1 = screen.getByTestId("stage-dot-1");
    expect(dot0).toHaveClass("bg-green-500");
    expect(dot1).toHaveClass("bg-primary", "ring-2");
  });

  it("0.66 <= progress < 1.0 の場合はステップ3がアクティブ", () => {
    render(<ProgressPanel latest={makeProgressEvent({ progress: 0.75 })} />);

    const dot2 = screen.getByTestId("stage-dot-2");
    expect(dot2).toHaveClass("bg-primary", "ring-2");
  });

  it("progress >= 1.0 の場合はステップ4が完了状態", () => {
    render(<ProgressPanel latest={makeProgressEvent({ progress: 1.0, status: "completed" })} />);

    const dot3 = screen.getByTestId("stage-dot-3");
    expect(dot3).toHaveClass("bg-green-500");
  });

  it("OCR 処理中の進捗メッセージを単一行で表示する", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({
          message: "OCR 処理中です（1/2）",
        })}
      />
    );

    expect(screen.getByTestId("ocr-status-line")).toHaveTextContent(
      "OCR 処理中です（1/2）"
    );
  });

  it("OCR 完了の進捗メッセージを単一行で表示する", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({
          progress: 1.0,
          status: "completed",
          message: "OCR 処理が完了しました（2/2）",
        })}
      />
    );

    expect(screen.getByTestId("ocr-status-line")).toHaveTextContent(
      "OCR 処理が完了しました（2/2）"
    );
  });

  it("PDF 生成中の進捗メッセージを単一行で表示する", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({
          message: "PDF を生成中です",
        })}
      />
    );

    expect(screen.getByTestId("pdf-status-line")).toHaveTextContent(
      "PDF 作成中です"
    );
  });

  it("PDF 生成完了の進捗メッセージを単一行で表示する", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({
          progress: 1.0,
          status: "completed",
          message: "PDF 生成が完了しました",
        })}
      />
    );

    expect(screen.getByTestId("pdf-status-line")).toHaveTextContent(
      "PDF 作成しました"
    );
  });

  it("認識できないメッセージは OCR／PDF 行に表示しない", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({
          message: "一般的なログメッセージ",
        })}
      />
    );

    expect(screen.queryByTestId("ocr-status-line")).not.toBeInTheDocument();
    expect(screen.queryByTestId("pdf-status-line")).not.toBeInTheDocument();
  });
});
