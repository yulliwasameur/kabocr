"""Error metrics for Kabyle OCR, with confidence intervals and paired tests."""
from __future__ import annotations

import random
from dataclasses import dataclass, asdict

from .charset import SPECIAL, normalise, script_of, strip_diacritics


try:  # fast path (C implementation); same alignment semantics
    from rapidfuzz.distance import Levenshtein as _Lev
except ImportError:  # pragma: no cover
    _Lev = None


def align(ref: list, hyp: list) -> list[tuple[str, object, object]]:
    """Levenshtein alignment. Returns ops: ('=', r, h) ('S', r, h) ('D', r, None) ('I', None, h)."""
    if _Lev is not None:
        ops = []
        for tag, i1, i2, j1, j2 in _Lev.opcodes(ref, hyp):
            if tag == "equal":
                ops += [("=", ref[i], hyp[j]) for i, j in zip(range(i1, i2), range(j1, j2))]
            elif tag == "replace":
                ops += [("S", ref[i], hyp[j]) for i, j in zip(range(i1, i2), range(j1, j2))]
            elif tag == "delete":
                ops += [("D", ref[i], None) for i in range(i1, i2)]
            else:
                ops += [("I", None, hyp[j]) for j in range(j1, j2)]
        return ops
    return _align_py(ref, hyp)


def _align_py(ref: list, hyp: list) -> list[tuple[str, object, object]]:
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        ri = ref[i - 1]
        row, prev = d[i], d[i - 1]
        for j in range(1, m + 1):
            cost = 0 if ri == hyp[j - 1] else 1
            row[j] = min(prev[j] + 1, row[j - 1] + 1, prev[j - 1] + cost)
    ops = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]):
            ops.append(("=" if ref[i - 1] == hyp[j - 1] else "S", ref[i - 1], hyp[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            ops.append(("D", ref[i - 1], None))
            i -= 1
        else:
            ops.append(("I", None, hyp[j - 1]))
            j -= 1
    return ops[::-1]


def edit_distance(ref: list, hyp: list) -> int:
    return sum(op != "=" for op, _, _ in align(ref, hyp))


@dataclass
class Counts:
    char_err: int = 0
    char_ref: int = 0
    word_err: int = 0
    word_ref: int = 0
    special_err: int = 0
    special_ref: int = 0
    special_miss: int = 0      # Kabyle letter lost or replaced
    special_spur: int = 0      # Kabyle letter produced where there was none
    base_err: int = 0          # errors after diacritic stripping
    inserted: int = 0          # inserted characters (hallucination proxy)
    wrong_script: int = 0      # hypothesis letters outside expected script
    hyp_letters: int = 0

    def __add__(self, other: "Counts") -> "Counts":
        return Counts(*(a + b for a, b in zip(asdict(self).values(), asdict(other).values())))


def count(ref: str, hyp: str, mode: str = "strict", expected_script: str = "Latn",
          punct_space: bool = False) -> Counts:
    ref_n, hyp_n = normalise(ref, mode, punct_space), normalise(hyp, mode, punct_space)
    ops = align(list(ref_n), list(hyp_n))
    c = Counts()
    c.char_ref = len(ref_n)
    c.char_err = sum(op != "=" for op, _, _ in ops)
    c.inserted = sum(op == "I" for op, _, _ in ops)
    for op, r, h in ops:
        if r is not None and r in SPECIAL:
            c.special_ref += 1
            if op != "=":
                c.special_err += 1
                c.special_miss += 1
        elif op in {"I", "S"} and h in SPECIAL:
            c.special_err += 1  # spurious special letter (t read as ṭ, etc.)
            c.special_spur += 1
    rw, hw = ref_n.split(), hyp_n.split()
    c.word_ref = len(rw)
    c.word_err = edit_distance(rw, hw)
    c.base_err = edit_distance(list(strip_diacritics(ref_n)), list(strip_diacritics(hyp_n)))
    for ch in hyp_n:
        s = script_of(ch)
        if s in {"Common"}:
            continue
        c.hyp_letters += 1
        if s != expected_script:
            c.wrong_script += 1
    return c


def rates(c: Counts) -> dict[str, float]:
    def r(a, b):
        return a / b if b else 0.0
    return {
        "CER": r(c.char_err, c.char_ref),
        "WER": r(c.word_err, c.word_ref),
        "DCER": r(c.special_err, c.special_ref),         # errors on Kabyle-specific letters
        "DCER_miss": r(c.special_miss, c.special_ref),   # part due to lost letters
        "DCER_spur": r(c.special_spur, c.special_ref),   # part due to invented letters
        "BaseCER": r(c.base_err, c.char_ref),            # CER once diacritics are removed
        "InsRate": r(c.inserted, c.char_ref),
        "WrongScript": r(c.wrong_script, c.hyp_letters),
    }


def corpus(pairs: list[tuple[str, str]], **kw) -> Counts:
    total = Counts()
    for ref, hyp in pairs:
        total = total + count(ref, hyp, **kw)
    return total


def bootstrap_ci(per_page: list[Counts], metric: str = "CER", n: int = 2000,
                 alpha: float = 0.05, seed: int = 0) -> tuple[float, float, float]:
    """Page-level bootstrap (pages are the sampling unit, not characters)."""
    rng = random.Random(seed)
    point = rates(sum(per_page, Counts()))[metric]
    stats = []
    k = len(per_page)
    for _ in range(n):
        sample = [per_page[rng.randrange(k)] for _ in range(k)]
        stats.append(rates(sum(sample, Counts()))[metric])
    stats.sort()
    lo = stats[int(alpha / 2 * n)]
    hi = stats[int((1 - alpha / 2) * n) - 1]
    return point, lo, hi


def paired_permutation(a: list[Counts], b: list[Counts], metric: str = "CER",
                       n: int = 5000, seed: int = 0) -> float:
    """Two-sided p-value that systems A and B have the same corpus-level metric."""
    assert len(a) == len(b)
    rng = random.Random(seed)
    obs = abs(rates(sum(a, Counts()))[metric] - rates(sum(b, Counts()))[metric])
    hits = 0
    for _ in range(n):
        xa, xb = Counts(), Counts()
        for pa, pb in zip(a, b):
            if rng.random() < 0.5:
                pa, pb = pb, pa
            xa, xb = xa + pa, xb + pb
        if abs(rates(xa)[metric] - rates(xb)[metric]) >= obs:
            hits += 1
    return (hits + 1) / (n + 1)


def holm(pvalues: dict[str, float], alpha: float = 0.05) -> dict[str, bool]:
    """Holm-Bonferroni: which comparisons stay significant."""
    order = sorted(pvalues.items(), key=lambda kv: kv[1])
    m, out, still = len(order), {}, True
    for i, (name, p) in enumerate(order):
        still = still and p <= alpha / (m - i)
        out[name] = still
    return out
