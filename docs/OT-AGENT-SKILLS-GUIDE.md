# AgentSkills 構成ガイド

## 概要

本ドキュメントは、book2pdf プロジェクトにおける Cline（AI アシスタント）向けルールの **AgentSkills 構成（`.cline/skills/`）** を定義するものです。各スキルの役割、アクティベーション条件、スキル間の連携、および実際の運用方法を記載します。

移行前の単一 `.clinerules` ファイルとの対応関係については、末尾の **付録A** を参照してください。

---

## 1. AgentSkills ディレクトリ構造

```
.clinerules                          # プロジェクト全体の基本方針（最小限）
.cline/
  skills/
    branch-manager/
      SKILL.md                       # ブランチ命名・マージ前承認・マージ済みブランチ追加実装
      references/
        branch-naming.md             # ブランチ命名規則と禁止事項
    code-generator/
      SKILL.md                       # コーディング規約・API整合性確認
    file-modifier/
      SKILL.md                       # 既存ドキュメント更新ルール
    task-manager/
      SKILL.md                       # タスク管理表・作業ログの運用
    test-manager/
      SKILL.md                       # テストデータ配置・検証レポート作成
      references/
        testdata-locations.md        # テストデータ配置の詳細リファレンス
    markdown-table-validator/
      SKILL.md                       # Markdown パイプテーブルのカラム整合性検証
    workflow-runner/
      SKILL.md                       # 4フェーズ実行・スキル選択・承認ゲート
```

### 設計方針

- **`.clinerules`** は、プロジェクト全体の基本方針・承認フロー・モジュール構成のみを保持する最小ファイルとする
- **`.cline/skills/`** には、タスク種別に応じて呼び出す専門スキルを配置する
- **`.clinerules.backup-20260904`** は移行前のオリジナルファイルとして Git 管理対象に残し、参照用とする

---

## 2. スキル一覧

| スキル名 | 定義ファイル | カテゴリ | 主な役割 | アクティベーション条件 |
|---|---|---|---|---|
| `branch-manager` | `.cline/skills/branch-manager/SKILL.md` | ブランチ運用 | ブランチ命名、マージ前承認チェック、マージ済みブランチの追加実装、タスク管理表との照合 | feature ブランチの作成・マージ・再利用時、タスク完了判定時 |
| `code-generator` | `.cline/skills/code-generator/SKILL.md` | コード生成 | 言語別コーディング規約、外部依存コメント、API・関数呼び出しの整合性確認 | Python / TypeScript / Rust のソースコードを書く・レビューする時 |
| `file-modifier` | `.cline/skills/file-modifier/SKILL.md` | ドキュメント更新 | 既存ファイル更新時の `replace_in_file` 適用ルール、末尾追記時のマーカー指定 | `docs/` や `test_cases/` 配下の既存ファイルを更新する時 |
| `task-manager` | `.cline/skills/task-manager/SKILL.md` | タスク管理 | タスクNo体系、粒度、記録場所（`OT-TASKS.md` / `OT-WORK-LOG.md`） | タスク管理表・作業ログを作成・更新する時 |
| `test-manager` | `.cline/skills/test-manager/SKILL.md` | テスト・検証 | テストデータ配置、検証レポート作成、PDF目視確認、README.md インデックス追加 | テストデータ配置、OCR 精度比較、検証レポート作成時 |
| `markdown-table-validator` | `.cline/skills/markdown-table-validator/SKILL.md` | ドキュメント検証 | Markdown パイプテーブルのカラム整合性検証、不整合検出、修正指針提示 | `*-TASKS.md` や `docs/**/*.md` のテーブル編集時、CI/pre-commit 実行時 |
| `workflow-runner` | `.cline/skills/workflow-runner/SKILL.md` | 実行・承認ゲート | タスクの4フェーズ実行、スキル選択、承認ゲート（Gate 1/2/3） | タスク開始〜完了のライフサイクル、スキル選択時 |

---

## 3. 各スキルの詳細

### 3.1 `code-generator`

コード生成・レビュー時に適用される規約群です。

- **技術スタック**: FastAPI + Python / Next.js 15 + TypeScript + Tailwind CSS / Tauri v2 + Rust + React + Vite / ndlocr_cli / PyMuPDF / Docker + Docker Compose
- **コメント規約**: 各関数・クラス・複雑なロジックに JSDoc / docstring / Rust doc comments を必須とする
- **外部依存コメント**: `import` / `use` / `from` 等の宣言文に、そのライブラリ・モジュールの用途と各識別子の役割をコメントする
- **API 整合性確認**: 呼び出し元と受け側の両ファイルを同時に開き、引数名・キー名・型を横並びで確認する

### 3.2 `file-modifier`

既存ドキュメントの更新ルールを定めます。

- 既存ファイルの更新には **必ず `replace_in_file`** を使用する
- 新規ファイル作成時のみ `write_to_file` を使用する
- 末尾追記時は、テーブル区切り行などの既存テキストを `SEARCH` に指定して確実にマッチさせる

### 3.3 `task-manager`

タスク管理の基本単位と記録ルールを定めます。

- タスク No は「モジュール識別子（2文字）＋ ユースケースNo（3桁）＋ 通番（3桁）」の計8文字とする（例：`OW003001`）
  - 識別子: `SY`=System/全体設計・仕様・横断基盤, `BE`=backend, `FE`=frontend, `OW`=ocr-worker, `LA`=localapp, `OT`=横断・その他
- タスク粒度は数時間〜1日以内で完了できる単位とする
- 記録は `<module>/docs/<モジュール識別子>-TASKS.md` と `<module>/docs/<モジュール識別子>-WORK-LOG.md` に行う
- 【計画】欄に記載した事柄は削除せず、実施しない場合は理由を追記する

### 3.4 `test-manager`

テスト・検証系タスクのフローと成果物の扱いを定めます。

- テストデータは `test_cases/benchmarks/` または `test_cases/testdata/<module>/<タスクNo>-<概要>/` に配置する
- レポートは `test_cases/results/ocr-results-<タスクNo>/<report-name>-<タスクNo>.md` 形式で作成する
- レポートには以下を含める:
  - タスク名・実施日・目的
  - 対象データ、OCR エンジン、評価指標
  - 使用データへのパス・実行手順
  - 期待結果・実際の結果
  - 判定（PASS/FAIL）
  - 考察・結論・今後の検討事項
- 付属データ（CSV、テキスト、画像、比較用 PDF 等）はレポートと同じディレクトリに配置する
- PDF 目視確認時は `docker compose cp backend:/data/pdfs/<job_id>.pdf ./test_cases/results/ocr-results-<タスクNo>/<パターン名>/pdfs/` で取得する
- 作成後は必ず `test_cases/README.md` のインデックスと `<module>/docs/<モジュール識別子>-TASKS.md` の【実施結果】にリンクを追加する

詳細な配置ルールは `.cline/skills/test-manager/references/testdata-locations.md` を参照。

### 3.5 `branch-manager`

本スキルは、book2pdf プロジェクトの feature ブランチ運用を一元管理します。

- ブランチ命名規則: `feature/<タスクNo>-<内容の短縮名>`
- マージ前最終承認チェックリスト（絶対遵守）:
  - UAT 明示的合格発言（UAT 要タスクの場合）
  - `<識別子>-TASKS.md` の【タスク完了日付】に日付が記入されていること
  - Gate 3 でのユーザー承認
- マージブロック条件: UAT合格発言なし・完了日付なし・Gate 3未承認
- マージ済みブランチの追加実装フロー:
  - マージ済みブランチが残存していれば再利用、削除済みであれば同じタスク番号で再作成
  - 完了日付が記入済みの場合は追加実装前に削除し、【実施結果】に追記
- タスク管理表との照合義務:
  - git log にマージコミットが存在しても、タスク管理表に完了日付がない場合は「未完了」とする
  - 矛盾発見時はマージ巻き戻しまたはユーザー確認

### 3.6 `markdown-table-validator`

`*-TASKS.md` やプロジェクト内のすべての `*.md` ファイルにおいて、Markdown パイプテーブルのカラム整合性を検証するスキルです。

- **検証対象**: `docs/**/*.md`、`*/docs/**/*.md`、およびプロジェクト内すべての `*.md`
- **検証内容**: 同一セクション内のテーブル行の `|` の数が統一されているかチェック
- **自動化連携**:
  - CI: `.github/workflows/lint-task-md.yml`（PR/push 時）
  - pre-commit: `.pre-commit-config.yaml`（コミット前）
  - 手動: `python scripts/lint-task-md.py`
- **スキル呼び出し元**: `file-modifier`、`task-manager`、`workflow-runner` の Phase 3

### 3.7 `workflow-runner`

タスク全体のライフサイクルと Git 運用を定めます。

#### Phase 1: Pre-work（前処理）
1. `.clinerules` と該当スキルを読み込む
2. `git status` で working tree が clean であることを確認
3. `main` ブランチを最新化（`git checkout main && git pull`）
4. 専用ブランチを作成（`git checkout -b feature/<タスクNo>-<短縮名>`）
5. `OT-TASKS.md` の【計画】に実施手順を記載
6. `OT-WORK-LOG.md` に【実施予定】を作成
7. ユーザーに計画を提示し、承認を取得

#### Phase 2: Execution（処理）
1. 計画に従って実装・調査・検証を実行
2. 節目のフェーズごとにユーザーに状況報告と承認依頼を行う
3. 必要に応じて `docs/OT-CAVEATS.md` や仕様書を更新

#### Phase 3: Post-work（後処理）
1. `OT-TASKS.md` の【実施結果】に実施内容を追記
2. `OT-WORK-LOG.md` の同一エントリに【実施実績】を追記
3. `git add -A && git commit` でコミット（コミットメッセージにタスク番号を含める）
4. `main` ブランチへマージ
5. `OT-TASKS.md` にタスク完了日付を記載
6. ユーザーにタスク完了を報告

---

## 4. スキル間の連携

```
workflow-runner Phase 1
        │
        ├─ タスクが実装主体 → code-generator
        ├─ タスクがドキュメント更新主体 → file-modifier
        ├─ タスクが検証・テスト主体 → test-manager
        └─ 全タスク共通 → task-manager

workflow-runner Phase 2
        │
        ├─ 実装中 → code-generator
        ├─ レポート作成中 → file-modifier + test-manager
        └─ タスク記録更新中 → task-manager

workflow-runner Phase 3
        │
        ├─ コミット・マージ → workflow-runner
        └─ OT-TASKS.md / OT-WORK-LOG.md 更新 → task-manager
```

### 依存関係の補足

- `test-manager` のレポート作成手順内で、既存ファイル更新時は `file-modifier` のルールが適用される
- `code-generator` は `workflow-runner` Phase 1 の「該当スキルを読み込む」ステップでアクティベートされる
- `task-manager` はタスク開始時・完了時の記録更新で必ず参照される

---

## 5. 運用指針

### 5.1 Cline（AI）側の運用

1. タスク開始時は `.clinerules` を読み込み、基本方針と承認フローを確認する
2. `workflow-runner` Phase 1 に従い、事前準備と計画承認を実施する
3. タスク種別に応じて該当スキルを読み込む:
   - コーディング主体 → `code-generator`
   - ドキュメント更新主体 → `file-modifier`
   - テスト・検証主体 → `test-manager`
   - タスク記録主体 → `task-manager`
4. 複数スキルが絡むタスクでは、スキルを横断して参照し、整合性を保つ
5. 各スキルのステップバイステップの手順に従い、省略せずに実施する

### 5.2 ユーザー側の運用

- スキルファイルの更新が必要な場合は、`.clinerules` 更新と同様にユーザー承認が必要である
- 新しいスキルの追加提案は、新規ユースケースの追加と同じフローで行う（ユーザー承認を得てから起票）
- バックアップファイル `.clinerules.backup-20260904` は Git 管理対象として残すため、意図的に削除しないこと

---

## 付録A：新旧対比表

移行前の `.clinerules.backup-20260904`（354 行・16 章）と、新 AgentSkills 構成の対応関係を以下に示します。

| 旧 `.clinerules` 章 | 内容 | 新配置先 | 備考 |
|---|---|---|---|
| **第1章** 基本方針 | `./docs/` 最優先、`old/` 禁止、変更前承認 | `.clinerules` Core Constraints / User Communication | 肯定形で簡潔化 |
| **第2.5章** ドキュメント更新ルール | `replace_in_file` 強制、`write_to_file` 禁止 | `file-modifier/SKILL.md` | スキルとして独立 |
| **第2.6章** テストデータ配置 | `testdata/` 配置、`test-results/` レポート | `test-manager/SKILL.md` + `testdata-locations.md` | 詳細リファレンスを分離 |
| **第2.7章** `test_cases/` ルール | ベンチマーク配置、README.md 更新 | `test-manager/SKILL.md` + `testdata-locations.md` | 命名規則をリファレンス化 |
| **第2.8章** テストデータの取り扱い | 厳格な変更禁止、差分検出時は確認 | `test-manager/SKILL.md` Pre-work / Prohibited Actions | タスク前チェックに統合 |
| **第3章** `docs/` 変更承認フロー | 変更提案 → 承認 → 実施 | `.clinerules` Approval Required | 最小限の記述に集約 |
| **第4章** タスク管理ルール | No体系・粒度・記録場所 | `task-manager/SKILL.md` | 独立スキル化 |
| **第5章** 作業ログ記録 | ※第13章へ統合移動 | `workflow-runner/SKILL.md` Phase 1, 3 | 3フェーズ構造に統合 |
| **第6章** タスク実行手順 | ※第13章へ統合移動 | `workflow-runner/SKILL.md` Phase 1-3 | 3フェーズ構造に統合 |
| **第7章** 技術スタック | Next.js/FastAPI/Tauri 等 | `code-generator/SKILL.md` Step 1 + `.clinerules` Project Context | コーディング時に参照 |
| **第8章** コーディング規約 | JSDoc/docstring 必須、外部依存コメント | `code-generator/SKILL.md` Step 2-3 | 言語別に構造化 |
| **第9章** API・整合性確認 | 双方向チェック、フレームワーク挙動確認 | `code-generator/SKILL.md` Step 4 | コード生成時に統合 |
| **第10章** ユーザー確認方式 | 自由記述形式、toggle to Act mode | `.clinerules` User Communication | 最小限の記述に集約 |
| **第11章** テスト・検証系タスク | 実施手順、レポート作成、PDF確認 | `test-manager/SKILL.md` | 詳細手順をスキル化 |
| **第12章** Git運用ルール | ブランチ命名、コミット前チェック | `branch-manager/SKILL.md` | `branch-manager` スキルとして独立 |
| **第13章** タスク実行3フェーズ | 前処理・処理・後処理 | `workflow-runner/SKILL.md` Phase 1-4 | 4フェーズ構造に最適化 |

### 主要な再構成ポイント

1. **ブランチ運用の独立**: 旧第12章（Git運用）で定義されていたブランチ命名・マージ・追加実装フローを、`branch-manager/SKILL.md` として独立させました。`workflow-runner` は実行フロー・承認ゲートに特化します。
2. **スキル間の依存関係の明確化**: `test-manager` は `workflow-runner` Phase 1 で読み込まれ、`file-modifier` は `test-manager` のレポート更新手順で参照されます。
3. **定義場所の最適化**: プロジェクト共通ポリシーは `.clinerules` に、タスク実行フローは `workflow-runner` に、専門領域ルールは各スキルファイルに分離しました。

---

## 関連ファイル

| ファイル | 内容 |
|---|---|
| `.clinerules` | プロジェクト基本方針・承認フロー・モジュール構成 |
| `.clinerules.backup-20260904` | 移行前のオリジナルファイル（Git管理対象・参照用） |
| `.cline/skills/code-generator/SKILL.md` | コーディング規約・API整合性確認 |
| `.cline/skills/file-modifier/SKILL.md` | 既存ドキュメント更新ルール |
| `.cline/skills/branch-manager/SKILL.md` | ブランチ命名・マージ前承認・追加実装フロー |
| `.cline/skills/branch-manager/references/branch-naming.md` | ブランチ命名規則と禁止事項 |
| `.cline/skills/task-manager/SKILL.md` | タスク管理表・作業ログ運用 |
| `.cline/skills/test-manager/SKILL.md` | テスト実施・検証レポート作成 |
| `.cline/skills/test-manager/references/testdata-locations.md` | テストデータ配置詳細 |
| `.cline/skills/markdown-table-validator/SKILL.md` | Markdown パイプテーブル整合性検証 |
| `.cline/skills/workflow-runner/SKILL.md` | 4フェーズ実行・スキル選択・承認ゲート |

---

## バージョン

- 移行日: 2026-09-04
- 新構成バージョン: 2.0（2026-09-08: `branch-manager` スキルを追加し Git 運用を独立）
- 旧構成バージョン: `.clinerules.backup-20260904`
