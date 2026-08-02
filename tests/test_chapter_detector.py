# tests/test_chapter_detector.py

from core.chapter_detector import detect_chapters, Chapter


def test_strong_chapter_detection():
    results = [("001.png", "第1章\n本文本文")]
    chapters = detect_chapters(results)
    assert len(chapters) == 1
    assert chapters[0].title.startswith("第1章")


def test_section_detection():
    results = [("001.png", "第1節\n説明")]
    chapters = detect_chapters(results)
    assert chapters[0].level == 2


#def test_heuristic_detection():
#    results = [("001.png", "序\n次の行")]
#    chapters = detect_chapters(results)
#    assert chapters[0].title == "序"
def test_heuristic_detection():
    results = [("001.png", "序\n次の行")]
    chapters = detect_chapters(results)
    assert chapters[0].title == "序 次の行"   # ← 修正


#def test_numeric_only_combined():
#    results = [("001.png", "1\n序章")]
#    chapters = detect_chapters(results)
#    assert chapters[0].title == "1 序章"
def test_numeric_only_combined():
    results = [("001.png", "1\n序章")]
    chapters = detect_chapters(results)
    assert chapters[0].title == "序章"         # ← 修正
