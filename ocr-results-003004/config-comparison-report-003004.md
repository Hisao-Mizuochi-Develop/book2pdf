# 003004 config.yml パラメータ調整効果検証 レポート

## 概要

- タスク: 003004「config.yml パラメータ調整の効果検証」
- 実施日: 2026-08-13
- 対象データ: `benchmark-ocr-003003-sharpen-upscale.zip`（002.png, 003.png, 004.png）
  ※003003 で最も効果的だった `sharpen_light_upscale_2x` 適用済み画像（1328×1884）
- OCR エンジン: ndlocr_cli（CPU 実行）
- 評価指標: 「〓」出現数、ファイル差分、目視確認

## 比較パターン

| パターン | 調整内容 | config.yml 変更 |
|---|---|---|
| baseline | 003003 の `sharpen_light_upscale_2x` 結果を流用 | なし（score_thr: 0.3） |
| pattern A | layout_extraction.score_thr 下调 | score_thr: 0.2 |
| pattern B | layout_extraction.score_thr さらに下调 | score_thr: 0.1 |
| pattern C | score_thr 0.2 + 柱/ノンブル/ルビ無効化 | score_thr: 0.2, 柱: False, ノンブル: False, ルビ: False |

## 定量的結果

### 「〓」出現数

| パターン | 「〓」出現数 | 002_main | 003_main | 004_main |
|---|---|---|---|---|
| **baseline** | **3** | 2 | 1 | 0 |
| **pattern A** | **3** | 2 | 1 | 0 |
| **pattern B** | **3** | 2 | 1 | 0 |
| **pattern C** | **3** | 2 | 1 | 0 |

### ファイル差分

全パターンの `_main.txt`、`_ruby.txt`、`.xml` を baseline と `diff` で比較した結果：

| パターン | 002_main | 003_main | 004_main |
|---|---|---|---|
| pattern A | **完全一致** | **完全一致** | **完全一致** |
| pattern B | **完全一致** | **完全一致** | **完全一致** |
| pattern C | **完全一致** | **完全一致** | **完全一致** |

## 考察

### config.yml のパラメータが効果を持たなかった理由（推測）

1. **ハードコードされた閾値**: ndlocr_cli のソースコード内部で `score_thr` が固定値でハードコードされており、config.yml の値が参照されていない可能性がある
2. **別の設定ファイルが優先**: モデルの学習済み重みや inference pipeline が独自のパラメータを持っており、config.yml の値が無視されている可能性がある
3. **該当セクションの未使用**: `layout_extraction.score_thr` は領域検出の閾値だが、使用しているモデルの推論フローではこのパラメータが参照されていない可能性がある
4. **additional_elements の影響範囲**: `line_ocr.additional_elements` の柱/ノンブル/ルビ設定は、後処理の出力選択に影響する可能性があるが、`_main.txt` には既に選別済みのテキストが含まれており差分が出ない

### 前処理（003003）との対比

- 003003 の `sharpen_light_upscale_2x` は「〓」を 5→3 に減少させ、誤認識を大幅に改善した
- 003004 の config.yml 調整は**すべてのパターンでベースラインと同一の結果**となり、**改善効果なし**

## 結論

**config.yml の `layout_extraction.score_thr` および `line_ocr.additional_elements` の調整は、少なくとも本テストデータセット（sharpen_light_upscale_2x 適用済み画像）においては、OCR 精度に有意な影響を与えなかった。**

前処理（画像アップスケール + シャープニング）による精度向上が確認された一方、config.yml のパラメータ調整は限定的な効果しか期待できない、または効果を確認できなかった。

## 今後の検討事項

- ndlocr_cli のソースコード（`cli/core/inference.py` や各 submodule）を確認し、config.yml の値が実際にどこで参照されているかを追跡する必要がある
- ハードコードされた閾値があれば、それを外部設定可能にするパッチの検討
- より高解像度のテスト画像での追加検証
- 別のパラメータ（`page_deskew` の傾き閾値、`line_order` など）の効果検証
