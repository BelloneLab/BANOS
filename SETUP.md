# One-Time Setup Guide

## GitHub Repository Settings

- **Branch protection on `main`**: require PR review + CI passing before merge
- **Actions permissions**: allow all actions (needed for CI and PyPI publish)
- **Secrets**: none required (OIDC replaces API tokens for PyPI)

---

## Local Development Setup

```bash
# Install uv (package manager)
pip install uv

# Install the package in editable mode with dev dependencies
uv sync --extra dev

# Verify everything works
uv run pytest -q
```

### Optional: pre-commit hooks
```bash
uv run pre-commit install
```

---

## Human-vs-Machine Tutorial — CalMS21 Task 1

The `demo/tutorial_calms21_task1.ipynb` notebook requires:

### 1. Model weights (already in repo)

The Conv-1D baseline model (`task1_seed_42_model.h5`, ~940 KB) is committed at
`demo/models/task1_seed_42_model.h5`. No extra download is needed — just clone
the repo.

If you need to **retrain** the model (e.g., for a different seed), follow these steps:

```bash
# Create a conda environment with the required packages
conda create -n mabe_baseline python=3.10 -y
conda activate mabe_baseline
pip install "tensorflow==2.12" "tensorflow-addons==0.20.0" numpy pandas scikit-learn easydict

# Convert CalMS21 Task 1 JSON files to .npy format
# (requires calms21_task1_train.json and calms21_task1_test.json in the data/ folder)
cd calms21_dataset/mab-e-baselines-master

python -c "
import json, numpy as np
for split in ['train', 'test']:
    with open(f'../../calms21_dataset/Dataset_Calms21/task1_classic_classification/calms21_task1_{split}.json') as f:
        data = json.load(f)
    for g in data:
        for s in data[g]:
            data[g][s]['keypoints'] = np.array(data[g][s]['keypoints'])
            data[g][s]['scores'] = np.array(data[g][s]['scores'])
            if 'annotations' in data[g][s]:
                data[g][s]['annotations'] = np.array(data[g][s]['annotations'])
    np.save(f'data/calms21_task1_{split}.npy', data, allow_pickle=True)
    print(f'{split} saved')
"

# Train the model (seed 42, 15 epochs, ~75 min on CPU)
python train_task1.py --seed 42

# Copy the model to the repo
cp results/task1_baseline/task1_seed_42_model.h5 ../../demo/models/
```

### 2. CalMS21 test data (downloaded at runtime)

The test JSON (~600 MB) is **not** included in the repo. The notebook downloads
it automatically on first run from CaltechDATA to `.cache/calms21/` (gitignored).

If the automatic download fails, download manually from:
https://data.caltech.edu/records/s0vdx-0k302

Place the file at: `.cache/calms21/calms21_task1_test.json`

### 3. Optional — publish model to GitHub Releases

If you want the model available for download without cloning the full repo:

```bash
# Install GitHub CLI if not available: https://cli.github.com/
gh release create calms21-assets-v1 demo/models/task1_seed_42_model.h5 \
  --title "CalMS21 Task 1 Baseline Assets" \
  --notes "Pre-trained Conv-1D baseline model (seed 42) for tutorial_calms21_task1.ipynb"
```

Then update `MODEL_URL` in the notebook's setup cell to the release asset URL.
