# tests/test_metrics.py
"""Unit tests for banos.core.metrics (identify_bouts, SO, TP, IC, PRF1).

WHY these tests matter
----------------------
Each function here is the authoritative Python implementation of a BANOS formula.
These tests pin exact formula behaviour — including NaN returns for undefined cases.

NaN vs 0 policy:
  NaN (not 0) is returned when a metric is mathematically undefined, e.g.:
  - No GT bouts -> recall denominator is 0 -> recall = NaN, not 0
  - No overlapping bouts -> SO/TP have no inputs -> NaN, not 0
  - Single-frame GT bout -> IC denominator is 0 -> NaN, not 0

  WHY NaN and not 0: returning 0 would bias the group/overall averages downward
  by treating "undefined" as "worst possible score". nanmean() in aggregate_metrics
  correctly excludes NaN values so they do not affect recordings where the behavior
  actually occurred.

IC switch-counting range:
  count_switches_within_bout uses range(gt_start, gt_end) — inclusive of gt_end-1,
  checking all adjacent pairs (i, i+1) up to (gt_end-1, gt_end). This was a bug
  fix from v0.1.5 which used range(gt_start, gt_end-1) and missed the last pair.
"""

import math

from banos.core.metrics import (
    calculate_ic,
    calculate_precision_recall_f1,
    calculate_so,
    calculate_tiou,
    calculate_tp_metric,
    count_switches_within_bout,
    identify_bouts,
)

# --- identify_bouts ---


def test_identify_bouts_simple():
    assert identify_bouts([0, 1, 1, 0, 1, 0]) == [(1, 2), (4, 4)]


def test_identify_bouts_ends_with_one():
    assert identify_bouts([0, 1, 1]) == [(1, 2)]


def test_identify_bouts_starts_with_one():
    assert identify_bouts([1, 1, 0]) == [(0, 1)]


def test_identify_bouts_all_zeros():
    assert identify_bouts([0, 0, 0]) == []


def test_identify_bouts_all_ones():
    assert identify_bouts([1, 1, 1]) == [(0, 2)]


def test_identify_bouts_single_one():
    assert identify_bouts([0, 1, 0]) == [(1, 1)]


# --- calculate_precision_recall_f1 ---


def test_prf1_perfect():
    p, r, f1 = calculate_precision_recall_f1(5, 0, 0)
    assert p == 1.0 and r == 1.0 and f1 == 1.0


def test_prf1_all_zero_returns_nan():
    p, r, f1 = calculate_precision_recall_f1(0, 0, 0)
    assert math.isnan(p) and math.isnan(r) and math.isnan(f1)


def test_prf1_no_tp_some_fp():
    p, r, f1 = calculate_precision_recall_f1(0, 3, 0)
    assert p == 0.0
    assert math.isnan(r)  # no GT bouts -> recall undefined


def test_prf1_balanced():
    p, r, f1 = calculate_precision_recall_f1(2, 1, 1)
    assert abs(p - 2 / 3) < 1e-10
    assert abs(r - 2 / 3) < 1e-10
    assert abs(f1 - 2 / 3) < 1e-10


# --- calculate_tiou ---


def test_tiou_perfect_overlap():
    assert calculate_tiou((0, 5), (0, 5)) == 1.0


def test_tiou_no_overlap():
    # These don't actually overlap; caller should not call tiou on non-overlapping bouts
    # but function should handle gracefully
    result = calculate_tiou((0, 2), (5, 8))
    assert result == 0.0


def test_tiou_partial():
    # pred=(0,4), gt=(2,6): intersection=[2,4]=3 frames, union=5+5-3=7
    result = calculate_tiou((0, 4), (2, 6))
    assert abs(result - 3 / 7) < 1e-10


def test_tiou_contained():
    # pred=(1,3) inside gt=(0,5): intersection=3, union=6
    result = calculate_tiou((1, 3), (0, 5))
    assert abs(result - 3 / 6) < 1e-10


# --- calculate_so ---


def test_so_returns_nan_for_empty_gt():
    """SO is undefined (NaN) when GT has no bouts — not 0.

    WHY: 'no GT bouts' means the metric is inapplicable, not that overlap is zero.
    NaN causes aggregate_metrics to exclude this recording from the SO average.
    """
    assert math.isnan(calculate_so([(0, 5)], []))


def test_so_returns_nan_for_no_overlap():
    """SO is also NaN when pred and GT exist but share no overlapping frames.

    WHY: no overlapping pairs means there are no tIoU scores to average.
    Returning 0 would conflate "non-overlapping bouts" with "no GT bouts", both
    of which are genuinely different situations. NaN is the correct signal.
    """
    assert math.isnan(calculate_so([(0, 2)], [(5, 8)]))


def test_so_perfect():
    assert calculate_so([(0, 5)], [(0, 5)]) == 1.0


def test_so_averages_multiple():
    # Two perfect overlaps -> mean is 1.0
    result = calculate_so([(0, 5), (10, 15)], [(0, 5), (10, 15)])
    assert abs(result - 1.0) < 1e-10


# --- calculate_tp_metric ---


def test_tp_metric_perfect():
    assert calculate_tp_metric([(0, 5)], [(0, 5)]) == 1.0


def test_tp_metric_nan_for_empty_gt():
    assert math.isnan(calculate_tp_metric([(0, 5)], []))


def test_tp_metric_off_by_one_frame():
    # pred=(0,5), gt=(0,6): |0-0| + |5-6| = 1 -> 1/(1+1) = 0.5
    assert abs(calculate_tp_metric([(0, 5)], [(0, 6)]) - 0.5) < 1e-10


def test_tp_metric_large_offset():
    # pred=(0,10), gt=(5,15): |0-5| + |10-15| = 10 -> 1/11
    assert abs(calculate_tp_metric([(0, 10)], [(5, 15)]) - 1 / 11) < 1e-10


# --- count_switches_within_bout ---


def test_switches_at_last_position():
    # [1, 1, 1, 0] with gt (0,3): switch at i=2 comparing pred[2]=1, pred[3]=0
    assert count_switches_within_bout([1, 1, 1, 0], 0, 3) == 1


def test_no_switches():
    assert count_switches_within_bout([1, 1, 1, 1], 0, 3) == 0


def test_all_switches():
    assert count_switches_within_bout([1, 0, 1, 0], 0, 3) == 3


def test_switches_subset_range():
    # Only count within [1,3], not outside
    assert count_switches_within_bout([0, 1, 0, 1, 0], 1, 3) == 2


# --- calculate_ic ---


def test_ic_nan_for_empty_gt():
    """IC is undefined (NaN) when GT has no bouts — same rationale as SO."""
    assert math.isnan(calculate_ic([1, 0, 1], []))


def test_ic_perfect():
    assert calculate_ic([0, 1, 1, 1, 0], [(1, 3)]) == 1.0


def test_ic_with_switches():
    # gt=(0,3), pred=[1,0,1,1]: switches at (0,1) and (1,2) = 2 in length 3 -> 1 - 2/3
    result = calculate_ic([1, 0, 1, 1], [(0, 3)])
    assert abs(result - (1 - 2 / 3)) < 1e-10


def test_ic_zero_length_bout_excluded():
    """Single-frame GT bout (start == end, length 0) yields NaN IC.

    WHY: gt_length = gt_end - gt_start = 0, so there are no adjacent frame
    pairs to inspect for transitions. IC is undefined for such a bout.
    If all bouts are zero-length, IC returns NaN overall.
    """
    result = calculate_ic([1], [(0, 0)])
    # gt_length = 0, so this bout is skipped -> no valid scores -> NaN
    assert math.isnan(result)
