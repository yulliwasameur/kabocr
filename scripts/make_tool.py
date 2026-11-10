"""Build the self-contained annotation tool (one HTML file, images embedded) from pool.json.
Sample: up to N lines per issue, seeded; 20 % flagged 'double' (second pass starts from an EMPTY field).
Output: annotation_tool_<annotator>.html  — opens in any browser, works offline, autosaves in the browser,
exports a JSON file to send back."""
import json, base64, random, pathlib, io, sys, html
from PIL import Image
POOL = pathlib.Path("/home/claude/bench/pool")
rows = json.load(open(POOL / "pool.json"))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
rng = random.Random(2026)
by = {}
for r in rows: by.setdefault(r["source"], []).append(r)
sample = []
for src in sorted(by):
    L = by[src][:]; rng.shuffle(L); sample += L[:N]
rng.shuffle(sample)
k = max(1, len(sample) // 5)
for i, r in enumerate(sample): r["double"] = i < k
for r in sample:
    im = Image.open(POOL / "lines" / f"{r['id']}.png").convert("L")
    if im.height > 90: im = im.resize((int(im.width * 90 / im.height), 90), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); r["img"] = base64.b64encode(b.getvalue()).decode()
json.dump([{k: v for k, v in r.items() if k != "img"} for r in sample], open("/home/claude/bench/sample.json", "w"), ensure_ascii=False, indent=0)

TPL = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KabOCR-Bench annotation</title><style>
:root{--bg:#fbfaf7;--fg:#1d1d1f;--mut:#6b6b70;--line:#dcd8cf;--acc:#2f5d8a;--ok:#2e7d32;--warn:#b26a00}
@media (prefers-color-scheme:dark){:root{--bg:#18181a;--fg:#ececec;--mut:#a0a0a6;--line:#3a3a3e;--acc:#7fb0e0;--ok:#81c784;--warn:#ffb74d}}
body{background:var(--bg);color:var(--fg);font:16px/1.45 system-ui,sans-serif;margin:0;padding:0 16px 80px}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 0;z-index:2}
h1{font-size:18px;margin:0 0 6px}.bar button{font-size:18px;min-width:34px;margin:2px;padding:2px 6px}
.card{border:1px solid var(--line);border-radius:8px;padding:10px;margin:12px 0}
.card.done{border-color:var(--ok)}.card.skip{opacity:.6}
.img{background:#fff;padding:4px;overflow-x:auto}.img img{display:block;height:64px;max-width:none}
input[type=text]{width:100%;box-sizing:border-box;font:20px/1.4 "DejaVu Sans",system-ui,sans-serif;padding:6px;margin:6px 0;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px}
.meta{color:var(--mut);font-size:13px}.st button{margin-right:6px}.st button.on{outline:2px solid var(--acc)}
.dbl{color:var(--warn);font-weight:600}
</style></head><body>
<header><h1>KabOCR-Bench — annotation (__WHO__)</h1>
<div class="meta">Corrige le texte pour qu'il soit <b>exactement</b> ce qui est imprimé. Lettres :</div>
<div class="bar" id="bar"></div>
<div class="meta"><span id="prog"></span> · <button id="exp">Exporter (JSON)</button> · Entrée = valider et passer à la suivante</div></header>
<main id="m"></main>
<script>
const WHO="__WHO__", DATA=__DATA__, KEY="kabocr-bench-"+WHO;
let S={};try{S=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}};
const L="ɛ ɣ č ǧ ḍ ḥ ṛ ṣ ṭ ẓ ţ Ɛ Ɣ Č Ǧ Ḍ Ḥ Ṛ Ṣ Ṭ Ẓ Ţ « » “ ” — #".split(" ");
let last=null;const bar=document.getElementById("bar");
L.forEach(c=>{const b=document.createElement("button");b.textContent=c;b.onmousedown=e=>e.preventDefault();
 b.onclick=()=>{if(!last)return;const s=last.selectionStart,t=last.value;last.value=t.slice(0,s)+c+t.slice(last.selectionEnd);last.selectionStart=last.selectionEnd=s+c.length;last.dispatchEvent(new Event("input"))};bar.appendChild(b)});
const m=document.getElementById("m");
function prog(){const n=Object.values(S).filter(x=>x.status).length;document.getElementById("prog").textContent=n+" / "+DATA.length+" lignes traitées"}
DATA.forEach((r,i)=>{const d=document.createElement("div");d.className="card";d.id="c"+i;
 const pre=(WHO.endsWith("-B")&&r.double)?"":r.pre; const st=S[r.id]||{text:pre,status:""};
 d.innerHTML=`<div class="meta">#${i+1} · ${r.source} · page ${r.page}${r.double?' · <span class="dbl">double</span>':''}</div>
 <div class="img"><img src="data:image/png;base64,${r.img}" alt="ligne"></div>
 <input type="text" spellcheck="false" lang="kab">
 <div class="st">${["Corrigée","Hors périmètre","Mauvaise découpe","Illisible"].map(s=>`<button data-s="${s}">${s}</button>`).join("")}</div>`;
 const inp=d.querySelector("input");inp.value=st.text;
 const upd=()=>{d.classList.toggle("done",st.status==="Corrigée");d.classList.toggle("skip",!!st.status&&st.status!=="Corrigée");
  d.querySelectorAll(".st button").forEach(b=>b.classList.toggle("on",b.dataset.s===st.status))};
 inp.onfocus=()=>last=inp;inp.oninput=()=>{st.text=inp.value;S[r.id]=st;save()};
 inp.onkeydown=e=>{if(e.key==="Enter"){st.status="Corrigée";st.t=Date.now();S[r.id]=st;save();upd();prog();const nx=document.querySelector("#c"+(i+1)+" input");if(nx){nx.focus();nx.scrollIntoView({block:"center"})}}};
 d.querySelectorAll(".st button").forEach(b=>b.onclick=()=>{st.status=b.dataset.s;st.t=Date.now();S[r.id]=st;save();upd();prog()});
 upd();m.appendChild(d)});
prog();
document.getElementById("exp").onclick=()=>{const out=DATA.map(r=>({id:r.id,source:r.source,page:r.page,double:r.double,pre:r.pre,...(S[r.id]||{})}));
 const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([JSON.stringify({annotator:WHO,lines:out},null,1)],{type:"application/json"}));
 a.download="kabocr-bench-"+WHO+".json";a.click()};
</script></body></html>"""
for who in ("annotateur-A", "annotateur-B"):
    data = sample if who.endswith("A") else [r for r in sample if r["double"]]
    out = pathlib.Path(f"/home/claude/bench/annotation_tool_{who}.html")
    out.write_text(TPL.replace("__WHO__", who).replace("__DATA__", json.dumps(data, ensure_ascii=False)))
    print(out, len(data), round(out.stat().st_size / 1e6, 2), "MB")
