# tests/test_pipeline.py
"""Integration tests for banos.score() and the three-stage pipeline.

WHY these tests matter
----------------------
banos.score() is the public entry point. These tests verify end-to-end
behaviour: correct return types, all 6 metrics present, NaN exclusion in
aggregate_metrics, value range [0, 1], error handling for bad inputs,
and version consistency.

Pipeline stages tested together:
  preprocess_data -> calculate_banos_for_each_file -> aggregate_metrics
  preprocess_data -> calculate_components_for_each_file -> pool_components
  (the second chain is aggregation='pooled')

The test_aggregate_metrics_excludes_nan test confirms that NaN cells (a metric
undefined for a behavior in a recording, e.g. precision when nothing is
predicted there) are left out of the group/overall averages (nanmean).
A recording with no GT bout of a behavior is not NaN with the default
per-file aggregation: it scores 1.0 if nothing is predicted and 0.0 otherwise.
"""

import math
import tomllib
import warnings
from pathlib import Path

import pandas as pd
import pytest

import banos
from banos.core.matching import calculate_tp_fp_fn
from banos.pipeline import (
    aggregate_metrics,
    calculate_components_for_each_file,
    compute_behavior_components,
    pool_components,
)

PRED = pd.DataFrame(
    {
        "event1": [0, 1, 1, 1, 0, 0, 1, 1, 0],
        "event2": [1, 1, 0, 0, 0, 1, 1, 0, 0],
    }
)
GT = pd.DataFrame(
    {
        "event1": [0, 0, 1, 1, 1, 0, 1, 0, 0],
        "event2": [1, 0, 0, 0, 1, 1, 0, 0, 0],
    }
)

# Hand-made videos of 60 frames with three real bouts of one behavior ("evt").
N_FRAMES = 60
REAL_BOUTS = [(5, 9), (25, 29), (45, 49)]


def _frames(bouts: list[tuple[int, int]]) -> list[int]:
    """0/1 sequence of N_FRAMES frames, 1 on every frame of the (start, end) bouts."""
    sequence = [0] * N_FRAMES
    for start, end in bouts:
        sequence[start : end + 1] = [1] * (end - start + 1)
    return sequence


def _video(
    pred_bouts: list[tuple[int, int]], gt_bouts: list[tuple[int, int]] = REAL_BOUTS
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(pred_df, gt_df) pair of one video from its predicted and real bouts."""
    return pd.DataFrame({"evt": _frames(pred_bouts)}), pd.DataFrame({"evt": _frames(gt_bouts)})


def test_score_single_file_returns_dict():
    result = banos.score(PRED, GT)
    assert isinstance(result, dict)
    assert set(result.keys()) == {"event1", "event2"}


def test_score_single_file_has_all_metrics():
    result = banos.score(PRED, GT)
    for behavior in result:
        assert set(result[behavior].keys()) == {"precision", "recall", "f1_score", "so", "tp", "ic"}


def test_score_multi_file_returns_tuple():
    result = banos.score({"f1": (PRED, GT), "f2": (PRED.copy(), GT.copy())})
    assert isinstance(result, tuple) and len(result) == 2
    group_m, overall_m = result
    assert isinstance(group_m, dict)
    assert isinstance(overall_m, dict)


def test_score_requires_gt_for_single_df():
    with pytest.raises(ValueError):
        banos.score(PRED)


def test_score_optimal_matching():
    result = banos.score(PRED, GT, matching="optimal")
    assert isinstance(result, dict)


def test_score_all_metrics_in_range():
    """All finite metric values must lie in [0, 1]; NaN is allowed (undefined case).

    WHY: values outside [0, 1] indicate a formula error (e.g., division producing
    values > 1). NaN is explicitly allowed because a metric can be undefined for
    a behavior that has GT bouts: precision when nothing is predicted, SO and TP
    when no predicted bout overlaps a GT bout, IC when no GT bout longer than
    one frame is found.
    """
    result = banos.score(PRED, GT)
    for behavior, metrics in result.items():
        for key, val in metrics.items():
            if not math.isnan(val):
                assert 0.0 <= val <= 1.0, f"{behavior} {key} = {val} out of [0,1]"


def test_score_invalid_matching_raises():
    with pytest.raises(ValueError):
        banos.score(PRED, GT, matching="invalid")


def test_aggregate_metrics_excludes_nan():
    """NaN values in file metrics must be excluded from group and overall averages.

    WHY: f2 has all-NaN metrics (every metric undefined for that behavior in that
    recording). If NaN were averaged as 0, the average would be pulled toward
    0, making the system appear worse than it actually is. The result must equal
    only f1's values, as if f2 were never processed for that behavior.
    """
    file_metrics = {
        "f1": {
            "evt": {
                "precision": 0.8,
                "recall": 0.6,
                "f1_score": 0.686,
                "so": 0.5,
                "tp": 0.7,
                "ic": 0.9,
            }
        },
        "f2": {
            "evt": {
                "precision": float("nan"),
                "recall": float("nan"),
                "f1_score": float("nan"),
                "so": float("nan"),
                "tp": float("nan"),
                "ic": float("nan"),
            }
        },
    }
    group, overall = aggregate_metrics(file_metrics)
    # f2 has all NaN -> should be excluded from average
    assert abs(group["evt"]["precision"] - 0.8) < 1e-10
    assert abs(overall["precision"] - 0.8) < 1e-10


def test_score_version():
    """banos.__version__ is the version declared in pyproject.toml.

    WHY: the version is written in both files; a release that bumps only one
    of them would publish a package whose __version__ is wrong.
    """
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject, "rb") as f:
        declared = tomllib.load(f)["project"]["version"]
    assert banos.__version__ == declared


FRAME_INDEXES = {
    "1-based": range(1, N_FRAMES + 1),
    "reversed": range(N_FRAMES - 1, -1, -1),
    "float": [frame / 30 for frame in range(N_FRAMES)],
    "string": [f"frame_{frame}" for frame in range(N_FRAMES)],
}


@pytest.mark.parametrize("kind", FRAME_INDEXES)
def test_score_reads_frames_by_position_whatever_the_index(kind):
    """The DataFrame index is ignored: every metric reads the frames by position.

    Real bouts (5,9), (25,29), (45,49); predicted (5,9), (25,27), (45,49).
    The second real bout has one switch (frames 27-28) in length 4, so
    IC = (1 + 3/4 + 1) / 3 = 11/12 with the default index, and must stay so
    with frames numbered from 1, reversed labels, times in seconds or strings.
    Read by label, IC was 2/3 (1-based), 1.0 (reversed) or a KeyError.
    """
    pred, gt = _video([(5, 9), (25, 27), (45, 49)])
    expected = banos.score(pred, gt)
    assert abs(expected["evt"]["ic"] - 11 / 12) < 1e-10

    index = pd.Index(FRAME_INDEXES[kind])
    assert banos.score(pred.set_axis(index), gt.set_axis(index)) == expected


def test_score_missed_bouts_zero():
    """missed_bouts='zero' adds a 0 term per missed real bout to SO, TP and IC only.

    Real bouts (5,9), (25,29), (45,49); predicted (5,9) and (26,29): the
    third real bout is missed. Terms of the found bouts: SO 1 and 4/5,
    TP 1 and 1/2, IC 1 and 3/4 (one switch, frames 25-26, in length 4).
    exclude: SO 0.9, TP 0.75, IC 0.875; zero: SO 1.8/3, TP 1.5/3, IC 1.75/3.
    Detection is the same in both modes: TP 2, FN 1 -> P 1, R 2/3, F1 0.8.
    """
    video = _video([(5, 9), (26, 29)])
    exclude = banos.score(*video)["evt"]
    zero = banos.score(*video, missed_bouts="zero")["evt"]
    expected_exclude = {"so": 0.9, "tp": 0.75, "ic": 0.875}
    expected_zero = {"so": 1.8 / 3, "tp": 1.5 / 3, "ic": 1.75 / 3}
    for key in expected_exclude:
        assert abs(exclude[key] - expected_exclude[key]) < 1e-10, key
        assert abs(zero[key] - expected_zero[key]) < 1e-10, key
    for key in ("precision", "recall", "f1_score"):
        assert exclude[key] == zero[key]
    assert abs(zero["f1_score"] - 0.8) < 1e-10

    group, _ = banos.score({"v1": video, "v2": video}, missed_bouts="zero")
    assert abs(group["evt"]["so"] - 0.6) < 1e-10


def test_missed_bouts_zero_keeps_absent_behavior_rule():
    """With no real bout in a file, 'zero' keeps 1.0 (nothing predicted) or 0.0 (false bouts)."""
    absent = banos.score(*_video([], []), missed_bouts="zero")["evt"]
    false_detection = banos.score(*_video([(5, 9)], []), missed_bouts="zero")["evt"]
    assert set(absent.values()) == {1.0}
    assert set(false_detection.values()) == {0.0}


def test_score_invalid_missed_bouts_raises():
    with pytest.raises(ValueError, match="Unknown missed_bouts option"):
        banos.score(PRED, GT, missed_bouts="drop")


NO_COLUMN = pd.DataFrame(index=range(N_FRAMES))


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            lambda: banos.score(NO_COLUMN, NO_COLUMN, missed_bouts="drop"), id="no-column"
        ),
        pytest.param(lambda: banos.score(PRED * 0.5, GT, missed_bouts="drop"), id="all-dropped"),
        pytest.param(lambda: banos.score({}, missed_bouts="drop"), id="no-file"),
        pytest.param(
            lambda: banos.compute_behavior_metrics(NO_COLUMN, NO_COLUMN, missed_bouts="drop"),
            id="compute_behavior_metrics",
        ),
        pytest.param(
            lambda: banos.calculate_banos_for_each_file({}, missed_bouts="drop"),
            id="calculate_banos_for_each_file",
        ),
    ],
)
def test_invalid_missed_bouts_raises_without_any_column(call):
    """An unknown missed_bouts raises even when no column reaches the metrics.

    No behavior column, every column dropped by preprocessing (values 0 and
    0.5), or no file at all: the option is checked on entry, not only by the
    metric functions.
    """
    with pytest.raises(ValueError, match="Unknown missed_bouts option"):
        call()


def test_file_with_only_false_bouts_scores_f1_zero():
    """A file whose predicted bouts all miss the real bouts scores F1 0 and stays in the mean.

    Both models predict video 1 exactly. In video 2, model C predicts three
    bouts that overlap no real bout (TP 0, FP 3, FN 3: P 0, R 0, F1 0) and
    model D finds two of the three real bouts (TP 2, FN 1: P 1, R 2/3, F1 0.8).
    Per-file means: C (1 + 0) / 2 = 0.5, D (1 + 0.8) / 2 = 0.9. Before 1.1.0,
    C's video 2 scored F1 NaN, left the mean, and C got 1.0.
    """
    false_bouts = [(15, 19), (35, 39), (52, 56)]
    c_video2 = banos.score(*_video(false_bouts))["evt"]
    assert c_video2["precision"] == 0.0
    assert c_video2["recall"] == 0.0
    assert c_video2["f1_score"] == 0.0

    group_c, _ = banos.score({"v1": _video(REAL_BOUTS), "v2": _video(false_bouts)})
    group_d, _ = banos.score({"v1": _video(REAL_BOUTS), "v2": _video(REAL_BOUTS[:2])})
    assert abs(group_c["evt"]["f1_score"] - 0.5) < 1e-10
    assert abs(group_d["evt"]["f1_score"] - 0.9) < 1e-10

    # Pooled: C has TP 3, FP 3, FN 3 -> F1 0.5; D has TP 5, FP 0, FN 1 ->
    # P 1, R 5/6, F1 10/11.
    pooled_c, _ = banos.score(
        {"v1": _video(REAL_BOUTS), "v2": _video(false_bouts)}, aggregation="pooled"
    )
    pooled_d, _ = banos.score(
        {"v1": _video(REAL_BOUTS), "v2": _video(REAL_BOUTS[:2])}, aggregation="pooled"
    )
    assert abs(pooled_c["evt"]["f1_score"] - 0.5) < 1e-10
    assert abs(pooled_d["evt"]["f1_score"] - 10 / 11) < 1e-10


def test_silent_model_on_bundled_data(all_recordings):
    """A model that predicts nothing scores F1 0 on every recording with the behavior.

    Its only non-zero F1 cells are the correct absences (1.0). In the bundled
    data, attack is absent from 5 of the 10 recordings and mount from 4, while
    investigation and other are in all 10. Per-file means: attack 5/10 = 0.5,
    mount 4/10 = 0.4, investigation 0, other 0; overall F1 = 9 cells of 40 =
    0.225. Before 1.1.0 the recordings with the behavior scored F1 NaN and left
    the means: attack, mount and overall F1 were 1.0.

    IC has no found bout to average in any recording with the behavior, so
    investigation and other (present in all 10) have IC NaN, not 1.0.
    """
    data = {f"Recording_{n}": (gt * 0, gt) for n, (_, gt) in all_recordings.items()}
    group, overall = banos.score(data)
    expected = {"attack": 0.5, "investigation": 0.0, "mount": 0.4, "other": 0.0}
    for behavior, f1 in expected.items():
        assert abs(group[behavior]["f1_score"] - f1) < 1e-10, behavior
    assert abs(overall["f1_score"] - 0.225) < 1e-10
    assert math.isnan(group["investigation"]["ic"])
    assert math.isnan(group["other"]["ic"])

    # Pooled: TP 0, FP 0, FN > 0 for every behavior, so F1 is 0 everywhere;
    # SO, TP and IC have no term (NaN), or only 0 terms with missed_bouts='zero'.
    pooled, pooled_overall = banos.score(data, aggregation="pooled")
    assert {m["f1_score"] for m in pooled.values()} == {0.0}
    assert pooled_overall["f1_score"] == 0.0
    assert all(math.isnan(m["so"]) for m in pooled.values())
    pooled_zero, _ = banos.score(data, aggregation="pooled", missed_bouts="zero")
    assert {m["so"] for m in pooled_zero.values()} == {0.0}


# --- aggregation='pooled' ---


def test_pooled_counts_and_terms_equal_hand_sums():
    """Pooled metrics come from the bout counts and terms summed over the files.

    Video a: predicted (5,9) and (26,29) -> TP 2, FP 0, FN 1; SO terms 1, 4/5;
    TP terms 1, 1/2; IC terms 1, 3/4 (the third real bout is missed).
    Video b: predicted (15,19) and (45,49) -> TP 1, FP 1, FN 2; one term of 1
    for SO, TP and IC (bout 3 found exactly, bouts 1 and 2 missed).
    Pooled: TP 3, FP 1, FN 3 -> P 3/4, R 1/2, F1 0.6; SO (1 + 0.8 + 1) / 3,
    TP (1 + 0.5 + 1) / 3, IC (1 + 0.75 + 1) / 3. With missed_bouts='zero',
    the three missed bouts add three 0 terms: SO = 2.8 / 6.
    """
    data = {"a": _video([(5, 9), (26, 29)]), "b": _video([(15, 19), (45, 49)])}
    preprocessed, _ = banos.preprocess_data(data)
    components = calculate_components_for_each_file(preprocessed)
    assert components["a"]["evt"] == {
        "n_tp": 2,
        "n_fp": 0,
        "n_fn": 1,
        "so_terms": [1.0, 0.8],
        "tp_terms": [1.0, 0.5],
        "ic_terms": [1.0, 0.75],
    }
    assert components["b"]["evt"] == compute_behavior_components(*preprocessed["b"])["evt"]
    assert components["b"]["evt"] == {
        "n_tp": 1,
        "n_fp": 1,
        "n_fn": 2,
        "so_terms": [1.0],
        "tp_terms": [1.0],
        "ic_terms": [1.0],
    }

    group, overall = pool_components(components)
    expected = {
        "precision": 0.75,
        "recall": 0.5,
        "f1_score": 0.6,
        "so": 2.8 / 3,
        "tp": 2.5 / 3,
        "ic": 2.75 / 3,
    }
    for key, value in expected.items():
        assert abs(group["evt"][key] - value) < 1e-10, key
    assert overall == group["evt"]
    assert banos.score(data, aggregation="pooled") == (group, overall)

    zero, _ = banos.score(data, aggregation="pooled", missed_bouts="zero")
    assert abs(zero["evt"]["so"] - 2.8 / 6) < 1e-10


def test_pooled_absent_behavior():
    """In pooled mode a file without the behavior adds its false bouts to FP, nothing else.

    "evt" has the real bouts of video a only (P 1, R 2/3, F1 0.8); "rare"
    has no real bout anywhere.
    - Video c has neither behavior and predicts nothing: the pooled values
      do not move (per file, its correct absences would score 1.0).
    - "rare" with nothing predicted anywhere is NaN on all six metrics.
    - Video d predicts one false bout of each: "evt" gets FP 1, so
      P = R = F1 = 2/3 and SO, TP, IC are unchanged; "rare" gets P 0,
      F1 0, and R, SO, TP, IC NaN.
    overall_metrics is the mean over the behaviors, NaN excluded.
    """

    def video(evt_pred, evt_gt, rare_pred):
        pred = pd.DataFrame({"evt": _frames(evt_pred), "rare": _frames(rare_pred)})
        gt = pd.DataFrame({"evt": _frames(evt_gt), "rare": _frames([])})
        return pred, gt

    a = video([(5, 9), (26, 29)], REAL_BOUTS, [])
    c = video([], [], [])
    d = video([(15, 19)], [], [(40, 42)])

    alone, _ = banos.score({"a": a}, aggregation="pooled")
    group, overall = banos.score({"a": a, "c": c}, aggregation="pooled")
    assert group["evt"] == alone["evt"]
    assert abs(group["evt"]["f1_score"] - 0.8) < 1e-10
    assert all(math.isnan(value) for value in group["rare"].values())
    assert overall == group["evt"]

    per_file, _ = banos.score({"a": a, "c": c})
    assert abs(per_file["evt"]["f1_score"] - 0.9) < 1e-10  # (0.8 + 1.0) / 2
    assert per_file["rare"]["f1_score"] == 1.0

    group, overall = banos.score({"a": a, "c": c, "d": d}, aggregation="pooled")
    evt, rare = group["evt"], group["rare"]
    for key in ("precision", "recall", "f1_score"):
        assert abs(evt[key] - 2 / 3) < 1e-10, key
    for key in ("so", "tp", "ic"):
        assert evt[key] == alone["evt"][key], key
    assert rare["precision"] == 0.0
    assert rare["f1_score"] == 0.0
    assert all(math.isnan(rare[key]) for key in ("recall", "so", "tp", "ic"))
    assert abs(overall["f1_score"] - 1 / 3) < 1e-10  # (2/3 + 0) / 2
    assert abs(overall["recall"] - 2 / 3) < 1e-10  # rare's NaN recall is excluded
    assert overall["so"] == evt["so"]


def test_pooled_ranks_models_by_bouts_found():
    """Model A finds 6 of 12 real bouts, model B 3 of 12: both modes rank A first.

    Four videos with real bouts (5,9), (25,29), (45,49). A finds all three in
    video 1 and the first one in videos 2-4; B finds all three in video 1 and
    nothing else.
    Per file: A (1 + 3 * 0.5) / 4 = 0.625 (F1 0.5 from P 1, R 1/3),
    B (1 + 0 + 0 + 0) / 4 = 0.25. Pooled: A TP 6, FN 6 -> F1 2/3;
    B TP 3, FN 9 -> F1 0.4. Before 1.1.0, B's three empty videos scored F1 NaN
    and left the mean: B got 1.0 and ranked above A.
    """
    model_a = {"v1": _video(REAL_BOUTS)} | {f"v{k}": _video(REAL_BOUTS[:1]) for k in (2, 3, 4)}
    model_b = {"v1": _video(REAL_BOUTS)} | {f"v{k}": _video([]) for k in (2, 3, 4)}
    expected = {"per_file": (0.625, 0.25), "pooled": (2 / 3, 0.4)}
    for aggregation, (f1_a, f1_b) in expected.items():
        group_a, _ = banos.score(model_a, aggregation=aggregation)
        group_b, _ = banos.score(model_b, aggregation=aggregation)
        assert abs(group_a["evt"]["f1_score"] - f1_a) < 1e-10, aggregation
        assert abs(group_b["evt"]["f1_score"] - f1_b) < 1e-10, aggregation


def test_pooled_single_file_returns_dict_per_behavior():
    """A single DataFrame pair gives a dict per behavior in both aggregation modes.

    PRED and GT have real bouts of both behaviors, so pooling one file changes
    no value. Without real bouts, per file scores 1.0 (correct absence) and
    pooled NaN.
    """
    assert banos.score(PRED, GT, aggregation="pooled") == banos.score(PRED, GT)
    absent = banos.score(*_video([], []), aggregation="pooled")["evt"]
    assert all(math.isnan(value) for value in absent.values())


def test_score_reports_dropped_columns_and_rejects_length_mismatch():
    """score() no longer drops columns silently, and checks the lengths.

    A probability column (0 or 0.2) is dropped with a warning naming the file
    and the column, in single- and multi-file calls; before 1.1.0 the second
    file silently left the mean. A prediction shorter or longer than its
    ground truth raises ValueError (it used to raise KeyError or be scored).
    """
    pred, gt = _video(REAL_BOUTS)
    probability = pred * 0.2
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert banos.score(probability, gt) == {}
        group, _ = banos.score({"v1": (pred, gt), "v2": (probability, gt)})
    assert [str(w.message) for w in caught if w.category is UserWarning] == [
        "File 'single': prediction column 'evt' dropped (values other than 0 and 1).",
        "File 'single': ground truth column 'evt' dropped (missing or invalid in the prediction).",
        "File 'v2': prediction column 'evt' dropped (values other than 0 and 1).",
        "File 'v2': ground truth column 'evt' dropped (missing or invalid in the prediction).",
    ]
    assert group["evt"]["f1_score"] == 1.0  # from v1 alone
    with pytest.raises(ValueError, match="File 'single': the prediction has 45 frames"):
        banos.score(pred.iloc[:45], gt)
    with pytest.raises(ValueError, match="File 'v2': the prediction has 60 frames"):
        banos.score({"v1": (pred, gt), "v2": (pred, gt.iloc[:45])})


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(lambda data: banos.preprocess_data(data), id="preprocess_data"),
        pytest.param(lambda data: banos.score(*data["v"]), id="score-single"),
        pytest.param(
            lambda data: banos.score(*data["v"], aggregation="pooled"), id="score-single-pooled"
        ),
        pytest.param(lambda data: banos.score(data), id="score-several"),
        pytest.param(
            lambda data: banos.score(data, aggregation="pooled"), id="score-several-pooled"
        ),
    ],
)
def test_warnings_point_at_the_caller(call):
    """Warnings name the caller's line, through preprocess_data() and every score() path.

    Python shows a warning with the file and line it is attributed to; one
    stack level too few would name a line of banos instead of this file.
    """
    pred, gt = _video(REAL_BOUTS)
    data = {"v": (pred * 0.2, gt)}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        call(data)
    assert caught
    assert {Path(w.filename).resolve() for w in caught} == {Path(__file__).resolve()}


def test_score_invalid_aggregation_raises():
    with pytest.raises(ValueError, match="Unknown aggregation"):
        banos.score(PRED, GT, aggregation="pool")
    with pytest.raises(ValueError, match="Unknown aggregation"):
        banos.score({"f1": (PRED, GT)}, aggregation="pool")


@pytest.mark.parametrize(
    "call, message",
    [
        pytest.param(
            lambda: banos.score(NO_COLUMN, NO_COLUMN, matching="best"),
            "Unknown matching",
            id="score-no-column-matching",
        ),
        pytest.param(
            lambda: banos.score(PRED * 0.5, GT, matching="best"),
            "Unknown matching",
            id="score-all-dropped-matching",
        ),
        pytest.param(
            lambda: banos.score({}, matching="best"),
            "Unknown matching",
            id="score-no-file-matching",
        ),
        pytest.param(
            lambda: banos.score({}, aggregation="pool"),
            "Unknown aggregation",
            id="score-no-file-aggregation",
        ),
        pytest.param(
            lambda: compute_behavior_components(NO_COLUMN, NO_COLUMN, matching="best"),
            "Unknown matching",
            id="compute_behavior_components-matching",
        ),
        pytest.param(
            lambda: compute_behavior_components(NO_COLUMN, NO_COLUMN, missed_bouts="drop"),
            "Unknown missed_bouts",
            id="compute_behavior_components-missed_bouts",
        ),
        pytest.param(
            lambda: banos.compute_behavior_metrics(NO_COLUMN, NO_COLUMN, matching="best"),
            "Unknown matching",
            id="compute_behavior_metrics-matching",
        ),
        pytest.param(
            lambda: calculate_components_for_each_file({}, matching="best"),
            "Unknown matching",
            id="calculate_components_for_each_file-matching",
        ),
        pytest.param(
            lambda: calculate_components_for_each_file({}, missed_bouts="drop"),
            "Unknown missed_bouts",
            id="calculate_components_for_each_file-missed_bouts",
        ),
        pytest.param(
            lambda: banos.calculate_banos_for_each_file({}, matching="best"),
            "Unknown matching",
            id="calculate_banos_for_each_file-matching",
        ),
    ],
)
def test_invalid_options_raise_without_any_column(call, message):
    """Unknown matching, missed_bouts and aggregation values raise even when
    no column reaches the bout matching or the metrics (no column, every
    column dropped, no file)."""
    with pytest.raises(ValueError, match=message):
        call()


@pytest.mark.parametrize("aggregation", ["per_file", "pooled"])
@pytest.mark.parametrize("several_files", [False, True])
def test_score_passes_matching_to_bout_matching(monkeypatch, aggregation, several_files):
    """Every score() path hands the matching option to calculate_tp_fp_fn.

    Greedy and optimal matching count the same true positives on bouts read
    from frame sequences: such bouts never overlap one another, on either
    side, and then taking the first free overlapping real bout is already a
    maximum matching. No input of score() can tell the two apart by its
    numbers, so this test records the option that reaches the bout matching.
    """
    seen = []

    def spy(pred_bouts, gt_bouts, matching="greedy"):
        seen.append(matching)
        return calculate_tp_fp_fn(pred_bouts, gt_bouts, matching=matching)

    monkeypatch.setattr("banos.pipeline.calculate_tp_fp_fn", spy)
    if several_files:
        banos.score(
            {"f1": (PRED, GT), "f2": (PRED, GT)}, matching="optimal", aggregation=aggregation
        )
    else:
        banos.score(PRED, GT, matching="optimal", aggregation=aggregation)
    assert seen
    assert set(seen) == {"optimal"}
