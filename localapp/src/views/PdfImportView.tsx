/**
 * PDF 読込機能のメインビュー
 *
 * 【ユースケース 003 — PDF 読込】
 * 外部 PDF ファイルを PNG 画像に展開し、トリミングタブに自動引き継ぐ。
 *
 * 【レイアウト】
 * ┌─────────────────────────────────────────────────────┐
 * │ ヘッダー（PDF読込）                                    │
 * ├─────────────────────────────────────────────────────┤
 * │ [PDFファイルを選択]  選択済みパス表示                  │
 * │ [出力先フォルダを選択]  選択済みパス表示               │
 * ├─────────────────────────────────────────────────────┤
 * │ 解像度（DPI）: [200 ▼] [300 ▼] [400 ▼]              │
 * │ ファイルサイズ目安: 約 2.5 MB / ページ（300 DPI）     │
 * ├─────────────────────────────────────────────────────┤
 * │ [PDF を画像化]                                        │
 * ├─────────────────────────────────────────────────────┤
 * │ 進捗バー: 5 / 120 ページ                               │
 * └─────────────────────────────────────────────────────┘
 */

import { FileUp, FolderInput, FileText, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CaptureResultGallery } from "@/components/capture/CaptureResultGallery";
import {
  usePdfImportStore,
  PDF_DPI_OPTIONS,
  estimatePdfImageSize,
} from "@/store/pdfImportStore";

/**
 * PDF 読込ビューコンポーネント
 *
 * @returns PDF 読込画面の JSX
 */
export function PdfImportView() {
  // PDF 読込ストアから状態とアクションを取得
  const pdfPath = usePdfImportStore((state) => state.pdfPath);
  const outputFolder = usePdfImportStore((state) => state.outputFolder);
  const dpi = usePdfImportStore((state) => state.dpi);
  const isLoading = usePdfImportStore((state) => state.isLoading);
  const progressCurrent = usePdfImportStore((state) => state.progressCurrent);
  const progressTotal = usePdfImportStore((state) => state.progressTotal);
  const progressMessage = usePdfImportStore((state) => state.progressMessage);
  const error = usePdfImportStore((state) => state.error);
  const result = usePdfImportStore((state) => state.result);
  const selectPdf = usePdfImportStore((state) => state.selectPdf);
  const selectOutputFolder = usePdfImportStore(
    (state) => state.selectOutputFolder
  );
  const setDpi = usePdfImportStore((state) => state.setDpi);
  const extractPdf = usePdfImportStore((state) => state.extractPdf);
  const openOutputFolder = usePdfImportStore(
    (state) => state.openOutputFolder
  );
  const goToTrim = usePdfImportStore((state) => state.goToTrim);

  // ファイルサイズ目安の計算
  // ページ数はまだ不明なため、1 ページあたりの目安を表示する。
  // 変換中に total が判明したら合計サイズを表示する。
  const fileSizeEstimate = estimatePdfImageSize(
    dpi,
    progressTotal > 0 ? progressTotal : null
  );

  // 進捗率（0〜100）
  const progressPercent =
    progressTotal > 0
      ? Math.round((progressCurrent / progressTotal) * 100)
      : 0;

  return (
    <div className="flex h-full flex-col p-6 gap-5 overflow-auto">
      {/* ── ヘッダーセクション ───────────────────────── */}
      <div>
        <h2 className="text-xl font-semibold tracking-tight">PDF読込</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          外部 PDF を画像化して、トリミングタブに引き継ぎます。
        </p>
      </div>

      {/* ── エラー表示 ───────────────────────── */}
      {error && (
        <div className="flex items-start gap-2 rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* ── 入力セクション ───────────────────────── */}
      <section className="flex flex-col gap-4 rounded-lg border bg-card p-5 shadow-sm">
        {/* PDF ファイル選択 */}
        <div className="flex flex-col gap-2">
          <Label className="text-sm font-medium">PDF ファイル</Label>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={selectPdf}
              disabled={isLoading}
              className="gap-2 shrink-0"
            >
              <FileUp className="h-4 w-4" />
              PDF を選択
            </Button>
            {pdfPath ? (
              <code
                className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded truncate max-w-full"
                title={pdfPath}
              >
                {pdfPath}
              </code>
            ) : (
              <span className="text-sm text-muted-foreground">
                ファイルが選択されていません
              </span>
            )}
          </div>
        </div>

        {/* 出力先フォルダ選択 */}
        <div className="flex flex-col gap-2">
          <Label className="text-sm font-medium">出力先フォルダ</Label>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={selectOutputFolder}
              disabled={isLoading}
              className="gap-2 shrink-0"
            >
              <FolderInput className="h-4 w-4" />
              フォルダを選択
            </Button>
            {outputFolder ? (
              <code
                className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded truncate max-w-full"
                title={outputFolder}
              >
                {outputFolder}
              </code>
            ) : (
              <span className="text-sm text-muted-foreground">
                出力先フォルダが選択されていません
              </span>
            )}
          </div>
        </div>

        {/* DPI 選択 */}
        <div className="flex flex-col gap-2">
          <Label className="text-sm font-medium">解像度（DPI）</Label>
          <Select
            value={String(dpi)}
            onValueChange={(value) => setDpi(Number(value))}
            disabled={isLoading}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="DPI を選択" />
            </SelectTrigger>
            <SelectContent>
              {PDF_DPI_OPTIONS.map((option) => (
                <SelectItem key={option} value={String(option)}>
                  {option} DPI
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            高いほど画像が鮮明になりますが、ファイルサイズと処理時間が増加します。
          </p>
        </div>

        {/* ファイルサイズ目安 */}
        <div className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">
            ファイルサイズ目安（PNG / 未圧縮）: {fileSizeEstimate}
          </span>
        </div>
      </section>

      {/* ── アクションセクション ───────────────────────── */}
      <section className="flex flex-col gap-3">
        <Button
          onClick={extractPdf}
          disabled={isLoading || !pdfPath || !outputFolder}
          className="w-full sm:w-auto gap-2"
          size="lg"
        >
          {isLoading ? (
            <>
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
              画像化中...
            </>
          ) : (
            <>
              <FileUp className="h-4 w-4" />
              PDF を画像化
            </>
          )}
        </Button>

        {/* 進捗表示 */}
        {isLoading && (
          <div className="flex flex-col gap-3 rounded-lg border bg-card p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <div className="flex flex-col">
                <span className="text-sm font-medium">PDF を画像化しています</span>
                {progressMessage && (
                  <span className="text-xs text-muted-foreground">
                    {progressMessage}
                  </span>
                )}
              </div>
            </div>

            {progressTotal > 0 ? (
              <>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary transition-all duration-300 ease-out"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {progressCurrent} / {progressTotal} ページ
                  </span>
                  <span>{progressPercent}%</span>
                </div>
              </>
            ) : (
              // ページ数が判明する前の不定形プログレス
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full w-1/3 animate-[shimmer_1.5s_infinite] rounded-full bg-primary" />
              </div>
            )}

            <p className="text-xs text-muted-foreground">
              完了後、下に結果が表示されます。
            </p>
          </div>
        )}
      </section>

      {/* ── 完了結果表示 ───────────────────────── */}
      {result && !isLoading && (
        <section className="flex flex-col gap-4 rounded-lg border bg-card p-5 shadow-sm">
          <CaptureResultGallery
            folderPath={result.folderPath}
            imageCount={result.imageCount}
            onOpenFolder={openOutputFolder}
            onGoTrim={goToTrim}
          />
        </section>
      )}
    </div>
  );
}
