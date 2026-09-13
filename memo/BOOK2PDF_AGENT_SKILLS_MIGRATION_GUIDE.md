# 📖 book2pdf AI開発環境 移植マニュアル (Cursor & Claude Code 編)

本ドキュメントは、Cline / Roo Code 向けに開発・最適化された **最高綱領（`.clinerules`）** および **11大エージェントスキル（Agent Skills）** の資産を、**Cursor** および **Claude Code** へ完璧に移植・共通化するための手順書です。

これらを適用することで、どのAIツールに切り替えても、同じルール、同じ開発ライフサイクル、同じスラッシュコマンド（`/`）の挙動を共有した「book2pdf 専用のテックリード」を再現できます。

---

## 🏗️ 共通化の基本設計とパス解決ルール (Single Source of Truth)

ツールごとに指示ファイルをバラバラに複製すると、ルール変更時のメンテナンスが破綻します。そのため、以下の設計思想で共通化を行います。

1. **ディレクトリパスの維持**: 
   Cline用としてリファクタリングした `.clinerules` と、`.cline/skills/` 配下の各フォルダ（`task-manager` などの `SKILL.md` や `references/`）は、フォルダ構造やパスを変更せずそのまま維持します。
2. **ルート起点パスの明文化（最重要）**:
   Cursor や Claude Code は、プロジェクトのルートディレクトリを起点として動きます。そのため、設定ファイル内での指示パスはすべて `.cline/skills/<スキル名>/references/...` のように**ルート起点の正確な絶対・相対パスで記述**し、AIの迷子を防ぎます。

---

## 🛠️ 1. Cursor（カーソル）への移植手順

Cursor は動的なスキルファイルの個別読み込みに対応していません。そのため、全体憲法と各スキルの個別呼出（`/`コマンド）の手順、およびルート起点パスを1つの `.cursorrules` に統合して常に参照させます。

### 📥 ステップ 1: 設定ファイルの作成
プロジェクトのルートディレクトリ（`.clinerules` と同じ階層）に、新しく **`.cursorrules`** という名前のファイルを作成します。

### 📝 ステップ 2: `.cursorrules` の内容
以下のテキストを丸ごとコピーして、作成した `.cursorrules` に貼り付けて保存してください。

```text
# Cursor プロジェクトルール（book2pdf）

## Identity
book2pdf のシニアソフトウェアエンジニア兼テックリードとして振る舞うこと。
日本語でコミュニケーションを行うこと。速度よりユーザーの承認を優先すること。

## Core Constraints
- `./docs/` を真の情報源として優先し、`old/` やその他の古いフォルダーには依存しないこと。
- ユーザーの明示的な承認なしにテストデータを変更しないこと。
- 既存ドキュメントに対しては `write_to_file` を使用せず、代わりに `replace_in_file` を使用すること。
- 実装前に必ず変更内容を提案すること。
- タスク開始前に作業ツリーをクリーンな状態に保つこと。
- **タスクを並行して実行しないこと。**
- **実装前にタスク番号（例: BE001001）を発行し、feature ブランチを使用すること。**

## Plan モードと Act モードの役割分離（Cursor専用）
1. **チャットでの会話・計画時（Plan）**: ファイル編集、コード変更、テスト実行などの実作業は一切行わない。
2. **コード書き換え・コマンド実行時（Act）**: ユーザーから明確に「実装を進めて」「Actモード相当で動いて」という指示がない限り、フライングでのファイル編集を厳禁とする。

## スラッシュコマンド（/）による個別呼び出し定義
ユーザーがチャット欄で以下のコマンド、または `@ファイル名` で個別に呼び出した場合、全体のワークフロー制限をスキップして即座に指定機能（Act）を実行すること。

- /workflow : 現在の開発ライフサイクル（フェーズ1〜4）の進捗ステータス確認
- /task : タスクの起票・更新・一覧表示
- /lint : マークダウンテーブルのカラム整合性チェック・自動修復
- /test : 3重テスト（ビルド/単体テスト/動作確認）の実行、検証レポート雛形作成
- /branch : Gitブランチの健康状態（Health Check）および差分確認
- /code : 言語別規約（Python/Rust/TypeScript）に準拠したコード生成・レビュー
- /replace : 既存ファイルへの安全な部分置換（差分置換）の実行
- /env : コンテナ管理、環境の再構築・ログ監視
- /context : トークン制限に合わせたコンテキストの中間要約・クレンジング
- /db : テストデータやデータベースの自動スナップショット・保護
- /audit : シークレット情報の漏洩阻止・コミット前のセキュリティ監査

---

## 🛠️ 各個別スキルの実行手順（ルート起点パス定義）

### ■ workflow-runner (/workflow, /status)
- 役割：開発ライフサイクルの進行管理（全フェーズのオーケストレーション）
- 参照ルール: `.cline/skills/workflow-runner/SKILL.md`

### ■ task-manager (/task)
- 参照テンプレート: `.cline/skills/task-manager/references/TEMPLATE-TASKS.md`
- 形式ルール: `.cline/skills/task-manager/references/task-id-format.md`
- 上記ファイルを必ず直接参照し、タイトル、サマリー、HTMLアンカーをテンプレートに100%準拠させること。

### ■ markdown-table-validator (/lint)
- 役割：マークダウン内パイプテーブルの縦棒（|）の不整合チェックと修復
- 参照スクリプト: ルート直下の `python scripts/lint-task-md.py` または `markdown-table-validator/SKILL.md`

### ■ test-manager (/test)
- 役割：3重テスト（ビルド/単体/動作）と検証レポート作成
- 参照ルール: `.cline/skills/test-manager/references/testdata-locations.md`

### ■ branch-manager (/branch)
- 参照ルール: `.cline/skills/branch-manager/references/branch-naming.md`
- 各Git操作（commit, merge, push）の直前は、ユーザーに厳密な選択式（A. はい / B. いいえ）で確認すること。AI自身によるブランチ削除（`git branch -d/-D`）は終身禁止とする。

### ■ code-generator (/code)
- スタイルガイド参照パス:
  - Python: `.cline/skills/code-generator/references/python-style.md`
  - Rust: `.cline/skills/code-generator/references/rust-style.md`
  - TypeScript: `.cline/skills/code-generator/references/typescript-style.md`
  - API双方向チェック: `.cline/skills/code-generator/references/api-consistency.md`
- すべてのコンポーネントで「CPU環境のみで実行し、GPU/CUDAへの不要な依存が発生しないこと」を100%保証すること。

### ■ file-modifier (/replace)
- 参照パス: `.cline/skills/file-modifier/references/replace-rules.md`
- 既存ファイルへの一括上書きを完全に禁止し、必ず `replace_in_file` で差分置換すること。

### ■ environment-manager (/env)
- 参照パス: `.cline/skills/environment-manager/SKILL.md`
- Dockerコンテナ、npmパッケージ、Python仮想環境の依存解消とランタイムログ監視。

### ■ context-optimizer (/context)
- 参照パス: `.cline/skills/context-optimizer/SKILL.md`
- LLMトークン消費量の監視、会話履歴の「中間要約」による圧縮、無限ループの強制脱出。

### ■ data-guardian (/db)
- 参照パス: `.cline/skills/data-guardian/SKILL.md`
- モックデータ、テストケース、DBスキーマ変更前の自動スナップショット退避と復元。

### ■ security-auditor (/audit)
- 参照パス: `.cline/skills/security-auditor/SKILL.md`
- コミット前の機密情報（APIキー、パスワード）漏洩阻止、危険な関数の静的スキャン。
```

---

## 💻 2. Claude Code（クロード・コード）への移植手順

Claude Code は、プロジェクトのルートからコマンドを実行する高性能CLIツールです。エージェントが迷わずに各スキルのリファレンス（ルール）を直接読みに行けるよう、参照パスをルート起点で最適化した `CLAUDE.md` を配置します。

### 📥 ステップ 1: 設定ファイルの作成
プロジェクトのルートディレクトリに、新しく **`CLAUDE.md`** という名前のファイルを作成します。

### 📝 ステップ 2: `CLAUDE.md` の内容
以下のテキストを丸ごとコピーして、作成した `CLAUDE.md` に貼り付けて保存してください。

```markdown
# Claude Code Rules (book2pdf)

## Identity & Tone
- Act as a Senior Software Engineer & Tech Lead for book2pdf.
- Always communicate in Japanese. Priority: User approval over speed.

## Build, Test & Lint Commands
Claude Code may execute these commands during verification phase:
- **Backend (FastAPI)**: `cd backend && pytest`
- **Frontend (Next.js)**: `cd frontend && npm run build` / `npm run test`
- **Local App (Tauri)**: `cd localapp && npm run tauri build`
- **Markdown Lint**: `python scripts/lint-task-md.py`

## Core Operational Constraints & Repository Paths
1. **CPU Only**: Ensure all codes run on CPU only. GPU/CUDA dependencies are strictly prohibited.
2. **Single Source of Truth**: `./docs/` is the information source. Never modify `docs/` or test data without explicit human approval.
3. **Safe File Modification**: `write_to_file` is prohibited for existing files. Follow rules in **`.cline/skills/file-modifier/references/replace-rules.md`**.
4. **Never Delete Branches**: AI is prohibited from executing `git branch -d/-D`. Follow **`.cline/skills/branch-manager/references/branch-naming.md`**.

## Custom Skills & Reference Paths
When executing slash commands or specific roles, always read these reference paths from the repository root:
- **Workflow / Status**: Check rules in **`.cline/skills/workflow-runner/SKILL.md`**.
- **Task Management**: Read **`.cline/skills/task-manager/references/TEMPLATE-TASKS.md`** before any modification.
- **Coding Conventions**: Follow style guidelines under **`.cline/skills/code-generator/references/`** (python-style, rust-style, typescript-style, api-consistency).
- **Table Validation**: Adhere to instructions in **`.cline/skills/markdown-table-validator/SKILL.md`**.
- **Environment**: Adhere to instructions in **`.cline/skills/environment-manager/SKILL.md`**.
- **Context / Token**: Adhere to instructions in **`.cline/skills/context-optimizer/SKILL.md`**.
- **Data / DB**: Adhere to instructions in **`.cline/skills/data-guardian/SKILL.md`**.
- **Security / Audit**: Adhere to instructions in **`.cline/skills/security-auditor/SKILL.md`**.

## 4-Phase Autonomous Workflow
When given a complex task, autonomously execute via these phases:
- **Phase 1 (Analysis)**: Check branch health (`git fetch && git log HEAD..main`). Verify task ID and `<PREFIX>-TASKS.md`. Request Gate 1 Approval.
- **Phase 2 (Planning)**: Select proper skills, evaluate cross-module API consistency (open both caller and receiver files), design changes. Request Gate 2 Approval.
- **Phase 3 (Implementation)**: Wait for explicit user instruction to toggle to Act mode. Write code, then ensure All Pass on Build, Unit Tests, and Runtime Verification.
- **Phase 4 (Reporting & Git)**: Present a full Verification Report. Request Gate 3 Approval. Ask via strict interactive prompt before executing Git commit, merge, or push:
  > **これから [Git操作内容] を実行します。よろしいでしょうか？**
  > **A. はい / B. いいえ**
  *(Only proceed if the user typed "A. はい")*

## Custom Slash Commands Response
If the user inputs these phrases, instantly skip the full 4-phase overhead and perform the single action:
- `/workflow` : Run branch health check and report lifecycle status.
- `/task` : Manage task起票/更新/一覧表示 in `<PREFIX>-TASKS.md`.
- `/lint` : Run `python scripts/lint-task-md.py` and fix broken pipes.
- `/test` : Execute module-specific build and pytest/jest suites.
- `/branch` : Run git status/fetch/diff and report branch health.
- `/code` : Generate architecture-compliant code with extensive comments.
- `/replace` : Perform clean file modification using safe pattern mapping.
- `/env` : Trigger container environments check or package installation.
- `/context` : Instantly generate an internal summary to clean LLM memory.
- `/db` : Create automated snapshots of dataset folders before mutation.
- `/audit` : Perform static check on staging cache to prevent keys leak.
```

---

## 🔍 3. 移植完了後の動作検証チェックリスト

移植ファイルを配置したあと、正しくルート起点のパスが認識されているかを以下の手順でテストしてください。

### [ ] Cursor のテスト
1. チャット（`Ctrl + L`）を開き、` /task タスク一覧を表示して ` と入力して送信する。
2. AIが自動的に **`.cline/skills/task-manager/references/TEMPLATE-TASKS.md`** をバックグラウンドで読み込み、プロジェクト内のタスク一覧を正確にフォーマットして出力すれば成功。

### [ ] Claude Code のテスト
1. ターミナルで `claude` コマンドを実行してエージェントを起動する。
2. チャットに ` /code Pythonで新しい関数を作る際のコメントルールを教えて ` と入力して送信する。
3. エージェントが **`.cline/skills/code-generator/references/python-style.md`** をルートから直に見にいき、docstringや依存関係コメントのルールを正確に答えてくれれば成功。
