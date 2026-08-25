/**
 * OCR 済み PDF 作成画面（PDF作成タブ）
 *
 * 【機能概要】
 * - キャプチャ画像フォルダまたは ZIP ファイルを選択
 * - ZIP の場合は Rust 側で一時フォルダに展開し、処理完了後に削除
 * - 画像（001-999）を昇順に OCR して 1 つの PDF に統合
 * - 進捗インジケータ（current / total）を表示
 * - 完了後は「フォルダを開く」ボタンを表示
 *
 * 【技術仕様】
 * - `tauri-plugin-dialog` の `open()` でフォルダ/ZIP を選択
 * - `invoke("create_searchable_pdf")` で Rust 側コマンドを呼び出し
 * - `listen("pdf-creation-progress")` で進捗イベントを受信
 * - `exportStore` と同様の UI パターンで統一感を持たせる
 */

import { useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { usePdfCreationStore } from "@/store/pdfCreationStore";
import {
  FileText,
  FolderOpen,
  Folder,
  FileArchive,
  RotateCcw,
  BookOpen,
} from "lucide-react";

/**
 * OCR 済み PDF 作成画面コンポーネント
 *
 * Apple HIG 風のデザイン（白基調・余白多め・控えめな角丸）で構築する。
 */
export function PdfCreationView() {
  // ─── pdfCreationStore から状態を取得 ───
  const {
    sourcePath,
    sourceType,
    outputName,
    outputFolder,
    isProcessing,
    progressMessage,
    progressCurrent,
    progressTotal,
    resultPdfPath,
    imageCount,
    setSourcePath,
    setOutputName,
    setOutputFolder,
    setImageCount,
    createPdf,
    reset,
  } = usePdfCreationStore();

  // 進捗率（0〜100）
  const progressPercent =
    progressTotal > 0
      ? Math.round((progressCurrent / progressTotal) * 100)
      : 0;

  /**
   * 入力ソースの変更を監視し、フォルダの場合は画像枚数を取得する
   */
  useEffect(() => {
    if (sourcePath && sourceType === "folder") {
      invoke<string[]>("list_capture_images", { folderPath: sourcePath })
        .then((files) => setImageCount(files.length))
        .catch(() => setImageCount(0));
    }
  }, [sourcePath, sourceType, setImageCount]);

  /**
   * 入力フォルダ選択ダイアログを開く
   */
  const handleSelectSourceFolder = async () => {
    try {
      const selected = await open({ directory: true });
      if (selected && typeof selected === "string") {
        setSourcePath(selected, "folder");
      }
    } catch (err) {
      console.error("フォルダ選択エラー:", err);
    }
  };

  /**
   * ZIP ファイル選択ダイアログを開く
   */
  const handleSelectZipFile = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{ name: "ZIP", extensions: ["zip"] }],
      });
      if (selected && typeof selected === "string") {
        setSourcePath(selected, "zip");
      }
    } catch (err) {
      console.error("ZIP 選択エラー:", err);
    }
  };

  /**
   * 出力先フォルダ選択ダイアログを開く
   */
  const handleSelectOutputFolder = async () => {
    try {
      const selected = await open({ directory: true });
      if (selected && typeof selected === "string") {
        setOutputFolder(selected);
      }
    } catch (err) {
      console.error("出力先選択エラー:", err);
    }
  };

  /**
   * PDF 作成ボタンクリックハンドラ
   */
  const handleCreatePdf = async () => {
    try {
      await createPdf();
    } catch {
      // エラーは store 内で progressMessage に設定されている
    }
  };

  /**
   * 作成された PDF の親フォルダを OS のファイルマネージャーで開く
   */
  const handleOpenResultFolder = async () => {
    if (!resultPdfPath) return;
    const lastSep = resultPdfPath.lastIndexOf("/");
    const lastSepWin = resultPdfPath.lastIndexOf("\\");
    const sepIndex = Math.max(lastSep, lastSepWin);
    const folder = sepIndex > 0 ? resultPdfPath.substring(0, sepIndex) : resultPdfPath;
    try {
      await invoke("open_capture_folder", { folderPath: folder });
    } catch (err) {
      console.error("フォルダを開けません:", err);
    }
  };

  return (
    <div className="flex h-full flex-col gap-6 overflow-auto p-6">
      {/* ─── ヘッダー ─── */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#F5F5F7]">
          <FileText className="h-5 w-5 text-[#007AFF]" />
        </div>
        <div>
          <h2 className="text-xl font-semibold tracking-tight">PDF 作成</h2>
          <p className="text-sm text-muted-foreground">
            キャプチャ画像を OCR して検索可能な PDF を作成します
          </p>
        </div>
      </div>

      {/* ─── 入力設定セクション ─── */}
      <section className="rounded-lg border border-border bg-white p-4">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          <BookOpen className="h-4 w-4 text-muted-foreground" />
          入力設定
        </div>

        {!sourcePath ? (
          // 未選択時: フォルダ or ZIP の二択ボタン
          <div className="mt-3 grid grid-cols-2 gap-3">
            <Button
              variant="outline"
              className="h-16 flex-col gap-1"
              onClick={handleSelectSourceFolder}
            >
              <Folder className="h-5 w-5" />
              <span className="text-xs">フォルダを選択</span>
            </Button>
            <Button
              variant="outline"
              className="h-16 flex-col gap-1"
              onClick={handleSelectZipFile}
            >
              <FileArchive className="h-5 w-5" />
              <span className="text-xs">ZIP ファイルを選択</span>
            </Button>
          </div>
        ) : (
          // 選択済み: パス表示 + 変更ボタン
          <div className="mt-3 space-y-2">
            <div className="flex items-center gap-2">
              <div className="flex-1 rounded-md bg-[#F5F5F7] px-3 py-2 text-sm text-foreground">
                <span className="text-muted-foreground">
                  {sourceType === "folder" ? "フォルダ:" : "ZIP:"}
                </span>{" "}
                <span className="font-mono">{sourcePath}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSourcePath(null, null)}
                disabled={isProcessing}
              >
                <RotateCcw className="mr-1.5 h-4 w-4" />
                変更
              </Button>
            </div>
            {/* 画像枚数表示（フォルダのみ ZIP は展開後に分かる） */}
            {sourceType === "folder" && (
              <p className="text-sm text-muted-foreground">
                画像ファイル:{" "}
                <span className="font-medium text-foreground">{imageCount}</span>{" "}
                枚
              </p>
            )}
            {sourceType === "zip" && (
              <p className="text-sm text-muted-foreground">
                ZIP 展開後の画像数は処理開始時に確認されます
              </p>
            )}
          </div>
        )}
      </section>

      {/* ─── 出力設定セクション ─── */}
      <section className="rounded-lg border border-border bg-white p-4">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          <FileText className="h-4 w-4 text-muted-foreground" />
          出力設定
        </div>
        <div className="mt-3 space-y-4">
          {/* 出力ファイル名 */}
          <div className="space-y-1.5">
            <Label htmlFor="pdf-output-name" className="text-sm font-medium">
              出力ファイル名
            </Label>
            <div className="flex items-center gap-2">
              <Input
                id="pdf-output-name"
                value={outputName}
                onChange={(e) => setOutputName(e.target.value)}
                placeholder="output"
                disabled={isProcessing}
                className="max-w-[240px]"
              />
              <span className="text-sm text-muted-foreground">.pdf</span>
            </div>
          </div>

          {/* 出力先フォルダ */}
          <div className="space-y-1.5">
            <Label className="text-sm font-medium">出力先フォルダ</Label>
            <div className="flex items-center gap-2">
              <div className="flex-1 rounded-md border border-border bg-[#F5F5F7] px-3 py-2 text-sm text-foreground">
                {outputFolder ? (
                  <span className="font-mono">{outputFolder}</span>
                ) : (
                  <span className="text-muted-foreground">フォルダが未選択です</span>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleSelectOutputFolder}
                disabled={isProcessing}
              >
                <Folder className="mr-1.5 h-4 w-4" />
                選択
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* ─── アクションエリア ─── */}
      <div className="flex flex-col gap-3">
        <Button
          className="w-full"
          onClick={handleCreatePdf}
          disabled={!sourcePath || !outputFolder || isProcessing}
          size="lg"
        >
          <FileText className="mr-2 h-4 w-4" />
          {isProcessing ? "PDF 作成中..." : "PDF 作成"}
        </Button>

        {/* 進捗表示 */}
        {isProcessing && (
          <div className="flex flex-col gap-3 rounded-lg border border-border bg-white p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <div className="flex flex-col">
                <span className="text-sm font-medium">OCR 処理を実行しています</span>
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
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full w-1/3 animate-[shimmer_1.5s_infinite] rounded-full bg-primary" />
              </div>
            )}
          </div>
        )}

        {/* 完了後の結果表示 */}
        {resultPdfPath && !isProcessing && (
          <div className="space-y-2">
            <div className="rounded-md border border-border bg-white px-3 py-2 text-sm">
              <span className="text-muted-foreground">作成先:</span>{" "}
              <span className="font-mono">{resultPdfPath}</span>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                className="flex-1"
                onClick={handleOpenResultFolder}
              >
                <FolderOpen className="mr-1.5 h-4 w-4" />
                フォルダを開く
              </Button>
              <Button variant="ghost" size="icon" onClick={reset}>
                <RotateCcw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
