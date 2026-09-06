# branch-naming

## ブランチ命名規則

```
feature/<タスクNo>-<内容の短縮名>
```

## 例

- `feature/OT001001-scaffold`
- `feature/OT002001-screenshot-research`

## ブランチ運用手順

1. `git checkout main && git pull`
2. `git checkout -b feature/<タスクNo>-<xxx>`
3. 作業実施
4. `git add -A && git commit -m "<タスクNo>: <内容>"`
5. `git checkout main && git merge feature/<タスクNo>-<xxx>`

## コミット前必須チェック

- ユーザーによる動作テスト実施
- ユーザーからの「合格」明示的判定
- `<モジュール識別子>-TASKS.md` / `<モジュール識別子>-WORK-LOG.md` 更新内容のユーザー承認

## 禁止事項（Prohibited Operations）

- 既存の feature ブランチを強制上書き・再作成しない。同一タスク番号のブランチが存在する場合は既存ブランチを再利用するか、不要であれば削除してから新規作成する。
- 同じタスク番号で複数の feature ブランチを同時に作成・保持しない。
- `main` ブランチに直接コミットしない。すべてのタスク作業は feature ブランチ上で行う。
- マージ済みの feature ブランチをそのまま再利用しない。追加修正が必要な場合は新しいタスク番号を発行するか、明示的な理由をユーザーと確認する。
- 同名・同タスク番号のコミットを重複して作成しない。コミット前に `git log --oneline` で既存コミットを確認する。
