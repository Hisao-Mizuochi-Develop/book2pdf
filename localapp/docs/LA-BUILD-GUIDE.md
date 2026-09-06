# localapp ビルド・起動ガイド

localapp（Tauri v2 + React + Vite）の開発・ビルド手順をまとめたガイドです。

---

## 1. 前提条件

| 項目 | バージョン | 確認コマンド |
|---|---|---|
| Node.js | v20 以上 | `node --version` |
| npm | v10 以上 | `npm --version` |
| Rust | 最新 stable | `rustc --version` |
| macOS | 13 (Ventura) 以上 | — |

プロジェクトルートからのパス: `/Users/hisao/Documents/work4/sakura/book2pdf/localapp/`

---

## 2. クイックスタート

開発モードでアプリを起動する（Hot Reload あり）:

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/localapp
npm run tauri dev
```

初回は Rust の依存クレートコンパイルに **5〜10分** かかります。2回目以降は **30秒〜1分** 程度で起動します。

起動後、macOS のアプリウィンドウが開きます。フロントエンド（React/Vite）のコード変更は自動反映されます。

---

## 3. ビルドコマンド一覧

### 3.1 フロントエンドのみビルド確認

TypeScript の型チェックと Vite ビルドを実行:

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/localapp
npm run build
```

内部的には `tsc && vite build` が実行されます。

### 3.2 Rust 側コンパイル確認

Rust コードのコンパイルエラーをチェック（バイナリ生成は行わない）:

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/localapp/src-tauri
cargo check
```

### 3.3 開発モード起動

フロントエンド + Rust バックエンドを同時に開発モードで起動:

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/localapp
npm run tauri dev
```

- フロントエンド: Vite dev server（ホットリロード有効）
- Rust 側: 開発プロファイルでコンパイル（デバッグ情報付き）

### 3.4 本番ビルド（.app 生成）

配布用の `.app` バンドルを生成:

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/localapp
npm run tauri build
```

生成物のパス:
```
localapp/src-tauri/target/release/bundle/macos/book2pdf.app
```

---

## 4. 日常的な開発フロー

### フロントエンドのみ修正した場合

```bash
cd localapp && npm run build
```

→ `npm run tauri dev` で起動中であれば、自動的にホットリロードが効きます。

### Rust 側を修正した場合

```bash
cd localapp/src-tauri && cargo check
```

→ `npm run tauri dev` で起動中であれば、Rust 側の変更も自動リビルドされます（アプリの再起動が必要な場合あり）。

---

## 5. トラブルシューティング

### 5.1 Babel エラー: `yield* (intermediate value) is not iterable`

**原因**: Vite / Babel のキャッシュ破損

**対処**:
```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/localapp
rm -rf node_modules package-lock.json
npm install
```

### 5.2 Rust ビルドエラー: 依存関係の不整合

**原因**: Rust のビルドキャッシュ破損

**対処**:
```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/localapp/src-tauri
cargo clean
cargo check
```

### 5.3 プロセスが残って起動しない

既存の localapp プロセスを終了:
```bash
pkill -f "book2pdf"
```

### 5.4 `npm run tauri dev` で Rust エラー

Rust 側のエラーメッセージを確認し、`cargo check` で個別に修正してください。

---

## 6. テスト実行手順

### 6.1 Rust 結合テスト（モック backend 使用）

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf/localapp/src-tauri
cargo test backend_api_impl -- --nocapture
```

### 6.2 backend API 連携テスト（フルフロー）

1. backend / ocr-worker コンテナを起動:
   ```bash
   cd /Users/hisao/Documents/work4/sakura/book2pdf
   docker compose up -d
   ```

2. localapp を開発モードで起動:
   ```bash
   cd /Users/hisao/Documents/work4/sakura/book2pdf/localapp
   npm run tauri dev
   ```

3. UI から「PDF作成」タブを開き、backend OCR を実行して PDF ダウンロードまで確認

---

## 7. package.json scripts 定義

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "tauri": "tauri"
  }
}
```

### 補足: Tauri CLI コマンド

- `npm run tauri dev` — 開発モード起動
- `npm run tauri build` — 本番ビルド
- `npm run tauri -- --help` — その他の Tauri CLI オプション

---

## 8. よく使うコマンドまとめ

| 目的 | コマンド |
|---|---|
| 開発モード起動 | `cd localapp && npm run tauri dev` |
| TypeScript 確認だけ | `cd localapp && npx tsc --noEmit` |
| フロントエンドビルド | `cd localapp && npm run build` |
| Rust コンパイル確認 | `cd localapp/src-tauri && cargo check` |
| Rust テスト | `cd localapp/src-tauri && cargo test` |
| 本番ビルド | `cd localapp && npm run tauri build` |
| 依存再インストール | `cd localapp && rm -rf node_modules && npm install` |
| Rust キャッシュクリア | `cd localapp/src-tauri && cargo clean` |

---

*最終更新: 2026-09-03*
