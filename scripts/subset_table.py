"""Slow baselines (Feraoun, open VLMs) on the fixed 1-in-32 subset; all systems scored on the SAME lines."""
import sys, json, pathlib, collections, random
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.metrics import count, rates, Counts
from kabocr_eval.charset import normalise
from kabocr_eval.gtquality import reasons
MODELS = ["Latin_fast", "easyocr", "Feraoun-36M", "Feraoun-Pro", "GOT-OCR-2.0", "Qwen2-VL-2B", "kab_aitbad", "kabhamo", "kablibre", "kabv4", "kabv5c"]
out = {}
for s in ["set_bou", "set_bej", "set_liv"]:
    S = pathlib.Path(s); meta = json.load(open(S / "meta.json"))
    L = meta["lines"][::32]
    ids = [l["id"] for l in meta["lines"]]; doc = {l["id"]: l["doc"] for l in meta["lines"]}
    GT = {i: (S / "lines" / f"{i}.gt.txt").read_text().strip() for i in ids}; R = {i: reasons(GT[i]) for i in ids}
    legacy = {d for d, n in collections.Counter(doc[i] for i in ids if "legacy_font_encoding" in R[i]).items() if n >= 3}
    keep = [l["id"] for l in L if not R[l["id"]] and doc[l["id"]] not in legacy and not (s == "set_bej" and doc[l["id"]] == "bej033")]
    out[s] = {"lines": len(keep)}
    for M in MODELS:
        f = S / "pred" / M / "all.txt"
        if not f.exists(): continue
        h = json.load(open(f))
        if not all(i in h for i in keep): continue
        d = collections.defaultdict(Counts)
        for i in keep: d[doc[i]] += count(normalise(GT[i], "lenient"), h[i], mode="strict")
        r = rates(sum(d.values(), Counts())); out[s][M] = {"CER": round(100 * r["CER"], 2), "DCER": round(100 * r["DCER"], 2), "WER": round(100 * r["WER"], 2)}
    print(s, out[s])
json.dump(out, open("subset_table.json", "w"), indent=1)
