"use client";

// OCR ジョブの実行進捗管理を担当するカスタムフックです。
// ZIP アップロード完了後の OCR 実行、SSE 進捗購読、PDF ダウンロード可能状態の
// 管理を一括して行います。

import { useCallback, useEffect, useRef, useState } from "react";
import { runOcr, subscribeJobProgress, pollJobProgress } from "@/lib/api";
import type { ProgressEvent } from "@/types";

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
  /** OCR 結果の文字列表現です。 */
  result: string;
  /** エラーメッセージです。 */
  error: string;
  /** 処理中フラグです。 */
  isLoading: boolean;
  /** PDF ダウンロード可能なジョブ ID です。 */
  downloadableJobId: string | null;
  /** ZIP アップロード完了後に OCR 処理を開始します。 */
  handleUploaded: (jobId: string, files: string[]) => Promise<void>;
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
  const [result, setResult] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [downloadableJobId, setDownloadableJobId] = useState<string | null>(null);
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
    setResult("");
    setError("");
    setIsLoading(false);
    setDownloadableJobId(null);
  }, [cleanupProgress]);

  const parseProgressEvent = useCallback((message: string): ProgressEvent | null => {
    try {
      const parsed = JSON.parse(message) as unknown;
      if (
        parsed !== null &&
        typeof parsed === "object" &&
        "job_id" in parsed &&
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
    async (newJobId: string, uploadedFiles: string[]) => {
      reset();
      setJobId(newJobId);
      setFiles(uploadedFiles);
      setProgressLog([
        `ジョブを作成しました: ${newJobId}`,
        `画像を ${uploadedFiles.length} 枚検出しました`,
      ]);
      setIsLoading(true);

      // 進捗イベントの共通ハンドラです。SSE と polling の両方で使用します。
      const handleProgressMessage = (message: string) => {
        const event = parseProgressEvent(message);
        if (event) {
          setLatestProgress(event);
          const text =
            event.message ??
            `${event.status} - ${Math.round(event.progress * 100)}% (${event.current_page}/${event.total_pages})`;
          setProgressLog((prev) => [...prev, text]);

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
            setProgressLog((prev) => [...prev, "ポーリングによる進捗監視が完了しました"]);
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
            setProgressLog((prev) => [...prev, "進捗通知が完了しました"]);
            cleanupProgress();
          },
        );

        const ocrResult = await runOcr(newJobId);
        setResult(JSON.stringify(ocrResult, null, 2));
      } catch (err) {
        setError(err instanceof Error ? err.message : "不明なエラーが発生しました");
        cleanupProgress();
      } finally {
        setIsLoading(false);
      }
    },
    [reset, parseProgressEvent, cleanupProgress],
  );

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
    result,
    error,
    isLoading,
    downloadableJobId,
    handleUploaded,
    reset,
  };
}
