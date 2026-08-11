"""ndlocr_cli の XML 出力を解析するサービスです。

OCR 処理結果は XML 形式（.sorted.xml）で出力されます。
このモジュールでは、ページ画像、テキスト行、座標情報を取り出して、
検索可能 PDF 生成に利用できる形式に変換します。
"""

# 型注釈を文字列として遅延評価できるようにするための import です
# Python 3.9 でも Python 3.10+ の型注釈記法を使えるようになります
from __future__ import annotations

# XML を解析するための標準ライブラリです
import xml.etree.ElementTree as ET

# ファイルパスをオブジェクトとして扱うための標準ライブラリです
from pathlib import Path


class OcrLine:
    """OCR によって検出された 1 行のテキストを表します。"""

    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        """OCR 行データを初期化します。

        Args:
            text: 認識されたテキスト
            x: テキスト行の左上 X 座標（画像左上原点）
            y: テキスト行の左上 Y 座標（画像左上原点）
            width: テキスト行の幅
            height: テキスト行の高さ
        """
        # 認識されたテキスト本文です
        self.text = text

        # テキスト行の左上 X 座標です（画像左上原点）
        self.x = x

        # テキスト行の左上 Y 座標です（画像左上原点）
        self.y = y

        # テキスト行の幅です
        self.width = width

        # テキスト行の高さです
        self.height = height


class OcrPage:
    """OCR 結果の 1 ページ分を表します。"""

    def __init__(
        self,
        image_name: str,
        width: int,
        height: int,
        lines: list[OcrLine],
    ) -> None:
        """OCR ページデータを初期化します。

        Args:
            image_name: ページ画像のファイル名
            width: ページ画像の幅
            height: ページ画像の高さ
            lines: ページ内のテキスト行一覧
        """
        # ページ画像のファイル名です
        self.image_name = image_name

        # ページ画像の幅です
        self.width = width

        # ページ画像の高さです
        self.height = height

        # ページ内のテキスト行一覧です
        self.lines = lines


def parse_sorted_xml(xml_path: str | Path) -> list[OcrPage]:
    """ndlocr_cli の .sorted.xml ファイルを解析します。

    XML 形式例:
        <?xml version="1.0" encoding="UTF-8"?>
        <OCRDATASET>
          <PAGE HEIGHT="1200" WIDTH="800" IMAGENAME="page1.png">
            <LINE TYPE="テキスト" X="100" Y="200" WIDTH="300" HEIGHT="40" STRING="サンプル" ORDER="1" />
            ...
          </PAGE>
          ...
        </OCRDATASET>

    Args:
        xml_path: 解析対象の XML ファイルパス

    Returns:
        ページ情報のリスト
    """
    # 文字列の場合は Path オブジェクトに変換します
    path = Path(xml_path)

    # XML ファイルが存在しない場合は空のリストを返します
    if not path.exists():
        return []

    # XML ファイルを読み込んで要素ツリーを構築します
    tree = ET.parse(path)
    root = tree.getroot()

    # 解析結果のページ一覧を格納するリストです
    pages: list[OcrPage] = []

    # ルート要素（OCRDATASET）以下の PAGE 要素を順に処理します
    for page_elem in root.findall("PAGE"):
        # ページ画像のファイル名を取得します
        image_name = page_elem.get("IMAGENAME", "")

        # ページ画像の幅を取得します（未設定時は 0）
        width = int(page_elem.get("WIDTH", "0") or "0")

        # ページ画像の高さを取得します（未設定時は 0）
        height = int(page_elem.get("HEIGHT", "0") or "0")

        # ページ内のテキスト行一覧を格納するリストです
        lines: list[OcrLine] = []

        # PAGE 要素以下の LINE 要素を順に処理します
        for line_elem in page_elem.findall("LINE"):
            # 認識されたテキストを取得します
            text = line_elem.get("STRING", "")

            # 空のテキスト行は無視します
            if not text:
                continue

            # テキスト行の座標を取得します（未設定時は 0）
            x = int(line_elem.get("X", "0") or "0")
            y = int(line_elem.get("Y", "0") or "0")
            line_width = int(line_elem.get("WIDTH", "0") or "0")
            line_height = int(line_elem.get("HEIGHT", "0") or "0")

            # 座標情報をもつ OcrLine オブジェクトを作成します
            line = OcrLine(
                text=text,
                x=x,
                y=y,
                width=line_width,
                height=line_height,
            )
            lines.append(line)

        # ページ情報を作成して結果リストに追加します
        page = OcrPage(
            image_name=image_name,
            width=width,
            height=height,
            lines=lines,
        )
        pages.append(page)

    # 解析したページ一覧を返します
    return pages


def find_sorted_xml(output_dir: str | Path) -> Path | None:
    """OCR 出力ディレクトリから .sorted.xml ファイルを探します。

    Args:
        output_dir: OCR 結果のルートディレクトリ

    Returns:
        見つかった .sorted.xml ファイルのパス。存在しない場合は None
    """
    # 文字列の場合は Path オブジェクトに変換します
    root = Path(output_dir)

    # output_dir 以下の xml ディレクトリを再帰的に探します
    for xml_dir in root.rglob("xml"):
        # xml ディレクトリ内の .sorted.xml ファイルを探します
        for xml_path in xml_dir.glob("*.sorted.xml"):
            # 最初に見つかったファイルを返します
            return xml_path

    # 見つからない場合は None を返します
    return None
