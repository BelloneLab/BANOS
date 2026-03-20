# Release Process

## Pre-release Checklist

Before tagging a release, verify:

- [ ] All CI tests pass on `main` (`pytest` green, coverage >= 80%)
- [ ] `uv run pytest tests/test_regression.py` passes (verifies golden fixtures)
- [ ] Version bumped consistently in `pyproject.toml` and `src/banos/__init__.py`
- [ ] `CHANGELOG.md` has an entry for this version with a summary of changes
- [ ] README examples are up to date

---

## Python Package — PyPI

Publishing is fully automated via GitHub Actions on version tag push.

```bash
# 1. Bump version in two places
#    pyproject.toml: version = "X.Y.Z"
#    src/banos/__init__.py: __version__ = "X.Y.Z"

# 2. Update CHANGELOG.md

# 3. Commit
git commit -am "chore: bump version to vX.Y.Z"

# 4. Tag
git tag vX.Y.Z

# 5. Push tag — this triggers the publish workflow automatically
git push origin vX.Y.Z
```

The `publish.yml` workflow:
1. Runs the full test suite (excluding parity tests)
2. Builds the package with `uv build`
3. Publishes to PyPI using OIDC trusted publishing (no API token required)

The `README.md` is automatically bundled because `pyproject.toml` specifies
`readme = "README.md"` — no manual copying needed.

**Note:** OIDC trusted publishing requires a one-time setup in your PyPI account:
go to the project page → Publishing → Add a new pending publisher, and configure
it for this GitHub repository and the `publish.yml` workflow.

---

## MATLAB File Exchange — Manual Steps

MATLAB File Exchange does not have a public API for automated uploads.
Updates are done manually when a new version is released.

1. Download the release ZIP from the GitHub releases page:
   `https://github.com/BelloneLab/BANOS/releases`

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
| `tests/fixtures/golden_python_v020.json` | **Current Python (v0.2.0)** — score 1.0 for correct absence, 0.0 for false detection, corrected IC counting. Canonical reference. |
| `tests/fixtures/golden_matlab_v020.json` | **Current Matlab (v0.2.0)** — same semantics as Python. Used for parity tests. |
| `tests/fixtures/golden_python_v015.json` | **Original Python (v0.1.5)** — returns 0 for absent behaviors, IC misses last frame pair. Kept for historical comparison only. |

To regenerate fixtures after a deliberate algorithm change:
```bash
python tests/fixtures/python/generate_golden_fixtures.py
matlab -batch "run('tests/fixtures/matlab/generate_matlab_fixtures.m')"
```
