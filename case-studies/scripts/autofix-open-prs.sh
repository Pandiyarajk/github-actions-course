#!/usr/bin/env bash
# Apply safe formatting fixes (pre-commit) to every open PR branch and push
# the changes back. Only formatting/lint auto-fixes — never behavior changes.
#
# Requires: gh (authenticated via GH_TOKEN), git, pre-commit.
# Run from a scheduled job on the default branch.
set -euo pipefail

for pr in $(gh pr list --state open --json number --jq '.[].number'); do
  branch=$(gh pr view "$pr" --json headRefName --jq '.headRefName')
  echo "Processing PR #$pr (branch: $branch)"

  git fetch origin "$branch"
  git checkout -B "$branch" "origin/$branch"

  # Run formatters/linters; `|| true` so a non-zero exit doesn't stop the loop.
  pre-commit run --all-files || true

  # Only commit if pre-commit actually changed files.
  if [ -n "$(git status --porcelain)" ]; then
    git config user.name "automation-bot"
    git config user.email "automation@your-domain.com"
    git add .
    git commit -m "chore: apply safe formatting fixes"
    git push origin "HEAD:$branch"
    echo "Pushed formatting fixes to $branch"
  else
    echo "No changes for $branch"
  fi
done
