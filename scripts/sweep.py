"""Robustness sweep: same line crops, controlled degradations, several levels each.
Lines: every 8th quality-kept line of Bouira and Books test sets (fixed rule). Models: public best + ours."""
import sys, json, pathlib, subprocess, os, io, random, collections
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.metrics import count, rates, Counts
from kabocr_eval.charset import normalise
from kabocr_eval.gtquality import reasons
OUT = pathlib.Path("/home/claude/robust"); MODELS = sys.argv[1:] or ["kabhamo", "kablibre", "kabv4", "kabv5c"]
lines = []
for s in ("set_bou", "set_liv"):
    S = pathlib.Path("/home/claude/ood") / s; meta = json.load(open(S / "meta.json"))
    R = {l["id"]: reasons((S / "lines" / f"{l['id']}.gt.txt").read_text()) for l in meta["lines"]}
    legacy = {d for d, n in collections.Counter(l["doc"] for l in meta["lines"] if "legacy_font_encoding" in R[l["id"]]).items() if n >= 3}
    keep = [l for l in meta["lines"] if not R[l["id"]] and l["doc"] not in legacy][::8]
    lines += [(s, l["id"], S / "lines" / f"{l['id']}.png", normalise((S / "lines" / f"{l['id']}.gt.txt").read_text(), "lenient")) for l in keep]
def deg(img, kind, lv, rng):
    if kind == "clean": return img
    if kind == "res":   # scan at lower resolution, then shown at original size
        w, h = img.size; small = img.resize((max(1, int(w * lv)), max(1, int(h * lv))), Image.BILINEAR); return small.resize((w, h), Image.BILINEAR)
    if kind == "blur": return img.filter(ImageFilter.GaussianBlur(lv))
    if kind == "noise":
        a = np.asarray(img, dtype=np.float32) + np.random.default_rng(rng.randrange(10**9)).normal(0, lv, (img.height, img.width)); return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if kind == "jpeg":
        b = io.BytesIO(); img.save(b, "JPEG", quality=lv); return Image.open(io.BytesIO(b.getvalue())).convert("L")
CONDS = [("clean", 0), ("res", .5), ("res", .33), ("res", .25), ("blur", 1.0), ("blur", 1.5), ("blur", 2.0), ("noise", 15), ("noise", 30), ("noise", 45), ("jpeg", 30), ("jpeg", 10)]
res = json.load(open(OUT / "results.json")) if (OUT / "results.json").exists() else {}
for kind, lv in CONDS:
    d = OUT / f"img_{kind}_{lv}"; d.mkdir(exist_ok=True); rng = random.Random(1)
    for s, i, p, g in lines:
        f = d / f"{s}__{i}.png"
        if not f.exists(): deg(Image.open(p).convert("L"), kind, lv, rng).save(f)
    lst = d / "list.txt"; lst.write_text("\n".join(str(d / f"{s}__{i}.png") for s, i, p, g in lines) + "\n")
    for M in MODELS:
        key = f"{kind}|{lv}|{M}"
        if key in res: continue
        o = d / f"out_{M}"
        subprocess.run(["tesseract", str(lst), str(o), "-l", M, "--tessdata-dir", "/home/claude/pilot/tessdata", "--psm", "7"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env={**os.environ, "OMP_THREAD_LIMIT": "1"})
        hyp = (o.parent / (o.name + ".txt")).read_text().split("\f")
        c = Counts()
        for (s, i, p, g), h in zip(lines, hyp): c += count(g, h.strip())
        r = rates(c); res[key] = {"CER": round(100 * r["CER"], 2), "DCER": round(100 * r["DCER"], 2), "n": len(lines)}
        print(key, res[key], flush=True); json.dump(res, open(OUT / "results.json", "w"), indent=1)
