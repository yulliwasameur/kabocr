"""Open vision-language OCR baselines on CPU, on a FIXED subset (every 8th line of each main set,
all lines of the magazine set). Same frozen prompt as release/run_vlm_ollama.py. Greedy decoding.
usage: run_vlm_cpu.py {got|qwen2vl} SET_DIR...   -> SET/pred/<name>/all.txt (partial cache, resumable)"""
import sys, json, pathlib, time, torch
from PIL import Image
torch.set_num_threads(int(__import__("os").environ.get("NT", "2")))
which = sys.argv[1]
PROMPT = ("Transcribe the text in this image exactly, character by character. "
          "The language is Kabyle (Taqbaylit) written in Latin script, possibly with French words. "
          "Keep the letters ɛ ɣ č ǧ ḍ ḥ ṛ ṣ ṭ ẓ ţ exactly. Output only the transcription, nothing else.")
if which == "got":
    from transformers import AutoProcessor, AutoModelForImageTextToText
    repo = "stepfun-ai/GOT-OCR-2.0-hf"; name = "GOT-OCR-2.0"
    proc = AutoProcessor.from_pretrained(repo); model = AutoModelForImageTextToText.from_pretrained(repo, torch_dtype=torch.float32).eval()
    def run(img):
        inp = proc(img, return_tensors="pt")
        out = model.generate(**inp, do_sample=False, tokenizer=proc.tokenizer, stop_strings="<|im_end|>", max_new_tokens=120)
        return proc.decode(out[0, inp["input_ids"].shape[1]:], skip_special_tokens=True, clean_up_tokenization_spaces=False).strip()
else:
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
    repo = "Qwen/Qwen2-VL-2B-Instruct"; name = "Qwen2-VL-2B"
    proc = AutoProcessor.from_pretrained(repo, min_pixels=64 * 28 * 28, max_pixels=512 * 28 * 28)
    model = Qwen2VLForConditionalGeneration.from_pretrained(repo, torch_dtype=torch.bfloat16).eval()
    def run(img):
        msgs = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PROMPT}]}]
        text = proc.apply_chat_template(msgs, add_generation_prompt=True)
        inp = proc(text=[text], images=[img], return_tensors="pt")
        out = model.generate(**inp, do_sample=False, max_new_tokens=120)
        return proc.batch_decode(out[:, inp["input_ids"].shape[1]:], skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()
limit = int(__import__("os").environ.get("LIMIT", "100000"))
for s in sys.argv[2:]:
    S = pathlib.Path(s); meta = json.load(open(S / "meta.json"))
    # CPU budget: every 32nd line of each main set (magazine set skipped); lines excluded by the
    # ground-truth quality rules (for every system) are skipped. Fixed rule, decided before scoring.
    sys.path.insert(0, "/home/claude/91/outil"); from kabocr_eval.gtquality import reasons
    import collections
    R = {l["id"]: reasons((S / "lines" / f"{l['id']}.gt.txt").read_text()) for l in meta["lines"]}
    legacy = {d for d, n in collections.Counter(l["doc"] for l in meta["lines"] if "legacy_font_encoding" in R[l["id"]]).items() if n >= 3}
    L = meta["lines"] if S.name == "set_aya" else meta["lines"][::32]
    L = [l for l in L if not R[l["id"]] and l["doc"] not in legacy]
    out = S / "pred" / name; out.mkdir(parents=True, exist_ok=True); cache = out / "all.txt"
    hyp = json.load(open(cache)) if cache.exists() else {}
    t0 = time.time(); n = 0
    for l in L[:limit]:
        if l["id"] in hyp: continue
        img = Image.open(S / "lines" / f"{l['id']}.png").convert("RGB")
        if img.height > 64: img = img.resize((int(img.width * 64 / img.height), 64))
        with torch.inference_mode(): hyp[l["id"]] = run(img)
        n += 1
        if n % 5 == 0:
            json.dump(hyp, open(cache, "w"), ensure_ascii=False); print(s, len(hyp), f"{(time.time()-t0)/n:.1f}s/line", flush=True)
    json.dump(hyp, open(cache, "w"), ensure_ascii=False); print(s, "done", len(hyp), flush=True)
