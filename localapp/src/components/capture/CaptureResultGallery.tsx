/**
 * キャプチャ結果のサムネイルギャラリーコンポーネント
 *
 * 002004: キャプチャ画像のフォルダ管理
 * キャプチャ完了後に CaptureView で表示される。
 * サムネイルグリッド・フォルダを開く・トリミングへ進む の3機能を提供する。
 *
 * 【データフロー】
 * 1. マウント時に `list_capture_images` でフォルダ内 PNG 一覧を取得
 * 2. 先頭10枚を `get_capture_image` で Base64 取得してサムネイル表示
 * 3. 残りはファイル名のみ表示（クリック時に読み込む方式は将来拡張）
 */

import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Button } from "@/components/ui/button";
import { FolderOpen, Scissors } from "lucide-react";

/**
 * CaptureResultGallery コンポーネントのプロパティ
 */
interface CaptureResultGalleryProps {
  /** キャプチャ画像が保存されたフォルダの絶対パス */
  folderPath: string;
  /** キャプチャした総画像枚数 */
  imageCount: number;
  /** 「フォルダを開く」ボタンクリック時のコールバック */
  onOpenFolder: () => void;
  /** 「トリミングへ進む」ボタンクリック時のコールバック */
  onGoTrim: () => void;
}

/**
 * キャプチャ結果ギャラリーコンポーネント
 *
 * @param folderPath - キャプチャフォルダパス
 * @param imageCount - 画像総数
 * @param onOpenFolder - フォルダを開くハンドラ
 * @param onGoTrim - トリム画面遷移ハンドラ
 */
export function CaptureResultGallery({
  folderPath,
  imageCount,
  onOpenFolder,
  onGoTrim,
}: CaptureResultGalleryProps) {
  /** PNG 画像ファイル名一覧 */
  const [images, setImages] = useState<string[]>([]);
  /** インデックス → Base64 DataURL のマップ */
  const [thumbnails, setThumbnails] = useState<Map<number, string>>(new Map());
  /** 読み込み中フラグ */
  const [isLoading, setIsLoading] = useState(true);
  /** エラーメッセージ */
  const [error, setError] = useState<string | null>(null);

  /**
   * マウント時: サムネイル画像を読み込む
   *
   * 1. `list_capture_images` で PNG ファイル名一覧を取得
   * 2. 先頭10枚までを `get_capture_image` で Base64 取得して state に保存
   * 3. それ以降は必要時（将来的にクリック時など）にロードする方針
   */
  useEffect(() => {
    async function loadThumbnails() {
      try {
        setIsLoading(true);
        setError(null);

        // PNG 画像のファイル名一覧を Rust 側から取得
        const filenames = await invoke<string[]>("list_capture_images", {
          folderPath,
        });
        setImages(filenames);

        // 先頭10枚までを先読み（全枚数が多い場合のパフォーマンス対策）
        const initialCount = Math.min(filenames.length, 10);
        const newThumbnails = new Map<number, string>();

        for (let i = 0; i < initialCount; i++) {
          const filepath = `${folderPath}/${filenames[i]}`;
          const base64 = await invoke<string>("get_capture_image", { filepath });
          newThumbnails.set(i, `data:image/png;base64,${base64}`);
        }

        setThumbnails(newThumbnails);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setIsLoading(false);
      }
    }

    loadThumbnails();
  }, [folderPath]);

  // ローディング状態
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          画像を読み込み中...
        </div>
      </div>
    );
  }

  // エラー状態
  if (error) {
    return (
      <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
        画像読み込みエラー: {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* --- ヘッダー: 件数・パス・アクションボタン --- */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-medium">
            {imageCount} ページをキャプチャしました
          </p>
          <p
            className="mt-0.5 truncate text-xs text-muted-foreground"
            title={folderPath}
          >
            {folderPath}
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenFolder}
            className="gap-1.5"
          >
            <FolderOpen className="h-3.5 w-3.5" />
            フォルダを開く
          </Button>
          <Button size="sm" onClick={onGoTrim} className="gap-1.5">
            <Scissors className="h-3.5 w-3.5" />
            トリミングへ進む
          </Button>
        </div>
      </div>

      {/* --- サムネイルグリッド --- */}
      {images.length > 0 ? (
        <div className="grid grid-cols-4 gap-2 sm:grid-cols-5 md:grid-cols-6">
          {images.map((filename, index) => (
            <div
              key={filename}
              className="group relative aspect-[3/4] overflow-hidden rounded-md border bg-muted"
            >
              {thumbnails.has(index) ? (
                <img
                  src={thumbnails.get(index)}
                  alt={`ページ ${index + 1}`}
                  className="h-full w-full object-cover transition-transform duration-200 group-hover:scale-105"
                  loading="lazy"
                />
              ) : (
                <div className="flex h-full flex-col items-center justify-center gap-1 text-xs text-muted-foreground">
                  <span className="font-mono">{filename}</span>
                  <span className="text-[10px]">未読み込み</span>
                </div>
              )}
              {/* ホバー時のページ番号オーバーレイ */}
              <div className="absolute bottom-0 left-0 right-0 bg-black/50 px-1.5 py-0.5 text-[10px] text-white opacity-0 transition-opacity group-hover:opacity-100">
                {index + 1} / {images.length}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="py-4 text-center text-sm text-muted-foreground">
          フォルダに画像が見つかりませんでした。
        </p>
      )}
    </div>
  );
}
