# Reference Cheat Sheet

### Common Triggers

```yaml
on:
  push:
  pull_request:
  workflow_dispatch:
  schedule:
    - cron: "0 2 * * *"
```

### Schedule Cron Examples

```yaml
on:
  schedule:
    - cron: "0 * * * *"      # hourly
    - cron: "0 2 * * *"      # daily
    - cron: "0 2 * * 1"      # weekly
    - cron: "0 2 1 * *"      # monthly
```

### Lifecycle and Review Triggers

```yaml
on:
  create:
  delete:
  pull_request:
    types: [opened, closed]
  pull_request_review_comment:
    types: [created]
  pull_request_review:
    types: [submitted]
```

### Folder-Scoped Triggers

```yaml
on:
  pull_request:
    paths:
      - "apps/web/**"
  push:
    branches:
      - main
    paths:
      - "apps/web/**"
```

### Self-Hosted Runner Selection

```yaml
jobs:
  qa:
    runs-on:
      - self-hosted
      - windows
      - qa-runner-1
```

### Checkout Depth Examples

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 1  # current commit only, fastest

  - uses: actions/checkout@v4
    with:
      fetch-depth: 2  # compare HEAD with HEAD~1

  - uses: actions/checkout@v4
    with:
      fetch-depth: 0  # full history for branch, tag, or merge-base comparisons
```

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      ref: ${{ inputs.target_ref }}
      fetch-depth: 0
```

### Run an Executable or Pip Package Command

```yaml
steps:
  - name: Run Windows executable
    shell: pwsh
    run: '& "C:\Tools\app-checker\app-checker.exe" --mode smoke --output reports'

  - name: Install and run Python CLI package
    run: |
      python -m pip install --upgrade pip
      python -m pip install generic-report-cli
      generic-report --suite regression --output reports/report.json
```

### Simple Workflow Summary

```yaml
steps:
  - name: Add summary
    if: always()
    run: |
      echo "## Run Summary" >> "$GITHUB_STEP_SUMMARY"
      echo "- Branch: ${{ github.ref_name }}" >> "$GITHUB_STEP_SUMMARY"
      echo "- Status: ${{ job.status }}" >> "$GITHUB_STEP_SUMMARY"
```

### Common Permissions

```yaml
permissions:
  contents: read
```

```yaml
permissions:
  contents: read
  packages: write
```

```yaml
permissions:
  contents: read
  id-token: write
```

### Useful Actions

| Purpose | Action |
| --- | --- |
| Checkout code | `actions/checkout@v4` |
| Setup Node | `actions/setup-node@v4` |
| Setup Python | `actions/setup-python@v5` |
| Setup .NET | `actions/setup-dotnet@v4` |
| Upload artifact | `actions/upload-artifact@v4` |
| Download artifact | `actions/download-artifact@v4` |
| Docker build | `docker/build-push-action@v6` |
| Docker login | `docker/login-action@v3` |
| Path filtering | `dorny/paths-filter@v3` |

### Production Workflow Checklist

- [ ] Workflow has a clear name.
- [ ] Trigger is intentional.
- [ ] Permissions are minimal.
- [ ] Secrets are not printed.
- [ ] Jobs have meaningful names.
- [ ] Deployment uses environments.
- [ ] Expensive jobs have timeouts.
- [ ] Deployments use concurrency.
- [ ] Reports upload with `if: always()`.
- [ ] Failure notifications are actionable.
- [ ] README or runbook explains rerun and rollback.

---

## Git Contribution Playbook

### Opening a Pull Request

1. Create a focused branch.
2. Add or update workflows.
3. Run local tests where possible.
4. Commit with a clear message.
5. Open a pull request.
6. Verify GitHub Actions checks.
7. Attach logs or screenshots if the change affects QA or deployment workflows.

```bash
git switch -c feature/add-docker-pipeline
git add .
git commit -m "feat: add docker build workflow"
git push -u origin feature/add-docker-pipeline
gh pr create --title "feat: add docker build workflow" --body "Adds Docker CI pipeline with GHCR publishing."
```

### Merging Safely

- Required checks are green.
- Security scans are reviewed.
- Deployment impact is understood.
- Secrets or permissions changes are reviewed carefully.
- Rollback plan exists for deployment changes.

If a merge causes a production issue, prefer `git revert` over rewriting shared history.

### Gathering Commit and PR Metadata

| Detail needed | Recommended command | Notes |
| --- | --- | --- |
| Branch source/target | `gh pr view <number> --json headRefName,baseRefName` | Works after merge for audit trails. |
| Commit message and body | `git show -s <sha>` | Add `--pretty=format:` to control fields. |
| PR description | `gh pr view <number> --json body --jq '.body'` | Useful for release notes. |
| Conflict files | `git diff --name-only --diff-filter=U` | Run after merge or rebase conflicts. |
| Files modified and stats | `git show <sha> --stat --name-status` | Includes additions and deletions. |
| Contributors per release | `git shortlog -sne <prev-tag>..<new-tag>` | Helps populate changelog contributors. |

---

[Reference Index](./README.md) | [Course Home](../README.md)
