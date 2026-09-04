# 003006 Backend API OCR 連携 end-to-end テスト結果

## 概要

| 項目 | 内容 |
|------|------|
| タスクID | 003006 |
| タスク名 | localapp → backend API 経由の OCR/PDF 作成連携 |
| 実施日 | （テスト実行後に記入） |
| 目的 | localapp の「PDF作成」画面から backend API を呼び出し、OCR 済み PDF が正常に作成されることを確認する |

## 使用したテストデータ

- パス: `test_cases/testdata/localapp/003006-backend-ocr-test/`
- ファイル:
  - `002.png`
  - `003.png`
  - `004.png`

## 実行手順

1. `npm run tauri dev` で localapp を起動
2. 左サイドバーから **「PDF作成」** を選択
3. 「入力設定」で **「フォルダを選択」** をクリック
4. `test_cases/testdata/localapp/003006-backend-ocr-test/` を選択
5. 「出力ファイル名」に `003006-backend-ocr-test-09030008` を入力
6. 「出力先フォルダ」に `/Users/hisao/Documents/work4/sakura/book2pdf/test_cases/testdata/localapp` を選択
7. **「backend OCR で PDF 作成」** ボタンをクリック
8. 保存ダイアログで `test_cases/testdata/localapp/003006-backend-ocr-test-09030008.pdf` を指定
9. 進捗表示が `completed` になるまで待機
10. DevTools Console (`Cmd + Shift + I` / `Cmd + Option + I`) でエラーを確認

## 期待結果

- 画像ファイルが 3 枚と認識される
- 進捗バーが `preparing → uploading → ocr → polling → downloading → completed` と進む
- `/ocr` リクエストは 60 秒以内に `processing` 状態を返す
- ポーリング中に `processing` 状態が維持される
- `test_cases/testdata/localapp/003006-backend-ocr-test-09030008.pdf` が作成される
- 生成された PDF はテキスト検索可能（例：「Improving」「RAG」などで検索）
- DevTools Console に赤いエラーが表示されない

## 実際の結果

| 項目 | 結果 |
|------|------|
| PDF 作成 | （後で記入） |
| 作成先パス | （後で記入） |
| 進捗表示 | （後で記入） |
| DevTools Console エラー | （後で記入） |

## 判定

<!-- テスト完了後、PASS または FAIL を記入 -->

**（後で記入）**

## 備考

- OCR 処理は 1 ページあたり約 6 分かかる（3 ページで計測値 396 秒）。完了までに数十分かかるため、テスト時は時間に余裕を持つこと。
- backend コンテナを再起動すると、進行中のバックグラウンド OCR タスクは失われる。今後 005001（SQLite 永続化）の対応で解消予定。
- （スクリーンショットや追加メモがあれば記入）
