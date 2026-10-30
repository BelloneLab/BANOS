# tests/test_compare_fixtures.py
"""Tests of the fixture comparison script, tests/fixtures/compare_fixtures.py.

WHY these tests matter
----------------------
The script tags every golden value that changed between two versions and
explains each tag; its HTML output, reports/fixture_comparison.html, is
committed. No other test reads them, so swapped tags, a fixture edited without
regenerating the report, or a report edited by hand would go unnoticed.

The report is not in the sdist (reports/ is left out), so the report test is
skipped there.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "tests" / "fixtures" / "compare_fixtures.py"
REPORT = ROOT / "reports" / "fixture_comparison.html"

# The IC values that differ between golden_python_v020.json and
# golden_python_v110.json: the overall IC and the IC of these behaviors, per
# recording (39 values). With the two F1 values of Recording_8 (mount and
# overall), they are the 41 values changed by v1.1.0.
IC_CHANGED = {
    1: ["overall", "investigation", "mount", "other"],
    2: ["overall", "investigation", "mount", "other"],
    3: ["overall", "investigation", "mount", "other"],
    4: ["overall", "mount", "other"],
    5: ["overall", "investigation", "mount", "other"],
    6: ["overall", "attack", "investigation", "other"],
    7: ["overall", "attack", "investigation", "other"],
    8: ["overall", "investigation", "mount", "other"],
    9: ["overall", "attack", "investigation", "other"],
    10: ["overall", "attack", "investigation", "other"],
}


def _load_script():
    spec = importlib.util.spec_from_file_location("compare_fixtures", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v020_to_v110_finds_the_41_changed_values():
    """Mode 3 (Python v0.2.0 vs v1.1.0) tags exactly the 41 values that v1.1.0 changed.

    Recording_8 mount: F1 NaN -> 0 (NULL->VALUE), IC 1.0 -> NaN (VALUE->NULL);
    Recording_8 overall F1 and the 38 other IC values: CHANGED. The other 259
    values are SAME.
    """
    script = _load_script()
    comparison = next(c for c in script.COMPARISONS if c["id"] == 3)
    rows, counts = script.compare_two(
        script.load_fixture(comparison["a_key"]), script.load_fixture(comparison["b_key"])
    )

    expected = {}
    for n, places in IC_CHANGED.items():
        for place in places:
            label = (
                f"Recording_{n}/overall" if place == "overall" else f"Recording_{n}/group/{place}"
            )
            expected[(label, "ic")] = "CHANGED"
    expected[("Recording_8/group/mount", "ic")] = "VALUE->NULL"
    expected[("Recording_8/group/mount", "f1_score")] = "NULL->VALUE"
    expected[("Recording_8/overall", "f1_score")] = "CHANGED"
    assert len(expected) == 41

    changed = {(row["label"], row["metric"]): row["tag"] for row in rows if row["tag"] != "SAME"}
    assert changed == expected
    assert counts == {"SAME": 259, "VALUE->NULL": 1, "NULL->VALUE": 1, "CHANGED": 39}


def test_committed_report_is_the_script_output(tmp_path):
    """reports/fixture_comparison.html equals what the script writes now.

    The script's output depends only on the fixture files (recordings, behaviors
    and metrics in a fixed order, no date or path), so it can be compared as is;
    line endings are normalized by reading both files as text.
    """
    if not REPORT.exists():
        pytest.skip("reports/fixture_comparison.html is not shipped in the sdist")
    out = tmp_path / "fixture_comparison.html"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--html", str(out)], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr
    assert out.read_text(encoding="utf-8") == REPORT.read_text(encoding="utf-8"), (
        "reports/fixture_comparison.html is out of date: "
        "run python tests/fixtures/compare_fixtures.py --html"
    )
