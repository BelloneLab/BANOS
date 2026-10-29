# src/banos/core/preprocessing.py
"""Data preprocessing utilities for BANOS."""

from __future__ import annotations

import warnings
from collections.abc import Hashable

import pandas as pd


def is_logical_column(column: pd.Series) -> bool:
    """Return True if column contains only 0s and 1s."""
    return bool(column.isin([0, 1]).all())


def drop_non_logical_columns(matrix: pd.DataFrame) -> tuple[pd.DataFrame, list[Hashable]]:
    """Drop columns that do not contain only binary (0/1) values.

    Returns
    -------
    matrix : DataFrame with non-logical columns removed
    dropped : list of dropped column names
    """
    dropped = [col for col in matrix if not is_logical_column(matrix[col])]
    return matrix.drop(columns=dropped), dropped


def match_headers(
    pred_matrix: pd.DataFrame, gt_matrix: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Retain only columns present in both matrices.

    Returns
    -------
    pred_matrix : filtered prediction DataFrame
    gt_matrix   : filtered ground truth DataFrame
    dropped     : list of column names present in only one matrix
    """
    common = pred_matrix.columns.intersection(gt_matrix.columns)
    dropped = list(set(pred_matrix.columns).symmetric_difference(gt_matrix.columns))
    return pred_matrix[common], gt_matrix[common], dropped


def _warn(message: str) -> None:
    # Level 4 is the line that called preprocess_data() or score(): the levels
    # below are _warn, _preprocess_data, then preprocess_data or score.
    warnings.warn(message, UserWarning, stacklevel=4)


def preprocess_data(data_dict: dict[str, tuple[pd.DataFrame, pd.DataFrame]]) -> tuple[dict, dict]:
    """Preprocess prediction and ground truth DataFrames.

    Fills NaN with 0, drops non-binary columns, aligns headers.
    A UserWarning naming the file and the column is emitted for each column
    whose NaN values are replaced by 0 (with their count) and for each dropped
    column (values other than 0 and 1, or a column present on one side only).

    Parameters
    ----------
    data_dict : {filename: (pred_df, gt_df)}

    Returns
    -------
    data_dict : cleaned data
    dropped_info : per-file info about dropped columns

    Raises
    ------
    ValueError
        If the prediction and the ground truth of a file differ in length
        (number of rows, i.e. frames), or a file has no frame.
    """
    return _preprocess_data(data_dict)


def _preprocess_data(data_dict: dict[str, tuple[pd.DataFrame, pd.DataFrame]]) -> tuple[dict, dict]:
    # Body of preprocess_data(). score() calls it directly, so that the
    # warnings point at the caller's line in both cases (see _warn).
    data_dict = dict(data_dict)  # avoid mutating caller's dict
    dropped_info: dict = {}
    for file_name, (pred, gt) in data_dict.items():
        if len(pred) != len(gt):
            raise ValueError(
                f"File {file_name!r}: the prediction has {len(pred)} frames "
                f"but the ground truth has {len(gt)}."
            )
        if len(pred) == 0:
            raise ValueError(f"File {file_name!r} has no frame.")
        for side, matrix in (("prediction", pred), ("ground truth", gt)):
            for column, n_nan in matrix.isna().sum().items():
                if n_nan:
                    _warn(
                        f"File {file_name!r}: {n_nan} NaN value(s) in {side} column "
                        f"{column!r} replaced by 0."
                    )
        pred = pred.fillna(0)
        gt = gt.fillna(0)
        pred, pred_dropped = drop_non_logical_columns(pred)
        gt, gt_dropped = drop_non_logical_columns(gt)
        for side, dropped in (("prediction", pred_dropped), ("ground truth", gt_dropped)):
            for column in dropped:
                _warn(
                    f"File {file_name!r}: {side} column {column!r} dropped "
                    "(values other than 0 and 1)."
                )
        for column in pred.columns.difference(gt.columns, sort=False):
            _warn(
                f"File {file_name!r}: prediction column {column!r} dropped "
                "(missing or invalid in the ground truth)."
            )
        for column in gt.columns.difference(pred.columns, sort=False):
            _warn(
                f"File {file_name!r}: ground truth column {column!r} dropped "
                "(missing or invalid in the prediction)."
            )
        pred, gt, header_dropped = match_headers(pred, gt)
        data_dict[file_name] = (pred, gt)
        dropped_info[file_name] = {
            "pred_dropped": pred_dropped,
            "gt_dropped": gt_dropped,
            "header_dropped": header_dropped,
        }
    return data_dict, dropped_info
