# Model card — KabOCR-Free v0.1

- **Task**: text-line recognition (OCR) of printed Kabyle in Latin script, inside Tesseract (LSTM engine, `--oem 1`).
- **File**: `models/kabocr-free-v0.1.traineddata`, 3.5 MB, SHA-256 `cbe045771f735e4dc1e144a3872d7530fd40bb8620a856cf2c7a6b66ce8104e1`.
- **Start model**: Tesseract `kab` by Bouaziz Ait Driss (Apache-2.0), same character set.
- **Training data**: 11,848 synthetic lines. They come from 13,095 Kabyle Wikipedia sentences (CC BY-SA 4.0), rendered with 77 free fonts; 45 % are degraded (photocopy, phone photo, low resolution). **No thesis, book or magazine page was used.**
- **Training**: `lstmtraining`, 20,000 iterations, CPU.
- **Evaluation**: real lines from born-digital PDFs never seen in training. Line level, strict mode, document-level 95 % bootstrap intervals.

| Test set | lines / docs | CER % [95 % CI] | WER % | DCER % (Kabyle letters) |
|---|---|---|---|---|
| Theses, Univ. of Bouira | 1,285 / 12 | 0.90 [0.73, 1.06] | 5.3 | 6.0 |
| Theses, Univ. of Béjaïa (excl. phonetic-notation thesis) | 962 / 12 | 0.75 [0.54, 0.92] | 3.8 | 1.8 |
| Publishers' books | 1,235 / 15 | 1.70 [1.11, 2.55] | 9.5 | 10.1 |

- **Limits**: printed Latin script only. The character set lacks ţ and phonetic letters. Expect higher error on blurred or very low-resolution scans, and on fonts far from the training fonts.
- **Licence**: CC BY-SA 4.0 (weights). Please cite the software (see `CITATION.cff`).
- **Not released**: the stronger KabOCR-v2 to v5 models (CER 0.38–0.73 %). They were trained on theses and books whose rights do not allow redistribution.
