# Web OCR/PDF システム 全体計画書

本ドキュメントは、book2pdf プロジェクト全体において、各モジュールが協調して実現する最終的なアプリケーション機能と全体アーキテクチャをまとめたものです。

## 1. プロジェクト概要

- **目的**: 電子書籍のページ画像から OCR 処理を行い、検索可能 PDF を生成する
- **対象コンテンツ**: 電子書籍リーダー上で表示されたページ画像
- **学習目的**: Next.js / FastAPI / Docker / Rust / Tauri の習得
- **方針**: 既存の `old/` フォルダのソースコード・ドキュメントは一切参照せず、スクラッチで開発する

## 2. システム全体構成

本プロジェクトは以下の 2 つのシステムで構成されます。

| システム | 用途 | 技術スタック | 担当モジュール |
|---|---|---|---|
| ローカルスタンドアローンアプリ | 電子書籍画面のキャプチャ＋不要部分のトリミング | Tauri v2 + Rust + React + Vite | `localapp/` |
| Web OCR/PDF システム | ZIP 画像 → OCR → 検索可能 PDF 生成 | Next.js 15 + FastAPI + Docker + ndlocr_cli | `frontend/` / `backend/` / `ocr-worker/` |

各システムの選定理由や非機能要件などの詳細は `docs/SY-DESIGN-DECISIONS.md` を参照してください。

### 2.1 ドキュメント構成

本プロジェクトのドキュメントは、プロジェクト全体の設計と各モジュール固有の設計に分けて管理します。

| 種別 | 配置先 | 主な内容 |
|---|---|---|
| 全体設計・決定事項 | `./docs/` | プロジェクト全体の方針、アーキテクチャ、技術選定 |
| 全体横断のタスク・作業ログ・注意事項 | `./docs/` | 複数モジュールにまたがるタスク管理、作業ログ、注意事項 |
| backend 固有 | `backend/docs/` | backend のタスク管理、環境構築ログ、詳細計画 |
| frontend 固有 | `frontend/docs/` | frontend のタスク管理、環境構築ログ、詳細計画 |
| localapp 固有 | `localapp/docs/` | localapp のタスク管理、環境構築ログ、詳細計画 |
| ocr-worker 固有 | `ocr-worker/docs/` | ocr-worker のタスク管理、環境構築ログ、詳細計画 |

各モジュールの `docs/` には `OT-TASKS.md`（タスク管理表）、`OT-WORK-LOG.md`（作業ログ）、`OT-CAVEATS.md`（注意事項）を配置します。複数モジュールにまたがる内容は `./docs/` 配下に配置します。詳細な運用ルールは `./.clinerules` を参照してください。

## 3. 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                         ユーザー                                │
└─────────────────────────────────────────────────────────────────┘
       │                                       │
       │ 1. 電子書籍画面をキャプチャ           │ 2. ZIP をアップロード
       ▼                                       ▼
┌──────────────┐                    ┌──────────────────────────┐
│   localapp   │── トリミング済み ─▶│        frontend          │
│ (Tauri v2)   │   画像を ZIP 化    │      (Next.js 15)        │
└──────────────┘                    └───────────┬──────────────┘
                                                │ 3. ジョブ作成・進捗確認
                                                ▼
┌───────────────────────────────────────────────────────────────┐
│                        backend (FastAPI)                      │
│  ZIP 展開 / ジョブ管理 / ocr-worker 連携 / PDF 生成 / SSE 通知  │
└───────────────────────┬───────────────────────────────────────┘
                        │ 4. OCR 処理依頼
                        ▼
┌───────────────────────────────────────────────────────────────┐
│                      ocr-worker (ndlocr_cli)                  │
│                    日本語縦書き対応 OCR 実行                   │
└───────────────────────────────────────────────────────────────┘
                        │ 5. OCR 結果
                        ▼
┌───────────────────────────────────────────────────────────────┐
│                        backend (FastAPI)                      │
│                    検索可能 PDF を生成                         │
└───────────────────────┬───────────────────────────────────────┘
                        │ 6. PDF ダウンロード
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ユーザー                                │
└─────────────────────────────────────────────────────────────────┘
```

## 4. 各モジュールの責務

### 4.1 `localapp/`（ローカルスタンドアローンアプリ）

- 電子書籍リーダーの画面をキャプチャする
- キャプチャ画像から外枠などの不要部分をトリミングする
- トリミング済み画像を ZIP アーカイブにまとめて保存する
- Web システムへアップロードするための入出力ファイルを提供する

### 4.2 `frontend/`（Web フロントエンド）

- ブラウザ上で ZIP アーカイブをアップロードする UI を提供する
- OCR 処理ジョブの進捗状況をリアルタイムで表示する
- OCR 完了後に生成された検索可能 PDF をダウンロードする UI を提供する
- 必要に応じて、進捗通知のフォールバック（ポーリング）にも対応する

### 4.3 `backend/`（Web バックエンド）

- アップロードされた ZIP を受け取り、画像を展開する
- OCR ジョブを発行し、ジョブ状態を管理する
- `ocr-worker` を通じて ndlocr_cli による OCR 処理を実行する
- OCR 結果をもとに検索可能 PDF を生成する
- 処理進捗を `frontend` へ通知する
- 生成した PDF をダウンロードできるようにする

### 4.4 `ocr-worker/`（OCR 実行モジュール）

- ndlocr_cli を Python パッケージとして実行する環境を提供する
- `backend` から受け取った画像に対して OCR 処理を行う
- 日本語縦書き・ルビ・複雑な和書レイアウトにも対応した OCR 結果を返す

## 5. 全体処理フロー

1. ユーザーは `localapp` で電子書籍ページをキャプチャし、不要部分をトリミングする
2. `localapp` はトリミング済み画像を ZIP アーカイブにまとめて保存する
3. ユーザーはブラウザで `frontend` を開き、ZIP をアップロードする
4. `frontend` は `backend` にアップロードし、ジョブ ID を取得する
5. `backend` は ZIP を展開し、ジョブ状態を管理する
6. `backend` は `ocr-worker` に OCR 処理を依頼する
7. `ocr-worker` が ndlocr_cli を実行し、OCR 結果を返す
8. `backend` は OCR 結果をもとに検索可能 PDF を生成する
9. 処理進捗は SSE またはポーリングで `frontend` に通知される
10. ユーザーは `frontend` から完成した PDF をダウンロードする

## 6. 最終的に実現する機能

### 6.1 電子書籍ページのキャプチャと前処理

- 画面キャプチャによるページ画像の取得
- 不要な枠線や余白の自動・手動トリミング
- 複数ページの画像を ZIP アーカイブにまとめる

### 6.2 ZIP アーカイブのアップロードとジョブ管理

- ブラウザからの ZIP アップロード
- ジョブ ID の発行と状態管理
- ジョブ一覧・詳細の確認

### 6.3 OCR 処理

- ndlocr_cli を用いた高精度な日本語 OCR
- 縦書き・横書きのテキスト検出
- ルビ・複雑レイアウトへの対応（段階的）

### 6.4 検索可能 PDF の生成

- 元のページ画像を背景とする PDF
- OCR 結果の座標情報に基づく透明テキストレイヤーの配置
- ブラウザからの PDF ダウンロード

### 6.5 進捗通知

- リアルタイムな処理進捗の表示
- プロキシ環境への対応として SSE と HTTP ポーリングの両方を定義
- 詳細は [`docs/SY-PROGRESS-NOTIFICATION-SPEC.md`](SY-PROGRESS-NOTIFICATION-SPEC.md) を参照

## 7. 技術選定の概要

| レイヤー | 技術 | 理由 |
|---|---|---|
| ローカルアプリ | Tauri v2 + Rust + React + Vite | クロスプラットフォーム対応、軽量、画面キャプチャプラグインが利用可能 |
| Web フロントエンド | Next.js 15 App Router | モダン Web 技術の学習、SSR/SSG/Route Handlers の実践 |
| Web バックエンド | FastAPI | Python 製 OCR ライブラリとの親和性が高い、非同期処理が得意 |
| OCR | ndlocr_cli | 日本語縦書き・ルビ・複雑レイアウトに強い国立国会図書館製 OCR |
| PDF 生成 | PyMuPDF | 画像背景＋透明テキストレイヤーの検索可能 PDF 作成に向いている |
| コンテナ | Docker + Docker Compose | 環境の再現性、OS 依存の排除 |

各技術の詳細な選定理由や実行環境については `docs/SY-DESIGN-DECISIONS.md` を参照してください。

## 8. 初期実装範囲

### 8.1 今回の初期実装で採用する方式

| 項目 | 初期実装 |
|---|---|
| ジョブ状態管理 | メモリ内（辞書） |
| 進捗通知 | Server-Sent Events (SSE） |
| テキスト方向 | 横書きを優先し、縦書きは段階的に対応 |
| OCR 実行 | Python パッケージとして `import` して関数を呼び出す |

### 8.2 採用理由

- メモリ内管理：実装がシンプルで、学習初期に集中できる
- SSE：リアルタイム性があり、FastAPI との相性が良い
- 横書き優先：縦書き PDF 生成は高度な処理となるため、まず横書きで動作確認してから段階的に対応する

## 9. 将来の課題・拡張

以下は今回の初期実装では対応せず、次のステップで検討・実装する課題として記録します。

### 9.1 ジョブ状態の永続化

- **目標**: SQLite に永続化
- **理由**: プロセス再起動後もジョブ状態を保持し、複数 worker 間での状態共有を可能にする

### 9.2 進捗通知方式の見直し

- **目標**: localapp / frontend のポーリング方式を整備
- **理由**: プロキシ環境やタイムアウト設定によって SSE が不安定になる場合への対応
- **詳細**: [`docs/SY-PROGRESS-NOTIFICATION-SPEC.md`](SY-PROGRESS-NOTIFICATION-SPEC.md)

### 9.3 縦書き・複雑レイアウトの本格対応

- **目標**: 縦書きテキストやルビを含むページでも正しい検索可能 PDF を生成
- **理由**: 和書電子書籍への対応範囲を広げるため

## 10. フォルダ・ファイル構成

```
book2pdf/
├── .clinerules                  # Cline プロジェクトルール
├── backend/                     # FastAPI バックエンド
│   └── docs/
│       ├── BE-BACKEND-SYSTEM-SPEC.md   # backend 仕様書
│       ├── OT-CAVEATS.md               # backend 注意事項
│       ├── setup-log.md             # backend 環境構築ログ
│       └── OT-TASKS.md                 # backend タスク管理表
├── frontend/                    # Next.js フロントエンド
│   └── docs/
│       ├── FE-FRONTEND-SYSTEM-SPEC.md  # frontend 仕様書
│       ├── setup-log.md             # frontend 環境構築ログ
│       └── OT-TASKS.md                 # frontend タスク管理表
├── localapp/                    # Tauri ローカルスタンドアローンアプリ
│   └── docs/
│       ├── LA-LOCALAPP-SPEC.md         # localapp 仕様書
│       ├── setup-log.md             # localapp 環境構築ログ
│       └── OT-TASKS.md                 # localapp タスク管理表
├── ocr-worker/                  # ndlocr_cli 実行コンテナ
│   └── docs/
│       ├── OW-OCR-WORKER-SYSTEM-SPEC.md  # ocr-worker 仕様書
│       ├── setup-log.md               # ocr-worker 環境構築ログ
│       └── OT-TASKS.md                   # ocr-worker タスク管理表
├── docs/                        # プロジェクト全体の設計・決定事項
│   ├── OT-CAVEATS.md               # 全体横断の注意事項
│   ├── OT-CODING-CONVENTIONS.md    # コーディング規約
│   ├── SY-DESIGN-DECISIONS.md      # 設計決定事項
│   ├── SY-PROGRESS-NOTIFICATION-SPEC.md  # 進捗通知方式仕様書
│   ├── README.md                # ドキュメントインデックス
│   ├── OT-INTEGRATION-TEST-GUIDE.md  # 結合テスト手順書
│   ├── OT-TASKS.md                 # 全体横断のタスク管理表
│   ├── SY-WEB-OCR-SYSTEM-PLAN.md   # 本ドキュメント
│   └── OT-WORK-LOG.md              # 全体横断の作業ログ
└── old/                         # 既存アプリケーションの仕様参考用
    └── （ソースコード・ドキュメントは新規開発では参照しない）
```

## 11. 注意事項

- ndlocr_cli は公式 Docker スクリプトがあるが、今回は自分で Dockerfile を組み立てる
- CPU 実行のため、OCR 処理には時間がかかることを想定
- ndlocr_cli の import パスや関数 signature はリポジトリの実際のコードを確認する必要がある
- 縦書き PDF 生成は高度な処理となるため、まず横書きで動作確認してから段階的に対応する
- 各モジュールの詳細な仕様は以下を参照すること
  - backend: [`backend/docs/BE-BACKEND-SYSTEM-SPEC.md`](../backend/docs/BE-BACKEND-SYSTEM-SPEC.md)
  - frontend: [`frontend/docs/FE-FRONTEND-SYSTEM-SPEC.md`](../frontend/docs/FE-FRONTEND-SYSTEM-SPEC.md)
  - ocr-worker: [`ocr-worker/docs/OW-OCR-WORKER-SYSTEM-SPEC.md`](../ocr-worker/docs/OW-OCR-WORKER-SYSTEM-SPEC.md)
  - localapp: [`localapp/docs/LA-LOCALAPP-SPEC.md`](../localapp/docs/LA-LOCALAPP-SPEC.md)
- 進捗通知方式: [`docs/SY-PROGRESS-NOTIFICATION-SPEC.md`](SY-PROGRESS-NOTIFICATION-SPEC.md)
