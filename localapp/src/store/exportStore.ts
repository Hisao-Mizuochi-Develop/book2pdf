/**
 * ZIP 出力（エクスポート）画面の状態を管理する Zustand ストア
 *
 * 【データフロー】
 * 1. ユーザーが ZIP 作成タブを開く
 * 2. `initFromCaptureStore()` で captureStore.lastCaptureFolder から sourceFolder を自動設定
 * 3. ユーザーが出力ファイル名・出力先フォルダを設定
 * 4. `createZip()` で Rust 側 `create_zip_archive` を invoke
 * 5. Rust 側から `zip-progress` イベントが emit される
 * 6. `listen()` でイベントを受信し、progressMessage を更新
 * 7. 完了後、resultPath に出力ファイルパスを保存
 *
 * 【タブ間自動連携（005003）】
 * - captureStore.lastCaptureFolder の変更を監視し、自動的に sourceFolder に反映する
 * - exportStore の sourceFolder は captureStore の変更を受けて常に最新になる
 */

// React 用の軽量状態管理ライブラリ Zustand のストア作成関数を読み込み
// ZIP 出力の進捙・状態をコンポーネント間で共有するために使用する
import { create } from "zustand";
// Tauri の Rust コマンド呼び出し関数を読み込み
// invoke("command_name") で Rust 側の #[tauri::command] 関数を実行する
import { invoke } from "@tauri-apps/api/core";
// Tauri のイベント購読機能を読み込み
// listen("event_name", callback) で Rust 側から発射されたイベントを受信する
import { listen, type UnlistenFn } from "@tauri-apps/api/event";

/**
 * Rust 側 `ZipProgressPayload` に対応するフロントエンド型
 */
export interface ZipProgressPayload {
  /** 現在処理済みのファイル数 */
  current: number;
  /** 処理対象の総ファイル数 */
  total: number;
  /** ユーザー向けメッセージ */
  message: string;
}

/**
 * エクスポートストアの状態インターフェース
 */
export interface ExportState {
  /** 入力画像フォルダパス */
  sourceFolder: string | null;
  /** 出力 ZIP ファイル名（拡張子除く） */
  outputName: string;
  /** 出力先フォルダパス */
  outputFolder: string | null;
  /** ZIP 作成実行中フラグ */
  isCreating: boolean;
  /** 進捗メッセージ */
  progressMessage: string;
  /** 現在処理済みのファイル数 */
  progressCurrent: number;
  /** 処理対象の総ファイル数 */
  progressTotal: number;
  /** 作成された ZIP ファイルパス */
  resultPath: string | null;

  /** 入力フォルダを設定 */
  setSourceFolder: (folder: string | null) => void;
  /** 出力ファイル名を設定 */
  setOutputName: (name: string) => void;
  /** 出力先フォルダを設定 */
  setOutputFolder: (folder: string | null) => void;
  /** ZIP 作成を開始 */
  createZip: () => Promise<void>;
  /** 進捗メッセージを設定 */
  setProgressMessage: (message: string) => void;
  /** 結果パスを設定 */
  setResultPath: (path: string | null) => void;
  /** 状態をリセット */
  reset: () => void;
}

/**
 * ZIP 出力状態を管理する Zustand ストア
 *
 * `listen("zip-progress")` で Rust 側からの進捗イベントを受信し、
 * UI に進捗メッセージを表示する。
 */
export const useExportStore = create<ExportState>((set, get) => ({
  sourceFolder: null,
  outputName: "images",
  outputFolder: null,
  isCreating: false,
  progressMessage: "",
  progressCurrent: 0,
  progressTotal: 0,
  resultPath: null,

  /**
   * 入力フォルダを設定する
   *
   * @param folder - 画像フォルダの絶対パス、または null
   */
  setSourceFolder: (folder) => set({ sourceFolder: folder }),

  /**
   * 出力ファイル名を設定する
   *
   * @param name - 拡張子除く ZIP ファイル名
   */
  setOutputName: (name) => set({ outputName: name }),

  /**
   * 出力先フォルダを設定する
   *
   * @param folder - 出力先フォルダの絶対パス、または null
   */
  setOutputFolder: (folder) => set({ outputFolder: folder }),

  /**
   * ZIP アーカイブを作成する
   *
   * 1. 入力フォルダと出力先のバリデーション
   * 2. `zip-progress` イベントリスナーを登録
   * 3. Rust 側 `create_zip_archive` を呼び出し
   * 4. 進捗イベントを受信して progressMessage を更新
   * 5. 完了後、resultPath に出力ファイルパスを保存
   *
   * @throws 入力フォルダまたは出力先が未設定の場合、または ZIP 作成エラー時
   */
  createZip: async () => {
    const { sourceFolder, outputName, outputFolder } = get();

    if (!sourceFolder) {
      throw new Error("入力フォルダが設定されていません");
    }
    if (!outputFolder) {
      throw new Error("出力先フォルダが設定されていません");
    }

    set({
      isCreating: true,
      progressMessage: "ZIP 作成を開始しています...",
      progressCurrent: 0,
      progressTotal: 0,
      resultPath: null,
    });

    // 出力パスを組み立て
    const outputPath = `${outputFolder}/${outputName}`;

    let unlisten: UnlistenFn | null = null;

    try {
      // 進捗イベントリスナーを登録
      unlisten = await listen<ZipProgressPayload>("zip-progress", (event) => {
        set({
          progressMessage: event.payload.message,
          progressCurrent: event.payload.current,
          progressTotal: event.payload.total,
        });
      });

      // Rust 側で ZIP アーカイブ作成
      const result = await invoke<string>("create_zip_archive", {
        folderPath: sourceFolder,
        outputPath: outputPath,
      });

      set({ resultPath: result, progressMessage: "ZIP ファイルの作成が完了しました" });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      set({ progressMessage: `エラー: ${message}` });
      throw err;
    } finally {
      if (unlisten) {
        unlisten();
      }
      set({ isCreating: false });
    }
  },

  /**
   * 進捗メッセージを設定する
   *
   * @param message - ユーザー向けメッセージ
   */
  setProgressMessage: (message) => set({ progressMessage: message }),

  /**
   * 結果パスを設定する
   *
   * @param path - 作成された ZIP ファイルの絶対パス、または null
   */
  setResultPath: (path) => set({ resultPath: path }),

  /**
   * ストアの状態をリセットする（初期値に戻す）
   *
   * sourceFolder は captureStore からの連携値のため、このメソッドではリセットしない。
   */
  reset: () =>
    set({
      outputName: "images",
      outputFolder: null,
      isCreating: false,
      progressMessage: "",
      progressCurrent: 0,
      progressTotal: 0,
      resultPath: null,
    }),
}));
