/**
 * localapp → backend API 経由の OCR/PDF 作成を管理する Zustand ストア
 *
 * 【データフロー】
 * 1. ユーザーが「PDF作成」タブで入力ソースと出力先を設定する
 * 2. `runBackendOcr(outputPath)` で Rust 側 `run_backend_ocr` を invoke
 * 3. Rust 側で ZIP 作成 → backend ジョブ作成 → アップロード → OCR → PDF ダウンロード
 * 4. Rust 側から `ocr-progress` イベントが emit される
 * 5. `listen()` でイベントを受信し、進捗インジケータを更新
 * 6. 完了後、resultPdfPath にダウンロードされた PDF のパスを保存
 */

// React 用の軽量状態管理ライブラリ Zustand のストア作成関数を読み込み
// グローバル状態（進捗・結果パス等）をコンポーネント間で共有するために使用する
import { create } from "zustand";
// Tauri の Rust コマンド呼び出し関数を読み込み
// invoke("command_name") で Rust 側の #[tauri::command] 関数を実行する
import { invoke } from "@tauri-apps/api/core";
// Tauri のイベント購読機能を読み込み
// listen("event_name", callback) で Rust 側から発射されたイベントを受信する
import { listen, type UnlistenFn } from "@tauri-apps/api/event";

/**
 * Rust 側 `OcrProgressPayload` に対応するフロントエンド型
 */
export interface OcrProgressPayload {
  /** 処理フェーズ（preparing / uploading / ocr / polling / downloading / completed など） */
  stage: string;
  /** ユーザー向けメッセージ */
  message: string;
  /** 現在の進捗値（ページ数など） */
  current?: number;
  /** 総進捗値（ページ数など） */
  total?: number;
}

/**
 * Rust 側 `BackendOcrResult` に対応するフロントエンド型
 */
export interface BackendOcrResult {
  /** backend 側で発行されたジョブ ID */
  jobId: string;
  /** 保存された PDF ファイルの絶対パス */
  outputPath: string;
}

/**
 * backend API 連携ストアの状態インターフェース
 */
export interface BackendApiState {
  /** 処理実行中フラグ */
  isProcessing: boolean;
  /** 進捗メッセージ */
  progressMessage: string;
  /** 現在処理済みのページ数 */
  progressCurrent: number;
  /** 処理対象の総ページ数 */
  progressTotal: number;
  /** 作成された PDF ファイルパス */
  resultPdfPath: string | null;

  /** backend API 経由で OCR 済み PDF を作成する */
  runBackendOcr: (
    sourcePath: string,
    sourceType: "folder" | "zip",
    outputPath: string
  ) => Promise<void>;
  /** 状態をリセット */
  reset: () => void;
}

/**
 * backend API 連携状態を管理する Zustand ストア
 */
export const useBackendApiStore = create<BackendApiState>((set) => ({
  isProcessing: false,
  progressMessage: "",
  progressCurrent: 0,
  progressTotal: 0,
  resultPdfPath: null,

  /**
   * backend API 経由で OCR 済み PDF を作成する
   *
   * 1. `ocr-progress` イベントリスナーを登録
   * 2. Rust 側 `run_backend_ocr` を呼び出し
   * 3. 進捗イベントを受信して progressCurrent / progressTotal / progressMessage を更新
   * 4. 完了後、resultPdfPath に PDF ファイルパスを保存
   *
   * @param sourcePath - 入力フォルダまたは ZIP ファイルの絶対パス
   * @param sourceType - "folder" | "zip"
   * @param outputPath - 出力先 PDF ファイルの絶対パス
   * @throws 処理エラー時
   */
  runBackendOcr: async (
    sourcePath: string,
    sourceType: "folder" | "zip",
    outputPath: string
  ) => {
    set({
      isProcessing: true,
      progressMessage: "backend OCR を開始しています...",
      progressCurrent: 0,
      progressTotal: 0,
      resultPdfPath: null,
    });

    let unlisten: UnlistenFn | null = null;

    try {
      unlisten = await listen<OcrProgressPayload>("ocr-progress", (event) => {
        const { current, total, message } = event.payload;
        set({
          progressMessage: message,
          progressCurrent: current ?? 0,
          progressTotal: total ?? 0,
        });
      });

      const result = await invoke<BackendOcrResult>("run_backend_ocr", {
        sourcePath,
        sourceType,
        outputPath,
      });

      set({
        resultPdfPath: result.outputPath,
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
   * ストアの状態をリセットする（初期値に戻す）
   */
  reset: () =>
    set({
      isProcessing: false,
      progressMessage: "",
      progressCurrent: 0,
      progressTotal: 0,
      resultPdfPath: null,
    }),
}));
