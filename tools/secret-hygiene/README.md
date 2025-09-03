# Secret Hygiene (History Purge Kit)

> Use these tools if secrets accidentally landed in git history.

## What this does
- Rewrites repository history to *remove* tracked secret files (e.g., `.env`) and optionally replace known tokens via regex/string substitution.

## One-time backup
```bash
git clone --mirror $(git remote get-url origin) backup-bare.git
