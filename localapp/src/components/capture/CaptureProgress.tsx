/**
 * 連続キャプチャの進捗表示コンポーネント
 *
 * captureStore の状態を購読し、進捗バー・ステータス・メッセージを表示する。
 * IDLE 時は非表示、キャプチャ中はアニメーション付きで進捗を表示する。
 *
 * 【表示内容】
 * - ステータスバッジ（カラーで状態を視覚的に表現）
 * - 進捗バー（0~100%、ステータスに応じた色）
 * - メッセージテキスト（Rust 側から送信された内容）
 * - ページ数（"X / Y ページ"形式）
 */

import type { CaptureStatus } from "@/store/captureStore";

/**
 * CaptureProgress コンポーネントのプロパティ
 */
interface CaptureProgressProps {
  /** 連続キャプチャ実行中か */
  isCapturing: boolean;
  /** 現在キャプチャ済みのページ数 */
  currentPage: number;
  /** 予想総ページ数 */
  totalPages: number;
  /** 現在のステータス */
  status: CaptureStatus;
  /** ユーザー向けメッセージ */
  message: string;
}

/**
 * ステータスごとの日本語表示テキスト
 */
const STATUS_LABEL: Record<CaptureStatus, string> = {
  idle: "待機中",
  capturing: "キャプチャ中",
  page_turn: "ページ送り",
  waiting: "待機中",
  completed: "完了",
  stopped: "停止済み",
  error: "エラー",
};

/**
 * ステータスごとの Tailwind CSS 色クラス（バッジ用）
 *
 * Apple HIG 風デザインに合わせた控えめな色づけ。
 * テキスト色は対応する背景色より濃いトーンにする。
 */
const STATUS_COLORS: Record<CaptureStatus, { bg: string; text: string; bar: string }> = {
  idle: {
    bg: "bg-muted",
    text: "text-muted-foreground",
    bar: "bg-muted-foreground",
  },
  capturing: {
    bg: "bg-primary/10",
    text: "text-primary",
    bar: "bg-primary",
  },
  page_turn: {
    bg: "bg-purple-100",
    text: "text-purple-700",
    bar: "bg-purple-500",
  },
  waiting: {
    bg: "bg-amber-100",
    text: "text-amber-700",
    bar: "bg-amber-500",
  },
  completed: {
    bg: "bg-green-100",
    text: "text-green-700",
    bar: "bg-green-500",
  },
  stopped: {
    bg: "bg-orange-100",
    text: "text-orange-700",
    bar: "bg-orange-500",
  },
  error: {
    bg: "bg-destructive/10",
    text: "text-destructive",
    bar: "bg-destructive",
  },
};

/**
 * 連続キャプチャの進捗表示コンポーネント
 *
 * IDLE 時は何も表示しない。キャプチャ中はステータスバッジ、
 * 進捗バー、メッセージテキストを縦積みで表示する。
 *
 * 進捗バーの計算：
 * - totalPages > 0 の場合: (currentPage / totalPages) * 100%
 * - totalPages === 0 の場合（開始直後など）: 不確定インジケータ（アニメーション）
 */
export function CaptureProgress({
  isCapturing,
  currentPage,
  totalPages,
  status,
  message,
}: CaptureProgressProps) {
  // IDLE 状態かつ実行中でない場合は非表示
  if (status === "idle" && !isCapturing) {
    return null;
  }

  const colors = STATUS_COLORS[status];

  // 進捗率の計算
  const progressPercent =
    totalPages > 0 ? Math.min((currentPage / totalPages) * 100, 100) : 0;

  // 終端状態（完了・停止・エラー）は確定表示として最大幅で表示し、アニメーションはしない
  const isTerminal = status === "completed" || status === "stopped" || status === "error";

  return (
    <div className="space-y-3 rounded-lg border bg-card p-5 shadow-sm">
      {/* --- ステータスバッジとページ数 --- */}
      <div className="flex items-center justify-between">
        {/* ステータスバッジ */}
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors.bg} ${colors.text}`}
        >
          {/* キャプチャ中は脈動アニメーションのドット */}
          {isCapturing && !isTerminal && (
            <span className="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
          )}
          {STATUS_LABEL[status]}
        </span>

        {/* ページ数表示 */}
        {currentPage > 0 && (
          <span className="text-sm text-muted-foreground">
            {totalPages > 0
              ? `${currentPage} / ${totalPages} ページ`
              : `${currentPage} ページ取得`}
          </span>
        )}
      </div>

      {/* --- 進捗バー --- */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full rounded-full transition-all duration-300 ease-out ${colors.bar} ${
            isCapturing && !isTerminal && totalPages === 0 ? "animate-progress-indeterminate" : ""
          }`}
          style={{
            width: isCapturing && !isTerminal && totalPages === 0 ? "40%" : `${progressPercent}%`,
          }}
        />
      </div>

      {/* --- メッセージテキスト --- */}
      {message && (
        <p className="text-sm text-muted-foreground">{message}</p>
      )}
    </div>
  );
}
