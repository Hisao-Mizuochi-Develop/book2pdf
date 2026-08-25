/**
 * アプリケーション全体の画面遷移（ナビゲーション）状態を管理する Zustand ストア
 *
 * 【Zustand とは】
 * React のグローバル状態管理ライブラリ。Context API よりもシンプルで
 * ボイラープレートが少なく、型推論も効きやすいのが特徴。
 * create() でストアを定義し、useNavigationStore() フックで各コンポーネントから
 * 必要な状態だけを subscribe して利用する。
 *
 * 【このストアの役割】
 * サイドバーで選択された現在のビュー（capture / trim / pdf / export / pdfCreation）を管理し、
 * App.tsx がこの状態を参照して対応する View コンポーネントを描画する。
 */

import { create } from "zustand";

/**
 * アプリケーション内の5つの機能ビューを表す型
 *
 * - capture: 電子書籍キャプチャ機能（UC002）
 * - pdf: PDF読込・画像展開機能（UC003）
 * - trim: 画像トリミング機能（UC004）
 * - export: ZIP出力機能（UC005）
 * - pdfCreation: OCR済みPDF作成機能（UC006）
 */
export type AppView = "capture" | "trim" | "pdf" | "export" | "pdfCreation";

/**
 * ナビゲーションストアの状態インターフェース
 *
 * Zustand ではインターフェース（型）を明示的に定義することで、
 * TypeScript の型安全性を確保する。setView は状態を更新するアクション関数。
 */
export interface NavigationState {
  /** 現在アクティブなビュー（初期値: capture = 電子書籍） */
  currentView: AppView;
  /** 指定したビューに切り替えるアクション関数 */
  setView: (view: AppView) => void;
}

/**
 * ナビゲーション状態を管理する Zustand ストア
 *
 * 【なぜ capture を初期値とするのか】
 * アプリの主要な用途は「電子書籍の画面キャプチャ」であるため、
 * 起動時に最もよく使うタブを先に表示することでユーザーの操作ステップを減らす。
 */
export const useNavigationStore = create<NavigationState>((set) => ({
  currentView: "capture",
  setView: (view) => set({ currentView: view }),
}));
