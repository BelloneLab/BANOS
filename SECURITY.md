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
- Reads only local CSV files passed explicitly by the user

The attack surface is minimal. Security reports are most relevant to dependency
vulnerabilities (e.g., malicious `pandas` or `scipy` releases) or unsafe handling of
user-supplied CSV input.
