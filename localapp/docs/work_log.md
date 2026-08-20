### 【実施実績】

- 2026-08-20: 初回実装
  - `localapp/src/store/exportStore.ts` に `progressCurrent` / `progressTotal` を追加
  - `localapp/src/views/ExportView.tsx` にスピナー・プログレスバー・カウンタ・パーセント表示を追加
  - `cargo check` / `npm run build` に成功
- 2026-08-20: ユーザー動作テストで不合格
  - 症状: 「進捗表示はなく、カーソルがクルクルするだけ」
  - 原因: `create_zip_archive` が同期コマンドで、ZIP 作成中にフロントエンドのメインスレッドがブロックされていた
  - 修正方針: PDF 読込機能（003002）と同様に `async` コマンド + `tokio::task::spawn_blocking` でバックグラウンド実行
- 2026-08-20: Rust 側非同期化対応
  - `localapp/src-tauri/src/commands/capture.rs`
    - `create_zip_archive` を `pub async fn` に変更
    - 実処理を `create_zip_archive_blocking` として分離し、`tokio::task::spawn_blocking` で実行
    - `tokio::sync::mpsc` チャネルで進捗情報を async 部に転送し、`AppHandle::emit("zip-progress", ...)` でフロントエンドに送信
    - 進捗イベントの送信頻度を「毎ファイル」に変更
  - `localapp/src-tauri/Cargo.toml` に tokio features `macros` / `sync` を追加
- 2026-08-20: 再テストで合格
  - ZIP 作成時に進捗バー・カウンタ・パーセンテージが正しく表示されることを確認
  - `cargo check`: 成功（non_snake_case 警告のみ）
  - `npm run build`: 成功
- 実施コマンド:
  1. `cd localapp/src-tauri && cargo check`
  2. `cd localapp && npm run build`
  3. `cd localapp && npm run tauri dev`
- 変更ファイル:
  - `localapp/src/store/exportStore.ts`
  - `localapp/src/views/ExportView.tsx`
  - `localapp/src-tauri/src/commands/capture.rs`
  - `localapp/src-tauri/Cargo.toml`
