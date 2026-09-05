"use client";

// book2pdf Web OCR/PDF システムのメインページです
// ZIP アップロードから OCR 実行、PDF ダウンロードまでをブラウザ上で操作できます

// React のフック（状態管理・参照保持）を読み込み
// useState: ファイル・ジョブ ID 等の状態管理, useRef: SSE 接続の参照保持
import { useState, useRef } from "react";
// FastAPI バックエンド通信用 API 関数群を読み込み
// createJob: ジョブ作成, uploadZip: ZIP アップロード, runOcr: OCR 実行,
// subscribeJobProgress: 進捗購読（SSE）, downloadPdf: PDF ダウンロード
import {
  createJob,
  uploadZip,
  runOcr,
  subscribeJobProgress,
  downloadPdf,
} from "@/lib/api";
import type { ProgressEvent } from "@/types";

export default function Home() {
  // 選択された ZIP ファイルを保持する state です
  const [file, setFile] = useState<File | null>(null);
  // ジョブ ID を保持する state です
  const [jobId, setJobId] = useState<string | null>(null);
  // アップロードされた画像ファイル一覧を保持する state です
  const [files, setFiles] = useState<string[]>([]);
  // 最新の進捗イベントを保持する state です
  const [latestProgress, setLatestProgress] = useState<ProgressEvent | null>(null);
  // 時系列順の進捗メッセージログを保持する state です
  const [progressLog, setProgressLog] = useState<string[]>([]);
  // OCR 完了後の結果メッセージを保持する state です
  const [result, setResult] = useState<string>("");
  // エラーメッセージを保持する state です
  const [error, setError] = useState<string>("");
  // 処理中かどうかを判定する state です
  const [isLoading, setIsLoading] = useState<boolean>(false);
  // PDF ダウンロード可能なジョブ ID を保持する state です
  const [downloadableJobId, setDownloadableJobId] = useState<string | null>(null);
  // EventSource インスタンスを保持する ref です
  const eventSourceRef = useRef<EventSource | null>(null);

  /**
   * ファイル選択 input の変更を処理します
   */
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
    setError("");
  };

  /**
   * ジョブ作成 → ZIP アップロード → OCR 実行の一連の処理を行います
   */
  const handleSubmit = async () => {
    if (!file) {
      setError("ZIP ファイルを選択してください");
      return;
    }

    setIsLoading(true);
    setError("");
    setLatestProgress(null);
    setProgressLog([]);
    setResult("");
    setDownloadableJobId(null);

    try {
      // ジョブを作成します
      const newJobId = await createJob();
      setJobId(newJobId);
      setProgressLog((prev) => [...prev, `ジョブを作成しました: ${newJobId}`]);

      // ZIP ファイルをアップロードします
      const uploadedFiles = await uploadZip(newJobId, file);
      setFiles(uploadedFiles);
      setProgressLog((prev) => [...prev, `画像を ${uploadedFiles.length} 枚検出しました`]);

      // 進捗通知を購読します
      eventSourceRef.current = subscribeJobProgress(
        newJobId,
        (message) => {
          // バックエンドからの JSON イベントをパースして表示します
          let event: ProgressEvent | null = null;
          try {
            const parsed = JSON.parse(message) as unknown;
            if (
              parsed !== null &&
              typeof parsed === "object" &&
              "job_id" in parsed &&
              "status" in parsed &&
              "progress" in parsed
            ) {
              event = parsed as ProgressEvent;
            }
          } catch {
            // JSON でないメッセージはそのままテキストとして扱います
          }

          if (event) {
            setLatestProgress(event);
            const text =
              event.message ??
              `${event.status} - ${event.progress}% (${event.current_page}/${event.total_pages})`;
            setProgressLog((prev) => [...prev, text]);
          } else {
            setProgressLog((prev) => [...prev, message]);
          }
        },
        (err) => {
          // EventSource のエラーは一時的な切断も含むため、OCR 結果を待つ形にします
          console.error("進捗通知の接続でエラーが発生しました:", err);
          setProgressLog((prev) => [...prev, "進捗通知の接続でエラーが発生しました"]);
          if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
          }
        },
        () => {
          setProgressLog((prev) => [...prev, "進捗通知が完了しました"]);
          if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
          }
        }
      );

      // OCR 処理を実行します
      const ocrResult = await runOcr(newJobId);
      setResult(JSON.stringify(ocrResult, null, 2));
      setDownloadableJobId(newJobId);
      setProgressLog((prev) => [...prev, "OCR 処理が完了しました"]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "不明なエラーが発生しました");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-2xl space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            book2pdf
          </h1>
          <p className="mt-2 text-lg text-muted-foreground">
            ZIP 画像から OCR 処理を行い、検索可能 PDF を生成します
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <label
            htmlFor="zip-upload"
            className="block text-sm font-medium text-card-foreground"
          >
            ZIP ファイルを選択
          </label>
          <input
            id="zip-upload"
            type="file"
            accept=".zip,application/zip"
            onChange={handleFileChange}
            disabled={isLoading}
            className="mt-2 block w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground file:mr-4 file:rounded-full file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-medium file:text-primary-foreground hover:file:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          />
          {file && (
            <p className="mt-2 text-sm text-muted-foreground">
              選択ファイル: {file.name}
            </p>
          )}

          <button
            onClick={handleSubmit}
            disabled={!file || isLoading}
            className="mt-4 w-full rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? "処理中..." : "アップロードして OCR 実行"}
          </button>

          {error && (
            <div className="mt-4 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
              {error}
            </div>
          )}
        </div>

        {jobId && (
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-card-foreground">ジョブ情報</h2>
            <p className="mt-1 text-sm text-muted-foreground">ジョブ ID: {jobId}</p>
            {files.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium text-card-foreground">
                  アップロードされた画像
                </h3>
                <ul className="mt-1 max-h-32 overflow-auto rounded-lg border border-border bg-background p-2 text-sm text-foreground">
                  {files.map((name) => (
                    <li key={name}>{name}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {(latestProgress || progressLog.length > 0) && (
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-card-foreground">進捗</h2>
            {latestProgress && (
              <div className="mt-3 space-y-2">
                <div className="flex items-center justify-between text-sm text-card-foreground">
                  <span>状態: {latestProgress.status}</span>
                  <span>
                    {latestProgress.current_page} / {latestProgress.total_pages} ページ
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary transition-all duration-500 ease-out"
                    style={{
                      width: `${Math.min(100, Math.max(0, latestProgress.progress))}%`,
                    }}
                  />
                </div>
                <p className="text-sm text-muted-foreground">
                  {latestProgress.progress}%
                </p>
              </div>
            )}
            {progressLog.length > 0 && (
              <pre className="mt-4 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-background p-3 text-sm text-foreground">
                {progressLog.join("\n")}
              </pre>
            )}
          </div>
        )}

        {result && (
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-card-foreground">OCR 結果</h2>
            <pre className="mt-2 max-h-64 overflow-auto rounded-lg border border-border bg-background p-3 text-sm text-foreground">
              {result}
            </pre>
          </div>
        )}

        {downloadableJobId && (
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm text-center">
            <button
              onClick={() => downloadPdf(downloadableJobId)}
              className="inline-flex items-center justify-center rounded-lg bg-primary px-6 py-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              PDF をダウンロード
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
