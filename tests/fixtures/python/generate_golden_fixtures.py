# tests/fixtures/python/generate_golden_fixtures.py
"""Generate golden output fixtures from the current BANOS code (v0.2.0).

These fixtures freeze the current (corrected) behaviour for regression testing.
They reflect three improvements over archive v0.1.5:
  1. Score 1.0 for correct absence (both GT and machine have no bouts).
  2. Score 0.0 for false detection (machine predicts bouts when GT has none).
  3. IC switch-counting correctly includes the last adjacent frame pair.

Run once to regenerate after a deliberate algorithm change:
    python tests/fixtures/python/generate_golden_fixtures.py

See also:
    tests/fixtures/python/generate_archive_fixtures.py  — v0.1.5 behaviour (returns 0 for absent)
    uv run pytest tests/test_regression.py              — check current code matches stored fixtures
"""

import json
import math
from pathlib import Path

import pandas as pd

from banos import aggregate_metrics, calculate_banos_for_each_file, preprocess_data

DATASET_DIR = Path(__file__).parent.parent.parent.parent / "data" / "dataset_human_vs_human"
OUT_FILE = Path(__file__).parent.parent / "golden_python_v020.json"


def load_recording(n: int):
    """Load pred/gt DataFrames for recording N."""
    rec_dir = DATASET_DIR / f"Recording_{n}"
    pred_path = rec_dir / "humanAnnotation_2.csv"
    if not pred_path.exists():
        raise FileNotFoundError(f"No pred file found for Recording_{n}")
    pred = pd.read_csv(pred_path)
    gt_path = rec_dir / "humanAnnotation_1.csv"
    if not gt_path.exists():
        raise FileNotFoundError(f"No GT found for Recording_{n}")
    return pred, pd.read_csv(gt_path)


def make_json_serializable(obj):
    """Convert NaN/inf to null for JSON serialization."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    return obj


if __name__ == "__main__":
    results = {}
    for n in range(1, 11):
        pred, gt = load_recording(n)
        data, _ = preprocess_data({f"Recording_{n}": (pred.copy(), gt.copy())})
        file_metrics = calculate_banos_for_each_file(data)
        group_m, overall_m = aggregate_metrics(file_metrics)
        results[f"Recording_{n}"] = {
            "file_metrics": make_json_serializable(file_metrics),
            "group_metrics": make_json_serializable(group_m),
            "overall_metrics": make_json_serializable(overall_m),
        }
        print(f"Recording_{n}: {overall_m}")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved golden fixtures to {OUT_FILE}")
    print(f"Total recordings: {len(results)}")
