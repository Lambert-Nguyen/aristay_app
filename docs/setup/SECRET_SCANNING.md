# Secret Scanning

This repository uses [gitleaks](https://github.com/gitleaks/gitleaks) for secret scanning both locally and in CI.

## Local Scanning (pre-commit)

1. **Install pre-commit:**
   ```sh
   pip install pre-commit && pre-commit install
   ```
   This will enable automatic secret scanning on every commit.

2. **Run manual scan:**
   ```sh
   gitleaks detect -v
   ```

## CI Scanning

- Secret scanning runs automatically on pushes and pull requests to `main` and `master` branches via GitHub Actions.

## Notes

- If a secret is detected, follow the remediation steps in `tools/secret-hygiene`.

---
For more information, see the [gitleaks documentation](https://github.com/gitleaks/gitleaks).# Secret Scanning

## Local Setup

1. Install `pre-commit`:
   ```bash
   pip install pre-commit && pre-commit install
   ```

2. Run a manual scan:
   ```bash
   gitleaks detect -v
   ```

## CI Integration

- Secret scanning is automatically performed on all pushes and pull requests to `main` and `master` branches.
