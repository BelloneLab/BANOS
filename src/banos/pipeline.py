# src/banos/pipeline.py
"""BANOS computation pipeline."""

from __future__ import annotations

import math

import pandas as pd

from banos.core.matching import calculate_tp_fp_fn
from banos.core.metrics import (
    calculate_ic,
    calculate_precision_recall_f1,
    calculate_so,
    calculate_tp_metric,
    identify_bouts,
)


def compute_behavior_metrics(
    pred_matrix: pd.DataFrame,
    gt_matrix: pd.DataFrame,
    matching: str = "greedy",
) -> dict:
    """Compute all BANOS metrics for each behavior column.

    Returns
    -------
    {behavior: {precision, recall, f1_score, so, tp, ic}}
    """
    metrics: dict = {}
    for behavior in pred_matrix.columns:
        pred_bouts = identify_bouts(pred_matrix[behavior])
        gt_bouts = identify_bouts(gt_matrix[behavior])

        if not gt_bouts:
            if not pred_bouts:
                # Correct absence: system correctly detected nothing
                metrics[behavior] = {
                    "precision": 1.0,
                    "recall": 1.0,
                    "f1_score": 1.0,
                    "so": 1.0,
                    "tp": 1.0,
                    "ic": 1.0,
                }
            else:
                # False detection: system predicted bouts that don't exist in GT
                metrics[behavior] = {
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                    "so": 0.0,
                    "tp": 0.0,
                    "ic": 0.0,
                }
            continue

        n_tp, n_fp, n_fn = calculate_tp_fp_fn(pred_bouts, gt_bouts, matching=matching)
        precision, recall, f1_score = calculate_precision_recall_f1(n_tp, n_fp, n_fn)
        so = calculate_so(pred_bouts, gt_bouts)
        tp_m = calculate_tp_metric(pred_bouts, gt_bouts)
        ic = calculate_ic(pred_matrix[behavior], gt_bouts)
        metrics[behavior] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "so": so,
            "tp": tp_m,
            "ic": ic,
        }
    return metrics


def calculate_banos_for_each_file(preprocessed_data: dict, matching: str = "greedy") -> dict:
    """Compute BANOS metrics for each file in the preprocessed data dict."""
    return {
        file_name: compute_behavior_metrics(pred, gt, matching=matching)
        for file_name, (pred, gt) in preprocessed_data.items()
    }


def aggregate_metrics(file_metrics: dict) -> tuple[dict, dict]:
    """Aggregate metrics per behavior (group) and overall.

    NaN values are excluded from averages (nanmean behavior).

    Returns
    -------
    group_metrics  : {behavior: {metric: mean_across_files}}
    overall_metrics: {metric: mean_across_behaviors_and_files}
    """
    metric_keys = ["precision", "recall", "f1_score", "so", "tp", "ic"]
    group: dict = {}
    overall: dict = {k: [] for k in metric_keys}

    for behaviors in file_metrics.values():
        for behavior, m in behaviors.items():
            if behavior not in group:
                group[behavior] = {k: [] for k in metric_keys}
            for key in metric_keys:
                val = m.get(key, float("nan"))
                group[behavior][key].append(val)
                overall[key].append(val)

    def _nanmean(values: list) -> float:
        valid = [
            v for v in values if v is not None and not math.isnan(v)
        ]  # None guard for JSON round-trip safety
        return sum(valid) / len(valid) if valid else float("nan")

    for behavior in group:
        for key in metric_keys:
            group[behavior][key] = _nanmean(group[behavior][key])

    return group, {key: _nanmean(vals) for key, vals in overall.items()}
