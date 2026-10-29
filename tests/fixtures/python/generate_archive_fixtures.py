"""Record of how the frozen v0.1.5 fixture, golden_python_v015.json, was made.

The fixture holds the output of the original BANOS 0.1.5 code on the 10
bundled recordings, each scored alone with that code's preprocess_data,
calculate_banos_for_each_file and aggregate_metrics. It is an archive, kept
for comparison with later versions (see tests/fixtures/compare_fixtures.py),
and is not regenerated: the code it records no longer changes.

It was written by this script, which imported the 0.1.5 module from a copy at
archive/python/BANOS/BANOS.py. That folder is not part of this repository, so
the import below only works where the BANOS 0.1.5 package from PyPI (module
BANOS.BANOS) is installed. Run that way from the project root, the script
writes the committed file again, unchanged:
    uv run --isolated --no-project --with "BANOS==0.1.5" python tests/fixtures/python/generate_archive_fixtures.py
"""

import json
import math
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Import the 0.1.5 module (archive copy if present, else the installed
# BANOS 0.1.5 package) — NOT the banos package of this repository
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "archive" / "python"))
from BANOS.BANOS import (  # noqa: E402
    aggregate_metrics,
    calculate_banos_for_each_file,
    preprocess_data,
)

DATASET_DIR = PROJECT_ROOT / "data" / "dataset_human_vs_human"
OUT_FILE = PROJECT_ROOT / "tests" / "fixtures" / "golden_python_v015.json"


def load_recording(n):
    rec_dir = DATASET_DIR / f"Recording_{n}"
    pred_path = rec_dir / "humanAnnotation_2.csv"

    import pandas as pd  # import here so archive path injection is in effect

    if not pred_path.exists():
        raise FileNotFoundError(f"No pred file found for Recording_{n}")
    pred = pd.read_csv(pred_path)
    gt_path = rec_dir / "humanAnnotation_1.csv"
    if not gt_path.exists():
        raise FileNotFoundError(f"No GT found for Recording_{n}")
    return pred, pd.read_csv(gt_path)


def make_json_serializable(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    return obj


if __name__ == "__main__":
    results = {}
    for n in range(1, 11):
        pred, gt = load_recording(n)
        data, _ = preprocess_data({f"Recording_{n}": (pred.copy(), gt.copy())})
        file_metrics = calculate_banos_for_each_file(data)
        group_m, overall_m = aggregate_metrics(file_metrics)
        results[f"Recording_{n}"] = {
            "file_metrics": make_json_serializable(file_metrics),
            "group_metrics": make_json_serializable(group_m),
            "overall_metrics": make_json_serializable(overall_m),
        }
        print(f"Recording_{n}: {overall_m}")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
        f.write("\n")

    print(f"\nSaved archive fixtures to {OUT_FILE}")
    print(f"Total recordings: {len(results)}")
