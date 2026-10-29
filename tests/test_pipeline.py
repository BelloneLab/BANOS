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

# Hand-made videos of 60 frames with three real bouts of one behavior ("evt").
N_FRAMES = 60
REAL_BOUTS = [(5, 9), (25, 29), (45, 49)]


def _frames(bouts: list[tuple[int, int]]) -> list[int]:
    """0/1 sequence of N_FRAMES frames, 1 on every frame of the (start, end) bouts."""
    sequence = [0] * N_FRAMES
    for start, end in bouts:
        sequence[start : end + 1] = [1] * (end - start + 1)
    return sequence


def _video(
    pred_bouts: list[tuple[int, int]], gt_bouts: list[tuple[int, int]] = REAL_BOUTS
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(pred_df, gt_df) pair of one video from its predicted and real bouts."""
    return pd.DataFrame({"evt": _frames(pred_bouts)}), pd.DataFrame({"evt": _frames(gt_bouts)})


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


def test_file_with_only_false_bouts_scores_f1_zero():
    """A file whose predicted bouts all miss the real bouts scores F1 0 and stays in the mean.

    Both models predict video 1 exactly. In video 2, model C predicts three
    bouts that overlap no real bout (TP 0, FP 3, FN 3: P 0, R 0, F1 0) and
    model D finds two of the three real bouts (TP 2, FN 1: P 1, R 2/3, F1 0.8).
    Per-file means: C (1 + 0) / 2 = 0.5, D (1 + 0.8) / 2 = 0.9. Before 1.1.0,
    C's video 2 scored F1 NaN, left the mean, and C got 1.0.
    """
    false_bouts = [(15, 19), (35, 39), (52, 56)]
    c_video2 = banos.score(*_video(false_bouts))["evt"]
    assert c_video2["precision"] == 0.0
    assert c_video2["recall"] == 0.0
    assert c_video2["f1_score"] == 0.0

    group_c, _ = banos.score({"v1": _video(REAL_BOUTS), "v2": _video(false_bouts)})
    group_d, _ = banos.score({"v1": _video(REAL_BOUTS), "v2": _video(REAL_BOUTS[:2])})
    assert abs(group_c["evt"]["f1_score"] - 0.5) < 1e-10
    assert abs(group_d["evt"]["f1_score"] - 0.9) < 1e-10


def test_silent_model_on_bundled_data(all_recordings):
    """A model that predicts nothing scores F1 0 on every recording with the behavior.

    Its only non-zero F1 cells are the correct absences (1.0). In the bundled
    data, attack is absent from 5 of the 10 recordings and mount from 4, while
    investigation and other are in all 10. Per-file means: attack 5/10 = 0.5,
    mount 4/10 = 0.4, investigation 0, other 0; overall F1 = 9 cells of 40 =
    0.225. Before 1.1.0 the recordings with the behavior scored F1 NaN and left
    the means: attack, mount and overall F1 were 1.0.
    """
    data = {f"Recording_{n}": (gt * 0, gt) for n, (_, gt) in all_recordings.items()}
    group, overall = banos.score(data)
    expected = {"attack": 0.5, "investigation": 0.0, "mount": 0.4, "other": 0.0}
    for behavior, f1 in expected.items():
        assert abs(group[behavior]["f1_score"] - f1) < 1e-10, behavior
    assert abs(overall["f1_score"] - 0.225) < 1e-10
