# localapp 注意事項

本ファイルは、localapp モジュールで遭遇した技術的な注意事項・落とし穴・回避策を記録するものです。

---

## xcap crate — "Failed to copy data" エラーとリトライ機構

### 事象
`xcap` crate を使用した連続キャプチャ中、`.capture_image()` を呼び出すと以下のエラーが断続的に発生する。

```
Failed to copy data
```

エラー発生時、キャプチャ画像が取得できず、連続キャプチャが中断する。

### 原因
`xcap` crate は OS のネイティブ API を使用してウィンドウ画像を取得しているが、macOS 等で最前面化処理とキャプチャ処理のタイミングが合わない場合、フレームバッファのコピーに失敗することがある。これは xcap 内部の一過性のエラーであり、同一ウィンドウに対して数100ms 後に再試行すると成功するケースがある。

### 対応策
`capture_window_image()` 内で `.capture_image()` を最大3回、500ms 間隔でリトライする機構を追加する。

```rust
for attempt in 0..3 {
    match window.capture_image() {
        Ok(image) => return Ok(image),
        Err(e) => {
            if attempt < 2 {
                std::thread::sleep(std::time::Duration::from_millis(500));
            } else {
                return Err(format!("ウィンドウキャプチャに失敗しました（3回試行）: {}", e));
            }
        }
    }
}
```

- 1回目で成功する場合がほとんど
- 2回目以降のリトライは最前面化直後の一過性エラーを吸収する
- 3回連続で失敗した場合のみエラーを返す

### 関連タスク
- 002008-1: 連続キャプチャバグ修正（MSE計算 & 最前面化）

---

## xcap crate — macOS/Windows プロセス名互換性

### 事象
ビルトインプロファイルで `process_name: "Kindle.exe"` を設定している状態で、macOS 上でウィンドウ指定キャプチャを実行しても、該当ウィンドウが見つからない。

### 原因
`xcap::Window` が返す `app_name` は OS によって異なる。
- Windows: 実行ファイル名（例: `Kindle.exe`）
- macOS: アプリケーションバンドル名（例: `Kindle`）

そのため、プロファイルの `process_name` に `"Kindle.exe"` をそのまま指定すると、macOS では `app_name.contains("Kindle.exe")` が false になりマッチしない。

### 対応策
1. プロファイルの `process_name` から `.exe` 拡張子を除去する
   ```rust
   let target_process = profile
       .process_name
       .trim_end_matches(".exe")
       .to_lowercase();
   ```
2. 完全一致ではなく部分一致（`contains()`）を使用する
   ```rust
   if window.app_name().to_lowercase().contains(&target_process) { ... }
   ```
3. ビルトインプロファイルの `process_name` を `"Kindle.exe"` ではなく `"Kindle"` に変更する

### 関連タスク
- 002008: ウィンドウ指定キャプチャ実装（xcap crate 版）
- 002008-1: 連続キャプチャバグ修正（MSE計算 & 最前面化）

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

## replace_in_file ツール — SEPARATOR 文字列の混入事故

### 事象
`replace_in_file` で複数の SEARCH/REPLACE ブロックを記述した際、ファイル内に `>>>>+++ REPLACE` などの SEPARATOR 文字列が混入し、ソースコードが壊れて `cargo check` / `npm run build` が失敗する。

### 原因
`replace_in_file` の複数ブロック形式では、各ブロックを専用の SEPARATOR で区切る必要がある。SEPARATOR の組み合わせを間違えると、意図しない文字列がファイルに残ってしまう。混入例 `>>>>+++ REPLACE` は、終了マーカーの先頭文字を誤って重ねて記述した結果である。

### 対応策
1. **SEPARATOR は正確に記述する**
2. **複数ブロックを使う場合は、各ブロックを上から順に正しい形式で記述する**
3. **置換後は必ず該当ファイルを開いて、SEPARATOR 文字列が残っていないか目視確認する**
4. **ビルド確認を必ず実施する**（`cargo check` / `npm run build`）

### 教訓
AI 側の入力ミスであっても、最終的にファイルに書き込まれる内容は人間が確認する必要がある。特に diff 形式の入力では、SEPARATOR の正否を必ずチェックすること。

### 関連タスク
- 002008-2: プロファイルUI改善（デフォルト選択・表示・バリデーション）

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

---

## write_to_file ツール — 既存ドキュメントの誤上書き事故

### 事象
作業ログ（`localapp/docs/work_log.md`）や注意事項（`localapp/docs/caveats.md`）といった既存ドキュメントを `write_to_file` で更新したところ、ファイルの既存内容がすべて失われ、新規作成時のような状態になってしまった。

### 原因
`write_to_file` はファイルが存在する場合、内容を完全に上書きする。追記や部分更新を意図していたが、既存内容を保持せずに新しい内容だけを書き込んでしまったため、過去の作業履歴・注意事項が消失した。

### 対応策
1. **既存ドキュメントの更新は `replace_in_file` を使用する**
   - `docs/`、`backend/docs/`、`frontend/docs/`、`localapp/docs/`、`ocr-worker/docs/` 配下の既存ファイルはすべて `replace_in_file` で更新する
2. **`write_to_file` は新規ファイル作成時のみ使用する**
3. **末尾に追記する場合も `replace_in_file` を使用する**
   - 既存の末尾マーカー（`---`、`##` 見出し、セクション終端）を SEARCH に指定して追記する
4. **誤上書きした場合は Git から復旧する**
   - `git checkout -- <file>` または `git show <commit>:<file>` で復旧
   - 復旧後、正しい方法（`replace_in_file`）で再適用する

### 教訓
`write_to_file` は強力なツールであるが、既存ファイルに対しては非常に危険である。ドキュメント類の更新では、必ず `replace_in_file` を使う習慣を徹底する。

### 関連タスク
- 005004: ZIP 作成進捗インジケーター追加

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

---

## 連続キャプチャ — MSE 同一ページ判定の猶予（002008-3）

### 事象
Kindle プロファイル等で `page_wait` が短い（0.15秒）場合、ページ送り直後に次のキャプチャが実行され、ページ遷移が完了する前に前回と同じ画像が取得されることがある。この状態で MSE（平均二乗誤差）が閾値未満となり、「最終ページ到達」と誤判定して連続キャプチャが途中で完了してしまう。

### 原因
`run_continuous_capture_loop()` 内で、前回画像との MSE が `MSE_THRESHOLD`（1000.0）未満の場合、即座に `completed` を発行していた。ページ遷移アニメーション中や `page_wait` が短くて遷移が追いついていない場合、1回だけ MSE が低くなることがあり、これを誤って最終ページと判断していた。

### 対応策
MSE 同一ページ判定を「連続2回閾値未満」方式に変更する。

```rust
// run_continuous_capture_loop() 内
let mut same_page_count: u32 = 0;
const MSE_THRESHOLD: f64 = 1000.0;

// ...

if mse < MSE_THRESHOLD {
    same_page_count += 1;
    if same_page_count >= 2 {
        // 2回連続で変化が少ない＝最終ページ到達と判断
        emit_progress(..., "completed", ...);
        break;
    }
    // 1回目はページ遷移が追いついていない可能性があるため、
    // もう一度ページ送りを試みる（キャプチャ画像は保存しない）
    turn_page(&mut enigo, &profile.page_turn_key)?;
    thread::sleep(Duration::from_secs_f64(profile.page_wait));
    continue;
} else {
    same_page_count = 0;
}
```

- 1回目の同一ページ判定：キャプチャ画像を破棄し、再度ページ送りして待機する
- 2回連続で同一ページ判定：実際の最終ページ到達として `completed` を発行する
- MSE が閾値以上の場合は `same_page_count` をリセットする

### デバッグ
毎回の MSE 値と判定結果を `eprintln!` で出力し、誤判定の確認ができるようにする。

```rust
eprintln!(
    "[002008-3 DEBUG] page={} MSE={:.2} threshold={} same_page_count={}",
    page_num, mse, MSE_THRESHOLD, same_page_count
);
```

### 注意点
- 本対応により、実際の最終ページは確実に検出できるように維持しつつ、一時的なページ遷移遅延による誤完了を防ぐ
- `page_wait` が極端に短いプロファイルでは、同一ページ判定→再ページ送りが頻発し、キャプチャ速度が低下する可能性がある
- 必要に応じて `page_wait` の調整も検討する（Kindle プロファイルのデフォルト 0.15秒は現状維持）

### 関連タスク
- 002008-3: 連続キャプチャ途中完了バグ修正（MSE同一ページ判定の猶予）
