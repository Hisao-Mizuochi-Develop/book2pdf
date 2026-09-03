// Next.js のメタデータ型を読み込み
// ページの SEO 情報（タイトル・説明）を型安全に定義するために使用する
import type { Metadata } from "next";
// Next.js の Google Fonts 最適化読み込み機能から Geist フォントを読み込み
// 無衬線（サンセリフ）フォントとして UI テキストに使用する
import { Geist, Geist_Mono } from "next/font/google";
// アプリケーション全体のグローバル CSS（Tailwind ベース）を読み込み
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "book2pdf - Web OCR/PDF システム",
  description: "電子書籍のページ画像から OCR 処理を行い、検索可能 PDF を生成する Web システム",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="ja"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
