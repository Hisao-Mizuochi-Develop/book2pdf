# testdata-locations

## 各モジュールのテストデータ配置

| 用途 | 配置先 | 例 |
|---|---|---|
| モジュール固有 e2e データ | `<module>/testdata/<タスクNo>-<概要>/` | `localapp/testdata/003006-backend-ocr-test/` |
| モジュール固有 結果レポート | `<module>/test-results/<タスクNo>-<概要>/README.md` | `localapp/test-results/003006-backend-ocr-test/README.md` |
| プロジェクト全体共有 | `test_cases/` | `test_cases/benchmarks/`, `test_cases/ocr-results-003003/` |
| 検証結果アーカイブ | `test_cases/results/` | `test_cases/results/ocr-results-003003/` |
| 書籍単位テストデータ | `test_cases/<書籍名>/` | `test_cases/sample-book/` |

## ベンチマーク ZIP 命名

- `test_cases/benchmarks/benchmark-ocr-<タスクNo>-<条件>.zip`

## 検証レポート命名

- `<レポート種別>-report-<タスクNo>.md`
- 例: `preprocess-comparison-report-003003.md`

## Git 管理

- `testdata/` 配下のファイルは Git 管理の対象とする
- `.gitignore` で `testdata/` を除外しないこと
