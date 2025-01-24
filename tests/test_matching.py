# tests/test_matching.py
"""Unit tests for banos.core.matching (greedy and optimal bout assignment).

WHY these tests matter
----------------------
Matching determines which predicted bouts count as true positives.
An error here silently corrupts Precision, Recall, F1, SO, and TP for every
behavior — all downstream metrics depend on the TP/FP/FN counts.

Greedy matching: for each predicted bout, claim the first available GT bout
that overlaps. Fast (O(n*m)) but can make suboptimal early commitments.

Optimal matching: Hungarian algorithm (scipy.optimize.linear_sum_assignment)
finds the globally best assignment, maximizing total overlap. Slower (O(n^3))
but scientifically preferable when bouts are densely overlapping.

The test_optimal_beats_greedy test documents the exact scenario where greedy
fails: pred(0,10) greedily takes gt(0,3) — the first overlap it finds — leaving
pred(0,3) unable to match gt(8,12) (no overlap). Optimal correctly assigns
pred(0,3)→gt(0,3) and pred(0,10)→gt(8,12), yielding 2 TP vs greedy's 1 TP.
"""

import pytest

from banos.core.matching import calculate_tp_fp_fn


def test_empty_gt():
    """No GT bouts: every prediction is a false positive; FN=0 (no GT to miss)."""
    tp, fp, fn = calculate_tp_fp_fn([(0, 5)], [])
    assert tp == 0 and fp == 1 and fn == 0


def test_empty_pred():
    """No predictions: every GT bout is a false negative; FP=0."""
    tp, fp, fn = calculate_tp_fp_fn([], [(0, 5)])
    assert tp == 0 and fp == 0 and fn == 1


def test_both_empty():
    """Edge case: TP=FP=FN=0 when both sides are empty — perfect vacuous agreement."""
    tp, fp, fn = calculate_tp_fp_fn([], [])
    assert tp == 0 and fp == 0 and fn == 0


def test_perfect_match_greedy():
    tp, fp, fn = calculate_tp_fp_fn([(0, 5), (10, 15)], [(0, 5), (10, 15)])
    assert tp == 2 and fp == 0 and fn == 0


def test_no_overlap_greedy():
    tp, fp, fn = calculate_tp_fp_fn([(0, 3)], [(10, 15)])
    assert tp == 0 and fp == 1 and fn == 1


def test_partial_match_greedy():
    pred = [(0, 5), (10, 15)]
    gt = [(0, 5), (20, 25)]
    tp, fp, fn = calculate_tp_fp_fn(pred, gt)
    assert tp == 1 and fp == 1 and fn == 1


def test_perfect_match_optimal():
    tp, fp, fn = calculate_tp_fp_fn([(0, 5), (10, 15)], [(0, 5), (10, 15)], matching="optimal")
    assert tp == 2 and fp == 0 and fn == 0


def test_optimal_beats_greedy():
    """Greedy takes suboptimal match; optimal finds better assignment."""
    pred = [(0, 10), (0, 3)]
    gt = [(0, 3), (8, 12)]
    tp_g, fp_g, fn_g = calculate_tp_fp_fn(pred, gt, matching="greedy")
    tp_o, fp_o, fn_o = calculate_tp_fp_fn(pred, gt, matching="optimal")
    assert tp_g == 1 and fp_g == 1 and fn_g == 1
    assert tp_o == 2 and fp_o == 0 and fn_o == 0


def test_invalid_matching_raises():
    with pytest.raises(ValueError, match="Unknown matching"):
        calculate_tp_fp_fn([(0, 5)], [(0, 5)], matching="invalid")


def test_invalid_matching_raises_with_empty_bouts():
    """ValueError raised even with empty bouts -- guard is at top of function."""
    with pytest.raises(ValueError, match="Unknown matching"):
        calculate_tp_fp_fn([], [], matching="invalid")
