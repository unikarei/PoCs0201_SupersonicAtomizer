#!/usr/bin/env bash
# Commit all current changes with a message (used after completing a task)
set -euo pipefail

MSG="${1:-Automated commit after task completion}"

if ! command -v git >/dev/null 2>&1; then
  echo "git not found in PATH" >&2
  exit 2
fi

echo "Staging all changes..."
git add -A

echo "Committing with message: $MSG"
git commit -m "$MSG"

echo "Commit complete."
