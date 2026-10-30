<div align="center">

<p align="center">
<img src="https://raw.githubusercontent.com/BelloneLab/BANOS/main/assets/Logo_BANOS.png" width="20%">
</p>

# Behavior Annotation Score (BANOS)

[![PyPI](https://img.shields.io/pypi/v/banos)](https://pypi.org/project/banos/)
[![PyPI Downloads](https://static.pepy.tech/badge/banos)](https://pepy.tech/project/banos)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/BelloneLab/BANOS/blob/main/LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/BelloneLab/BANOS/actions/workflows/ci.yml/badge.svg)](https://github.com/BelloneLab/BANOS/actions/workflows/ci.yml)
[![MATLAB File Exchange](https://www.mathworks.com/matlabcentral/images/matlab-file-exchange.svg)](https://www.mathworks.com/matlabcentral/fileexchange/157916-banos)

</div>

## What is BANOS?

BANOS is a set of metrics for evaluating algorithmic behavior annotations against a
ground truth (typically human annotations). It is designed for ethology and computer
vision workflows where researchers annotate behaviors in video data.

Traditional frame-based metrics (precision/recall/F1) capture detection accuracy but miss important
temporal qualities: does the predicted segment overlap well with the ground-truth
bout? Does the prediction start and end at the right time? Is the prediction
internally consistent, or does it flicker on and off inside the bout?

BANOS addresses these questions with four complementary metrics, computed for each behavior.

## The 4 BANOS Metrics

<p align="center">
    <img src="https://raw.githubusercontent.com/BelloneLab/BANOS/main/assets/Schema_BANOS.png" width="364" height="224">
</p>

Annotations are binary: one column per behavior, one row per frame, 1 when the behavior is
present. A **bout** is a run of consecutive frames with value 1. Real bouts come from the
ground truth, predicted bouts from the annotation being evaluated. A predicted bout
**overlaps** a real bout when they share at least one frame.

1. **Detection Accuracy (DA)** — precision, recall and F1 over bouts. Predicted bouts are
   taken in time order, and each is matched to the first real bout it overlaps that is not
   matched yet (greedy matching). TP is the number of matched pairs, FP the number of
   predicted bouts left unmatched, FN the number of real bouts left unmatched (TP here is
   a count, not the Temporal Precision metric).
   Precision = TP / (TP + FP), recall = TP / (TP + FN),
   F1 = 2 · precision · recall / (precision + recall). F1 is 0 when no bout is matched
   (TP = 0) but some bouts were predicted or missed (FP + FN > 0).

2. **Segment Overlap (SO)** — the temporal intersection over union (shared frames / frames
   in the union) of every overlapping (predicted, real) bout pair, averaged over all such
   pairs.

3. **Temporal Precision (TP)** — `1 / (1 + |start difference| + |end difference|)`, in
   frames, for every overlapping (predicted, real) bout pair, averaged over all such pairs.
   It falls quickly: a bout predicted 2 frames late at both ends scores 1 / 5 = 0.2.

4. **Intra-bout Continuity (IC)** — label stability inside the real bouts that are found,
   that is, with at least one predicted frame inside. For each found real bout longer than
   one frame: `1 - switches / (bout length - 1)`, where the bout length is in frames and
   the switches are the changes of the predicted value between consecutive frames of the
   bout (a bout has bout length - 1 such frame pairs). IC is the mean over these bouts.
   One-frame real bouts have no frame pair and are left out.

SO and TP average over pairs, not over real bouts: a real bout overlapped by two predicted
bouts gives two terms, and a predicted bout that overlaps two real bouts gives one term with
each. A real bout with no predicted frame inside it (a missed bout) gives no SO, TP or IC
term by default (see the `missed_bouts` option below).

**Undefined values.** For a behavior with real bouts in a recording (or, with
`aggregation="pooled"`, in at least one recording), recall and F1 are always defined, and
a metric is NaN when it is undefined:

- precision, when nothing is predicted (TP + FP = 0);
- SO and TP, when no predicted bout overlaps a real bout;
- IC, when no real bout longer than one frame is found.

With `missed_bouts="zero"`, each missed bout adds a term equal to 0: SO and TP are then
always defined, and IC is NaN only when no real bout is longer than one frame. Per
recording, a behavior without real bouts follows the absent-behavior rule (see
`aggregation` below). Pooled, a behavior with no real bout in any recording has an
undefined recall, SO, TP and IC, and an undefined precision and F1 too when nothing is
predicted either (TP = FP = FN = 0).

NaN values are left out of every mean, over recordings or behaviors: a NaN never counts as
0 or 1, and a mean with no defined value is NaN.

**Matching.** `matching="optimal"` replaces greedy matching with the Hungarian algorithm
(`scipy.optimize.linear_sum_assignment`), which finds the largest possible number of
matched pairs. On bouts read from 0/1 columns, as in `banos.score()` and the pipeline
functions, greedy matching already finds that number, so both options give the same counts
and the same metrics. They can differ only when `banos.core.calculate_tp_fp_fn` is given
bouts directly and the bouts of one side overlap one another or are not in time order;
`banos.score()` always passes disjoint bouts in time order, so it is unaffected.

## Installation

```bash
pip install banos
```

Requires Python 3.11+. Dependencies: `numpy` (>= 1.24), `pandas` (>= 2.0) and
`scipy` (>= 1.10).

Two optional extras install what the tutorial notebooks need (the notebooks are in the
[GitHub repository](https://github.com/BelloneLab/BANOS/tree/main/demo), not in the
package):

- `pip install "banos[notebook]"`: jupyter, nbformat, matplotlib and seaborn, for
  `demo/tutorial_python.ipynb`;
- `pip install "banos[calms21]"`: tensorflow, scikit-learn and tqdm, for
  `demo/tutorial_calms21_task1.ipynb` (together with the `notebook` extra).

## Quick Start

```python
import banos
import pandas as pd

# One recording: one row per frame, one 0/1 column per behavior
pred = pd.read_csv("machine_annotations.csv")
gt   = pd.read_csv("human_annotations.csv")

metrics = banos.score(pred, gt)
# {'attack': {'precision': ..., 'recall': ..., 'f1_score': ..., 'so': ..., 'tp': ..., 'ic': ...}, ...}

# Several recordings: a dict of (prediction, ground truth) pairs
group_metrics, overall_metrics = banos.score({
    "recording_1": (pred_1, gt_1),
    "recording_2": (pred_2, gt_2),
})
```

**Input.** For each recording, the prediction and the ground truth are DataFrames with the
same number of rows (frames). Rows are read by position: the index is ignored. Columns are
matched by name and hold 0 and 1 (integers, floats or booleans). NaN values are replaced by
0, and columns that cannot be scored are dropped, each with a warning (see Errors and
warnings below).

**Returns.** `banos.score()` returns, with either aggregation:

- for one recording (a DataFrame pair): `{behavior: {metric: value}}`, with the metrics
  `precision`, `recall`, `f1_score` (DA), `so`, `tp` and `ic`;
- for several recordings (a dict): a tuple `(group_metrics, overall_metrics)`, where
  `group_metrics` is `{behavior: {metric: value}}` over all recordings and
  `overall_metrics` is `{metric: value}`.

## Options

`banos.score(data, gt=None, *, matching="greedy", missed_bouts="exclude", aggregation="per_file")`

### Combining recordings: `aggregation`

**`aggregation="per_file"` (default).** Each recording is scored on its own, then the
values are averaged: `group_metrics` is the mean of each behavior over the recordings,
`overall_metrics` the mean of every (recording, behavior) value, NaN left out. Each
recording weighs the same, whatever its number of bouts.

*Absent-behavior rule:* when the ground truth of a recording has no bout of a behavior,
that behavior scores 1.0 on all six metrics if nothing is predicted (correct absence), and
0.0 on all six if at least one bout is predicted (false detection).

The per-file mean therefore mixes detection quality with the share of recordings without
the behavior. A model that predicts nothing scores 1.0 on every recording without the
behavior and F1 = 0 on the others: on the bundled data, its per-file F1 is 0.5 for attack
(absent from 5 of the 10 recordings) and 0.4 for mount (absent from 4), while it finds no
bout at all.

Use it to know how good the annotation of each recording is: look at the value of each
recording (`calculate_banos_for_each_file`, see Lower-level API) and at their mean, with
the share of recordings without each behavior in mind.

**`aggregation="pooled"`.** Each behavior is scored once over all recordings: TP, FP and
FN are summed over the recordings and give precision, recall and F1, and the SO, TP and IC
terms of all recordings are averaged together. There is no absent-behavior rule: a
recording without the behavior only adds its predicted bouts to FP. A behavior with no
real and no predicted bout in any recording is NaN on all six metrics. `overall_metrics` is
the mean over the behaviors, NaN left out. Every bout weighs the same, and predicting
nothing gives F1 = 0: this is the right choice to compare or rank models and methods on
the same recordings.

```python
import pandas as pd
import banos

gt     = pd.DataFrame({"attack": [0, 1, 1, 1, 0, 0, 1, 1, 1, 0]})  # two real bouts
silent = pd.DataFrame({"attack": [0] * 10})                        # a model that predicts nothing

data = {
    "video_1": (silent, gt),      # both real bouts missed
    "video_2": (silent, silent),  # no attack in this video: correct absence
}

group, overall = banos.score(data)                        # per_file
# group["attack"]: precision 1.0, recall 0.5, f1_score 0.5, so 1.0, tp 1.0, ic 1.0

group, overall = banos.score(data, aggregation="pooled")
# group["attack"]: precision nan, recall 0.0, f1_score 0.0, so nan, tp nan, ic nan
```

Per file, `video_2` scores 1.0 everywhere, while `video_1` has recall and F1 0 and its
precision, SO, TP and IC undefined: every mean but recall and F1 is 1.0. Pooled, the model
has found 0 of the 2 bouts.

### Missed bouts: `missed_bouts`

**`missed_bouts="exclude"` (default).** A real bout with no predicted frame inside it gives
no SO, TP or IC term. SO, TP and IC then describe the quality of the bouts that were found,
and are read together with recall, the share of real bouts found.

**`missed_bouts="zero"`.** Each missed real bout adds a term equal to 0 to SO, to TP and,
if it is longer than one frame, to IC, so these metrics also drop when bouts are missed.

Precision, recall, F1 and the absent-behavior rule do not depend on this option.

```python
gt   = pd.DataFrame({"attack": [0, 1, 1, 1, 0, 0, 1, 1, 1, 0]})  # two real bouts
pred = pd.DataFrame({"attack": [0, 1, 1, 1, 0, 0, 0, 0, 0, 0]})  # finds the first only

banos.score(pred, gt)["attack"]
# precision 1.0, recall 0.5, f1_score 0.667, so 1.0, tp 1.0, ic 1.0

banos.score(pred, gt, missed_bouts="zero")["attack"]
# precision 1.0, recall 0.5, f1_score 0.667, so 0.5, tp 0.5, ic 0.5
```

The two options combine: `banos.score(data, missed_bouts="zero", aggregation="pooled")`.

### Errors and warnings

`banos.score()` raises `ValueError`:

- for an unknown `matching`, `missed_bouts` or `aggregation` value, before reading the data;
- when `data` is a DataFrame and `gt` is missing;
- when the prediction and the ground truth of a recording have different numbers of
  frames, or a recording has no frame.

It emits a `UserWarning` naming the recording and the column:

- for each column whose NaN values are replaced by 0;
- for each column dropped because it holds values other than 0 and 1 (probabilities, for
  example);
- for each column dropped because it is missing, or was dropped, on the other side.

A single DataFrame pair is named `'single'` in these messages. Valid input gives no
warning. `preprocess_data()` raises and warns in the same way.

## Lower-level API

`banos.score()` chains three functions; each step can be called on its own, for example
to keep the results of each recording.

```python
from banos import (
    preprocess_data,
    calculate_banos_for_each_file, aggregate_metrics,      # per_file
    calculate_components_for_each_file, pool_components,   # pooled
)

data = {
    "recording_1": (pred_1, gt_1),
    "recording_2": (pred_2, gt_2),
}
clean, dropped = preprocess_data(data)  # dropped: the columns removed from each recording

# Per file: the metrics of each recording, then their means
file_metrics = calculate_banos_for_each_file(clean)  # {recording: {behavior: {metric: value}}}
group_metrics, overall_metrics = aggregate_metrics(file_metrics)

# Pooled: the bout counts and terms of each recording, then one score per behavior
file_components = calculate_components_for_each_file(clean)  # {recording: {behavior: components}}
group_metrics, overall_metrics = pool_components(file_components)
```

`calculate_banos_for_each_file` and `calculate_components_for_each_file` take the
`matching` and `missed_bouts` options of `banos.score()`. The components of a behavior in a
recording are what its metrics are computed from:
`{"n_tp": ..., "n_fp": ..., "n_fn": ..., "so_terms": [...], "tp_terms": [...], "ic_terms": [...]}`,
the bout counts and the lists of terms that SO, TP and IC average. For a single recording
that has already been preprocessed, `compute_behavior_metrics(pred, gt)` and
`compute_behavior_components(pred, gt)` return its per-behavior metrics and components.

`banos.core` holds the building blocks: `identify_bouts`, `calculate_tp_fp_fn`,
`calculate_precision_recall_f1`, `calculate_tiou`, `calculate_so` and
`calculate_so_terms`, `calculate_tp_metric` and `calculate_tp_terms`, `calculate_ic` and
`calculate_ic_terms`, `count_switches_within_bout`, and the preprocessing functions
`is_logical_column`, `drop_non_logical_columns`, `match_headers` and `preprocess_data`.
Import the metric functions from `banos.core`.

## MATLAB

A MATLAB implementation is provided in `matlab/BANOS/`. It needs base MATLAB only, no
toolbox. Usage mirrors the Python API.

```matlab
% Add the toolbox to the path for this session
run('matlab/BANOS/setup.m');

% Score a single recording (pred/gt = cell arrays: row 1 = headers, rows 2+ = binary data)
metrics = BANOS_score(pred, gt);

% Score multiple recordings
dataStruct.Recording_1 = {pred1, gt1};
dataStruct.Recording_2 = {pred2, gt2};
[groupMetrics, overallMetrics] = BANOS_score(dataStruct);

% Options as name-value pairs (names and values are case-insensitive)
metrics = BANOS_score(pred, gt, 'missed_bouts', 'zero');
[groupMetrics, overallMetrics] = BANOS_score(dataStruct, 'aggregation', 'pooled');
```

The MATLAB code computes the same metrics with the same options and rules; the parity
tests compare the Python results with golden values written by the MATLAB code, within
1e-6. MATLAB uses greedy matching only (`'matching', 'optimal'` raises an error). A
single recording is named `single_recording` in messages, and errors and warnings carry
identifiers: `BANOS:lengthMismatch`, `BANOS:noFrame`, `BANOS:nanReplaced`,
`BANOS:columnDropped`, `BANOS:unknownOption`, `BANOS:missingOptionValue`,
`BANOS:invalidOption`, `BANOS:optimalNotImplemented`, `BANOS:missingGroundTruth` and
`BANOS:invalidData`. `BANOScalculateBANOSForEachFile` returns the components of each
recording as a second output, and `BANOSpoolComponents` pools them.

See [`demo/tutorial_matlab.m`](https://github.com/BelloneLab/BANOS/blob/main/demo/tutorial_matlab.m)
for a full walkthrough.

Also available on
[MATLAB File Exchange](https://www.mathworks.com/matlabcentral/fileexchange/157916-banos).

## Examples & Tutorials

| Resource | Description |
|----------|-------------|
| [`demo/quickstart.py`](https://github.com/BelloneLab/BANOS/blob/main/demo/quickstart.py) | Minimal Python example — score annotations in two lines |
| [`demo/quickstart.m`](https://github.com/BelloneLab/BANOS/blob/main/demo/quickstart.m) | Minimal MATLAB example |
| [`demo/tutorial_python.ipynb`](https://github.com/BelloneLab/BANOS/blob/main/demo/tutorial_python.ipynb) | Full Python tutorial: classic BANOS usage + frame F1 vs BANOS comparison (`notebook` extra) |
| [`demo/tutorial_matlab.m`](https://github.com/BelloneLab/BANOS/blob/main/demo/tutorial_matlab.m) | Full MATLAB tutorial mirroring the Python notebook |
| [`demo/tutorial_calms21_task1.ipynb`](https://github.com/BelloneLab/BANOS/blob/main/demo/tutorial_calms21_task1.ipynb) | Human vs machine: CalMS21 Task 1 baseline, F1 + BANOS (Python only; `calms21` and `notebook` extras) |

The demos run from a clone of the repository. The quickstarts and the two full tutorials
score the example recordings in `data/dataset_human_vs_human/`; the CalMS21 notebook
downloads its test data on first run.

## Contributing

BANOS is functionally complete by design. We welcome **bug reports** and
**documentation improvements**. See
[CONTRIBUTING.md](https://github.com/BelloneLab/BANOS/blob/main/CONTRIBUTING.md) for
details on how to report issues, submit fixes, and the project's maintenance lifecycle.

To report a security vulnerability, see
[SECURITY.md](https://github.com/BelloneLab/BANOS/blob/main/SECURITY.md) — please do not
use public GitHub Issues for security reports.

## Citation

If you use BANOS, please cite the article:

> Chindemi G, Bellone C, Girard B. *From eye to AI: Studying rodent social behavior in the
> era of machine learning.* Neuroscience & Biobehavioral Reviews 188 (2026) 106766.
> https://doi.org/10.1016/j.neubiorev.2026.106766

The preprint of this article is:

> Chindemi G, Bellone C, Girard B. *From eye to AI: studying rodent social behavior in the
> era of machine Learning.* arXiv:2508.04255 (2025).
> https://doi.org/10.48550/arXiv.2508.04255

```bibtex
@article{chindemi2026eye,
  title   = {From eye to {AI}: Studying rodent social behavior in the era of machine learning},
  author  = {Chindemi, Giuseppe and Bellone, Camilla and Girard, Benoit},
  journal = {Neuroscience \& Biobehavioral Reviews},
  volume  = {188},
  pages   = {106766},
  year    = {2026},
  doi     = {10.1016/j.neubiorev.2026.106766}
}

@article{chindemi2025eye,
  title   = {From eye to {AI}: studying rodent social behavior in the era of machine {L}earning},
  author  = {Chindemi, Giuseppe and Bellone, Camilla and Girard, Benoit},
  journal = {arXiv preprint arXiv:2508.04255},
  year    = {2025},
  doi     = {10.48550/arXiv.2508.04255}
}
```

The same references are in
[CITATION.cff](https://github.com/BelloneLab/BANOS/blob/main/CITATION.cff), which GitHub
offers as "Cite this repository".

## Changelog

See [CHANGELOG.md](https://github.com/BelloneLab/BANOS/blob/main/CHANGELOG.md) for release
history.

## License

MIT — see [LICENSE](https://github.com/BelloneLab/BANOS/blob/main/LICENSE).
