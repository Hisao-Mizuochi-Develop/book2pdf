import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Button } from "@/components/ui/button";
import { Camera } from "lucide-react";
import { ProfileSelector } from "@/components/capture/ProfileSelector";
import { ProfileEditor } from "@/components/capture/ProfileEditor";
import { useProfileStore } from "@/store/profileStore";

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
 * 【002002: プロファイル管理統合版】
 * 画面上段にプロファイル選択・編集パネル、下段にキャプチャテストUIを配置。
 * 起動時に Rust 側からビルトインプロファイル一覧を取得し、
 * Zustand ストアに保存してセレクタとエディタで利用する。
 *
 * レイアウト:
 * ┌──────────────────────────────┐
 * │ プロファイルセレクタ          │
 * ├──────────────────────────────┤
 * │ プロファイル設定（編集フォーム）│
 * ├──────────────────────────────┤
 * │ キャプチャテストボタン        │
 * │ [画像プレビュー]             │
 * └──────────────────────────────┘
 */
export function CaptureView() {
  /** キャプチャした画像の Data URL */
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  /** キャプチャ実行中のローディング状態 */
  const [isCapturing, setIsCapturing] = useState(false);
  /** エラーメッセージ */
  const [error, setError] = useState<string | null>(null);

  // Zustand ストアからプロファイル取得アクションを取得
  const fetchProfiles = useProfileStore((state) => state.fetchProfiles);

  /**
   * コンポーネントマウント時: ビルトインプロファイルを Rust 側から取得
   *
   * 002002 ではメモリ内のみ保持。ブラウザリロードでリセットされる。
   * 将来の 007001 で永続化を実装予定。
   */
  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

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
    <div className="flex h-full flex-col p-6 gap-5 overflow-auto">
      {/* ── プロファイル管理セクション ───────────────────────── */}
      <section className="space-y-4">
        {/* セクションタイトル */}
        <div>
          <h2 className="text-xl font-semibold tracking-tight">キャプチャ設定</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            電子書籍アプリに応じたプロファイルを選択・編集します。
          </p>
        </div>

        {/* プロファイルセレクタ */}
        <ProfileSelector />

        {/* プロファイル編集パネル */}
        <div className="rounded-lg border bg-card p-5 shadow-sm">
          <ProfileEditor />
        </div>
      </section>

      {/* ── キャプチャテストセクション ───────────────────────── */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">キャプチャテスト</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            選択した設定でスクリーンショットを取得して確認します。
          </p>
        </div>

        {/* キャプチャテストボタン */}
        <div>
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
          <div className="rounded-md bg-destructive/10 px-4 py-2 text-sm text-destructive">
            エラー: {error}
          </div>
        )}

        {/* キャプチャした画像のプレビュー */}
        {capturedImage && (
          <div className="flex flex-col items-start gap-2">
            <p className="text-sm text-muted-foreground">キャプチャ結果:</p>
            <img
              src={capturedImage}
              alt="キャプチャ画像"
              className="max-h-[400px] max-w-full rounded-md border shadow-sm"
            />
          </div>
        )}
      </section>
    </div>
  );
}
