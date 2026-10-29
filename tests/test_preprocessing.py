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
- Input checks: ValueError when a file's prediction and ground truth differ in
  length or have no frame; a UserWarning for each NaN replacement and each
  dropped column, naming the file and the column.
"""

import warnings

import pandas as pd
import pytest

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
    with pytest.warns(UserWarning, match="replaced by 0"):
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
    with pytest.warns(UserWarning, match="dropped"):
        result, info = preprocess_data({"f1": (pred, gt)})
    pred_out, _ = result["f1"]
    assert "b" not in pred_out.columns
    assert "b" in info["f1"]["pred_dropped"]


# --- input checks: errors and warnings ---


def _preprocess_with_warnings(data_dict: dict) -> tuple[dict, dict, list[str]]:
    """Run preprocess_data and also return the messages of the UserWarnings it emits."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result, info = preprocess_data(data_dict)
    messages = [str(w.message) for w in caught if w.category is UserWarning]
    return result, info, messages


def test_preprocess_data_raises_on_length_mismatch():
    """Prediction and ground truth of a file must have the same number of frames (rows)."""
    pred = pd.DataFrame({"a": [0, 1, 0]})
    gt = pd.DataFrame({"a": [0, 1, 0, 0]})
    with pytest.raises(ValueError, match="File 'f1': the prediction has 3 frames but"):
        preprocess_data({"ok": (gt, gt.copy()), "f1": (pred, gt)})


def test_preprocess_data_raises_on_file_without_frame():
    empty = pd.DataFrame({"a": []})
    with pytest.raises(ValueError, match="File 'f1' has no frame"):
        preprocess_data({"f1": (empty, empty.copy())})


def test_preprocess_data_warns_for_each_nan_column():
    """Each column with NaN replaced by 0 is reported with its file, side and count."""
    pred = pd.DataFrame({"a": [float("nan"), 1.0, float("nan")], "b": [0, 1, 0]})
    gt = pd.DataFrame({"a": [1.0, 0.0, 0.0], "b": [0.0, float("nan"), 1.0]})
    result, _, messages = _preprocess_with_warnings({"f1": (pred, gt)})
    assert messages == [
        "File 'f1': 2 NaN value(s) in prediction column 'a' replaced by 0.",
        "File 'f1': 1 NaN value(s) in ground truth column 'b' replaced by 0.",
    ]
    assert result["f1"][0]["a"].tolist() == [0.0, 1.0, 0.0]


def test_preprocess_data_warns_for_each_dropped_column():
    """Each dropped column is reported: values other than 0/1 (a probability, inf)
    or a column missing, or dropped, on the other side."""
    pred = pd.DataFrame(
        {"a": [0, 1, 0], "prob": [0.2, 0.9, 0.1], "only_pred": [0, 1, 1], "inf": [0, 1, 0]}
    )
    gt = pd.DataFrame(
        {"a": [0, 1, 1], "prob": [0, 1, 0], "only_gt": [1, 0, 0], "inf": [0, float("inf"), 1]}
    )
    result, info, messages = _preprocess_with_warnings({"f1": (pred, gt)})
    assert list(result["f1"][0].columns) == ["a"]
    assert list(result["f1"][1].columns) == ["a"]
    assert info["f1"]["pred_dropped"] == ["prob"]
    assert info["f1"]["gt_dropped"] == ["inf"]
    assert messages == [
        "File 'f1': prediction column 'prob' dropped (values other than 0 and 1).",
        "File 'f1': ground truth column 'inf' dropped (values other than 0 and 1).",
        "File 'f1': prediction column 'only_pred' dropped (missing or invalid in the ground truth).",
        "File 'f1': prediction column 'inf' dropped (missing or invalid in the ground truth).",
        "File 'f1': ground truth column 'prob' dropped (missing or invalid in the prediction).",
        "File 'f1': ground truth column 'only_gt' dropped (missing or invalid in the prediction).",
    ]


def test_preprocess_data_valid_input_emits_no_warning():
    """Binary columns (int, float or bool) on both sides, same length: no warning."""
    pred = pd.DataFrame({"a": [0, 1, 1], "b": [True, False, True]})
    gt = pd.DataFrame({"a": [0.0, 1.0, 0.0], "b": [1, 0, 0]})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _, info = preprocess_data({"f1": (pred, gt)})
    assert info["f1"] == {"pred_dropped": [], "gt_dropped": [], "header_dropped": []}
