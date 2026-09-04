# python-style

## 基本

- Python 3.x（プロジェクト指定バージョン）
- 関数・クラスには docstring を記述
- 複雑なロジックには「なぜそのように実装したか」を含むコメント

## import コメント例

```python
# FastAPI: Web フレームワーク。ルーティングとリクエスト処理を提供
from fastapi import FastAPI, HTTPException

# PyMuPDF: PDF 生成・操作ライブラリ
import fitz
```

## docstring 例

```python
def create_job(input_format: str) -> str:
    """
    新規 OCR ジョブを作成する。

    Args:
        input_format: 入力ファイル形式（"zip" など）

    Returns:
        作成されたジョブID
    """
    ...
```
