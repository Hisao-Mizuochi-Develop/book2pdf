# コーディング規約

本ドキュメントは、book2pdf プロジェクトで使用するプログラミング言語のコーディング規約を定めたものです。

## 1. 対象言語と module

| 言語 | 使用 module |
|---|---|
| Python | `backend/` / `ocr-worker/` |
| TypeScript | `frontend/` / `localapp/` |
| Rust | `localapp/` |

各言語の規約は、モダンなツールチェーンとベストプラクティスに基づいて定義します。本規約に従ってコードを記述し、レビュー時の指摘事項とします。

## 2. 共通事項

### 2.1 基本原則

- **DRY（Don't Repeat Yourself）**: 同じロジックの重複を避け、共通化や抽象化を検討する
- **KISS（Keep It Simple, Stupid）**: 過度にスマートなコードより、読みやすいシンプルなコードを優先する
- **YAGNI（You Aren't Gonna Need It）**: 必要になるまで過剰な一般化や抽象化を行わない
- **可読性を最優先**: 命名、分割、コメントは、半年後の自分や他の開発者が理解できることを目指す

### 2.2 フォーマット・リント

- 各言語の標準的なフォーマッタとリンタを使用する
- CI または pre-commit hook で自動チェックする
- 手動での整形は避け、ツールに任せる

### 2.3 命名規則の基本

- 意味のある名前を付ける。`tmp`、`data`、`info` などの曖昧な命名は避ける
- 略語は一貫性を保って使用する（例：`id` は可、`ID` も可だが混在しない）
- 真偽値を表す変数・関数は `is_xxx`、`has_xxx`、`should_xxx` などの接頭辞を使う

### 2.4 コメント

- **なぜ（Why）を書く**: コードが何をしているかは読めばわかるようにし、背景や意図をコメントする
- **API は doc comment を必須**: 公開関数・クラス・型には、入力・出力・副作用の概要を記載する
- **処理や変数に対して適切なコメントを記載する**: 学習を前提とするため、変数の意味や処理の流れも含めて初学者が理解しやすいように説明する
- **コメント行以外のプログラムの各行には原則としてコメントを記載する**: import 文、変数宣言、制御構文、関数呼び出し、演算など、初学者が読むことを前提として「何をしているか」「なぜそうしているか」を説明する。ただし、極めて短い処理で意図が明確な場合は、1行上にブロックコメントを記載してもよい
- **import 行には必ず 1行ごとにコメントを記載する**: `import` 文および `from ... import ...` 文を含むすべての import 行に、そのモジュールやクラスを「何のために」「なぜ必要か」を初学者にもわかるように説明する。標準ライブラリ・サードパーティ・自前モジュールの区別がつくようにする
- **初学者が平易に可読できるコードを心がける**: 短絡的な書き方や高度なイディオムは避け、基本的で読みやすい構文・命名を優先する
- TODO / FIXME はタスク No を付与し、放置しない

### 2.5 テスト

- ビジネスロジックはユニットテストを書く
- 外部依存が多い処理は統合テストを書く
- テスト名は「何を・どの条件で・どうなるか」がわかるようにする

### 2.6 バージョン管理

- コミットは論理的な単位に分ける
- コミットメッセージは日本語または英語のいずれかを統一する（本プロジェクトでは日本語を推奨）
- 大きな変更は PR / レビューを経由する

## 3. Python

### 3.1 フォーマット・リント

- **フォーマッタ**: [Black](https://github.com/psf/black) または [Ruff format](https://docs.astral.sh/ruff/)
- **リンタ**: [Ruff](https://docs.astral.sh/ruff/)
- **型チェッカー**: [mypy](https://mypy.readthedocs.io/) または [pyright](https://github.com/microsoft/pyright)
- 設定は `pyproject.toml` に集約する

### 3.2 型ヒント

- すべての公開関数・メソッドには型ヒントを付ける
- Python 3.10+ の新記法を使用する

```python
# Good
# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# ユーザー情報を表すモデルを自前のモジュールから読み込みます
from app.models.user import User

# 指定された user_id に一致するユーザーを検索します
# 見つからない場合は None を返します
def find_user(user_id: str) -> User | None:
    ...

# 文字列のリストを受け取り、各要素の長さを辞書として返します
def process(items: list[str]) -> dict[str, int]:
    ...

# Bad
# 型ヒントがなく、引数や戻り値の型がわかりません
def find_user(user_id):
    ...
```

### 3.3 非同期処理

- I/O 待ちが発生する処理は原則 `async` / `await` を使用する
- FastAPI のエンドポイントは非同期関数で実装する
- ブロッキング処理（OCR など）を呼び出す場合は、`asyncio.to_thread` や別スレッド / ワーカーで実行する

### 3.4 FastAPI / Pydantic

- リクエスト / レスポンスは Pydantic モデルで定義する
- 依存性注入（Dependency Injection）を活用し、テスタビリティを高める
- HTTPException には適切な HTTP ステータスコードを設定する

### 3.5 エラーハンドリング

- `except Exception:` は避け、具体的な例外をキャッチする
- ライブラリ固有の例外は必要に応じてラップし、呼び出し元が扱いやすい形にする
- ログには `logging` または `structlog` を使用し、例外情報を含める

### 3.6 ファイル・パス操作

- パス操作は `pathlib.Path` を使用する
- 文字列結合より f-string を使用する

### 3.7 ドキュメンテーション

- 公開 API には Google Style または NumPy Style の docstring を使用する
- 内部関数でも複雑な処理には docstring またはコメントを付ける

## 4. TypeScript

### 4.1 コンパイラ・ツール

- **TypeScript**: `strict: true` を有効にする
- **リンタ**: [ESLint](https://eslint.org/) + [typescript-eslint](https://typescript-eslint.io/)
- **フォーマッタ**: [Prettier](https://prettier.io/)
- 設定は `tsconfig.json` / `eslint.config.*` / `.prettierrc` に集約する

### 4.2 型安全性

- `any` は禁止に近い扱いとする。どうしても必要な場合は理由をコメントする
- 不明な型は `unknown` を使用し、型ガードまたは Zod などで絞り込む
- 判別的 union（Discriminated Union）を活用する

```typescript
// Good
type Result =
  | { status: "ok"; data: User }
  | { status: "error"; message: string };

function handle(result: Result) {
  switch (result.status) {
    case "ok":
      return result.data;
    case "error":
      throw new Error(result.message);
    default:
      const _exhaustive: never = result;
      return _exhaustive;
  }
}
```

### 4.3 命名規則

| 対象 | 規則 |
|---|---|
| 変数・関数・プロパティ | `camelCase` |
| 型・インターフェース・クラス・React コンポーネント | `PascalCase` |
| 定数 | `SCREAMING_SNAKE_CASE` |
| ファイル名 | `kebab-case.ts`（コンポーネントは `PascalCase.tsx` も可） |

### 4.4 React

- コンポーネントは関数コンポーネントで記述する
- Hooks のルール（ループ・条件分岐内で呼び出さないなど）を守る
- Next.js App Router では、可能な限り Server Components を使用する
- Client Components が必要な場合はファイル先頭に `"use client"` を明示する

### 4.5 Next.js App Router

- データ取得は Server Components で行うことを基本とする
- Route Handlers は `app/api/.../route.ts` に配置し、HTTP メソッドごとにエクスポートする
- Server Actions を使用する場合は、機密情報をクライアントに露出しないよう注意する

### 4.6 null / undefined 扱い

- オプショナルチェーン（`?.`）と nullish coalescing（`??`）を適切に使用する
- `||` による falsy 値の誤判定を避ける

### 4.7 エラーハンドリング

- API エラーは Result 型または try-catch で統一的に扱う
- ユーザーへのエラーメッセージは日本語で表示し、内部詳細は隠蔽する

## 5. Rust

### 5.1 フォーマット・リント

- **フォーマッタ**: [rustfmt](https://github.com/rust-lang/rustfmt)
- **リンタ**: [clippy](https://github.com/rust-lang/rust-clippy)
- CI で `cargo fmt --check` と `cargo clippy -- -D warnings` を実行する

### 5.2 命名規則

| 対象 | 規則 |
|---|---|
| 変数・関数・モジュール | `snake_case` |
| 定数・静的変数 | `SCREAMING_SNAKE_CASE` |
| 型・トレイト・列挙型 | `PascalCase` |
| ライフタイム | `'a`, `'static` など短い名前 |

### 5.3 所有権・借用・ライフタイム

- 不必要な `.clone()` は避け、借用を活用する
- 所有権が複雑になる場合は、`Rc` / `Arc` や `Cow` を検討する
- ライフタイム注釈は、コンパイラが推論できない場合のみ記述する

### 5.4 エラーハンドリング

- 回復可能なエラーは `Result` で表現する
- エラー型は `thiserror` で定義し、コンテキストを持たせる
- アプリケーション層では `anyhow` を使ってもよい
- `unwrap()` / `expect()` は、本当に panic してよい場所のみ使用する

```rust
// Good
let config = fs::read_to_string(path)
    .with_context(|| format!("failed to read config: {}", path))?;

// Bad
let config = fs::read_to_string(path).unwrap();
```

### 5.5 非同期処理

- 非同期ランタイムは [tokio](https://tokio.rs/) を使用する
- I/O 処理は原則非同期で実装する
- `spawn` する際は JoinHandle の管理を徹底する

### 5.6 Tauri

- コマンド関数は `#[tauri::command]` で定義する
- 状態共有には `tauri::State` を使用し、グローバル変数は避ける
- JavaScript 側に返すエラーは `Result<T, String>` などシリアライズ可能な形にする
- 重い処理（OCR など）は非同期コマンドまたは別スレッドで実行する

### 5.7 unsafe

- `unsafe` は原則使用しない
- どうしても必要な場合は、安全性の根拠をコメントし、範囲を最小限にする

## 6. まとめ

本規約は、保守性・可読性・安全性を高めるために定めたものです。ツールによる自動チェックを前提としつつ、最終的には人間が読んで理解できるコードを心がけてください。規約に反するケースが生じた場合は、理由をコメントし、必要に応じて本ドキュメントを更新してください。
