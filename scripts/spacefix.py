"""Lexicon-based space correction for Kabyle OCR output.

Idea (simple, explainable): Kabyle OCR loses or adds spaces in justified text.
- a token unknown to the lexicon that splits into two frequent known words -> split
- two adjacent tokens whose concatenation is a frequent known word, while one of
  them is unknown -> merge
The lexicon is built ONLY from training ground truth (+ Wikipedia sentences),
never from test text. Thresholds are tuned on the validation documents only.
"""
from __future__ import annotations
import re, collections, json, sys, unicodedata

TOK = re.compile(r"^([^\w]*)(.*?)([^\w]*)$", re.UNICODE)


def norm(w: str) -> str:
    return unicodedata.normalize("NFC", w).lower()


def build_lexicon(paths):
    c = collections.Counter()
    for p in paths:
        for line in open(p, encoding="utf-8"):
            for w in line.split():
                core = TOK.match(w).group(2)
                if core:
                    c[norm(core)] += 1
    return c


class SpaceFixer:
    def __init__(self, lex, min_part=3, min_freq=2, min_merge=3):
        self.lex, self.min_part, self.min_freq, self.min_merge = lex, min_part, min_freq, min_merge

    def known(self, w, f=1):
        return self.lex.get(norm(w), 0) >= f

    def split(self, tok):
        pre, core, post = TOK.match(tok).groups()
        if len(core) < 2 * self.min_part or self.known(core) or not core.isalpha() and "-" not in core:
            return [tok]
        best = None
        for i in range(self.min_part, len(core) - self.min_part + 1):
            a, b = core[:i], core[i:]
            fa, fb = self.lex.get(norm(a), 0), self.lex.get(norm(b), 0)
            if fa >= self.min_freq and fb >= self.min_freq:
                sc = min(fa, fb)
                if best is None or sc > best[0]:
                    best = (sc, a, b)
        if best is None:
            return [tok]
        return [pre + best[1], best[2] + post]

    def fix(self, line: str) -> str:
        toks = line.split()
        # merges first
        out, i = [], 0
        while i < len(toks):
            if i + 1 < len(toks):
                a, b = toks[i], toks[i + 1]
                pa, ca, sa = TOK.match(a).groups()
                pb, cb, sb = TOK.match(b).groups()
                if not sa and not pb and ca and cb and (not self.known(ca) or not self.known(cb)) \
                        and self.lex.get(norm(ca + cb), 0) >= self.min_merge:
                    out.append(pa + ca + cb + sb); i += 2; continue
            out.append(toks[i]); i += 1
        res = []
        for t in out:
            res.extend(self.split(t))
        return " ".join(res)
