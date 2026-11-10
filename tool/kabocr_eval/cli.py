"""Usage:
    python -m kabocr_eval.cli GT_DIR PRED_DIR [--mode strict|lenient] [--script Latn|Tfng] [--json out.json]

GT_DIR and PRED_DIR contain one UTF-8 .txt file per page (same file names).
A page missing from PRED_DIR counts as an empty prediction (never skipped).
"""
from __future__ import annotations

import argparse
import json
import pathlib

from .metrics import Counts, bootstrap_ci, count, rates


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("gt")
    ap.add_argument("pred")
    ap.add_argument("--mode", default="strict", choices=["strict", "lenient"])
    ap.add_argument("--script", default="Latn")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    gt_dir, pr_dir = pathlib.Path(a.gt), pathlib.Path(a.pred)
    pages = sorted(gt_dir.glob("*.txt"))
    if not pages:
        raise SystemExit("no ground-truth pages found")
    per_page = []
    for p in pages:
        ref = p.read_text(encoding="utf-8")
        q = pr_dir / p.name
        hyp = q.read_text(encoding="utf-8") if q.exists() else ""
        per_page.append(count(ref, hyp, mode=a.mode, expected_script=a.script))
    total = sum(per_page, Counts())
    report = {"pages": len(pages), "mode": a.mode, **rates(total)}
    for m in ("CER", "WER", "DCER"):
        _, lo, hi = bootstrap_ci(per_page, m)
        report[f"{m}_CI95"] = [lo, hi]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    main()
