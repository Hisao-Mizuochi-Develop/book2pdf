# replace-rules

既存ドキュメントの `replace_in_file` 使用時の具体ルール。

## 対象ドキュメント

- `docs/**`
- `backend/docs/**`
- `frontend/docs/**`
- `localapp/docs/**`
- `ocr-worker/docs/**`
- `test_cases/**/*.md`
- `.clinerules` 自身も含む

## 推奨 SEARCH パターン

| 状況 | SEARCH 例 |
|---|---|
| セクション末尾追記 | `## セクション名\n\n既存内容` |
| テーブル末尾追記 | `| --- | --- | --- |\n| 最終行 | ... |` |
| ファイル末尾追記 | `\n---\n` などの末尾マーカー |

## 禁止事項

- 既存ファイルへの `write_to_file`
- `sed -i` / `perl -i` などによる直接書き換え
- ユーザー承認なしの `.clinerules` 変更
