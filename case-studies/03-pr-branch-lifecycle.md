# Pull Request and Branch Lifecycle Automation

![Case Study](https://img.shields.io/badge/Case%20Study-3-1f6feb?style=flat-square) ![Difficulty](https://img.shields.io/badge/Difficulty-%E2%98%85%E2%98%85-cf222e?style=flat-square) ![Level](https://img.shields.io/badge/Level-Advanced-cf222e?style=flat-square) [![Case Studies](https://img.shields.io/badge/%E2%AC%85%20Case%20Studies-555?style=flat-square)](README.md)

> Level: **Advanced** | Suggested modules: **Module 3, Module 19**

## 1. Title

Pull Request and Branch Lifecycle Automation for `api-service`

## 2. What This Workflow Does

This case study teaches how to respond to branch creation, branch deletion, pull request creation, pull request merge, commit pushes, and ref-to-ref comparison reports. It generalizes event-driven automation into safe governance patterns.

Real-world scenario: a team wants consistent branch naming, issue tracking, changed-file reporting, and PR lifecycle notifications without exposing internal tools.

## 3. When to Use This

- Use it when branch names follow an issue-key convention.
- Use it when PR open and merge events should trigger automation.
- Use it when commit messages should be attached to an external tracker.
- Use it when reviewers need changed-file or comparison reports.

## 4. Workflow Breakdown

- **Trigger (`on`)**: Uses `create`, `delete`, `push`, `pull_request`, and `workflow_dispatch` depending on the lifecycle event.
- **Jobs**: Separate event processing from report generation when workflows grow.
- **Steps**: Detect event type, validate branch name, checkout code, compare refs, post or upload reports.
- **Actions used**: `actions/checkout`, `actions/setup-python`, `actions/upload-artifact`.
- **Conditions**: Merge-only logic checks `github.event.pull_request.merged == true`.
- **Outputs**: Branch metadata, changed-file reports, comparison reports, and generic tracker updates.

## 5. ASCII Flow Diagram

```text
Branch / PR / Push Event
   |
   v
Detect Event Type
   |
   v
Validate Branch Name
   |
   +--> Create or Delete Branch Action
   +--> PR Open or Merge Action
   +--> Commit Metadata Action
   +--> Comparison Report
   |
   v
Upload Evidence or Notify Generic Tracker
```

## 6. Simple Version YAML

```yaml
name: Branch Event Logger

on:
  - create
  - delete

jobs:
  log:
    runs-on: ubuntu-latest
    steps:
      - name: Print event details
        run: |
          echo "Event: ${{ github.event_name }}"
          echo "Ref type: ${{ github.event.ref_type }}"
          echo "Ref: ${{ github.event.ref }}"
```

## 7. Production Version YAML

Different events expose the branch/ref under different context variables, which is why the workflow below reads `github.head_ref || github.ref_name || github.event.ref` — it takes the first one that is set for the current event:

| Event | Where the ref is | Example value |
| --- | --- | --- |
| `pull_request` | `github.head_ref` | the PR's source branch |
| `push` | `github.ref_name` | the pushed branch |
| `create` / `delete` | `github.event.ref` | the created/deleted branch or tag |

```yaml
name: Generic Lifecycle Automation

on:
  create:
  delete:
  push:
    branches:
      - "**"
  pull_request:
    types:
      - opened
      - closed
    branches:
      - main
  workflow_dispatch:
    inputs:
      base_ref:
        default: main
      target_ref:
        required: false

permissions:
  contents: read
  pull-requests: read

jobs:
  lifecycle:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Resolve branch context
        id: context
        shell: bash
        run: |
          ref_name="${{ github.head_ref || github.ref_name || github.event.ref }}"
          issue_key=$(echo "$ref_name" | grep -oE 'ISSUE-[0-9]+' || true)
          echo "ref_name=$ref_name" >> $GITHUB_OUTPUT
          echo "issue_key=$issue_key" >> $GITHUB_OUTPUT

      - name: Checkout repository
        if: github.event_name == 'pull_request' || github.event_name == 'workflow_dispatch'
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Collect merged PR changed files
        if: github.event_name == 'pull_request' && github.event.action == 'closed' && github.event.pull_request.merged == true
        run: |
          git diff --name-status ${{ github.event.pull_request.base.sha }} ${{ github.event.pull_request.head.sha }} > changed-files.txt
          cat changed-files.txt

      - name: Generate comparison report
        if: github.event_name == 'workflow_dispatch'
        run: |
          base="${{ inputs.base_ref }}"
          target="${{ inputs.target_ref || github.ref_name }}"
          python scripts/compare_refs.py "$base" "$target" > comparison-report.md

      - name: Send generic lifecycle update
        if: steps.context.outputs.issue_key != ''
        env:
          API_TOKEN: ${{ secrets.API_TOKEN }}
        run: |
          echo "Send lifecycle update for ${{ steps.context.outputs.issue_key }} to https://example.com/api/events"

      - name: Upload lifecycle evidence
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: lifecycle-evidence
          path: |
            changed-files.txt
            comparison-report.md
          if-no-files-found: ignore
```

## 8. Line-by-Line Explanation

- Multiple triggers show that lifecycle automation is event-driven.
- `github.head_ref`, `github.ref_name`, and `github.event.ref` are used because different events expose refs differently.
- The issue key is generic: `ISSUE-123`.
- Checkout runs only when file history is needed.
- Merged PR logic is guarded by both `closed` and `merged == true`.
- Comparison reporting is manual because reviewers often need control over base and target refs.
- External integration uses only `https://example.com` and `API_TOKEN`.
- Artifacts preserve changed-file and comparison evidence.

## 9. Checkout Depth and Summary Examples

Comparison and changed-file workflows often need more Git history than the default checkout. `actions/checkout` fetches only one commit by default, which is fast but not enough for comparing branches, merge bases, or older commits.

### Checkout Depth Options

```yaml
steps:
  - name: Fast checkout for current commit only
    uses: actions/checkout@v6
    with:
      fetch-depth: 1

  - name: Checkout enough history for HEAD~1 comparisons
    uses: actions/checkout@v6
    with:
      fetch-depth: 2

  - name: Checkout full history for branch or tag comparisons
    uses: actions/checkout@v6
    with:
      fetch-depth: 0
```

Use `fetch-depth: 1` for simple build and test jobs. Use `fetch-depth: 2` when a job compares the latest commit with the previous commit. Use `fetch-depth: 0` when a job needs full branch history, tags, merge-base logic, or comparisons between user-selected refs.

### Generic Ref Comparison With Full History

```yaml
name: Generic Comparison Report

on:
  pull_request:
    types:
      - opened
  workflow_dispatch:
    inputs:
      base_ref:
        description: "Base branch or commit"
        required: true
        default: main
      target_ref:
        description: "Target branch or commit"
        required: true
      include_details:
        description: "Include detailed changes"
        type: boolean
        default: false

permissions:
  contents: read

jobs:
  compare-refs:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout full repository history
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Resolve comparison refs
        id: refs
        run: |
          echo "base=${{ github.event_name == 'workflow_dispatch' && inputs.base_ref || github.base_ref }}" >> "$GITHUB_OUTPUT"
          echo "target=${{ github.event_name == 'workflow_dispatch' && inputs.target_ref || github.head_ref }}" >> "$GITHUB_OUTPUT"

      - name: Run comparison command
        run: |
          generic-compare \
            "${{ steps.refs.outputs.base }}" \
            "${{ steps.refs.outputs.target }}" \
            --repo-path "${{ github.workspace }}" \
            ${{ github.event_name == 'workflow_dispatch' && inputs.include_details && '--details' || '' }} \
            > comparison-report.md
          echo "Report saved to comparison-report.md"
```

The full checkout lets the script compare refs reliably even when the base and target are not both present in a shallow clone.

### Checkout a Specific Ref

```yaml
steps:
  - name: Checkout pull request source branch
    uses: actions/checkout@v6
    with:
      ref: ${{ github.head_ref }}
      fetch-depth: 0

  - name: Checkout manually selected ref
    uses: actions/checkout@v6
    with:
      ref: ${{ inputs.target_ref }}
      fetch-depth: 0
```

Use `ref` when the workflow must run against a PR source branch, release branch, tag, or manually selected branch instead of the default checkout ref.

### Add a Simple Workflow Summary

```yaml
steps:
  - name: Write workflow summary
    if: always()
    run: |
      {
        echo "## Comparison Summary"
        echo ""
        echo "- Base ref: ${{ steps.refs.outputs.base }}"
        echo "- Target ref: ${{ steps.refs.outputs.target }}"
        echo "- Status: ${{ job.status }}"
        echo ""
        echo "### Report"
        cat comparison-report.md
      } >> "$GITHUB_STEP_SUMMARY"
```

`$GITHUB_STEP_SUMMARY` writes Markdown to the run summary page, which is easier for reviewers to scan than raw logs.

## 10. Event-Specific Examples

Use these generic examples when you want one small workflow per lifecycle event instead of one larger combined workflow.

### On PR Create

```yaml
name: On PR Created

on:
  pull_request:
    types:
      - opened
    branches:
      - main

permissions:
  contents: read
  pull-requests: read

jobs:
  pr-created:
    runs-on: ubuntu-latest
    steps:
      - name: Print PR context
        run: |
          echo "PR #${{ github.event.pull_request.number }}"
          echo "Source: ${{ github.event.pull_request.head.ref }}"
          echo "Target: ${{ github.event.pull_request.base.ref }}"
```

### On PR Merge

```yaml
name: On PR Merged

on:
  pull_request:
    types:
      - closed
    branches:
      - main

permissions:
  contents: read
  pull-requests: read

jobs:
  pr-merged:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: List files merged by the PR
        run: |
          git diff --name-status \
            ${{ github.event.pull_request.base.sha }} \
            ${{ github.event.pull_request.head.sha }}
```

### On Branch Create

```yaml
name: On Branch Created

on:
  create:

jobs:
  branch-created:
    if: github.event.ref_type == 'branch'
    runs-on: ubuntu-latest
    steps:
      - name: Handle new branch
        run: |
          echo "Branch created: ${{ github.event.ref }}"
          echo "Created by: ${{ github.actor }}"
```

### On Branch Delete

```yaml
name: On Branch Deleted

on:
  delete:

jobs:
  branch-deleted:
    if: github.event.ref_type == 'branch'
    runs-on: ubuntu-latest
    steps:
      - name: Handle deleted branch
        run: |
          echo "Branch deleted: ${{ github.event.ref }}"
          echo "Deleted by: ${{ github.actor }}"
```

### On Review Comment Trigger

```yaml
name: On Inline Review Comment

on:
  pull_request_review_comment:
    types:
      - created

permissions:
  contents: read
  pull-requests: read

jobs:
  review-comment:
    runs-on: ubuntu-latest
    steps:
      - name: Print review comment context
        run: |
          echo "PR #${{ github.event.pull_request.number }}"
          echo "Comment path: ${{ github.event.comment.path }}"
          echo "Comment author: ${{ github.event.comment.user.login }}"
```

This event is for inline code review comments, not regular issue-style comments on the PR conversation tab.

### On Review Submit

```yaml
name: On Review Submitted

on:
  pull_request_review:
    types:
      - submitted

permissions:
  contents: read
  pull-requests: read

jobs:
  review-submitted:
    runs-on: ubuntu-latest
    steps:
      - name: Print review decision
        run: |
          echo "PR #${{ github.event.pull_request.number }}"
          echo "Review state: ${{ github.event.review.state }}"
          echo "Reviewer: ${{ github.event.review.user.login }}"
```

Review states include values such as `approved`, `changes_requested`, and `commented`.

### Pull and Push Events for a Specific Folder

```yaml
name: Folder Scoped CI

on:
  pull_request:
    branches:
      - main
    paths:
      - "apps/web/**"
      - ".github/workflows/web-ci.yml"
  push:
    branches:
      - main
    paths:
      - "apps/web/**"

jobs:
  web-ci:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
      - name: Run folder-specific checks
        run: echo "Run checks for apps/web"
```

For pull requests, the workflow runs when the proposed change touches the folder. For pushes, it runs when committed changes on the selected branch touch the folder.

## 11. Common Mistakes

- Assuming `github.ref_name` works the same for every event.
- Treating every closed PR as merged.
- Hardcoding internal issue prefixes.
- Sending external updates for bot-created branches.
- Running full checkout on events that only need metadata.
- Using `pull_request_review_comment` when you actually need PR conversation comments.
- Using shallow checkout for branch-to-branch comparisons that need full history.

## 12. Debugging Guide

- Print `github.event_name`, `github.event.action`, `github.ref_name`, `github.head_ref`, and `github.base_ref`.
- Use manual dispatch to test diff behavior safely.
- Upload reports before adding notifications.
- Validate branch naming rules in documentation.
- Use generic tracker payloads until the workflow is stable.

## 13. Exercises

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Log branch create and delete events. | Workflow prints event and ref details. |
| Intermediate | Validate branch names using `ISSUE-[0-9]+`. | Invalid branches skip tracker updates. |
| Challenge | Generate a changed-file or comparison report for merged PRs. | Report uploads as an artifact. |

---

[Case Study Index](README.md) | [Course Home](../README.md)
