# 既知の制約・注意点

## キャプチャ関連

- **座標系はポイント単位（Retina等倍）**: `ImageGrab.grab(bbox=...)` はmacOS上で
  ウィンドウのポイント座標をそのままピクセル数として出力するため、Retina
  ディスプレイのネイティブ解像度（2倍等）はキャプチャに反映されません。
  OCR用途では通常十分ですが、高解像度が必要な場合は別途対応が必要です
  （[macos-port-notes.md](macos-port-notes.md) の座標系の節を参照）。
- **`process_name` 指定時はフォールバックしない**: 指定したプロセス名の
  ウィンドウが見つからない場合、タイトルだけの緩い一致では拾いません
  （意図的な安全設計。[macos-port-notes.md](macos-port-notes.md) 参照）。
- **マルチSpace/フルスクリーンアプリの扱い未検証**: 対象アプリが独立した
  フルスクリーンSpaceで動いている場合、`CGWindowListCopyWindowInfo` の
  `kCGWindowListOptionOnScreenOnly` は現在アクティブなSpace以外のウィンドウを
  返さないことがあります。`activate_window()` でアプリをアクティブ化すれば
  多くの場合Space切り替えも追従しますが、完全に検証済みとは言えません。
- **ページめくりのエスカレーションは「変化検出」ベース**: スクロール型の
  コンテンツで、スクロール量が小さすぎて閾値（0.5%）を超えない場合、
  正しくスクロールしていても「変化なし」と誤判定される可能性があります。

## OCR関連

- **NDLOCR-LiteはCPU実行**: GPUを使わないため、ページ数が多いと変換に
  時間がかかります（M-series Mac実測で1ページあたり約15〜20秒）。
- **前処理のデフォルト値はKindle基準**: `upscale=1.5`, `enhance_contrast=True`
  はKindleのアンチエイリアス文字を想定した既定値です。他アプリ・他解像度では
  最適値が異なる可能性があります。

## 対応アプリ

- 実機検証済みなのは **Amazon Kindle (Mac)** のみです。`google_play` /
  `rakuten_kobo` / `bookwalker` / `dmm_books` / `kinoppy` の各ビルトイン
  プロファイルはWindows版からの移植で、macOS上でのウィンドウタイトル・
  プロセス名が一致するかは未確認です。

## PDF生成関連

- **画像+テキストPDFはA4固定でスケーリング**: `images_with_text_pdf()` は
  画像を全ページA4サイズに収まるよう縦横比を保って縮小します。元画像の
  実寸を保持したPDFが必要な場合は「画像PDF」（`images_to_pdf`、画像サイズを
  そのままページサイズにする）を使ってください。
- **章検出はヒューリスティック**: `chapter_detector.py` の検出は「第◯章」等の
  定型パターンとページ先頭行のヒューリスティックに依存しており、小説の
  無題の章やレイアウトが特殊な書籍では誤検出・見逃しが起こり得ます。

## ビルド/配布

- 本移植では PyInstaller 等によるフルスタンドアロン化は行っておらず、
  venvベースの起動を前提としています。理由と代替案は
  [../operations/build-distribution.md](../operations/build-distribution.md) を参照してください。
