# Web OCR/PDF システム フロントエンド 仕様書

本ドキュメントは、電子書籍のページ画像から OCR 処理を行い、検索可能 PDF を生成する Web システムのフロントエンド仕様をまとめたものです。

## 1. 責務

- ブラウザ上で ZIP アーカイブをアップロードする UI を提供する
- OCR 処理ジョブの進捗状況をリアルタイムで表示する
- OCR 完了後に生成された検索可能 PDF をダウンロードする UI を提供する
- 必要に応じて、進捗通知のフォールバック（ポーリング）にも対応する

## 2. 技術選定

| 項目 | 技術 | 理由 |
|---|---|---|
| フレームワーク | Next.js 15 App Router | モダン Web 技術の学習、SSR/SSG/Route Handlers の実践 |
| 言語 | TypeScript | 型安全性と開発体験の向上 |
| スタイリング | Tailwind CSS | ユーティリティファーストで迅速に UI を構築 |
| 通信 | fetch / EventSource | FastAPI との連携、SSE 進捗通知の受信 |

## 3. 初期実装範囲

### 3.1 今回の初期実装で採用する方式

| 項目 | 初期実装 |
|---|---|
| 進捗通知 | **Server-Sent Events (SSE)** |
| ページルーティング | Next.js App Router |

### 3.2 採用理由

- SSE：リアルタイム性があり、FastAPI との相性が良い
- App Router：Next.js 15 の推奨方式であり、モダンな開発パターンを学習できる

## 4. 将来の課題・拡張

### 4.1 進捗通知のポーリング方式対応

- **目標**: SSE が利用できない環境（プロキシ・タイムアウトなど）でも進捗を確認できるようにする
- **理由**: 利用環境によっては SSE が不安定になる場合があるため

## 5. フォルダ・ファイル構成

### 現時点の構成

```
frontend/                         # フロントエンドルート
├── docs/                         # frontend 専用ドキュメント
│   ├── frontend-system-spec.md   # 本仕様書
│   ├── work_log.md               # 作業ログ
│   └── tasks.md                  # タスク管理表
├── src/                          # アプリケーションコード
│   ├── app/                      # App Router ページディレクトリ
│   │   ├── page.tsx              # ZIP アップロード画面（トップページ）
│   │   ├── layout.tsx            # 共通レイアウト
│   │   └── globals.css           # グローバルスタイル（Tailwind CSS v4）
│   └── lib/                      # 共通ライブラリ
│       └── api.ts                # FastAPI 通信用クライアント
├── public/                       # 静的アセット
├── package.json                  # Node.js 依存定義
├── package-lock.json             # npm ロックファイル
├── next.config.mjs               # Next.js 設定（standalone 出力）
├── tsconfig.json                 # TypeScript 設定
├── postcss.config.mjs            # PostCSS 設定
├── eslint.config.mjs             # ESLint 設定
└── Dockerfile                    # フロントエンド Docker イメージ
```

### 将来の構成案

```
frontend/                         # フロントエンドルート
├── docs/                         # frontend 専用ドキュメント
│   ├── frontend-system-spec.md   # 本仕様書
│   ├── setup-log.md              # 環境構築ログ
│   └── tasks.md                  # タスク管理表
├── src/                          # アプリケーションコード
│   ├── app/                      # App Router ページディレクトリ
│   │   ├── page.tsx              # ZIP アップロード画面（トップページ）
│   │   ├── layout.tsx            # 共通レイアウト
│   │   └── jobs/                 # ジョブ関連ページ
│   │       └── [id]/             # 動的ルート（ジョブ ID）
│   │           └── page.tsx      # ジョブ詳細・進捗・ダウンロード画面
│   ├── components/               # React コンポーネント
│   └── lib/                      # 共通ライブラリ
│       └── api.ts                # FastAPI 通信用クライアント
├── package.json                  # Node.js 依存定義
├── next.config.js                # Next.js 設定
├── tsconfig.json                 # TypeScript 設定
├── tailwind.config.ts            # Tailwind CSS 設定
└── Dockerfile                    # フロントエンド Docker イメージ
```
