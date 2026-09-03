// React のコア機能を読み込みます
// React コンポーネントの作成・レンダリングに必要な基本ライブラリ
import React from "react";
// React 18 の新しいレンダリング API を読み込みます
// createRoot: 従来の ReactDOM.render に代わる新しいエントリポイント作成関数
import ReactDOM from "react-dom/client";
// アプリケーションのルートコンポーネントを読み込みます
// ナビゲーション・レイアウト・各ビューの統合を担当する最上位コンポーネント
import App from "./App";
// Tailwind CSS ベースのグローバルスタイルシートを読み込みます
// ダークモード対応の CSS 変数やユーティリティクラスを定義
import "./index.css";

/**
 * OS の外観モード（ライト / ダーク）を検出し、HTML 要素に .dark クラスを付与する。
 *
 * 【なぜこの処理が必要か】
 * 本アプリは CSS カスタムプロパティによるテーマ切り替えを採用しており、
 * ダークモード時は html 要素に .dark クラスが必要。Tailwind CSS v4 の
 * @custom-variant dark (&:is(.dark *)) がこのクラスをトリガーとして動作する。
 *
 * 【実装方針】
 * 1. window.matchMedia('(prefers-color-scheme: dark)') で現在の OS 設定を取得
 * 2. matches が true なら document.documentElement.classList.add('dark')
 * 3. change イベントリスナーを登録し、OS 設定の変更をリアルタイムで反映
 */
function initTheme(): void {
  const darkModeQuery = window.matchMedia("(prefers-color-scheme: dark)");

  /**
   * 現在の OS 外観設定に応じて .dark クラスを切り替える。
   * @param isDark - OS がダークモードかどうか
   */
  const applyTheme = (isDark: boolean): void => {
    if (isDark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  // 初回: ページ読み込み時の OS 設定を反映
  applyTheme(darkModeQuery.matches);

  // 継続: OS 設定変更をリアルタイムで監視（ユーザーがシステム設定を切り替えた際に自動反映）
  darkModeQuery.addEventListener("change", (event) => {
    applyTheme(event.matches);
  });
}

// OS 外観モード検出を初期化（React レンダリングより先に実行して画面ちらつきを防止）
initTheme();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
