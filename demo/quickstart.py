"""BANOS Quickstart — Score annotation files with two lines.

Demonstrates the high-level banos.score() API using the example dataset.
Run from the project root:
    python demo/quickstart.py
"""

from pathlib import Path

import banos
import pandas as pd

DATASET = Path(__file__).parent.parent / "data" / "dataset_human_vs_human"


# ── 1. Single recording ──────────────────────────────────────────────────────
pred = pd.read_csv(DATASET / "Recording_1" / "humanAnnotation_2.csv")
gt = pd.read_csv(DATASET / "Recording_1" / "humanAnnotation_1.csv")

BEHAVIORS = ["attack", "investigation", "mount"]
pred = pred[BEHAVIORS]
gt = gt[BEHAVIORS]

metrics = banos.score(pred, gt)

print("Per-behavior metrics - Recording 1")
print("-" * 48)
for behavior, m in metrics.items():
    f1 = m["f1_score"]
    so = m["so"]
    ic = m["ic"]
    f1_s = f"{f1:.3f}" if f1 is not None else "NaN"
    so_s = f"{so:.3f}" if so is not None else "NaN"
    ic_s = f"{ic:.3f}" if ic is not None else "NaN"
    print(f"  {behavior:<12}  F1={f1_s}  SO={so_s}  IC={ic_s}")

print()

# ── 2. Multiple recordings ────────────────────────────────────────────────────
data = {}
for n in range(1, 11):
    rec_dir = DATASET / f"Recording_{n}"
    pred_file = rec_dir / "humanAnnotation_2.csv"
    gt_file = rec_dir / "humanAnnotation_1.csv"
    if pred_file.exists() and gt_file.exists():
        p = pd.read_csv(pred_file)[BEHAVIORS]
        g = pd.read_csv(gt_file)[BEHAVIORS]
        data[f"Recording_{n}"] = (p, g)

group_metrics, overall_metrics = banos.score(data)

print("Overall metrics - 10 recordings (nanmean across behaviors and recordings)")
print("-" * 48)
for metric, value in overall_metrics.items():
    v_s = f"{value:.4f}" if value is not None else "NaN"
    print(f"  {metric:<12}  {v_s}")
