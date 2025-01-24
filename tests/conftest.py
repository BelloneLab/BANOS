# tests/conftest.py
from pathlib import Path

import pandas as pd
import pytest

DATASET_DIR = Path(__file__).parent.parent / "data" / "dataset_human_vs_human"
N_RECORDINGS = 10


def load_recording(n: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load two human annotation CSVs for recording N."""
    rec_dir = DATASET_DIR / f"Recording_{n}"
    pred_candidates = [
        rec_dir / "humanAnnotation_2.csv",
    ]
    pred = None
    for path in pred_candidates:
        if path.exists():
            pred = pd.read_csv(path)
            break
    if pred is None:
        raise FileNotFoundError(f"No annotation 2 found for Recording_{n}")
    gt_candidates = [
        rec_dir / "humanAnnotation_1.csv",
    ]
    for path in gt_candidates:
        if path.exists():
            gt = pd.read_csv(path)
            return pred, gt
    raise FileNotFoundError(f"No annotation 1 found for Recording_{n}")


@pytest.fixture(scope="session")
def all_recordings() -> dict:
    """Returns dict mapping recording number → (pred_df, gt_df)."""
    return {n: load_recording(n) for n in range(1, N_RECORDINGS + 1)}


@pytest.fixture(scope="session")
def single_recording() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (pred_df, gt_df) for Recording_1."""
    return load_recording(1)
