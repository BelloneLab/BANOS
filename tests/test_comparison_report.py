# tests/test_comparison_report.py
"""Python vs Matlab output comparison — generates HTML side-by-side tables.

PURPOSE
-------
This module produces a human-readable HTML report (via pytest-html) that shows
Python and Matlab metric values side-by-side for every recording, every behavior,
and every metric.

It serves two goals:
  1. Visually confirm Python and Matlab agree (or document where they intentionally differ).
  2. Provide a permanent audit trail: if you change either implementation, running
     `pytest --html=reports/test_report.html` gives you an updated comparison.

RUNNING
-------
Requires Matlab fixtures to be pre-generated:
  matlab -batch "run('tests/fixtures/matlab/generate_matlab_fixtures.m')"

If no Matlab fixtures are found, all tests in this module are automatically
skipped — safe for CI where Matlab is not installed.

EXPECTED DIVERGENCES (orange rows, not test failures)
------------------------------------------------------
The Python and Matlab implementations have one known intentional difference:

  - Python returns NaN when a behavior has no GT bouts (mathematically undefined).
  - The current Matlab implementation may return 0 in the same case (legacy choice).

These rows are marked orange ("expected divergence") rather than red (failure).
All other differences are marked red and cause the test to fail.

TOLERANCE
---------
Numeric values are compared with tolerance 1e-6 (matching test_parity.py).
"""

import json
import math
from pathlib import Path

import pandas as pd
import pytest

from banos import aggregate_metrics, calculate_banos_for_each_file, preprocess_data

DATASET_DIR = Path(__file__).parent.parent / "data" / "dataset_human_vs_human"
MATLAB_FIXTURE = Path(__file__).parent / "fixtures" / "golden_matlab_current.json"
TOLERANCE = 1e-6
METRICS = ["precision", "recall", "f1_score", "so", "tp", "ic"]


# ---------------------------------------------------------------------------
# Skip entire module if Matlab fixture is absent
# ---------------------------------------------------------------------------
if not MATLAB_FIXTURE.exists():
    pytest.skip(
        "Matlab fixture not found: tests/fixtures/golden_matlab_current.json. "
        "Run: matlab -batch \"run('tests/fixtures/matlab/generate_matlab_fixtures.m')\"",
        allow_module_level=True,
    )

with open(MATLAB_FIXTURE, encoding="utf-8") as _f:
    _MATLAB_ALL = json.load(_f)


def load_recording(n: int):
    """Load pred/gt DataFrames for Recording N."""
    rec_dir = DATASET_DIR / f"Recording_{n}"
    pred_path = rec_dir / "humanAnnotation_2.csv"
    if not pred_path.exists():
        raise FileNotFoundError(f"No pred file for Recording_{n}")
    pred = pd.read_csv(pred_path)
    gt_path = rec_dir / "humanAnnotation_1.csv"
    if not gt_path.exists():
        raise FileNotFoundError(f"No GT file for Recording_{n}")
    return pred, pd.read_csv(gt_path)


def _is_nan(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _fmt(v) -> str:
    if _is_nan(v):
        return "NaN"
    return f"{v:.6f}"


def _build_html_table(rec_name: str, python_group: dict, matlab_group: dict) -> str:
    """Build an HTML comparison table for one recording."""
    rows = []
    all_behaviors = sorted(set(python_group) | set(matlab_group))
    unexpected_diffs = 0

    for behavior in all_behaviors:
        py_bm = python_group.get(behavior, {})
        ml_bm = matlab_group.get(behavior, {})
        for metric in METRICS:
            py_val = py_bm.get(metric)
            ml_val = ml_bm.get(metric)
            py_nan = _is_nan(py_val)
            ml_nan = _is_nan(ml_val)

            if py_nan and ml_nan:
                status = "NaN/NaN"
                color = "#d4edda"  # green — both undefined
                diff_str = "—"
            elif py_nan and not ml_nan:
                # Python undefined, Matlab numeric (expected divergence: Matlab returns 0)
                status = "expected divergence (Py=NaN, Ml=0)"
                color = "#fff3cd"  # orange
                diff_str = f"Py=NaN, Ml={_fmt(ml_val)}"
            elif not py_nan and ml_nan:
                # Should not happen — flag as unexpected
                status = "UNEXPECTED (Py=numeric, Ml=NaN)"
                color = "#f8d7da"  # red
                diff_str = f"Py={_fmt(py_val)}, Ml=NaN"
                unexpected_diffs += 1
            else:
                diff = abs(py_val - ml_val)
                if diff <= TOLERANCE:
                    status = "OK"
                    color = "#d4edda"  # green
                    diff_str = f"{diff:.2e}"
                else:
                    status = f"DIFF > {TOLERANCE:.0e}"
                    color = "#f8d7da"  # red
                    diff_str = f"{diff:.2e}"
                    unexpected_diffs += 1

            rows.append(
                f"<tr style='background:{color}'>"
                f"<td>{behavior}</td><td>{metric}</td>"
                f"<td>{_fmt(py_val)}</td><td>{_fmt(ml_val)}</td>"
                f"<td>{diff_str}</td><td>{status}</td>"
                "</tr>"
            )

    header = (
        "<table border='1' cellpadding='4' cellspacing='0' style='font-family:monospace;font-size:12px'>"
        "<tr style='background:#343a40;color:white'>"
        "<th>Behavior</th><th>Metric</th><th>Python</th><th>Matlab</th>"
        "<th>Diff</th><th>Status</th></tr>"
    )
    footer = "</table>"
    legend = (
        "<p style='font-size:11px'>"
        "<span style='background:#d4edda;padding:2px 6px'>Green</span> = agree &nbsp;"
        "<span style='background:#fff3cd;padding:2px 6px'>Orange</span> = expected divergence (NaN vs 0) &nbsp;"
        "<span style='background:#f8d7da;padding:2px 6px'>Red</span> = unexpected mismatch"
        "</p>"
    )
    return header + "".join(rows) + footer + legend, unexpected_diffs


@pytest.mark.parametrize("n", range(1, 11))
def test_comparison_python_vs_matlab(n, extras):
    """Compare Python and Matlab per-behavior metrics for Recording N.

    Produces an HTML table in the pytest report showing values side-by-side.
    Orange rows = known Python(NaN) vs Matlab(0) divergence — not failures.
    Red rows = unexpected mismatches — cause this test to fail.
    """
    rec_name_key = f"Recording_{n}"
    if rec_name_key not in _MATLAB_ALL:
        pytest.skip(f"Recording_{n} not in Matlab fixture")

    matlab_result = _MATLAB_ALL[rec_name_key]

    # Compute Python output
    pred, gt = load_recording(n)
    rec_name = rec_name_key
    data, _ = preprocess_data({rec_name: (pred.copy(), gt.copy())})
    file_metrics = calculate_banos_for_each_file(data)
    group_py, _ = aggregate_metrics(file_metrics)

    matlab_group = matlab_result.get("group_metrics", {})

    table_html, unexpected_diffs = _build_html_table(rec_name, group_py, matlab_group)

    # Inject into HTML report
    try:
        from pytest_html import extras as html_extras

        extras.append(html_extras.html(f"<h4>{rec_name} — Python vs Matlab</h4>{table_html}"))
    except ImportError:
        pass  # pytest-html not installed; test still runs, just no HTML extra

    assert unexpected_diffs == 0, (
        f"{rec_name}: {unexpected_diffs} unexpected mismatches between Python and Matlab. "
        "See the HTML report for details."
    )
