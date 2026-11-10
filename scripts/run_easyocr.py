"""EasyOCR baseline (Latin CRNN 'latin_g2' via lang fr), recognition only on ground-truth line crops.
Writes SET/pred/easyocr/all.txt in the cache format read by ood/eval_lines.py."""
import sys, json, pathlib, torch
torch.set_num_threads(1)
import easyocr
r = easyocr.Reader(["fr"], gpu=False, verbose=False)
for s in sys.argv[1:]:
    S = pathlib.Path(s); meta = json.load(open(S / "meta.json"))
    out = S / "pred" / "easyocr"; out.mkdir(parents=True, exist_ok=True)
    hyp = {}
    for l in meta["lines"]:
        res = r.recognize(str(S / "lines" / f"{l['id']}.png"), detail=0, paragraph=False)
        hyp[l["id"]] = " ".join(res)
    json.dump(hyp, open(out / "all.txt", "w"), ensure_ascii=False)
    print(s, len(hyp), flush=True)
