"""Feraoun-36M / Feraoun-Pro at LINE level (their native unit): fair comparison on ground-truth line crops."""
import sys, json, pathlib, torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer
torch.set_num_threads(1)
name = sys.argv[1]; repo = f"/home/claude/models/{name}"
model = AutoModel.from_pretrained(repo, trust_remote_code=True).eval()
tok = AutoTokenizer.from_pretrained(repo, trust_remote_code=True) if name.endswith("36M") else None
for s in sys.argv[2:]:
    S = pathlib.Path(s); meta = json.load(open(S / "meta.json"))
    out = S / "pred" / name; out.mkdir(parents=True, exist_ok=True)
    out0 = S / "pred" / name / "all.txt"
    hyp = json.load(open(out0)) if out0.exists() else {}; L = meta["lines"]
    # CPU budget: same fixed subset as the VLM baselines (every 32nd line, quality rules applied)
    sys.path.insert(0, "/home/claude/91/outil"); from kabocr_eval.gtquality import reasons
    import collections
    R = {l["id"]: reasons((S / "lines" / f"{l['id']}.gt.txt").read_text()) for l in meta["lines"]}
    legacy = {d for d, n in collections.Counter(l["doc"] for l in meta["lines"] if "legacy_font_encoding" in R[l["id"]]).items() if n >= 3}
    if S.name != "set_aya": L = L[::32]
    L = [l for l in L if not R[l["id"]] and l["doc"] not in legacy]
    for k in range(0, len(L), 16):
        chunk = L[k:k + 16]; imgs = [Image.open(S / "lines" / f"{l['id']}.png").convert("RGB") for l in chunk]
        with torch.inference_mode():
            res = model.transcribe(imgs, tok) if tok else [model.transcribe(im) for im in imgs]
        for l, r in zip(chunk, res): hyp[l["id"]] = r
    json.dump(hyp, open(out / "all.txt", "w"), ensure_ascii=False)
    print(s, len(hyp), flush=True)
