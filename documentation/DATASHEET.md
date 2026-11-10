# Datasheet — KabOCR line-level test sets (v0.1, 10 Nov 2026)

Format after Gebru et al., *Datasheets for Datasets* (2021). Short answers.

## Motivation
- **Why?** No public set of real Kabyle (Latin script) pages existed to compare OCR systems. Published figures used synthetic lines or private tests.
- **Who?** Yulliwas Ameur (Cnam-CEDRIC / Efrei). No external funding for this version.

## Composition
| Set | Source (Hugging Face `taqbaylit/…`) | Documents | Lines kept | Lines total |
|---|---|---|---|---|
| set_bou | `bouira` (theses, Univ. of Bouira) | 12 | 1 285 | 1 581 |
| set_bej | `bejaia` (theses, Univ. of Béjaïa) | 13 | 1 040 | 1 042 |
| set_liv | `adlis-pdfs` (publishers' books) | 15 | 1 235 | 1 520 |
| set_aya | `ayamun-pdfs` (magazine) | 2 | 63 | 328 |
| twin | `adlis-pdfs`, *Tacelhabt ur yessin* (image-only 96 dpi) + its born-digital twin | 1 book | 77 pages | 96 pages |

- **Instance** = one text line: image crop (300 dpi render) + reference text from the PDF text layer.
- **Kept** = passes the ground-truth quality rules (`kabocr_eval/gtquality.py`): no other script, no dingbats, no dot leaders, no legacy font encoding; a document with ≥ 3 legacy-encoded lines is dropped.
- **Languages**: Kabyle (majority), French (quotations, references). Tifinagh and Arabic lines are excluded.
- **Known errors**: superscript note calls are flattened in the text layer; one Béjaïa thesis uses phonetic notation; reference text keeps the authors' spacing around punctuation (see CER_ps).

## Collection
- Documents drawn at random with a fixed seed from the public collections. Pages chosen at random inside each document.
- Rendering: `pdftoppm -r 300`; lines from `pdftotext -bbox-layout`.

## Preprocessing
- Unicode NFC; homoglyphs typed by authors folded in the reference (fixed table in `charset.py`); ellipsis → three dots.

## Uses
- **Intended**: comparing OCR systems on Kabyle print; measuring Kabyle-letter errors (DCER).
- **Not intended**: training (the test documents must never be used for training); judging authors' writing.

## Distribution
- We distribute **scripts, document lists and line coordinates**, not the images or texts: the rights belong to authors and universities. Anyone can rebuild the sets from the public collections.
- Evaluation code: Apache-2.0.

## Maintenance
- Versioned with the evaluation toolkit. Errors reported in the repository issue tracker. A human-verified benchmark on physical scans (KabOCR-Bench) will supersede these sets for final claims.
