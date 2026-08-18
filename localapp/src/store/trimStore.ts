/**
 * トリミング画面用の Zustand ストア
 *
 * 【004001改修版】
 * - 1ページプレビュー表示（前次ページナビゲーション付き）
 * - トリミング調整UI（上下左右ピクセル入力）
 * - ボタンクリックによるプレビュー更新
 *
 * 管理する状態：
 * - 入力フォルダパス
 * - フォルダ内の画像ファイル名一覧
 * - 現在のページインデックス（0-based）
 * - トリミング値（上/右/下/左）
 * - 画像読み込み中フラグ/エラー
 *
 * captureStore（002004）との連携：
 * TrimView.tsx で captureStore.lastCaptureFolder を監視し、
 * 存在する場合は自動的に trimStore.loadFolder() を呼び出す。
 */

import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

/**
 * 4辺のトリミング値を表す型
 *
 * 画像の外縁から内部に向かって切り取るピクセル数。
 * 初期値はすべて 0（トリミングなし）。
 */
export interface CropInsets {
  /** 上側トリミング値（ピクセル） */
  top: number;
  /** 右側トリミング値（ピクセル） */
  right: number;
  /** 下側トリミング値（ピクセル） */
  bottom: number;
  /** 左側トリミング値（ピクセル） */
  left: number;
}

/**
 * トリミング画面の状態を管理する Zustand ストア
 */
interface TrimState {
  /** 入力フォルダの絶対パス */
  folderPath: string | null;
  /** フォルダ内の画像ファイル名一覧（ファイル名順でソート済み） */
  imageFiles: string[];
  /** 現在表示中の画像インデックス（0-based） */
  currentImageIndex: number;
  /** トリミング値（上/右/下/左） */
  cropInsets: CropInsets;
  /** トリミング適用後のプレビュー画像（Base64 data URL） */
  previewImage: string | null;
  /** プレビュー読み込み中フラグ */
  isPreviewLoading: boolean;
  /** 画像一覧読み込み中フラグ */
  isLoading: boolean;
  /** エラーメッセージ */
  error: string | null;

  /** フォルダパスと画像一覧をセット */
  setFolderPath: (folderPath: string) => void;
  /** トリミング値を更新 */
  setCropInsets: (insets: Partial<CropInsets>) => void;
  /** トリミング値をすべてリセット（0に戻す） */
  resetCropInsets: () => void;
  /** 前のページへ移動 */
  prevPage: () => void;
  /** 次のページへ移動 */
  nextPage: () => void;
  /** 指定インデックスのページへ移動 */
  goToPage: (index: number) => void;
  /** トリミングを適用したプレビューを更新 */
  loadPreview: () => Promise<void>;
  /** フォルダを読み込み、画像一覧を取得 */
  loadFolder: (folderPath: string) => Promise<void>;
  /** 状態をリセット */
  reset: () => void;
}

/**
 * trimStore のデフォルト状態値
 *
 * 未選択状態を表す初期値。
 */
const defaultState = {
  folderPath: null,
  imageFiles: [],
  currentImageIndex: 0,
  cropInsets: { top: 0, right: 0, bottom: 0, left: 0 } as CropInsets,
  previewImage: null,
  isPreviewLoading: false,
  isLoading: false,
  error: null,
};

/**
 * トリミング画面用 Zustand ストア
 *
 * @example
 * ```tsx
 * const folderPath = useTrimStore((state) => state.folderPath);
 * const loadFolder = useTrimStore((state) => state.loadFolder);
 * await loadFolder("/Users/xxx/Pictures/BookCapture/MyBook");
 * ```
 */
export const useTrimStore = create<TrimState>((set, get) => ({
  ...defaultState,

  /**
   * フォルダパスと画像一覧をセットする
   */
  setFolderPath: (folderPath: string) => {
    set({ folderPath });
  },

  /**
   * トリミング値を部分的に更新する
   *
   * @param insets - 更新する辺の値。指定しなかった辺は現在値を維持。
   */
  setCropInsets: (insets: Partial<CropInsets>) => {
    set((state) => ({
      cropInsets: { ...state.cropInsets, ...insets },
    }));
  },

  /**
   * トリミング値をすべて 0 にリセットする
   */
  resetCropInsets: () => {
    set({ cropInsets: { top: 0, right: 0, bottom: 0, left: 0 } });
  },

  /**
   * 前のページへ移動する
   *
   * 先頭ページの場合は何もしない（インデックスを負にしない）。
   */
  prevPage: () => {
    set((state) => {
      if (state.imageFiles.length === 0) return state;
      const newIndex = Math.max(0, state.currentImageIndex - 1);
      return { currentImageIndex: newIndex, previewImage: null };
    });
  },

  /**
   * 次のページへ移動する
   *
   * 最終ページの場合は何もしない（インデックスを超えない）。
   */
  nextPage: () => {
    set((state) => {
      if (state.imageFiles.length === 0) return state;
      const newIndex = Math.min(
        state.imageFiles.length - 1,
        state.currentImageIndex + 1
      );
      return { currentImageIndex: newIndex, previewImage: null };
    });
  },

  /**
   * 指定インデックスのページへ移動する
   *
   * @param index - 移動先のインデックス。範囲外の場合はクランプする。
   */
  goToPage: (index: number) => {
    set((state) => {
      if (state.imageFiles.length === 0) return state;
      const clamped = Math.max(0, Math.min(state.imageFiles.length - 1, index));
      return { currentImageIndex: clamped, previewImage: null };
    });
  },

  /**
   * 現在のページ画像にトリミングを適用したプレビューを読み込む
   *
   * 処理フロー：
   * 1. 現在のページインデックスからファイル名を特定
   * 2. 現在の cropInsets を取得
   * 3. Rust 側の `apply_crop_preview` にパスとトリミング値を渡す
   * 4. トリミング後の画像（Base64 PNG）をプレビューとして表示
   *
   * cropInsets がすべて 0 の場合でも同じコマンドを呼び出すことで、
   * 処理の一貫性を保つ。Rust 側で元画像をそのまま返す。
   */
  loadPreview: async () => {
    const state = get();
    const { folderPath, imageFiles, currentImageIndex, cropInsets } = state;
    if (!folderPath || imageFiles.length === 0) return;

    const filename = imageFiles[currentImageIndex];
    if (!filename) return;

    set({ isPreviewLoading: true, error: null });
    try {
      const base64 = await invoke<string>("apply_crop_preview", {
        folderPath,
        filename,
        top: cropInsets.top,
        right: cropInsets.right,
        bottom: cropInsets.bottom,
        left: cropInsets.left,
      });
      set({
        previewImage: `data:image/png;base64,${base64}`,
        isPreviewLoading: false,
      });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : String(err),
        isPreviewLoading: false,
      });
    }
  },

  /**
   * 指定フォルダ内の画像一覧を Rust 側から取得して state に保存する
   *
   * 処理フロー：
   * 1. `list_capture_images` で PNG 画像のファイル名一覧を取得
   * 2. 取得したファイル名一覧を `imageFiles` state に保存
   * 3. ファイルが存在する場合、インデックス 0 を自動選択
   * 4. 画像があれば自動的にプレビューを読み込む
   * 5. エラー時は `error` state にメッセージを保存
   *
   * 注意: `currentImageIndex` の初期値も 0 なので、React の useEffect だけでは
   * フォルダ読み込み後のプレビュー自動表示が発火しない。そのため本関数内で
   * 直接 `loadPreview()` を呼び出すことで確実にプレビューを表示する。
   *
   * @param folderPath - 読み込むフォルダの絶対パス
   */
  loadFolder: async (folderPath: string) => {
    set({ isLoading: true, error: null, previewImage: null });
    try {
      const filenames = await invoke<string[]>("list_capture_images", {
        folderPath,
      });
      set({
        folderPath,
        imageFiles: filenames,
        currentImageIndex: 0,
        isLoading: false,
      });
      // 画像があればプレビューを自動読み込み
      // useEffect では currentImageIndex が 0→0 で変化しないため発火しないため、
      // ここで直接呼び出す必要がある
      if (filenames.length > 0) {
        await get().loadPreview();
      }
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : String(err),
        isLoading: false,
      });
    }
  },

  /**
   * 全状態をデフォルト値にリセットする
   */
  reset: () => {
    set(defaultState);
  },
}));
