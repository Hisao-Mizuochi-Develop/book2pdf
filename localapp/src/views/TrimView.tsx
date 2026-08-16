/**
 * トリミング機能のメインビュー
 *
 * 【002004: キャプチャ画像のフォルダ管理連携版】
 * キャプチャタブで完了した連続キャプチャ結果を自動的に引き継ぐ。
 * captureStore の lastCaptureFolder を監視し、存在する場合は
 * CaptureResultGallery でサムネイル一覧を表示する。
 *
 * 完全なトリミング機能（余白検出・BeforeAfter プレビュー・一括実行）は
 * UC004（004001〜004005）で実装予定。現時点では結果確認と手動フォルダ選択の
 * 土台を提供する。
 *
 * 【レイアウト】
 * ┌──────────────────────────────┐
 * │ ヘッダー（タイトル + フォルダパス）│
 * ├──────────────────────────────┤
 * │ キャプチャ結果引継ぎ表示       │
 * │ [サムネイルグリッド]           │
 * │ または                        │
 * │ 「フォルダを選択」ボタン       │
 * └──────────────────────────────┘
 */

import { useCaptureStore } from "@/store/captureStore";
import { CaptureResultGallery } from "@/components/capture/CaptureResultGallery";
import { Button } from "@/components/ui/button";
import { FolderOpen, Scissors } from "lucide-react";
import { invoke } from "@tauri-apps/api/core";

/**
 * トリミングビューコンポーネント
 *
 * @returns トリミング画面の JSX
 */
export function TrimView() {
  // captureStore から最後のキャプチャ結果を取得（002004 連携用）
  const lastCaptureFolder = useCaptureStore((state) => state.lastCaptureFolder);
  const lastCaptureImageCount = useCaptureStore(
    (state) => state.lastCaptureImageCount
  );

  /**
   * キャプチャフォルダを OS のファイルマネージャーで開く
   */
  async function handleOpenFolder() {
    if (!lastCaptureFolder) return;
    try {
      await invoke("open_capture_folder", { folderPath: lastCaptureFolder });
    } catch (err) {
      console.error("フォルダを開けません:", err);
    }
  }

  return (
    <div className="flex h-full flex-col p-6 gap-5 overflow-auto">
      {/* ── ヘッダーセクション ───────────────────────── */}
      <div>
        <h2 className="text-xl font-semibold tracking-tight">トリミング</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          キャプチャまたは PDF 展開した画像から余白を削除します。
        </p>
      </div>

      {/* ── キャプチャ結果引継ぎ（002004）──────────────────────── */}
      {lastCaptureFolder ? (
        <section className="space-y-4 rounded-lg border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <Scissors className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-medium">キャプチャ結果を読み込みました</h3>
          </div>
          <CaptureResultGallery
            folderPath={lastCaptureFolder}
            imageCount={lastCaptureImageCount}
            onOpenFolder={handleOpenFolder}
            onGoTrim={() => {
              // 将来的にトリミング実行画面へ遷移（004001〜で実装）
              console.log("トリミング実行画面へ（将来実装）");
            }}
          />
        </section>
      ) : (
        /* ── フォルダ未選択時のプレースホルダ ───────────────────────── */
        <section className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed bg-card p-10">
          <Scissors className="h-8 w-8 text-muted-foreground/50" />
          <div className="text-center">
            <p className="text-sm font-medium text-muted-foreground">
              画像フォルダが選択されていません
            </p>
            <p className="mt-1 text-xs text-muted-foreground/70">
              「電子書籍」タブでキャプチャを完了すると、結果が自動的にここに表示されます。
            </p>
          </div>
          <Button variant="outline" disabled className="gap-2">
            <FolderOpen className="h-4 w-4" />
            フォルダを選択（将来実装）
          </Button>
        </section>
      )}
    </div>
  );
}
