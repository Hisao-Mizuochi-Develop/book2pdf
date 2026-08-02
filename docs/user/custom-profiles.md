# 対応アプリ・カスタムプロファイル作成ガイド

## ビルトインプロファイル

`config.json` の初期値として2種類が用意されています（`core/config.py` の `DEFAULT_CONFIG`）。

| キー | アプリ | 備考 |
|------|--------|------|
| `kindle` | Kindle for PC / Amazon Kindle (Mac) | ウィンドウタイトル `kindle` で検出。実機は「Amazon Kindle.app」 |
| `google_play` | Google Play ブックス | `BringWindowToTop` 相当の前面化オプション有効 |

macOS実機で動作確認済みなのは Amazon Kindle アプリのみです。それ以外のアプリを
使う場合は、以下の手順でカスタムプロファイルを作成してください。

## カスタムプロファイルの作り方

1. キャプチャタブでお使いのアプリを開いた状態にする
2. 「▶ 詳細設定」を開く
3. 各項目を設定する（下表）
4. 「領域プレビュー」でウィンドウが正しく検出されるか確認
5. 「名前」欄にプロファイル名を入力し「複製して保存」

| 項目 | 説明 | 決め方のヒント |
|------|------|--------------|
| ウィンドウタイトル | ウィンドウタイトルに含まれるキーワード（大文字小文字区別なし） | メニューバーの「ウインドウ」メニューで実際のタイトルを確認 |
| プロセス名 | アプリ名でのフィルタ（例: `Kindle`）。空欄なら無効 | 指定すると誤検出防止に効果大（後述） |
| ページ送りキー | 通常は `right`。効かない場合は下記の自動フォールバックに任せてOK | — |
| 待機時間(秒) | ページめくり後、次の撮影までの待機 | 遅いアプリほど長く（Google Play Booksは5秒） |
| 境界検出 | `full`（クロップなし・既定）/ `manual`（手動範囲） | 通常は `full` のままでよい。余白はトリミングタブで除去 |

## プロセス名フィルタの重要性（macOS版特有の注意）

macOS版の `find_window()` は、**プロセス名を指定した場合、そのプロセスの
ウィンドウ以外には一切フォールバックしません**。これは、たまたま同じキーワードを
含む無関係なウィンドウ（例: ターミナルの作業フォルダ名に "kindle" が含まれる場合など）
を誤って掴んでしまう事故を防ぐためです。

- Windows用に書かれた `.exe` 付きの値（例: `Kindle.exe`）は自動的に `.exe` を除去して
  比較するため、そのまま流用しても動きます。
- プロセス名がわからない場合は空欄のままにしてください（タイトルキーワードのみで検索します）。
  この場合、無関係なウィンドウを誤って選んでしまうリスクが上がる点に注意してください。

macOS上でのアプリのプロセス名（OwnerName）は、以下のワンライナーで一覧できます。

```bash
kindle_env/bin/python3 -c "
import Quartz
opts = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
for w in Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID):
    if w.get('kCGWindowLayer') == 0 and w.get('kCGWindowName'):
        print(w.get('kCGWindowOwnerName'), '|', w.get('kCGWindowName'))
"
```

## 未対応アプリの追加を試す場合の注意

- honto, BookLive, ebookjapan などブラウザ閲覧専用のサービスは、対象が「ブラウザの
  タブ」になるため、ウィンドウタイトルがページ遷移のたびに変わり不安定です。
  ブラウザ全体をキャプチャ対象にする専用プロファイルの作成をおすすめします。
- ページ送りキーがどうしても効かない場合、`core/capture_engine.py` の
  ページめくりフォールバック（right → space → pagedown → down → scroll）が
  自動的に働きます。詳細は [troubleshooting.md](troubleshooting.md) を参照してください。
