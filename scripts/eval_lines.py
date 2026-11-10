"""Line-level evaluation (ground-truth segmentation): no reading-order noise.
usage: eval_lines.py SET_DIR MODEL [MODEL...]  -> prints corpus metrics + doc-level bootstrap CI"""
import sys, json, pathlib, subprocess, os, random
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.metrics import count, rates, Counts
from kabocr_eval.charset import script_of, normalise
from kabocr_eval.gtquality import reasons
import collections
def in_scope(g):
    return all(script_of(c) in ("Latn", "Common") for c in normalise(g, "lenient")) and not any(0x2460 <= ord(c) <= 0x27BF for c in g)
S = pathlib.Path(sys.argv[1]); meta = json.load(open(S / "meta.json"))
ids = [l["id"] for l in meta["lines"]]; doc = {l["id"]: l["doc"] for l in meta["lines"]}
GT = {i: (S / "lines" / f"{i}.gt.txt").read_text().strip() for i in ids}
R = {i: reasons(GT[i]) for i in ids}
legacy_docs = {d for d, n in collections.Counter(doc[i] for i in ids if "legacy_font_encoding" in R[i]).items() if n >= 3}
KEEP = [i for i in ids if not R[i] and doc[i] not in legacy_docs]
excl = collections.Counter(r for i in ids for r in R[i]); excl["legacy_doc"] = sum(1 for i in ids if doc[i] in legacy_docs)
print(f"{S.name}: {len(KEEP)}/{len(ids)} lignes gardées ; exclusions {dict(excl)} ; documents à police ancienne : {sorted(legacy_docs)}", flush=True)
res = {}
for M in sys.argv[2:]:
    outd = S / "pred" / M; outd.mkdir(parents=True, exist_ok=True)
    cache = outd / "all.txt"
    if not cache.exists():
        chunks = [ids[i::2] for i in range(2)]
        procs = []
        for k, ch in enumerate(chunks):
            lst = outd / f"list{k}.txt"; lst.write_text("\n".join(str(S / "lines" / f"{i}.png") for i in ch) + "\n")
            procs.append(subprocess.Popen(["tesseract", str(lst), str(outd / f"out{k}"), "-l", M, "--tessdata-dir", "/home/claude/pilot/tessdata", "--psm", "7"],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env={**os.environ, "OMP_THREAD_LIMIT": "1"}))
        for p in procs: p.wait()
        hyp = {}
        for k, ch in enumerate(chunks):
            parts = (outd / f"out{k}.txt").read_text().split("\f")
            for i, h in zip(ch, parts): hyp[i] = h.strip()
        json.dump(hyp, open(cache, "w"), ensure_ascii=False)
    hyp = json.load(open(cache))
    for mode in ("strict", "lenient", "strict_ps"):
        per_doc = {}
        kept = 0
        for i in KEEP:
            gt = normalise(GT[i], "lenient")  # GT cleaning: fold homoglyphs typed by authors
            kept += 1
            per_doc[doc[i]] = per_doc.get(doc[i], Counts()) + count(gt, hyp.get(i, ""), mode=mode.replace("_ps", ""), punct_space=mode.endswith("_ps"))
        tot = sum(per_doc.values(), Counts()); r = rates(tot)
        rng = random.Random(0); ds = list(per_doc.values()); bs = []
        for _ in range(1000):
            bs.append(rates(sum((ds[rng.randrange(len(ds))] for _ in ds), Counts()))["CER"])
        bs.sort(); r["CER_CI"] = [bs[25], bs[974]]
        r["lines_kept"] = kept; r["lines_total"] = len(ids)
        res[f"{M}|{mode}"] = r
        if mode in ("strict", "strict_ps"):
            print(f"[{mode}] ", end="")
            print(f"{S.name:<8}{M:<14} n={kept}/{len(ids)} CER {100*r['CER']:5.2f} [{100*bs[25]:4.2f};{100*bs[974]:4.2f}]  WER {100*r['WER']:5.2f}  DCER {100*r['DCER']:5.2f} (perdues {100*r['DCER_miss']:4.1f} / inventées {100*r['DCER_spur']:4.1f})", flush=True)
old = json.load(open(S / "results_lines.json")) if (S / "results_lines.json").exists() else {}
old.update(res); json.dump(old, open(S / "results_lines.json", "w"), indent=1)
