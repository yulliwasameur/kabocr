"""Ground-truth quality rules for text-layer truth (born-digital PDFs).

A line is kept only if its truth can be trusted. Each rule targets a failure
seen in real Kabyle documents (pilot of 9-10 Nov 2026):
- other scripts (Arabic, Tifinagh) or dingbats: out of scope;
- dot leaders of tables of contents ("......"): layout, not text;
- legacy Kabyle font encodings: '$' typed for ɣ, 'ê' for ḥ, 'î' for ṭ, etc.
  The image shows a Kabyle letter but the text layer holds another code point,
  so the truth is wrong. Circumflex vowels and '$' inside a word never occur
  in Kabyle orthography, which makes them a reliable signal.
"""
import re
import unicodedata
from .charset import normalise, script_of

LEGACY = re.compile(r"[A-Za-zɛɣḍḥṛṣṭẓčǧ]\$|\$[A-Za-zɛɣḍḥṛṣṭẓčǧ]|[âêîôûÂÊÎÔÛäëïöüÄËÏÖÜ]")
LEADERS = re.compile(r"(\.\s?){4,}|…{2,}|_{4,}")
FRENCH = re.compile(r"\b(le|la|les|des|du|et|est|une|dans|que|pour|qui|sur|par|avec)\b", re.I)


def reasons(gt: str) -> list[str]:
    g = normalise(gt, "lenient")
    r = []
    if any(script_of(c) not in ("Latn", "Common") for c in g):
        r.append("other_script")
    if any(0x2460 <= ord(c) <= 0x27BF for c in g):
        r.append("dingbat")
    # leaders are checked on the text as typed (ellipsis not yet expanded), so "…." is not a leader
    if LEADERS.search(" ".join(unicodedata.normalize("NFC", gt).split())):
        r.append("dot_leaders")
    words = g.split()
    if LEGACY.search(g) and not (words and len(FRENCH.findall(g)) / len(words) > 0.15):
        r.append("legacy_font_encoding")
    return r


def line_ok(gt: str) -> bool:
    return not reasons(gt)
