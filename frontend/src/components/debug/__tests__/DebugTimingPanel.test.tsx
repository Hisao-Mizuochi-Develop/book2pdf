import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DebugTimingPanel } from "../DebugTimingPanel";
import type { TimingDebugInfo } from "@/types";

const baseTiming: TimingDebugInfo = {
  zipUpload: { start: null, end: null, elapsedMs: null },
  ocrTotal: { start: null, end: null, elapsedMs: null },
  ocrPages: [],
  pdfGeneration: { start: null, end: null, elapsedMs: null },
  overall: { start: null, end: null, elapsedMs: null },
};

describe("DebugTimingPanel", () => {
  it("パネルが表示される", () => {
    render(<DebugTimingPanel timing={baseTiming} />);

    expect(screen.getByTestId("debug-timing-panel")).toBeInTheDocument();
    expect(screen.getByText("デバッグ情報（処理時間）")).toBeInTheDocument();
  });

  it("タイミング値が正しくフォーマットされる", () => {
    const timing: TimingDebugInfo = {
      ...baseTiming,
      zipUpload: {
        start: "2026-09-15T10:00:00.000Z",
        end: "2026-09-15T10:00:01.500Z",
        elapsedMs: 1500,
      },
      overall: {
        start: "2026-09-15T10:00:00.000Z",
        end: "2026-09-15T10:00:05.000Z",
        elapsedMs: 5000,
      },
    };

    render(<DebugTimingPanel timing={timing} />);

    expect(screen.getByText("1.50s")).toBeInTheDocument();
    expect(screen.getByText("5.00s")).toBeInTheDocument();
  });

  it("OCR 処理総時間が表示される", () => {
    const timing: TimingDebugInfo = {
      ...baseTiming,
      ocrTotal: {
        start: "2026-09-15T10:00:01.000Z",
        end: "2026-09-15T10:00:03.500Z",
        elapsedMs: 2500,
      },
    };

    render(<DebugTimingPanel timing={timing} />);

    expect(screen.getByText("OCR 処理総時間")).toBeInTheDocument();
    expect(screen.getByText("2.50s")).toBeInTheDocument();
  });

  it("OCR ページが表示される", () => {
    const timing: TimingDebugInfo = {
      ...baseTiming,
      ocrPages: [
        {
          pageIndex: 0,
          fileName: "page_001.png",
          start: "2026-09-15T10:00:00.000Z",
          end: "2026-09-15T10:00:00.200Z",
          elapsedMs: 200,
        },
        {
          pageIndex: 1,
          fileName: "page_002.png",
          start: null,
          end: null,
          elapsedMs: null,
        },
      ],
    };

    render(<DebugTimingPanel timing={timing} />);

    expect(screen.getByText("OCR 処理時間（ページ毎）")).toBeInTheDocument();
    expect(screen.getByText("page_001.png")).toBeInTheDocument();
    expect(screen.getByText("page_002.png")).toBeInTheDocument();
    expect(screen.getByText("200ms")).toBeInTheDocument();
  });
});
