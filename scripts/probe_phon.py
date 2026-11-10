"""Find Béjaïa theses (never used in test or training) that use phonetic notation (ə ṯ ḏ ḇ ḵ ǥ æ)."""
import subprocess, urllib.parse, pathlib, json, random
PH = set("əƏṯṮḏḎḇḆḵḴǥǤæÆ")
used = set(l.strip() for l in open("/home/claude/ood/bej_pick.txt"))
allp = [l.strip() for l in open("/home/claude/ood/bejaia.txt") if l.strip() and l.strip() not in used]
random.Random(7).shuffle(allp)
base = "https://huggingface.co/datasets/taqbaylit/bejaia/resolve/main/"
out = []
for i, p in enumerate(allp[:200]):
    f = pathlib.Path(f"p{i:03d}.pdf")
    subprocess.run(["curl", "-sL", "-m", "120", "-o", str(f), base + urllib.parse.quote(p)])
    t = subprocess.run(["pdftotext", str(f), "-"], capture_output=True, text=True).stdout
    n = sum(ch in PH for ch in t)
    rec = {"id": f.stem, "src": p, "phon": n, "chars": len(t)}
    print(json.dumps(rec, ensure_ascii=False), flush=True); out.append(rec)
    if n < 200: f.unlink()
json.dump(out, open("probe_phon.json", "w"), ensure_ascii=False)
