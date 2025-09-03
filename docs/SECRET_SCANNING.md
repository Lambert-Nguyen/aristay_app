# Secret Scanning

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
