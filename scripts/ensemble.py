"""System combination by minimum-Bayes-risk (MBR) line selection, plus character voting.
MBR: for each line, keep the hypothesis with the smallest weighted sum of edit distances to the others.
Weights / member set are chosen on the VALIDATION theses only, then applied once to the test sets."""
import sys, json, pathlib, itertools, collections
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.metrics import count, rates, Counts, edit_distance
from kabocr_eval.charset import normalise
from kabocr_eval.gtquality import reasons

def mbr(hyps, w):
    best, bs = None, None
    for i, h in enumerate(hyps):
        sc = sum(w[j] * edit_distance(list(h), list(o)) for j, o in enumerate(hyps) if j != i) - 1e-6 * w[i]
        if bs is None or sc < bs: best, bs = h, sc
    return best

# ---- validation
V = pathlib.Path("/home/claude/spacefix"); png = [l.strip() for l in open(V / "val_png.txt") if l.strip()]
gt = [normalise(open(p.replace(".png", ".gt.txt")).read(), "lenient") for p in png]
VAL = {"kabv4": V / "val_v4.txt", "kabv5c": V / "val_kabv5c.txt", "kablibre": V / "val_kablibre.txt", "kabhamo": V / "val_kabhamo.txt"}
vh = {M: [x.strip() for x in f.read_text().split("\f")][:len(png)] for M, f in VAL.items()}
def score(lines_h):
    c = Counts()
    for g, h in zip(gt, lines_h): c += count(g, h)
    return 100 * rates(c)["CER"]
res = {M: score(vh[M]) for M in VAL}
print("validation single:", {k: round(v, 3) for k, v in res.items()})
best = None
for members in [("kabv4", "kabv5c", "kablibre"), ("kabv4", "kabv5c", "kabhamo"), ("kabv4", "kabv5c", "kablibre", "kabhamo")]:
    for w in itertools.product([1, 2, 3], repeat=len(members)):
        comb = [mbr([vh[M][i] for M in members], w) for i in range(len(png))]
        s = score(comb)
        if best is None or s < best[0]: best = (s, members, w)
print("validation best combination:", best)
s0, members, w = best
# ---- test, applied once
out = {"validation": {"single": res, "combo": {"members": members, "weights": w, "CER": s0}}}
for s in ("set_bou", "set_bej", "set_liv"):
    S = pathlib.Path("/home/claude/ood") / s; meta = json.load(open(S / "meta.json"))
    R = {l["id"]: reasons((S / "lines" / f"{l['id']}.gt.txt").read_text()) for l in meta["lines"]}
    legacy = {d for d, n in collections.Counter(l["doc"] for l in meta["lines"] if "legacy_font_encoding" in R[l["id"]]).items() if n >= 3}
    keep = [l for l in meta["lines"] if not R[l["id"]] and l["doc"] not in legacy and l["doc"] != "bej033"]
    H = {M: json.load(open(S / "pred" / M / "all.txt")) for M in members}
    c = Counts(); cs = {M: Counts() for M in members}; per_doc = collections.defaultdict(Counts); per_doc_v4 = collections.defaultdict(Counts)
    for l in keep:
        g = normalise((S / "lines" / f"{l['id']}.gt.txt").read_text(), "lenient")
        h = mbr([H[M][l["id"]] for M in members], w); x = count(g, h); c += x; per_doc[l["doc"]] += x
        for M in members: cs[M] += count(g, H[M][l["id"]])
        per_doc_v4[l["doc"]] += count(g, H["kabv4"][l["id"]])
    from kabocr_eval.metrics import paired_permutation
    docs = sorted(per_doc)
    p = paired_permutation([per_doc[d] for d in docs], [per_doc_v4[d] for d in docs], "CER", n=5000)
    out[s] = {"combo": round(100 * rates(c)["CER"], 3), **{M: round(100 * rates(cs[M])["CER"], 3) for M in members}, "p_vs_v4": p,
              "docs_better": sum(rates(per_doc[d])["CER"] < rates(per_doc_v4[d])["CER"] for d in docs), "docs": len(docs)}
    print(s, out[s])
json.dump(out, open("/home/claude/analysis/ensemble.json", "w"), indent=1)
