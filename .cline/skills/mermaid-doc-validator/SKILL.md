---
name: mermaid-doc-validator
description: |
  Validate Mermaid diagram syntax in Markdown files.
  Activate when creating or editing Mermaid diagrams (sequenceDiagram, flowchart,
  graph, stateDiagram, classDiagram). Can be invoked explicitly or automatically
  by file-modifier / task-manager.
compatibility: VS Code + Cline
metadata:
  author: book2pdf-team
  version: "1.0"
---

# mermaid-doc-validator

## 概要
本スキルは、Markdown 内の Mermaid 図の構文エラーを検出し、修正指針を提示します。

## 検証対象
- `docs/**/*.md`
- その他、プロジェクト内の `*.md` ファイルに含まれる ` ```mermaid ` コードブロック

## 図作成前の自己確認リスト

新規または既存の Mermaid 図を作成・編集する前に、以下を必ず確認すること。

- [ ] `{` または `}` を含むテキストがある場合、ダブルクォート `"..."` で囲んでいるか
- [ ] `[` または `]` を含むテキストがある場合、ダブルクォート `"..."` で囲むか代替表現にしていないか
- [ ] `class` / `classDef` などの予約語をテキストとして使用している場合、ダブルクォートで囲んでいるか
- [ ] `participant` / `state` / `subgraph` の識別子とラベルの間に半角スペースが正しく入っているか
- [ ] `subgraph`、`loop`、`alt`、`opt` などのブロックに対応する `end` が欠落していないか
- [ ] 同一文書内で図種別（`flowchart` / `sequenceDiagram` / `stateDiagram`）が目的に応じて統一されているか
- [ ] VS Code Mermaid プレビュー拡張機能でレンダリングエラーが出ていないか

## 主要的な構文エラーパターンと対処法

### 1. `{}` 波括弧の衝突（最も頻出）

Mermaid では `{}` は diamond ノード（{rhombus}）の構文として解釈されます。
テキスト内に `{job_id}` などの波括弧を含めると構文エラーになります。

#### 影響を受ける要素
- `sequenceDiagram` の `participant` 宣言
- `flowchart` / `graph` のノードラベル `[label]`
- `subgraph` タイトル

#### 修正方法
テキストをダブルクォートで囲む：

```mermaid
# NG
participant FILE as /data/progress/{job_id}.json
FILE[/data/progress/{job_id}.json]

# OK
participant FILE as "/data/progress/{job_id}.json"
FILE["/data/progress/{job_id}.json"]
```

### 2. `[]` 角括弧の衝突（flowchart / graph）

角括弧はノード形状の構文 `[label]` です。URL や配列表現で衝突する可能性があります。

#### 修正方法
ダブルクォートで囲む、または `[ ]` 内では避ける表現を使用する。

### 3. `class` / `classDef` と CSS キーワードの衝突

`class` は Mermaid の予約語です。テキストとして使用する場合はダブルクォートで囲む。

### 4. よくあるその他の構文エラー

| エラーパターン | 症状 | 修正方法 |
|---|---|---|
| 半角スペース不足 | `participantA as Name` は認識されない | `participant A as Name` とスペースを入れる |
| `subgraph` の閉じ忘れ | `subgraph` を開いたら必ず `end` で閉じる | `end` を追加する |
| `end` の欠落 | `loop`、`alt`、`opt` なども `end` で閉じる必要がある | 各ブロックに対応する `end` を確認 |

## 検証手順

1. ファイル保存後、VS Code Mermaid プレビュー拡張機能でレンダリング確認
2. エラーがあれば上記パターンを照合
3. 修正後、再度プレビュー確認

## 図種別別の注意点

| 図種別 | 特有の注意点 |
|---|---|
| `sequenceDiagram` | `participant` ラベルはダブルクォートで囲む。`->>` / `-->>` 構文は半角スペース区切り。`activate` / `deactivate` は対で使用。 |
| `flowchart` / `graph` | ノード形状 `[ ]` / `( )` / `{ }` / `[/ /]`。`-->` 接続、双方向 `--`。`direction TD` / `LR` は `flowchart` 宣言直後に記述。 |
| `stateDiagram` | `state` 宣言は `state "Name" as ID`。`[*]` は初期/終了状態。转移は `ID1 --> ID2`。 |
| `classDiagram` | `class` は予約語。`<<interface>>` ステレオタイプは `class Name { }` 内で使用。 |
