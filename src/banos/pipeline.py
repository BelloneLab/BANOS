# src/banos/pipeline.py
"""BANOS computation pipeline."""

from __future__ import annotations

import math

import pandas as pd

from banos.core.matching import _check_matching, calculate_tp_fp_fn
from banos.core.metrics import (
    _check_missed_bouts,
    _mean,
    calculate_ic_terms,
    calculate_precision_recall_f1,
    calculate_so_terms,
    calculate_tp_terms,
    identify_bouts,
)

METRIC_KEYS = ["precision", "recall", "f1_score", "so", "tp", "ic"]


def _check_options(matching: str, missed_bouts: str) -> None:
    """Raise ValueError for an unknown matching or missed_bouts value."""
    _check_matching(matching)
    _check_missed_bouts(missed_bouts)


def _nanmean(values: list) -> float:
    valid = [
        v for v in values if v is not None and not math.isnan(v)
    ]  # None guard for JSON round-trip safety
    return _mean(valid)


def _metrics_from_components(components: dict) -> dict:
    """The six metrics of one behavior from its bout counts and terms."""
    precision, recall, f1_score = calculate_precision_recall_f1(
        components["n_tp"], components["n_fp"], components["n_fn"]
    )
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "so": _mean(components["so_terms"]),
        "tp": _mean(components["tp_terms"]),
        "ic": _mean(components["ic_terms"]),
    }


def compute_behavior_components(
    pred_matrix: pd.DataFrame,
    gt_matrix: pd.DataFrame,
    matching: str = "greedy",
    *,
    missed_bouts: str = "exclude",
) -> dict:
    """Compute the components of the BANOS metrics for each behavior column.

    The components are what the metrics are computed from: the bout counts
    behind precision, recall and F1, and the terms that SO, TP and IC
    average. Summed over files, they give the pooled metrics
    (see ``pool_components``).

    ``missed_bouts`` sets how SO, TP and IC count a GT bout that no predicted
    bout overlaps: left out ('exclude', default) or a term equal to 0 ('zero').

    Returns
    -------
    {behavior: {n_tp, n_fp, n_fn, so_terms, tp_terms, ic_terms}}
        n_tp, n_fp, n_fn : matched, false and missed bout counts
        so_terms, tp_terms, ic_terms : lists of the terms of SO, TP and IC
    """
    _check_options(matching, missed_bouts)
    components: dict = {}
    for behavior in pred_matrix.columns:
        pred_bouts = identify_bouts(pred_matrix[behavior])
        gt_bouts = identify_bouts(gt_matrix[behavior])
        n_tp, n_fp, n_fn = calculate_tp_fp_fn(pred_bouts, gt_bouts, matching=matching)
        components[behavior] = {
            "n_tp": n_tp,
            "n_fp": n_fp,
            "n_fn": n_fn,
            "so_terms": calculate_so_terms(pred_bouts, gt_bouts, missed_bouts=missed_bouts),
            "tp_terms": calculate_tp_terms(pred_bouts, gt_bouts, missed_bouts=missed_bouts),
            "ic_terms": calculate_ic_terms(
                pred_matrix[behavior].to_numpy(), gt_bouts, missed_bouts=missed_bouts
            ),
        }
    return components


def compute_behavior_metrics(
    pred_matrix: pd.DataFrame,
    gt_matrix: pd.DataFrame,
    matching: str = "greedy",
    *,
    missed_bouts: str = "exclude",
) -> dict:
    """Compute all BANOS metrics for each behavior column.

    ``missed_bouts`` sets how SO, TP and IC count a GT bout that no predicted
    bout overlaps: left out ('exclude', default) or a term equal to 0 ('zero').

    Returns
    -------
    {behavior: {precision, recall, f1_score, so, tp, ic}}
    """
    components = compute_behavior_components(
        pred_matrix, gt_matrix, matching=matching, missed_bouts=missed_bouts
    )
    metrics: dict = {}
    for behavior, behavior_components in components.items():
        if behavior_components["n_tp"] + behavior_components["n_fn"] == 0:
            # No GT bout: 1.0 for a correct absence (system correctly detected
            # nothing), 0.0 for a false detection (system predicted bouts that
            # don't exist in GT)
            value = 1.0 if behavior_components["n_fp"] == 0 else 0.0
            metrics[behavior] = dict.fromkeys(METRIC_KEYS, value)
        else:
            metrics[behavior] = _metrics_from_components(behavior_components)
    return metrics


def calculate_components_for_each_file(
    preprocessed_data: dict, matching: str = "greedy", *, missed_bouts: str = "exclude"
) -> dict:
    """Compute the BANOS metric components for each file in the preprocessed data dict."""
    _check_options(matching, missed_bouts)
    return {
        file_name: compute_behavior_components(
            pred, gt, matching=matching, missed_bouts=missed_bouts
        )
        for file_name, (pred, gt) in preprocessed_data.items()
    }


def calculate_banos_for_each_file(
    preprocessed_data: dict, matching: str = "greedy", *, missed_bouts: str = "exclude"
) -> dict:
    """Compute BANOS metrics for each file in the preprocessed data dict."""
    _check_options(matching, missed_bouts)
    return {
        file_name: compute_behavior_metrics(pred, gt, matching=matching, missed_bouts=missed_bouts)
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
    group: dict = {}
    overall: dict = {k: [] for k in METRIC_KEYS}

    for behaviors in file_metrics.values():
        for behavior, m in behaviors.items():
            if behavior not in group:
                group[behavior] = {k: [] for k in METRIC_KEYS}
            for key in METRIC_KEYS:
                val = m.get(key, float("nan"))
                group[behavior][key].append(val)
                overall[key].append(val)

    for behavior in group:
        for key in METRIC_KEYS:
            group[behavior][key] = _nanmean(group[behavior][key])

    return group, {key: _nanmean(vals) for key, vals in overall.items()}


def pool_components(file_components: dict) -> tuple[dict, dict]:
    """Pool the metric components of all files and score each behavior once.

    For each behavior, the TP, FP and FN counts are summed over the files and
    give precision, recall and F1; SO, TP and IC are the means of all their
    terms over all files. A file without the behavior adds its false bouts to
    FP and no SO, TP or IC term: the 1.0/0.0 absent-behavior rule of the
    per-file metrics does not apply. A behavior with no GT bout and no
    predicted bout in any file is NaN on all six metrics.

    Parameters
    ----------
    file_components : {file_name: {behavior: components}}
        As returned by ``calculate_components_for_each_file``.

    Returns
    -------
    group_metrics  : {behavior: {metric: pooled_value}}
    overall_metrics: {metric: mean_of_pooled_values_across_behaviors} (NaN excluded)
    """
    pooled: dict = {}
    for behaviors in file_components.values():
        for behavior, components in behaviors.items():
            if behavior not in pooled:
                pooled[behavior] = {
                    "n_tp": 0,
                    "n_fp": 0,
                    "n_fn": 0,
                    "so_terms": [],
                    "tp_terms": [],
                    "ic_terms": [],
                }
            for key in ("n_tp", "n_fp", "n_fn"):
                pooled[behavior][key] += components[key]
            for key in ("so_terms", "tp_terms", "ic_terms"):
                pooled[behavior][key].extend(components[key])

    group = {behavior: _metrics_from_components(p) for behavior, p in pooled.items()}
    overall = {key: _nanmean([m[key] for m in group.values()]) for key in METRIC_KEYS}
    return group, overall
