# tests/test_regression.py
"""Regression tests: verify BANOS outputs match golden fixtures.

WHY these tests matter
----------------------
Golden fixtures freeze the exact numerical output of the pipeline.
If any refactoring introduces an unintended numerical change — even a tiny
floating-point difference — these tests catch it immediately.

The golden fixtures in tests/fixtures/golden_python_v020.json represent the
CORRECTED v0.2.0 behaviour (three improvements over v0.1.5):
  1. Score 1.0 for correct absence (both GT and machine have no bouts).
  2. Score 0.0 for false detection (machine predicts bouts when GT has none).
  3. IC switch-counting covers all adjacent frame pairs within each GT bout
     (the original code missed the last pair, giving inflated IC values).

The archive fixtures (tests/fixtures/golden_python_v015.json) preserve
the original v0.1.5 behaviour for reference and comparison.

JSON null = Python NaN
----------------------
JSON has no NaN literal. NaN values may be stored as `null` in the fixture file.
The `_close()` helper treats JSON `null` (loaded as Python `None`) as
equivalent to `float('nan')` for comparison purposes.

Updating fixtures
-----------------
If you make a deliberate algorithm change that affects output values, update
the fixtures and document why:
    python scripts/generate_golden_fixtures.py
    # Then commit the updated tests/fixtures/golden_python_v020.json with a
    # clear commit message explaining the change.
"""

import json
import math
from pathlib import Path

import pandas as pd
import pytest

from banos import aggregate_metrics, calculate_banos_for_each_file, preprocess_data

DATASET_DIR = Path(__file__).parent.parent / "data" / "dataset_human_vs_human"
GOLDEN_FILE = Path(__file__).parent / "fixtures" / "golden_python_v020.json"
TOLERANCE = 1e-10

with open(GOLDEN_FILE) as f:
    GOLDEN = json.load(f)


def load_recording(n):
    rec_dir = DATASET_DIR / f"Recording_{n}"
    pred_path = rec_dir / "humanAnnotation_2.csv"
    if not pred_path.exists():
        raise FileNotFoundError(f"No pred file found for Recording_{n}")
    pred = pd.read_csv(pred_path)
    gt_path = rec_dir / "humanAnnotation_1.csv"
    if not gt_path.exists():
        raise FileNotFoundError(f"No GT found for Recording_{n}")
    return pred, pd.read_csv(gt_path)


def _close(actual, expected) -> bool:
    """Compare two metric values, handling None (JSON null = NaN)."""
    if expected is None:
        return actual is None or (isinstance(actual, float) and math.isnan(actual))
    if actual is None or (isinstance(actual, float) and math.isnan(actual)):
        return expected is None
    return abs(actual - expected) < TOLERANCE


@pytest.mark.parametrize("n", range(1, 11))
def test_regression_overall_metrics(n):
    """Overall metrics for each recording must exactly match golden fixtures (tol=1e-10).

    If this fails after a code change, the change affected numerical output.
    Decide whether the change is a bug fix or a regression, then either:
      - Fix the regression (no fixture update needed), OR
      - Deliberately update: python scripts/generate_golden_fixtures.py
    """
    pred, gt = load_recording(n)
    data, _ = preprocess_data({f"Recording_{n}": (pred.copy(), gt.copy())})
    file_metrics = calculate_banos_for_each_file(data)
    _, overall = aggregate_metrics(file_metrics)

    golden_overall = GOLDEN[f"Recording_{n}"]["overall_metrics"]
    for metric, expected in golden_overall.items():
        actual = overall[metric]
        assert _close(actual, expected), (
            f"Recording_{n} {metric}: expected {expected}, got {actual}"
        )


@pytest.mark.parametrize("n", range(1, 11))
def test_regression_group_metrics(n):
    """Per-behavior metrics for each recording must match golden fixtures (tol=1e-10).

    `null` in the JSON fixture means NaN — the behavior had no GT bouts in that
    recording and the metric is undefined. The `_close()` helper treats `null`
    and `float('nan')` as equivalent.
    """
    pred, gt = load_recording(n)
    data, _ = preprocess_data({f"Recording_{n}": (pred.copy(), gt.copy())})
    file_metrics = calculate_banos_for_each_file(data)
    group, _ = aggregate_metrics(file_metrics)

    golden_group = GOLDEN[f"Recording_{n}"]["group_metrics"]
    for behavior, metrics in golden_group.items():
        for metric, expected in metrics.items():
            actual = group[behavior][metric]
            assert _close(actual, expected), (
                f"Recording_{n} {behavior} {metric}: expected {expected}, got {actual}"
            )
