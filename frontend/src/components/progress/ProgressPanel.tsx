"use client";

// OCR 処理の進捗を表示する機能単位のコンポーネントです。
// useOcrJob から受け取った最新進捗イベントを、ステップ表示・プログレスバー・
// 1行専用メッセージエリア・エラーメッセージエリアで描画します。

import type { ProgressPanelProps } from "@/types";

/** 進捗段階を表すステップ定義です。 */
const STAGES = [
  { label: "ZIPアップロード", threshold: 0 },
  { label: "OCR処理", threshold: 0.33 },
  { label: "PDF生成", threshold: 0.66 },
  { label: "完了", threshold: 1.0 },
] as const;

/**
 * 現在の進捗値とステータスに基づき、どのステップがアクティブかを判定します。
 * @param progress 進捗値（0.0〜1.0）
 * @param status 進捗ステータス（uploaded / processing / completed / failed）
 * @returns アクティブなステップの 0-based インデックス
 */
function getActiveStageIndex(progress: number, status: string): number {
  if (status === "completed") {
    return STAGES.length - 1;
  }
  if (status === "uploaded") {
    return 0;
  }
  if (status === "processing") {
    if (progress >= 0.75) {
      return 2; // PDF生成
    }
    return 1; // OCR処理
  }
  return 0;
}

/**
 * メッセージまたは状態がエラーを示すかどうかを判定します。
 */
function hasErrorState(message: string | undefined, status: string): boolean {
  if (status === "failed") return true;
  if (!message) return false;
  return message.includes("失敗") || message.includes("エラー");
}

/**
 * OCR 処理の進捗を表示します。
 *
 * 最新の進捗イベントに基づき、以下の4領域で描画します。
 *   1. 段階的ステップ表示（ZIPアップロード → OCR処理 → PDF生成 → 完了）
 *   2. プログレスバー + パーセンテージ
 *   3. 1行専用メッセージエリア
 *   4. エラーメッセージ表示エリア
 *
 * `latest` が未受信でもパネル自体は描画され、ステップ1「ZIPアップロード」を
 * アクティブに表示します。
 *
 * @param latest 最新の進捗イベント。未受信時は null です。
 * @param error 表示するエラーメッセージ。省略時は表示しません。
 */
export function ProgressPanel({ latest, error = "" }: ProgressPanelProps) {
  const progress = latest?.progress ?? 0;
  const status = latest?.status ?? "uploaded";
  const message = latest?.message ?? "";

  // backend からは 0.0〜1.0 の float で送られてくるため、×100 してパーセンテージに変換します
  const progressPercent = Math.min(100, Math.max(0, Math.round(progress * 100)));

  const activeStageIndex = getActiveStageIndex(progress, status);

  const errorFromState = hasErrorState(message, status);
  const shouldShowError = Boolean(error) || errorFromState;
  const errorMessage = error || (errorFromState ? message : "");

  return (
    <div
      data-testid="progress-panel"
      className="rounded-2xl border border-border bg-card p-6 shadow-sm"
    >
      <h2 className="text-lg font-semibold text-card-foreground">進捗</h2>

      {/* 1. 段階的なステップ表示 */}
      <div className="mt-4 flex items-center justify-between" data-testid="progress-stages">
        {STAGES.map((stage, index) => {
          const isCompleted = index < activeStageIndex || status === "completed";
          const isActive = index === activeStageIndex && status !== "completed";
          const isPending = index > activeStageIndex && status !== "completed";

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
                    mt-1 text-center text-xs font-medium
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

      {/* 2. プログレスバー + %（横並び） */}
      <div className="mt-6 flex items-center gap-3">
        <div
          data-testid="progress-track"
          className="h-3 flex-1 overflow-hidden rounded-full bg-muted"
        >
          <div
            data-testid="progress-bar"
            className="h-full bg-primary transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <span className="text-sm font-semibold text-card-foreground tabular-nums">
          {progressPercent}%
        </span>
      </div>

      {/* 3. 1行専用メッセージエリア */}
      {message && !shouldShowError && (
        <div className="mt-4 rounded-lg border border-border bg-muted/40 px-4 py-2">
          <p
            data-testid="progress-message-line"
            className="text-sm font-medium text-card-foreground"
          >
            📄 {message}
          </p>
        </div>
      )}

      {/* 4. エラーメッセージ表示エリア */}
      {shouldShowError && errorMessage && (
        <div className="mt-4 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-2">
          <p
            data-testid="progress-error-line"
            className="text-sm font-medium text-destructive"
          >
            ⚠️ {errorMessage}
          </p>
        </div>
      )}
    </div>
  );
}
