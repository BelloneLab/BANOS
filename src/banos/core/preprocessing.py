# src/banos/core/preprocessing.py
"""Data preprocessing utilities for BANOS."""

from __future__ import annotations

import pandas as pd


def is_logical_column(column: pd.Series) -> bool:
    """Return True if column contains only 0s and 1s."""
    return column.isin([0, 1]).all()


def drop_non_logical_columns(matrix: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
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


def preprocess_data(data_dict: dict[str, tuple[pd.DataFrame, pd.DataFrame]]) -> tuple[dict, dict]:
    """Preprocess prediction and ground truth DataFrames.

    Fills NaN with 0, drops non-binary columns, aligns headers.

    Parameters
    ----------
    data_dict : {filename: (pred_df, gt_df)}

    Returns
    -------
    data_dict : cleaned data
    dropped_info : per-file info about dropped columns
    """
    data_dict = dict(data_dict)  # avoid mutating caller's dict
    dropped_info: dict = {}
    for file_name, (pred, gt) in data_dict.items():
        pred = pred.fillna(0)
        gt = gt.fillna(0)
        pred, pred_dropped = drop_non_logical_columns(pred)
        gt, gt_dropped = drop_non_logical_columns(gt)
        pred, gt, header_dropped = match_headers(pred, gt)
        data_dict[file_name] = (pred, gt)
        dropped_info[file_name] = {
            "pred_dropped": pred_dropped,
            "gt_dropped": gt_dropped,
            "header_dropped": header_dropped,
        }
    return data_dict, dropped_info
