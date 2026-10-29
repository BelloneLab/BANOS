# src/banos/core/metrics.py
"""Individual BANOS metric calculation functions."""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np
import pandas as pd


def _by_position(sequence: pd.Series | np.ndarray | list) -> np.ndarray | list:
    """Return ``sequence`` indexable by frame position (a Series gives its values)."""
    return sequence.to_numpy() if isinstance(sequence, pd.Series) else sequence


def identify_bouts(sequence: pd.Series | list) -> list[tuple[int, int]]:
    """Identify continuous runs of 1s in a binary sequence.

    Returns list of (start, end) tuples with inclusive indices.
    """
    bouts: list[tuple[int, int]] = []
    start = None
    for i, value in enumerate(sequence):
        if value == 1 and start is None:
            start = i
        elif value == 0 and start is not None:
            bouts.append((start, i - 1))
            start = None
    if start is not None:
        bouts.append((start, len(sequence) - 1))
    return bouts


def calculate_precision_recall_f1(n_tp: int, n_fp: int, n_fn: int) -> tuple[float, float, float]:
    """Compute Detection Accuracy: Precision, Recall, F1.

    Precision and recall are NaN when their denominator is zero.
    F1 is 0 when no bout is matched but some bouts were predicted or missed
    (``n_tp == 0`` and ``n_fp + n_fn > 0``), and NaN only when all three
    counts are zero.
    """
    precision = n_tp / (n_tp + n_fp) if (n_tp + n_fp) > 0 else float("nan")
    recall = n_tp / (n_tp + n_fn) if (n_tp + n_fn) > 0 else float("nan")
    if n_tp == 0 and n_fp + n_fn > 0:
        f1_score = 0.0
    elif not math.isnan(precision) and not math.isnan(recall) and (precision + recall) > 0:
        f1_score = 2 * precision * recall / (precision + recall)
    else:
        f1_score = float("nan")
    return precision, recall, f1_score


def calculate_tiou(pred_bout: tuple[int, int], gt_bout: tuple[int, int]) -> float:
    """Temporal Intersection over Union for a single bout pair."""
    intersection_start = max(pred_bout[0], gt_bout[0])
    intersection_end = min(pred_bout[1], gt_bout[1])
    intersection = max(intersection_end - intersection_start + 1, 0)
    union = (pred_bout[1] - pred_bout[0] + 1) + (gt_bout[1] - gt_bout[0] + 1) - intersection
    return intersection / union if union != 0 else 0.0


def _check_missed_bouts(missed_bouts: str) -> None:
    if missed_bouts not in ("exclude", "zero"):
        raise ValueError(f"Unknown missed_bouts option: {missed_bouts!r}. Use 'exclude' or 'zero'.")


def _mean(terms: list[float]) -> float:
    return sum(terms) / len(terms) if terms else float("nan")


def _pair_terms(
    pred_bouts: list[tuple[int, int]],
    gt_bouts: list[tuple[int, int]],
    pair_term: Callable[[tuple[int, int], tuple[int, int]], float],
    missed_bouts: str,
) -> list[float]:
    """Apply ``pair_term`` to every overlapping (pred, GT) bout pair, GT bout by GT bout.

    A GT bout that no predicted bout overlaps is missed: it adds one term
    equal to 0 with ``missed_bouts="zero"`` and no term with ``"exclude"``.
    """
    _check_missed_bouts(missed_bouts)
    terms: list[float] = []
    for gt in gt_bouts:
        gt_terms = [
            pair_term(pred, gt) for pred in pred_bouts if pred[1] >= gt[0] and pred[0] <= gt[1]
        ]
        if not gt_terms and missed_bouts == "zero":
            gt_terms = [0.0]
        terms.extend(gt_terms)
    return terms


def _boundary_precision(pred_bout: tuple[int, int], gt_bout: tuple[int, int]) -> float:
    return 1.0 / (1.0 + abs(pred_bout[0] - gt_bout[0]) + abs(pred_bout[1] - gt_bout[1]))


def calculate_so_terms(
    pred_bouts: list[tuple[int, int]],
    gt_bouts: list[tuple[int, int]],
    *,
    missed_bouts: str = "exclude",
) -> list[float]:
    """Segment Overlap terms: the tIoU of every overlapping bout pair.

    A GT bout that no predicted bout overlaps adds no term
    (``missed_bouts="exclude"``, default) or one term equal to 0 (``"zero"``).
    """
    return _pair_terms(pred_bouts, gt_bouts, calculate_tiou, missed_bouts)


def calculate_so(
    pred_bouts: list[tuple[int, int]],
    gt_bouts: list[tuple[int, int]],
    *,
    missed_bouts: str = "exclude",
) -> float:
    """Segment Overlap: average tIoU over all overlapping bout pairs.

    With ``missed_bouts="zero"``, each GT bout that no predicted bout overlaps
    adds a 0 to the average (see ``calculate_so_terms``).
    Returns NaN if there are no GT bouts, or no overlapping pair with "exclude".
    """
    return _mean(calculate_so_terms(pred_bouts, gt_bouts, missed_bouts=missed_bouts))


def calculate_tp_terms(
    pred_bouts: list[tuple[int, int]],
    gt_bouts: list[tuple[int, int]],
    *,
    missed_bouts: str = "exclude",
) -> list[float]:
    """Temporal Precision terms: 1 / (1 + |Δstart| + |Δend|) of every overlapping bout pair.

    A GT bout that no predicted bout overlaps adds no term
    (``missed_bouts="exclude"``, default) or one term equal to 0 (``"zero"``).
    """
    return _pair_terms(pred_bouts, gt_bouts, _boundary_precision, missed_bouts)


def calculate_tp_metric(
    pred_bouts: list[tuple[int, int]],
    gt_bouts: list[tuple[int, int]],
    *,
    missed_bouts: str = "exclude",
) -> float:
    """Temporal Precision: 1 / (1 + |Δstart| + |Δend|) averaged over overlapping bouts.

    With ``missed_bouts="zero"``, each GT bout that no predicted bout overlaps
    adds a 0 to the average (see ``calculate_tp_terms``).
    Returns NaN if there are no GT bouts, or no overlapping pair with "exclude".
    """
    return _mean(calculate_tp_terms(pred_bouts, gt_bouts, missed_bouts=missed_bouts))


def count_switches_within_bout(
    pred_sequence: pd.Series | np.ndarray | list, gt_start: int, gt_end: int
) -> int:
    """Count label transitions within [gt_start, gt_end] (inclusive).

    Compares pred[i] with pred[i+1] for i in [gt_start, gt_end-1].
    This includes the transition at the last frame boundary (gt_end-1 → gt_end).
    Frames are read by position: the index labels of a Series are ignored.
    """
    pred_sequence = _by_position(pred_sequence)
    switches = 0
    for i in range(gt_start, gt_end):  # gt_end inclusive: checks pairs up to (gt_end-1, gt_end)
        if pred_sequence[i] != pred_sequence[i + 1]:
            switches += 1
    return switches


def calculate_ic_terms(
    pred_sequence: pd.Series | np.ndarray | list,
    gt_bouts: list[tuple[int, int]],
    *,
    missed_bouts: str = "exclude",
) -> list[float]:
    """Intra-bout Continuity terms: 1 - (switches / gt_length) for each found GT bout.

    A GT bout is found when at least one of its frames is predicted (value 1).
    A missed GT bout adds no term (``missed_bouts="exclude"``, default) or one
    term equal to 0 (``"zero"``). One-frame GT bouts (gt_length = end - start
    = 0, no frame pair to compare) add no term.
    Frames are read by position: the index labels of a Series are ignored.
    """
    _check_missed_bouts(missed_bouts)
    pred_sequence = _by_position(pred_sequence)
    terms: list[float] = []
    for gt in gt_bouts:
        gt_length = gt[1] - gt[0]
        if gt_length == 0:
            continue
        if any(pred_sequence[i] == 1 for i in range(gt[0], gt[1] + 1)):
            switches = count_switches_within_bout(pred_sequence, gt[0], gt[1])
            terms.append(1.0 - (switches / gt_length))
        elif missed_bouts == "zero":
            terms.append(0.0)
    return terms


def calculate_ic(
    pred_sequence: pd.Series | np.ndarray | list,
    gt_bouts: list[tuple[int, int]],
    *,
    missed_bouts: str = "exclude",
) -> float:
    """Intra-bout Continuity: 1 - (switches / gt_length) averaged over found GT bouts.

    A GT bout is found when at least one of its frames is predicted (value 1).
    Missed GT bouts are left out of the average (``missed_bouts="exclude"``,
    default) or count as 0 (``"zero"``); one-frame GT bouts are always left
    out (see ``calculate_ic_terms``).
    Frames are read by position: the index labels of a Series are ignored.
    Returns NaN if there is no term (no GT bout longer than one frame, or none
    found with "exclude").
    """
    return _mean(calculate_ic_terms(pred_sequence, gt_bouts, missed_bouts=missed_bouts))
