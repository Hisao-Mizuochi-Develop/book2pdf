# testdata-locations

## 各モジュールのテストデータ配置

| 用途 | 配置先 | 例 |
|---|---|---|
| モジュール固有 e2e データ | `test_cases/testdata/<module>/<タスクNo>-<概要>/` | `test_cases/testdata/localapp/003006-backend-ocr-test/` |
| モジュール固有 結果レポート | `<module>/test-results/<タスクNo>-<概要>/README.md` | `localapp/test-results/003006-backend-ocr-test/README.md` |
| プロジェクト全体共有 | `test_cases/benchmarks/` 等 | `test_cases/benchmarks/`, `test_cases/ocr-results-003003/` |
| 検証結果アーカイブ | `test_cases/results/` | `test_cases/results/ocr-results-003003/` |
| 書籍単位テストデータ | `test_cases/<書籍名>/` | `test_cases/sample-book/` |
| 横断・結合テストデータ | `test_cases/testdata/integration/` | `test_cases/testdata/integration/` |
| 性能テストデータ | `test_cases/testdata/performance/` | `test_cases/testdata/performance/` |

## ベンチマーク ZIP 命名

- `test_cases/benchmarks/benchmark-ocr-<タスクNo>-<条件>.zip`

## 検証レポート命名

- `<レポート種別>-report-<タスクNo>.md`
- 例: `preprocess-comparison-report-003003.md`

## Git 管理

- `test_cases/testdata/` 配下のファイルは Git 管理の対象とする
- `.gitignore` で `test_cases/testdata/` を除外しないこと
