# タブ間状態遷移図

`ui/state.py` の `AppState` が発行するイベントと、それを購読する各タブの関係です。

```mermaid
stateDiagram-v2
    [*] --> Idle: アプリ起動 (KindleShotApp)

    state "キャプチャタブ" as Capture
    state "PDF読込タブ" as PdfLoad
    state "トリミングタブ" as Trim
    state "変換タブ" as Convert

    Idle --> Capture: ユーザーがキャプチャ開始
    Idle --> PdfLoad: ユーザーがPDFを選択

    Capture --> Trim: capture_complete\n(state.last_capture_folder に保存)
    Capture --> Convert: capture_complete\n(input_var に直接反映)
    PdfLoad --> Trim: capture_complete\n(同上、PDF読込もキャプチャと同じイベント名)
    PdfLoad --> Convert: capture_complete

    Trim --> Convert: trim_complete\n(state.last_trim_output_folder に保存)

    Convert --> [*]: 変換完了 (PDF/Markdown生成)
```

## 実装メモ

- `AppState.notify(event, data)` は登録済みリスナー全員に同期的に通知します。
  リスナーは `add_listener()` で登録した `_on_state_change(event, data)` メソッドです
- `capture_complete` は「キャプチャタブ」「PDF読込タブ」の両方から発行される
  共通イベント名です。両者は「画像フォルダを用意する」という同じ役割を
  果たすため、下流（トリミング・変換タブ）は発行元を区別する必要がありません
- `trim_complete` は「トリミングタブ」のみが発行します
- 変換タブはこの2つのイベントの両方を購読しており、`capture_complete` でも
  `trim_complete` でも自分の入力フォルダ欄を更新します（`ui/convert_tab.py`
  の `_on_state_change()`）
- 状態は `AppState` インスタンス1つがアプリ全体で共有されます
  （`ui/main_window.py` の `KindleShotApp.__init__` で生成し、各タブの
  コンストラクタに渡すだけ）。永続化はされず、アプリ終了で失われます
  （永続化されるのは `config.json` に保存される設定値のみ）
