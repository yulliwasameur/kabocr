import sys, json, pathlib, collections
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.charset import normalise
from kabocr_eval.gtquality import reasons
from PIL import Image
def collect(ids, docof):
    R = {i: reasons(pathlib.Path(i + ".gt.txt").read_text().strip()) for i in ids}
    bad = {d for d, n in collections.Counter(docof(i) for i in ids if "legacy_font_encoding" in R[i]).items() if n >= 3}
    keep = [i for i in ids if not R[i] and docof(i) not in bad]
    return keep, bad
doc = lambda i: pathlib.Path(i).name.split("_")[0]
bou_tr = ["/home/claude/train/" + x for x in open("/home/claude/train/train_ids.txt").read().split()]
bou_va = ["/home/claude/train/" + x for x in open("/home/claude/train/val_ids.txt").read().split()]
bej = [str(p)[:-7] for p in sorted(pathlib.Path("/home/claude/train_bej/lines").glob("*.gt.txt"))]
syn = ["/home/claude/synth/" + x for x in open("/home/claude/synth/syn_ids.txt").read().split()]
k1, b1 = collect(bou_tr, doc); k2, b2 = collect(bou_va, doc); k3, b3 = collect(bej, doc)
# normalise Béjaïa truth (lenient folding) and write box files
for i in k3:
    gt = normalise(pathlib.Path(i + ".gt.txt").read_text().strip(), "lenient")
    pathlib.Path(i + ".gt.txt").write_text(gt + "\n")
    w, h = Image.open(i + ".png").size
    pathlib.Path(i + ".box").write_text(f"WordStr 0 0 {w} {h} 0 #{gt}\n\t {w} {h} {w+1} {h+1} 0\n")
aug = ["/home/claude/train/" + a for a in open("/home/claude/train/aug_ids.txt").read().split() if "/home/claude/train/" + a[:-4] in set(k1)]
train = k1 + aug + k3 + syn
open("train_ids.txt", "w").write("\n".join(train)); open("val_ids.txt", "w").write("\n".join(k2))
txt = "\n".join(pathlib.Path(i + ".gt.txt").read_text().strip() for i in train + k2)
open("all_gt.txt", "w").write(txt)
print({"bouira": len(k1), "bouira_aug": len(aug), "bejaia": len(k3), "synth": len(syn), "val": len(k2), "excluded_legacy_docs": sorted(b1 | b2 | b3)})
