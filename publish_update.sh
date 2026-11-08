#!/usr/bin/env bash
# Refresh the research export, commit changes, and push the same GitHub repo.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
python sync_from_workspace.py
git diff --check
git add -A
git diff --cached --check
if ! git diff --cached --quiet; then
  git commit -m "${1:-Update dynamic collaboration benchmark research}"
fi
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "No origin remote configured; local commit is ready but not uploaded." >&2
  exit 2
fi
git push origin main
