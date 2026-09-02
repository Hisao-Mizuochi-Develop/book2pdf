# localapp システム 仕様書

本ドキュメントは、電子書籍のページ画像から OCR 処理を行い、検索可能 PDF を生成するプロジェクトにおける、ローカルスタンドアローンアプリ（localapp）の仕様をまとめたものです。

## 1. 責務

- 電子書籍リーダーの画面をキャプチャする
- PDF ファイルを画像に展開する
- 画像から外枠や余白などの不要部分をトリミングする
- トリミング済み画像を ZIP アーカイブにまとめて保存する
- Web システム（backend/frontend）へアップロードするための入出力ファイルを提供する
- backend API（FastAPI）経由で OCR 処理を実行し、検索可能 PDF を取得する（003006）

## 2. 技術選定

| 項目 | 技術 | 理由 |
|---|---|---|
| フレームワーク | Tauri v2 | クロスプラットフォーム（macOS / Windows / Linux）対応、軽量、Web 技術で UI を構築可能 |
| バックエンド処理 | Rust | Tauri の標準言語。高いパフォーマンスと安全性を持つ |
| フロントエンド | React + Vite + TypeScript | モダンな UI 開発と高速な開発体験 |
| キャプチャ | Tauri screenshot プラグインまたは OS 標準 API | 画面キャプチャ機能の実現 |
| 画像処理 | Rust `image` crate + frontend Canvas | 高品質なリサイズ・クロップ処理 |
| ZIP 圧縮 | Rust `zip` crate | 標準的で使いやすい ZIP 圧縮ライブラリ |
| PDF 展開 | Rust `pdfium-render` crate 等 | ページ画像化の実現 |
| HTTP クライアント | Tauri `tauri-plugin-http` | backend API との通信。`reqwest` を re-export し、`multipart`/`json` feature でファイルアップロードを実現（003006） |
| 状態管理 | Zustand | 軽量なグローバル状態管理 |
| UI コンポーネント | shadcn/ui + Tailwind CSS v4 | モダンで統一感のある UI 構築 |
| アイコン | lucide-react | シンプルで統一感のあるアイコンセット |

## 3. 処理フロー

1. ユーザーが localapp を起動する
2. 左サイドバーから機能を選択する
3. 各機能のフロー
   - **キャプチャ**: プロファイル選択 → ウィンドウ検出 → 連続キャプチャ実行 → 画像フォルダ保存
   - **PDF読込**: PDF 選択 → DPI/形式設定 → 画像展開
   - **トリミング**: 画像フォルダ選択 → プレビュー → 余白調整 → 一括トリミング実行
   - **ZIP出力**: トリミング済みフォルダ選択 → ファイル名設定 → ZIP 保存
   - **PDF作成（ローカル）**: 画像フォルダ/ZIP 選択 → 出力先設定 → `create_searchable_pdf` で OCR → PDF 保存
   - **PDF作成（backend API 経由）**: 画像フォルダ/ZIP 選択 → 保存ダイアログで PDF パス指定 → `run_backend_ocr` で ZIP 作成 → backend ジョブ作成 → アップロード → OCR → PDF ダウンロード（003006）
4. 各工程の結果は次の工程に自動的に引き継がれる

## 4. GUI デザイン方針

### 4.1 基本コンセプト

**クリーン＆ミニマル（Apple HIG 風）**

- 白を基調とした明るい UI
- 広めの余白と整ったグリッド
- 大きなプレビューエリアを確保
- 視覚的ノイズを最小限に抑え、コンテンツ（画像）が主役となる

### 4.2 レイアウト

- **左サイドバー（垂直ナビゲーション）**: アイコン + 短いラベルで 4 機能を切り替え
- **右メインエリア**: 選択した機能の画面を表示
- **共通フッター/ステータスバー**: 進捗状況、メッセージ、簡易ログ

### 4.3 カラーパレット

Apple HIG を参考に、`localapp/src/index.css` の CSS カスタムプロパティとして定義している。
oklch() 色空間を使用し、人間の目に見えやすい色のまま彩度を調整している。

| 用途 | CSS 変数名 | HEX 近似 | oklch 値 | 説明 |
|---|---|---|---|---|
| 背景 | `--background` | `#FFFFFF` | `oklch(1 0 0)` | ページ全体の背景。白を基調とする |
| サイドバー背景 | `--sidebar` | `#F5F5F7` | `oklch(0.97 0 0)` | 左ナビゲーションの背景。白と区別する微妙なグレー |
| プライマリー | `--primary` | `#007AFF` | `oklch(0.588 0.194 257.1)` | 主要ボタン・アクセント。Apple システムブルー |
| セカンダリー | `--secondary` | `#F5F5F7` | `oklch(0.97 0 0)` | 補助ボタンの背景。控えめなグレー |
| テキストプライマリー | `--foreground` | `#1D1D1F` | `oklch(0.225 0 0)` | 主要テキスト。純粋な黒より目に優しいソフトブラック |
| テキストセカンダリー | `--muted-foreground` | `#6E6E73` | `oklch(0.53 0 0)` | 補足テキスト・プレースホルダー。目立たないグレー |
| ボーダー | `--border` | `#D2D2D7` | `oklch(0.853 0 0)` | 区切り線・枠線。目立ちすぎない薄いグレー |
| エラー | `--destructive` | `#FF3B30` | `oklch(0.63 0.22 30)` | エラーメッセージ・削除ボタン。赤系 |
| 警告 | `--ring`（フォーカス） | `#BDBDBD` | `oklch(0.708 0 0)` | フォーカス時の輪郭線。キーボード操作の目印 |

### 4.3a ダークモードカラーパレット

OS の外観モードがダークの場合、`main.tsx` の `initTheme()` が `html` 要素に `.dark` クラスを付与し、以下の変数が自動的に適用される。

| 用途 | CSS 変数名 | HEX 近似 | oklch 値 | 説明 |
|---|---|---|---|---|
| 背景 | `--background` | `#252525` | `oklch(0.145 0 0)` | ダークモード時のページ背景。純黒よりやや明るい深い黒 |
| サイドバー背景 | `--sidebar` | `#353535` | `oklch(0.205 0 0)` | 左ナビゲーション背景。背景と区別する暗灰色 |
| プライマリー | `--primary` | `#EBEBF5` | `oklch(0.922 0 0)` | ダーク時の主要ボタン色。ライトモードと反転し白系 |
| セカンダリー | `--secondary` | `#454545` | `oklch(0.269 0 0)` | 補助ボタン背景。暗めのグレー |
| テキストプライマリー | `--foreground` | `#F5F5F5` | `oklch(0.985 0 0)` | ダーク時の主要テキスト。白に近い明るい色 |
| テキストセカンダリー | `--muted-foreground` | `#BDBDBD` | `oklch(0.708 0 0)` | 補足テキスト。ライト時と比べ明るく設定 |
| ボーダー | `--border` | `rgba(255,255,255,0.1)` | `oklch(1 0 0 / 10%)` | 区切り線。白の 10% 不透明度で微妙に見える |
| エラー | `--destructive` | `#FF453A` | `oklch(0.704 0.191 22.216)` | ダーク時のエラー色。ライト時よりやや明るく |
| フォーカス | `--ring` | `#8E8E93` | `oklch(0.556 0 0)` | ダーク時のフォーカス輪郭線 |

【テーマ切り替えの仕組み】
- Tailwind CSS v4 の `@custom-variant dark (&:is(.dark *))` を使用
- `main.tsx` で `window.matchMedia("(prefers-color-scheme: dark)")` を監視
- OS 設定変更時に `.dark` クラスを `html` 要素に付与/除去
- React レンダリングより先に実行し、画面ちらつきを防止

### 4.4 タイポグラフィ

- フォント: Geist Variable（優先）、システムフォントフォールバック
  - `font-family: 'Geist Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- フォントウェート:
  - 見出し: 600（semibold）
  - ボディ: 400（regular）・500（medium）
- フォントサイズ（rem ベース）:
  - 見出し: 1rem〜1.25rem（16px〜20px）
  - ボディ: 0.8125rem〜0.9375rem（13px〜15px）
  - キャプション: 0.6875rem〜0.75rem（11px〜12px）
- 角丸サイズ: `--radius: 0.5rem`（8px）。Apple HIG 風に控えめに設定

## 5. 初期実装範囲

### 5.1 今回の初期実装で採用する方式

| 項目 | 初期実装 |
|---|---|
| 画面キャプチャ | Tauri screenshot プラグインまたは OS 標準 API を利用 |
| トリミング | 手動での矩形選択を基本とし、自動検出を補助 |
| PDF 展開 | `pdfium-render` 等を用いたページ画像化 |
| 出力形式 | ZIP アーカイブ |
| ナビゲーション | 左サイドバー型垂直ナビゲーション |
| テーマ | ライトモード基本 + OS ダークモード自動連動 |

### 5.2 採用理由

- 手動トリミング: 実装がシンプルで、学習初期に集中できる
- ZIP 出力: Web システムとの連携が容易
- サイドバーナビゲーション: モダンで視認性が高く、機能切り替えが直感的

## 6. 将来の課題・拡張

### 6.1 自動トリミング

- **目標**: ページ外枠や余白を自動で検出・削除する精度向上
- **理由**: ユーザー操作を簡略化し、処理の再現性を高めるため

### 6.2 Web システムとの連携

- **目標**: localapp から直接 backend へ ZIP をアップロードする
- **理由**: ユーザーがブラウザを介さずに一連の処理を完結させられるようにするため

### 6.3 ダークモード対応

- **目標**: ライト/ダークの手動切り替えと OS 設定連動
- **理由**: 利用環境や好みに応じた表示切り替え

## 7. フォルダ・ファイル構成

### 現時点の構成

```
localapp/                         # ローカルアプリルート
└── docs/                         # localapp 専用ドキュメント
    ├── localapp-spec.md          # 本仕様書
    ├── setup-log.md              # 環境構築ログ
    ├── tasks.md                  # タスク管理表
    ├── caveats.md                # 注意事項
    └── work_log.md               # 作業ログ
```

### 将来の構成案

```
localapp/                         # ローカルアプリルート
├── docs/                         # localapp 専用ドキュメント
│   ├── localapp-spec.md          # 本仕様書
│   ├── setup-log.md              # 環境構築ログ
│   ├── tasks.md                  # タスク管理表
│   ├── caveats.md                # 注意事項
│   └── work_log.md               # 作業ログ
├── src/                          # フロントエンドコード（React + Vite）
│   ├── App.tsx                   # メインアプリケーションコンポーネント
│   ├── main.tsx                  # React エントリポイント
│   ├── index.css                 # グローバルスタイル
│   ├── components/               # 共通的・再利用可能な React コンポーネント
│   │   ├── ui/                   # shadcn/ui コンポーネント
│   │   ├── layout/               # レイアウトコンポーネント（Sidebar 等）
│   │   └── shared/               # 共通部品（Button, Card 等のラッパー）
│   ├── pages/                    # 各機能画面
│   │   ├── CapturePage.tsx
│   │   ├── PdfLoadPage.tsx
│   │   ├── TrimPage.tsx
│   │   └── ZipExportPage.tsx
│   ├── stores/                   # Zustand 状態管理
│   │   └── app-store.ts
│   ├── hooks/                    # カスタム React Hooks
│   ├── lib/                      # ユーティリティ関数
│   └── types/                    # TypeScript 型定義
├── src-tauri/                    # Tauri / Rust コード
│   ├── Cargo.toml                # Rust 依存定義
│   ├── tauri.conf.json           # Tauri 設定
│   ├── capabilities/             # Tauri v2 権限設定
│   ├── icons/                    # アプリアイコン
│   └── src/                      # Rust ソースコード
│       ├── main.rs               # Rust エントリポイント
│       ├── lib.rs                # コマンド登録等
│       ├── commands/             # Tauri コマンド
│       │   ├── capture.rs
│       │   ├── pdf.rs
│       │   ├── trim.rs
│       │   ├── zip.rs
│       │   └── config.rs
│       ├── core/                 # コアロジック
│       │   ├── capture.rs
│       │   ├── pdf.rs
│       │   ├── trim.rs
│       │   └── zip.rs
│       └── models/               # データモデル
├── package.json                  # Node.js 依存定義
├── vite.config.ts                # Vite 設定
├── tsconfig.json                 # TypeScript 設定
├── components.json               # shadcn/ui 設定
├── tailwind.config.ts            # Tailwind CSS 設定
└── index.html                    # HTML エントリポイント
```

## 8. 注意事項

- 各モジュール共通の注意事項は [../../docs/caveats.md](../../docs/caveats.md) を参照
- ローカルアプリ固有の注意事項は [./caveats.md](./caveats.md) を参照
