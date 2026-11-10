"""Image-only (96 dpi JPEG) edition of a Kabyle novel vs its born-digital twin (same 96 pages).
Page-level CER, single-column text. Usage: run_twin.py MODEL..."""
import sys, json, pathlib, subprocess, os, random
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.metrics import count, rates, Counts
from kabocr_eval.charset import normalise
pages = sorted(pathlib.Path("img").glob("p-*.png"), key=lambda p: int(p.stem.split("-")[1]))
# Scope fixed by page TYPE, not by error: the novel body (pp. 9-85). pp. 86-96 = French bibliography / back matter.
pages = [p for p in pages if os.environ.get("ALLPAGES") or 9 <= int(p.stem.split("-")[1]) <= 85]
res = json.load(open("results.json")) if pathlib.Path("results.json").exists() else {}
for M in sys.argv[1:]:
    od = pathlib.Path("pred") / M; od.mkdir(parents=True, exist_ok=True)
    per = {}
    for p in pages:
        o = od / (p.stem + ".txt")
        if not o.exists():
            h = subprocess.run(["tesseract", str(p), "-", "-l", M, "--tessdata-dir", "/home/claude/pilot/tessdata", "--dpi", "96"],
                               capture_output=True, text=True, env={**os.environ, "OMP_THREAD_LIMIT": "1"}).stdout
            o.write_text(h)
        g = normalise((pathlib.Path("gt") / (p.stem + ".txt")).read_text().replace("<", "\u2026"), "lenient")  # "<" in this text layer = the printed ellipsis (checked on page images)
        per[p.stem] = {m: count(g, o.read_text(), mode=m.replace("_ps", ""), punct_space=m.endswith("_ps")) for m in ("strict", "strict_ps")}
    for m in ("strict", "strict_ps"):
        ds = [per[k][m] for k in per]; r = rates(sum(ds, Counts()))
        rng = random.Random(0); bs = sorted(rates(sum((ds[rng.randrange(len(ds))] for _ in ds), Counts()))["CER"] for _ in range(1000))
        r["CER_CI"] = [bs[25], bs[974]]; r["pages"] = len(ds)
        res[f"{M}|{m}"] = r
        print(f"{M:<12}{m:<10} CER {100*r['CER']:5.2f} [{100*bs[25]:.2f};{100*bs[974]:.2f}] WER {100*r['WER']:5.2f} DCER {100*r['DCER']:5.2f}", flush=True)
    json.dump(res, open("results.json", "w"), indent=1)
    json.dump({k: {m: rates(v)["CER"] for m, v in d.items()} for k, d in per.items()}, open(f"perpage_{M}.json", "w"))
