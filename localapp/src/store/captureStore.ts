/**
 * 連続キャプチャの進捗・状態を管理する Zustand ストア
 *
 * 【データフロー】
 * 1. ユーザーが「連続キャプチャ開始」ボタンをクリック
 * 2. `startCapture()` で Rust 側 `start_continuous_capture` を invoke
 * 3. Rust 側から `capture-progress` イベントが emit される
 * 4. `listen()` でイベントを受信し、ストアの状態を更新
 * 5. UI（CaptureProgress コンポーネント）はストアを購読して進捗を表示
 *
 * 【状態遷移】
 * idle → capturing → [page_turn → waiting → capturing] → completed/stopped/error
 */

import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";

/**
 * Rust 側 `ProgressPayload` に対応するフロントエンド型
 *
 * serde の camelCase リネームにより、Rust の `capture_folder` が
 * JavaScript 側では `captureFolder` として扱われる。
 */
export interface ProgressPayload {
  /** 現在キャプチャ済みのページ数 */
  current: number;
  /** 予想総ページ数 */
  total: number;
  /** ステータス種別 */
  status: CaptureStatus;
  /** ユーザー向けメッセージ */
  message: string;
  /** キャプチャ画像の保存先フォルダパス */
  captureFolder: string | null;
}

/**
 * 連続キャプチャのステータス種別
 *
 * Rust 側と同じ値を使用し、フロントエンドで表示テキストや色を切り替える。
 */
export type CaptureStatus =
  | "idle"
  | "capturing"
  | "page_turn"
  | "waiting"
  | "completed"
  | "stopped"
  | "error";

/**
 * 連続キャプチャストアの状態インターフェース
 */
export interface CaptureState {
  /** 連続キャプチャ実行中か */
  isCapturing: boolean;
  /** 現在キャプチャ済みのページ数 */
  currentPage: number;
  /** 予想総ページ数（完了までは current と同値） */
  totalPages: number;
  /** 現在のステータス */
  status: CaptureStatus;
  /** ユーザー向けメッセージ */
  message: string;
  /** キャプチャ画像の保存先フォルダパス */
  captureFolder: string | null;
  /** 進捗イベントのリスナー解除関数（停止時に呼び出す） */
  unlistenFn: UnlistenFn | null;

  /** 連続キャプチャ開始（リスナー登録 + Rust コマンド呼び出し） */
  startCapture: (profile: unknown, bookTitle: string) => Promise<void>;
  /** 連続キャプチャ停止 */
  stopCapture: () => Promise<void>;
  /** 進捗イベントを受信して状態を更新する */
  setProgress: (payload: ProgressPayload) => void;
  /** リスナー解除関数を設定する */
  setUnlisten: (fn: UnlistenFn | null) => void;
  /** エラー状態を設定する */
  setError: (message: string) => void;
}

/**
 * 連続キャプチャ状態を管理する Zustand ストア
 *
 * 進捗イベントは `listen("capture-progress")` で受信し、isCapturing を
 * true の間は UI に進捗バーとステータスメッセージを表示する。
 * 完了・停止・エラー時には isCapturing を false に戻す。
 */
export const useCaptureStore = create<CaptureState>((set, get) => ({
  isCapturing: false,
  currentPage: 0,
  totalPages: 0,
  status: "idle",
  message: "",
  captureFolder: null,
  unlistenFn: null,

  /**
   * 連続キャプチャを開始する
   *
   * 1. 既存リスナーがあれば解除
   * 2. `capture-progress` イベントのリスナーを登録
   * 3. Rust 側 `start_continuous_capture` を呼び出し
   * 4. 開始時の状態を idle → capturing に更新
   *
   * @param profile - 選択中のキャプチャプロファイル（profileStore から取得）
   * @param bookTitle - 保存フォルダ名に使用する書籍タイトル
   */
  startCapture: async (profile, bookTitle) => {
    // 既存リスナーがあれば解除（重複防止）
    const prevUnlisten = get().unlistenFn;
    if (prevUnlisten) {
      prevUnlisten();
    }

    // 進捗イベントリスナーを登録
    const unlisten = await listen<ProgressPayload>("capture-progress", (event) => {
      get().setProgress(event.payload);
    });

    set({ unlistenFn: unlisten, status: "capturing" });

    try {
      // Rust 側で連続キャプチャを開始
      await invoke("start_continuous_capture", {
        profile,
        bookTitle,
      });
    } catch (err) {
      // 開始失敗時はリスナーを解除してエラー状態にする
      unlisten();
      set({
        unlistenFn: null,
        status: "error",
        message: err instanceof Error ? err.message : String(err),
        isCapturing: false,
      });
    }
  },

  /**
   * 連続キャプチャを停止する
   *
   * Rust 側 `stop_continuous_capture` を呼び出し、停止フラグをセットする。
   * リスナーは最終イベント（"stopped"）を受信してから解除される。
   */
  stopCapture: async () => {
    try {
      await invoke("stop_continuous_capture");
    } catch (err) {
      console.error("停止コマンドエラー:", err);
    }
  },

  /**
   * 進捗イベントを受信して状態を更新する
   *
   * `capture-progress` イベントのペイロードを受け取り、ストアの状態を更新する。
   * 完了・停止・エラーの場合は isCapturing を false に戻し、
   * リスナー解除関数を呼び出してイベント受信を停止する。
   *
   * @param payload - Rust 側から emit された進捗ペイロード
   */
  setProgress: (payload) => {
    const isTerminal =
      payload.status === "completed" ||
      payload.status === "stopped" ||
      payload.status === "error";

    set({
      isCapturing: !isTerminal,
      currentPage: payload.current,
      totalPages: payload.total,
      status: payload.status,
      message: payload.message,
      captureFolder: payload.captureFolder,
    });

    // 終端状態ならリスナーを解除
    if (isTerminal) {
      const unlisten = get().unlistenFn;
      if (unlisten) {
        unlisten();
        set({ unlistenFn: null });
      }
    }
  },

  /**
   * リスナー解除関数を設定する
   *
   * @param fn - `listen()` が返した UnlistenFn、または null
   */
  setUnlisten: (fn) => set({ unlistenFn: fn }),

  /**
   * エラー状態を設定する
   *
   * フロントエンド側で発生したエラーをストアに反映する。
   *
   * @param message - エラーメッセージ
   */
  setError: (message) =>
    set({
      status: "error",
      message,
      isCapturing: false,
    }),
}));
