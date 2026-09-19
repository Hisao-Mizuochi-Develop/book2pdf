"use client";

// book2pdf Web OCR/PDF システムのメインページです
// ZIP アップロードから OCR 実行、PDF ダウンロードまでをブラウザ上で操作できます
// 各機能は独立したコンポーネントに委譲し、本ファイルは統合のみを担当します

import { DebugTimingPanel } from "@/components/debug/DebugTimingPanel";
import { ProgressPanel } from "@/components/progress";
import { ZipUploadForm } from "@/components/upload/ZipUploadForm";
import { useDebugConfig } from "@/hooks/useDebugConfig";
import { useOcrJob } from "@/hooks/useOcrJob";
import { downloadPdf } from "@/lib/api";

export default function Home() {
  const {
    latestProgress,
    error,
    downloadableJobId,
    jobId,
    timingDebug,
    handleUploaded,
    handleCancel,
    reset,
  } = useOcrJob();
  const { showDebugTimingPanel } = useDebugConfig();

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

        <ProgressPanel
          latest={latestProgress}
          error={error}
          jobId={jobId}
          onDownload={async () => {
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

              // ダウンロード成功後は初期画面に戻します
              reset();
            } catch (error) {
              // ユーザーが保存ダイアログをキャンセルした場合は無視します
              if (error instanceof DOMException && error.name === "AbortError") {
                return;
              }
              console.error("PDF ダウンロードに失敗しました:", error);
            }
          }}
          onCancel={handleCancel}
        />

        {showDebugTimingPanel && <DebugTimingPanel timing={timingDebug} />}
      </div>
    </main>
  );
}
