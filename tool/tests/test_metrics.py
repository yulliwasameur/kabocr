import unicodedata

from kabocr_eval.charset import normalise, strip_diacritics, uncovered_chars, script_of
from kabocr_eval.metrics import count, rates, corpus, bootstrap_ci, paired_permutation, holm


def test_nfc_merges_combining_dot():
    decomposed = "ḍ"  # d + combining dot below
    assert normalise(decomposed) == "ḍ"
    assert len(normalise(decomposed)) == 1


def test_strict_vs_lenient_epsilon():
    ref, hyp = "ɛeddi", "εeddi"  # Greek epsilon in the hypothesis
    assert rates(count(ref, hyp, mode="strict"))["CER"] == 1 / 5
    assert rates(count(ref, hyp, mode="lenient"))["CER"] == 0.0


def test_perfect():
    r = rates(count("Azul fell-awen, ad nɣer taqbaylit.", "Azul fell-awen, ad nɣer taqbaylit."))
    assert r["CER"] == r["WER"] == r["DCER"] == 0.0


def test_dcer_counts_lost_diacritic():
    # ḥ read as h, ɣ read as g: 2 special errors / 2 special letters
    r = rates(count("aḥeddad yeɣra", "aheddad yegra"))
    assert r["DCER"] == 1.0
    assert r["BaseCER"] > 0  # ɣ->g is a base-letter error too (ɣ is a letter, not a mark)


def test_dcer_spurious_special_letter():
    c = count("tamurt", "tamurṭ")
    assert c.special_err == 1 and c.special_ref == 0
    assert c.special_spur == 1 and c.special_miss == 0


def test_strip_diacritics():
    assert strip_diacritics("ḍṛṣṭẓčǧḥ") == "drstzcgh"


def test_wrong_script():
    r = rates(count("ⴰⵣⵓⵍ", "azul", expected_script="Tfng"))
    assert r["WrongScript"] == 1.0
    assert script_of("ⵣ") == "Tfng"


def test_uncovered():
    vocab = set("abcdefghijklmnopqrstuvwxyz")
    assert uncovered_chars("aɣrum ḍ", vocab) == {"ɣ", "ḍ"}


def test_bootstrap_and_permutation():
    refs = ["taddart n wedrar"] * 30
    a = [count(r, r) for r in refs]
    b = [count(r, "tadart n wedrar") for r in refs]
    p, lo, hi = bootstrap_ci(b, "CER", n=200)
    assert lo <= p <= hi
    assert paired_permutation(a, b, n=500) < 0.01
    assert holm({"x": 0.001, "y": 0.04, "z": 0.2}) == {"x": True, "y": False, "z": False}


def test_corpus_is_character_weighted():
    tot = corpus([("ab", "ab"), ("abcdefghij", "xbcdefghij")])
    assert rates(tot)["CER"] == 1 / 12


def test_gt_quality_rules():
    from kabocr_eval.gtquality import reasons, line_ok
    assert line_ok("Tasekla d lemri n tmetti tettawi-d ɣef leɛwayed")
    assert "legacy_font_encoding" in reasons("yettwa$ra s tmeslayt")
    assert "dot_leaders" in reasons("Tazwert ............ 12")
    assert "other_script" in reasons("awal ⴰⵣⵓⵍ")
    assert line_ok("une tâche pour le maître et les élèves")  # French circumflex is fine


def test_punct_space_mode():
    a = normalise("fahmen ugar . HANOTEAU , yella-d", punct_space=True)
    b = normalise("fahmen ugar. HANOTEAU, yella-d", punct_space=True)
    assert a == b
    assert normalise("ad yelmed", punct_space=True) == "ad yelmed"  # word spaces kept


def test_ellipsis():
    assert normalise("aman…") == normalise("aman...")


def test_cyrillic_schwa_folded():
    assert normalise("lәqraya", "lenient") == "ləqraya"
