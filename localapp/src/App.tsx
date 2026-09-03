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

// 画面レイアウトコンポーネント（Sidebar + メインコンテンツエリア）を読み込みます
// アプリ全体の共通レイアウト枠を提供する
import { MainLayout } from "@/components/layout/MainLayout";
// ナビゲーション状態管理ストア（Zustand）を読み込みます
// 現在の表示ビュー（currentView）を取得して画面切り替えに使用する
import { useNavigationStore } from "@/store/navigationStore";
// 電子書籍キャプチャ画面コンポーネントを読み込みます
// ウィンドウキャプチャ・連続キャプチャ機能の UI（UC002）
import { CaptureView } from "@/views/CaptureView";
// 画像トリミング画面コンポーネントを読み込みます
// キャプチャ画像の余白トリミング機能の UI（UC004）
import { TrimView } from "@/views/TrimView";
// PDF読込・展開画面コンポーネントを読み込みます
// PDF ファイルからページ画像を抽出する機能の UI（UC003）
import { PdfImportView } from "@/views/PdfImportView";
// ZIP出力画面コンポーネントを読み込みます
// キャプチャ画像を ZIP アーカイブ化する機能の UI（UC005）
import { ExportView } from "@/views/ExportView";
// OCR済みPDF作成画面コンポーネントを読み込みます
// 画像から OCR 処理済み PDF を生成する機能の UI（UC006）
import { PdfCreationView } from "@/views/PdfCreationView";
// ナビゲーションストアで定義したビュー型を読み込みます
// viewMap の型安全性（Record<AppView, ...>）を保証するために使用する
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
