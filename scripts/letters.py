"""Per-letter analysis of Kabyle-specific letters on the three main test sets (all kept lines).
For each reference special letter: correct / read as its base letter / other / deleted.
Spurious: special letters output where the reference has another character."""
import sys, json, pathlib, collections, unicodedata
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.metrics import align
from kabocr_eval.charset import normalise, SPECIAL, strip_diacritics
from kabocr_eval.gtquality import reasons
MODELS = ["Latin_fast", "kab_aitbad", "kabhamo", "kablibre", "kabv4", "kabv5c"]
BASE = {"ɛ": "e", "ɣ": "g", "Ɛ": "E", "Ɣ": "G"}
def base(c):
    return BASE.get(c, strip_diacritics(c))
stat = {M: collections.defaultdict(collections.Counter) for M in MODELS}
spur = {M: collections.Counter() for M in MODELS}
conf = {M: collections.Counter() for M in MODELS}
for s in ("set_bou", "set_bej", "set_liv"):
    S = pathlib.Path("/home/claude/ood") / s; meta = json.load(open(S / "meta.json"))
    R = {l["id"]: reasons((S / "lines" / f"{l['id']}.gt.txt").read_text()) for l in meta["lines"]}
    legacy = {d for d, n in collections.Counter(l["doc"] for l in meta["lines"] if "legacy_font_encoding" in R[l["id"]]).items() if n >= 3}
    keep = [l for l in meta["lines"] if not R[l["id"]] and l["doc"] not in legacy and l["doc"] != "bej033"]
    for M in MODELS:
        h = json.load(open(S / "pred" / M / "all.txt"))
        for l in keep:
            g = normalise((S / "lines" / f"{l['id']}.gt.txt").read_text(), "lenient"); y = normalise(h.get(l["id"], ""), "strict")
            for op, r, x in align(list(g), list(y)):
                if r is not None and r in SPECIAL and r != "ʷ":
                    k = r.lower()
                    if op == "=": stat[M][k]["ok"] += 1
                    elif op == "D": stat[M][k]["deleted"] += 1
                    elif x is not None and base(r).lower() == x.lower(): stat[M][k]["base"] += 1; conf[M][(r, x)] += 1
                    else: stat[M][k]["other"] += 1; conf[M][(r, x)] += 1
                elif x is not None and x in SPECIAL and (r is None or r != x):
                    spur[M][(r or "∅", x)] += 1
out = {M: {k: dict(v) for k, v in stat[M].items()} for M in MODELS}
json.dump({"stat": out, "spur": {M: [[a, b, n] for (a, b), n in spur[M].most_common(10)] for M in MODELS},
           "conf": {M: [[a, b, n] for (a, b), n in conf[M].most_common(10)] for M in MODELS}}, open("/home/claude/analysis/letters.json", "w"), ensure_ascii=False, indent=1)
L = "ɛɣčǧḍḥṛṣṭẓţ"
print("letter   n   " + "  ".join(f"{M[:8]:>8}" for M in MODELS))
for k in L:
    n = sum(stat["kabv4"][k].values())
    print(f"{k}  {n:5d} " + "  ".join(f"{100*(1-stat[M][k]['ok']/max(1,sum(stat[M][k].values()))):8.1f}" for M in MODELS))
for M in ("kab_aitbad", "kabhamo", "kabv4"):
    print(M, "top confusions", conf[M].most_common(6), "top spurious", spur[M].most_common(6))
