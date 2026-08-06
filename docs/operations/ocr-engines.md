# OCR エンジン追加・変更ガイド

## 現在のデフォルトエンジン

**NDLOCR-Lite**

- 国立国会図書館製の日本語 OCR
- GPU 不要、CPU 実行
- 縦書き・ルビ・漫画的なレイアウトに強い
- 外部リポジトリとして `ndlocr-lite/` に配置

## 抽象化インターフェース

`core/ocr_engine.py` 内で `OCREngine` 抽象クラスを定義している。新規エンジンを追加する際は、このインターフェースを実装する。

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

## 新規エンジン追加手順

1. `core/ocr_engine.py` に新しいエンジンクラスを作成する（例: `TesseractEngine`）
2. `is_available()` でそのエンジンが使えるか判定する
3. `process_single()` / `process_folder()` でテキスト認識結果を返す
4. `get_available_engines()` またはファクトリ関数に新しいエンジンを登録する
5. `config.json` の `ocr.engine` 等で切り替えられるようにする
6. 必要に応じて依存を `pyproject.toml` に追加する
7. このドキュメントにエンジンの特徴と制限を追記する

## 検討可能な代替エンジン

| エンジン | 強み | 弱み |
|---------|------|------|
| Tesseract OCR | 軽量、多言語、導入簡単 | 日本語縦書きは NDLOCR より弱い |
| Manga OCR | 漫画・縦書き日本語に強い | 一般的な文書レイアウトには不向き |
| PaddleOCR | 日本語モデルあり | 環境依存で品質が変わる |
| EasyOCR | 多言語 | 初回ダウンロードが重い |

## 前処理・後処理

OCR エンジン固有の処理は極力避け、前処理・後処理はアプリ側で統一する。

- **前処理**: `core/ocr_preprocess.py`（アップスケール・コントラスト・二値化）
- **後処理**: `core/text_replacements.py`（置換辞書）と `core/text_reflow.py`（段落整形）

## 注意点

- OCR エンジンを追加・変更しても、既存の 5 出力形式が動作しなくならないように注意する
- 未導入時は「画像 PDF」以外の形式で明確な警告を出す
- サブプロセス起動時は `sys.executable` 問題を避ける設計を維持する
