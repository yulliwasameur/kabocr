#!/usr/bin/env python3
"""KabOCR command line: OCR a PDF or image with the KabOCR-Free model (Tesseract >= 4.1).

  python3 kabocr.py document.pdf            -> document-kabocr.txt  and  document-kabocr.pdf (searchable)
  python3 kabocr.py page.png --dpi 300 --no-pdf

Needs: tesseract (>= 4.1) and, for PDFs, pdftoppm (poppler-utils).
"""
import argparse, pathlib, shutil, subprocess, sys, tempfile, unicodedata

HERE = pathlib.Path(__file__).resolve().parent
MODEL_DIR = HERE.parent / "models"
MODEL = "kabocr-free-v0.1"
HOMO = {"ε": "ɛ", "Ε": "Ɛ", "γ": "ɣ", "Γ": "Ɣ", "Г": "Ɣ", "ԑ": "ɛ", "Ԑ": "Ɛ", "ɤ": "ɣ",
        "Ʃ": "Ɛ", "ğ": "ǧ", "Ğ": "Ǧ", "ț": "ţ", "ә": "ə", "Ә": "Ə"}


def fold(s):
    return "".join(HOMO.get(c, c) for c in unicodedata.normalize("NFC", s))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input"); ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--first", type=int); ap.add_argument("--last", type=int)
    ap.add_argument("--no-pdf", action="store_true", help="do not build the searchable PDF")
    ap.add_argument("--no-fold", action="store_true", help="keep homoglyphs (Greek ε, γ…) as output")
    a = ap.parse_args()
    for tool in ("tesseract",) + (("pdftoppm",) if a.input.lower().endswith(".pdf") else ()):
        if not shutil.which(tool): sys.exit(f"missing dependency: {tool}")
    src = pathlib.Path(a.input); stem = src.with_suffix("")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        if src.suffix.lower() == ".pdf":
            cmd = ["pdftoppm", "-r", str(a.dpi), "-gray", "-png"]
            if a.first: cmd += ["-f", str(a.first)]
            if a.last: cmd += ["-l", str(a.last)]
            subprocess.run(cmd + [str(src), str(tmp / "p")], check=True)
            images = sorted(tmp.glob("p-*.png"))
        else:
            images = [src]
        texts, pdfs = [], []
        for i, img in enumerate(images, 1):
            out = tmp / f"o{i:05d}"
            cfg = ["-c", "tessedit_create_txt=1"] + ([] if a.no_pdf else ["-c", "tessedit_create_pdf=1"])
            subprocess.run(["tesseract", str(img), str(out), "--tessdata-dir", str(MODEL_DIR), "-l", MODEL,
                            "--dpi", str(a.dpi)] + cfg, check=True, stderr=subprocess.DEVNULL)
            t = (tmp / f"o{i:05d}.txt").read_text(encoding="utf-8")
            texts.append(f"— page {i} —\n{(t if a.no_fold else fold(t)).strip()}\n")
            if not a.no_pdf: pdfs.append(tmp / f"o{i:05d}.pdf")
            print(f"page {i}/{len(images)}", file=sys.stderr)
        pathlib.Path(f"{stem}-kabocr.txt").write_text("\n".join(texts), encoding="utf-8")
        if pdfs:
            if len(pdfs) == 1:
                shutil.copy(pdfs[0], f"{stem}-kabocr.pdf")
            elif shutil.which("pdfunite"):
                subprocess.run(["pdfunite", *map(str, pdfs), f"{stem}-kabocr.pdf"], check=True)
            else:
                print("pdfunite not found: searchable PDF skipped (install poppler-utils)", file=sys.stderr)
    print(f"written: {stem}-kabocr.txt" + ("" if a.no_pdf else f", {stem}-kabocr.pdf"))


if __name__ == "__main__":
    main()
