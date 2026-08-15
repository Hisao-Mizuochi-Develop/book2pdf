import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Button } from "@/components/ui/button";
import { Camera } from "lucide-react";

/**
 * CaptureResult: Rust 側 capture_screen コマンドの戻り値型
 */
interface CaptureResult {
  /** Base64 エンコードされた PNG 画像データ */
  base64: string;
  /** 画像幅（ピクセル） */
  width: number;
  /** 画像高さ（ピクセル） */
  height: number;
}

/**
 * 画面キャプチャ機能のメインビュー
 *
 * 002001: 単発スクリーンショット取得のテストUI
 * 将来的に連続キャプチャ・プロファイル選択等が追加される予定
 */
export function CaptureView() {
  /** キャプチャした画像の Data URL */
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  /** キャプチャ実行中のローディング状態 */
  const [isCapturing, setIsCapturing] = useState(false);
  /** エラーメッセージ */
  const [error, setError] = useState<string | null>(null);

  /**
   * スクリーンショットを取得して状態に保存する
   *
   * 1. ローディング状態を ON
   * 2. Rust 側 `capture_screen` コマンドを invoke
   * 3. 成功: Base64 画像を Data URL 形式で state に保存
   * 4. 失敗: エラーメッセージを state に保存
   * 5. ローディング状態を OFF
   */
  async function handleCapture() {
    setIsCapturing(true);
    setError(null);
    try {
      const result = await invoke<CaptureResult>("capture_screen");
      // Base64 を Data URL 形式に変換して img タグで表示可能にする
      const dataUrl = `data:image/png;base64,${result.base64}`;
      setCapturedImage(dataUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsCapturing(false);
    }
  }

  return (
    <div className="flex h-full flex-col items-center p-8">
      <div className="text-center">
        <h2 className="text-2xl font-semibold tracking-tight">キャプチャ</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          電子書籍リーダー画面を連続キャプチャします。
        </p>
      </div>

      {/* 002001: キャプチャテストボタン */}
      <div className="mt-8">
        <Button
          onClick={handleCapture}
          disabled={isCapturing}
          className="gap-2"
        >
          <Camera className="h-4 w-4" />
          {isCapturing ? "キャプチャ中..." : "キャプチャテスト"}
        </Button>
      </div>

      {/* エラーメッセージ表示 */}
      {error && (
        <div className="mt-4 rounded-md bg-destructive/10 px-4 py-2 text-sm text-destructive">
          エラー: {error}
        </div>
      )}

      {/* キャプチャした画像のプレビュー */}
      {capturedImage && (
        <div className="mt-8 flex flex-col items-center gap-2">
          <p className="text-sm text-muted-foreground">キャプチャ結果:</p>
          <img
            src={capturedImage}
            alt="キャプチャ画像"
            className="max-h-[400px] max-w-full rounded-md border shadow-sm"
          />
        </div>
      )}
    </div>
  );
}
