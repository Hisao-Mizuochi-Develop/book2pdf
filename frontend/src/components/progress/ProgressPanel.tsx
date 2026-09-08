"use client";

// OCR 処理の進捗を表示する機能単位のコンポーネントです。
// useOcrJob から受け取った最新進捗イベントとログを、プログレスバーとテキストで描画します。

import type { ProgressPanelProps } from "@/types";

/** 進捗段階を表すステップ定義です。 */
const STAGES = [
  { label: "アップロード", threshold: 0 },
  { label: "OCR 処理", threshold: 0.33 },
  { label: "PDF 生成", threshold: 0.66 },
  { label: "完了", threshold: 1.0 },
] as const;

/**
 * 現在の進捗値（0〜1）に基づき、どのステップがアクティブかを判定します。
 * @param progress 進捗値（0.0〜1.0）
 * @returns アクティブなステップの 0-based インデックス
 */
function getActiveStageIndex(progress: number): number {
  for (let i = STAGES.length - 1; i >= 0; i--) {
    if (progress >= STAGES[i].threshold) {
      return i;
    }
  }
  return 0;
}

/**
 * OCR 処理の進捗を表示します。
 *
 * 最新の進捗イベントに基づき、段階的なステップ表示・プログレスバー・パーセンテージを表示し、
 * 時系列の進捗ログを併せて出力します。表示データがない場合は何も描画しません。
 *
 * @param latest 最新の進捗イベント。未受信時は null です。
 * @param log 時系列順の進捗メッセージログです。
 */
export function ProgressPanel({ latest, log }: ProgressPanelProps) {
  if (!latest && log.length === 0) {
    return null;
  }

  // progress が範囲外の値を返した場合でも UI が崩れないよう 0〜100 にクランプします
  // backend からは 0.0〜1.0 の float で送られてくるため、×100 してパーセンテージに変換します
  const progressPercent = latest
    ? Math.min(100, Math.max(0, Math.round(latest.progress * 100)))
    : 0;

  // total_pages が 0 や未設定の場合に備え、安全な表示文字列を用意します
  const totalPages = latest && latest.total_pages > 0 ? latest.total_pages : "?";
  const currentPage = latest ? latest.current_page : "?";

  const allCompleted = latest ? latest.progress >= 1.0 : false;
  const activeStageIndex = latest && !allCompleted ? getActiveStageIndex(latest.progress) : 0;

  return (
    <div
      data-testid="progress-panel"
      className="rounded-2xl border border-border bg-card p-6 shadow-sm"
    >
      <h2 className="text-lg font-semibold text-card-foreground">進捗</h2>

      {/* 段階的なステップ表示 */}
      {latest && (
        <div className="mt-4 flex items-center justify-between" data-testid="progress-stages">
          {STAGES.map((stage, index) => {
            const isCompleted = allCompleted || index < activeStageIndex;
            const isActive = !allCompleted && index === activeStageIndex;
            const isPending = !allCompleted && index > activeStageIndex;

            return (
              <div key={stage.label} className="flex flex-1 items-center">
                <div className="flex flex-col items-center">
                  <div
                    data-testid={`stage-dot-${index}`}
                    className={`
                      flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold
                      transition-colors duration-300
                      ${isCompleted ? "bg-green-500 text-white" : ""}
                      ${isActive ? "bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2" : ""}
                      ${isPending ? "bg-muted text-muted-foreground" : ""}
                    `}
                  >
                    {isCompleted ? "✓" : index + 1}
                  </div>
                  <span
                    className={`
                      mt-1 text-xs font-medium
                      ${isCompleted || isActive ? "text-foreground" : "text-muted-foreground"}
                    `}
                  >
                    {stage.label}
                  </span>
                </div>
                {index < STAGES.length - 1 && (
                  <div
                    data-testid={`stage-line-${index}`}
                    className={`
                      mx-2 h-0.5 flex-1 transition-colors duration-300
                      ${isCompleted ? "bg-green-500" : "bg-muted"}
                    `}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      {latest && (
        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between text-sm text-card-foreground">
            <span>状態: {latest.status}</span>
            <span>
              {currentPage} / {totalPages} ページ
            </span>
          </div>
          <div
            data-testid="progress-track"
            className="h-2 w-full overflow-hidden rounded-full bg-muted"
          >
            <div
              data-testid="progress-bar"
              className="h-full bg-primary transition-all duration-500 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <p className="text-sm text-muted-foreground">{progressPercent}%</p>
        </div>
      )}

      {log.length > 0 && (
        <pre
          data-testid="progress-log"
          className="mt-4 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-background p-3 text-sm text-foreground"
        >
          {log.join("\n")}
        </pre>
      )}
    </div>
  );
}
