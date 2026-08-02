# kindle2pdf ドキュメント（macOS版）

このディレクトリには、macOS移植版 kindle2pdf に関するドキュメントを
対象者別のフォルダに分けて格納しています。アプリのソースコードと実際の
動作検証結果から作成したもので、元のWindows版ドキュメントとは独立しています。

## [user/](user/) — 使う人向け

| ドキュメント | 内容 |
|-------------|------|
| [setup.md](user/setup.md) | セットアップ手順（Python/Homebrew導入〜起動まで） |
| [quickstart.md](user/quickstart.md) | キャプチャ→トリミング→変換の最短手順 |
| [tabs-reference.md](user/tabs-reference.md) | 4タブそれぞれの設定項目リファレンス |
| [output-formats.md](user/output-formats.md) | 5つの出力形式の比較と選び方 |
| [custom-profiles.md](user/custom-profiles.md) | Kindle以外のアプリ用プロファイルの作り方 |
| [permissions.md](user/permissions.md) | 画面収録・アクセシビリティ権限の許可手順 |
| [troubleshooting.md](user/troubleshooting.md) | 実際に発生した不具合と対処法のFAQ |

## [developer/](developer/) — 開発・保守する人向け

| ドキュメント | 内容 |
|-------------|------|
| [architecture.md](developer/architecture.md) | core/ui分離、タブ間状態共有の仕組み |
| [module-reference.md](developer/module-reference.md) | 全モジュール・主要関数の一覧 |
| [macos-port-notes.md](developer/macos-port-notes.md) | Windows→macOS移植で変更した箇所と理由 |
| [known-limitations.md](developer/known-limitations.md) | 既知の制約・未検証事項 |
| [config-schema.md](developer/config-schema.md) | config.json / CaptureProfile のフィールド一覧 |
| [verification-log.md](developer/verification-log.md) | 実機での動作検証記録 |
| [contributing.md](developer/contributing.md) | コーディング規約、機能追加の手順 |

## [operations/](operations/) — 運用・配布する人向け

| ドキュメント | 内容 |
|-------------|------|
| [build-distribution.md](operations/build-distribution.md) | venvベースの起動方式と配布手順 |
| [changelog.md](operations/changelog.md) | Windows版からの変更点まとめ |
| [security-privacy.md](operations/security-privacy.md) | 通信の有無、権限要求の理由、利用上の注意 |

## [diagrams/](diagrams/) — 図解

| ドキュメント | 内容 |
|-------------|------|
| [workflow.md](diagrams/workflow.md) | 4タブの入出力関係、出力形式ごとのOCR要否 |
| [capture-sequence.md](diagrams/capture-sequence.md) | キャプチャ開始〜ページめくりのシーケンス図 |
| [state-transitions.md](diagrams/state-transitions.md) | AppStateによるタブ間イベント通知の状態遷移図 |

## どこから読めばいいか

- **とりあえず使いたい** → [user/setup.md](user/setup.md) → [user/quickstart.md](user/quickstart.md)
- **うまく動かない** → [user/troubleshooting.md](user/troubleshooting.md) →
  [user/permissions.md](user/permissions.md)
- **コードを読む/直す** → [developer/architecture.md](developer/architecture.md) →
  [developer/module-reference.md](developer/module-reference.md)
- **Windows版との違いを知りたい** → [developer/macos-port-notes.md](developer/macos-port-notes.md)
