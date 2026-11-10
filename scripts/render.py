"""Render rights-clean synthetic Kabyle lines (Wikipedia CC BY-SA text) with many fonts."""
import subprocess, random, pathlib, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
sys.path.insert(0, "/home/claude/pilot/scripts")
NEED = set("ɛɣčǧḍḥṛṣṭẓƐƔČǦḌḤṚṢṬẒəṯḏḇḵǥ")
files = subprocess.run(["fc-list", "--format", "%{file}\n"], capture_output=True, text=True).stdout.split()
fonts = []
for f in sorted(set(files)):
    if not f.lower().endswith((".ttf", ".otf")) or "Mono" in f: continue
    try:
        cmap = TTFont(f, lazy=True, fontNumber=0).getBestCmap()
    except Exception:
        continue
    if NEED <= set(map(chr, cmap)): fonts.append(f)
print(len(fonts), "fonts", sorted({pathlib.Path(f).stem.split('-')[0] for f in fonts}), file=sys.stderr)
import degrade  # noqa: E402  (pilot functions: photocopy, lowres, phone)
SPIR = {"t": "ṯ", "d": "ḏ", "b": "ḇ", "k": "ḵ", "g": "ǥ", "e": "ə"}
def notation(s, rng):  # linguistic (spirant) notation used in Kabyle linguistics theses
    return "".join(SPIR[c] if c in SPIR and rng.random() < 0.5 else c for c in s)
out = pathlib.Path("lines"); out.mkdir(exist_ok=True)
sents = open("wiki_sents.txt").read().split("\n")
rng = random.Random(11); ids = []
for i, s in enumerate(sents):
    if rng.random() < 0.08: s = notation(s, rng)
    f = rng.choice(fonts); size = rng.randint(30, 46)
    font = ImageFont.truetype(f, size)
    w = int(font.getlength(s)) + 2 * size; h = int(size * 1.6)
    im = Image.new("L", (w, h), 255)
    ImageDraw.Draw(im).text((size, int(size * 0.25)), s, font=font, fill=rng.randint(0, 50))
    r = rng.random()
    nr = np.random.default_rng(i)
    if r < 0.15: im = degrade.photocopy(im, nr)
    elif r < 0.3: im = degrade.phone(im, nr)
    elif r < 0.45: im = degrade.lowres(im.resize((w * 2, h * 2)), nr)
    name = f"syn{i:05d}"; im.save(out / f"{name}.png"); (out / f"{name}.gt.txt").write_text(s + "\n")
    with open(out / f"{name}.box", "w") as fb:
        fb.write(f"WordStr 0 0 {im.size[0]} {im.size[1]} 0 #{s}\n\t {im.size[0]} {im.size[1]} {im.size[0]+1} {im.size[1]+1} 0\n")
    ids.append(str(out / name))
open("syn_ids.txt", "w").write("\n".join(ids)); print(len(ids), "lines", file=sys.stderr)
