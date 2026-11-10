"""Kabyle character inventory, Unicode normalisation and homoglyph folding.

Two evaluation modes are always reported:
- strict  : NFC normalisation only. A Greek epsilon is NOT a Kabyle ɛ.
- lenient : NFC + folding of known homoglyphs (encoding variants that are
            visually identical and frequent in Kabyle texts on the web).
"""
from __future__ import annotations

import re
import unicodedata

# Letters specific to the Kabyle / Berber Latin orthography (lower + upper).
SPECIAL_LOWER = "ɛɣčǧḍḥṛṣṭẓţ"
SPECIAL_UPPER = "ƐƔČǦḌḤṚṢṬẒŢ"
LABIALISATION = "ʷ"
SPECIAL = set(SPECIAL_LOWER + SPECIAL_UPPER + LABIALISATION)

# Plain Latin letters used in standard Kabyle (o, p, v appear in loans / some
# conventions; kept so the inventory does not silently reject real text).
BASE_LATIN = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Neo-Tifinagh block U+2D30..U+2D7F (+ U+2D7F joiner).
TIFINAGH = {chr(c) for c in range(0x2D30, 0x2D80)}

# Homoglyphs: visually identical code points that are NOT the Kabyle letter.
HOMOGLYPHS = {
    "ε": "ɛ",  # Greek small epsilon  -> Latin open e
    "Ε": "Ɛ",  # Greek capital epsilon
    "γ": "ɣ",  # Greek small gamma    -> Latin gamma
    "Γ": "Ɣ",  # Greek capital gamma
    "Г": "Ɣ",  # Cyrillic capital ghe (seen in Tesseract outputs)
    "ɣ": "ɣ",  # identity, kept for clarity
    # seen in real Kabyle theses (pilot of 9 Nov 2026):
    "\u0511": "ɛ",  # Cyrillic small reversed ze (ԑ)
    "\u0510": "Ɛ",  # Cyrillic capital reversed ze (Ԑ)
    "\u0264": "ɣ",  # Latin small rams horn (ɤ)
    "\u01a9": "Ɛ",  # Latin capital esh (Ʃ), typed for capital ɛ
    "\u011f": "ǧ",  # g with breve (ğ), typed for g with caron
    "\u011e": "Ǧ",  # capital G with breve
    "\u021b": "ţ",  # t with comma below (ț), typed for t with cedilla
    # seen in Béjaïa theses in phonetic notation (10 Nov 2026):
    "\u04d9": "ə",  # Cyrillic small schwa (ә) -> Latin small schwa
    "\u04d8": "Ə",  # Cyrillic capital schwa
}


def nfc(text: str) -> str:
    """Canonical composition: 'd' + U+0323 becomes 'ḍ' (one code point)."""
    return unicodedata.normalize("NFC", text)


def fold_homoglyphs(text: str) -> str:
    return "".join(HOMOGLYPHS.get(ch, ch) for ch in text)


# Punctuation around which authors type spaces inconsistently ("ugar ." vs
# "ugar."). Found on the VALIDATION documents (9 Nov 2026): about half of the
# lines still wrong after OCR differ from the text layer only by such spaces.
PUNCT_SPACE = re.compile(r"\s*([,.;:!?«»“”\"()\[\]\-–—’'])\s*")


def normalise(text: str, mode: str = "strict", punct_space: bool = False) -> str:
    """strict / lenient as above. punct_space=True also deletes every space
    touching a punctuation mark, in BOTH reference and hypothesis: the score
    then ignores typographic spacing conventions, not words."""
    if mode not in {"strict", "lenient"}:
        raise ValueError(f"unknown mode {mode!r}")
    text = nfc(text).replace("\u2026", "...")  # ellipsis = 3 dots (Unicode compatibility mapping)
    if mode == "lenient":
        text = fold_homoglyphs(text)
    # collapse runs of whitespace, strip ends: layout spaces are not content
    text = " ".join(text.split())
    if punct_space:
        text = PUNCT_SPACE.sub(r"\1", text)
    return text


def strip_diacritics(text: str) -> str:
    """Base-letter view: ḍ->d, č->c, ɛ stays ɛ (it is a letter, not a mark)."""
    decomposed = unicodedata.normalize("NFD", text)
    kept = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", kept)


def script_of(ch: str) -> str:
    if ch in TIFINAGH:
        return "Tfng"
    if ch.isspace() or not ch.isalpha():
        return "Common"
    name = unicodedata.name(ch, "")
    if "LATIN" in name or ch in SPECIAL:
        return "Latn"
    if "GREEK" in name:
        return "Grek"
    if "CYRILLIC" in name:
        return "Cyrl"
    if "ARABIC" in name:
        return "Arab"
    return "Other"


def uncovered_chars(text: str, vocabulary: set[str]) -> set[str]:
    """Characters of the ground truth that a model vocabulary cannot emit.

    Any such character puts a hard floor under the achievable CER (lesson of
    the Sorani-Kurdish OCR work): check it before training, not after.
    """
    return {ch for ch in nfc(text) if not ch.isspace() and ch not in vocabulary}
