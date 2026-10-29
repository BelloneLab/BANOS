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

__version__ = "1.0.0"

import pandas as pd

from banos.core.preprocessing import _preprocess_data, preprocess_data
from banos.pipeline import (
    _check_options,
    aggregate_metrics,
    calculate_banos_for_each_file,
    calculate_components_for_each_file,
    compute_behavior_components,
    compute_behavior_metrics,
    pool_components,
)

__all__ = [
    "score",
    "preprocess_data",
    "compute_behavior_metrics",
    "calculate_banos_for_each_file",
    "aggregate_metrics",
    "compute_behavior_components",
    "calculate_components_for_each_file",
    "pool_components",
    "__version__",
]


def score(
    data: pd.DataFrame | dict,
    gt: pd.DataFrame | None = None,
    *,
    matching: str = "greedy",
    missed_bouts: str = "exclude",
    aggregation: str = "per_file",
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
        'greedy': each predicted bout, in time order, takes the first unmatched
        GT bout it overlaps (default)
        'optimal': Hungarian algorithm (scipy), the largest number of matched
        pairs. On bouts read from 0/1 columns, as here, greedy matching already
        reaches it, so both give the same results.
    missed_bouts : {'exclude', 'zero'}
        How SO, TP and IC count a GT bout with no predicted frame inside it.
        'exclude': left out of their averages (default)
        'zero': one term equal to 0 in each of them
        Precision, recall and F1 do not depend on this option.
    aggregation : {'per_file', 'pooled'}
        How the metrics are combined.
        'per_file': each file is scored on its own, then averaged (default)
        'pooled': each behavior is scored once on the bout counts and terms
        of all files (see ``pool_components``)

    Returns
    -------
    Single file : dict
        ``{behavior: {precision, recall, f1_score, so, tp, ic}}``
    Multi file  : tuple[dict, dict]
        ``(group_metrics, overall_metrics)``: ``group_metrics`` has the same
        form as the single-file dict; ``overall_metrics`` is
        ``{metric: value}``.

    Notes
    -----
    With ``aggregation='per_file'``, a behavior with no GT bout in a file scores
    1.0 on all six metrics if nothing is predicted there and 0.0 otherwise.
    ``group_metrics`` averages each behavior over the files and
    ``overall_metrics`` averages every (file, behavior) cell, NaN excluded.
    With ``aggregation='pooled'``, this 1.0/0.0 rule does not apply and
    ``overall_metrics`` averages the pooled behaviors, NaN excluded.
    A metric is NaN when it is undefined: precision when nothing is predicted,
    recall when there is no GT bout (pooled), F1 when there is no bout at all
    (pooled), SO, TP and IC when they have no term (no overlap, or no found GT
    bout).

    An unknown ``matching``, ``missed_bouts`` or ``aggregation`` value raises
    ValueError before the data is read.

    The input goes through ``preprocess_data``: a ValueError is raised when the
    prediction and the ground truth of a file differ in length or a file has no
    frame, and a UserWarning, naming the file and the column, is emitted for each
    column dropped and for each column whose NaN values are replaced by 0.
    """
    _check_options(matching, missed_bouts)
    if aggregation not in ("per_file", "pooled"):
        raise ValueError(f"Unknown aggregation: {aggregation!r}. Use 'per_file' or 'pooled'.")

    if isinstance(data, pd.DataFrame):
        if gt is None:
            raise ValueError("When 'data' is a DataFrame, 'gt' must be provided.")
        data_dict = {"single": (data, gt)}
        data_dict, _ = _preprocess_data(data_dict)
        if aggregation == "pooled":
            components = compute_behavior_components(
                data_dict["single"][0],
                data_dict["single"][1],
                matching=matching,
                missed_bouts=missed_bouts,
            )
            group_metrics, _ = pool_components({"single": components})
            return group_metrics
        return compute_behavior_metrics(
            data_dict["single"][0],
            data_dict["single"][1],
            matching=matching,
            missed_bouts=missed_bouts,
        )

    # Multi-file path
    data_dict, _ = _preprocess_data(dict(data))
    if aggregation == "pooled":
        file_components = calculate_components_for_each_file(
            data_dict, matching=matching, missed_bouts=missed_bouts
        )
        return pool_components(file_components)
    file_metrics = calculate_banos_for_each_file(
        data_dict, matching=matching, missed_bouts=missed_bouts
    )
    return aggregate_metrics(file_metrics)
