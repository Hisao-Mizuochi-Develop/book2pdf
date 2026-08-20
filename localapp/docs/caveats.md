
---

## Tauri 同期コマンドのイベント配信制限（005004 ZIP 進捗表示で再発）

### 事象
「ZIP作成」タブで ZIP 作成を実行しても、進捗バー・カウンタ・パーセンテージが表示されず、ボタンがローディング状態のまま処理が完了する。

### 原因
`create_zip_archive` を `#[tauri::command]` 同期コマンドとして実装していたため、`invoke("create_zip_archive")` 呼び出し中にフロントエンドの JavaScript メインスレッドがブロックされていた。これにより Rust 側から `app_handle.emit("zip-progress", ...)` で送信された進捗イベントが、コマンド完了まで UI 側の `listen` コールバックに届かなかった。

### 対応策
1. **Rust 側を async コマンド + `tokio::task::spawn_blocking` に変更**
   - `#[tauri::command]` 関数を `pub async fn` に変更
   - 重い ZIP 作成処理を `tokio::task::spawn_blocking` でバックグラウンドスレッドに移行
   - `AppHandle` は `!Send + !Sync` なため、`spawn_blocking` 内で直接 `emit()` できない
   - `tokio::sync::mpsc` チャネルで進捗情報を async 部に転送し、async 部で `app_handle.emit("zip-progress", payload)` を実行
2. **Cargo.toml で tokio features を確認**
   - `tokio = { version = "1", features = ["rt", "rt-multi-thread", "macros", "sync"] }`
   - `tokio::join!` マクロを使うには `macros` feature が必要
   - `tokio::sync::mpsc` を使うには `sync` feature が必要

### 関連ファイル
- `localapp/src-tauri/src/commands/capture.rs` — `create_zip_archive` / `create_zip_archive_blocking`
- `localapp/src-tauri/Cargo.toml` — tokio features
- `localapp/src/store/exportStore.ts` — `zip-progress` イベント受信
- `localapp/src/views/ExportView.tsx` — 進捗 UI 表示

### 関連タスク
- 005004: ZIP 作成進捗インジケーター追加
- 003002: PDF 読込（同様の同期コマンドブロッキング問題を事前に対応済み）
