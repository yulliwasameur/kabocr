import hashlib, pathlib, json, re, collections, sys
sys.path.insert(0, "/home/claude/91/outil")
from kabocr_eval.charset import normalise
def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()
train_pdfs = list(pathlib.Path("/home/claude/train/pdf").glob("*.pdf")) + list(pathlib.Path("/home/claude/ood/bej_train").glob("*.pdf"))
test_pdfs = {s: list(pathlib.Path(f"/home/claude/ood/{d}").glob("*.pdf")) for s, d in [("bou", "bou_test"), ("bej", "bej_test"), ("liv", "liv"), ("aya", "aya")]}
H = {md5(p) for p in train_pdfs}
out = {"pdf_overlap": {s: sum(md5(p) in H for p in ps) for s, ps in test_pdfs.items()}}
norm = lambda s: re.sub(r"\W+", " ", normalise(s, "lenient").lower()).strip()
train_lines = [norm(pathlib.Path(f[:-6] + ".gt.txt").read_text()) for f in open("train_same.list").read().split()]
TL = set(train_lines)
def grams(s, n=8):
    w = s.split(); return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}
TG = set().union(*(grams(s) for s in train_lines))
for s in ["set_bou", "set_bej", "set_liv", "set_aya"]:
    L = [norm(p.read_text()) for p in pathlib.Path(f"/home/claude/ood/{s}/lines").glob("*.gt.txt")]
    L = [x for x in L if len(x.split()) >= 4]
    exact = sum(x in TL for x in L)
    g8 = sum(1 for x in L if grams(x) & TG)
    out[s] = {"lines": len(L), "exact_duplicate_lines": exact, "lines_sharing_an_8gram": g8}
print(json.dumps(out, indent=1)); json.dump(out, open("audit_leak.json", "w"), indent=1)
