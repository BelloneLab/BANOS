# src/banos/core/matching.py
"""Bout matching algorithms (greedy and optimal/Hungarian)."""

from __future__ import annotations


def _overlaps(pred: tuple[int, int], gt: tuple[int, int]) -> bool:
    return pred[1] >= gt[0] and pred[0] <= gt[1]


def calculate_tp_fp_fn(
    pred_bouts: list[tuple[int, int]],
    gt_bouts: list[tuple[int, int]],
    matching: str = "greedy",
) -> tuple[int, int, int]:
    """Count true positives, false positives, false negatives at bout level.

    Parameters
    ----------
    pred_bouts : list of (start, end) tuples for predicted bouts
    gt_bouts   : list of (start, end) tuples for ground truth bouts
    matching   : 'greedy' (first overlap wins) or 'optimal' (Hungarian algorithm)

    Returns
    -------
    (true_positives, false_positives, false_negatives)
    """
    if matching not in ("greedy", "optimal"):
        raise ValueError(f"Unknown matching algorithm: {matching!r}. Use 'greedy' or 'optimal'.")

    if not gt_bouts:
        return 0, len(pred_bouts), 0
    if not pred_bouts:
        return 0, 0, len(gt_bouts)

    if matching == "optimal":
        import numpy as np
        from scipy.optimize import linear_sum_assignment

        overlap = np.array(
            [[1 if _overlaps(p, g) else 0 for g in gt_bouts] for p in pred_bouts],
            dtype=float,
        )
        row_ind, col_ind = linear_sum_assignment(1 - overlap)
        n_tp = int(sum(overlap[r, c] for r, c in zip(row_ind, col_ind)))
        return n_tp, len(pred_bouts) - n_tp, len(gt_bouts) - n_tp

    # greedy (default — original BANOS behavior)
    n_tp = 0
    n_fp = 0
    matched_gt: set[int] = set()
    for pred in pred_bouts:
        matched = False
        for i, gt in enumerate(gt_bouts):
            if i not in matched_gt and _overlaps(pred, gt):
                n_tp += 1
                matched_gt.add(i)
                matched = True
                break
        if not matched:
            n_fp += 1
    n_fn = len(gt_bouts) - len(matched_gt)
    return n_tp, n_fp, n_fn
