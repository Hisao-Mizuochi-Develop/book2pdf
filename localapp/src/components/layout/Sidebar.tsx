/**
 * 左サイドバーナビゲーションコンポーネント
 *
 * 【役割】
 * アプリケーションの5つの機能（電子書籍キャプチャ / PDF読込 / トリミング / ZIP作成 / PDF作成）を
 * 垂直リストで表示し、ユーザーが現在のビューを切り替えられるようにする。
 *
 * 【デザイン方針】
 * - Apple HIG 風: 白基調・余白多め・控えめな角丸・左端アクセントライン
 * - アクティブ状態: 背景色 `#F5F5F7` + 左端 3px の黒ラインで視覚的に示す
 * - 非アクティブ: 薄いグレーの文字色、ホバーで背景色変化
 *
 * 【状態管理】
 * `useNavigationStore` を subscribe して `currentView` を取得。
 * ユーザーが項目をクリックすると `setView()` を呼び出して状態を更新。
 * 状態変更は App.tsx に伝搬し、対応するビューコンポーネントが再描画される。
 */

import { Camera, Crop, FileUp, Package, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { type AppView, useNavigationStore } from "@/store/navigationStore";

/**
 * ナビゲーション項目の型定義
 */
interface NavItem {
  /** ビューの識別子（Zustand ストアと対応） */
  view: AppView;
  /** サイドバーに表示される日本語ラベル */
  label: string;
  /** lucide-react アイコンコンポーネント */
  icon: React.ElementType;
}

/**
 * サイドバーに配置するナビゲーション項目一覧
 *
 * 【並び順の意図】
 * 電子書籍キャプチャ → PDF読込 → トリミング → ZIP作成 → PDF作成 は、
 * 実際の作業フロー順に対応している。
 * キャプチャ → PDF読込 → トリミング → ZIP出力 → OCR済みPDF作成 の順でユーザーが作業を進める。
 */
const navItems: NavItem[] = [
  { view: "capture", label: "電子書籍キャプチャ", icon: Camera },
  { view: "pdf", label: "PDFキャプチャ", icon: FileUp },
  { view: "trim", label: "トリミング", icon: Crop },
  { view: "export", label: "ZIP作成", icon: Package },
  { view: "pdfCreation", label: "PDF作成", icon: FileText },
];

/**
 * サイドバーナビゲーションコンポーネント
 *
 * @returns 左側固定幅の垂直ナビゲーションバー
 */
export function Sidebar() {
  // Zustand から現在アクティブなビューと切り替え関数を取得
  const { currentView, setView } = useNavigationStore();

  return (
    <aside className="w-[200px] flex flex-col border-r bg-background">
      {/* アプリロゴエリア */}
      <div className="flex h-14 items-center px-5">
        <span className="text-sm font-semibold tracking-tight">Book Capture</span>
      </div>
      {/* ナビゲーションリスト */}
      <nav className="flex flex-1 flex-col gap-1 px-3 py-4">
        {navItems.map(({ view, label, icon: Icon }) => {
          const active = currentView === view;
          return (
            <Button
              key={view}
              variant="ghost"
              onClick={() => setView(view)}
              className={cn(
                // 基本スタイル: 高さ固定、左寄せ、角丸、遷移アニメーション
                "h-10 justify-start gap-3 rounded-lg px-3 text-sm font-normal transition-colors",
                active
                  ? // アクティブ状態: 背景色 + 太字 + 左端アクセントライン
                    "bg-[#F5F5F7] text-foreground font-medium relative before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2 before:h-5 before:w-[3px] before:rounded-r-full before:bg-foreground"
                  : // 非アクティブ状態: 薄い文字色、ホバーで背景色変化
                    "text-muted-foreground hover:bg-[#F5F5F7] hover:text-foreground"
              )}
            >
              <Icon className="size-4" />
              {label}
            </Button>
          );
        })}
      </nav>
    </aside>
  );
}
