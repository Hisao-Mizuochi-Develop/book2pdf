import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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
  it("進捗データが未受信でもパネルは描画される", () => {
    render(<ProgressPanel latest={null} />);

    expect(screen.getByTestId("progress-panel")).toBeInTheDocument();
    expect(screen.getByText("進捗")).toBeInTheDocument();
    expect(screen.getByText("0%")).toBeInTheDocument();

    // ステップ1（ZIPアップロード）がアクティブ
    const dot0 = screen.getByTestId("stage-dot-0");
    expect(dot0).toHaveClass("bg-primary", "ring-2");
  });

  it("最新進捗をプログレスバー付きで表示する", () => {
    render(<ProgressPanel latest={makeProgressEvent()} />);

    expect(screen.getByText("進捗")).toBeInTheDocument();
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

  it("段階的なステップ表示がレンダリングされる", () => {
    render(<ProgressPanel latest={makeProgressEvent({ progress: 0.5 })} />);

    expect(screen.getByTestId("progress-stages")).toBeInTheDocument();
    expect(screen.getByText("ZIPアップロード")).toBeInTheDocument();
    expect(screen.getByText("OCR処理")).toBeInTheDocument();
    expect(screen.getByText("PDF生成")).toBeInTheDocument();
    expect(screen.getByText("完了")).toBeInTheDocument();
  });

  it("status=uploaded の場合はステップ1がアクティブ", () => {
    render(<ProgressPanel latest={makeProgressEvent({ status: "uploaded", progress: 0 })} />);

    const dot0 = screen.getByTestId("stage-dot-0");
    expect(dot0).toHaveClass("bg-primary", "ring-2");
  });

  it("status=processing かつ progress < 0.75 の場合はステップ2がアクティブ", () => {
    render(<ProgressPanel latest={makeProgressEvent({ status: "processing", progress: 0.5 })} />);

    const dot0 = screen.getByTestId("stage-dot-0");
    const dot1 = screen.getByTestId("stage-dot-1");
    expect(dot0).toHaveClass("bg-green-500");
    expect(dot1).toHaveClass("bg-primary", "ring-2");
  });

  it("status=processing かつ progress >= 0.75 の場合はステップ3がアクティブ", () => {
    render(<ProgressPanel latest={makeProgressEvent({ status: "processing", progress: 0.75 })} />);

    const dot2 = screen.getByTestId("stage-dot-2");
    expect(dot2).toHaveClass("bg-primary", "ring-2");
  });

  it("status=completed の場合はステップ4が完了状態", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({ status: "completed", progress: 1.0 })}
      />,
    );

    const dot3 = screen.getByTestId("stage-dot-3");
    expect(dot3).toHaveClass("bg-green-500");
  });

  it("status=completed でも progress が低い場合は完了ステップを維持する", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({ status: "completed", progress: 0.5 })}
      />,
    );

    const dot3 = screen.getByTestId("stage-dot-3");
    expect(dot3).toHaveClass("bg-green-500");
  });

  it("進捗メッセージを1行表示エリアに表示する", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({
          message: "OCR処理中です（1/2）",
        })}
      />
    );

    expect(screen.getByTestId("progress-message-line")).toHaveTextContent(
      "OCR処理中です（1/2）"
    );
  });

  it("error Props をエラー表示エリアに表示する", () => {
    render(<ProgressPanel latest={makeProgressEvent()} error="エラーが発生しました" />);

    expect(screen.getByTestId("progress-error-line")).toHaveTextContent("エラーが発生しました");
  });

  it("status が failed の場合はメッセージをエラー表示エリアに表示する", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({
          status: "failed",
          progress: 0.5,
          message: "OCR 処理に失敗しました",
        })}
      />
    );

    expect(screen.getByTestId("progress-error-line")).toHaveTextContent(
      "OCR 処理に失敗しました"
    );
  });

  it("メッセージに『エラー』が含まれる場合はエラー表示エリアに表示する", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({
          message: "接続エラーが発生しました",
        })}
      />
    );

    expect(screen.getByTestId("progress-error-line")).toHaveTextContent(
      "接続エラーが発生しました"
    );
  });

  it("通常のメッセージはエラー表示エリアに表示しない", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({
          message: "PDFファイル生成が完了しました",
          status: "completed",
          progress: 1.0,
        })}
      />
    );

    expect(screen.queryByTestId("progress-error-line")).not.toBeInTheDocument();
  });

  it("showCancel=true かつ onCancel ありの場合にキャンセルボタンを表示する", () => {
    render(<ProgressPanel latest={makeProgressEvent()} showCancel onCancel={vi.fn()} />);

    expect(screen.getByTestId("cancel-button")).toBeInTheDocument();
  });

  it("キャンセルボタンをクリックすると onCancel が呼ばれる", () => {
    const onCancel = vi.fn();
    render(<ProgressPanel latest={makeProgressEvent()} showCancel onCancel={onCancel} />);

    fireEvent.click(screen.getByTestId("cancel-button"));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("showCancel=false ではキャンセルボタンを表示しない", () => {
    render(<ProgressPanel latest={makeProgressEvent()} onCancel={vi.fn()} />);

    expect(screen.queryByTestId("cancel-button")).not.toBeInTheDocument();
  });

  it("onCancel が未指定ではキャンセルボタンを表示しない", () => {
    render(<ProgressPanel latest={makeProgressEvent()} showCancel />);

    expect(screen.queryByTestId("cancel-button")).not.toBeInTheDocument();
  });

  it("status=completed ではキャンセルボタンを表示しない", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({ status: "completed", progress: 1.0 })}
        showCancel
        onCancel={vi.fn()}
      />,
    );

    expect(screen.queryByTestId("cancel-button")).not.toBeInTheDocument();
  });

  it("status=cancelled ではキャンセルボタンを表示しない", () => {
    render(
      <ProgressPanel
        latest={makeProgressEvent({ status: "cancelled", progress: 0 })}
        showCancel
        onCancel={vi.fn()}
      />,
    );

    expect(screen.queryByTestId("cancel-button")).not.toBeInTheDocument();
  });
});
