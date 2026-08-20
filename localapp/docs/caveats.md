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

---

## Tauri `invoke` の引数名完全一致（重要）

### 事象
JS 側で `invoke("start_continuous_capture", { startFromBeginning: true })` と camelCase で渡しても、Rust 側では `start_from_beginning` (snake_case) を受け取れない。

### 原因
Tauri v2 の `invoke` API は、JS 側オブジェクトの**キー名**と Rust 側コマンドの**引数名**が**完全一致**する必要がある。自動的な snake_case ↔ camelCase 変換は行われない。

### 対応策
```typescript
// ❌ 誤り: camelCase で渡すと Rust 側では undefined 扱いになる
await invoke("start_continuous_capture", { profile, startFromBeginning: true });

// ✅ 正解: Rust 側の引数名と完全に一致させる
await invoke("start_continuous_capture", {
  profile,
  start_from_beginning: startFromBeginning,
});
```

### 関連タスク
- 002008-2: プロファイルUI改善（`startFromBeginning` → `start_from_beginning` の修正）

---

## base-ui/react-select の `<SelectValue>` と非同期データ

### 事象
`ProfileSelector.tsx` で `<SelectValue />`（auto-render 方式）を使用した場合、`builtinProfiles` の非同期読み込み完了前は初期表示が placeholder のままになる。

### 原因
`<SelectValue />` は `builtinProfiles` 内の対応する `<SelectItem>` の children を自動で探して表示する。しかし `fetchProfiles()` が非同期のため、初期レンダリング時は `builtinProfiles` が空配列で `<SelectItem>` が存在せず、表示テキストが解決できない。

### 対応策
```tsx
const selectedProfile = builtinProfiles.find((p) => p.key === selectedProfileKey);
const displayLabel = selectedProfile?.name ?? selectedProfileKey ?? "プロファイルを選択";

<SelectValue placeholder="プロファイルを選択">{displayLabel}</SelectValue>
```
手動で `displayLabel` を計算して children として渡す。読み込み前は `selectedProfileKey`（"kindle"）が表示され、読み込み後は正しい日本語名に切り替わる。

### 関連タスク
- 002008-2: プロファイルUI改善（ProfileSelector 初期表示対応）

---

## pdfium-render crate — PDFium 動的ライブラリのバンドル

### 事象
`pdfium-render` crate を使用して PDF をレンダリングする際、実行時に `libpdfium.dylib` が見つからないエラーが発生する。

### 原因
`pdfium-render` は PDFium を動的ライブラリとして読み込む必要がある。開発時は `Pdfium::bind_to_library()` に絶対パスを渡せば動作するが、Tauri アプリとしてビルド・配布する場合は `.dylib` をバンドルに含める必要がある。

### 対応策
1. `localapp/src-tauri/pdfium/libpdfium.dylib` を配置する（macOS arm64 用は `bblanchon/pdfium-binaries` 等から取得）
2. `localapp/src-tauri/tauri.conf.json` の `bundle.resources` に以下を追加：
   ```json
   "bundle": {
     "resources": {
       "pdfium/libpdfium.dylib": "pdfium/libpdfium.dylib"
     }
   }
   ```
3. Rust コマンド内で `Pdfium::bind_to_library()` にバンドルされたパスを解決して渡す
   - 開発時: リポジトリ内の `pdfium/libpdfium.dylib`
   - 本番時: Tauri の `app.path().resource_dir()` 等で解決
4. Windows/Linux への移植時はそれぞれ `pdfium.dll` / `libpdfium.so` を同様に配置する

### 関連タスク
- 003001〜003002: PDF 読込（PDF 選択・設定 UI + PDF → 画像展開）

---

## Node.js v26 + Tailwind CSS v4 / PostCSS — ビルドエラー

### 事象
`npm run build` 実行時に以下のようなエラーが発生する。
- `LazyResult.registerPostcss is not a function`
- `yield* (intermediate value) is not iterable`
- PostCSS 周りの TypeError

### 原因
Node.js v26.0.0 と Tailwind CSS v4 / `@tailwindcss/vite` / PostCSS 系の互換性問題、または `node_modules` の破損・依存解決の不整合が考えられる。

### 対応策
```bash
rm -rf localapp/node_modules localapp/package-lock.json
cd localapp && npm install
```
上記で `node_modules` と `package-lock.json` を削除して再インストールすることで解消した。同様の症状が再発した場合、まず本対策を試す。

### 関連タスク
- 003001〜003002: PDF 読込（PDF 選択・設定 UI + PDF → 画像展開）
- 005001〜005003: ZIP アーカイブ化・出力設定 UI・タブ間連携（node_modules 破損発生）

---

## Tauri 同期コマンドのイベント配信制限

### 事象
`#[tauri::command]` で定義された同期コマンドを呼び出している間、Rust 側から `app_handle.emit()` で送信した進捗イベントがフロントエンドでリアルタイムに受信できない。コマンド完了後にまとめて受信される、または全く受信されないように見える。

### 原因
Tauri の同期コマンドを `invoke` で呼び出すと、コマンドが完了するまで JavaScript 側のメインスレッドがブロッキングされる。WebView のイベントループも同じスレッドで動作しているため、Rust 側から `pdf-progress` 等のイベントが emit されても、コマンド完了まで UI 側の `listen` コールバックが実行されない。

加えて、React 18 の自動バッチングにより、イベント受信後の `setState` 呼び出しがコマンド完了までまとめられる可能性もある。これにより「ボタンを押しても何も表示されない」という症状が強調される。

### 対応策
1. **Rust 側を async コマンド + バックグラウンド処理に変更**
   ```rust
   #[tauri::command]
   async fn extract_pdf_to_images(
       app_handle: AppHandle,
       pdf_path: String,
       output_folder: String,
       dpi: f32,
   ) -> Result<String, String> {
       let app_handle_for_emit = app_handle.clone();
       tokio::task::spawn_blocking(move || {
           // 重い処理
           app_handle_for_emit.emit("pdf-progress", payload).ok();
       })
       .await
       .map_err(|e| e.to_string())?
   }
   ```
2. **フロントエンド側で `invoke` をマイクロタスクに入れる**
   ```typescript
   Promise.resolve().then(async () => {
     await invoke("extract_pdf_to_images", { ... });
   });
   ```
   これによりメインスレッドを一度解放し、イベントリスナーが動作する余地を作る。

3. **コマンド呼び出し前にローディング state を先に設定**
   ボタン押下時に即座に `setProgressMessage("PDFを読み込んでいます...")` 等を呼び出してから `invoke` を実行する。ただし、同期コマンドの場合はこの state 更新もコマンド完了までバッチングされることがあるため、根本解決には async 化が必要。

### 関連タスク
- 003002-1: PDF 読込 進捗インジケーター表示不具合調査・修正

---

## pdfium-render crate — PdfiumLibraryBindingsAlreadyInitialized 二重初期化エラー

### 事象
`extract_pdf_to_images` を async コマンド + `tokio::task::spawn_blocking` に変更後、コマンド実行時に `PdfiumLibraryBindingsAlreadyInitialized` エラーが発生する。PNG ファイルが生成されず、コマンドが失敗して返却される。

### 原因
`pdfium-render` crate はプロセス内で `Pdfium::bind_to_library()` を1回のみ呼び出し可能。
async 部で `Pdfium::bind_to_library()` → `Pdfium::new()` を行った後、`tokio::task::spawn_blocking` 内で再度 `bind_to_library()` を呼んでいたため、2重初期化エラーが発生した。

### 対応策
```rust
// ❌ 誤り: async 部と spawn_blocking 内で bind_to_library() を2回呼ぶ
#[tauri::command]
pub async fn extract_pdf_to_images(...) -> Result<String, String> {
    let bindings = Pdfium::bind_to_library(&library_path)?; // 1回目
    let pdfium = Pdfium::new(bindings);
    let page_count = { /* ... */ };

    tokio::task::spawn_blocking(move || {
        let bindings = Pdfium::bind_to_library(&library_path)?; // 2回目 → エラー
        // ...
    }).await
}

// ✅ 正解: ライブラリパス等の情報のみを渡し、spawn_blocking 内でまとめて初期化する
#[tauri::command]
pub async fn extract_pdf_to_images(...) -> Result<String, String> {
    let library_path = resolve_pdfium_library_path()?;
    // async 部では PDFium 初期化を行わない

    tokio::task::spawn_blocking(move || {
        let bindings = Pdfium::bind_to_library(&library_path)?; // 1回のみ
        let pdfium = Pdfium::new(bindings);
        let document = pdfium.load_pdf_from_file(&pdf_path, None)?;
        let page_count = document.pages().len();
        // 進捗 emit(0) → レンダリング
    }).await
}
```

`Pdfium::bind_to_library()` は `OnceCell` のようなグローバルな `BINDINGS` を保持しているため、1度成功すると2回目の呼び出しはエラーとなる。async コマンド内で PDFium を初期化する必要がある場合は、初期化からレンダリングまでを `spawn_blocking` 内で一貫して実行する。

### 関連タスク
- 003002-2: PDF 読込 Pdfium 二重初期化エラー修正

---

## image crate による PNG 保存 — Operation timed out (os error 60)

### 事象
`extract_pdf_to_images` で PDF ページを PNG 画像として保存する際、特定のページ（例: ページ 6）で以下のエラーが発生することがある。

```
ページ 6 の保存に失敗しました: Operation timed out (os error 60)
```

PNG ファイルの書き込み途中で失敗し、画像が出力されない。

### 原因
`image::DynamicImage::save()` 実行時に、macOS のファイルシステム／I/O サブシステムで一時的なタイムアウトが発生したと考えられる。
エラーコード `60` は `ETIMEDOUT` に対応し、macOS での一過性の OS レベル I/O エラーである。
特定のページにのみ発生するため、ファイルサイズ・ディスクキャッシュの状態・他プロセスの I/O 負荷などが影響している可能性がある。

### 対応策
画像保存処理にリトライ機構を設ける（最大 3 回、失敗時は 1 秒待機）。

```rust
let mut save_error: Option<image::ImageError> = None;
for attempt in 0..3 {
    match rgba_image.save(&output_path) {
        Ok(()) => {
            save_error = None;
            break;
        }
        Err(e) => {
            save_error = Some(e);
            if attempt < 2 {
                std::thread::sleep(std::time::Duration::from_secs(1));
            }
        }
    }
}
if let Some(e) = save_error {
    return Err(format!(
        "ページ {} の保存に失敗しました（3回試行）: {}（ファイルパス: {}）",
        page_number, e, output_path.display()
    ));
}
```

- 1 回目の保存で成功する場合がほとんどである
- 3 回連続で失敗した場合のみエラーを返す
- リトライ間隔は 1 秒とし、連続する I/O 負荷を避ける

### 確認事項
本対応後、ユーザー動作テストで `Operation timed out (os error 60)` が再発しないことを確認する。
再発する場合は、以下を追加検討する。

- 出力先ディスクの空き容量と権限の確認
- ウイルス対策ソフト・クラウドストレージ同期ツールによるファイルロックの有無
- リトライ間隔・回数の調整（指数バックオフ等）
- 保存先を一時ディレクトリに変更してから最終出力先へ `rename` する方式

### 関連タスク
- 003002-2: PDF 読込 Pdfium 二重初期化エラー修正（本現象は動作テスト中に発見された副次的な問題）
