"""v5 data: lines that need the extended character set (ə ṯ ḏ ḇ ḵ ǥ ţ ḷ ʷ ˢ ᶻ š →), from
(a) 5 Béjaïa theses in phonetic notation never used anywhere (8-gram check vs the Béjaïa test set),
(b) lines of the existing TRAINING pools that v1-v4 had to drop because of ţ and similar letters.
Validation documents and all test documents are excluded."""
import json, sys, pathlib, random, collections
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.charset import normalise
from kabocr_eval.gtquality import reasons
from PIL import Image
uni = {l.split(' ')[0] for l in open("/home/claude/phon/cs/data/kab/kab.unicharset").read().split('\n')[1:] if l}
old = {l.split(' ')[0] for l in open("/home/claude/phon/cs/old.unicharset").read().split('\n')[1:] if l}
VAL = {"t059", "t064", "t065", "t066", "t067"}
test_txt = " ".join(p.read_text() for s in ("set_bou", "set_bej", "set_liv", "set_aya") for p in pathlib.Path(f"/home/claude/ood/{s}/lines").glob("*.gt.txt"))
tw = test_txt.split(); grams = {" ".join(tw[i:i + 8]) for i in range(len(tw) - 7)}
out, stat = [], collections.Counter()
for pool, newonly in [("/home/claude/phon/ex", False), ("/home/claude/train", True), ("/home/claude/train_bej", True), ("/home/claude/train_liv", True)]:
    for m in json.load(open(f"{pool}/lines_meta.json")):
        if m["doc"] in VAL: continue
        gt = normalise(m["gt"], "lenient")
        if reasons(gt): stat["quality"] += 1; continue
        if any(c not in uni and c != " " for c in gt): stat["charset"] += 1; continue
        new = any(c not in old and c != " " for c in gt)
        if newonly and not new: continue
        w = gt.split()
        if any(" ".join(w[i:i + 8]) in grams for i in range(len(w) - 7)): stat["overlap_test"] += 1; continue
        base = pathlib.Path(pool) / "lines" / m["id"]
        if not pathlib.Path(str(base) + ".png").exists(): stat["noimg"] += 1; continue
        d = pathlib.Path("lines"); d.mkdir(exist_ok=True); b = d / (pathlib.Path(pool).name + "_" + m["id"])
        if not pathlib.Path(str(b) + ".png").exists(): pathlib.Path(str(b) + ".png").symlink_to(str(base) + ".png")
        W, H = Image.open(str(base) + ".png").size
        pathlib.Path(str(b) + ".gt.txt").write_text(gt + "\n")
        with open(str(b) + ".box", "w") as f:
            f.write(f"WordStr 0 0 {W} {H} 0 #{gt}\n"); f.write(f"\t {W} {H} {W+1} {H+1} 0\n")
        out.append(str(b)); stat[pathlib.Path(pool).name + ("_new" if new else "")] += 1
print(dict(stat)); open("v5_new.txt", "w").write("\n".join(out) + "\n")
