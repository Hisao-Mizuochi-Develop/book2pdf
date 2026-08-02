# tests/test_text_reflow.py

import textwrap
from core.text_reflow import (
    reflow_text,
    reflow_markdown,
)


def test_reflow_text_joins_non_terminal_lines():
    src = "これは\nテストです。"
    out = reflow_text(src)
    assert out == "これはテストです。"


def test_reflow_text_keeps_sentence_endings():
    src = "これはテストです。\n次の文です。"
    out = reflow_text(src)
    assert out == "これはテストです。\n次の文です。"


def test_reflow_text_english_hyphen_join():
    src = "inter-\nnational"
    out = reflow_text(src)
    assert out == "international"


def test_reflow_text_english_space_join():
    src = "This is\nan example."
    out = reflow_text(src)
    assert out == "This is an example."


def test_reflow_text_block_leading_breaks_paragraph():
    src = "これはテスト\n（補足です）"
    out = reflow_text(src)
    assert out == "これはテスト\n（補足です）"


def test_reflow_text_structural_heading():
    src = "# 見出し\n本文\n続き"
    out = reflow_text(src)
    assert out == "# 見出し\n本文続き"


def test_reflow_text_structural_list():
    src = "- 項目1\n- 項目2\n本文\n続き"
    out = reflow_text(src)
    assert out == "- 項目1\n- 項目2\n本文続き"


def test_reflow_text_table_lines_are_preserved():
    src = "| a | b |\n|---|---|\nvalue\nnext"
    out = reflow_text(src)
    assert out == "| a | b |\n|---|---|\nvalue next"


def test_reflow_text_empty_lines_collapse():
    src = "文1\n\n\n文2"
    out = reflow_text(src)
    assert out == "文1\n\n文2"


def test_reflow_text_short_line_breaks_paragraph():
    src = "第1章\nこれは本文です"
    out = reflow_text(src)
    assert out == "第1章\nこれは本文です"


def test_reflow_text_list_item_dots_break():
    src = "項目……\n次の行"
    out = reflow_text(src)
    assert out == "項目……\n次の行"


def test_reflow_markdown_preserves_front_matter():
    src = textwrap.dedent("""\
        ---
        title: Sample
        date: 2024-01-01
        ---
        これは
        テストです。
    """)
    out = reflow_markdown(src)
    assert out.startswith("---")
    assert "これはテストです。" in out


def test_reflow_markdown_preserves_code_fence():
    src = textwrap.dedent("""\
        ```
        a = 1
        b = 2
        ```
        文1
        文2
    """)
    out = reflow_markdown(src)
    assert "a = 1" in out
    assert "文1文2" in out


def test_reflow_markdown_multiple_blocks():
    src = textwrap.dedent("""\
        # 見出し
        文1
        文2

        ```
        code
        block
        ```

        文3
        文4
    """)
    out = reflow_markdown(src)
    assert "# 見出し" in out
    assert "文1文2" in out
    assert "code" in out
    assert "文3文4" in out
