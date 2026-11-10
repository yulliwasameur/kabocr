# kabocr_eval

Evaluation harness for Kabyle OCR (Latin and Tifinagh scripts). Part of the **kabocr** project. Licence: Apache-2.0.

```bash
python -m kabocr_eval.cli GT_DIR PRED_DIR --mode strict   # or lenient
python -m pytest -q tests
```

Metrics: CER, WER, **DCER** (errors on Kabyle-specific letters ɛ ɣ č ǧ ḍ ḥ ṛ ṣ ṭ ẓ ţ), BaseCER (diacritics removed), insertion rate, wrong-script rate; page-level bootstrap CI, paired permutation test, Holm correction.
