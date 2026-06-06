# PR Maintenance, Auto-Fix, and Workflow Cleanup

![Case Study](https://img.shields.io/badge/Case%20Study-4-1f6feb?style=flat-square) ![Difficulty](https://img.shields.io/badge/Difficulty-%E2%98%85%E2%98%85%E2%98%85-cf222e?style=flat-square) ![Level](https://img.shields.io/badge/Level-Advanced-cf222e?style=flat-square) [![Case Studies](https://img.shields.io/badge/%E2%AC%85%20Case%20Studies-555?style=flat-square)](README.md)

> Level: **Advanced** | Suggested modules: **Module 11, Module 20**

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

      # `gh pr list --json number --jq '.[].number'` returns one PR number per
      # line; the loop tries to update each branch and comments if it conflicts.
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

      # The auto-fix loop (checkout each PR branch, run pre-commit, commit and
      # push only if files changed) lives in a script to keep this step readable.
      - name: Apply safe pre-commit fixes
        if: github.event_name == 'schedule'
        env:
          GH_TOKEN: ${{ github.token }}
        shell: bash
        run: ./scripts/autofix-open-prs.sh

  cleanup-runs:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"

      # The helper lists runs, keeps anything newer than --days, and deletes the
      # rest. --dry-run true just previews. No jq/date arithmetic to read here.
      - name: Clean old workflow runs
        env:
          GH_TOKEN: ${{ github.token }}
        run: python scripts/clean_old_runs.py --days 7 --dry-run ${{ inputs.dry_run || 'true' }}
```

## 8. Line-by-Line Explanation

- `push` to `main` reacts when the base branch changes.
- `schedule` allows routine maintenance without developer action.
- `workflow_dispatch.dry_run` makes cleanup safer.
- `contents: write` is required only because auto-fix pushes commits.
- `pull-requests: write` allows branch updates and comments.
- `actions: write` allows workflow run deletion.
- `gh pr update-branch` keeps PR branches current without manual merges.
- Auto-fix runs `scripts/autofix-open-prs.sh`, which uses `pre-commit` and only commits when files changed.
- Cleanup runs `scripts/clean_old_runs.py`, which deletes runs older than `--days` and honors `--dry-run`.

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
