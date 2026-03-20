# tests/test_preprocessing.py
"""Unit tests for banos.core.preprocessing.

WHY these tests matter
----------------------
Preprocessing is the boundary between raw user data and the BANOS pipeline.
If non-binary columns are silently kept, or headers are not aligned, every
downstream metric will be computed on wrong data with no error raised.
These tests verify that data cleaning is both correct and non-destructive
(the caller's dict object must not be replaced or mutated unexpectedly).

Key behaviours tested:
- Binary detection: 0/1 int and float are accepted; 2, -1, or NaN are not.
- Column dropping: non-binary columns are removed and their names reported.
- Header alignment: only behaviors present in both pred and GT are kept.
- NaN filling: missing values are replaced with 0 before further processing.
"""

import pandas as pd

from banos.core.preprocessing import (
    drop_non_logical_columns,
    is_logical_column,
    match_headers,
    preprocess_data,
)


def test_is_logical_column_valid():
    """Standard binary column (int 0/1) is accepted."""
    assert is_logical_column(pd.Series([0, 1, 0, 1]))


def test_is_logical_column_all_zeros():
    assert is_logical_column(pd.Series([0, 0, 0]))


def test_is_logical_column_all_ones():
    assert is_logical_column(pd.Series([1, 1, 1]))


def test_is_logical_column_with_float_binary():
    """Float 0.0/1.0 is accepted — CSV files often load binary columns as floats."""
    assert is_logical_column(pd.Series([0.0, 1.0, 0.0]))


def test_is_logical_column_invalid_contains_two():
    """Value of 2 is rejected — prevents treating count or confidence data as binary."""
    assert not is_logical_column(pd.Series([0, 1, 2]))


def test_is_logical_column_invalid_negative():
    assert not is_logical_column(pd.Series([-1, 0, 1]))


def test_drop_non_logical_columns_removes_invalid():
    """Non-binary column 'b' is dropped and listed in dropped; 'a' and 'c' survive."""
    df = pd.DataFrame({"a": [0, 1], "b": [0, 2], "c": [1, 0]})
    result, dropped = drop_non_logical_columns(df)
    assert list(result.columns) == ["a", "c"]
    assert "b" in dropped
    assert "a" not in dropped


def test_drop_non_logical_columns_keeps_all_if_valid():
    df = pd.DataFrame({"a": [0, 1], "b": [1, 0]})
    result, dropped = drop_non_logical_columns(df)
    assert list(result.columns) == ["a", "b"]
    assert dropped == []


def test_match_headers_keeps_common_only():
    pred = pd.DataFrame({"a": [0], "b": [1], "c": [0]})
    gt = pd.DataFrame({"a": [1], "c": [0], "d": [1]})
    p, g, dropped = match_headers(pred, gt)
    assert set(p.columns) == {"a", "c"}
    assert set(g.columns) == {"a", "c"}
    assert set(dropped) == {"b", "d"}


def test_match_headers_no_common():
    pred = pd.DataFrame({"a": [0]})
    gt = pd.DataFrame({"b": [1]})
    p, g, dropped = match_headers(pred, gt)
    assert len(p.columns) == 0
    assert len(g.columns) == 0
    assert set(dropped) == {"a", "b"}


def test_match_headers_all_common():
    pred = pd.DataFrame({"a": [0], "b": [1]})
    gt = pd.DataFrame({"a": [1], "b": [0]})
    p, g, dropped = match_headers(pred, gt)
    assert set(p.columns) == {"a", "b"}
    assert dropped == []


def test_preprocess_data_fills_nan():
    pred = pd.DataFrame({"a": [float("nan"), 1.0, 0.0]})
    gt = pd.DataFrame({"a": [1.0, float("nan"), 0.0]})
    result, _ = preprocess_data({"f1": (pred, gt)})
    pred_out, gt_out = result["f1"]
    assert pred_out["a"].isna().sum() == 0
    assert gt_out["a"].isna().sum() == 0


def test_preprocess_data_does_not_mutate_caller_dict():
    """The caller's dict object must not be replaced — only internal copies are modified.

    WHY: user code often reuses the same dict across multiple calls. If preprocess_data
    replaced the dict in-place, the second call would receive already-processed data,
    causing subtle double-processing bugs.
    """
    pred = pd.DataFrame({"a": [0, 1]})
    gt = pd.DataFrame({"a": [1, 0]})
    original = {"f1": (pred, gt)}
    original_id = id(original)
    preprocess_data(original)
    assert id(original) == original_id  # same dict object, not mutated internally


def test_preprocess_data_drops_non_logical():
    pred = pd.DataFrame({"a": [0, 1], "b": [0, 2]})
    gt = pd.DataFrame({"a": [1, 0], "b": [1, 1]})
    result, info = preprocess_data({"f1": (pred, gt)})
    pred_out, _ = result["f1"]
    assert "b" not in pred_out.columns
    assert "b" in info["f1"]["pred_dropped"]
