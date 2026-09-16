"use client";

import type { TimingDebugInfo } from "@/types";

/**
 * デバッグ用のタイミングパネルです。
 *
 * ZIP アップロード、各ページ OCR 処理、PDF 生成、全体経過時間を
 * 表形式で表示します。
 */
export interface DebugTimingPanelProps {
  /** 表示するタイミング情報です。 */
  timing: TimingDebugInfo;
}

/** ISO 8601 時刻を読みやすい形式にフォーマットします。 */
function formatTime(iso: string | null): string {
  if (!iso) return "-";
  const date = new Date(iso);
  return date.toLocaleTimeString("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    fractionalSecondDigits: 3,
    hour12: false,
  });
}

/** ミリ秒を秒・ミリ秒表記にフォーマットします。 */
function formatElapsed(ms: number | null): string {
  if (ms === null || ms === undefined) return "-";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

/** 位相タイミング行コンポーネントです。 */
function PhaseRow({
  label,
  timing,
}: {
  label: string;
  timing: {
    start: string | null;
    end: string | null;
    elapsedMs: number | null;
  };
}) {
  return (
    <tr className="border-b border-border last:border-b-0">
      <td className="py-2 pr-4 font-medium text-foreground">{label}</td>
      <td className="py-2 pr-4 font-mono text-muted-foreground">
        {formatTime(timing.start)}
      </td>
      <td className="py-2 pr-4 font-mono text-muted-foreground">
        {formatTime(timing.end)}
      </td>
      <td className="py-2 text-right font-mono text-muted-foreground">
        {formatElapsed(timing.elapsedMs)}
      </td>
    </tr>
  );
}

export function DebugTimingPanel({ timing }: DebugTimingPanelProps) {
  return (
    <div
      className="rounded-2xl border border-border bg-card p-6 shadow-sm"
      data-testid="debug-timing-panel"
    >
      <h2 className="text-lg font-semibold text-card-foreground">
        デバッグ情報（処理時間）
      </h2>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted-foreground">
              <th className="pb-2 pr-4 font-medium">項目</th>
              <th className="pb-2 pr-4 font-medium">開始</th>
              <th className="pb-2 pr-4 font-medium">完了</th>
              <th className="pb-2 text-right font-medium">経過</th>
            </tr>
          </thead>
          <tbody>
            <PhaseRow label="ZIP アップロード" timing={timing.zipUpload} />
            <PhaseRow label="OCR 処理総時間" timing={timing.ocrTotal} />
            <PhaseRow label="PDF 生成" timing={timing.pdfGeneration} />
            <PhaseRow label="全体" timing={timing.overall} />
          </tbody>
        </table>
      </div>

      {timing.ocrPages.length > 0 && (
        <div className="mt-6">
          <h3 className="text-base font-semibold text-card-foreground">
            OCR 処理時間（ページ毎）
          </h3>
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium">ページ</th>
                  <th className="pb-2 pr-4 font-medium">ファイル名</th>
                  <th className="pb-2 pr-4 font-medium">開始</th>
                  <th className="pb-2 pr-4 font-medium">完了</th>
                  <th className="pb-2 text-right font-medium">経過</th>
                </tr>
              </thead>
              <tbody>
                {timing.ocrPages.map((page) => (
                  <tr
                    key={page.pageIndex}
                    className="border-b border-border last:border-b-0"
                  >
                    <td className="py-2 pr-4 font-medium text-foreground">
                      {page.pageIndex + 1}
                    </td>
                    <td className="py-2 pr-4 text-muted-foreground">
                      {page.fileName}
                    </td>
                    <td className="py-2 pr-4 font-mono text-muted-foreground">
                      {formatTime(page.start)}
                    </td>
                    <td className="py-2 pr-4 font-mono text-muted-foreground">
                      {formatTime(page.end)}
                    </td>
                    <td className="py-2 text-right font-mono text-muted-foreground">
                      {formatElapsed(page.elapsedMs)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
