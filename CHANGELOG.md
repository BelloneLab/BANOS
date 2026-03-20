# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] — 2026-03-19

### Breaking Changes
- Package renamed from `BANOS` to `banos` on PyPI (`pip install banos`)
- New primary API: `banos.score(pred_df, gt_df)` replaces 3-step pipeline
- **Absent-behavior scoring**: when GT has no bouts, metrics are no longer `NaN`/`0`:
  - Machine also has no bouts → all metrics = **1.0** (correct absence, rewarded)
  - Machine predicts bouts that don't exist in GT → all metrics = **0.0** (false detection, penalized)
- Python minimum version raised to 3.9

### Bug Fixes
- Fixed IC boundary: last transition within GT bout was not counted (`range(gt_end-1)` → `range(gt_end)`)
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
