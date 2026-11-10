import sys, json, pathlib, collections, random
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.metrics import count, rates, Counts, paired_permutation
from kabocr_eval.charset import normalise
from kabocr_eval.gtquality import reasons
MODELS = ["Latin_fast", "easyocr", "kab_aitbad", "kabhamo", "kablibre", "kabft2", "kabv3", "kabv4", "kabs1", "kabs2", "kabs3", "kabv5c"]
out = {}
for s, excl in [("set_bou", set()), ("set_bej", set()), ("set_bej", {"bej033"}), ("set_liv", set()), ("set_aya", set())]:
    S = pathlib.Path(s); meta = json.load(open(S / "meta.json"))
    ids = [l["id"] for l in meta["lines"]]; doc = {l["id"]: l["doc"] for l in meta["lines"]}
    GT = {i: (S / "lines" / f"{i}.gt.txt").read_text().strip() for i in ids}; R = {i: reasons(GT[i]) for i in ids}
    legacy = {d for d, n in collections.Counter(doc[i] for i in ids if "legacy_font_encoding" in R[i]).items() if n >= 3}
    keep = [i for i in ids if not R[i] and doc[i] not in legacy and doc[i] not in excl]
    per = {}
    for M in MODELS:
        h = json.load(open(S / "pred" / M / "all.txt")); d = collections.defaultdict(Counts); dp = collections.defaultdict(Counts)
        for i in keep:
            g = normalise(GT[i], "lenient")  # clean GT homoglyphs typed by authors; hypothesis scored STRICT
            d[doc[i]] += count(g, h.get(i, ""), mode="strict")
            dp[doc[i]] += count(g, h.get(i, ""), mode="strict", punct_space=True)
        per[M] = d; per[M + "|ps"] = dp
    docs = sorted(per[MODELS[0]])
    key = s + ("-" + "-".join(sorted(excl)) if excl else "")
    out[key] = {"lines": len(keep), "docs": len(docs)}
    for M in MODELS:
        r = rates(sum(per[M].values(), Counts()))
        out[key][M] = {k: round(100 * r[k], 2) for k in ("CER", "WER", "DCER", "DCER_miss", "DCER_spur")}
        out[key][M]["CER_ps"] = round(100 * rates(sum(per[M + "|ps"].values(), Counts()))["CER"], 2)
        rng = random.Random(0); ds = list(per[M].values())
        bs = sorted(rates(sum((ds[rng.randrange(len(ds))] for _ in ds), Counts()))["CER"] for _ in range(1000))
        out[key][M]["CER_CI"] = [round(100 * bs[25], 2), round(100 * bs[974], 2)]
    a = [per["kabv4"][d] for d in docs]; b = [per["kab_aitbad"][d] for d in docs]
    out[key]["p_v4_vs_aitbad_CER"] = paired_permutation(a, b, "CER", n=5000) if len(docs) > 1 else None
    out[key]["p_v4_vs_aitbad_DCER"] = paired_permutation(a, b, "DCER", n=5000) if len(docs) > 1 else None
    out[key]["docs_better_v4"] = sum(rates(x)["CER"] < rates(y)["CER"] for x, y in zip(a, b))
    c = [per["kabhamo"][d] for d in docs]
    out[key]["p_v4_vs_hamo_CER"] = paired_permutation(a, c, "CER", n=5000) if len(docs) > 1 else None
    out[key]["docs_better_v4_vs_hamo"] = sum(rates(x)["CER"] < rates(y)["CER"] for x, y in zip(a, c))
    l = [per["kablibre"][d] for d in docs]
    out[key]["p_libre_vs_hamo_CER"] = paired_permutation(l, c, "CER", n=5000) if len(docs) > 1 else None
    out[key]["docs_better_libre_vs_hamo"] = sum(rates(x)["CER"] < rates(y)["CER"] for x, y in zip(l, c))
    print(key, out[key]["lines"], "lignes", len(docs), "docs |", " ".join(f"{M}={out[key][M]['CER']}" for M in MODELS), "| p", out[key]["p_v4_vs_aitbad_CER"], "| docs mieux", out[key]["docs_better_v4"], "/", len(docs), "| vs hamo p", out[key]["p_v4_vs_hamo_CER"], out[key]["docs_better_v4_vs_hamo"], "| libre vs hamo p", out[key]["p_libre_vs_hamo_CER"], out[key]["docs_better_libre_vs_hamo"])
json.dump(out, open("final_table.json", "w"), indent=1)
