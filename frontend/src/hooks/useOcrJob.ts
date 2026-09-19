"use client";

// OCR ジョブの実行進捗管理を担当するカスタムフックです。
// ZIP アップロード完了後の OCR 実行、SSE 進捗購読、PDF ダウンロード可能状態の
// 管理を一括して行います。

import { useCallback, useEffect, useRef, useState } from "react";
import { cancelJob, runOcr, subscribeJobProgress, pollJobProgress } from "@/lib/api";
import type { ProgressEvent, TimingDebugInfo, UploadTimingInfo } from "@/types";

/** useOcrJob の戻り値型です。 */
export interface UseOcrJobResult {
  /** 現在のジョブ ID です。 */
  jobId: string | null;
  /** アップロードされた画像ファイル名の一覧です。 */
  files: string[];
  /** 最新の進捗イベントです。 */
  latestProgress: ProgressEvent | null;
  /** 時系列順の進捗メッセージログです。 */
  progressLog: string[];
  /** エラーメッセージです。 */
  error: string;
  /** 処理中フラグです。 */
  isLoading: boolean;
  /** PDF ダウンロード可能なジョブ ID です。 */
  downloadableJobId: string | null;
  /** デバッグ用のタイミング情報です。 */
  timingDebug: TimingDebugInfo;
  /** ZIP アップロード完了後に OCR 処理を開始します。 */
  handleUploaded: (jobId: string, files: string[], timing?: UploadTimingInfo) => Promise<void>;
  /** 進行中のジョブをキャンセルします。 */
  handleCancel: () => Promise<void>;
  /** 状態を初期化します。 */
  reset: () => void;
}

/**
 * OCR ジョブの状態と実行制御を管理するカスタムフックです。
 */
export function useOcrJob(): UseOcrJobResult {
  const [jobId, setJobId] = useState<string | null>(null);
  const [files, setFiles] = useState<string[]>([]);
  const [latestProgress, setLatestProgress] = useState<ProgressEvent | null>(null);
  const [progressLog, setProgressLog] = useState<string[]>([]);
  const [error, setError] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [downloadableJobId, setDownloadableJobId] = useState<string | null>(null);
  const [timingDebug, setTimingDebug] = useState<TimingDebugInfo>({
    zipUpload: { start: null, end: null, elapsedMs: null },
    ocrTotal: { start: null, end: null, elapsedMs: null },
    ocrPages: [],
    pdfGeneration: { start: null, end: null, elapsedMs: null },
    overall: { start: null, end: null, elapsedMs: null },
  });
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollStopRef = useRef<(() => void) | null>(null);

  const cleanupProgress = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollStopRef.current) {
      pollStopRef.current();
      pollStopRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    cleanupProgress();
    setJobId(null);
    setFiles([]);
    setLatestProgress(null);
    setProgressLog([]);
    setError("");
    setIsLoading(false);
    setDownloadableJobId(null);
    setTimingDebug(() => ({
      zipUpload: { start: null, end: null, elapsedMs: null },
      ocrTotal: { start: null, end: null, elapsedMs: null },
      ocrPages: [],
      pdfGeneration: { start: null, end: null, elapsedMs: null },
      overall: { start: null, end: null, elapsedMs: null },
    }));
  }, [cleanupProgress]);

  const parseProgressEvent = useCallback((message: string): ProgressEvent | null => {
    try {
      const parsed = JSON.parse(message) as unknown;
      if (
        parsed !== null &&
        typeof parsed === "object" &&
        "status" in parsed &&
        "progress" in parsed
      ) {
        return parsed as ProgressEvent;
      }
    } catch {
      // JSON でないメッセージはそのままテキストとして扱います
    }
    return null;
  }, []);

  const handleUploaded = useCallback(
    async (newJobId: string, uploadedFiles: string[], uploadTiming?: UploadTimingInfo) => {
      reset();
      setJobId(newJobId);
      setFiles(uploadedFiles);
      const overallStart = uploadTiming?.uploadStart ?? new Date().toISOString();
      setProgressLog([`画像を ${uploadedFiles.length} 枚検出しました`]);
      setIsLoading(true);
      setTimingDebug(() => ({
        zipUpload: uploadTiming
          ? {
              start: uploadTiming.uploadStart,
              end: uploadTiming.uploadEnd,
              elapsedMs: uploadTiming.elapsedMs,
            }
          : { start: null, end: null, elapsedMs: null },
        ocrTotal: { start: null, end: null, elapsedMs: null },
        ocrPages: uploadedFiles.map((fileName, index) => ({
          pageIndex: index,
          fileName,
          start: null,
          end: null,
          elapsedMs: null,
        })),
        pdfGeneration: { start: null, end: null, elapsedMs: null },
        overall: { start: overallStart, end: null, elapsedMs: null },
      }));

      // 進捗イベントからタイミング情報を更新する補助関数です。
      const updateTimingDebug = (event: ProgressEvent) => {
        const now = new Date();
        // SY002003: backend/frontend/ocr-worker 間で UTC の秒精度 ISO 8601 を統一します
        const nowIso = now.toISOString().split(".")[0] + "Z";

        setTimingDebug((prev) => {
          const next: TimingDebugInfo = JSON.parse(JSON.stringify(prev));

          // processing イベントのたびに overall の終了時刻をリセットします。
          // これにより、重複イベントやポーリング遅延による stale な overall.end を防ぎます。
          if (event.status === "processing") {
            next.overall.end = null;
            next.overall.elapsedMs = null;
          }

          // SY002003: ocr-worker から送信された per-page タイミングをそのまま使用します。
          // frontend 側の推定やフォールバックは行いません。
          if (event.ocrPages && event.ocrPages.length > 0) {
            next.ocrPages = event.ocrPages.map((page) => ({
              pageIndex: page.pageIndex,
              fileName: page.fileName,
              start: page.start ?? null,
              end: page.end ?? null,
              elapsedMs: page.elapsedMs ?? null,
            }));
          }

          // 初回 processing イベント受信時に OCR 総時間の開始を無条件で記録します。
          if (!next.ocrTotal.start) {
            next.ocrTotal.start = event.timestamp || nowIso;
          }

          // PDF 生成開始を検出します（progress 75% 以上）。
          if (
            event.progress >= 0.75 &&
            event.status === "processing" &&
            !next.pdfGeneration.start
          ) {
            next.pdfGeneration.start = nowIso;
            // 1 枚目画像 OCR 開始から最終画像 OCR 完了までの総時間を確定します。
            if (next.ocrTotal.start && !next.ocrTotal.end) {
              next.ocrTotal.end = nowIso;
              next.ocrTotal.elapsedMs =
                now.getTime() - new Date(next.ocrTotal.start).getTime();
            }
          }

          // ジョブが完了・失敗・キャンセルされたら、全体の終了時刻を確定します。
          if (
            event.status === "completed" ||
            event.status === "failed" ||
            event.status === "cancelled"
          ) {
            // OCR 総時間の end が未設定であれば補完します。
            if (next.ocrTotal.start && !next.ocrTotal.end) {
              next.ocrTotal.end = nowIso;
              next.ocrTotal.elapsedMs =
                now.getTime() - new Date(next.ocrTotal.start).getTime();
            }

            next.overall.end = nowIso;
            if (next.overall.start) {
              next.overall.elapsedMs =
                now.getTime() - new Date(next.overall.start).getTime();
            }
            if (next.pdfGeneration.start && !next.pdfGeneration.end) {
              next.pdfGeneration.end = nowIso;
              next.pdfGeneration.elapsedMs =
                now.getTime() - new Date(next.pdfGeneration.start).getTime();
            }
          }

          return next;
        });
      };

      // 進捗イベントの共通ハンドラです。SSE と polling の両方で使用します。
      const handleProgressMessage = (message: string) => {
        const event = parseProgressEvent(message);
        if (event) {
          setLatestProgress(event);
          const text =
            event.message ??
            `${event.status} - ${Math.round(event.progress * 100)}% (${event.current_page}/${event.total_pages})`;
          setProgressLog((prev) => [...prev, text]);

          // デバッグ用のタイミング情報を更新します。
          // SSE と polling の重複イベントを区別するため、ページ番号の変化を基準にします。
          updateTimingDebug(event);

          // 終了状態になったらローディングを解除します
          if (event.status === "completed" || event.status === "failed" || event.status === "cancelled") {
            setIsLoading(false);
          }
          // PDF ダウンロードは OCR/PDF 生成が完了してから有効にします
          if (event.status === "completed") {
            setDownloadableJobId(newJobId);
          }
        } else {
          setProgressLog((prev) => [...prev, message]);
        }
      };

      // SSE エラー時に polling にフォールバックします
      const startPollingFallback = () => {
        setProgressLog((prev) => [...prev, "プロキシ環境を検出しました。ポーリング方式に切り替えます…"]);
        pollStopRef.current = pollJobProgress(
          newJobId,
          handleProgressMessage,
          (pollErr) => {
            console.error("ポーリングでエラーが発生しました:", pollErr);
            setProgressLog((prev) => [...prev, `ポーリングでエラーが発生しました: ${pollErr.message}`]);
            setError(pollErr.message);
            cleanupProgress();
          },
          () => {
            cleanupProgress();
          },
        );
      };

      try {
        eventSourceRef.current = subscribeJobProgress(
          newJobId,
          handleProgressMessage,
          () => {
            // SSE 接続エラー時は polling にフォールバックします
            setProgressLog((prev) => [...prev, "進捗通知の接続でエラーが発生しました"]);
            cleanupProgress();
            startPollingFallback();
          },
          () => {
            cleanupProgress();
          },
        );

        await runOcr(newJobId);
      } catch (err) {
        setError(err instanceof Error ? err.message : "不明なエラーが発生しました");
        cleanupProgress();
        setIsLoading(false);
      }
    },
    [reset, parseProgressEvent, cleanupProgress],
  );

  const handleCancel = useCallback(async () => {
    if (!jobId) {
      return;
    }

    cleanupProgress();

    try {
      await cancelJob(jobId);
      setLatestProgress({
        job_id: jobId,
        status: "cancelled",
        progress: 0,
        current_page: 0,
        total_pages: files.length,
        message: "ジョブをキャンセルしました",
        timestamp: new Date().toISOString(),
      });
      setProgressLog((prev) => [...prev, "ジョブをキャンセルしました"]);
      setDownloadableJobId(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "不明なエラーが発生しました";
      setError(message);
      setProgressLog((prev) => [...prev, `キャンセルに失敗しました: ${message}`]);
    } finally {
      setIsLoading(false);
    }
  }, [jobId, files.length, cleanupProgress]);

  useEffect(() => {
    return () => {
      cleanupProgress();
    };
  }, [cleanupProgress]);

  return {
    jobId,
    files,
    latestProgress,
    progressLog,
    error,
    isLoading,
    downloadableJobId,
    timingDebug,
    handleUploaded,
    handleCancel,
    reset,
  };
}
