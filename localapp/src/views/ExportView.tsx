/**
 * ZIP 出力画面（エクスポートタブ）
 *
 * 【機能概要】
 * - キャプチャ完了後の画像フォルダを自動的に入力として引き継ぐ（タブ間連携）
 * - 出力ファイル名・出力先フォルダを設定
 * - ZIP アーカイブを作成し、進捗を表示
 * - 完了後、出力ファイルパスを表示 + フォルダを開く
 *
 * 【技術仕様】
 * - `tauri-plugin-dialog` の `open()` で出力先フォルダを選択
 * - `invoke("create_zip_archive")` で Rust 側コマンドを呼び出し
 * - `listen("zip-progress")` で進捗イベントを受信（exportStore 内で処理）
 * - `captureStore.lastCaptureFolder` の変更を監視して自動連携（LA005003）
 */

// React のフック（状態管理・副作用処理）を読み込み
// useState: フォーム入力値等の状態管理, useEffect: ストア購読等の副作用
import { useState, useEffect } from "react";
// Tauri の Rust コマンド呼び出し関数を読み込み
// invoke("command_name") で Rust 側の #[tauri::command] 関数を実行する
import { invoke } from "@tauri-apps/api/core";
// Tauri のネイティブファイルダイアログ機能を読み込み
// open(): 出力先フォルダ選択ダイアログを表示する
import { open } from "@tauri-apps/plugin-dialog";
// UI ボタンコンポーネントを読み込み
// ZIP 作成・フォルダ開く等のアクションを実行するボタン
import { Button } from "@/components/ui/button";
// UI テキスト入力コンポーネントを読み込み
// 出力ファイル名の入力欄として使用する
import { Input } from "@/components/ui/input";
// UI ラベルコンポーネントを読み込み
// フォーム項目の見出しとして使用する
import { Label } from "@/components/ui/label";
// ZIP 出力状態管理ストア（Zustand）を読み込み
// 進捗・結果パス・処理中フラグ等を取得するために使用する
import { useExportStore } from "@/store/exportStore";
// キャプチャ状態管理ストア（Zustand）を読み込み
// キャプチャ完了フォルダの自動引き継ぎに使用する
import { useCaptureStore } from "@/store/captureStore";
// アイコンライブラリ（lucide-react）からアイコンを読み込み
// FileArchive（ZIP）, FolderOpen, Folder, Package, RotateCcw（再試行）アイコン
import { FileArchive, FolderOpen, Folder, Package, RotateCcw } from "lucide-react";

/**
 * ZIP 出力画面コンポーネント
 *
 * Apple HIG 風のデザイン（白基調・余白多め・控えめな角丸）で構築する。
 */
export function ExportView() {
  // ─── exportStore から状態を取得 ───
  const {
    sourceFolder,
    outputName,
    outputFolder,
    isCreating,
    progressMessage,
    progressCurrent,
    progressTotal,
    resultPath,
    setSourceFolder,
    setOutputName,
    setOutputFolder,
    createZip,
    reset,
  } = useExportStore();

  // 進捗率（0〜100）
  const progressPercent =
    progressTotal > 0
      ? Math.round((progressCurrent / progressTotal) * 100)
      : 0;

  // ─── captureStore からタブ間連携情報を取得（LA005003） ───
  const lastCaptureFolder = useCaptureStore((state) => state.lastCaptureFolder);

  // ─── 入力フォルダ内の画像枚数を管理 ───
  const [imageCount, setImageCount] = useState(0);

  /**
   * captureStore.lastCaptureFolder の変更を監視し、
   * 自動的に exportStore.sourceFolder に反映する（タブ間連携）
   */
  useEffect(() => {
    if (lastCaptureFolder) {
      setSourceFolder(lastCaptureFolder);
    }
  }, [lastCaptureFolder, setSourceFolder]);

  /**
   * sourceFolder が変更されたら画像枚数を取得する
   */
  useEffect(() => {
    if (sourceFolder) {
      invoke<string[]>("list_capture_images", { folderPath: sourceFolder })
        .then((files) => setImageCount(files.length))
        .catch(() => setImageCount(0));
    } else {
      setImageCount(0);
    }
  }, [sourceFolder]);

  /**
   * 入力フォルダ選択ダイアログを開く
   *
   * `tauri-plugin-dialog` の `open()` を使用して、
   * ユーザーに入力画像フォルダを選択するダイアログを表示する。
   */
  const handleSelectSourceFolder = async () => {
    try {
      const selected = await open({ directory: true });
      if (selected && typeof selected === "string") {
        setSourceFolder(selected);
      }
    } catch (err) {
      console.error("フォルダ選択エラー:", err);
    }
  };

  /**
   * 出力先フォルダ選択ダイアログを開く
   *
   * `tauri-plugin-dialog` の `open()` を使用して、
   * ユーザーにフォルダ選択ダイアログを表示する。
   */
  const handleSelectOutputFolder = async () => {
    try {
      const selected = await open({ directory: true });
      if (selected && typeof selected === "string") {
        setOutputFolder(selected);
      }
    } catch (err) {
      console.error("フォルダ選択エラー:", err);
    }
  };

  /**
   * ZIP 作成ボタンクリックハンドラ
   *
   * exportStore.createZip() を呼び出し、エラー時は progressMessage に反映する。
   */
  const handleCreateZip = async () => {
    try {
      await createZip();
    } catch {
      // エラーは exportStore 内で progressMessage に設定されている
    }
  };

  /**
   * ZIP ファイルの親フォルダを OS のファイルマネージャーで開く
   */
  const handleOpenResultFolder = async () => {
    if (!resultPath) return;
    // パス区切りは OS に応じて / または \ となるため、両方に対応
    const lastSep = resultPath.lastIndexOf("/");
    const lastSepWin = resultPath.lastIndexOf("\\");
    const sepIndex = Math.max(lastSep, lastSepWin);
    const folder = sepIndex > 0 ? resultPath.substring(0, sepIndex) : resultPath;
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
          <FileArchive className="h-5 w-5 text-[#007AFF]" />
        </div>
        <div>
          <h2 className="text-xl font-semibold tracking-tight">ZIP 作成</h2>
          <p className="text-sm text-muted-foreground">
            画像フォルダを ZIP アーカイブにまとめます
          </p>
        </div>
      </div>

      {/* ─── 入力設定セクション ─── */}
      <section className="rounded-lg border border-border bg-white p-4">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          <Package className="h-4 w-4 text-muted-foreground" />
          入力設定
        </div>
        <div className="mt-3 space-y-2">
          {sourceFolder ? (
            <>
              <div className="flex items-center gap-2">
                <div className="flex-1 rounded-md bg-[#F5F5F7] px-3 py-2 text-sm text-foreground">
                  <span className="text-muted-foreground">フォルダ:</span>{" "}
                  <span className="font-mono">{sourceFolder}</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSelectSourceFolder}
                  disabled={isCreating}
                >
                  <Folder className="mr-1.5 h-4 w-4" />
                  変更
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                画像ファイル: <span className="font-medium text-foreground">{imageCount}</span> 枚
              </p>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <p className="flex-1 text-sm text-muted-foreground">
                入力フォルダが設定されていません。
                「電子書籍」タブでキャプチャを完了すると、自動的に反映されます。
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={handleSelectSourceFolder}
                disabled={isCreating}
              >
                <Folder className="mr-1.5 h-4 w-4" />
                選択
              </Button>
            </div>
          )}
        </div>
      </section>

      {/* ─── 出力設定セクション ─── */}
      <section className="rounded-lg border border-border bg-white p-4">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          <FileArchive className="h-4 w-4 text-muted-foreground" />
          出力設定
        </div>
        <div className="mt-3 space-y-4">
          {/* 出力ファイル名 */}
          <div className="space-y-1.5">
            <Label htmlFor="output-name" className="text-sm font-medium">
              出力ファイル名
            </Label>
            <div className="flex items-center gap-2">
              <Input
                id="output-name"
                value={outputName}
                onChange={(e) => setOutputName(e.target.value)}
                placeholder="images"
                disabled={isCreating}
                className="max-w-[240px]"
              />
              <span className="text-sm text-muted-foreground">.zip</span>
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
                disabled={isCreating}
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
          onClick={handleCreateZip}
          disabled={!sourceFolder || !outputFolder || isCreating || imageCount === 0}
          size="lg"
        >
          <FileArchive className="mr-2 h-4 w-4" />
          {isCreating ? "ZIP 作成中..." : "ZIP 作成"}
        </Button>

        {/* 進捗表示 */}
        {isCreating && (
          <div className="flex flex-col gap-3 rounded-lg border border-border bg-white p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <div className="flex flex-col">
                <span className="text-sm font-medium">ZIP を作成しています</span>
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
                    {progressCurrent} / {progressTotal} ファイル
                  </span>
                  <span>{progressPercent}%</span>
                </div>
              </>
            ) : (
              // 総ファイル数が判明する前の不定形プログレス
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full w-1/3 animate-[shimmer_1.5s_infinite] rounded-full bg-primary" />
              </div>
            )}
          </div>
        )}

        {/* 完了後の結果表示 */}
        {resultPath && !isCreating && (
          <div className="space-y-2">
            <div className="rounded-md border border-border bg-white px-3 py-2 text-sm">
              <span className="text-muted-foreground">作成先:</span>{" "}
              <span className="font-mono">{resultPath}</span>
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
