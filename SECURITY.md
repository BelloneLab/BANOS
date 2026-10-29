# Security Policy

## Supported Versions

Only the current PyPI release of BANOS receives security fixes.

| Version | Supported |
|---------|-----------|
| Latest PyPI release | Yes |
| Older releases | No |

## Reporting a Vulnerability

**Do NOT open a public GitHub Issue for security vulnerabilities.**

Please use one of the following private channels:

- **GitHub private security advisory**: navigate to the
  [Security tab](https://github.com/BelloneLab/BANOS/security/advisories/new)
  of this repository and open a private advisory.
- **Email**: contact the maintainer directly at bijeytis@gmail.com.

## Response

This project is maintained on a best-effort basis. We aim to respond within **30 days**.
There is no guaranteed SLA.

## Scope

BANOS is a pure-Python / MATLAB computation library. It:

- Has **no network access**
- Has **no authentication or authorization layer**
- Has **no persistent data storage**
- Reads **no file**: it takes pandas DataFrames (Python) or cell arrays (MATLAB) that the
  caller has already loaded. Only the demos and tutorials read files, the CSV files of
  the repository and, for the CalMS21 tutorial, a dataset it downloads

The attack surface is minimal. Security reports are most relevant to dependency
vulnerabilities (e.g., malicious `pandas` or `scipy` releases) or unsafe handling of
user-supplied data.

## Dependency Policy

BANOS accompanies a peer-reviewed publication and is maintained in security-only mode.
Dependency handling follows two rules.

**Numerical results must not change.** `uv.lock` pins the development and CI
environment. Every update of the lock is validated by the golden regression tests
(`tests/test_regression.py`, tolerance `1e-10`) across the whole supported Python
matrix before it is merged. An update that moves a metric is rejected — the golden
fixtures are never regenerated to accommodate a dependency bump. Users who install
`banos` are not bound by the lock: they get any version of its dependencies within the
bounds declared in `pyproject.toml`.

**Updates are deliberate, never automatic.** Dependabot alerts are enabled for
monitoring, but automatic security updates and version updates are disabled. Each
alert is triaged by hand and remediated with a targeted `uv lock --upgrade-package`,
never a blanket `uv lock --upgrade`.

Dependabot itself is configured for GitHub Actions only (see
[`.github/dependabot.yml`](.github/dependabot.yml)). Actions are pinned to commit
SHAs: they run with access to this repository and to the OIDC identity used for PyPI
publishing, and unlike Python packages they cannot affect a computed result.

One caveat when reading alerts: Dependabot reports every entry of `uv.lock` as
`runtime` scope. In practice the BANOS runtime closure is limited to `numpy`,
`pandas` and `scipy`, and the packages they depend on. The `notebook` and `calms21`
extras are optional tutorial environments, and the `dev` dependency group is the
development environment; neither is needed to import or use BANOS.
