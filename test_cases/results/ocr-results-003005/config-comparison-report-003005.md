# config.yml score_thr 修正後の再検証レポート

タスク No: 003005
実施日: 2026-08-14

## 概要

本レポートは、タスク 003005「OCR精度向上の統合検討と実装修正（config.yml score_thr 無視問題の修正と再検証）」の再検証結果をまとめたものです。

- OCR エンジン: ndlocr_cli（CPU 実行）
- 対象データ: `benchmark-ocr-003002.zip`（002.png 表紙、003.png 注意書き、004.png はじめに）
- 評価指標: TEXTBLOCK 数、LINE 数、認識文字数、「〓」置換数、PDF 目視確認
- 実施方法: `.clinerules` 第 10 章に基づき、backend API 経由のフルフローで実行

## 背景

003004 で `layout_extraction.score_thr` の変更に効果がないと判断しましたが、これは ndl_layout submodule の `process_textblock.py` / `process.py` に `score_thr: float = 0.3` がハードコードされており、config.yml の値が無視されていたためでした。003005 では `process_textblock.py` をパッチ版で上書きし、config.yml の値が反映されるように修正しました。

本レポートでは、修正後に backend API 経由のフルフローで pattern-A/B/C を再実行し、生成された PDF を含めて精度を比較します。

## 比較パターン

| パターン | layout_extraction.score_thr | 目的 |
|---|---|---|
| Pattern-A | 0.2 | 低 CONF 領域も検出する |
| Pattern-B | 0.1 | さらに検出感度を上げる |
| Pattern-C | 0.5 | 高閾値でノイズ抑制を狙う |

## 実施手順

1. `docker compose up -d` で backend / ocr-worker を起動
2. ocr-worker コンテナ内の `/opt/ocr-worker/config.yml` の `layout_extraction.score_thr` を各パターンの値に変更
3. `POST /api/jobs` → `POST /api/jobs/{job_id}/upload` → `POST /api/jobs/{job_id}/ocr` → `GET /api/jobs/{job_id}` ポーリング
4. 生成 PDF を `docker compose cp backend:/data/pdfs/<job_id>.pdf ./ocr-results-003005/<pattern>/pdfs/` で取得
5. OCR 出力（XML / txt）も併せて取得
6. PDF をページ画像に変換し、ブラウザで 3 パターンを横並び目視確認

## 定量的結果

### XML 構造比較

| パターン | 002_L.jpg TEXTBLOCK | 002_L.jpg BLOCK | 002_L.jpg LINE | 003_L.jpg TEXTBLOCK | 004_L.jpg TEXTBLOCK |
|---|---:|---:|---:|---:|---:|
| Pattern-A (0.2) | 1 | 3 | 11 | 2 | 2 |
| Pattern-B (0.1) | 1 | 3 | 11 | 2 | 2 |
| Pattern-C (0.5) | 0 | 1 | 9  | 2 | 1 |

### 認識文字数・置換記号

| パターン | ページ数 | 認識文字数 | 「〓」出現数 |
|---|---:|---:|---:|
| Pattern-A (0.2) | 3 | 1,294 | 5 |
| Pattern-B (0.1) | 3 | 1,295 | 5 |
| Pattern-C (0.5) | 3 | 1,265 | 5 |

### PDF 情報

| パターン | ページ数 | サイズ | ページ寸法 |
|---|---:|---:|---|
| Pattern-A (0.2) | 3 | 22,368,443 bytes | 664 x 942 pt |
| Pattern-B (0.1) | 3 | 22,368,443 bytes | 664 x 942 pt |
| Pattern-C (0.5) | 3 | 22,367,788 bytes | 664 x 942 pt |

### テキスト差分

- Pattern-A と Pattern-B の `_main.txt` は完全一致（`diff` で差分なし）
- Pattern-C の 002.png から「咸毅成[著]」と「RAC」が欠落
- Pattern-C の 004.png から「はじめに」が欠落

## PDF 目視確認結果

目視確認用 HTML: [visual-compare-pages.html](visual-compare-pages.html)

### Page 1: 表紙 (002.png)

- Pattern-A/B: 右下の著者名「咸毅成[著]」が緑色で重ね表示されている
- Pattern-C: 右下の著者名「咸毅成[著]」が欠落している

### Page 2: 注意書き (003.png)

- 3 パターンともレイアウト・文字認識に目視で確認できる差分はない

### Page 3: はじめに (004.png)

- Pattern-A/B: 左上の「はじめに」が表示されている
- Pattern-C: 左上の「はじめに」が欠落している

## 考察

1. **config.yml の score_thr が反映された**: Pattern-C で score_thr=0.5 と高く設定したところ、低 CONF のテキストブロックが検出されなくなりました。これは、修正後の `process_textblock.py` が config.yml の値を実際に参照していることを示しています。

2. **score_thr=0.2 と 0.1 の差は検出されなかった**: 本テストデータでは、0.2 まで下げれば既にすべての対象テキストブロックが検出されており、0.1 まで下げても追加のブロックは得られませんでした。過度に下げるとノイズ検出リスクが増すため、0.2 が実用上の下限と考えられます。

3. **score_thr=0.5 の影響は限定的**: 表紙の著者名と「はじめに」の見出しが欠落しましたが、これらは比的小さな文字や低 CONF に分類されるテキストブロックです。一方、本文ページ（003.png）では影響がほとんどありませんでした。これは、本文の行ほど CONF が高く、0.5 を超えているためです。

4. **認識品質（文字の正しさ）には影響なし**: score_thr の変更は「検出するかどうか」の閾値であり、一度検出された行の文字認識品質自体は変化しませんでした。したがって「〓」の出現数や誤認識箇所は 3 パターンで同一でした。

## 結論

- `process_textblock.py` パッチにより、config.yml の `layout_extraction.score_thr` が実際に反映されるようになったことを確認しました。
- 本テストデータにおいては `score_thr=0.2` が最適であり、デフォルト値 0.3 よりも若干低い閾値で全テキストブロックを検出できました。
- `score_thr=0.5` は表紙や見出しの小さな文字ブロックを落とすため、推奨されません。
- 自動前処理統合（sharpen_light_upscale_2x）や表紙ページ対策は別タスクとして実施します。

## 今後の検討事項

- より多様なページ（小さな注釈・縦書き・図表内文字）を含むデータセットで score_thr の最適値を再評価する
- 前処理（sharpen_light_upscale_2x）と組み合わせた場合の score_thr 最適値を検討する
- 表紙ページに対する専用前処理や後処理辞書の効果を別途検証する

## 参考ファイル

- PDF 目視比較（ページ画像）: [visual-compare-pages.html](visual-compare-pages.html)
- PDF 目視比較（PDF iframe）: [visual-compare.html](visual-compare.html)
- Pattern-A PDF: [pattern-a/pdfs/9c09ae26-bc1b-48e8-a0e1-5408ce42a3a6.pdf](pattern-a/pdfs/9c09ae26-bc1b-48e8-a0e1-5408ce42a3a6.pdf)
- Pattern-B PDF: [pattern-b/pdfs/a4345c8a-9842-440d-8731-200f7785f059.pdf](pattern-b/pdfs/a4345c8a-9842-440d-8731-200f7785f059.pdf)
- Pattern-C PDF: [pattern-c/pdfs/068fee0f-6ab1-4dfa-be9a-958568687897.pdf](pattern-c/pdfs/068fee0f-6ab1-4dfa-be9a-958568687897.pdf)
