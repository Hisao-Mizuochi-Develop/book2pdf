# タスク管理（System / 全体設計・仕様・横断基盤）

本ファイルは、`backend` / `frontend` / `ocr-worker` / `localapp` を横断するプロジェクト全体の「設計・仕様・横断基盤」に関するタスクを追記型で管理するものです。

- 個別モジュールの実装タスクは各 `<module>/docs/<識別子>-TASKS.md` に記載してください。
- 複数モジュールにまたがる実装作業は `docs/OT-TASKS.md` に記載してください。
- 本来 `SY` であるタスクが `OT` や他の識別子で起票されていた場合、履歴を本ファイルに移行記録し、元タスクからは設計・仕様部分を除きます。

## タスク粒度の方針

- タスクは数時間〜1日以内で完了できる粒度とする
- 1つのタスクに複数の責務が含まれる場合は分割を検討する
- 詳細項目を無理に別タスクにせず、達成可能な単位でまとめる
- 作業の記録はタスク詳細欄に箇条書きで記載する
- タスク No は「モジュール識別子（2文字）＋ ユースケースNo（3桁）＋ 通番（3桁）」とする
  - 識別子: `SY`=System/全体設計・仕様・横断基盤, `BE`=backend, `FE`=frontend, `OW`=ocr-worker, `LA`=localapp, `OT`=横断・その他
  - 例：ユースケース001の1番目のタスク → `SY001001`
  - 例：ユースケース002の1番目のタスク → `SY002001`
- 通番は各ユースケース内で 001 から連番で振る

---

## ユースケースNo | 001

ユースケース
プロジェクト全体のドキュメント整備と横断基盤の確立

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| SY001001 | 全体計画書・設計決定事項・コーディング規約の整備 | 2026-08-11 | 2026-08-11 | 設計 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | プロジェクト全体の構成を `docs/SY-WEB-OCR-SYSTEM-PLAN.md` にまとめる |  |  |  |
|  | 技術選定の理由を `docs/SY-DESIGN-DECISIONS.md` にまとめる |  |  |  |
|  | Python / TypeScript / Rust のコーディング規約を `docs/OT-CODING-CONVENTIONS.md` にまとめる |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-08-11: `docs/SY-WEB-OCR-SYSTEM-PLAN.md` を新規作成し、システム全体構成・アーキテクチャ・処理フローを記載した |  |  |  |
|  | 2026-08-11: `docs/SY-DESIGN-DECISIONS.md` を新規作成し、技術選定と将来の課題を記載した |  |  |  |
|  | 2026-08-11: `docs/OT-CODING-CONVENTIONS.md` を新規作成し、各言語のコーディング規約を定めた |  |  |  |
|  | 【移行履歴】 |  |  |  |
|  | 元 `OT001001` として起票・完了したが、内容が System / 全体設計に該当するため、本ファイルに分離記録した（実施結果は変更なし） |  |  |  |

---

## ユースケースNo | 002

ユースケース
進捗通知方式の全体仕様策定

| タスクNO | タスクタイトル | タスク起票日付 | タスク完了日付 | タスク種別 |
|---|---|---|---|---|
| SY002001 | 進捗通知のポーリング方式全体仕様策定 | 2026-09-03 | 2026-09-03 | 仕様 |
|  | タスク詳細 |  |  |  |
|  | 【計画】 |  |  |  |
|  | `docs/progress-notification-polling-design.md` と `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` を統合し、SSE / HTTP ポーリングの全体仕様を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に整理する |  |  |  |
|  | 進捗ペイロード `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止する |  |  |  |
|  | ポーリングプロトコルを文書化する（1 リクエストあたり 10 秒タイムアウト、1 秒 / 2 秒 / 4 秒の指数関数的バックオフ、最大 3 回リトライ） |  |  |  |
|  | 【実施結果】 |  |  |  |
|  | 2026-09-03: `docs/progress-notification-polling-design.md` を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に統合し、前者を削除した |  |  |  |
|  | 2026-09-03: `OcrProgressPayload` を `stage` / `message` / `current` / `total` に統一し、`progress_percent` を廃止した |  |  |  |
|  | 2026-09-03: ポーリングプロトコル（10 秒タイムアウト、1/2/4 秒バックオフ、最大 3 回リトライ）を `docs/SY-PROGRESS-NOTIFICATION-SPEC.md` に文書化した |  |  |  |
|  | 2026-09-03: `docs/README.md` / `docs/SY-WEB-OCR-SYSTEM-PLAN.md` を更新した |  |  |  |
|  | 【移行履歴】 |  |  |  |
|  | 元 `OT003001` に含まれていた「進捗通知ポーリング方式の仕様策定」部分を `SY` タスクとして分離記録した。`localapp` 側のリトライ実装・タイムアウト設定ファイル化は `OT003001` に残した |  |  |  |

---

## 移行履歴

本ファイルに記載されていた `.clinerules` / AgentSkills / ガバナンス・運用ルールに関するタスクは、新規モジュール識別子 `PJ` の設立に伴い `docs/PJ-TASKS.md` へ移行しました。

| 元タスクNO | 移行先タスクNO | 移行先ファイル | 移行理由 | 移行実施日 |
|---|---|---|---|---|
| SY007001 | PJ001001 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007002 | PJ001002 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007003 | PJ001003 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007004 | PJ001004 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007005 | PJ001005 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007006 | PJ001006 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007007 | PJ001007 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007008 | PJ001008 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007009 | PJ001009 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007010 | PJ001010 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007011 | PJ001011 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007012 | PJ001012 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |
| SY007013 | PJ001013 | docs/PJ-TASKS.md | `.clinerules`/AgentSkills ガバナンスは `PJ` の対象となるため | 2026-09-09 |