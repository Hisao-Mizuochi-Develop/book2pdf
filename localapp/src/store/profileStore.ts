/**
 * キャプチャプロファイル（電子書籍アプリ別設定）を管理する Zustand ストア
 *
 * 【プロファイルとは】
 * 各電子書籍リーダーアプリ（Kindle / BOOK☆WALKER など）に最適化された
 * キャプチャ設定のセット。ページ送り待機時間やウィンドウ検索キーワード、
 * クリック位置など、アプリごとに異なる値を一括で切り替えられる。
 *
 * 【データフロー】
 * 1. 起動時: `fetchProfiles()` で Rust 側 `get_builtin_profiles` を呼び出し、
 *    ビルトインプロファイル一覧を取得
 * 2. 選択: ユーザーがプロファイルセレクタで選択 → `selectProfile(id)` で状態更新
 * 3. 編集: ProfileEditor で値を変更 → `updateCustomProfile(id, data)` で上書き保存
 * 4. 復元: 「デフォルトに戻す」→ `resetProfile(id)` でカスタム値を破棄
 *
 * 【永続化方針】
 * 002002 の段階ではメモリ内のみ保持（ブラウザリロードでリセット）。
 * 将来の 007001（設定永続化）で localStorage または Rust 側 config ファイルへの
 * 保存・復元を実装する予定。
 */

import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

/**
 * コンテンツ領域トリミング設定（ピクセル単位）
 *
 * Rust 側 `CropInsets` に対応するフロントエンド型。
 * ウィンドウキャプチャ後に外枠・タイトルバーなどを除去するために使用する。
 */
export interface CropInsets {
  /** 上端からのトリミング量（ピクセル） */
  top: number;
  /** 右端からのトリミング量（ピクセル） */
  right: number;
  /** 下端からのトリミング量（ピクセル） */
  bottom: number;
  /** 左端からのトリミング量（ピクセル） */
  left: number;
}

/**
 * Rust 側 `models/capture_profile.rs` の `ProfileEntry` に対応するフロントエンド型
 *
 * serde の camelCase リネームにより、Rust の `page_turn_key` が
 * JavaScript 側では `pageTurnKey` として扱われる。
 */
export interface CaptureProfile {
  /** プロファイルの一意キー（例: "kindle"） */
  key: string;
  /** プロファイルの表示名（UI の選択肢として表示される） */
  name: string;
  /** ウィンドウタイトルに含まれるキーワード（大文字小文字区別なしで検索） */
  windowTitleKeyword: string;
  /** ページ送りに使うキー（"right" / "left" / "space" / "arrow" など） */
  pageTurnKey: string;
  /** ページ送り後の待ち時間（秒） */
  pageWait: number;
  /** 境界検出方式（"full"=全画面 / "manual"=手動クロップ） */
  boundaryMethod: string;
  /** クリック位置（"center"=中央 / "top_left"=左上） */
  clickPosition: string;
  /** キャプチャ前に対象ウィンドウを最前面へ持ってくるか */
  useBringToTop: boolean;
  /** プロセス名フィルタ（例: "Kindle.exe"）。空欄なら無効 */
  processName: string;
  /** ウィンドウ検索などのタイムアウト時間（秒） */
  timeoutSeconds: number;
  /** 失敗時の最大再試行回数 */
  maxRetries: number;
  /** コンテンツ領域トリミング設定（外枠除去用） */
  cropInsets: CropInsets;
}

/**
 * プロファイルストアの状態インターフェース
 */
export interface ProfileState {
  /** Rust 側から取得したビルトインプロファイル一覧（読み取り専用） */
  builtinProfiles: CaptureProfile[];
  /** ユーザーが編集したカスタムプロファイル（上書き値を保持） */
  customProfiles: Record<string, Partial<CaptureProfile>>;
  /** 現在選択中のプロファイルキー */
  selectedProfileKey: string | null;
  /** プロファイル一覧を Rust 側から取得して state に保存する */
  fetchProfiles: () => Promise<void>;
  /** 指定キーのプロファイルを選択する */
  selectProfile: (key: string) => void;
  /** カスタムプロファイルの値を更新する（ビルトインを部分的に上書き） */
  updateCustomProfile: (key: string, data: Partial<CaptureProfile>) => void;
  /** カスタム上書きを破棄してビルトインプロファイルの値に戻す */
  resetProfile: (key: string) => void;
  /** 指定キーのプロファイルを取得（カスタム上書きがあれば適用済み） */
  getEffectiveProfile: (key: string) => CaptureProfile | undefined;
}

/**
 * キャプチャプロファイルを管理する Zustand ストア
 *
 * 【customProfiles の構造】
 * Record<string, Partial<CaptureProfile>> 型で、キーはプロファイルキー、
 * 値は上書きしたいフィールドだけを含む Partial オブジェクト。
 * これにより、未変更フィールドはビルトイン値をそのまま利用できる。
 *
 * 【effectiveProfile の計算】
 * getEffectiveProfile() で、builtinProfiles から該当プロファイルを探し、
 * customProfiles に上書き値があれば Object.assign でマージして返す。
 */
export const useProfileStore = create<ProfileState>((set, get) => ({
  builtinProfiles: [],
  customProfiles: {},
  selectedProfileKey: null,

  /**
   * Rust 側の `get_builtin_profiles` コマンドを呼び出してプロファイル一覧を取得する
   *
   * アプリ起動時や、プロファイル一覧が必要なタイミングで呼び出す。
   * エラー時はコンソールにログ出力し、空配列のままにする。
   */
  fetchProfiles: async () => {
    try {
      const profiles = await invoke<CaptureProfile[]>("get_builtin_profiles");
      set({ builtinProfiles: profiles });
      // 初回取得時、最初のプロファイルを自動選択しておく
      if (profiles.length > 0 && !get().selectedProfileKey) {
        set({ selectedProfileKey: profiles[0].key });
      }
    } catch (err) {
      console.error("プロファイル取得エラー:", err);
    }
  },

  /**
   * プロファイルを選択する
   *
   * サイドバーやセレクタ UI でユーザーが選択した際に呼び出される。
   */
  selectProfile: (key) => set({ selectedProfileKey: key }),

  /**
   * カスタムプロファイルの値を更新する
   *
   * 既存のカスタム値とマージ（既存カスタム値を保持しつつ新しい値を上書き）。
   * スプレッド構文で新しいオブジェクトを生成し、React/Zustand の
   * 状態変更検知が正常に機能するようにする。
   */
  updateCustomProfile: (key, data) =>
    set((state) => ({
      customProfiles: {
        ...state.customProfiles,
        [key]: { ...state.customProfiles[key], ...data },
      },
    })),

  /**
   * カスタム上書きを破棄してビルトイン値に戻す
   *
   * delete 演算子で customProfiles から該当キーを削除。
   * 残りのキーはスプレッド構文で保持する。
   */
  resetProfile: (key) =>
    set((state) => {
      const next = { ...state.customProfiles };
      delete next[key];
      return { customProfiles: next };
    }),

  /**
   * 実効プロファイルを取得する（ビルトイン + カスタム上書きをマージ）
   *
   * @param key - プロファイルキー
   * @returns マージ済みのプロファイル、または見つからなければ undefined
   */
  getEffectiveProfile: (key) => {
    const builtin = get().builtinProfiles.find((p) => p.key === key);
    if (!builtin) return undefined;
    const custom = get().customProfiles[key];
    return custom ? { ...builtin, ...custom } : builtin;
  },
}));
