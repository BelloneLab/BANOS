# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] — 2026-10-30

Two metrics are corrected (detection F1 and IC), two options are added (`missed_bouts` and
`aggregation`), and invalid input now raises an error or a warning. With the default
options and valid input, precision, recall, SO and TP are unchanged.

### Numerical changes
- **Detection F1 is 0, not NaN, when no real bout is matched.** F1 is now 0 when TP = 0
  and FP + FN > 0 (a recording with real bouts and nothing predicted, or only false
  bouts), the value of 2 TP / (2 TP + FP + FN). It stays NaN only when TP = FP = FN = 0;
  every other value is unchanged. Such a recording now stays in the means instead of
  leaving them. Precision and recall are unchanged (NaN on a zero denominator). This
  brings back the 0 of v0.1.5, which v0.2.0 had turned into NaN.
- **IC averages over the found real bouts only.** A real bout with no predicted frame
  inside it holds no switch and scored IC 1.0: missing a bout raised IC, and a model that
  predicted nothing scored IC 1.0. IC is now the mean of `1 - switches / (bout length - 1)`
  over the real bouts with at least one predicted frame, one-frame bouts still left out,
  and NaN when no such bout is found.
- **IC reads the prediction by position.** IC read the prediction by index label, so
  DataFrames indexed other than 0..n-1 (frames numbered from 1, reversed, float or string
  labels, concatenated recordings) got a wrong IC or an exception. Input with the default
  index is unchanged.
- **Golden values.** The fixtures move to `golden_python_v110.json` and
  `golden_matlab_v110.json`; the v0.2.0 files are kept as archives. 41 of the 300
  per-recording values change: 2 F1 values (Recording_8 mount F1 from NaN to 0,
  Recording_8 overall F1 from 0.6062 to 0.4546) and 39 IC values, in every recording
  (Recording_8 mount IC from 1.0 to NaN: both its real bouts are missed). The other 259
  are unchanged. `python tests/fixtures/compare_fixtures.py --mode 3` shows them.
- **Bundled data**, the 10 recordings scored together with the default options
  (`banos.score(data)`, four behaviors), 1.0.0 → 1.1.0: F1 mount 0.8780 → 0.7902, overall
  0.7746 → 0.7553; IC attack 0.9956 → 0.9949, investigation 0.9918 → 0.9875, mount
  0.9969 → 0.9942, other 0.9945 → 0.9927, overall 0.9947 → 0.9923. Precision, recall, SO
  and TP are unchanged.
- **A model that predicts nothing**, on the same data, per file: F1 attack 1.0 → 0.5,
  mount 1.0 → 0.4, investigation and other NaN → 0, overall 1.0 → 0.225; IC investigation
  and other 1.0 → NaN. The 0.5 and 0.4 that remain are the share of recordings without
  the behavior (absent-behavior rule, unchanged). Pooled, its F1 is 0 for every behavior.
- The MATLAB code gives the same numbers (parity tests within 1e-6).

### Added
- `missed_bouts` option of `banos.score()`: `"exclude"` (default) leaves a missed real
  bout out of SO, TP and IC; `"zero"` adds a term equal to 0 to SO, to TP and, for a bout
  longer than one frame, to IC. Precision, recall and F1 do not depend on it.
- `aggregation` option of `banos.score()`: `"per_file"` (default) scores each recording,
  then averages; `"pooled"` sums the TP, FP and FN counts of all recordings and averages
  all their SO, TP and IC terms, for each behavior, without the absent-behavior rule, and
  `overall_metrics` is the mean over the behaviors. The result has the same form in both.
- Functions `calculate_so_terms`, `calculate_tp_terms` and `calculate_ic_terms`
  (`banos.core`), `compute_behavior_components`, `calculate_components_for_each_file` and
  `pool_components` (`banos`). `calculate_so`, `calculate_tp_metric`, `calculate_ic`,
  `compute_behavior_metrics` and `calculate_banos_for_each_file` take the keyword
  `missed_bouts`.
- MATLAB: the `'missed_bouts'` and `'aggregation'` options of `BANOS_score`;
  `BANOSparseOptions` and `BANOSpoolComponents`; the terms as second output of
  `BANOScalculateSO`, `BANOScalculateTP` and `BANOScalculateIC`, and the components as
  second output of `BANOScomputeBehaviorMetrics` and `BANOScalculateBANOSForEachFile`.
- Golden values of the 10 recordings scored together, for each combination of the two
  options (`all_recordings` in the v110 fixtures), checked by the regression and parity
  tests.
- `py.typed`: type checkers read the annotations of the package.
- `CITATION.cff`, with the article to cite.
- Mode 3 of `tests/fixtures/compare_fixtures.py` (v0.2.0 against v1.1.0), and a test that
  runs the script and compares its output with `reports/fixture_comparison.html`.

### Changed
- **Input errors.** `ValueError` when the prediction and the ground truth of a recording
  have different numbers of frames (a shorter prediction raised `KeyError` when a real
  bout longer than one frame reached past its last frame, and was scored otherwise; a
  longer one was scored) or when a recording has no frame (it scored 1.0 on all six
  metrics).
- **Warnings.** A `UserWarning` names the recording and the column for each column
  dropped (values other than 0 and 1, or missing or invalid on the other side) and for
  each column whose NaN values are replaced by 0; both were silent. The warnings point at
  the line that called `banos.score()` or `preprocess_data()`. Valid input gives no
  warning.
- **Options checked on entry.** `banos.score()` and the pipeline functions raise
  `ValueError` for an unknown `matching`, `missed_bouts` or `aggregation` value even when
  nothing would be scored; an unknown `matching` used to pass unnoticed when no behavior
  had real bouts.
- **MATLAB.** `BANOSpreprocessData` raises and warns in the same way (identifiers
  `BANOS:lengthMismatch`, `BANOS:noFrame`, `BANOS:nanReplaced`, `BANOS:columnDropped`).
  Options are stricter: an unknown option name, which was ignored, and an unknown
  `'matching'` value, which was treated as greedy, raise an error (`BANOS:unknownOption`,
  `BANOS:missingOptionValue`, `BANOS:invalidOption`). The other errors of `BANOS_score`
  get identifiers too: `BANOS:optimalNotImplemented`, `BANOS:missingGroundTruth` and
  `BANOS:invalidData`.
- **Imports.** `calculate_so`, `calculate_tp_metric` and `calculate_ic` are no longer
  importable from `banos.pipeline`, which only used them; import them from `banos.core`.
- **Packaging.** matplotlib and seaborn move from the runtime dependencies to the
  `notebook` extra: `pip install banos` installs numpy, pandas and scipy only. The `dev`
  extra is removed; the `dev` dependency group, which `uv sync` installs, stays. Authors
  and maintainers are set, the license is an SPDX expression (`License-Expression: MIT`,
  with `License-File`) and the license classifier is removed. The build backend is
  `hatchling>=1.27,<2`. The sdist holds the package, its tests with the data they read,
  `demo/quickstart.py`, README, LICENSE and CHANGELOG (about 70 kB instead of 1.2 MB).
- **CI.** The test matrix runs the parity tests; a `Type check (mypy)` job runs mypy on
  `src/`; checkouts do not keep credentials. The publish workflow checks that the tag is
  `v` followed by the version in `pyproject.toml` and runs the whole CI before building
  and publishing.
- **Development tools.** Pre-commit runs ruff 0.15.7, the version of the lock and CI. CI
  also lints `demo/quickstart.py`. mypy, pandas-stubs and scipy-stubs join the dev group;
  pytest-html leaves it.
- **Tests.** `tests/test_comparison_report.py`, which was always skipped, is removed:
  `test_parity_group_metrics` checks the same values, and now also fails when Python and
  MATLAB report different behaviors.

### Fixed
- The `score()` docstring and the `BANOS_score` help said that a metric is NaN when the
  ground truth has no bout; per file, such a behavior scores 1.0 or 0.0.
- README: the IC formula (the denominator is the bout length minus 1), SO and TP (averaged
  over every overlapping pair, not over matched pairs), the return value for several
  recordings, the dependencies, and links that did not work on the PyPI page.
- Tutorials: the text said that the prediction shifted by 15 frames still detects both
  bouts (DA 1.0); it shares no frame with them, so DA is 0 (it printed NaN before this
  release).
- The CalMS21 tutorial printed the absolute local paths of its model and data cache; it
  prints them relative to the repository. Its download failed: data.caltech.edu refuses
  the default user agent of urllib (HTTP 403), so the requests now send a User-Agent
  that names the tutorial and the repository. Its stored outputs are those of 1.1.0.
- `compare_fixtures.py` swapped the `VALUE->NULL` and `NULL->VALUE` tags and misdescribed
  the v0.1.5 to v0.2.0 changes in its legend; it no longer fails on a Windows console.
- `test_preprocess_data_does_not_mutate_caller_dict` compared a dict's id with itself and
  could not fail; it now compares the caller's data before and after. `test_score_version`
  compares `banos.__version__` with the version in `pyproject.toml`.
- Type errors reported by mypy: `is_logical_column` returns a Python `bool`, and
  `drop_non_logical_columns` is annotated with the column labels it returns.
- The MATLAB code averaged with `nanmean`, a function of the Statistics and Machine
  Learning Toolbox, so scoring several recordings needed that toolbox. It now uses
  `mean(..., 'omitnan')` of base MATLAB, which gives the same values.
- `SECURITY.md` said that BANOS reads CSV files (it reads no file: it takes DataFrames or
  MATLAB cell arrays) and that `uv.lock` pins the dependencies users get (it pins the
  development and CI environment). `SETUP.md` said to allow all actions (the repository
  allows selected actions, pinned by SHA).

## [1.0.0] — 2025-02-27

First stable release. Metric computation and the golden fixtures are unchanged from 0.3.0.

### Changed
- Development status set to Production/Stable
- New project logo, also provided as a vector file (`assets/Logo_BANOS.svg`)

## [0.3.0] — 2025-02-19

### Breaking Changes
- Minimum Python version raised to 3.11 (3.9 reaches end of life in October 2025, 3.10 in October 2026)

### Security
- Refreshed `uv.lock` onto non-vulnerable releases of every flagged dependency
- GitHub Actions pinned to commit SHAs; the repository now requires SHA pinning
- Dependency policy documented in `SECURITY.md`

### Maintenance
- CI matrix now covers Python 3.11 to 3.14
- CI installs with `uv sync --locked`, so the committed lockfile is what gets tested
- Dependabot configured for GitHub Actions only
- Regenerated `uv.lock`, which had drifted from `pyproject.toml`

No change to metric computation: `src/banos/` and the golden fixtures are unchanged.

## [0.2.0] — 2025-01-23

### Breaking Changes
- Package renamed from `BANOS` to `banos` on PyPI (`pip install banos`)
- New primary API: `banos.score(pred_df, gt_df)` replaces 3-step pipeline
- **Absent-behavior scoring**: when GT has no bouts, metrics are no longer `NaN`/`0`:
  - Machine also has no bouts → all metrics = **1.0** (correct absence, rewarded)
  - Machine predicts bouts that don't exist in GT → all metrics = **0.0** (false detection, penalized)
- **Undefined metrics are NaN instead of 0** (missing from this entry until 1.1.0): for a
  behavior with real bouts in a recording and no predicted bout matching any of them (so
  none overlapping them), F1, SO and TP became NaN instead of 0, and so did precision when
  nothing was predicted. The averages leave NaN out, so such a recording no longer
  counted in these means. 1.1.0 scores this F1 as 0 again.
- Python minimum version raised to 3.9

### Bug Fixes
- Fixed IC boundary: last transition within GT bout was not counted (`range(gt_end-1)` → `range(gt_end)`)
- **One-frame real bouts are left out of IC** (missing from this entry until 1.1.0): such a
  bout has no frame pair to compare; v0.1.5 gave it an IC of 0, whatever was predicted.
- Fixed variable shadowing of `tp` count and `tp` metric in `compute_behavior_metrics`
- Fixed Matlab `BANOSmatchHeaders`: now matches by column name, not column index
- Fixed `aggregate_metrics`: NaN values now excluded from averages (nanmean behavior)

### New Features
- `banos.score()` convenience function with single/multi-file support
- `matching='optimal'` parameter for Hungarian algorithm matching (via scipy)
- Full test suite: unit tests, regression tests, Python/Matlab parity tests
- MIT license (replaces custom Early Access license)
- Modern packaging: `pyproject.toml`, `src/` layout, Ruff linting, pre-commit hooks
- CI/CD via GitHub Actions

## [0.1.3] — 2024

Initial public release.
