"""Character-level ROVER with v4 as pivot: each other system is aligned to the pivot; at each pivot position
the pivot character is replaced only if ALL other systems agree on the same alternative. Tuned/validated on validation."""
import sys, json, pathlib, collections
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.metrics import count, rates, Counts, align
from kabocr_eval.charset import normalise
def rover(piv, others):
    alts = []
    for o in others:
        a = collections.defaultdict(str)  # pivot index -> replacement ('' = delete); insertions attached to previous index
        i = -1
        for op, r, h in align(list(piv), list(o)):
            if op == "=": i += 1; a[i] += "\x00" + r
            elif op == "S": i += 1; a[i] += "\x00" + h
            elif op == "D": i += 1; a[i] += "\x00"
            else: a[i] += h
        alts.append(a)
    out = []
    for i in range(-1, len(piv)):
        mine = ("\x00" + piv[i]) if i >= 0 else ""
        cand = [a.get(i, mine if i >= 0 else "") for a in alts]
        out.append(cand[0] if len(set(cand)) == 1 and cand[0] != mine else mine)
    return "".join(out).replace("\x00", "")
V = pathlib.Path("/home/claude/spacefix"); png = [l.strip() for l in open(V / "val_png.txt") if l.strip()]
gt = [normalise(open(p.replace(".png", ".gt.txt")).read(), "lenient") for p in png]
vh = {M: [x.strip() for x in (V / f).read_text().split("\f")][:len(png)] for M, f in {"kabv4": "val_v4.txt", "kabv5c": "val_kabv5c.txt", "kablibre": "val_kablibre.txt", "kabhamo": "val_kabhamo.txt"}.items()}
def score(hs):
    c = Counts()
    for g, h in zip(gt, hs): c += count(g, h)
    return round(100 * rates(c)["CER"], 3)
print("v4", score(vh["kabv4"]))
for others in (["kabv5c", "kablibre"], ["kabv5c", "kabhamo"], ["kabv5c", "kablibre", "kabhamo"]):
    print(others, score([rover(vh["kabv4"][i], [vh[o][i] for o in others]) for i in range(len(png))]))
