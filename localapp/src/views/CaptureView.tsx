import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Play, Square } from "lucide-react";
import { ProfileSelector } from "@/components/capture/ProfileSelector";
import { ProfileEditor } from "@/components/capture/ProfileEditor";
import { CaptureProgress } from "@/components/capture/CaptureProgress";
import { CaptureResultGallery } from "@/components/capture/CaptureResultGallery";
import { useProfileStore } from "@/store/profileStore";
import { useCaptureStore } from "@/store/captureStore";
import { useNavigationStore } from "@/store/navigationStore";

/**
 * 画面キャプチャ機能のメインビュー
 *
 * 【002002: プロファイル管理統合版】
 * 画面上段にプロファイル選択・編集パネル、下段に連続キャプチャUIを配置。
 * 起動時に Rust 側からビルトインプロファイル一覧を取得し、
 * Zustand ストアに保存してセレクタとエディタで利用する。
 *
 * レイアウト:
 * ┌──────────────────────────────┐
 * │ プロファイルセレクタ          │
 * ├──────────────────────────────┤
 * │ プロファイル設定（編集フォーム）│
 * ├──────────────────────────────┤
 * │ 連続キャプチャ                │
 * └──────────────────────────────┘
 */
export function CaptureView() {
  /** エラーメッセージ */
  const [error, setError] = useState<string | null>(null);
  /** 連続キャプチャの書籍タイトル */
  const [bookTitle, setBookTitle] = useState("");
  /** 先頭ページから開始するかどうか */
  const [startFromBeginning, setStartFromBeginning] = useState(true);

  // Zustand ストアからプロファイル取得アクションを取得
  const fetchProfiles = useProfileStore((state) => state.fetchProfiles);

  // 連続キャプチャストアから状態・アクションを取得
  const {
    isCapturing: isContinuousCapturing,
    currentPage,
    totalPages,
    status,
    message: captureMessage,
    lastCaptureFolder,
    lastCaptureImageCount,
    startCapture,
    stopCapture,
  } = useCaptureStore();

  // ナビゲーションストアから画面遷移アクションを取得（トリム画面連携用）
  const setView = useNavigationStore((state) => state.setView);

  // 現在選択中の有効プロファイルを取得
  const selectedProfileKey = useProfileStore((state) => state.selectedProfileKey);
  const getEffectiveProfile = useProfileStore((state) => state.getEffectiveProfile);

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
   * 連続キャプチャを開始する
   *
   * 1. 選択中のプロファイルを取得
   * 2. プロファイルが未選択の場合はエラーを表示
   * 3. captureStore の `startCapture` を呼び出し
   */
  async function handleStartCapture() {
    setError(null);
    const profile = getEffectiveProfile(selectedProfileKey || "");
    if (!profile) {
      setError("プロファイルが選択されていません");
      return;
    }
    if (bookTitle.trim() === "") {
      setError("書籍タイトルを入力してください");
      return;
    }
    await startCapture(profile, bookTitle, startFromBeginning);
  }

  /**
   * 連続キャプチャを停止する
   *
   * captureStore の `stopCapture` を呼び出し、停止フラグをセットする。
   */
  async function handleStopCapture() {
    await stopCapture();
  }

  /**
   * キャプチャフォルダを OS のファイルマネージャーで開く
   *
   * Rust 側 `open_capture_folder` を invoke して、macOS では Finder、
   * Windows ではエクスプローラーでフォルダを開く。
   */
  async function handleOpenFolder() {
    if (!lastCaptureFolder) return;
    try {
      await invoke("open_capture_folder", { folder_path: lastCaptureFolder });
    } catch (err) {
      console.error("フォルダを開けません:", err);
    }
  }

  /**
   * トリム画面に遷移する
   *
   * navigationStore の `setView("trim")` を呼び出して画面を切り替える。
   * TrimView 側はストアに保存された lastCaptureFolder を参照して自動読み込みする。
   */
  function handleGoTrim() {
    setView("trim");
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

      {/* ── 連続キャプチャセクション ───────────────────────── */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">連続キャプチャ</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            選択したプロファイルで自動的にページをめくりながら連続キャプチャを実行します。
          </p>
        </div>

        {/* 書籍タイトル入力フィールド */}
        <div className="space-y-2">
          <label htmlFor="book-title" className="text-sm font-medium">
            書籍タイトル（保存フォルダ名）
          </label>
          <Input
            id="book-title"
            placeholder="例: 吾輩は猫である"
            value={bookTitle}
            onChange={(e) => setBookTitle(e.target.value)}
            disabled={isContinuousCapturing}
            className="max-w-md"
          />
        </div>

        {/* 連続キャプチャ開始/停止ボタン + 開始位置選択スイッチ */}
        <div className="flex items-center gap-4">
          {!isContinuousCapturing ? (
            <Button
              onClick={handleStartCapture}
              disabled={!selectedProfileKey || isContinuousCapturing}
              className="gap-2"
            >
              <Play className="h-4 w-4" />
              連続キャプチャ開始
            </Button>
          ) : (
            <Button
              onClick={handleStopCapture}
              variant="destructive"
              className="gap-2"
            >
              <Square className="h-4 w-4" />
              停止
            </Button>
          )}

          <div className="flex items-center gap-2">
            <Switch
              id="start-from-beginning"
              checked={startFromBeginning}
              onCheckedChange={setStartFromBeginning}
              disabled={isContinuousCapturing}
            />
            <Label htmlFor="start-from-beginning" className="text-sm">
              {startFromBeginning ? "先頭ページから" : "現在ページから"}
            </Label>
          </div>

          {/* エラーメッセージ — ボタンの右に表示 */}
          {error && (
            <span className="text-sm text-destructive">
              {error}
            </span>
          )}
        </div>

        {/* 進捗表示 */}
        <CaptureProgress
          isCapturing={isContinuousCapturing}
          currentPage={currentPage}
          totalPages={totalPages}
          status={status}
          message={captureMessage}
        />

      </section>

      {/* ── キャプチャ結果セクション（002004）──────────────────────── */}
      {lastCaptureFolder && !isContinuousCapturing && (
        <section className="space-y-4 rounded-lg border bg-card p-5 shadow-sm">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">キャプチャ結果</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              キャプチャした画像を確認し、次のステップに進みます。
            </p>
          </div>
          <CaptureResultGallery
            folderPath={lastCaptureFolder}
            imageCount={lastCaptureImageCount}
            onOpenFolder={handleOpenFolder}
            onGoTrim={handleGoTrim}
          />
        </section>
      )}
    </div>
  );
}
