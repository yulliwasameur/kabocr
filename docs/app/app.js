/* KabOCR web app — everything runs in the browser (pdf.js renders, tesseract.js recognises). */
"use strict";
const $ = (id) => document.getElementById(id);
pdfjsLib.GlobalWorkerOptions.workerSrc = "vendor/pdf.worker.min.js";
const HOMO = { "ε": "ɛ", "Ε": "Ɛ", "γ": "ɣ", "Γ": "Ɣ", "Г": "Ɣ", "ԑ": "ɛ", "Ԑ": "Ɛ", "ɤ": "ɣ", "Ʃ": "Ɛ", "ğ": "ǧ", "Ğ": "Ǧ", "ț": "ţ", "ә": "ə", "Ә": "Ə" };
const fold = (s) => s.normalize("NFC").replace(/./gu, (c) => HOMO[c] || c);

let file = null, worker = null, pdfParts = [], baseName = "kabocr";

function setFile(f) {
  if (!f) return;
  const ok = f.type === "application/pdf" || /^image\/(png|jpeg)$/.test(f.type);
  if (!ok) { $("fileinfo").textContent = "Format non reconnu : choisissez un PDF, un PNG ou un JPG."; return; }
  file = f; baseName = f.name.replace(/\.[^.]+$/, "") || "kabocr";
  $("fileinfo").textContent = `${f.name} — ${(f.size / 1e6).toFixed(1)} Mo`;
  $("run").disabled = false;
}
$("file").addEventListener("change", (e) => setFile(e.target.files[0]));
const drop = $("drop");
["dragenter", "dragover"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => setFile(e.dataTransfer.files[0]));
drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $("file").click(); } });

function parsePages(spec, n) {
  if (!spec.trim()) return [...Array(n).keys()].map((i) => i + 1);
  const out = new Set();
  for (const part of spec.split(",")) {
    const m = part.trim().match(/^(\d+)(?:\s*-\s*(\d+))?$/);
    if (!m) continue;
    const a = +m[1], b = m[2] ? +m[2] : a;
    for (let p = Math.max(1, a); p <= Math.min(n, b); p++) out.add(p);
  }
  return [...out].sort((x, y) => x - y);
}
function status(msg, frac) {
  $("status").textContent = msg;
  if (frac !== undefined) $("barfill").style.width = `${Math.round(100 * frac)}%`;
}
async function getWorker() {
  if (worker) return worker;
  status("Chargement du modèle kabyle (3,5 Mo, une seule fois)…", 0);
  worker = await Tesseract.createWorker("kab", 1, {
    workerPath: "vendor/worker.min.js", corePath: "vendor/core", langPath: "model", gzip: false,
    cacheMethod: "none",
  });
  await worker.setParameters({ tessedit_pageseg_mode: "3", preserve_interword_spaces: "1" });
  return worker;
}
async function renderPdfPage(pdf, n, dpi) {
  const page = await pdf.getPage(n);
  const vp = page.getViewport({ scale: dpi / 72 });
  const canvas = document.createElement("canvas");
  canvas.width = Math.floor(vp.width); canvas.height = Math.floor(vp.height);
  const ctx = canvas.getContext("2d"); ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, canvas.width, canvas.height);
  await page.render({ canvasContext: ctx, viewport: vp }).promise;
  return canvas;
}
async function run() {
  if (!file) return;
  $("run").disabled = true; $("progress").hidden = false; $("output").hidden = false;
  $("text").value = ""; $("dlpdf").disabled = true; pdfParts = [];
  const doFold = $("fold").checked, makePdf = $("mkpdf").checked, dpi = +$("dpi").value;
  try {
    const w = await getWorker();
    await w.setParameters({ user_defined_dpi: String(dpi) });
    const chunks = [];
    if (file.type === "application/pdf") {
      const pdf = await pdfjsLib.getDocument({ data: await file.arrayBuffer() }).promise;
      const pages = parsePages($("pages").value, pdf.numPages);
      for (let k = 0; k < pages.length; k++) {
        const p = pages[k];
        status(`Page ${p} (${k + 1}/${pages.length}) : lecture…`, k / pages.length);
        const canvas = await renderPdfPage(pdf, p, dpi);
        const r = await w.recognize(canvas, {}, { text: true, pdf: makePdf });
        const t = doFold ? fold(r.data.text) : r.data.text;
        chunks.push(`— page ${p} —\n${t.trim()}\n`);
        if (makePdf && r.data.pdf) pdfParts.push(r.data.pdf);
        $("text").value = chunks.join("\n");
      }
    } else {
      status("Lecture de l'image…", 0.1);
      const r = await w.recognize(file, {}, { text: true, pdf: makePdf });
      chunks.push(doFold ? fold(r.data.text) : r.data.text);
      if (makePdf && r.data.pdf) pdfParts.push(r.data.pdf);
      $("text").value = chunks.join("\n");
    }
    status("Terminé. Relisez le texte avant de l'utiliser.", 1);
    $("dlpdf").disabled = !pdfParts.length;
  } catch (err) {
    console.error(err);
    status("Erreur : " + (err && err.message ? err.message : err) + ". Essayez un autre fichier ou une résolution plus basse.");
  } finally {
    $("run").disabled = false;
  }
}
$("run").addEventListener("click", run);

function download(name, blob) {
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name;
  document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}
$("dltxt").addEventListener("click", () => download(`${baseName}-kabocr.txt`, new Blob([$("text").value], { type: "text/plain;charset=utf-8" })));
$("dlpdf").addEventListener("click", async () => {
  const { PDFDocument } = PDFLib; const out = await PDFDocument.create();
  for (const part of pdfParts) {
    const src = await PDFDocument.load(new Uint8Array(part));
    (await out.copyPages(src, src.getPageIndices())).forEach((pg) => out.addPage(pg));
  }
  out.setTitle(`${baseName} (KabOCR)`); out.setProducer("KabOCR 0.1.0 (tesseract.js, KabOCR-Free model)");
  download(`${baseName}-kabocr.pdf`, new Blob([await out.save()], { type: "application/pdf" }));
});
async function copy(text, btn) {
  try { await navigator.clipboard.writeText(text); const o = btn.textContent; btn.textContent = "Copié ✓"; setTimeout(() => (btn.textContent = o), 1500); }
  catch (e) { /* clipboard unavailable: select the text instead */ }
}
$("copy").addEventListener("click", (e) => copy($("text").value, e.target));
$("copycite").addEventListener("click", (e) => copy($("cite").textContent, e.target));
