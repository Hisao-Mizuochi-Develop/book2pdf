# 06-ocr.md — OCR パイプライン

## ゴール

トリミング済み画像からテキストを抽出し、後続の変換処理に渡す。NDLOCR-Lite をデフォルトとしつつ、将来のエンジン追加に備えた抽象化を用意する。

## ファイル構成

```
core/
├── ocr_engine.py         # OCR 抽象化・NDLOCR-Lite 連携
├── ocr_preprocess.py     # 画像前処理
├── text_replacements.py  # 置換辞書適用
├── text_reflow.py        # 段落自動整形
└── chapter_detector.py   # 章しおり自動検出
```

## OCR 抽象化インターフェース

```python
from abc import ABC, abstractmethod
from typing import Any


class OCREngine(ABC):
    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def process_single(
        self, image_path: str, preprocess_opts: dict | None = None
    ) -> dict[str, Any]: ...

    @abstractmethod
    def process_folder(
        self,
        image_folder: str,
        preprocess_opts: dict | None = None,
        on_progress=None,
    ) -> list[tuple[str, dict]]: ...
```

## NDLOCR-Lite 実装

- NDLOCR-Lite は外部リポジトリ `ndlocr-lite/` として配置
- アプリ側は `python ndlocr-lite/main.py <入力画像> <出力ディレクトリ>` をサブプロセスで実行
- GPU 不要、CPU 実行前提
- `is_available()` で `ndlocr-lite` ディレクトリと必要ファイルの存在を確認
- 未導入時は「画像 PDF」以外の形式選択時に明確な警告を表示

## OCR 前処理

```python
def preprocess_image(
    image,
    upscale: float = 1.0,
    enhance_contrast: bool = False,
    binarize: bool = False,
    binarize_threshold: int = 180,
):
    """Lanczos アップスケール + コントラスト調整 + 任意で二値化。"""
```

- アップスケール: 1.0 / 1.5 / 2.0 倍から選択
- コントラスト自動調整: Kindle のアンチエイリアス文字に有効
- 二値化: 既定 OFF。地色が薄い本・カラー図版で逆効果になりやすいため

## 置換辞書

`replacements.json` を読み込み、OCR 結果に適用する。

```json
{
  "literal": { "誤": "正" },
  "regex": [
    { "pattern": "(?<=\\d)O(?=\\d)", "replace": "0" }
  ]
}
```

- `literal`: 文字列置換。長いキーから順に適用
- `regex`: 正規表現置換
- 辞書ファイルが存在しない/壊れている場合は no-op または明確なエラーメッセージで動作継続

## 段落自動整形

```python
def reflow_text(text: str) -> str:
    """OCR の改行ノイズを段落として結合する。"""
```

- 日本語: 無空白結合
- 英語: 半角スペース結合
- 英単語のハイフン分割: 結合してハイフン除去
- LLM/外部 API は使わずオフラインで完結

## 章しおり自動検出

```python
@dataclass
class Chapter:
    page_index: int      # 0-based
    title: str
    level: int


def detect_chapters(results: list[tuple[str, dict]]) -> list[Chapter]:
    """第◯章 / Chapter N 等を検出し、Chapter リストを返す。"""
```

- 「第◯章」「Chapter N」等の定型パターンを検出
- ヒューリスティックで章タイトルを判定
- 結果は PDF しおりまたは Markdown 見出しに変換

## UI 関連（convert_tab.py と連携）

- OCR 前処理の有無とオプション選択
- 置換辞書の有効/無効とパス選択
- 章自動検出の有効/無効
- 段落自動整形の有効/無効

## 完了条件

- NDLOCR-Lite 未導入時は「画像 PDF」以外の形式で警告を表示
- OCR 前処理の有無で OCR 結果の精度に差が出る
- 置換辞書ルールが OCR 結果に反映される
- 章自動検出が有効な場合、PDF しおり/Markdown 見出しに反映される
- 段落自動整形で OCR の改行ノイズが結合される
