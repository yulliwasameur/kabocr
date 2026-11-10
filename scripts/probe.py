import subprocess, urllib.parse, pathlib, json, sys
base="https://huggingface.co/datasets/taqbaylit/adlis-pdfs/resolve/main/"
out=[]
for i,p in enumerate(open('cand.txt').read().split('\n')):
    if not p: continue
    f=pathlib.Path(f"c{i:03d}.pdf")
    if not f.exists():
        r=subprocess.run(["curl","-sL","-m","120","-o",str(f),base+urllib.parse.quote(p)])
    try:
        info=subprocess.run(["pdfinfo",str(f)],capture_output=True,text=True).stdout
        pages=int([l for l in info.splitlines() if l.startswith("Pages:")][0].split()[1])
        txt=subprocess.run(["pdftotext","-f","5","-l","9",str(f),"-"],capture_output=True,text=True).stdout
    except Exception as e:
        pages=0; txt=""
    rec={"id":f.stem,"src":p,"pages":pages,"chars":len(txt.strip()),"mb":round(f.stat().st_size/1e6,1)}
    out.append(rec); print(json.dumps(rec,ensure_ascii=False),flush=True)
    if rec["chars"]>200: f.unlink()   # keep only image-only (scanned) PDFs
json.dump(out,open('probe.json','w'),ensure_ascii=False,indent=0)
