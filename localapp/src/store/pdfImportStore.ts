/**
 * PDF 読込機能の状態を管理する Zustand ストア
 *
 * 【ユースケース 003 — PDF 読込】
 * - PDF ファイル選択
 * - 出力先フォルダ選択
 * - DPI（200 / 300 / 400）選択
 * - ファイルサイズ目安表示
 * - PDF → PNG 画像展開の進捗管理
 * - 完了後のトリミングタブへの自動引き継ぎ
 *
 * 【データフロー】
 * 1. ユーザーが PDF ファイルと出力先フォルダを選択
 * 2. DPI を選択（デフォルト 300）
 * 3. 「PDF を画像化」ボタンで Rust 側 `extract_pdf_to_images` を invoke
 * 4. Rust 側から `pdf-progress` イベントが emit される
 * 5. 完了後、`useTrimStore.loadFolder()` でトリミングタブに自動引き継ぎ
 * 6. `useNavigationStore.setView("trim")` でタブを切り替え
 */

import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import { open } from "@tauri-apps/plugin-dialog";
import { useTrimStore } from "@/store/trimStore";
import { useExportStore } from "@/store/exportStore";
import { useNavigationStore } from "@/store/navigationStore";

/** PDF 読込完了後の結果状態 */
export interface PdfImportResult {
  /** 画像化されたフォルダパス */
  folderPath: string;
  /** 画像枚数 */
  imageCount: number;
}

/** PDF → 画像変換の進捗イベントペイロード（Rust 側 `PdfProgressPayload` に対応） */
export interface PdfProgressPayload {
  /** 現在処理済みのページ数 */
  current: number;
  /** PDF の総ページ数 */
  total: number;
  /** ユーザー向けメッセージ */
  message: string;
}

/** PDF 読込画面の状態インターフェース */
export interface PdfImportState {
  /** 選択中の PDF ファイルパス */
  pdfPath: string | null;
  /** 画像出力先フォルダパス */
  outputFolder: string | null;
  /** レンダリング DPI（200 / 300 / 400） */
  dpi: number;
  /** 変換実行中か */
  isLoading: boolean;
  /** 現在処理済みページ数 */
  progressCurrent: number;
  /** PDF の総ページ数 */
  progressTotal: number;
  /** エラーメッセージ */
  error: string | null;
  /** 変換後の画像枚数 */
  outputImageCount: number;
  /** ユーザー向け進捗メッセージ */
  progressMessage: string;
  /** 進捗イベントのリスナー解除関数 */
  unlistenFn: UnlistenFn | null;
  /** 変換完了後の結果（完了表示用） */
  result: PdfImportResult | null;

  /** DPI を設定する */
  setDpi: (dpi: number) => void;
  /** PDF ファイル選択ダイアログを開く */
  selectPdf: () => Promise<void>;
  /** 出力先フォルダ選択ダイアログを開く */
  selectOutputFolder: () => Promise<void>;
  /** PDF → PNG 画像展開を実行する */
  extractPdf: () => Promise<void>;
  /** 進捗イベントを受信して状態を更新する */
  setProgress: (payload: PdfProgressPayload) => void;
  /** 出力フォルダを開く（完了後アクション） */
  openOutputFolder: () => Promise<void>;
  /** トリミングタブに手動で進む（完了後アクション） */
  goToTrim: () => Promise<void>;
  /** 状態をリセットする */
  reset: () => void;
}

/** DPI 選択肢（ユーザーが選べる解像度） */
export const PDF_DPI_OPTIONS = [200, 300, 400] as const;

/** デフォルト状態値 */
const defaultState = {
  pdfPath: null,
  outputFolder: null,
  dpi: 300,
  isLoading: false,
  progressCurrent: 0,
  progressTotal: 0,
  error: null,
  outputImageCount: 0,
  progressMessage: "",
  unlistenFn: null,
  result: null,
};

/**
 * PDF 読込状態を管理する Zustand ストア
 *
 * ファイル選択から画像展開、トリミングタブへの引き継ぎまでを一括で管理する。
 */
export const usePdfImportStore = create<PdfImportState>((set, get) => ({
  ...defaultState,

  /**
   * DPI を設定する
   *
   * @param dpi - 200 / 300 / 400 のいずれか
   */
  setDpi: (dpi: number) => {
    set({ dpi });
  },

  /**
   * PDF ファイル選択ダイアログを開く
   *
   * フィルタは PDF のみとし、複数選択は不可。
   * 選択後、ファイル名から拡張子を除いた名前で Pictures/BookCapture/<basename>/
   * をデフォルトの出力先として自動設定する。
   */
  selectPdf: async () => {
    try {
      const selected = await open({
        directory: false,
        multiple: false,
        filters: [
          {
            name: "PDF ファイル",
            extensions: ["pdf"],
          },
        ],
      });

      if (selected && typeof selected === "string") {
        // 003003: PDF ファイル名からデフォルト出力フォルダを自動設定
        let defaultOutputFolder: string | null = null;
        try {
          defaultOutputFolder = await invoke<string>(
            "get_pdf_default_output_folder",
            { pdfPath: selected }
          );
        } catch (folderErr) {
          // フォルダ自動設定に失敗しても、PDF 選択自体は成功させる
          // ユーザーは手動で出力先を選択可能
          console.warn(
            "デフォルト出力フォルダの取得に失敗しました:",
            folderErr
          );
        }

        set({
          pdfPath: selected,
          outputFolder: defaultOutputFolder,
          error: null,
          result: null,
        });
      }
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : String(err),
      });
    }
  },

  /**
   * 出力先フォルダ選択ダイアログを開く
   */
  selectOutputFolder: async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
      });

      if (selected && typeof selected === "string") {
        set({ outputFolder: selected, error: null });
      }
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : String(err),
      });
    }
  },

  /**
   * PDF → PNG 画像展開を実行する
   *
   * 処理フロー：
   * 1. 既存リスナーがあれば解除（重複防止）
   * 2. `pdf-progress` イベントのリスナーを登録
   * 3. 入力値のバリデーション
   * 4. Rust 側 `extract_pdf_to_images` を invoke
   * 5. 完了後、result 状態を設定し完了表示を行う
   *
   * 003003 改修により、完了後の自動遷移は廃止。
   * ユーザーは「フォルダを開く」「トリミングに進む」ボタンで次のアクションを選択する。
   */
  extractPdf: async () => {
    const { pdfPath, outputFolder, dpi } = get();

    // 既存リスナーがあれば解除
    const prevUnlisten = get().unlistenFn;
    if (prevUnlisten) {
      prevUnlisten();
    }

    // 入力値のバリデーション
    if (!pdfPath) {
      set({ error: "PDF ファイルを選択してください" });
      return;
    }
    if (!outputFolder) {
      set({ error: "出力先フォルダを選択してください" });
      return;
    }

    // 進捗イベントリスナーを登録
    let unlisten: UnlistenFn | null = null;
    try {
      unlisten = await listen<PdfProgressPayload>("pdf-progress", (event) => {
        get().setProgress(event.payload);
      });
      // ボタン押下直後から進捗エリアを表示するため、
      // ページ数が判明する前の不定形状態を先に設定する。
      set({
        unlistenFn: unlisten,
        isLoading: true,
        error: null,
        progressCurrent: 0,
        progressTotal: 0,
        progressMessage: "PDFを読み込んでいます...",
        result: null,
      });
    } catch (err) {
      set({
        error:
          "進捗イベントの登録に失敗しました: " +
          (err instanceof Error ? err.message : String(err)),
        isLoading: false,
      });
      return;
    }

    try {
      // Rust 側で PDF → PNG 画像展開を実行
      // Tauri の async コマンドでも、呼び出し直後は JavaScript メインスレッドが
      // 一瞬ブロックされ `pdf-progress` イベントの受信が遅れることがある。
      // マイクロタスクで実行を遅らせることで、イベントリスナーが確実に登録・発火される
      // タイミングを作り、進捗表示がスムーズに反映されるようにする。
      const resultFolder = await Promise.resolve().then(() =>
        invoke<string>("extract_pdf_to_images", {
          pdfPath,
          outputFolder,
          dpi,
        })
      );

      // 完了状態を更新
      // 003003: 自動遷移せず、result 状態に完了情報を保持して完了表示を行う
      const completedImageCount = get().progressTotal;
      set({
        isLoading: false,
        outputImageCount: completedImageCount,
        result: {
          folderPath: resultFolder,
          imageCount: completedImageCount,
        },
      });

      // 003003: 取り込み完了後は出力フォルダをトリミング・ZIP 出力の入力フォルダに反映
      await useTrimStore.getState().loadFolder(resultFolder);
      useExportStore.getState().setSourceFolder(resultFolder);
    } catch (err) {
      if (unlisten) {
        unlisten();
      }
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : String(err),
        unlistenFn: null,
      });
    }
  },

  /**
   * 出力フォルダを開く
   *
   * 完了後の「フォルダを開く」ボタンから呼ばれる。
   * Rust 側 `open_capture_folder` を利用して Finder/Explorer を開く。
   */
  openOutputFolder: async () => {
    const { result } = get();
    if (!result) {
      set({ error: "フォルダを開く前に変換を完了してください" });
      return;
    }

    try {
      await invoke("open_capture_folder", { folderPath: result.folderPath });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : String(err),
      });
    }
  },

  /**
   * トリミングタブに手動で進む
   *
   * 完了後の「トリミングに進む」ボタンから呼ばれる。
   * 変換結果フォルダを trimStore に読み込み、ナビゲーションを切り替える。
   */
  goToTrim: async () => {
    const { result } = get();
    if (!result) {
      set({ error: "トリミングに進む前に変換を完了してください" });
      return;
    }

    try {
      await useTrimStore.getState().loadFolder(result.folderPath);
      useNavigationStore.getState().setView("trim");
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : String(err),
      });
    }
  },

  /**
   * 進捗イベントを受信して状態を更新する
   *
   * @param payload - Rust 側から emit された進捗ペイロード
   */
  setProgress: (payload: PdfProgressPayload) => {
    set({
      progressCurrent: payload.current,
      progressTotal: payload.total,
      progressMessage: payload.message,
    });

    // 完了時（current == total かつ total > 0）はリスナーを解除
    if (payload.current === payload.total && payload.total > 0) {
      const unlisten = get().unlistenFn;
      if (unlisten) {
        unlisten();
        set({ unlistenFn: null });
      }
    }
  },

  /**
   * 状態をリセットする
   */
  reset: () => {
    const unlisten = get().unlistenFn;
    if (unlisten) {
      unlisten();
    }
    set(defaultState);
  },
}));

/**
 * 推定ファイルサイズを計算する
 *
 * A4 サイズ（210mm x 297mm ≒ 8.27 x 11.69 inch）を基準に、
 * DPI とページ数から概算の未圧縮 PNG サイズを計算する。
 * 実際の PDF ページサイズは取得できないため、一般的な文書サイズで目安を示す。
 *
 * @param dpi - レンダリング DPI
 * @param pageCount - PDF のページ数（未知の場合は null）
 * @returns 目安ファイルサイズの文字列表現（例: "約 5.2 MB / ページ"）
 */
export function estimatePdfImageSize(dpi: number, pageCount: number | null): string {
  // A4 縦向きを inch 換算
  const widthInch = 8.27;
  const heightInch = 11.69;
  const bytesPerPixel = 4; // RGBA

  const widthPixels = Math.round(widthInch * dpi);
  const heightPixels = Math.round(heightInch * dpi);
  const bytesPerPage = widthPixels * heightPixels * bytesPerPixel;
  const mbPerPage = bytesPerPage / (1024 * 1024);

  if (pageCount && pageCount > 0) {
    const totalMb = mbPerPage * pageCount;
    return `約 ${formatFileSize(totalMb)}（${pageCount} ページ / ${dpi} DPI）`;
  }

  return `約 ${formatFileSize(mbPerPage)} / ページ（${dpi} DPI）`;
}

/**
 * MB 値を見やすい文字列にフォーマットする
 *
 * @param mb - メガバイト単位の値
 * @returns 例: "1.2 MB", "850 KB"
 */
function formatFileSize(mb: number): string {
  if (mb >= 1) {
    return `${mb.toFixed(1)} MB`;
  }
  const kb = mb * 1024;
  return `${Math.round(kb)} KB`;
}
