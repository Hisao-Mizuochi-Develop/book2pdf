# localapp 注意事項

本ファイルは、localapp モジュールで遭遇した技術的な注意事項・落とし穴・回避策を記録するものです。

---

## screenshots crate v0.8.10 — Window struct の非エクスポート

### 事象
`use screenshots::Window;` とするとコンパイルエラー `unresolved import` が発生する。

### 原因
`screenshots` crate v0.8.10 では `Screen` のみがパブリックにエクスポートされており、`Window` struct は存在しない。
ドキュメントや古い情報では `Window::all()` でウィンドウ一覧が取得できるように見えることがあるが、現行バージョンでは非対応。

### 対応策
- ウィンドウ指定キャプチャは `screenshots` crate 単体では実現不可
- 現状は全画面キャプチャ + `crop_insets` によるトリミング方式で代替
- 将来の拡張として以下を検討：
  - `xcap` crate（ウィンドウ指定キャプチャ対応のクロスプラットフォーム crate）
  - macOS 専用: `core-foundation` / `cocoa` crate + AppleScript
  - Tauri plugin の公式スクリーンショット機能（将来リリース時）

### 関連タスク
- 002005: ウィンドウ指定キャプチャ＋コンテンツ領域自動トリミング（実装途中で本問題を発見）
- 002007: ウィンドウ指定キャプチャ実装のコンパイルエラー修正（本問題の対応）

---

## image crate v0.25 — SubImage の as_flat_samples() 非対応

### 事象
`image::imageops::crop_imm()` で取得した `SubImage<&RgbaImage>` に対して `.as_flat_samples()` を呼び出すと、コンパイルエラー「メソッドが存在しない」が発生する。

### 原因
`image` crate v0.25 では `SubImage` に `as_flat_samples()` メソッドが定義されていない。
`as_flat_samples()` は `ImageBuffer`（所有権を持つバッファ型）でのみ利用可能なメソッド。

### 対応策
```rust
// ❌ 誤り: SubImage に as_flat_samples() は存在しない
let samples = cropped.as_flat_samples().samples;

// ✅ 正解: to_image() で ImageBuffer に変換してから as_raw() を使用
let samples = cropped.to_image().as_raw();
```

`SubImage<&RgbaImage>` → `to_image()` → `ImageBuffer<Rgba<u8>, Vec<u8>>` → `as_raw()` → `&Vec<u8>`

### 関連タスク
- 002007: ウィンドウ指定キャプチャ実装のコンパイルエラー修正（本問題の対応）

---

## enigo crate v0.6.1 — API 変更

### 事象
古いコード例やドキュメントに従って `Enigo::new()` や `key_click()` を使用するとコンパイルエラーが発生する。

### 原因
enigo v0.6.1 で API が変更された。

### 対応策
```rust
// ❌ 誤り（古いAPI）
let mut enigo = Enigo::new();
enigo.key_click(Key::RightArrow);

// ✅ 正解（v0.6.1）
use enigo::{Enigo, Key, Keyboard, Settings, Direction};
let mut enigo = Enigo::new(&Settings::default()).unwrap();
enigo.key(Key::RightArrow, Direction::Click).unwrap();
```

### 関連タスク
- 002003: 連続キャプチャ実行・進捗表示（enigo 導入時に対応済み）

---

## tauri::Emitter トレイトの明示的 use

### 事象
`app_handle.emit("event-name", payload)` とすると、コンパイルエラー「メソッド `emit` が `AppHandle` に存在しない」が発生する。

### 原因
`emit()` メソッドは `tauri::Emitter` トレイトで定義されているが、スコープに自動で入っていない場合がある。

### 対応策
```rust
use tauri::Emitter; // 明示的にインポートする必要がある
```

### 関連タスク
- 002003: 連続キャプチャ実行・進捗表示（初回実装時に発生・対応済み）

---

## cargo check の unused import warning

### 事象
`cargo check` で `use std::collections::HashMap;` など、未使用の import に対して warning が出る。

### 原因
実装途中で使用予定だったが、最終的に使われなかった import が残っている。

### 対応策
- 基本的に未使用 import は削除する
- ただし、将来のタスクで確実に必要になる import は、一時的に `#[allow(unused_imports)]` を付けて残すことも検討する
- 本プロジェクトでは将来実装必須のため、未使用 import の放置を最小限に留める（必要に応じて TODO コメント付きで残す）

### 関連タスク
- 002002: アプリプロファイル管理 UI（`capture_profile.rs` にて `HashMap` の unused import warning が検出された）
