# tests/test_pipeline.py
"""Integration tests for banos.score() and the three-stage pipeline.

WHY these tests matter
----------------------
banos.score() is the public entry point. These tests verify end-to-end
behaviour: correct return types, all 6 metrics present, NaN exclusion in
aggregate_metrics, value range [0, 1], error handling for bad inputs,
and version consistency.

Pipeline stages tested together:
  preprocess_data -> calculate_banos_for_each_file -> aggregate_metrics

The test_aggregate_metrics_excludes_nan test is critical: it confirms that
recordings where a behavior has no GT bouts (NaN metrics) do NOT pull down
the group/overall averages. Using nanmean() is the correct design choice.
"""

import math

import pandas as pd
import pytest

import banos
from banos.pipeline import (
    aggregate_metrics,
)

PRED = pd.DataFrame(
    {
        "event1": [0, 1, 1, 1, 0, 0, 1, 1, 0],
        "event2": [1, 1, 0, 0, 0, 1, 1, 0, 0],
    }
)
GT = pd.DataFrame(
    {
        "event1": [0, 0, 1, 1, 1, 0, 1, 0, 0],
        "event2": [1, 0, 0, 0, 1, 1, 0, 0, 0],
    }
)


def test_score_single_file_returns_dict():
    result = banos.score(PRED, GT)
    assert isinstance(result, dict)
    assert set(result.keys()) == {"event1", "event2"}


def test_score_single_file_has_all_metrics():
    result = banos.score(PRED, GT)
    for behavior in result:
        assert set(result[behavior].keys()) == {"precision", "recall", "f1_score", "so", "tp", "ic"}


def test_score_multi_file_returns_tuple():
    result = banos.score({"f1": (PRED, GT), "f2": (PRED.copy(), GT.copy())})
    assert isinstance(result, tuple) and len(result) == 2
    group_m, overall_m = result
    assert isinstance(group_m, dict)
    assert isinstance(overall_m, dict)


def test_score_requires_gt_for_single_df():
    with pytest.raises(ValueError):
        banos.score(PRED)


def test_score_optimal_matching():
    result = banos.score(PRED, GT, matching="optimal")
    assert isinstance(result, dict)


def test_score_all_metrics_in_range():
    """All finite metric values must lie in [0, 1]; NaN is allowed (undefined case).

    WHY: values outside [0, 1] indicate a formula error (e.g., division producing
    values > 1). NaN is explicitly allowed because behaviors with no GT bouts
    return NaN by design — that is the correct signal for 'not applicable'.
    """
    result = banos.score(PRED, GT)
    for behavior, metrics in result.items():
        for key, val in metrics.items():
            if not math.isnan(val):
                assert 0.0 <= val <= 1.0, f"{behavior} {key} = {val} out of [0,1]"


def test_score_invalid_matching_raises():
    with pytest.raises(ValueError):
        banos.score(PRED, GT, matching="invalid")


def test_aggregate_metrics_excludes_nan():
    """NaN values in file metrics must be excluded from group and overall averages.

    WHY: f2 has all-NaN metrics (behavior had no GT bouts in that recording).
    If nanmean() were replaced by plain mean(), the average would be pulled toward
    0, making the system appear worse than it actually is. The result must equal
    only f1's values, as if f2 were never processed for that behavior.
    """
    file_metrics = {
        "f1": {
            "evt": {
                "precision": 0.8,
                "recall": 0.6,
                "f1_score": 0.686,
                "so": 0.5,
                "tp": 0.7,
                "ic": 0.9,
            }
        },
        "f2": {
            "evt": {
                "precision": float("nan"),
                "recall": float("nan"),
                "f1_score": float("nan"),
                "so": float("nan"),
                "tp": float("nan"),
                "ic": float("nan"),
            }
        },
    }
    group, overall = aggregate_metrics(file_metrics)
    # f2 has all NaN -> should be excluded from average
    assert abs(group["evt"]["precision"] - 0.8) < 1e-10
    assert abs(overall["precision"] - 0.8) < 1e-10


def test_score_version():
    assert isinstance(banos.__version__, str)
    assert banos.__version__ != ""
