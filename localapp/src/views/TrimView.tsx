/**
 * トリミング機能のメインビュー
 *
 * 【大幅修正版】
 * Before/After 横並びレイアウト + トリミング調整UI + 前次ページナビゲーション を提供する。
 *
 * 【レイアウト】
 * ┌─────────────────────────────────────────────────────┐
 * │ ヘッダー（タイトル + フォルダパス）                    │
 * ├─────────────────────────────────────────────────────┤
 * │ [フォルダ選択]  3 / 25 ページ                        │
 * ├─────────────────────────────────────────────────────┤
 * │  ┌──────────────────┐  ┌──────────────────┐        │
 * │  │   Before（元画像） │  │ After（トリミング後）│        │
 * │  │  [originalPreview] │  │  [previewImage]   │        │
 * │  └──────────────────┘  └──────────────────┘        │
 * ├─────────────────────────────────────────────────────┤
 * │  [上] [下] [左] [右] トリミング入力                  │
 * ├─────────────────────────────────────────────────────┤
 * │ [< 前ページ] [プレビューに反映] [次ページ >]         │
 * └─────────────────────────────────────────────────────┘
 */

// React のフック（状態管理・副作用処理）を読み込み
// useState: トリミング値等の状態管理, useEffect: ストア購読・キーボードイベント
import { useEffect, useState } from "react";
// Tauri のネイティブファイルダイアログ機能を読み込み
// open(): トリミング対象の画像フォルダ選択ダイアログを表示する
import { open } from "@tauri-apps/plugin-dialog";
// キャプチャ状態管理ストア（Zustand）を読み込み
// キャプチャ結果フォルダの自動引き継ぎに使用する
import { useCaptureStore } from "@/store/captureStore";
// トリミング状態管理ストア（Zustand）を読み込み
// トリミング値・プレビュー画像・ページナビゲーション等を管理する
import { useTrimStore } from "@/store/trimStore";
// UI ボタンコンポーネントを読み込み
// 適用・リセット・ページ移動等のアクションボタン
import { Button } from "@/components/ui/button";
// UI テキスト入力コンポーネントを読み込み
// トリミング値（上/下/左/右ピクセル）の入力欄
import { Input } from "@/components/ui/input";
// UI ラベルコンポーネントを読み込み
// フォーム項目の見出しとして使用する
import { Label } from "@/components/ui/label";
// アイコンライブラリ（lucide-react）からアイコンを読み込み
// FolderInput（フォルダ）, Scissors（トリミング）, ChevronLeft/Right（ページ移動）,
// RotateCcw（リセット）, Eye（プレビュー）, Minus/Plus（調整）アイコン
import {
  FolderInput,
  Scissors,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Eye,
  Minus,
  Plus,
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
  const originalPreviewImage = useTrimStore((state) => state.originalPreviewImage);
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
   * 入力中はローカルの文字列として保持し、onBlur で確定する。
   * これにより 0 を削除して空欄にできるようになる。
   *
   * @param side - 変更する辺（top / right / bottom / left）
   * @param value - 入力文字列
   */
  function handleCropInputChange(
    side: "top" | "right" | "bottom" | "left",
    value: string
  ) {
    setCropInputs((prev) => ({ ...prev, [side]: value }));
  }

  /**
   * トリミング値の入力確定ハンドラ
   *
   * 入力値を数値に変換し、空文字や負数の場合は 0 に戻す。
   *
   * @param side - 確定する辺（top / right / bottom / left）
   */
  function handleCropInputBlur(
    side: "top" | "right" | "bottom" | "left"
  ) {
    const value = cropInputs[side];
    const num = parseInt(value, 10);
    setCropInsets({ [side]: isNaN(num) || num < 0 ? 0 : num });
  }

  /**
   * トリミング値を増減する
   *
   * +/- ボタンから呼び出され、現在値に delta を加算/減算する。
   * 結果が負数にならないようにクランプする。
   *
   * @param side - 変更する辺（top / right / bottom / left）
   * @param delta - 増減値（+1 または -1）
   */
  function handleCropAdjust(
    side: "top" | "right" | "bottom" | "left",
    delta: number
  ) {
    const current = cropInsets[side];
    const newValue = Math.max(0, current + delta);
    setCropInsets({ [side]: newValue });
  }

  /** ローカル入力値（文字列）— 入力中の一時的な値を保持 */
  const [cropInputs, setCropInputs] = useState({
    top: String(cropInsets.top),
    right: String(cropInsets.right),
    bottom: String(cropInsets.bottom),
    left: String(cropInsets.left),
  });

  /**
   * cropInsets が外部から変更された場合、ローカル入力値も同期する。
   *（リセットボタン等でストア値が変わった時の反映用）
   */
  useEffect(() => {
    setCropInputs({
      top: String(cropInsets.top),
      right: String(cropInsets.right),
      bottom: String(cropInsets.bottom),
      left: String(cropInsets.left),
    });
  }, [cropInsets.top, cropInsets.right, cropInsets.bottom, cropInsets.left]);

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

      {/* ── メインコンテンツ：Before/After プレビュー + トリミング入力 + ナビゲーション ─────── */}
      {effectiveFolderPath && !isLoading && imageFiles.length > 0 && (
        <section className="flex flex-col gap-5 rounded-lg border bg-card p-5 shadow-sm">
          {/* セクションヘッダー */}
          <div className="flex items-center gap-2 flex-wrap">
            <Scissors className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-medium">
              {folderPath ? "選択したフォルダ" : "キャプチャ結果を読み込みました"}
            </h3>
            {effectiveFolderPath && (
              <code
                className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded truncate max-w-full"
                title={effectiveFolderPath}
              >
                {effectiveFolderPath}
              </code>
            )}
          </div>

          {/* ── Before / After 横並びプレビュー ── */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Before：オリジナル画像 */}
            <div className="flex flex-col gap-2">
              <div className="text-center text-sm font-medium text-muted-foreground">
                Before（元画像）
              </div>
              <div className="flex items-center justify-center w-full min-h-[260px] rounded border border-[#0000FF] bg-muted/30">
                {isPreviewLoading ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                    読み込み中...
                  </div>
                ) : originalPreviewImage ? (
                  <div className="overflow-auto max-w-full max-h-[360px] rounded border border-[#0000FF]">
                    <img
                      src={originalPreviewImage}
                      alt={`ページ ${currentImageIndex + 1} - 元画像`}
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
            </div>

            {/* After：トリミング適用後画像 */}
            <div className="flex flex-col gap-2">
              <div className="text-center text-sm font-medium text-muted-foreground">
                After（トリミング後）
              </div>
              <div className="flex items-center justify-center w-full min-h-[260px] rounded border border-[#0000FF] bg-muted/30">
                {isPreviewLoading ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                    読み込み中...
                  </div>
                ) : previewImage ? (
                  <div className="overflow-auto max-w-full max-h-[360px] rounded border border-[#0000FF]">
                    <img
                      src={previewImage}
                      alt={`ページ ${currentImageIndex + 1} - トリミング後`}
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
            </div>
          </div>

          {/* ── トリミング入力UI（画像エリアの下） ── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 justify-items-center">
            {/* 上 */}
            <div className="flex flex-col items-center space-y-1 w-full max-w-[120px]">
              <Label className="text-xs">上 (px)</Label>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7 shrink-0"
                  onClick={() => handleCropAdjust("top", -1)}
                  disabled={cropInsets.top <= 0}
                >
                  <Minus className="h-3 w-3" />
                </Button>
                <Input
                  type="text"
                  inputMode="numeric"
                  className="text-center w-[56px]"
                  value={cropInputs.top}
                  onChange={(e) => {
                    handleCropInputChange("top", e.target.value);
                  }}
                  onBlur={() => handleCropInputBlur("top")}
                />
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7 shrink-0"
                  onClick={() => handleCropAdjust("top", +1)}
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            </div>
            {/* 下 */}
            <div className="flex flex-col items-center space-y-1 w-full max-w-[120px]">
              <Label className="text-xs">下 (px)</Label>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7 shrink-0"
                  onClick={() => handleCropAdjust("bottom", -1)}
                  disabled={cropInsets.bottom <= 0}
                >
                  <Minus className="h-3 w-3" />
                </Button>
                <Input
                  type="text"
                  inputMode="numeric"
                  className="text-center w-[56px]"
                  value={cropInputs.bottom}
                  onChange={(e) => {
                    handleCropInputChange("bottom", e.target.value);
                  }}
                  onBlur={() => handleCropInputBlur("bottom")}
                />
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7 shrink-0"
                  onClick={() => handleCropAdjust("bottom", +1)}
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            </div>
            {/* 左 */}
            <div className="flex flex-col items-center space-y-1 w-full max-w-[120px]">
              <Label className="text-xs">左 (px)</Label>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7 shrink-0"
                  onClick={() => handleCropAdjust("left", -1)}
                  disabled={cropInsets.left <= 0}
                >
                  <Minus className="h-3 w-3" />
                </Button>
                <Input
                  type="text"
                  inputMode="numeric"
                  className="text-center w-[56px]"
                  value={cropInputs.left}
                  onChange={(e) => {
                    handleCropInputChange("left", e.target.value);
                  }}
                  onBlur={() => handleCropInputBlur("left")}
                />
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7 shrink-0"
                  onClick={() => handleCropAdjust("left", +1)}
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            </div>
            {/* 右 */}
            <div className="flex flex-col items-center space-y-1 w-full max-w-[120px]">
              <Label className="text-xs">右 (px)</Label>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7 shrink-0"
                  onClick={() => handleCropAdjust("right", -1)}
                  disabled={cropInsets.right <= 0}
                >
                  <Minus className="h-3 w-3" />
                </Button>
                <Input
                  type="text"
                  inputMode="numeric"
                  className="text-center w-[56px]"
                  value={cropInputs.right}
                  onChange={(e) => {
                    handleCropInputChange("right", e.target.value);
                  }}
                  onBlur={() => handleCropInputBlur("right")}
                />
                <Button
                  variant="outline"
                  size="icon"
                  className="h-7 w-7 shrink-0"
                  onClick={() => handleCropAdjust("right", +1)}
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            </div>
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
