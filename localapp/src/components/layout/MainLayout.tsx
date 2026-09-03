/**
 * アプリケーションのメインレイアウトコンポーネント
 *
 * 【役割】
 * 画面全体を「左サイドバー + 右メインエリア」の2カラムレイアウトで構成する。
 * すべての機能ビュー（Capture / PDF / Trim / Export）はこのレイアウト内に描画される。
 *
 * 【レイアウト構成】
 * - Sidebar（左）: 幅 200px、機能ナビゲーションを配置
 * - main（右）: flex-1 で残りの領域を全て占有、スクロール可能
 */

// 左サイドバーナビゲーションコンポーネントを読み込み
// アプリの5機能へのタブ切り替え UI を提供する
import { Sidebar } from "./Sidebar";

/**
 * MainLayout の props インターフェース
 */
interface MainLayoutProps {
  /** メインエリアに描画する子要素（各機能ビューコンポーネント） */
  children: React.ReactNode;
}

/**
 * メインレイアウトコンポーネント
 *
 * @param children - サイドバーの右側に表示するコンテンツ
 * @returns 2カラムレイアウトの JSX 要素
 */
export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {/* 左サイドバー: 幅固定 200px */}
      <Sidebar />
      {/* 右メインエリア: 残りの領域を占有し、内容が溢れた場合はスクロール */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
