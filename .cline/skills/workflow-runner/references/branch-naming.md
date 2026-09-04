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
- tasks.md / work_log.md 更新内容のユーザー承認
