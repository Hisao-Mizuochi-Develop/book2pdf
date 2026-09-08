"use client";

// book2pdf Web OCR/PDF システムのメインページです
// ZIP アップロードから OCR 実行、PDF ダウンロードまでをブラウザ上で操作できます
// 各機能は独立したコンポーネントに委譲し、本ファイルは統合のみを担当します

import { ProgressPanel } from "@/components/progress";
import { ZipUploadForm } from "@/components/upload/ZipUploadForm";
import { useOcrJob } from "@/hooks/useOcrJob";
import { downloadPdf } from "@/lib/api";

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
          <div
            data-testid="job-info-panel"
            className="rounded-2xl border border-border bg-card p-6 shadow-sm"
          >
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

        <ProgressPanel latest={latestProgress} log={progressLog} />

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
              onClick={async () => {
                if (!downloadableJobId) return;

                try {
                  // ユーザージェスチャ（クリック）の文脈内でピッカーを呼び出します。
                  // showSaveFilePicker は同期イベントハンドラから直接呼ぶ必要があり、
                  // ここで await してもブラウザはクリックに起因する最初の await まで
                  // ジェスチャ文脈を維持するため、ダイアログが抑制されません。
                  if (typeof window.showSaveFilePicker === "function") {
                    const handle = await window.showSaveFilePicker({
                      suggestedName: `${downloadableJobId}.pdf`,
                      types: [
                        {
                          description: "PDF ファイル",
                          accept: { "application/pdf": [".pdf"] },
                        },
                      ],
                    });

                    await downloadPdf(downloadableJobId, undefined, handle);
                  } else {
                    // File System Access API 非対応ブラウザでは従来のダウンロード方式にフォールバックします
                    await downloadPdf(downloadableJobId);
                  }
                } catch (error) {
                  // ユーザーが保存ダイアログをキャンセルした場合は無視します
                  if (error instanceof DOMException && error.name === "AbortError") {
                    return;
                  }
                  // eslint-disable-next-line no-console
                  console.error("PDF ダウンロードに失敗しました:", error);
                }
              }}
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
