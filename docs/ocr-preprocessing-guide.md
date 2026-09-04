# OCR 前処理・画像サイズ制御ガイド

本ドキュメントは、`reference/docs/config-reference.md` および `CHANGELOG-20250815.md` の「変換（OCR）」に関する記載を参考にし、book2pdf（ndlocr_cli + FastAPI 構成）で活用できる知見をまとめたものです。

---

## 1. 取り込み済み（実装・検証済み）

| 項目 | book2pdf での対応状況 | 根拠レポート |
|---|---|---|
| ✅ OCR 前処理 ON/OFF | `ocr-worker/app/main.py` の `PREPROCESS_ENABLED` 環境変数で制御。`true` がデフォルト | [OW003006 レポート](../ocr-results-OW003006/preprocess-integration-report-OW003006.md) |
| ✅ 2x アップスケール + 軽度シャープニング | `ocr-worker/app/main.py` の `_preprocess_image()` で固定実装。デフォルト前処理として採用 | [OW003003 レポート](../ocr-results-OW003003/preprocess-comparison-report-OW003003.md)（最も効果的）、[OW003006 レポート](../ocr-results-OW003006/preprocess-integration-report-OW003006.md) |
| ✅ `layout_extraction.score_thr` 調整 | `ocr-worker/ndlocr_cli_patches/process_textblock.py` で config.yml の値を参照するようパッチ。0.1〜0.5 で検証済み | [OW003005 レポート](../ocr-results-OW003005/config-comparison-report-OW003005.md) |
| ✅ 前処理なし（baseline）との比較 | OW003003 で全パターンが baseline と比較。OW003006 で `PREPROCESS_ENABLED=true/false` で検証 | [OW003003 レポート](../ocr-results-OW003003/preprocess-comparison-report-OW003003.md)、[OW003006 レポート](../ocr-results-OW003006/preprocess-integration-report-OW003006.md) |
| ✅ 追加前処理パターンの効果検証 | `scripts/preprocess_image.py` に 11 パターンを実装。OW003007 で 7 パターンを比較 | [OW003007 レポート](../ocr-results-OW003007/additional-preprocess-report-OW003007.md) |

### 1.1 取り込み済み前処理の詳細

`ocr-worker` のデフォルト前処理は以下の通りです。

```python
# 2 倍アップスケール（LANCZOS 補間）
new_size = (img.width * 2, img.height * 2)
img = img.resize(new_size, Image.Resampling.LANCZOS)

# 軽度シャープニング
img = img.filter(
    ImageFilter.UnsharpMask(radius=2, percent=80, threshold=3)
)
```

これは OW003003 で最も効果的だった `sharpen_light_upscale_2x` と同一の処理です。

### 1.2 取り込み済み設定の推奨値

| 項目 | 推奨値 | 備考 |
|---|---|---|
| `PREPROCESS_ENABLED` | `true` | 前処理 ON で「〓」出現数が減少（OW003006: 5→3） |
| `layout_extraction.score_thr` | `0.2`〜`0.3` | デフォルト 0.3 で問題ない。0.2 まで下げても最終 PDF への影響は小さい（OW003005） |
| `OCR_WORKER_REQUEST_TIMEOUT` | `1800` 秒 | 一般書籍で十分。超大判書籍では `3600` 秒以上を検討 |

---

## 2. 取り込んでいないが要検討

| 項目 | 現状 | 未採用の理由 | 検討条件 |
|---|---|---|---|
| ⏳ `max_pixels` による画素数制限 | 未実装。`ocr-worker` は 2x アップスケールを固定適用し、上限なし | 超大判画像で処理時間短縮・メモリ抑制に有効だが、現状のテストデータでは発生していない | 8,000×14,000 ピクセル級の超大判書籍でタイムアウト / メモリ不足が発生した場合 |
| ⏳ `binarize`（二値化）の自動統合 | `scripts/preprocess_image.py` の `local_binarization` は実装済みだが、`ocr-worker` 自動前処理には未統合 | OW003007 で「文字潰れによる誤認識が増加」と判定。カラー図版では逆効果のリスク | 白黒印刷物・旧字体文書など、別データセットで再検証して効果が確認できた場合 |
| ⏳ `enhance_contrast`（コントラスト強調）の自動統合 | `contrast_gamma` / `contrast_strong` は実装済みだが、`ocr-worker` 自動前処理には未統合 | OW003007 で「細部潰れ・認識欠落」と判定。特に表紙・目次で悪化 | 薄字・地色ノイズが多い文書で、2x アップスケール単独では不足と確認できた場合 |
| ⏳ `upscale` 倍率の動的切り替え（1.5x / 3x など） | `ocr-worker` は固定 2x のみ | OW003003 で 2x が最良と確認。1.5x / 3x の効果は未検証 | 処理速度優先で 1.5x を試す、または表紙対策で 3x を試す場合 |
| ⏳ per-page タイムアウト制御 | backend→ocr-worker は job 全体の HTTP タイムアウト（1800秒）のみ | reference 側は 1枚あたり 120〜300 秒。book2pdf のアーキテクチャでは job 単位が自然 | 長大な文書で特定ページだけタイムアウトする問題が発生した場合 |
| ⏳ `replacements`（文字置換辞書） | 未実装 | OW003002 の「GPT-4→〓PT-4」「LLM→lm」など、固有名詞・記号の誤認識に対して有効 | 頻出する誤認識パターンが特定でき、後処理で補正したい場合 |
| ⏳ `reflow_paragraphs`（段落自動再構成） | 未実装。Markdown 出力機能自体が未実装 | Markdown 出力時の可読性向上に有効 | Markdown ダウンロード機能を実装する場合 |
| ⏳ `chapter_bookmarks`（章しおり検出） | 未実装。PDF 生成時に見出し検出・しおり挿入の機能なし | テキスト PDF の利便性向上に有効 | 検索可能 PDF にしおり / 目次を追加する場合 |
| ⏳ `markdown.embed_images` | 未実装 | Markdown ファイル単体配布時に画像を含めたい場合 | Markdown 出力機能を実装する場合 |
| ⏳ DecompressionBombError 対策の強化 | UI 層未実装。前処理層は部分的（上限解除なし）、OCR エンジン層は標準的 | reference 側の多層対策を参考に、ocr-worker の前処理層に `max_pixels` clamp を追加可能 | 超大判画像で `DecompressionBombError` が実際に発生した場合 |

---

## 3. 前処理パラメータと book2pdf への対応

kindle_shot（reference）側の変換タブでは、以下の前処理パラメータを制御しています。book2pdf では対応する機能が `scripts/preprocess_image.py` および `ocr-worker/app/main.py` に実装されています。

| kindle_shot パラメータ | 意味 | book2pdf での対応 |
|---|---|---|
| `ocr.preprocess.enabled` | OCR 前処理の ON/OFF | ✅ `ocr-worker/app/main.py` の `PREPROCESS_ENABLED` 環境変数（デフォルト: `true`） |
| `ocr.preprocess.upscale` | 画像拡大倍率（Lanczos） | ✅ 固定 2x + 軽度シャープニングを `_preprocess_image()` で適用 |
| `ocr.preprocess.enhance_contrast` | コントラスト自動調整 | ⏳ `scripts/preprocess_image.py` の `contrast_gamma` / `contrast_strong` で実装済み。`ocr-worker` 自動前処理には未統合 |
| `ocr.preprocess.binarize` | 二値化 ON/OFF | ⏳ `scripts/preprocess_image.py` の `local_binarization` で実装済み。`ocr-worker` 自動前処理には未統合 |
| `ocr.preprocess.binarize_threshold` | 二値化しきい値 | ⏳ `local_binarization` では OpenCV 非依存の adaptive threshold（blockSize=11, C=2）を使用 |
| `ocr.preprocess.max_pixels` | 前処理後の最大画素数 | ⏳ 未実装。今後の拡張候補 |

### 3.1 利用可能な前処理パターン

`scripts/preprocess_image.py` では、ベンチマーク用に以下のパターンを選択できます。

- `baseline`: 前処理なし
- `sharpen_light`: 軽度シャープニング
- `sharpen_light_upscale_2x`: 2倍アップスケール＋軽度シャープニング（`ocr-worker` デフォルトと同一）
- `contrast_gamma`: コントラスト強調＋ガンマ補正
- `contrast_gamma_sharpen_light`: コントラスト強調＋ガンマ補正＋軽度シャープニング
- `4x_upscale`: 4倍アップスケール
- `4x_upscale_sharpen`: 4倍アップスケール＋軽度シャープニング
- `local_binarization`: 局所的二値化（OpenCV 非依存）
- `local_binarization_sharpen`: 局所的二値化＋軽度シャープニング
- `contrast_strong`: 強コントラスト（enhance 2.0）
- `contrast_strong_4x`: 強コントラスト＋4倍アップスケール

### 3.2 パラメータ選定の指針

- **標準的な電子書籍画像**: `sharpen_light_upscale_2x` がバランス良好（`ocr-worker` のデフォルト前処理と同じ）。
- **薄字や地色ノイズが多い**: `scripts/preprocess_image.py` の `contrast_gamma` または `contrast_gamma_sharpen_light` を試す（ただし `ocr-worker` 自動適用は非推奨）。
- **古い白黒印刷物**: `scripts/preprocess_image.py` の `local_binarization` を試す（ただし OW003007 で文字潰れが確認されているため注意）。
- **極端に小さい文字**: `4x_upscale_sharpen` を試す。OW003007 では baseline より改善したが、ファイルサイズ・処理時間が 3 倍以上になるため注意。

---

## 4. OCR タイムアウト制御

### 4.1 現状の設定

book2pdf では、backend → ocr-worker 間の HTTP リクエストタイムアウトが `backend/app/services/ocr_engine.py` で制御されています。

- デフォルト: `1800` 秒（30 分）
- 環境変数 `OCR_WORKER_REQUEST_TIMEOUT` で上書き可能

```python
timeout_seconds = float(os.environ.get("OCR_WORKER_REQUEST_TIMEOUT", "1800.0"))
```

### 4.2 目安

| 画像サイズ | 推奨 timeout |
|---|---|
| 一般書籍（~5000×8000） | 1800 秒（デフォルト） |
| 超大判書籍（~8000×14000） | 3600 秒以上 |

OCR 処理は画像サイズに応じて処理時間が大きく変わるため、超大判画像を多用する場合は環境変数で延長することを検討してください。

---

## 5. DecompressionBombError / 超大判画像対策

### 5.1 多層アプローチ

reference 側では UI 層・前処理層・OCR エンジン層の 3 層で対応していましたが、book2pdf には UI 層（トリミングプレビュー）が存在しないため、以下 2 層で対応します。

#### 層1: 前処理層（`ocr-worker/app/main.py`）

- `_preprocess_image()` では 2x アップスケール + シャープニングを固定適用。
- 現状、明示的な `max_pixels` による強制縮小や `upscale` clamp は実装されていません。
- 今後、超大判画像でメモリ不足や OCR タイムアウトが頻発する場合は、ここに `max_pixels` 引数を追加することを検討してください。

#### 層2: OCR エンジン層（`ndlocr_cli`）

- ndlocr_cli 内部で Pillow の `DecompressionBombError` が発生する可能性があります。
- 現状、backend 側では `httpx` のリクエストタイムアウトで捕捉されます。
- 前処理スキップによるフォールバックは未実装です。必要に応じて ocr-worker 側で stderr を検出し、前処理 OFF で再試行するロジックを追加できます。

### 5.2 現状の制限

- `ocr-worker` の前処理は **常に 2x アップスケール + 軽度シャープニング** で固定です。
- `max_pixels` による制限はありません。
- `binarize` や `contrast_gamma` などの追加前処理は、backend 経由の通常フローでは適用されません（ベンチマーク用 `scripts/preprocess_image.py` でのみ利用可能）。

---

## 6. 画像サイズ別 推奨設定マトリクス

| 画像サイズ | `ocr-worker` 前処理 | `scripts/preprocess_image.py` の用途 | タイムアウト |
|---|---|---|---|
| 一般書籍（~5000×8000） | 2x upscale + sharpen（デフォルト） | 通常は不要 | 1800 秒 |
| 超大判書籍（~8000×14000） | 2x upscale + sharpen（デフォルト） | 追加前処理の効果検証用 | 3600 秒 |
| 速度優先 | 2x upscale + sharpen（デフォルト） | 前処理なしベースラインとの比較用 | 1800 秒 |
| 白黒印刷物 | 2x upscale + sharpen（デフォルト） | `local_binarization_sharpen` の試行 | 1800 秒 |

---

## 7. トラブルシューティング

| 症状 | 原因の可能性 | 対処 |
|---|---|---|
| OCR がタイムアウトする | 画像サイズが大きい / ページ数が多い | `OCR_WORKER_REQUEST_TIMEOUT` を延長 |
| `DecompressionBombError` | 超大判画像で Pillow の安全上限を超えた | 前処理で `max_pixels` を追加実装するか、入力画像を縮小 |
| 文字認識率が低い | 解像度不足 / コントラスト不足 | `scripts/preprocess_image.py` で `contrast_gamma_sharpen_light` などを試行 |
| 処理時間が長すぎる | 4x アップスケールなど高負荷前処理を使用 | 2x upscale + sharpen に戻す、または前処理 OFF で比較 |

---

## 8. 今後の拡張候補

- `ocr-worker` の前処理を動的に切り替えるパラメータ（`upscale` 倍率、`sharpen` 有無、`binarize` 有無など）の追加
- `max_pixels` による強制縮小の実装
- 前処理失敗時のフォールバック（前処理 OFF で再試行）
- 文字置換辞書（`replacements`）による OCR 後処理
- 章しおり検出（`chapter_bookmarks`）の PDF 生成への統合

---

## 更新履歴

| 日付 | 変更内容 |
|---|---|
| 2026-08-15 | 新規作成。reference/docs の「変換」章を参考に book2pdf 向けに整理 |
| 2026-08-15 | OW003002〜OW003007 の過去レポートを照らし、「取り込み済み」「要検討」を明確に分類 |

---

*本ドキュメントは `reference/docs/config-reference.md` および `CHANGELOG-20250815.md` の記載を参考に作成しました。*
