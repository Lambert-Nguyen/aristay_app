#!/usr/bin/env bash
set -euo pipefail

banner() {
  echo "============================================================"
  echo "$@"
  echo "============================================================"
}

banner "WARNING"
echo "This will rewrite git history to remove secrets and/or files."
echo "Make a backup before continuing:"
echo "  git clone --mirror \$(git remote get-url origin) backup-bare.git"
echo
echo "Make sure all work is pushed and PRs are merged or paused."
echo

if ! command -v git &>/dev/null; then
  echo "git not found." >&2
  exit 1
fi

if ! command -v git-filter-repo &>/dev/null; then
  echo "git-filter-repo is required but not installed." >&2
  echo "Install tips:"
  echo "  • Homebrew:   brew install git-filter-repo"
  echo "  • pipx:       pipx install git-filter-repo"
  echo "  • pip (venv): pip install git-filter-repo"
  exit 1
fi

mkdir -p tools/secret-hygiene

# Overwrite list of paths to purge from history each run.
cat > tools/secret-hygiene/paths-to-remove.txt <<'EOF'
aristay_backend/firebase_credentials.json
.env
.env.local
.env.production
.env.development
aristay_backend/.env
aristay_backend/.env.local
EOF

REPLACE_ARGS=()
if [[ -s tools/secret-hygiene/replacements.txt ]]; then
  REPLACE_ARGS=(--replace-text tools/secret-hygiene/replacements.txt)
fi

banner "About to run git-filter-repo"
echo "Removing paths listed in tools/secret-hygiene/paths-to-remove.txt"
if [[ -n "${REPLACE_ARGS[*]:-}" ]]; then
  echo "Using replacements from tools/secret-hygiene/replacements.txt"
fi
echo

git filter-repo --force \
  --paths-from-file tools/secret-hygiene/paths-to-remove.txt \
  --invert-paths \
  "${REPLACE_ARGS[@]}"

# Cleanup unreachable data locally.
git reflog expire --expire-unreachable=now --all || true
git gc --prune=now --aggressive || true

banner "NEXT STEPS"
cat <<'STEPS'
1) Review locally:
   git log --oneline --graph --decorate | head -n 30

2) Force push rewritten history:
   git push --force --all
   git push --force --tags

3) Tell collaborators to re-clone the repository fresh (history changed).

4) Rotate any keys that were exposed (Django SECRET_KEY, SMTP, Cloudinary, Firebase/FCM, Sentry, etc.).

STEPS
