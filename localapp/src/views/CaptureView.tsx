// React のフック（状態管理・副作用処理）を読み込み
// useState: コンポーネント内で状態を管理する, useEffect: 副作用（イベント購読等）を実行する
import { useState, useEffect } from "react";
// Tauri の Rust コマンド呼び出し関数を読み込み
// invoke("command_name") で Rust 側の #[tauri::command] 関数を実行する
import { invoke } from "@tauri-apps/api/core";
// Tauri のネイティブファイルダイアログ機能を読み込み
// open(): フォルダ/ファイル選択ダイアログを表示する
import { open } from "@tauri-apps/plugin-dialog";
// UI ボタンコンポーネントを読み込み
// Apple HIG 風デザインのボタン（primary/secondary/ghost バリエーション）
import { Button } from "@/components/ui/button";
// UI テキスト入力コンポーネントを読み込み
// フォーム入力欄として使用する
import { Input } from "@/components/ui/input";
// UI ラベルコンポーネントを読み込み
// フォーム項目の見出しとして使用する
import { Label } from "@/components/ui/label";
// UI トグルスイッチコンポーネントを読み込み
// ON/OFF の切り替え UI として使用する
import { Switch } from "@/components/ui/switch";
// アイコンライブラリ（lucide-react）からアイコンを読み込み
// Play（開始）, Square（停止）, FolderOpen（フォルダ開く）アイコン
import { Play, Square, FolderOpen } from "lucide-react";
// キャプチャプロファイル選択 UI コンポーネントを読み込み
// 電子書籍アプリ別のキャプチャ設定を選択するドロップダウン
import { ProfileSelector } from "@/components/capture/ProfileSelector";
// キャプチャプロファイル編集 UI コンポーネントを読み込み
// プロファイルの各種パラメータ（待機時間・クリック位置等）を編集するフォーム
import { ProfileEditor } from "@/components/capture/ProfileEditor";
// 連続キャプチャ進捗表示コンポーネントを読み込み
// キャプチャ中の進捗バー・メッセージ・アニメーションを表示
import { CaptureProgress } from "@/components/capture/CaptureProgress";
// キャプチャ結果サムネイルギャラリーコンポーネントを読み込み
// キャプチャ済み画像の一覧・プレビューを表示
import { CaptureResultGallery } from "@/components/capture/CaptureResultGallery";
// プロファイル状態管理ストア（Zustand）を読み込み
// 現在選択中のプロファイル・プロファイル一覧を取得するために使用する
import { useProfileStore } from "@/store/profileStore";
// キャプチャ状態管理ストア（Zustand）を読み込み
// 連続キャプチャの進捗・結果フォルダパス等を取得するために使用する
import { useCaptureStore } from "@/store/captureStore";
// ナビゲーション状態管理ストア（Zustand）を読み込み
// 画面遷移（タブ切り替え）のために使用する
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
  /** ユーザー指定の出力先フォルダパス（空文字でデフォルト） */
  const [outputFolder, setOutputFolder] = useState("");

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
    await startCapture(profile, bookTitle, startFromBeginning, outputFolder);
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
   * 出力先フォルダ選択ダイアログを開く
   *
   * tauri-plugin-dialog の `open({ directory: true })` を使用し、
   * ユーザーが選択したフォルダパスを outputFolder state に保存する。
   * キャンセル時は何もしない。
   */
  async function handleSelectOutputFolder() {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: "キャプチャ画像の保存先フォルダを選択",
      });
      if (selected && typeof selected === "string") {
        setOutputFolder(selected);
      }
    } catch (err) {
      console.error("フォルダ選択エラー:", err);
    }
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

        {/* 出力先フォルダ選択フィールド（002009） */}
        <div className="space-y-2">
          <label htmlFor="output-folder" className="text-sm font-medium">
            出力先フォルダ
          </label>
          <div className="flex items-center gap-2 max-w-md">
            <Input
              id="output-folder"
              placeholder="未指定時は Pictures/BookCapture/<書籍タイトル>/"
              value={outputFolder}
              onChange={(e) => setOutputFolder(e.target.value)}
              disabled={isContinuousCapturing}
              className="flex-1"
            />
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={handleSelectOutputFolder}
              disabled={isContinuousCapturing}
              title="フォルダを選択"
            >
              <FolderOpen className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            空欄の場合はデフォルトの Pictures/BookCapture 配下に保存されます。
          </p>
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
