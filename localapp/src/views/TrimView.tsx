/**
 * トリミング機能のメインビュー
 *
 * 【004001改修版】
 * 1ページプレビュー + 前次ページナビゲーション + トリミング調整UI を提供する。
 *
 * 【レイアウト】
 * ┌──────────────────────────────────────┐
 * │ ヘッダー（タイトル + フォルダパス）   │
 * ├──────────────────────────────────────┤
 * │ [フォルダ選択]  3 / 25 ページ        │
 * ├──────────────────────────────────────┤
 * │                                      │
 * │     [上]                            │
 * │                                      │
 * │  [左]  [プレビュー画像]  [右]        │
 * │                                      │
 * │     [下]                            │
 * │                                      │
 * ├──────────────────────────────────────┤
 * │ [< 前ページ] [プレビューに反映] [次ページ >]│
 * └──────────────────────────────────────┘
 *
 * 完全なトリミング機能（余白検出・BeforeAfter プレビュー・一括実行）は
 * UC004（004002〜004005）で実装予定。
 */

import { useEffect } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { useCaptureStore } from "@/store/captureStore";
import { useTrimStore } from "@/store/trimStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  FolderInput,
  Scissors,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Eye,
} from "lucide-react";

/**
 * トリミングビューコンポーネント
 *
 * @returns トリミング画面の JSX
 */
export function TrimView() {
  // captureStore から最後のキャプチャ結果を取得（002004 連携用）
  const lastCaptureFolder = useCaptureStore((state) => state.lastCaptureFolder);

  // trimStore からトリミング画面の状態を取得
  const folderPath = useTrimStore((state) => state.folderPath);
  const imageFiles = useTrimStore((state) => state.imageFiles);
  const currentImageIndex = useTrimStore((state) => state.currentImageIndex);
  const cropInsets = useTrimStore((state) => state.cropInsets);
  const previewImage = useTrimStore((state) => state.previewImage);
  const isPreviewLoading = useTrimStore((state) => state.isPreviewLoading);
  const isLoading = useTrimStore((state) => state.isLoading);
  const error = useTrimStore((state) => state.error);
  const loadFolder = useTrimStore((state) => state.loadFolder);
  const prevPage = useTrimStore((state) => state.prevPage);
  const nextPage = useTrimStore((state) => state.nextPage);
  const setCropInsets = useTrimStore((state) => state.setCropInsets);
  const resetCropInsets = useTrimStore((state) => state.resetCropInsets);
  const loadPreview = useTrimStore((state) => state.loadPreview);

  // 表示用のフォルダパス（trimStore > captureStore の優先順位）
  const effectiveFolderPath = folderPath || lastCaptureFolder;

  /**
   * 002004 連携: captureStore.lastCaptureFolder の変更を監視し、
   * trimStore に自動反映する。
   *
   * lastCaptureFolder が存在し、かつ trimStore の folderPath と異なる場合のみ
   * loadFolder() を呼び出す。これによりキャプチャタブからの自動引継ぎと、
   * 手動フォルダ選択が正しく共存する。
   */
  useEffect(() => {
    if (lastCaptureFolder && lastCaptureFolder !== folderPath) {
      loadFolder(lastCaptureFolder);
    }
  }, [lastCaptureFolder, folderPath, loadFolder]);

  /**
   * 現在のページインデックスが変わったら、プレビュー画像を自動読み込みする。
   *
   * ページを移動するたびに自動的にプレビューを更新する。
   * トリミング値の変更時は自動更新しない（「プレビューに反映」ボタンで手動更新）。
   */
  useEffect(() => {
    if (effectiveFolderPath && imageFiles.length > 0) {
      loadPreview();
    }
  }, [currentImageIndex, effectiveFolderPath, imageFiles.length, loadPreview]);

  /**
   * フォルダ選択ダイアログを開き、選択したフォルダを trimStore に読み込む
   */
  async function handleSelectFolder() {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
      });
      if (selected && typeof selected === "string") {
        await loadFolder(selected);
      }
    } catch (err) {
      console.error("フォルダ選択エラー:", err);
    }
  }

  /**
   * トリミング値の入力変更ハンドラ
   *
   * @param side - 変更する辺（top / right / bottom / left）
   * @param value - 入力文字列
   */
  function handleCropChange(
    side: "top" | "right" | "bottom" | "left",
    value: string
  ) {
    const num = parseInt(value, 10);
    setCropInsets({ [side]: isNaN(num) ? 0 : Math.max(0, num) });
  }

  // 画像枚数が 0 の場合は「未選択」と表示
  const pageCounter =
    imageFiles.length > 0
      ? `${currentImageIndex + 1} / ${imageFiles.length} ページ`
      : "画像なし";

  return (
    <div className="flex h-full flex-col p-6 gap-5 overflow-auto">
      {/* ── ヘッダーセクション ───────────────────────── */}
      <div>
        <h2 className="text-xl font-semibold tracking-tight">トリミング</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          キャプチャまたは PDF 展開した画像から余白を削除します。
        </p>
      </div>

      {/* ── フォルダ選択 + ページカウンター ─────────────────── */}
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          onClick={handleSelectFolder}
          className="gap-2"
        >
          <FolderInput className="h-4 w-4" />
          フォルダを選択
        </Button>
        {imageFiles.length > 0 && (
          <span className="text-sm text-muted-foreground">{pageCounter}</span>
        )}
      </div>

      {/* ── 読み込み中インジケータ ───────────────────────── */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            画像を読み込み中...
          </div>
        </div>
      )}

      {/* ── エラー表示 ───────────────────────── */}
      {error && (
        <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          画像読み込みエラー: {error}
        </div>
      )}

      {/* ── メインコンテンツ：プレビュー + トリミング入力 ─────── */}
      {effectiveFolderPath && !isLoading && imageFiles.length > 0 && (
        <section className="flex flex-col gap-5 rounded-lg border bg-card p-5 shadow-sm">
          {/* セクションヘッダー */}
          <div className="flex items-center gap-2">
            <Scissors className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-medium">
              {folderPath ? "選択したフォルダ" : "キャプチャ結果を読み込みました"}
            </h3>
          </div>

          {/* ── 十字レイアウト：トリミング入力 + プレビュー ── */}
          <div className="grid grid-cols-3 gap-x-6 gap-y-3 justify-items-center">
            {/* Row 1: empty | 上 | empty */}
            <div />
            <div className="flex flex-col items-center space-y-1">
              <Label className="text-xs">上 (px)</Label>
              <Input
                type="number"
                min="0"
                step="1"
                className="max-w-[80px] text-center"
                value={String(cropInsets.top)}
                onChange={(e) => handleCropChange("top", e.target.value)}
              />
            </div>
            <div />

            {/* Row 2: 左 | プレビュー | 右 */}
            <div className="flex flex-col items-center space-y-1">
              <Label className="text-xs">左 (px)</Label>
              <Input
                type="number"
                min="0"
                step="1"
                className="max-w-[80px] text-center"
                value={String(cropInsets.left)}
                onChange={(e) => handleCropChange("left", e.target.value)}
              />
            </div>

            {/* 中央：プレビュー画像 */}
            <div className="flex flex-col items-center justify-center space-y-2 w-full h-full min-h-[240px]">
              {isPreviewLoading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  読み込み中...
                </div>
              ) : previewImage ? (
                <div className="overflow-auto max-w-full max-h-[360px] rounded border">
                  <img
                    src={previewImage}
                    alt={`ページ ${currentImageIndex + 1}`}
                    className="object-contain"
                    style={{ maxHeight: "360px", maxWidth: "100%" }}
                  />
                </div>
              ) : (
                <span className="text-xs text-muted-foreground">
                  プレビューを読み込んでください
                </span>
              )}
            </div>

            <div className="flex flex-col items-center space-y-1">
              <Label className="text-xs">右 (px)</Label>
              <Input
                type="number"
                min="0"
                step="1"
                className="max-w-[80px] text-center"
                value={String(cropInsets.right)}
                onChange={(e) => handleCropChange("right", e.target.value)}
              />
            </div>

            {/* Row 3: empty | 下 | empty */}
            <div />
            <div className="flex flex-col items-center space-y-1">
              <Label className="text-xs">下 (px)</Label>
              <Input
                type="number"
                min="0"
                step="1"
                className="max-w-[80px] text-center"
                value={String(cropInsets.bottom)}
                onChange={(e) => handleCropChange("bottom", e.target.value)}
              />
            </div>
            <div />
          </div>

          {/* ── 説明文 + リセットボタン ── */}
          <div className="flex items-center justify-center gap-3">
            <p className="text-xs text-muted-foreground">
              外枠から内部に向かって切り取るピクセル数（0 = トリミングなし）
            </p>
            <Button
              variant="ghost"
              size="sm"
              className="gap-1 h-7 text-xs"
              onClick={resetCropInsets}
            >
              <RotateCcw className="h-3 w-3" />
              リセット
            </Button>
          </div>

          {/* ── ナビゲーション + プレビュー更新ボタン ── */}
          <div className="flex items-center justify-center gap-3 pt-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-1"
              onClick={prevPage}
              disabled={currentImageIndex <= 0}
            >
              <ChevronLeft className="h-4 w-4" />
              前ページ
            </Button>

            <Button
              variant="default"
              size="sm"
              className="gap-1"
              onClick={loadPreview}
              disabled={isPreviewLoading}
            >
              <Eye className="h-3.5 w-3.5" />
              プレビューに反映
            </Button>

            <Button
              variant="outline"
              size="sm"
              className="gap-1"
              onClick={nextPage}
              disabled={currentImageIndex >= imageFiles.length - 1}
            >
              次ページ
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </section>
      )}

      {/* ── フォルダ未選択時のプレースホルダ ───────────────────────── */}
      {!effectiveFolderPath && !isLoading && (
        <section className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed bg-card p-10">
          <Scissors className="h-8 w-8 text-muted-foreground/50" />
          <div className="text-center">
            <p className="text-sm font-medium text-muted-foreground">
              画像フォルダが選択されていません
            </p>
            <p className="mt-1 text-xs text-muted-foreground/70">
              「電子書籍」タブでキャプチャを完了すると、結果が自動的にここに表示されます。
              <br />
              または「フォルダを選択」ボタンから既存の画像フォルダを読み込んでください。
            </p>
          </div>
        </section>
      )}

      {/* ── 画像0枚時の表示 ───────────────────────── */}
      {effectiveFolderPath && !isLoading && imageFiles.length === 0 && (
        <section className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed bg-card p-10">
          <Scissors className="h-8 w-8 text-muted-foreground/50" />
          <div className="text-center">
            <p className="text-sm font-medium text-muted-foreground">
              フォルダ内に画像が見つかりません
            </p>
            <p className="mt-1 text-xs text-muted-foreground/70">
              選択したフォルダに PNG / JPG 画像が含まれているか確認してください。
            </p>
          </div>
        </section>
      )}
    </div>
  );
}
