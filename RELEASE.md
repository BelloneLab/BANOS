# Release Process

## Pre-release Checklist

Before tagging a release, verify:

- [ ] CI is green on `main`: `Lint (ruff)`, `Type check (mypy)` and `Test (Python 3.11)`
      to `Test (Python 3.14)`, which run the whole suite, regression and parity tests
      included, with coverage >= 80%
- [ ] The version is the same in `pyproject.toml`, `src/banos/__init__.py`, `uv.lock`
      (run `uv lock`), `CITATION.cff` and the `Version` line of `matlab/BANOS/Contents.m`
      (`test_score_version` compares the first two)
- [ ] `CHANGELOG.md` has an entry for this version, dated on release day; the same date
      is set in `CITATION.cff` (`date-released`) and in `matlab/BANOS/Contents.m`
- [ ] README examples are up to date

---

## Python Package — PyPI

Publishing is automated by GitHub Actions when a version tag is pushed. `main` only
accepts changes through a pull request, so the version is bumped on a branch.

```bash
# 1. On a branch, bump the version
#    pyproject.toml:          version = "X.Y.Z"
#    src/banos/__init__.py:   __version__ = "X.Y.Z"
#    CITATION.cff:            version: X.Y.Z  and  date-released: YYYY-MM-DD
#    matlab/BANOS/Contents.m: % Version X.Y.Z  DD-Mon-YYYY
uv lock

# 2. Date the CHANGELOG.md entry

# 3. Commit, open a pull request, and merge it once CI is green
git commit -am "chore: release vX.Y.Z"

# 4. Tag the merged commit on main
git fetch origin
git tag -a vX.Y.Z origin/main -m "BANOS X.Y.Z"

# 5. Push the tag — this triggers the publish workflow
git push origin vX.Y.Z
```

The `publish.yml` workflow:
1. Checks that the tag is `v` followed by the version in `pyproject.toml`, and stops
   otherwise
2. Runs the whole CI workflow (`ci.yml`): lint, type check, and the test matrix on
   Python 3.11 to 3.14, parity tests included
3. Builds the package with `uv build` and publishes it to PyPI using OIDC trusted
   publishing (no API token required). This job runs in the `pypi` environment, which
   waits for the maintainer's approval

The `README.md` is automatically bundled because `pyproject.toml` specifies
`readme = "README.md"` — no manual copying needed.

**Note:** OIDC trusted publishing requires a one-time setup in your PyPI account:
go to the project page → Publishing → Add a new publisher, and configure it for this
GitHub repository, the `publish.yml` workflow and the `pypi` environment.

---

## MATLAB File Exchange — Manual Steps

MATLAB File Exchange does not have a public API for automated uploads.
Updates are done manually when a new version is released.

1. Download the source ZIP of the tag:
   `https://github.com/BelloneLab/BANOS/archive/refs/tags/vX.Y.Z.zip`
   (also linked from the tag on the GitHub releases page,
   `https://github.com/BelloneLab/BANOS/releases`)

2. Log in to MATLAB File Exchange:
   `https://www.mathworks.com/matlabcentral/fileexchange/`

3. Navigate to the BANOS submission → click **Edit**.

4. Upload the new release ZIP file.

5. Update the version number and description to match `CHANGELOG.md`.

6. Click **Submit** and wait for the automated review.

---

## Notes on Fixture Files

| File | Represents |
|------|-----------|
| `tests/fixtures/golden_python_v110.json` | **Current Python (v1.1.0)** — detection F1 0 when no real bout is matched, IC averaged over the found real bouts. Each `Recording_N` entry scores one recording alone with the default options; `all_recordings` scores the 10 recordings together for each combination of `missed_bouts` and `aggregation`. Canonical reference, used by the regression tests. |
| `tests/fixtures/golden_matlab_v110.json` | **Current MATLAB (v1.1.0)** — the same entries, computed by the MATLAB code. Used by the parity tests. |
| `tests/fixtures/golden_python_v020.json` | **Python v0.2.0** (archive) — 1.0 for correct absence, 0.0 for false detection, NaN for undefined metrics (F1 included), IC counting the last frame pair. |
| `tests/fixtures/golden_matlab_v020.json` | **MATLAB v0.2.0** (archive) — same semantics as Python v0.2.0. |
| `tests/fixtures/golden_python_v015.json` | **Original Python (v0.1.5)** (archive) — 0 for absent behaviors and undefined metrics, IC misses the last frame pair. Kept for historical comparison only. |

To regenerate the current fixtures after a deliberate algorithm change, from the project
root:
```bash
uv run python tests/fixtures/python/generate_golden_fixtures.py
matlab -batch "run('tests/fixtures/matlab/generate_matlab_fixtures.m')"
```

Then regenerate the comparison report (`reports/fixture_comparison.html`), which
`tests/test_compare_fixtures.py` checks against the fixtures:
```bash
uv run python tests/fixtures/compare_fixtures.py --html
```

The archives are not regenerated. The v0.1.5 file can be reproduced with the BANOS 0.1.5
package from PyPI and Python 3.12 or later (with Python 3.11, about a hundred values
differ in their last digit):
```bash
uv run --isolated --no-project --python 3.12 --with "BANOS==0.1.5" python tests/fixtures/python/generate_archive_fixtures.py
```
