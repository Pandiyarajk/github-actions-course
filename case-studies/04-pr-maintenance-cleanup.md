# PR Maintenance, Auto-Fix, and Workflow Cleanup

> Level: **Advanced** | Suggested module: **Module 10**

## 1. Title

Pull Request Maintenance and Workflow Cleanup for `sample-app`

## 2. What This Workflow Does

This case study teaches how to maintain open pull requests, apply safe formatting fixes, report merge conflicts, and clean old workflow runs. It generalizes production maintenance workflows into safe public examples.

Real-world scenario: a busy repository has many open PRs, frequent default-branch changes, and high workflow volume. Maintainers want automation that reduces drift and operational clutter.

## 3. When to Use This

- Use it when open PRs frequently fall behind `main`.
- Use it when formatting fixes are safe to apply automatically.
- Use it when maintainers need early merge-conflict visibility.
- Use it when old workflow runs create noise or storage pressure.

## 4. Workflow Breakdown

- **Trigger (`on`)**: `push` to `main` updates PRs; `schedule` runs maintenance; `workflow_dispatch` supports safe manual runs.
- **Jobs**: One job handles PR maintenance; another can handle cleanup.
- **Steps**: List PRs, update branches, comment on conflicts, run pre-commit, commit safe fixes, delete old runs.
- **Actions used**: `actions/checkout`, `actions/setup-python`, GitHub CLI.
- **Conditions**: Only run write operations from trusted branches or scheduled default-branch workflows.
- **Outputs**: PR comments, auto-fix commits, workflow summaries.

## 5. ASCII Flow Diagram

```text
Push to Main / Schedule / Manual
   |
   v
List Open Pull Requests
   |
   +--> Update Branch
   |      |
   |      +--> Conflict? Comment on PR
   |
   +--> Run Safe Auto-Fix
   |      |
   |      +--> Changes? Commit and Push
   |
   v
Clean Old Workflow Runs
   |
   v
Write Summary
```

## 6. Simple Version YAML

```yaml
name: List Open Pull Requests

on:
  workflow_dispatch:

permissions:
  pull-requests: read

jobs:
  list:
    runs-on: ubuntu-latest
    steps:
      - name: List open PRs
        env:
          GH_TOKEN: ${{ github.token }}
        run: gh pr list --state open
```

## 7. Production Version YAML

```yaml
name: PR Maintenance and Cleanup

on:
  push:
    branches:
      - main
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:
    inputs:
      dry_run:
        type: boolean
        default: true

permissions:
  contents: write
  pull-requests: write
  actions: write

jobs:
  maintain-prs:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout default branch
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"
          cache: pip

      - name: Install tools
        run: pip install pre-commit

      - name: Update open PR branches
        env:
          GH_TOKEN: ${{ github.token }}
        shell: bash
        run: |
          for pr in $(gh pr list --state open --json number --jq '.[].number'); do
            if gh pr update-branch "$pr"; then
              echo "Updated PR #$pr"
            else
              gh pr comment "$pr" --body "This pull request could not be updated automatically because of merge conflicts. Please merge the latest main branch locally and resolve conflicts."
            fi
          done

      - name: Apply safe pre-commit fixes
        if: github.event_name == 'schedule'
        env:
          GH_TOKEN: ${{ github.token }}
        shell: bash
        run: |
          for pr in $(gh pr list --state open --json number --jq '.[].number'); do
            branch=$(gh pr view "$pr" --json headRefName --jq '.headRefName')
            git fetch origin "$branch"
            git checkout -B "$branch" "origin/$branch"
            pre-commit run --all-files || true
            if [ -n "$(git status --porcelain)" ]; then
              git config user.name "automation-bot"
              git config user.email "automation@example.com"
              git add .
              git commit -m "chore: apply safe formatting fixes"
              git push origin "HEAD:$branch"
            fi
          done

  cleanup-runs:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Clean old workflow runs
        env:
          GH_TOKEN: ${{ github.token }}
          DRY_RUN: ${{ inputs.dry_run || 'false' }}
        shell: bash
        run: |
          set -euo pipefail
          cutoff=$(date -d "7 days ago" +%Y-%m-%dT%H:%M:%SZ)
          total=0
          for run_id in $(gh run list --limit 100 --json databaseId,createdAt --jq ".[] | select(.createdAt < \"$cutoff\") | .databaseId"); do
            if [ "$DRY_RUN" = "true" ]; then
              echo "Would delete run $run_id"
            else
              gh api -X DELETE "repos/$GITHUB_REPOSITORY/actions/runs/$run_id"
            fi
            total=$((total + 1))
          done
          echo "Processed $total old workflow runs." >> $GITHUB_STEP_SUMMARY
```

## 8. Line-by-Line Explanation

- `push` to `main` reacts when the base branch changes.
- `schedule` allows routine maintenance without developer action.
- `workflow_dispatch.dry_run` makes cleanup safer.
- `contents: write` is required only because auto-fix pushes commits.
- `pull-requests: write` allows branch updates and comments.
- `actions: write` allows workflow run deletion.
- `gh pr update-branch` keeps PR branches current without manual merges.
- Auto-fix uses `pre-commit` and only commits when files changed.
- Cleanup writes a summary so maintainers know what happened.

## 9. Common Mistakes

- Auto-fixing behavior-changing code instead of formatting-only changes.
- Pushing to untrusted fork branches.
- Repeatedly posting duplicate conflict comments.
- Deleting workflow runs without dry-run validation.
- Granting broad repository permissions when specific scopes are enough.

## 10. Debugging Guide

- Start with `workflow_dispatch` and `dry_run: true`.
- Run against one test PR before enabling all PRs.
- Print PR number and branch before each operation.
- Confirm branch protection allows update-branch automation.
- Check GitHub API rate limits for large repositories.

## 11. Exercises

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | List open PRs using `gh pr list`. | Workflow logs open PR numbers. |
| Intermediate | Comment on a PR when an update fails. | PR receives a generic conflict comment. |
| Challenge | Add scheduled pre-commit auto-fix and dry-run cleanup. | Formatting commits and cleanup summaries are created safely. |

---

[Case Study Index](README.md) | [Course Home](../README.md)
