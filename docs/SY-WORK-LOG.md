# 作業ログ

本ドキュメントは、book2pdf プロジェクトのシステム全体（SY）に関する作業ログです。

---

## 2026-09-06 タスク識別子の正規化と重複文書の整理

### 目的

- タスク管理表・作業ログの識別子を `SY` / `OT` / `LA` 等のモジュール接頭辞付き体系に統一する
- `OT003001` と `OT006001` の混在を解消する
- 古い `tasks.md` / `work_log.md` と新しい `*-TASKS.md` / `*-WORK-LOG.md` の重複を解消する
- `.clinerules` に Task Identifier Rules を追加し、今後の識別子運用を明文化する

### 実施内容

- `docs/OT-TASKS.md`
  - ユースケース見出しを `001` / `002` / `006` / `007` / `008` から `OT001` / `OT002` / `OT006` / `OT007` / `OT008` に正規化
  - `OT003001` の残存参照を `OT006001` に統一
  - 調査報告書リンクを `localapp/docs/timeout-investigation-report-OT006001.md` に更新
- `localapp/docs/LA-TASKS.md`
  - 重複・空の見出し、非標準 ID、番号の連続性を監査
  - LA001 〜 LA008 は連番で配置され、重複 LA008 注釈ブロックは既に削除済み
  - 将来タスクの空の【実施結果】欄は計画として残置
- 文書の移行・削除
  - `docs/work_log.md` → `docs/OT-WORK-LOG.md` にリネーム
  - `localapp/docs/work_log.md` → `localapp/docs/LA-WORK-LOG.md` にリネーム
  - 古い重複ファイル `docs/tasks.md` / `localapp/docs/tasks.md` を削除
  - `localapp/docs/timeout-investigation-report-OT003001.md` → `timeout-investigation-report-OT006001.md` にリネーム
- `.clinerules` に `feature/OT002002-caveats-separation` 由来の `Task Identifier Rules` を追加
- 本 `docs/SY-WORK-LOG.md` を新規作成

### 結果

- タスク識別子の混在が解消され、`.clinerules` に選定基準が明文化された
- 重複したタスクファイルが整理され、新しい命名規約 `docs/OT-TASKS.md` / `localapp/docs/LA-TASKS.md` が残された
- 調査報告書のファイル名とリンクが一致し、リンク切れが解消された

### 関連タスク

- OT006001 進捗通知のポーリング方式仕様策定と localapp リトライ実装
- OT007001 `OT` に誤分類された System タスクを `SY` に分離し、運用ルールとスキルマトリックスを整備する
