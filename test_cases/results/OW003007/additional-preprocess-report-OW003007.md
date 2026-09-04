# OW003007 追加前処理効果検証レポート

## 概要

- タスク名: 追加前処理（4x アップスケール、局所的二値化、コントラスト強調など）の効果検証
- 実施日: 2026-08-14 〜 2026-08-15
- 対象データ: `sample-png/手を動かしながら学ぶDocker入門_trimmed/001.png` 〜 `010.png`（10枚）
- OCR エンジン: ndlocr_cli（CPU 実行）
- 評価指標: 「〓」出現数、明らかな誤認識箇所数、目視確認

## 比較パターン

| パターン | 前処理内容 | 備考 |
|---|---|---|
| baseline_2x | 2倍 LANCZOS アップスケール + 軽度シャープニング | ocr-worker 内部前処理と同等。PREPROCESS_ENABLED=false でスクリプト側で実施 |
| 4x_upscale | 4倍 LANCZOS アップスケール | - |
| 4x_upscale_sharpen | 4倍アップスケール + 軽度シャープニング | - |
| local_binarization | 局所的二値化（純粋 numpy 畳み込みによるガウシアン加重平均） | - |
| local_binarization_sharpen | 局所的二値化 + 軽度シャープニング | - |
| contrast_strong | ImageEnhance.Contrast で強コントラスト（enhance 2.0） | - |
| contrast_strong_4x | 強コントラスト + 4倍アップスケール | - |

## 実行環境

- backend / ocr-worker コンテナ: `docker compose up -d`
- ocr-worker 自動前処理: `PREPROCESS_ENABLED=false`
- backend → ocr-worker タイムアウト: `OCR_WORKER_REQUEST_TIMEOUT=3600`（10ページ処理で 20〜30分を要するため 1800秒から延長）

## ジョブ一覧

| パターン | job_id | 状態 |
|---|---|---|
| baseline_2x | 10ddd822-8aad-43ea-a38d-1f67048fa3c9 | completed |
| 4x_upscale | 9da8bd3f-5751-4cac-9b88-47384c5be083 | completed |
| 4x_upscale_sharpen | 88828d53-b030-494f-b187-36e32e553649 | completed |
| local_binarization | 904148bd-6aae-4e2b-a575-e890a3110230 | completed |
| local_binarization_sharpen | 5dfd249c-6046-4411-916b-af914fc50750 | completed |
| contrast_strong | 74048f6b-37ec-498c-99ac-cfcc6483f478 | completed |
| contrast_strong_4x | 76f20761-8c17-4fd4-9823-42362cebffca | completed |

## 定量的結果

### 「〓」出現数（全 txt ファイル合計）

| パターン | 001 | 002 | 003 | 004 | 005 | 006 | 007 | 008 | 009 | 010 | total |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline_2x | 4 | 0 | 8 | 0 | 0 | 22 | 10 | 44 | 58 | 48 | 194 |
| 4x_upscale | 2 | 0 | 10 | 0 | 2 | 16 | 10 | 48 | 62 | 52 | 202 |
| 4x_upscale_sharpen | 0 | 0 | 6 | 2 | 2 | 14 | 8 | 40 | 56 | 50 | 178 |
| local_binarization | 10 | 12 | 10 | 12 | 8 | 12 | 12 | 10 | 33 | 16 | 135 |
| local_binarization_sharpen | 10 | 12 | 10 | 12 | 8 | 12 | 12 | 10 | 33 | 16 | 135 |
| contrast_strong | 0 | 0 | 0 | 2 | 0 | 18 | 10 | 44 | 40 | 46 | 160 |
| contrast_strong_4x | 0 | 0 | 8 | 2 | 0 | 20 | 6 | 48 | 46 | 46 | 176 |

### 「〓」出現数（_main.txt のみ）

| パターン | total |
|---|---|
| baseline_2x | 97 |
| 4x_upscale | 101 |
| 4x_upscale_sharpen | 89 |
| local_binarization | 68 |
| local_binarization_sharpen | 68 |
| contrast_strong | 80 |
| contrast_strong_4x | 88 |

## 目視確認結果

### 001 ページ（表紙）

| パターン | 確認結果 |
|---|---|
| baseline_2x | 「Dock〓r」「売全網〓」などの誤認識あり |
| 4x_upscale | 「Dock〓r」「売全網!」などの誤認識あり |
| 4x_upscale_sharpen | 「告でもCき6」「Dockerを完全マスター1」などの誤認識あり |
| local_binarization | 文字が潰れ、「DOckeiの」「D)〓⑦〓K〓[」など誤認識多数。読みにくい |
| local_binarization_sharpen | local_binarization と同様。シャープニングで改善せず |
| contrast_strong | 認識が大幅に欠落。「長相ルード」のみ出力。強コントラストで細部が潰れたと考えられる |
| contrast_strong_4x | 「誰でもでAる」「元全網!」などの誤認識あり。contrast_strong 単独よりはマシだが baseline 並み |

### 003 ページ（本文冒頭）

| パターン | 確認結果 |
|---|---|
| baseline_2x | 「〓ckER」「第〓部」などの誤認識あり。全体としては読める |
| 4x_upscale | 「〓0ckER」「第〓部」など。baseline と同等かやや悪化 |
| 4x_upscale_sharpen | 「0ckER」「第【部」など。比較的読みやすい |
| local_binarization | 文字が潰れ、「locker」「bocker」「dockerfle」など誤認識多数。可読性が低い |
| local_binarization_sharpen | local_binarization と同様 |
| contrast_strong | 認識欠落が多い。「基壁編」「コヽ」などの誤認識あり |
| contrast_strong_4x | 「〓0ckeR」「第〓部」「応用絹」など。baseline 並みの誤認識 |

### 009 ページ（目次）

| パターン | 確認結果 |
|---|---|
| baseline_2x | 目次の特殊文字・図形が多く、「〓」が大量に出現。読める部分もある |
| 4x_upscale | baseline と同様。一部誤認識のパターンが変化 |
| 4x_upscale_sharpen | baseline よりやや改善。「第3ま問」「4章問題」など認識できている |
| local_binarization | 文字が潰れ、「pocker」「dockernain」「docg」など誤認識多数。可読性が低い |
| local_binarization_sharpen | local_binarization と同様 |
| contrast_strong | 認識が大幅に欠落。ほとんどの行が空または 1〜2文字のみ |
| contrast_strong_4x | baseline 並みの誤認識。「Aca9e」「会cei200me」などの謎の文字列あり |

## 考察

1. **局所的二値化は 〓 数は減少するが、文字潰れによる誤認識が増加**
   - local_binarization / local_binarization_sharpen は「〓」数が最少（135）だが、目視確認では文字が潰れて「pocker」「bocker」などの誤認識が頻発。これは二値化によりアンチエイリアシング部分や細い文字が消失したためと考えられる。
   - シャープニングを追加しても改善せず、二値化の副作用を補えなかった。

2. **4x アップスケールは処理時間とファイルサイズが増大し、精度は改善しない**
   - 4x_upscale は baseline_2x より「〓」数が増加（202 vs 194）。
   - ファイルサイズも 279MB と baseline（82MB）の 3倍以上。
   - 4x_upscale_sharpen は baseline より改善（178）だが、OW003005 の 2x アップスケール＋シャープニングと比較して大きな差はない。

3. **強コントラストは細部を潰して認識欠落を招く**
   - contrast_strong は一部ページで認識が大幅に欠落。特に 009 ページではほとんどの行が空になった。
   - 4倍アップスケールを組み合わせると欠落は減るが、baseline 並みの誤認識に戻る。

4. **全体として、今回試した追加前処理は OW003006 で採用済みの 2x アップスケール＋軽度シャープニングを超える明確な改善は見られなかった**
   - 4x_upscale_sharpen や contrast_strong_4x で若干の改善はあるが、処理コスト（時間・ファイルサイズ）に見合う効果ではない。

## 結論

- 局所的二値化、4x アップスケール、強コントラストなどの追加前処理は、OW003006 で採用済みの 2x アップスケール＋軽度シャープニングを超える効果は確認できなかった。
- 特に局所的二値化と強コントラストは、文字潰れや認識欠落を招くリスクが高く、現状の ocr-worker 自動前処理に追加導入することは推奨されない。
- 4x_upscale_sharpen は baseline より改善するが、ファイルサイズと処理時間が 3倍以上になるため、コストパフォーマンスが悪い。

## 今後の検討事項

1. **対象ページに応じた適応的前処理の検討**
   - 表紙や目次など、文字サイズやレイアウトが異なるページに対して、自動で前処理パラメータを切り替える仕組みを検討する。

2. **OCR 後処理（辞書ベース補正）の検討**
   - 前処理だけでは限界があるため、「Docker」「dockerfile」などの固有名詞や頻出単語を辞書で補正する後処理を検討する。

3. **他の前処理手法の検討**
   - ノイズ除去、傾き補正、背景除去など、他の前処理手法を追加検討する。

4. **レイアウト認識パラメータとの組み合わせ調整**
   - OW003005 で調整した `score_thr` パラメータとの組み合わせで、さらなる改善の余地があるか確認する。
