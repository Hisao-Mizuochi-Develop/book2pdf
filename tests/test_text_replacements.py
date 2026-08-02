# tests/test_text_replacements.py

from core.text_replacements import Replacer, apply_to_results


def test_literal_replacement():
    r = Replacer(literal={"啦": "です"})
    assert r.apply("これは啦") == "これはです"


#def test_regex_replacement():
#    r = Replacer(regex=[{"pattern": r"(\d)O(\d)", "replace": r"\10\2"}])
#    assert r.apply("1O2") == "102"
def test_regex_replacement():
    r = Replacer(regex=[{"pattern": r"(\d)O(\d)", "replace": r"\g<1>0\g<2>"}])
    assert r.apply("1O2") == "102"


def test_apply_to_results():
    results = [("001.png", "啦")]
    new, err = apply_to_results(results, path=None)
    assert new[0][1] == "啦"  # no-op because default replacer is empty
