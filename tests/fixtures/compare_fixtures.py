"""BANOS fixture comparison tool -- 2-way comparison across versions and languages.

Fixture files:
  golden_python_v015.json  v0.1.5 original Python (0 for absent behaviors, IC bug)
  golden_python_v020.json  v0.2.0 Python (score-1-for-correct-absence + IC bug fixed)
  golden_matlab_v020.json  v0.2.0 Matlab (same semantics as Python v0.2.0)

Two comparisons available via --mode:
  1  Python v0.2.0 vs Matlab v0.2.0 -- shows Python/Matlab parity
  2  Python v0.1.5 vs v0.2.0       -- shows ALL changes (absent-behavior fix + IC bug fix)

Usage:
    python tests/fixtures/compare_fixtures.py              # both modes, text only
    python tests/fixtures/compare_fixtures.py --html       # both modes + HTML report
    python tests/fixtures/compare_fixtures.py --mode 1     # single mode
    python tests/fixtures/compare_fixtures.py --mode 2 --html reports/parity.html
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
FIXTURES = PROJECT_ROOT / "tests" / "fixtures"

FILES = {
    "python_v015": FIXTURES / "golden_python_v015.json",
    "python_v020": FIXTURES / "golden_python_v020.json",
    "matlab_v020": FIXTURES / "golden_matlab_v020.json",
}

COMPARISONS = [
    {
        "id": 1,
        "title": "Python v0.2.0 vs Matlab v0.2.0",
        "subtitle": "Shows Python/Matlab parity -- should be SAME",
        "a_key": "python_v020",
        "b_key": "matlab_v020",
        "a_label": "Python v0.2.0",
        "b_label": "Matlab v0.2.0",
        "null_to_val_meaning": "Unexpected divergence (should not occur in v0.2.0)",
        "changed_meaning": "Unexpected numeric mismatch",
    },
    {
        "id": 2,
        "title": "Python v0.1.5 vs Python v0.2.0",
        "subtitle": "Shows ALL changes: absent-behavior fix (0→1 correct absence) + IC bug fix",
        "a_key": "python_v015",
        "b_key": "python_v020",
        "a_label": "Python v0.1.5",
        "b_label": "Python v0.2.0",
        "null_to_val_meaning": "v0.1.5=0 → v0.2.0=1.0 (correct absence now scores 1)",
        "changed_meaning": "IC bug fix",
    },
]

DEFAULT_HTML = PROJECT_ROOT / "reports" / "fixture_comparison.html"
TOLERANCE = 1e-10
METRICS = ["precision", "recall", "f1_score", "so", "tp", "ic"]


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
        return "NULL->VALUE"  # baseline numeric, target NaN
    if _is_nan(a_val) and not _is_nan(b_val):
        return "VALUE->NULL"  # baseline NaN, target numeric
    return "CHANGED"


def compare_two(a_data: dict, b_data: dict) -> tuple[list[dict], dict]:
    """Compare two fixture dicts. Returns (rows, counts)."""
    counts: dict[str, int] = {"SAME": 0, "NULL->VALUE": 0, "VALUE->NULL": 0, "CHANGED": 0}
    rows: list[dict] = []

    recs = sorted(set(a_data) | set(b_data), key=lambda x: int(x.split("_")[1]))
    for rec in recs:
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
    print(f"  SAME         : {counts['SAME']}")
    print(f"  NULL->VALUE  : {counts['NULL->VALUE']}  ({comp['null_to_val_meaning']})")
    print(f"  VALUE->NULL  : {counts['VALUE->NULL']}  (baseline=NaN, target=numeric)")
    print(f"  CHANGED      : {counts['CHANGED']}  ({comp['changed_meaning']})")


def _row_color(tag: str, comp_id: int) -> str:
    base = {
        "SAME": "#d4edda",
        "VALUE->NULL": "#f8d7da",
    }
    if tag in base:
        return base[tag]
    # Color meaning differs by mode
    if comp_id == 1:
        # Python vs Matlab: NULL->VALUE is unexpected divergence (red), CHANGED is bad (red)
        return {"NULL->VALUE": "#f8d7da", "CHANGED": "#f8d7da"}.get(tag, "white")
    # Mode 2: NULL->VALUE = absent-behavior fix (yellow), CHANGED = IC bug fix (orange)
    return {"NULL->VALUE": "#fff3cd", "CHANGED": "#fce8d5"}.get(tag, "white")


def _build_html_section(comp: dict, rows: list[dict], counts: dict) -> str:
    total = sum(counts.values())
    rows_html = []
    for row in rows:
        color = _row_color(row["tag"], comp["id"])
        rows_html.append(
            f"<tr style='background:{color}'>"
            f"<td>{row['label']}</td>"
            f"<td>{row['metric']}</td>"
            f"<td>{_fmt(row['a'])}</td>"
            f"<td>{_fmt(row['b'])}</td>"
            f"<td>{row['tag']}</td>"
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
        ("<span style='background:#d4edda;padding:2px 8px'>SAME</span>", "match"),
        (
            "<span style='background:#fff3cd;padding:2px 8px'>NULL-&gt;VALUE</span>",
            comp["null_to_val_meaning"],
        ),
        ("<span style='background:#fce8d5;padding:2px 8px'>CHANGED</span>", comp["changed_meaning"])
        if comp["id"] == 2
        else (
            "<span style='background:#f8d7da;padding:2px 8px'>CHANGED</span>",
            comp["changed_meaning"],
        ),
        ("<span style='background:#f8d7da;padding:2px 8px'>VALUE-&gt;NULL</span>", "unexpected"),
    ]
    legend = (
        "<p style='font-size:12px'>"
        + " &nbsp; ".join(f"{s} = {m}" for s, m in legend_items)
        + "</p>"
    )

    header = f"""
<h2>Mode {comp["id"]}: {comp["title"]}</h2>
<p><i>{comp["subtitle"]}</i></p>
<p>Total: {total} &nbsp;|&nbsp;
SAME: {counts["SAME"]} &nbsp;|&nbsp;
NULL-&gt;VALUE: {counts["NULL->VALUE"]} &nbsp;|&nbsp;
CHANGED: {counts["CHANGED"]} &nbsp;|&nbsp;
VALUE-&gt;NULL: {counts["VALUE->NULL"]}</p>
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
        "<h1>BANOS Fixture Comparison</h1>" + body + "</body></html>"
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
        choices=[1, 2],
        default=None,
        help="Which comparison to run (1=Python vs Matlab, 2=v015 vs v020). Default: all.",
    )
    parser.add_argument(
        "--html",
        metavar="PATH",
        nargs="?",
        const=str(DEFAULT_HTML),
        help=f"Write HTML report (default: {DEFAULT_HTML})",
    )
    args = parser.parse_args()

    mode_ids = [args.mode] if args.mode else [1, 2]
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
