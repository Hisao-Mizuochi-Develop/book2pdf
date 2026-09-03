/**
 * OCR 済み PDF 作成画面の状態を管理する Zustand ストア
 *
 * 【データフロー】
 * 1. ユーザーが「PDF作成」タブを開く
 * 2. キャプチャフォルダまたは ZIP ファイルを選択
 * 3. 出力先フォルダ・ファイル名を設定
 * 4. `createPdf()` で Rust 側 `create_searchable_pdf` を invoke
 * 5. Rust 側から `pdf-creation-progress` イベントが emit される
 * 6. `listen()` でイベントを受信し、進捗インジケータを更新
 * 7. 完了後、resultPdfPath に作成された PDF のパスを保存
 *
 * 【入力選択の2つのモード】
 * - folder: キャプチャ済みの画像フォルダを直接指定
 * - zip: ZIP ファイルを指定し、Rust 側で一時フォルダに展開して処理
 */

// React 用の軽量状態管理ライブラリ Zustand のストア作成関数を読み込み
// PDF 作成の進捗・結果をコンポーネント間で共有するために使用する
import { create } from "zustand";
// Tauri の Rust コマンド呼び出し関数を読み込み
// invoke("command_name") で Rust 側の #[tauri::command] 関数を実行する
import { invoke } from "@tauri-apps/api/core";
// Tauri のイベント購読機能を読み込み
// listen("event_name", callback) で Rust 側から発射されたイベントを受信する
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
// Tauri のネイティブファイルダイアログ機能を読み込み
// open(): フォルダ/ファイル選択ダイアログを表示する
import { open } from "@tauri-apps/plugin-dialog";

/**
 * 入力ソースの種別
 */
export type SourceType = "folder" | "zip";

/**
 * Rust 側 `PdfCreationProgressPayload` に対応するフロントエンド型
 */
export interface PdfCreationProgressPayload {
  /** 現在処理済みのページ数 */
  current: number;
  /** 処理対象の総ページ数 */
  total: number;
  /** ユーザー向けメッセージ */
  message: string;
}

/**
 * PDF 作成ストアの状態インターフェース
 */
export interface PdfCreationState {
  /** 選択されたソースパス（フォルダまたは ZIP ファイル） */
  sourcePath: string | null;
  /** ソースの種別（フォルダ or ZIP） */
  sourceType: SourceType | null;
  /** ZIP 展開後の一時フォルダ（Rust 側で管理） */
  tempFolder: string | null;
  /** 出力先フォルダパス */
  outputFolder: string | null;
  /** 出力ファイル名（拡張子除く） */
  outputName: string;
  /** PDF 作成実行中フラグ */
  isProcessing: boolean;
  /** 進捗メッセージ */
  progressMessage: string;
  /** 現在処理済みのページ数 */
  progressCurrent: number;
  /** 処理対象の総ページ数 */
  progressTotal: number;
  /** 作成された PDF ファイルパス */
  resultPdfPath: string | null;
  /** 検出された画像ファイル数 */
  imageCount: number;

  /** ソースパスを直接設定（指定フォルダまたはZIPパス） */
  setSourcePath: (path: string | null, type: SourceType | null) => void;
  /** ダイアログで入力フォルダを選択 */
  selectSourceFolder: () => Promise<void>;
  /** ダイアログで ZIP ファイルを選択 */
  selectZipFile: () => Promise<void>;
  /** 検出された画像数を設定 */
  setImageCount: (count: number) => void;
  /** 出力先フォルダを設定 */
  setOutputFolder: (folder: string | null) => void;
  /** 出力ファイル名を設定 */
  setOutputName: (name: string) => void;
  /** OCR 済み PDF を作成 */
  createPdf: () => Promise<void>;
  /** 画像結合 PDF（OCR なし）を作成 */
  generateImagePdf: () => Promise<void>;
  /** 進捗メッセージを設定 */
  setProgressMessage: (message: string) => void;
  /** 結果パスを設定 */
  setResultPdfPath: (path: string | null) => void;
  /** 状態をリセット */
  reset: () => void;
}

/**
 * PDF 作成状態を管理する Zustand ストア
 *
 * `listen("pdf-creation-progress")` で Rust 側からの進捗イベントを受信し、
 * UI に進捗インジケータを表示する。
 */
export const usePdfCreationStore = create<PdfCreationState>((set, get) => ({
  sourcePath: null,
  sourceType: null,
  tempFolder: null,
  outputFolder: null,
  outputName: "output",
  isProcessing: false,
  progressMessage: "",
  progressCurrent: 0,
  progressTotal: 0,
  resultPdfPath: null,
  imageCount: 0,

  /**
   * ソースパスを設定する
   *
   * @param path - フォルダまたは ZIP ファイルの絶対パス
   * @param type - "folder" | "zip" | null
   */
  setSourcePath: (path, type) => {
    set({ sourcePath: path, sourceType: type });
    // パスが変更されたら画像数をリセット（新たに取得する必要がある）
    if (path) {
      // フォルダの場合のみ直接画像数を取得
      if (type === "folder") {
        invoke<string[]>("list_capture_images", { folderPath: path })
          .then((files) => set({ imageCount: files.length }))
          .catch(() => set({ imageCount: 0 }));
      } else {
        // ZIPの場合はRust側で展開後に枚数が分かるため、ここでは0にしておく
        set({ imageCount: 0 });
      }
    } else {
      set({ imageCount: 0 });
    }
  },

  /**
   * ダイアログで入力フォルダを選択する
   *
   * `tauri-plugin-dialog` の `open({ directory: true })` を使用。
   */
  selectSourceFolder: async () => {
    try {
      const selected = await open({ directory: true });
      if (selected && typeof selected === "string") {
        get().setSourcePath(selected, "folder");
      }
    } catch (err) {
      console.error("フォルダ選択エラー:", err);
    }
  },

  /**
   * ダイアログで ZIP ファイルを選択する
   *
   * `tauri-plugin-dialog` の `open()` に ZIP フィルタを指定してファイル選択ダイアログを表示。
   */
  selectZipFile: async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{ name: "ZIP", extensions: ["zip"] }],
      });
      if (selected && typeof selected === "string") {
        get().setSourcePath(selected, "zip");
      }
    } catch (err) {
      console.error("ZIP 選択エラー:", err);
    }
  },

  /**
   * 検出された画像数を設定する
   *
   * @param count - 画像ファイル数
   */
  setImageCount: (count) => set({ imageCount: count }),

  /**
   * 出力先フォルダを設定する
   *
   * @param folder - 出力先フォルダの絶対パス
   */
  setOutputFolder: (folder) => set({ outputFolder: folder }),

  /**
   * 出力ファイル名を設定する
   *
   * @param name - 拡張子除く PDF ファイル名
   */
  setOutputName: (name) => set({ outputName: name }),

  /**
   * OCR 済み PDF を作成する
   *
   * 1. 入力ソースと出力先のバリデーション
   * 2. `pdf-creation-progress` イベントリスナーを登録
   * 3. Rust 側 `create_searchable_pdf` を呼び出し
   * 4. 進捗イベントを受信して progressCurrent / progressTotal を更新
   * 5. 完了後、resultPdfPath に PDF ファイルパスを保存
   *
   * @throws 入力ソースまたは出力先が未設定の場合、または処理エラー時
   */
  createPdf: async () => {
    const { sourcePath, sourceType, outputName, outputFolder } = get();

    if (!sourcePath || !sourceType) {
      throw new Error("入力フォルダまたは ZIP ファイルが選択されていません");
    }
    if (!outputFolder) {
      throw new Error("出力先フォルダが設定されていません");
    }

    set({
      isProcessing: true,
      progressMessage: "OCR 処理を開始しています...",
      progressCurrent: 0,
      progressTotal: 0,
      resultPdfPath: null,
    });

    const outputPath = `${outputFolder}/${outputName}.pdf`;

    let unlisten: UnlistenFn | null = null;

    try {
      // 進捗イベントリスナーを登録
      unlisten = await listen<PdfCreationProgressPayload>(
        "pdf-creation-progress",
        (event) => {
          set({
            progressMessage: event.payload.message,
            progressCurrent: event.payload.current,
            progressTotal: event.payload.total,
          });
        }
      );

      // Rust 側で ZIP 展開 → OCR → PDF 生成
      const result = await invoke<string>("create_searchable_pdf", {
        sourcePath: sourcePath,
        sourceType: sourceType,
        outputPath: outputPath,
      });

      set({
        resultPdfPath: result,
        progressMessage: "PDF の作成が完了しました",
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      set({ progressMessage: `エラー: ${message}` });
      throw err;
    } finally {
      if (unlisten) {
        unlisten();
      }
      set({ isProcessing: false });
    }
  },

  /**
   * 画像結合 PDF（OCR なし）を作成する
   *
   * 1. 入力ソースと出力先のバリデーション
   * 2. `pdf-creation-progress` イベントリスナーを登録
   * 3. Rust 側 `generate_image_pdf` を呼び出し
   * 4. 進捗イベントを受信して progressCurrent / progressTotal を更新
   * 5. 完了後、resultPdfPath に PDF ファイルパスを保存
   */
  generateImagePdf: async () => {
    const { sourcePath, sourceType, outputName, outputFolder } = get();

    if (!sourcePath || !sourceType) {
      throw new Error("入力フォルダまたは ZIP ファイルが選択されていません");
    }
    if (!outputFolder) {
      throw new Error("出力先フォルダが設定されていません");
    }

    set({
      isProcessing: true,
      progressMessage: "画像を PDF に結合しています...",
      progressCurrent: 0,
      progressTotal: 0,
      resultPdfPath: null,
    });

    const outputPath = `${outputFolder}/${outputName}.pdf`;

    let unlisten: UnlistenFn | null = null;

    try {
      // 進捗イベントリスナーを登録
      unlisten = await listen<PdfCreationProgressPayload>(
        "pdf-creation-progress",
        (event) => {
          set({
            progressMessage: event.payload.message,
            progressCurrent: event.payload.current,
            progressTotal: event.payload.total,
          });
        }
      );

      // Rust 側で ZIP 展開 → 画像結合 PDF 生成
      const result = await invoke<string>("generate_image_pdf", {
        sourcePath: sourcePath,
        sourceType: sourceType,
        outputPath: outputPath,
      });

      set({
        resultPdfPath: result,
        progressMessage: "PDF の結合が完了しました",
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      set({ progressMessage: `エラー: ${message}` });
      throw err;
    } finally {
      if (unlisten) {
        unlisten();
      }
      set({ isProcessing: false });
    }
  },

  /**
   * 進捗メッセージを設定する
   *
   * @param message - ユーザー向けメッセージ
   */
  setProgressMessage: (message) => set({ progressMessage: message }),

  /**
   * 結果パス（作成された PDF ファイルパス）を設定する
   *
   * @param path - PDF の絶対パス、または null
   */
  setResultPdfPath: (path) => set({ resultPdfPath: path }),

  /**
   * ストアの状態をリセットする（初期値に戻す）
   */
  reset: () =>
    set({
      sourcePath: null,
      sourceType: null,
      tempFolder: null,
      outputFolder: null,
      outputName: "output",
      isProcessing: false,
      progressMessage: "",
      progressCurrent: 0,
      progressTotal: 0,
      resultPdfPath: null,
      imageCount: 0,
    }),
}));
