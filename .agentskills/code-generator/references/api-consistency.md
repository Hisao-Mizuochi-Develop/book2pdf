# api-consistency

## 確認原則

API、関数、IPC コマンドなど、呼び出し元と受け側がある場合は**必ず双方向の整合性**を確認する。

## 確認項目

1. 呼び出し元でどのキー名・引数名で送信しているか
2. 受け側でどの引数名で受け取っているか
3. フレームワークの自動変換挙動（camelCase ↔ snake_case など）を確認

## 実施方法

- 呼び出し元と受け側の両ファイルを同時に開く
- 引数名・キー名・型の整合性を横並びで確認

## 代表的なフレームワーク

| フレームワーク | 変換挙動 | 注意点 |
|---|---|---|
| Tauri invoke | Rust snake_case ↔ JS camelCase（自動） | Rust 側で `rename_all` を使う場合は明示的に確認 |
| FastAPI + Pydantic | snake_case（受け側） | JS 側が camelCase の場合はマッピングを確認 |
| axios | そのまま送信 | 受け側の期待キー名に合わせる |

## 禁止事項

- コード片だけを見て「Rust 側が snake_case なので JS 側も snake_case に合わせる」などの単純推論に基づく修正
