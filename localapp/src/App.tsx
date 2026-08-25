/**
 * アプリケーションのルートコンポーネント
 *
 * 【役割】
 * ナビゲーションストア（Zustand）で管理される現在のビュー（currentView）を参照し、
 * 対応する機能ビューコンポーネントを MainLayout 内に描画する。
 *
 * 【ビュー切り替えの仕組み】
 * 1. Sidebar.tsx でユーザーがタブをクリック → `setView()` で状態更新
 * 2. App.tsx で `useNavigationStore` を subscribe して `currentView` を取得
 * 3. `viewMap` オブジェクトから対応するコンポーネントを動的に選択
 * 4. `<View />` で描画（React は状態変更を検知して再レンダリング）
 *
 * 【なぜ viewMap を使うのか】
 * switch 文や if-else よりも宣言的で型安全。
 * AppView 型の網羅性チェックが効き、新しいビューを追加する際に
 * ここのマッピングを忘れると TypeScript が即座にエラーを出す。
 */

import { MainLayout } from "@/components/layout/MainLayout";
import { useNavigationStore } from "@/store/navigationStore";
import { CaptureView } from "@/views/CaptureView";
import { TrimView } from "@/views/TrimView";
import { PdfImportView } from "@/views/PdfImportView";
import { ExportView } from "@/views/ExportView";
import { PdfCreationView } from "@/views/PdfCreationView";
import type { AppView } from "@/store/navigationStore";

/**
 * ビュー名（AppView）と対応するコンポーネントのマッピング
 *
 * Record<AppView, React.ComponentType> で、すべての AppView 値に
 * 対応するコンポーネントが必ず設定されていることを型レベルで保証する。
 */
const viewMap: Record<AppView, React.ComponentType> = {
  capture: CaptureView,     // 電子書籍キャプチャ（UC002）
  trim: TrimView,           // 画像トリミング（UC004）
  pdf: PdfImportView,       // PDF読込・展開（UC003）
  export: ExportView,       // ZIP出力（UC005）
  pdfCreation: PdfCreationView, // OCR済みPDF作成（UC006）
};

/**
 * アプリケーションのルートコンポーネント
 *
 * @returns MainLayout でラップされた現在のビューコンポーネント
 */
function App() {
  // Zustand ストアから現在のビューを取得（状態が変わると自動的に再レンダリング）
  const currentView = useNavigationStore((state) => state.currentView);

  // viewMap から対応するコンポーネントを取得（型安全な動的コンポーネント選択）
  const View = viewMap[currentView];

  return (
    <MainLayout>
      <View />
    </MainLayout>
  );
}

export default App;
