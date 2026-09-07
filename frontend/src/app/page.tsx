"use client";

// book2pdf Web OCR/PDF システムのメインページです
// ZIP アップロードから OCR 実行、PDF ダウンロードまでをブラウザ上で操作できます

import { ZipUploadForm } from "@/components/upload/ZipUploadForm";
import { useOcrJob } from "@/hooks/useOcrJob";

export default function Home() {
  const {
    jobId,
    files,
    latestProgress,
    progressLog,
    result,
    error,
    downloadableJobId,
    handleUploaded,
    download,
  } = useOcrJob();

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-2xl space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground">book2pdf</h1>
          <p className="mt-2 text-muted-foreground">
            ZIP 画像をアップロードして OCR → PDF 変換
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-card-foreground">ZIP アップロード</h2>
          <div className="mt-4">
            <ZipUploadForm onUploaded={handleUploaded} />
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
            {error}
          </div>
        )}

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
                <p className="text-sm text-muted-foreground">{latestProgress.progress}%</p>
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
              onClick={download}
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
