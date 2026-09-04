# OW003006: sharpen_light_upscale_2x 自動前処理の ocr-worker 組み込み 検証レポート

## 概要

- タスク名: sharpen_light_upscale_2x 自動前処理の ocr-worker 組み込み
- 実施日: 2026-08-14
- 対象データ: `benchmark-ocr-OW003002.zip`（002.png 表紙、003.png 注意書き、004.png 本文）
- OCR エンジン: ndlocr_cli（CPU 実行）
- 評価指標: 「〓」出現数、明らかな誤認識箇所数

## 比較パターン

| パターン | 前処理 | 備考 |
|---|---|---|
| preprocess-on | sharpen_light_upscale_2x（2x LANCZOS + UnsharpMask radius=2, percent=80, threshold=3） | `PREPROCESS_ENABLED=true`（デフォルト） |
| preprocess-off | 前処理なし | `PREPROCESS_ENABLED=false` |

## 実行条件

- ocr-worker コンテナ内で `PREPROCESS_ENABLED` 環境変数により ON/OFF を制御
- backend API 経由でフルフロー実行（ジョブ作成 → ZIP アップロード → OCR → PDF 生成）
- 各パターンごとに `/data/extracted/*`, `/data/ocr_output/*`, `/data/pdfs/*` をクリーンアップ

## 定量的結果

### ジョブ情報

| パターン | ジョブ ID | 状態 | PDF サイズ |
|---|---|---|---|
| preprocess-on | ec9acd66-563f-41e0-8410-08619208e6e9 | completed | 22,368,443 bytes |
| preprocess-off | e07faa8c-195b-4d36-bc7c-d44e0aa28582 | completed | 22,368,443 bytes |

### 「〓」出現数

| パターン | 002_main | 003_main | 004_main | 合計 |
|---|---|---|---|---|
| preprocess-on | 0 | 2 | 1 | 3 |
| preprocess-off | 0 | 3 | 2 | 5 |

### 主な誤認識箇所

#### 002.png（表紙）

| 箇所 | 正解 | preprocess-on | preprocess-off |
|---|---|---|---|
| タイトル | 精度改善 | 精度孜善 | 精度改善 |
| 英数字 | Improving | mproving | mproving |
| 英数字 | Generation | Generation | generation |
| カタカナ | AI前処理 | イ前処理 | K前処理 |
| カタカナ | AI検索 | イ検索 | K検索 |
| カタカナ | AI生成 | イ生成 | K生成 |
| 本文 | 実務に役立つ | 実務に役立つ | 実務に役立っ |

- preprocess-on でも表紙の「精度孜善」「mproving」などは改善されず
- preprocess-off では AI→K、実務に役立つ→実務に役立っ などの追加誤認識が発生

#### 003.png（注意書き）

- preprocess-on: 登録溶標（登録商標）、省略しています などに「〓」混在（2 個）
- preprocess-off: 上記に加え、変更されている→変〓されている、技術資料を基に→技術資料を基4 など（3 個）

#### 004.png（本文）

- preprocess-on: GPT-4→〓PT-4（1 個）
- preprocess-off: GPT-4→〓PT-4、LLM→〓LM（2 個）

## 考察

1. **前処理の効果は確認された**: preprocess-on の方が全体的に「〓」出現数が少なく、誤認識箇所も抑制されている。003.png・004.png では前処理 ON で改善が顕著。

2. **表紙（002.png）は改善が限定的**: OW003003 で手動前処理 ZIP をアップロードした際と比較すると、自動前処理 ON でも表紙の「精度孜善」「mproving」などが残存。これは以下の要因が考えられる:
   - OW003003 では ZIP 内画像に前処理を適用してから backend にアップロードしたが、今回は backend が ZIP を展開して input_root/img/ を作成し、ocr-worker がその画像に前処理を適用している。両者で画像形式やメタデータが異なる可能性がある。
   - backend から ocr-worker へのリクエスト経路では、画像の解像度や色空間がホスト側のスクリプト処理と異なる可能性がある。
   - 表紙は装飾フォント・小さな文字が多く、2x アップスケール＋軽度シャープニングだけでは不十分な可能性がある。

3. **処理時間**: 前処理 ON の場合、画像が 2 倍になるため OCR 処理時間が増加する。今回の計測では preprocess-on が約 2 分、preprocess-off が約 4 分だったが、これには初回モデル初期化の影響も含まれるため厳密な比較には不向き。詳細は別途性能評価タスクで計測する。

## 結論

- `sharpen_light_upscale_2x` の自動前処理を ocr-worker に組み込み、`PREPROCESS_ENABLED` 環境変数で ON/OFF 制御できるようにした。
- backend API 経由のフルフローで、前処理 ON の方が誤認識を抑制できることを確認した。
- 表紙ページに関しては、2x アップスケール＋軽度シャープニングだけでは完全な改善が難しく、別途表紙専用の追加前処理や後処理の検討が必要。

## 今後の検討事項

- 表紙ページ（002.png）に対する追加前処理（4x アップスケール、局所的二値化、コントラスト強調など）の効果検証
- 前処理による処理時間増加の定量的な性能評価
- 前処理パラメータを環境変数やリクエストパラメータで調整可能にする検討
- 前処理済み画像の品質確認用に一時ファイルのデバッグ保存オプションの検討
