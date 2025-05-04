#!/usr/bin/env python3
"""
recalc_ueq.py  – fix wrong UEQ scale scores in saved survey JSON files.

Usage examples
--------------
# one file
python recalc_ueq.py results/20250427_1042.json

# all UEQ logs in a folder
python recalc_ueq.py results/*.json
"""
from __future__ import annotations
import json, sys, glob, pathlib

# -------------------------------------------------------------------- #
# 1.  UEQ constants (official short-form, negative pole on the left)
# -------------------------------------------------------------------- #
SCALES: dict[str, list[int]] = {
    "Attractiveness": [1, 12, 14, 16, 24, 25],
    "Perspicuity"   : [2, 4, 13, 21],
    "Efficiency"    : [9, 20, 22, 23],
    "Dependability" : [8, 11, 17, 19],
    "Stimulation"   : [5, 6, 7, 18],
    "Novelty"       : [3, 10, 15, 26],
}

# public benchmark (mean, sd) – UEQ Handbook 2024
BENCH: dict[str, tuple[float, float]] = {
    "Attractiveness": (1.50, 0.85),
    "Perspicuity"   : (1.45, 0.83),
    "Efficiency"    : (1.38, 0.79),
    "Dependability" : (1.25, 0.86),
    "Stimulation"   : (1.17, 0.96),
    "Novelty"       : (0.78, 0.96),
}

def to_interval(score: int) -> int:
    """Convert 1-7 Likert to −3 … +3."""
    return score - 4

def grade(mean: float, bench_mean: float, sd: float) -> str:
    if mean >= bench_mean + 0.5 * sd:
        return "excellent"
    if mean >= bench_mean:
        return "good"
    if mean >= bench_mean - 0.5 * sd:
        return "okay"
    return "weak"

# -------------------------------------------------------------------- #
# 2.  Re-calculation routine
# -------------------------------------------------------------------- #
def recalc(path: pathlib.Path) -> pathlib.Path:
    data = json.loads(path.read_text(encoding="utf-8"))

    ans = data["answers"]
    means, grades = {}, {}
    for scale, items in SCALES.items():
        vals = [to_interval(ans[f"q{n}"]) for n in items]
        m = sum(vals) / len(vals)
        means[scale]  = m
        grades[scale] = grade(m, *BENCH[scale])

    data["scale_means"] = means
    data["grades"]      = grades

    out_path = path.with_name(path.stem + "_fixed.txt")
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out_path

# ────────────────────────────────────────────────────────────────────
# 3. CLI
# ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ueqrecalc.py <file>|<folder>|<glob>")
        sys.exit(1)

    targets: list[str] = []
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg)
        if p.is_file():
            targets.append(str(p))
        elif p.is_dir():
            targets.extend(glob.glob(str(p / "*.[jt][sx]t")))  # *.json or *.txt
        else:  # glob
            targets.extend(glob.glob(arg))

    if not targets:
        print("Nothing matched.")
        sys.exit(0)

    for f in targets:
        fixed = recalc(pathlib.Path(f))
        print(f"✔  {f}  →  {fixed.name}")