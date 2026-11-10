"""Build page-level and line-level test sets from born-digital PDFs (text layer = truth).
usage: build_set.py SRC_DIR OUT_DIR MAX_PAGES_PER_DOC [doc_glob]"""
import subprocess, re, sys, json, pathlib, unicodedata, html
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.charset import normalise, SPECIAL
from PIL import Image
src, out, maxp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), int(sys.argv[3])
pat = sys.argv[4] if len(sys.argv) > 4 else "*.pdf"
(out / "pages").mkdir(parents=True, exist_ok=True); (out / "lines").mkdir(exist_ok=True)
FUNC = re.compile(r"\b(n|deg|d|ɣef|akken|di|ur|ad|i|seg|ɣer|am|neɣ|maca|yiwen|ayen)\b")
FR = re.compile(r"\b(le|la|les|des|du|et|est|une|dans|que|pour)\b", re.I)
meta = {"pages": [], "lines": [], "rejected_docs": {}}
for pdf in sorted(src.glob(pat)):
    fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout
    if "GlyphLess" in fonts or len(fonts.strip().split("\n")) <= 2:
        meta["rejected_docs"][pdf.name] = "scan or OCR text layer"; continue
    m = re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout)
    if not m: meta["rejected_docs"][pdf.name] = "unreadable"; continue
    n = int(m.group(1)); cands = []
    for p in range(max(3, n // 10), n - 2):
        t = unicodedata.normalize("NFC", subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True).stdout)
        w = t.split()
        if len(t) < 900 or len(w) < 120: continue
        if any(0xE000 <= ord(c) <= 0xF8FF for c in t) or "�" in t: continue
        tl = normalise(t, "lenient")
        if sum(c in SPECIAL for c in tl) < 10: continue
        if len(FUNC.findall(tl)) / len(w) < 0.07 or len(FR.findall(tl)) / len(w) > 0.06: continue
        cands.append(p)
        if len(cands) >= 40: break
    if not cands: meta["rejected_docs"][pdf.name] = "no Kabyle page with clean text layer"; continue
    step = max(1, len(cands) // maxp)
    for p in cands[::step][:maxp]:
        pid = f"{pdf.stem}_p{p:03d}"
        subprocess.run(["pdftoppm", "-r", "300", "-gray", "-png", "-singlefile", "-f", str(p), "-l", str(p), str(pdf), str(out / "pages" / pid)], check=True)
        t = unicodedata.normalize("NFC", subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True).stdout)
        (out / "pages" / f"{pid}.txt").write_text(normalise(t, "lenient").replace(" ", " ") if False else t)
        meta["pages"].append({"id": pid, "doc": pdf.stem})
        x = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-bbox-layout", "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True).stdout
        img = Image.open(out / "pages" / f"{pid}.png"); sc = 300 / 72
        for li, (x0, y0, x1, y1, body) in enumerate(re.findall(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>', x, re.S)):
            gt = unicodedata.normalize("NFC", " ".join(html.unescape(wd) for wd in re.findall(r'<word[^>]*>(.*?)</word>', body))).strip()
            x0, y0, x1, y1 = (float(v) * sc for v in (x0, y0, x1, y1))
            if len(gt) < 10 or (y1 - y0) < 20 or (y1 - y0) > 160 or (x1 - x0) < 80: continue
            pad = 0.15 * (y1 - y0); lid = f"{pid}_l{li:02d}"
            img.crop((int(x0 - pad), int(y0 - pad), int(x1 + pad), int(y1 + pad))).save(out / "lines" / f"{lid}.png")
            (out / "lines" / f"{lid}.gt.txt").write_text(gt + "\n")
            meta["lines"].append({"id": lid, "doc": pdf.stem})
    print(pdf.stem, len([q for q in meta["pages"] if q["doc"] == pdf.stem]), file=sys.stderr, flush=True)
json.dump(meta, open(out / "meta.json", "w"), ensure_ascii=False, indent=0)
print(out, "pages", len(meta["pages"]), "lines", len(meta["lines"]), "rejected", len(meta["rejected_docs"]), file=sys.stderr)
