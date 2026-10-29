"""BANOS fixture comparison tool -- 2-way comparisons across versions and languages.

Fixture files:
  golden_python_v015.json  v0.1.5 original Python (archive): 0 for absent behaviors and
                           for undefined metrics, IC misses the last frame pair
  golden_python_v020.json  v0.2.0 Python (archive): 1.0 for correct absence, 0.0 for
                           false detection, NaN for undefined metrics, IC fixed
  golden_matlab_v020.json  v0.2.0 Matlab (archive, same semantics as Python v0.2.0)
  golden_python_v110.json  v1.1.0 Python (current): detection F1 0 when no real bout is
                           matched, IC averaged over the found real bouts only

Three comparisons available via --mode:
  1  Python v0.2.0 vs Matlab v0.2.0 -- shows Python/Matlab parity
  2  Python v0.1.5 vs v0.2.0       -- shows the changes of v0.2.0
  3  Python v0.2.0 vs v1.1.0       -- shows the changes of v1.1.0

The Recording_N entries are compared, overall and per behavior. The
"all_recordings" entry of the v1.1.0 files has no counterpart in older files
and is not compared.

Each pair of values (first file, second file) is tagged:
  SAME         equal within 1e-10, or NaN (JSON null) in both
  VALUE->NULL  a number in the first file, NaN in the second
  NULL->VALUE  NaN in the first file, a number in the second
  CHANGED      two different numbers
The legend of each comparison says what each tag means there.

Usage:
    python tests/fixtures/compare_fixtures.py              # all modes, text only
    python tests/fixtures/compare_fixtures.py --html       # all modes + HTML report
    python tests/fixtures/compare_fixtures.py --mode 1     # single mode
    python tests/fixtures/compare_fixtures.py --mode 2 --html reports/parity.html
"""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
FIXTURES = PROJECT_ROOT / "tests" / "fixtures"

FILES = {
    "python_v015": FIXTURES / "golden_python_v015.json",
    "python_v020": FIXTURES / "golden_python_v020.json",
    "matlab_v020": FIXTURES / "golden_matlab_v020.json",
    "python_v110": FIXTURES / "golden_python_v110.json",
}

TAGS = ["SAME", "VALUE->NULL", "NULL->VALUE", "CHANGED"]

# For each comparison, "meanings" maps each tag other than SAME to
# (what it means in that comparison, whether such a change is expected).
COMPARISONS = [
    {
        "id": 1,
        "title": "Python v0.2.0 vs Matlab v0.2.0",
        "subtitle": "Shows Python/Matlab parity -- should be SAME",
        "a_key": "python_v020",
        "b_key": "matlab_v020",
        "a_label": "Python v0.2.0",
        "b_label": "Matlab v0.2.0",
        "meanings": {
            "VALUE->NULL": ("Unexpected divergence (should not occur in v0.2.0)", False),
            "NULL->VALUE": ("Unexpected divergence (should not occur in v0.2.0)", False),
            "CHANGED": ("Unexpected numeric mismatch", False),
        },
    },
    {
        "id": 2,
        "title": "Python v0.1.5 vs Python v0.2.0",
        "subtitle": (
            "Shows the changes of v0.2.0: undefined metrics NaN instead of 0, "
            "correct absence 1.0 instead of 0, IC fixes"
        ),
        "a_key": "python_v015",
        "b_key": "python_v020",
        "a_label": "Python v0.1.5",
        "b_label": "Python v0.2.0",
        "meanings": {
            "VALUE->NULL": (
                "v0.1.5=0 -> v0.2.0=NaN: a metric with a zero denominator (precision "
                "when nothing is predicted; F1, SO and TP when no bout is matched) is "
                "NaN instead of 0 and leaves the means",
                True,
            ),
            "NULL->VALUE": ("Unexpected (v0.1.5 never gives NaN)", False),
            "CHANGED": (
                "correct absence (no real bout, nothing predicted) scores 1.0 instead "
                "of 0 on all six metrics; IC counts the last frame pair of each bout "
                "and leaves one-frame real bouts out instead of scoring them 0; the "
                "overall means of the recordings move with these changes and with the "
                "cells that became NaN",
                True,
            ),
        },
    },
    {
        "id": 3,
        "title": "Python v0.2.0 vs Python v1.1.0",
        "subtitle": (
            "Shows the changes of v1.1.0: detection F1 0 instead of NaN when no real "
            "bout is matched, IC averaged over the found real bouts only"
        ),
        "a_key": "python_v020",
        "b_key": "python_v110",
        "a_label": "Python v0.2.0",
        "b_label": "Python v1.1.0",
        "meanings": {
            "VALUE->NULL": (
                "v0.2.0=1.0 -> v1.1.0=NaN: IC is NaN, not 1.0, when no real bout is found",
                True,
            ),
            "NULL->VALUE": (
                "v0.2.0=NaN -> v1.1.0=0: detection F1 is 0, not NaN, when a behavior has "
                "real bouts and none is matched",
                True,
            ),
            "CHANGED": (
                "IC averages over the real bouts that contain a predicted frame (a missed "
                "bout no longer scores 1.0); the overall means of the recordings move with "
                "these IC changes and with the F1 change",
                True,
            ),
        },
    },
]

DEFAULT_HTML = PROJECT_ROOT / "reports" / "fixture_comparison.html"
TOLERANCE = 1e-10
METRICS = ["precision", "recall", "f1_score", "so", "tp", "ic"]

GREEN = "#d4edda"  # SAME
YELLOW = "#fff3cd"  # expected change between a number and NaN
ORANGE = "#fce8d5"  # expected change between two numbers
RED = "#f8d7da"  # unexpected change


def _is_nan(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _fmt(v) -> str:
    if _is_nan(v):
        return "NaN"
    return f"{v:.6f}"


def _close(a, b) -> bool:
    if _is_nan(a) and _is_nan(b):
        return True
    if _is_nan(a) or _is_nan(b):
        return False
    return abs(a - b) < TOLERANCE


def _classify(a_val, b_val) -> str:
    """Classify a pair of values (a=baseline, b=current/target)."""
    if _close(a_val, b_val):
        return "SAME"
    if not _is_nan(a_val) and _is_nan(b_val):
        return "VALUE->NULL"  # baseline numeric, target NaN
    if _is_nan(a_val) and not _is_nan(b_val):
        return "NULL->VALUE"  # baseline NaN, target numeric
    return "CHANGED"


def _recordings(a_data: dict, b_data: dict) -> list[str]:
    """Recording_N keys of both fixtures, in numeric order."""
    names = {key for key in (*a_data, *b_data) if key.startswith("Recording_")}
    return sorted(names, key=lambda x: int(x.split("_")[1]))


def compare_two(a_data: dict, b_data: dict) -> tuple[list[dict], dict]:
    """Compare two fixture dicts. Returns (rows, counts)."""
    counts: dict[str, int] = dict.fromkeys(TAGS, 0)
    rows: list[dict] = []

    for rec in _recordings(a_data, b_data):
        a_rec = a_data.get(rec, {})
        b_rec = b_data.get(rec, {})

        # overall_metrics
        for metric in METRICS:
            a_val = a_rec.get("overall_metrics", {}).get(metric)
            b_val = b_rec.get("overall_metrics", {}).get(metric)
            tag = _classify(a_val, b_val)
            counts[tag] += 1
            rows.append(
                {"label": f"{rec}/overall", "metric": metric, "a": a_val, "b": b_val, "tag": tag}
            )

        # group_metrics
        a_group = a_rec.get("group_metrics", {})
        b_group = b_rec.get("group_metrics", {})
        for beh in sorted(set(a_group) | set(b_group)):
            for metric in METRICS:
                a_val = a_group.get(beh, {}).get(metric)
                b_val = b_group.get(beh, {}).get(metric)
                tag = _classify(a_val, b_val)
                counts[tag] += 1
                rows.append(
                    {
                        "label": f"{rec}/group/{beh}",
                        "metric": metric,
                        "a": a_val,
                        "b": b_val,
                        "tag": tag,
                    }
                )

    return rows, counts


def _meaning(comp: dict, tag: str) -> str:
    if tag == "SAME":
        return "match"
    return comp["meanings"][tag][0]


def print_comparison(comp: dict, rows: list[dict], counts: dict) -> None:
    print(f"\n{'=' * 70}")
    print(f"Mode {comp['id']}: {comp['title']}")
    print(f"  {comp['subtitle']}")
    print(f"{'=' * 70}")
    for row in rows:
        if row["tag"] == "SAME":
            continue
        print(
            f"  [{row['tag']:14s}] {row['label']}/{row['metric']}: "
            f"{comp['a_label']}={_fmt(row['a'])}  {comp['b_label']}={_fmt(row['b'])}"
        )
    total = sum(counts.values())
    print(f"\nSUMMARY ({total} comparisons)")
    for tag in TAGS:
        print(f"  {tag:13s}: {counts[tag]}  ({_meaning(comp, tag)})")


def _row_color(tag: str, comp: dict) -> str:
    if tag == "SAME":
        return GREEN
    _, expected = comp["meanings"][tag]
    if not expected:
        return RED
    return ORANGE if tag == "CHANGED" else YELLOW


def _build_html_section(comp: dict, rows: list[dict], counts: dict) -> str:
    total = sum(counts.values())
    rows_html = []
    for row in rows:
        color = _row_color(row["tag"], comp)
        rows_html.append(
            f"<tr style='background:{color}'>"
            f"<td>{row['label']}</td>"
            f"<td>{row['metric']}</td>"
            f"<td>{_fmt(row['a'])}</td>"
            f"<td>{_fmt(row['b'])}</td>"
            f"<td>{html.escape(row['tag'])}</td>"
            "</tr>"
        )

    table = (
        "<table border='1' cellpadding='4' cellspacing='0' "
        "style='font-family:monospace;font-size:12px;border-collapse:collapse;width:100%'>"
        f"<tr style='background:#343a40;color:white'>"
        f"<th>Location</th><th>Metric</th>"
        f"<th>{comp['a_label']}</th><th>{comp['b_label']}</th><th>Status</th></tr>"
        + "".join(rows_html)
        + "</table>"
    )

    legend_items = [
        f"<span style='background:{_row_color(tag, comp)};padding:2px 8px'>"
        f"{html.escape(tag)}</span> = {html.escape(_meaning(comp, tag))}"
        for tag in TAGS
    ]
    legend = "<p style='font-size:12px'>" + " &nbsp; ".join(legend_items) + "</p>"

    summary = " &nbsp;|&nbsp;\n".join(f"{html.escape(tag)}: {counts[tag]}" for tag in TAGS)
    header = f"""
<h2>Mode {comp["id"]}: {comp["title"]}</h2>
<p><i>{html.escape(comp["subtitle"])}</i></p>
<p>Total: {total} &nbsp;|&nbsp;
{summary}</p>
{legend}
"""
    return header + table + "<br><hr>"


def build_html(sections: list[str]) -> str:
    body = "\n".join(sections)
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        "<title>BANOS Fixture Comparison</title>"
        "<style>body{font-family:sans-serif;padding:20px}"
        "table{width:100%}tr:hover{opacity:.85}th,td{text-align:left;padding:4px 8px}"
        "</style></head><body>"
        "<h1>BANOS Fixture Comparison</h1>" + body + "</body></html>\n"
    )


def load_fixture(key: str) -> dict | None:
    path = FILES[key]
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare BANOS golden fixtures (3 modes).")
    parser.add_argument(
        "--mode",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help=(
            "Which comparison to run (1=Python vs Matlab v0.2.0, 2=v015 vs v020, "
            "3=v020 vs v110). Default: all."
        ),
    )
    parser.add_argument(
        "--html",
        metavar="PATH",
        nargs="?",
        const=str(DEFAULT_HTML),
        help=f"Write HTML report (default: {DEFAULT_HTML})",
    )
    args = parser.parse_args()

    mode_ids = [args.mode] if args.mode else [1, 2, 3]
    selected = [c for c in COMPARISONS if c["id"] in mode_ids]

    html_sections: list[str] = []

    for comp in selected:
        a_data = load_fixture(comp["a_key"])
        b_data = load_fixture(comp["b_key"])

        if a_data is None:
            print(f"SKIP mode {comp['id']}: {FILES[comp['a_key']].name} not found")
            continue
        if b_data is None:
            print(f"SKIP mode {comp['id']}: {FILES[comp['b_key']].name} not found")
            continue

        rows, counts = compare_two(a_data, b_data)
        print_comparison(comp, rows, counts)

        if args.html:
            html_sections.append(_build_html_section(comp, rows, counts))

    if args.html and html_sections:
        out = Path(args.html)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_html(html_sections), encoding="utf-8")
        print(f"\nHTML report written to: {out}")


if __name__ == "__main__":
    main()
