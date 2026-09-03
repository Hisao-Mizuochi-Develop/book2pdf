# 003005 score_thr 比較レポート（前処理 ON）

## 概要

- タスクNo: 003005
- 実施日: 2026-08-14
- 目的: 前処理 ON（`PREPROCESS_ENABLED=true`）状態で、`layout_extraction.score_thr` を 0.1〜0.5 の5段階に設定し、backend API 経由のフルフローで OCR を実行して、生成 PDF と OCR 出力を比較する
- 対象データ: `benchmark-ocr-003002.zip`（002.png / 003.png / 004.png、計 3 ページ）
- OCR エンジン: ndlocr_cli（ocr-worker コンテナ経由）
- 評価指標: PDF ファイルサイズ、認識テキスト文字数、XML テキストブロック数、目視比較

## 比較パターン

| パターン | score_thr | 前処理 | 備考 |
|----------|-----------|--------|------|
| score-thr-0.1 | 0.1 | ON（sharpen_light_upscale_2x） | 低閾値：多くの候補を検出 |
| score-thr-0.2 | 0.2 | ON（sharpen_light_upscale_2x） | 前回 Pattern-A と同値 |
| score-thr-0.3 | 0.3 | ON（sharpen_light_upscale_2x） | 追加パターン |
| score-thr-0.4 | 0.4 | ON（sharpen_light_upscale_2x） | 追加パターン |
| score-thr-0.5 | 0.5 | ON（sharpen_light_upscale_2x） | 高閾値：スコアの高い候補のみ検出 |

## 実行手順

1. `docker compose up -d` で backend / ocr-worker コンテナを起動
2. `ocr-worker` コンテナ内の `/opt/ocr-worker/config.yml` の `layout_extraction.score_thr` を変更
3. `docker compose restart ocr-worker` で config.yml を再読み込み
4. backend API でジョブ作成 → ZIP アップロード → OCR 実行
5. `GET /api/jobs/{job_id}` で `completed` になるまでポーリング
6. 生成 PDF と OCR 出力（XML/txt）を `docker compose cp` で取得
7. 5パターンの PDF からページ画像を生成し、`visual-compare-5patterns.html` で目視比較

## 定量的結果

### PDF ファイルサイズと認識テキスト文字数

| score_thr | Job ID | PDF サイズ | テキスト文字数 | PDF ページ数 |
|-----------|--------|-----------|--------------|-------------|
| 0.1 | 392159c8-5036-48c8-82e6-0f6dced21378 | 22,367,802 bytes (21 MB) | 3,051 | 3 |
| 0.2 | 51915af2-4e01-4c50-adec-b372b20ca0ed | 22,367,802 bytes (21 MB) | 3,051 | 3 |
| 0.3 | be5913f9-6cd2-4632-8e87-f9e1205084b2 | 22,367,802 bytes (21 MB) | 3,051 | 3 |
| 0.4 | e8701df6-ccc7-4283-8fad-c901d8820250 | 22,367,802 bytes (21 MB) | 3,051 | 3 |
| 0.5 | 97053c56-ab64-483b-a625-0b2db60a31cb | 22,367,802 bytes (21 MB) | 3,051 | 3 |

### XML テキストブロック数

| score_thr | 総 BLOCK 数 | Page 1 (表紙) | Page 2 (注意書き) | Page 3 (はじめに) |
|-----------|------------|---------------|-------------------|-------------------|
| 0.1 | 5 | 3 | 0 | 2 |
| 0.2 | 4 | 3 | 0 | 1 |
| 0.3 | 2 | 1 | 0 | 1 |
| 0.4 | 2 | 1 | 0 | 1 |
| 0.5 | 1 | 1 | 0 | 0 |

## 目視確認結果

目視比較用 HTML: [visual-compare-5patterns.html](visual-compare-5patterns.html)

### Page 1: 表紙（002.png）

- score_thr=0.1 / 0.2: 表紙全体を覆う大きな緑色検出枠に加え、タイトル周辺や著者名周辺に小さな検出枠が複数ある
- score_thr=0.3 / 0.4: 大きな検出枠 1 のみとなり、小さな検出枠は除去された
- score_thr=0.5: score_thr=0.3 / 0.4 と同様に大きな検出枠 1 のみ

表紙の見た目上の違いは、緑色のレイアウト検出枠の数と範囲に集中しており、最終的な OCR テキストや PDF レイアウトには大きな差は見られない。

### Page 2: 注意書き（003.png）

- すべての score_thr で BLOCK 数は 0
- 目視でもレイアウト検出枠はほとんど確認できず、各パターンでほぼ同じ表示になっている
- このページは layout_extraction の検出対象にならないか、スコアがすべて閾値以下となった

### Page 3: はじめに（004.png）

- score_thr=0.1: 2 つの検出枠（タイトル部と本文部）
- score_thr=0.2: 1 つの検出枠（本文部のみ、タイトル部が閾値を下回った）
- score_thr=0.3 / 0.4: 1 つの検出枠
- score_thr=0.5: 0 ブロック（このページ全体の検出が閾値を下回った）

ただし、認識テキスト文字数はすべて 3,051 文字で同一であり、PDF としても同じ内容が出力されている。これは、最終的な文字認識結果には layout_extraction のブロック分割数が影響していないことを示唆している。

## 考察

1. **score_thr の影響範囲**
   - `layout_extraction.score_thr` は、レイアウト解析で検出するテキストブロックの信頼度閾値を制御している
   - score_thr が高いほど、低スコアの小さなブロックや周辺要素が除外され、シンプルなレイアウト構造になる
   - 今回のテストデータでは、表紙のタイトル周辺や「はじめに」ページのタイトル部など、スコアが中程度のブロックが閾値上昇に伴って除去された

2. **PDF / テキスト出力への影響**
   - 全パターンで PDF サイズ、テキスト文字数、ページ数は完全に同一
   - これは、backend の `pdf_generator.py` が XML のブロック情報ではなく、OCR 結果のテキストと元画像から PDF を生成しているため、layout_extraction のブロック分割数が最終 PDF に直接反映されていないことを示している
   - したがって、**このテストデータにおいては score_thr の変更が最終的な OCR テキスト精度や PDF 品質に影響を与えていない**

3. **前処理 ON の効果**
   - 前回の 003005/003006 検証で確認された通り、前処理 ON により認識率は向上している
   - 本検証では前処理を ON に固定し、score_thr のみを変化させたため、前処理の効果は共通因子として安定している

4. **score_thr の選定指針**
   - 現状の backend PDF 生成ロジックでは、score_thr の変更が視覚的・定量的に差を生じさせにくい
   - ただし、将来的に XML のブロック情報を利用した高度な PDF レイアウト制御を導入する場合、score_thr は重要な調整パラメータとなる
   - 現時点では、極端に高い値（0.5）にすると一部ページでブロックが 0 になりうるため、過剰除外のリスクがある

## 結論

- 前処理 ON 状態で score_thr を 0.1〜0.5 の範囲で変更しても、**最終的な PDF ファイルサイズ、テキスト文字数、ページ数には差が出なかった**
- score_thr の違いは **XML のテキストブロック数** に明確に表れ、高い閾値ほどブロック数が減少する
- 目視比較でも、最終 PDF の文字表示品質に大きな差は認められなかった
- 現状のシステムでは、最終出力品質への影響が小さいため、score_thr はデフォルト値（0.2）付近で運用して問題ない
- 将来的に XML ブロック情報を活用したレイアウト制御を強化する場合は、再検討が必要

## 今後の検討事項

- backend の `JobResponse` に `output_dir` を含める修正を検討し、OCR 出力の取得を容易にする
- よりレイアウトが複雑な文書（複数カラム、図表混在、注釈多数など）で score_thr の影響を再評価する
- XML のブロック情報を PDF 生成に活用する場合の設計を検討する
- 前処理 OFF 状態での score_thr 比較も実施し、前処理と score_thr の相互作用を確認する

## 参考ファイル

- 実行スクリプト: [../../scripts/run_003005_retest.sh](../../scripts/run_003005_retest.sh)
- 比較 HTML: [visual-compare-5patterns.html](visual-compare-5patterns.html)
- ページ画像ディレクトリ: [pdf_page_images_5patterns/](pdf_page_images_5patterns/)
