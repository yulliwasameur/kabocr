"""Build the real-scan pre-annotation pool for KabOCR-Bench.
Source: Timmuzgha N°03-09 (Kabyle/French magazine, physical 300 dpi bilevel scans, taqbaylit/adlis-pdfs).
Steps: render pages -> tesseract layout (kabv4, tsv) -> line crops -> keep lines that look Kabyle
(>= 50 % of words known from the TRAINING lexicon, French stop-words excluded) -> stratified sample.
Pre-annotation = kabv4 output. The 20 % 'double' lines are later re-typed from an EMPTY field."""
import sys, subprocess, pathlib, csv, random, json, re, collections, io
from PIL import Image
sys.path.insert(0, "/home/claude/spacefix"); from spacefix import build_lexicon, norm
LEX = build_lexicon(["/home/claude/spacefix/train_gt_all.txt"])
FR = set("le la les de des du et en un une que qui pour dans par sur au aux est sont pas plus ne se ce il elle nous vous ils avec son sa ses leur leurs".split())
ISSUES = {f"c{n}": f"Timmuzgha N°0{n-154}" for n in range(157, 164)}
OUT = pathlib.Path("/home/claude/bench/pool"); (OUT / "lines").mkdir(parents=True, exist_ok=True)
rng = random.Random(2026)
rows = []
for cid, name in ISSUES.items():
    pdf = f"/home/claude/scans/{cid}.pdf"
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    for pg in range(2, n + 1, 3):
        png = OUT / f"{cid}_p{pg:03d}"
        subprocess.run(["pdftoppm", "-f", str(pg), "-l", str(pg), "-r", "300", "-gray", "-png", "-singlefile", pdf, str(png)])
        img = Image.open(str(png) + ".png")
        tsv = subprocess.run(["tesseract", str(png) + ".png", "-", "-l", "kabv4", "--tessdata-dir", "/home/claude/pilot/tessdata", "-c", "tessedit_create_tsv=1"],
                             capture_output=True, text=True, env={"OMP_THREAD_LIMIT": "1", "PATH": "/usr/bin:/bin"}).stdout
        lines = collections.OrderedDict()
        for r in csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["level"] == "4":
                lines[(r["block_num"], r["par_num"], r["line_num"])] = {"box": [int(r[k]) for k in ("left", "top", "width", "height")], "words": []}
            elif r["level"] == "5" and r["text"].strip():
                k = (r["block_num"], r["par_num"], r["line_num"])
                if k in lines: lines[k]["words"].append(r["text"])
        for k, L in lines.items():
            txt = " ".join(L["words"]); words = [re.sub(r"[^\w-]", "", w) for w in L["words"]]; words = [w for w in words if len(w) > 1]
            if len(txt) < 15 or not words: continue
            known = sum(LEX.get(norm(w), 0) >= 2 for w in words) / len(words); fr = sum(norm(w) in FR for w in words) / len(words)
            x, y, w, h = L["box"]
            if known < 0.5 or fr > 0.15 or h < 20 or h > 150 or w < 300: continue
            lid = f"{cid}_p{pg:03d}_{'_'.join(k)}"
            img.crop((max(0, x - 8), max(0, y - 6), x + w + 8, y + h + 6)).save(OUT / "lines" / f"{lid}.png")
            rows.append({"id": lid, "source": name, "page": pg, "pre": txt, "kab_ratio": round(known, 2)})
        (pathlib.Path(str(png) + ".png")).unlink()
    print(name, sum(r["source"] == name for r in rows), flush=True)
json.dump(rows, open(OUT / "pool.json", "w"), ensure_ascii=False, indent=0)
