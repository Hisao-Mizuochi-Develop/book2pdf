# test_cases — テストデータ・検証結果インデックス

本ディレクトリは、book2pdf プロジェクト全体で共有するベンチマーク・評価用データおよび OCR 検証結果レポートを一元管理する場所です。

個別のタスク用テストデータは `test_cases/testdata/<module>/` に配置し、**プロジェクト全体で共有する比較評価データは本ディレクトリに配置**します。

---

## フォルダ構成

```
test_cases/
├── README.md                      ← 本ファイル
├── benchmarks/                    ← ベンチマーク用画像 ZIP ファイル群
├── results/                       ← OCR 精度比較・検証レポート（003002〜003007）
├── testdata/                      ← モジュール別・横断的なテストデータ
│   ├── backend/                   ← backend 用テストデータ
│   ├── frontend/                  ← frontend 用テストデータ
│   ├── integration/               ← 結合・横断テストデータ
│   ├── localapp/                  ← localapp 用テストデータ
│   ├── ocr-worker/                ← ocr-worker 用テストデータ
│   └── performance/               ← 性能テストデータ
└── AI ・LLMの実務でつかえるRAG精度改善/  ← テスト対象書籍のキャプチャ画像

> **モジュール固有のテスト結果について**:
> 以下のレポートは各モジュールの `test-results/` に移動しています。
> - `ocr-results-003008/` → [`../ocr-worker/test-results/ocr-results-003008/`](../ocr-worker/test-results/ocr-results-003008/)
> - `ocr-results-004003/` → [`../backend/test-results/benchmark-004003/`](../backend/test-results/benchmark-004003/)
```

---

## 1. benchmarks/ — ベンチマーク用画像セット

各タスクの検証で使用した画像 ZIP ファイルです。主に `AI ・LLMの実務でつかえるRAG精度改善` 書籍のトリミング済みページをアーカイブしたものです。

| ファイル名 | タスク | 内容 |
|---|---|---|
| `benchmark-ocr-003002.zip` | [003002](../backend/docs/tasks.md) | OCR 認識精度再測定用ベースライン（3ページ） |
| `benchmark-ocr-003003-sharpen.zip` | [003003](../ocr-worker/docs/tasks.md) | シャープニング前処理のみ適用 |
| `benchmark-ocr-003003-sharpen-upscale.zip` | 003003 | シャープニング + 2倍アップスケール |
| `benchmark-ocr-003003-contrast-gamma.zip` | 003003 | コントラスト強調 + ガンマ補正 |
| `benchmark-ocr-003003-contrast-gamma-sharpen.zip` | 003003 | コントラスト強調 + ガンマ補正 + シャープニング |
| `benchmark-ocr-003007.zip` | [003007](../ocr-worker/docs/tasks.md) | 追加前処理効果検証用ベースライン |
| `benchmark-ocr-003007-baseline-2x.zip` | 003007 | 2倍アップスケールベースライン |
| `benchmark-ocr-003007-4x-upscale.zip` | 003007 | 4倍アップスケール |
| `benchmark-ocr-003007-4x-upscale-sharpen.zip` | 003007 | 4倍アップスケール + シャープニング |
| `benchmark-ocr-003007-contrast-strong.zip` | 003007 | 強コントラスト強調 |
| `benchmark-ocr-003007-contrast-strong-4x.zip` | 003007 | 強コントラスト強調 + 4倍アップスケール |
| `benchmark-ocr-003007-local-binarization.zip` | 003007 | 局所二値化 |
| `benchmark-ocr-003007-local-binarization-sharpen.zip` | 003007 | 局所二値化 + シャープニング |

---

## 2. results/ — OCR 検証結果レポート

各タスクで実施した OCR 精度比較・検証レポートです。

| レポートパス | タスク | 実施日 | 評価内容 | 結論の概要 |
|---|---|---|---|---|
| [ocr-results-003002/ocr-accuracy-report-003002.md](results/ocr-results-003002/ocr-accuracy-report-003002.md) | [003002](../backend/docs/tasks.md) | 2026-08-13 | OCR 認識精度再測定（ベースライン） | ベースライン精度の測定 |
| [ocr-results-003003/preprocess-comparison-report-003003.md](results/ocr-results-003003/preprocess-comparison-report-003003.md) | [003003](../ocr-worker/docs/tasks.md) | 2026-08-13 | 入力画像前処理の効果検証 | `sharpen_light_upscale_2x` が最も効果的 |
| [ocr-results-003004/config-comparison-report-003004.md](results/ocr-results-003004/config-comparison-report-003004.md) | [003004](../ocr-worker/docs/tasks.md) | 2026-08-13 | config.yml パラメータ調整効果検証 | パラメータ調整単体では効果限定的 |
| [ocr-results-003005/score-thr-comparison-report-003005.md](results/ocr-results-003005/score-thr-comparison-report-003005.md) | [003005](../ocr-worker/docs/tasks.md) | 2026-08-14 | score_thr 比較（前処理 ON） | `score_thr=0.2` が最適と判断 |
| [ocr-results-003005/config-comparison-report-003005.md](results/ocr-results-003005/config-comparison-report-003005.md) | 003005 | 2026-08-14 | score_thr 修正後の再検証 | `score_thr=0.2` + `sharpen_light_upscale_2x` の組み合わせで精度向上を確認 |
| [ocr-results-003006/preprocess-integration-report-003006.md](results/ocr-results-003006/preprocess-integration-report-003006.md) | [003006](../ocr-worker/docs/tasks.md) | 2026-08-14 | `sharpen_light_upscale_2x` の ocr-worker 組み込み検証 | ocr-worker 自動前処理として採用決定 |
| [ocr-results-003007/additional-preprocess-report-003007.md](results/ocr-results-003007/additional-preprocess-report-003007.md) | [003007](../ocr-worker/docs/tasks.md) | 2026-09-01 | 追加前処理効果検証 | `sharpen_light_upscale_2x` を超える前処理は見つからず、現状の方式を維持 |

---

## 3. ocr-results-003008/ — 適応的前処理検討レポート（ocr-worker/test-results へ移動）

| レポートパス | タスク | 実施日 | 評価内容 | 結論 |
|---|---|---|---|---|
| [adaptive-preprocess-report-003008.md](../ocr-worker/test-results/ocr-results-003008/adaptive-preprocess-report-003008.md) | [003008](../ocr-worker/docs/tasks.md) | 2026-09-01 | ページタイプ別（表紙/目次/本文）に最適な前処理パラメータを切り替える方式の検討 | 実装コストに対する効果が不明確。OCR 後処理や UI 手動補正を優先し、本対応は**保留** |

**検討した方式**:
1. ページ分類ベース（表紙/目次/本文の自動判定）
2. 認識置信度ベース（低い箇所にだけ強力な前処理を適用）
3. レイアウト認識結果ベース（文字領域の混雑度に応じて切り替え）

---

## 4. benchmark-004003/ — OCR 処理性能計測レポート（backend/test-results へ移動）

> **注意**: 本レポートのタスク 004003 は backend の「OCR 処理性能計測の実施」であり、localapp の「余白自動検出（004003）」とは別タスクです。

| レポートパス | タスク | 実施日 | 評価内容 | 結論 |
|---|---|---|---|---|
| [performance-test-report-004003.md](../backend/test-results/benchmark-004003/performance-test-report-004003.md) | [004003](../backend/docs/tasks.md) | 2026-09-01 | ndlocr_cli の CPU 実行時の処理時間計測 | 3 ページで OCR 全体時間 **396秒**（1ページあたり平均 **126秒**）。HTTP タイムアウト設定に注意が必要 |

**測定対象工程**:
- Docker Compose 起動時間
- ジョブ作成・ZIP アップロード時間
- OCR 処理時間（1ページあたり）
- ZIP 解凍・PDF 生成時間

**付属データ**:
- `results-004003.csv` — 数値データ（CSV 形式）
- `results-004003.txt` — 数値データ（テキスト形式）

---

## 5. AI ・LLMの実務でつかえるRAG精度改善/ — テスト対象書籍データ

実際の OCR 検証に使用した書籍「AI・LLMの実務でつかえるRAG精度改善」のキャプチャ画像です。

```
AI ・LLMの実務でつかえるRAG精度改善/
├── AI ・LLMの実務でつかえるRAG精度改善_trimmed/   ← トリミング済みページ画像
├── ocr-evaluation.md                              ← OCR 評価対象ページのメタデータ
└── raw/                                           ← 生キャプチャ画像（未トリミング）
```

**使用用途**:
- OCR 精度比較のテストデータ
- 前処理効果検証の入力画像
- 性能計測のベンチマーク

---

## レポートの読み方

各レポートは以下の共通構成で記載されています：

1. **概要** — タスク No、実施日、目的、評価指標
2. **測定条件** — 環境、パラメータ、使用データ
3. **結果** — 定量的データ（テーブル・グラフ）
4. **考察** — なぜその結果になったかの分析
5. **結論** — 導出された判断・今後のアクション
6. **今後の検討事項** — 未解決の課題・次のステップ

---

## 関連ドキュメント

- [統合テストガイド](../docs/integration-test-guide.md) — フルフロー手順
- [backend/docs/tasks.md](../backend/docs/tasks.md) — backend タスク管理表
- [ocr-worker/docs/tasks.md](../ocr-worker/docs/tasks.md) — ocr-worker タスク管理表
- [localapp/docs/tasks.md](../localapp/docs/tasks.md) — localapp タスク管理表

---

*最終更新: 2026-09-04*
