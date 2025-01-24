# Contributing to BANOS

## Project Status

BANOS is considered **functionally complete**. It implements a fixed set of
metrics for evaluating behavioral annotations. We do not plan new features or major refactors.
The codebase is intentionally stable — "stable by design" reflects the nature of the underlying
metrics, which are defined in the accompanying paper.

## Maintenance Lifecycle

**Active window**: During and shortly after paper publication, the maintainer actively monitors
issues and reviews bug-fix PRs.

**Maintenance mode**: After the active window, BANOS enters maintenance mode. Only security
issues and critical bugs (incorrect metric computations) will be addressed.

If you need features beyond the current scope, please **fork the repository**. The MIT license
allows unrestricted use and modification — forking is a first-class option, not a workaround.

## Maintainer

**Benoit Girard** (BelloneLab)
Contact: open a [GitHub Issue](https://github.com/BelloneLab/BANOS/issues).

## How to Report a Bug

Open a [GitHub Issue](https://github.com/BelloneLab/BANOS/issues) using the bug report
template. Please include:

- BANOS version (`pip show banos` or check `pyproject.toml`)
- Python version (or MATLAB version, if applicable)
- A minimal reproducible example (small CSV + code that demonstrates the wrong output)

## How to Contribute Code

1. Fork the repository
2. Create a branch for your fix
3. Open a PR against `main`
4. PRs are reviewed on a **best-effort** basis — there is no guaranteed turnaround time

Code style:
- Python: follow existing style enforced by `ruff` (lint + format)
- Use type hints consistent with the existing codebase
- Tests are required for bug fixes (see `tests/`)

## What We Accept

- Bug fixes (incorrect metric computations, edge case errors)
- Documentation improvements
- Test coverage improvements

## What We Do Not Actively Pursue

- New metrics
- New features or API changes
- Performance optimizations beyond correctness

If your contribution falls into the second category, it is unlikely to be merged. Consider
forking instead.

## Forking

If you need features beyond the current scope, please fork. The MIT license allows unrestricted
use and modification. Forks are encouraged — this is the intended path for extending BANOS.

## Development Setup

See [`SETUP.md`](SETUP.md) for instructions on setting up a local development environment.
