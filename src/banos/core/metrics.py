# src/banos/core/metrics.py
"""Individual BANOS metric calculation functions."""

from __future__ import annotations

import math

import pandas as pd


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

    Returns NaN for any metric where the denominator is zero.
    """
    precision = n_tp / (n_tp + n_fp) if (n_tp + n_fp) > 0 else float("nan")
    recall = n_tp / (n_tp + n_fn) if (n_tp + n_fn) > 0 else float("nan")
    if not math.isnan(precision) and not math.isnan(recall) and (precision + recall) > 0:
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


def calculate_so(pred_bouts: list[tuple[int, int]], gt_bouts: list[tuple[int, int]]) -> float:
    """Segment Overlap: average tIoU over all overlapping bout pairs.

    Returns NaN if there are no GT bouts.
    """
    if not gt_bouts:
        return float("nan")
    scores = [
        calculate_tiou(pred, gt)
        for gt in gt_bouts
        for pred in pred_bouts
        if pred[1] >= gt[0] and pred[0] <= gt[1]
    ]
    return sum(scores) / len(scores) if scores else float("nan")


def calculate_tp_metric(
    pred_bouts: list[tuple[int, int]], gt_bouts: list[tuple[int, int]]
) -> float:
    """Temporal Precision: 1 / (1 + |Δstart| + |Δend|) averaged over overlapping bouts.

    Returns NaN if there are no GT bouts.
    """
    if not gt_bouts:
        return float("nan")
    scores = [
        1.0 / (1.0 + abs(pred[0] - gt[0]) + abs(pred[1] - gt[1]))
        for gt in gt_bouts
        for pred in pred_bouts
        if pred[1] >= gt[0] and pred[0] <= gt[1]
    ]
    return sum(scores) / len(scores) if scores else float("nan")


def count_switches_within_bout(pred_sequence: pd.Series | list, gt_start: int, gt_end: int) -> int:
    """Count label transitions within [gt_start, gt_end] (inclusive).

    Compares pred[i] with pred[i+1] for i in [gt_start, gt_end-1].
    This includes the transition at the last frame boundary (gt_end-1 → gt_end).
    """
    switches = 0
    for i in range(gt_start, gt_end):  # gt_end inclusive: checks pairs up to (gt_end-1, gt_end)
        if pred_sequence[i] != pred_sequence[i + 1]:
            switches += 1
    return switches


def calculate_ic(pred_sequence: pd.Series | list, gt_bouts: list[tuple[int, int]]) -> float:
    """Intra-bout Continuity: 1 - (switches / gt_length) averaged over GT bouts.

    Returns NaN if there are no GT bouts.
    """
    if not gt_bouts:
        return float("nan")
    ic_scores = []
    for gt in gt_bouts:
        gt_length = gt[1] - gt[0]
        if gt_length > 0:
            switches = count_switches_within_bout(pred_sequence, gt[0], gt[1])
            ic_scores.append(1.0 - (switches / gt_length))
        else:
            ic_scores.append(float("nan"))
    valid = [v for v in ic_scores if not math.isnan(v)]
    return sum(valid) / len(valid) if valid else float("nan")
