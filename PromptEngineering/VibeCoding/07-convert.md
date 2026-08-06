# 07-convert.md — 変換・出力生成

## ゴール

トリミング済み（またはキャプチャ直後の）画像を、以下 5 形式に変換する。

| 形式 | OCR | 説明 |
|------|-----|------|
| 画像 PDF | 不要 | 画像をファイル名昇順でそのまま 1 つの PDF に結合 |
| テキスト PDF | 必要 | OCR 抽出テキストのみの軽量 PDF（自動改ページ対応） |
| 検索可能 PDF | 必要 | 画像を描画した上に不可視テキストレイヤーを重ねる |
| Markdown | 必要 | OCR テキストをページ区切り付き `.md` として出力 |
| 画像＋テキスト PDF | 必要 | 画像 1 ページ → 同ページの OCR テキスト 1 ページ以上を繰り返す |

## ファイル構成

```
core/
├── pdf_builder.py        # 5 形式の PDF 生成
└── markdown_writer.py    # Markdown 生成
```

## 画像 PDF

- 入力フォルダ内の画像をファイル名昇順でソート
- 各画像を 1 ページとして結合
- しおりは任意（章自動検出が有効な場合）

## テキスト PDF

- OCR 結果を読みやすい形で配置
- 1 ページのテキストが長い場合、自動的に複数 PDF ページへ改ページ
- 日本語 CID フォント（HeiseiMin-W3）を使用
- 章検出結果に応じて PDF しおりを生成

## 検索可能 PDF

- 画像を背景として描画
- その上に不可視の OCR テキストレイヤーを重ねる
- 見た目は画像のまま、Ctrl+F 等でテキスト検索可能

## 画像＋テキスト PDF（見開き型）

- 各ページについて「画像 1 ページ → 同じページの OCR テキスト 1 ページ以上（自動改ページ）」を繰り返す
- PDF を開いてページ順を目視確認できる

## Markdown

- フロントマター（タイトル、生成日時等）を含む
- ページ区切りコメントまたは見出しを挿入
- 「ページ画像を併記」オプションあり。有効時は各ページの画像リンクを本文に埋め込む
- 章自動検出が有効な場合、見出しに変換

## 共通オプション

- OCR 前処理（アップスケール・コントラスト強調・二値化）
- 置換辞書
- 章自動検出
- 段落自動整形

## 関数シグネチャ例

```python
def images_to_pdf(
    folder_path: str,
    output_folder: str,
    output_filename: str,
    on_progress=None,
    chapters=None,
): ...


def text_to_pdf(
    results: list[tuple[str, str]],
    output_path: str,
    on_progress=None,
    chapters=None,
): ...


def images_to_searchable_pdf(
    image_folder: str,
    results: list[tuple[str, dict]],
    output_path: str,
    on_progress=None,
    chapters=None,
): ...


def images_with_text_pdf(
    image_folder: str,
    results: list[tuple[str, dict]],
    output_path: str,
    on_progress=None,
    chapters=None,
): ...


def write_markdown(
    results: list[tuple[str, str]],
    output_path: str,
    image_folder: str | None = None,
    embed_images: bool = False,
    chapters=None,
): ...
```

## UI 要件（convert_tab.py）

- 入力フォルダ・出力フォルダ選択
- 出力形式選択（5 形式）
- OCR オプション（前処理、置換辞書、章検出、段落整形）
- Markdown 画像併記オプション
- 変換実行ボタン
- 進捗ログ表示

## 完了条件

- 5 形式すべてが正常に生成される
- 画像 PDF は全ページが正しい順序で含まれる
- テキスト PDF は長文時に自動改ページされる
- 検索可能 PDF は画像の見た目を保ちつつテキスト検索できる
- Markdown はページ区切りとフロントマターが含まれる
- 画像＋テキスト PDF はページ順が正しく繰り返されている
