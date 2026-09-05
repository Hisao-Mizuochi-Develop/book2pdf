# 作業ログ

本ドキュメントは、book2pdf プロジェクトの複数モジュールにまたがる全体横断の作業ログです。

## 2026-09-06 OT002003 `docs/OT-CAVEATS.md` の内容を各モジュール `*-CAVEATS.md` に再配布し、`OT-CAVEATS.md` を削除する

### 目的

`docs/OT-CAVEATS.md` にまとめられていたモジュール横断の注意事項を、各モジュール固有の内容は各モジュールの `*-CAVEATS.md` に、横断的な参照は `docs/SY-CAVEATS.md` に集約し、重複管理を解消する。

### 実施内容

- `docs/OT-CAVEATS.md` に記載されていた backend / localapp / ocr-worker 固有の注意事項を、それぞれ `backend/docs/BE-CAVEATS.md` / `localapp/docs/LA-CAVEATS.md` / `ocr-worker/docs/OW-CAVEATS.md` に移動
- frontend で既存の `frontend/docs/FE-CAVEATS.md` 等でカバーされていた項目は `docs/OT-CAVEATS.md` から削除
- モジュール横断の参照を `docs/SY-CAVEATS.md` に新規作成して集約
- `docs/OT-TASKS.md` に `OT002003` を完了として追記
- `docs/OT-CAVEATS.md` を削除

### 結果

- 各モジュールの `*-CAVEATS.md` が自モジュール固有の注意事項を保持するようになった
- 横断的な注意事項は `docs/SY-CAVEATS.md` に集約された
- `docs/OT-CAVEATS.md` が削除され、重複した注意事項の一元管理が解消された

### コミット

`634f33af` — OT002003: Redistribute OT-CAVEATS.md items into per-module CAVEATS.md

---


## 2026-09-04 .clinerules §8 import/use/from コメント追加（全モジュール横断）

### 目的

`.clinerules` §8 で定義された「外部依存の宣言文（import / use / from 等）に必ずコメントを付ける」ルールを、既存コードベース全体に適用する。

### 対象モジュールとファイル数

| モジュール | ファイル数 | 言語 |
|---|---|---|
| localapp/src-tauri/src/ | 7 | Rust |
| localapp/src/ | 26 | TypeScript/React |
| frontend/src/ | 2 | TypeScript/React |
| ocr-worker/ | 2 | Python |
| **合計** | **37** | — |

### コメントの形式

- **Rust**: `///` doc コメント（`use crate::module;` / `use external_crate::Type;` / `mod submodule;`）
- **TypeScript**: `//` 行コメント（`import { ... } from "module"` / `import type { ... }`）
- **Python**: `#` 行コメント（`import module` / `from module import name`）

各コメントには「標準ライブラリか外部ライブラリかを明示」「モジュールが何を提供するものか」「インポートしている識別子の役割」を記載。

### コミット

`5c1870c` — docs: Add beginner-friendly comments to all import/use/from declarations per .clinerules §8

---

## 2026-08-13 frontend Docker イメージ再構成・docker compose 起動確認

### 目的

frontend コンテナの Next.js 15.1.6 への統一と、docker compose による backend / ocr-worker / frontend の 3 コンテナ起動確認を行う。

### 前提

- frontend の `package.json` / `package-lock.json` / `Dockerfile` は前段階で Next.js 15.1.6 向けに整理済み
- ocr-worker の Dockerfile は PyTorch インストール部分で `--index-url` を使用しており、ビルドエラーが発生していた

### 実施コマンド

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf

# 既存コンテナ・イメージ・ボリュームのクリーンアップ
docker compose down --rmi local --volumes --remove-orphans
docker builder prune -f
docker system prune -f

# frontend dev イメージの単体ビルド
cd frontend
docker build --no-cache --target dev -t book2pdf-frontend-dev .

# コンテナ内の next バージョン確認
docker run --rm -it book2pdf-frontend-dev:latest \
  cat /app/node_modules/next/package.json | grep '"version"'
# -> "version": "15.1.6"

# 単体起動確認
docker run -d --name book2pdf-frontend -p 3000:3000 book2pdf-frontend-dev:latest

# 起動ログ確認
docker logs --tail 50 book2pdf-frontend
# -> ▲ Next.js 15.1.6
# -> Ready in 1487ms

# ヘルスチェック
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# -> 200
```

### ocr-worker Dockerfile 修正

`ocr-worker/Dockerfile` の PyTorch インストール部分を以下のように修正した。

修正前：
```dockerfile
RUN pip install --no-cache-dir \
    torch==2.0.1+cpu \
    torchvision==0.15.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu
```

修正後：
```dockerfile
RUN pip install --upgrade "pip<24.1" setuptools wheel \
    && pip install --no-cache-dir \
        torch==2.0.1+cpu \
        torchvision==0.15.2+cpu \
        --extra-index-url https://download.pytorch.org/whl/cpu
```

修正理由：
- `--index-url` を使うと PyTorch 以外の依存パッケージも PyTorch の index から解決しようとし、メタデータ名の大文字小文字不一致で失敗する
- pip 24.1 以降では `pytorch-lightning==1.6.5` のメタデータ（`torch (>=1.8.*)`）が拒否されるため、`pip<24.1` を使用

### docker compose 起動確認

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
docker compose up -d --build
```

結果：
- `book2pdf-frontend`（Next.js 15.1.6）が `health: starting` で起動
- `book2pdf-backend` が起動
- `book2pdf-ocr-worker` が起動

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/jobs/
# -> 405 （POST 専用のため OK）
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/docs
# -> 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# -> 200
```

### テスト用 ZIP 作成

```bash
cd /Users/hisao/Documents/work4/sakura/book2pdf
mkdir -p test_zips
cd test_zips
zip -j sample_002-004.zip \
  ../sample-png/AI\ ・LLMの実務でつかえるRAG精度改善_trimmed/002.png \
  ../sample-png/AI\ ・LLMの実務でつかえるRAG精度改善_trimmed/003.png \
  ../sample-png/AI\ ・LLMの実務でつかえるRAG精度改善_trimmed/004.png
```

### 結果

- frontend の Docker イメージが Next.js 15.1.6 で正常に起動することを確認
- docker compose で 3 コンテナが同時に起動することを確認
- `http://localhost:3000` にブラウザでアクセス可能
- ZIP アップロード API は `Content-Type: application/zip` を明示すると正常に動作
- OCR 実行 API は ocr-worker 内部で 500 エラーが発生（詳細なトレースバックは取得中）

### 注意事項

- ocr-worker の 500 エラーは、モデルロードまでは成功しているが、その後の推論処理で失敗している可能性がある
- 詳細なエラーを取得するためには、ocr-worker コンテナ内で直接デバッグが必要
- 本件は `backend/docs/BE-WORK-LOG.md` および `ocr-worker/docs/OW-WORK-LOG.md` でも追記予定

### 関連タスク

- frontend タスク：Next.js 15.1.6 への Docker 再構成（完了）
- backend タスク：ocr-worker 500 エラーの原因調査（未完了）
- 全体タスク：frontend から ZIP アップロード・PDF ダウンロードの統合検証（未完了）

## 2026-09-03 OT003001 進捗通知のポーリング方式仕様策定と localapp リトライ実装

### 目的

localapp で発生していた「ジョブ状態の取得に失敗しました」というポーリングエラーを、per-request タイムアウトと指数関数的バックオフによるリトライで解消し、SSE / HTTP ポーリングの進捗通知仕様をプロジェクト全体で統一する。

### 前提

- `docs/progress-notification-polling-design.md` と `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` が別々に存在していた
- localapp のポーリングは 1 秒間隔で `GET /api/jobs/{job_id}` を呼び出すのみで、タイムアウト・リトライが未実装だった
- 進捗ペイロードに `progress_percent` と `stage`/`message`/`current`/`total` が混在していた

### 実施内容

- `docs/progress-notification-polling-design.md` を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に統合し、前者は削除した
- `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止した
- ポーリングプロトコルを文書化した
  - 1 リクエストあたり 10 秒タイムアウト
  - 接続失敗時は最大 3 回まで 1 秒 / 2 秒 / 4 秒の指数関数的バックオフでリトライ
  - リトライ前に「ジョブ状態の取得を再試行します」の進捗メッセージを UI に通知
- `docs/README.md` / `docs/SY-WEB-OCR-SYSTEM-PLAN.md` / `docs/OT-CAVEATS.md` / `docs/OT-TASKS.md` に進捗通知仕様と OT003001 の計画を反映した
- `localapp/src-tauri/src/commands/backend_api/backend_api_impl.rs` のポーリング処理に `poll_job_status` ヘルパーを導入し、タイムアウト・リトライ・バックオフを実装した

### 結果

- 進捗通知仕様書 [`docs/SY-PROGRESS-NOTIFICATION-SPEC.md`](SY-PROGRESS-NOTIFICATION-SPEC.md) が整備された
- localapp のポーリングが一過性の接続エラーに対して耐性を持つようになった
- `cargo check --tests` と `cargo test backend_api_impl -- --nocapture` にてコンパイル・テストを確認した

### 関連タスク

- OT003001 進捗通知のポーリング方式仕様策定と localapp リトライ実装（完了）
