# タイムアウト値調査報告書（OT003001）

## 1. 調査目的

localapp で backend OCR 連携時に発生した「OCR 処理がタイムアウトしました」エラーの根本原因を特定し、関連するすべてのタイムアウト値の管理方法（設定ファイル vs ハードコード vs 環境変数）を明確にすること。

## 2. 調査対象のタイムアウト値一覧

### 2.1 設定ファイル（`settings.json`）で管理される値

**設定ファイルの場所：**
- macOS: `~/Library/Application Support/book2pdf/settings.json`
- Linux: `~/.config/book2pdf/settings.json`

| 設定キー | デフォルト値 | 用途 | 変更時の再ビルド |
|---|---|---|---|
| `page_timeout_sec` | `600`（※今回 300→600 に変更） | 1 ページあたりの OCR タイムアウト。ポーリング全体の締切は `ページ数 × この値` で計算 | **不要**（設定ファイル編集で即時反映） |
| `polling_interval_sec` | `5` | backend へのジョブ状態ポーリング間隔（秒） | **不要** |

**注意：** `page_timeout_sec` の「デフォルト値そのもの」は `localapp/src-tauri/src/config.rs` の Rust ソースに定義されており、**新規ユーザーに 600 を反映させるにはバイナリの再ビルドが必要**です。ただし、設定ファイルに値が書かれている限り、その値が優先されます。

### 2.2 ソースコードにハードコードされている値

変更には Rust ソースコードの修正と **再ビルドが必須** です。

| ファイル | 値 | 用途 | 今回のエラーとの関連 |
|---|---|---|---|
| `localapp/src-tauri/src/commands/backend_api.rs` | `reqwest` クライアント全体タイムアウト **60 秒** | HTTP 接続全体の総合タイムアウト | 低（ポーリングは短いリクエストを繰り返すため） |
| `localapp/src-tauri/src/commands/backend_api/backend_api_impl.rs` | `GET /api/jobs/{job_id}` タイムアウト **10 秒** | 1 回のジョブ状態取得のタイムアウト | 低（リトライ機構 `[1,2,4]` 秒 / 最大 2 回で補完） |
| `localapp/src-tauri/src/commands/backend_api/backend_api_impl.rs` | `POST /api/jobs/{job_id}/upload` タイムアウト **600 秒** | ZIP アップロードのタイムアウト | なし（アップロードは秒単位で完了） |
| `localapp/src-tauri/src/commands/backend_api/backend_api_impl.rs` | `POST /api/jobs/{job_id}/ocr` タイムアウト **60 秒** | OCR 実行依頼のタイムアウト | なし（backend が即座に `processing` を返す） |

### 2.3 環境変数で実行時に上書き可能な値

| ファイル | 値 | 用途 | 備考 |
|---|---|---|---|
| `backend/app/routers/jobs.py` | `_POLL_INTERVAL`（デフォルト **0.5 秒**） | SSE 進捗ファイルのポーリング間隔 | `PROGRESS_POLL_INTERVAL` 環境変数で上書き可能。ソース変更・再ビルド不要 |

## 3. 今回のエラーと関連するタイムアウト値の特定

### 3.1 エラーの発生箇所

`localapp/src-tauri/src/commands/backend_api/backend_api_impl.rs` 内のポーリングループ：

```rust
let deadline = Instant::now() + Duration::from_secs(page_timeout_sec * num_pages);
// ... ポーリングループ ...
if Instant::now() > deadline {
    return Err("OCR 処理がタイムアウトしました。 ...".to_string());
}
```

### 3.2 根本原因

1. `page_timeout_sec` のデフォルトが `300`（5 分/ページ）に設定されていた
2. ocr-worker（ndlocr_cli CPU 実行）の実測値は 1 ページあたり約 **383 秒**（約 6.4 分）
3. 3 ページ分の計算式：
   - **設定上の締切**: `3 × 300 = 900` 秒（15 分）
   - **実際の処理時間**: 約 **1152** 秒（約 19 分）
4. その結果、backend/ocr-worker は正常に PDF 生成まで完了したが、localapp 側が先にポーリングを打ち切り、「タイムアウト」エラーを表示した

### 3.3 結論

**今回の「OCR 処理がタイムアウトしました」エラーは、設定ファイルの `page_timeout_sec` の値が直接的かつ唯一の原因であり、これを変更することで解消可能でした。**

ハードコードされている HTTP 通信レイヤーのタイムアウト値（10 秒、60 秒）は、今回の事象には直接的な関与はありませんでした。

## 4. 再ビルドに関する確認事項

### 4.1 `page_timeout_sec` のデフォルト値 600 を反映させるには？

| シナリオ | 600 を反映させる方法 |
|---|---|
| **開発中** (`cargo tauri dev`) | ソース保存後の自動リビルド・再起動で反映 |
| **バイナリ配布** (`cargo tauri build`) | **再ビルドが必要**。新しい `.app` / `.exe` を生成する |
| `settings.json` が既に存在する場合 | 設定ファイルの値が優先されるため、**設定ファイルを削除・編集する必要がある** |

### 4.2 ハードコード値の設定ファイル化

2026-09-03: 以下のタイムアウト値を設定ファイルに移行し、すべてのタイムアウト値が `settings.json` で調整可能になった。

| 設定キー | デフォルト | 用途 |
|---|---|---|
| `http_client_timeout_sec` | `60` | reqwest クライアント全体のデフォルトタイムアウト |
| `upload_timeout_sec` | `600` | ZIP アップロード時の個別タイムアウト |
| `ocr_request_timeout_sec` | `60` | OCR 実行依頼（`POST /ocr`）の個別タイムアウト |
| `poll_request_timeout_sec` | `10` | ジョブ状態取得（`GET /jobs/{id}`）の個別タイムアウト |

これにより、localapp→backend→ocr-worker 連携時のすべてのタイムアウト値が設定ファイルで一元管理されるようになった。

## 5. 推奨事項

1. **リリース前の今回の修正（デフォルト値 300→600）は、次回のバイナリビルド時に自然に反映される**
2. **今後 `page_timeout_sec` を調整する必要が生じた場合**、設定ファイル `settings.json` を編集するだけで即時反映可能（再ビルド不要）
3. **ハードコードされている HTTP タイムアウト値について**、現状のままで問題ない：
   - ポーリングリクエスト（`GET /api/jobs/{job_id}`）は短時間（10 秒）で完結し、指数関数的バックオフ `[1,2,4]` 秒と最大 2 回のリトライ機構があるため、一過性の通信エラーを吸収できる
   - `/ocr` エンドポイントは非同期化済みで即座にレスポンスを返すため、60 秒のタイムアウトで十分

## 6. 関連ドキュメント

- `localapp/docs/caveats.md` — 「`page_timeout_sec` のデフォルト値調整（OT003001）」セクション
- `docs/progress-notification-spec.md` — 進捗通知方式仕様書（`page_timeout_sec` の仕様定義）
