# AI-Assisted Pull Request Review

![Case Study](https://img.shields.io/badge/Case%20Study-5-1f6feb?style=flat-square) ![Difficulty](https://img.shields.io/badge/Difficulty-%E2%98%85-cf222e?style=flat-square) ![Level](https://img.shields.io/badge/Level-Advanced-cf222e?style=flat-square) [![Case Studies](https://img.shields.io/badge/%E2%AC%85%20Case%20Studies-555?style=flat-square)](README.md)

> Level: **Advanced** | Suggested modules: **Module 3, Module 20**

## 1. Title

AI-Assisted Pull Request Review for `sample-app`

## 2. What This Workflow Does

This case study teaches how to run an external review assistant against a pull request diff and post concise review comments. The workflow is intentionally generic and does not include vendor-specific prompts, internal review rules, or real service endpoints.

Real-world scenario: a team wants automated review support for high-signal issues such as security risks, logic bugs, performance regressions, duplicate code, unused code, and invalid structured files.

## 3. When to Use This

- Use it as a reviewer assistant, not as the only approval gate.
- Use it when review comments can be kept concise and actionable.
- Use it when the team can control which files and issue types are reviewed.
- Use it when external service usage is approved by security and compliance teams.

## 4. Workflow Breakdown

- **Trigger (`on`)**: Runs on pull requests and optionally manual dispatch.
- **Jobs**: One review job resolves the PR and runs the assistant.
- **Steps**: Checkout full history, resolve PR number, collect diff, call review script, post comments.
- **Actions used**: `actions/checkout`, `actions/setup-python`, GitHub CLI.
- **Conditions**: Skip review if no PR is found or the diff is empty.
- **Outputs**: Inline PR comments, optional summary comments, and optional diff artifacts during testing.

## 5. ASCII Flow Diagram

```text
Pull Request
   |
   v
Checkout Full History
   |
   v
Resolve PR Number
   |
   v
Fetch Diff and Existing Comments
   |
   v
Run Review Assistant
   |
   v
Post Concise Comments
```

## 6. Simple Version YAML

```yaml
name: Print PR Diff

on:
  pull_request:

permissions:
  contents: read
  pull-requests: read

jobs:
  diff:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Print diff
        env:
          GH_TOKEN: ${{ github.token }}
        run: gh pr diff ${{ github.event.pull_request.number }}
```

## 7. Production Version YAML

```yaml
name: AI-Assisted PR Review

on:
  pull_request:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"
          cache: pip

      - name: Install review dependencies
        run: pip install requests

      - name: Resolve pull request
        id: pr
        env:
          GH_TOKEN: ${{ github.token }}
        shell: bash
        run: |
          pr_number=$(gh pr view --json number --jq .number 2>/dev/null || true)
          echo "number=$pr_number" >> $GITHUB_OUTPUT

      - name: Run review assistant
        if: steps.pr.outputs.number != ''
        env:
          GH_TOKEN: ${{ github.token }}
          API_TOKEN: ${{ secrets.API_TOKEN }}
        shell: bash
        run: |
          gh pr diff "${{ steps.pr.outputs.number }}" > pr.diff
          if [ ! -s pr.diff ]; then
            echo "No diff found. Skipping review."
            exit 0
          fi
          python scripts/review_diff.py \
            --diff pr.diff \
            --api-url https://example.com/review \
            --max-comments 10

      - name: Upload review debug artifact
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: review-input
          path: pr.diff
          if-no-files-found: ignore
```

## 8. Line-by-Line Explanation

- `pull_request` gives the assistant a real review context.
- `pull-requests: write` is needed only if comments are posted.
- `fetch-depth: 0` gives review scripts enough history for comparisons.
- The PR resolution step exits safely when the branch has no open PR.
- The diff is saved to `pr.diff` for traceability and debugging.
- `[ ! -s pr.diff ]` tests whether `pr.diff` is empty (`-s` = "size greater than zero"); if so the step exits early instead of calling the review service with nothing.
- `API_TOKEN` represents a generic external review service credential.
- `--max-comments 10` limits review noise.
- The debug artifact should be used during development and removed or restricted if diffs are sensitive.

## 9. Common Mistakes

- Posting too many low-value comments.
- Sending secrets, environment dumps, or generated files to an external service.
- Treating AI comments as mandatory approval without human review.
- Reviewing the same issue repeatedly without duplicate detection.
- Running on untrusted fork PRs without a security review.

## 10. Debugging Guide

- First run the workflow in read-only mode and upload `pr.diff`.
- Print the resolved PR number and changed file count.
- Exclude generated files, lock files, and large binaries.
- Deduplicate against existing PR comments before posting.
- Log response metadata, not sensitive request payloads.

## 11. Exercises

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Fetch and upload a PR diff. | `pr.diff` appears as an artifact. |
| Intermediate | Skip review when no PR exists. | Workflow exits successfully with a clear log. |
| Challenge | Post at most five comments from a local review script. | PR receives concise, non-duplicate comments. |

---

[Case Study Index](README.md) | [Course Home](../README.md)
