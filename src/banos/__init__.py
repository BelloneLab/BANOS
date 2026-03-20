# src/banos/__init__.py
"""BANOS — Behavior ANnOtation Score.

Ethological metrics for evaluating behavior annotation quality:
Detection Accuracy (DA), Segment Overlap (SO), Temporal Precision (TP),
and Intra-bout Continuity (IC).

Usage
-----
>>> import banos
>>> metrics = banos.score(pred_df, gt_df)
>>> group_m, overall_m = banos.score({'rec1': (pred1, gt1), 'rec2': (pred2, gt2)})
"""

from __future__ import annotations

__version__ = "0.2.3"

import pandas as pd

from banos.core.preprocessing import preprocess_data
from banos.pipeline import (
    aggregate_metrics,
    calculate_banos_for_each_file,
    compute_behavior_metrics,
)

__all__ = [
    "score",
    "preprocess_data",
    "compute_behavior_metrics",
    "calculate_banos_for_each_file",
    "aggregate_metrics",
    "__version__",
]


def score(
    data: pd.DataFrame | dict,
    gt: pd.DataFrame | None = None,
    *,
    matching: str = "greedy",
) -> dict | tuple[dict, dict]:
    """Compute BANOS metrics for one or multiple annotation pairs.

    Parameters
    ----------
    data : pd.DataFrame or dict
        - Single DataFrame: prediction matrix (requires ``gt`` parameter)
        - Dict mapping filename → (pred_df, gt_df) for multiple files
    gt : pd.DataFrame, optional
        Ground truth DataFrame. Required when ``data`` is a single DataFrame.
    matching : {'greedy', 'optimal'}
        Bout matching algorithm.
        'greedy': first-match wins (fast, default, backward compatible)
        'optimal': Hungarian algorithm (scientifically optimal, requires scipy)

    Returns
    -------
    Single file : dict
        ``{behavior: {precision, recall, f1_score, so, tp, ic}}``
    Multi file  : tuple[dict, dict]
        ``(group_metrics, overall_metrics)``

    Notes
    -----
    Metrics return ``NaN`` when ground truth has no bouts for a given behavior.
    """
    if isinstance(data, pd.DataFrame):
        if gt is None:
            raise ValueError("When 'data' is a DataFrame, 'gt' must be provided.")
        data_dict = {"single": (data, gt)}
        data_dict, _ = preprocess_data(data_dict)
        return compute_behavior_metrics(
            data_dict["single"][0], data_dict["single"][1], matching=matching
        )

    # Multi-file path
    data_dict, _ = preprocess_data(dict(data))
    file_metrics = calculate_banos_for_each_file(data_dict, matching=matching)
    return aggregate_metrics(file_metrics)
