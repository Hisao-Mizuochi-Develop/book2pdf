# 設定ファイル(config.json)スキーマ

`core/config.py` の `DEFAULT_CONFIG` を起点に、`core/config.json`
（初回起動時に自動生成、`.gitignore` 対象の個人設定）へユーザー変更が
非破壊マージ（`_deep_merge`）されます。

## 全体構造

```jsonc
{
  "capture": {
    "active_profile": "kindle",
    "profiles": {
      "<profile_key>": { /* CaptureProfile フィールド一式 */ }
    }
  },
  "trim": {
    "left_margin": 0, "right_margin": 0, "top_margin": 0, "bottom_margin": 0
  },
  "ocr": {
    "reflow_paragraphs": true,
    "preprocess": { "enabled": true, "upscale": 1.5, "enhance_contrast": true,
                    "binarize": false, "binarize_threshold": 180 },
    "replacements": { "enabled": true, "path": "" },
    "chapter_bookmarks": { "enabled": true },
    "markdown": { "embed_images": false }
  },
  "general": { "default_save_folder": "", "theme": "auto" }
}
```

## `capture.profiles.<key>`（`CaptureProfile` dataclass, `core/capture_profiles.py`）

| フィールド | 型 | 既定値 | 説明 |
|-----------|-----|--------|------|
| `name` | str | `""` | 表示名 |
| `window_title_keyword` | str | `""` | ウィンドウタイトルの検索キーワード（大文字小文字無視） |
| `page_turn_key` | str | `"right"` | ページめくりキー。効かない場合は自動でspace/pagedown/down/scrollへエスカレーション |
| `fullscreen_wait` | float | `5.0` | キャプチャ開始前、ウィンドウ前面化後の待機秒数 |
| `page_wait` | float | `0.5` | ページめくり後、次の撮影までの待機秒数 |
| `boundary_method` | str | `"full"` | `"full"`（クロップなし）or `"manual"`（手動範囲） |
| `l_margin` / `r_margin` | int | `1` | 旧方式の名残。現在未使用（互換のため残置） |
| `manual_left` / `manual_right` | int | `0` | `boundary_method="manual"` 時のウィンドウ相対クロップ座標 |
| `click_position` | str | `"center"` | 旧: 前面化時のクリック位置指定。**macOS版ではクリック自体を行わないため実質未使用**（[macos-port-notes.md](macos-port-notes.md) 参照）。値自体はプロファイル間の互換性のため残置 |
| `use_bring_to_top` | bool | `False` | （Windows版の `BringWindowToTop` 相当。macOS版では前面化ロジックに影響しない） |
| `process_name` | str | `""` | プロセス名フィルタ。空なら無効。指定時は該当プロセスのウィンドウのみを探す（フォールバックなし） |
| `timeout_seconds` | float | `5.0` | 1ページあたり、変化なしと判定するまでのタイムアウト |
| `max_retries` | int | `3` | 例外発生時・保存失敗時のリトライ回数上限 |

未知のキーは `CaptureProfile.from_dict()` で無視されるため、Windows版の
`config.json` をそのまま流用しても壊れません。

## `ocr.preprocess`（`core/ocr_preprocess.py` に対応）

| フィールド | 説明 |
|-----------|------|
| `enabled` | OCR前処理を行うか |
| `upscale` | Lanczosアップスケール倍率（1.0=なし、1.5推奨、2.0=丁寧） |
| `enhance_contrast` | autocontrast（グレースケール化を伴う） |
| `binarize` / `binarize_threshold` | 単純二値化（既定OFF。地色が薄い本やカラー図版で逆効果になりやすい） |

## `ocr.replacements`（`core/text_replacements.py` に対応）

| フィールド | 説明 |
|-----------|------|
| `enabled` | 置換辞書を適用するか |
| `path` | 辞書ファイルパス。空なら既定パス（プロジェクトルート/replacements.json）を使用 |

辞書ファイル自体のスキーマは `replacements.json` の例、または
`core/text_replacements.py` のモジュールdocstringを参照してください。

## `ocr.chapter_bookmarks` / `ocr.markdown`

| フィールド | 説明 |
|-----------|------|
| `chapter_bookmarks.enabled` | 章自動検出を行い、PDFしおり/Markdown見出しを挿入するか |
| `markdown.embed_images` | Markdown出力時、ページ画像へのリンクを本文前に併記するか |

## `general`

| フィールド | 型 | 既定値 | 説明 |
|-----------|-----|--------|------|
| `default_save_folder` | str | `""` | 出力先フォルダのデフォルト。空なら OS 標準のダイアログ初期位置 |
| `theme` | str | `"auto"` | UI テーマ。`"dark"` / `"light"` / `"auto"` |

## `trim`

トリミングタブの「デフォルトとして保存」ボタンで書き込まれる、次回起動時の初期値。
