# 📋 Reference Cheat Sheet

![Section](https://img.shields.io/badge/Section-Cheat%20Sheet-8957e5?style=flat-square) ![Use](https://img.shields.io/badge/Use-Quick%20Reference-1f6feb?style=flat-square) [![Reference Library](https://img.shields.io/badge/⬅%20Reference-555?style=flat-square)](README.md) [![Course Home](https://img.shields.io/badge/⬅%20Course%20Home-555?style=flat-square)](../README.md)

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
  - uses: actions/checkout@v7
    with:
      fetch-depth: 1  # current commit only, fastest

  - uses: actions/checkout@v7
    with:
      fetch-depth: 2  # compare HEAD with HEAD~1

  - uses: actions/checkout@v7
    with:
      fetch-depth: 0  # full history for branch, tag, or merge-base comparisons
```

```yaml
steps:
  - uses: actions/checkout@v7
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
| Checkout code | `actions/checkout@v7` |
| Setup Python | `actions/setup-python@v7` |
| Cache pip packages | `actions/cache@v6` |
| Upload artifact | `actions/upload-artifact@v7` |
| Download artifact | `actions/download-artifact@v8` |
| Docker build | `docker/build-push-action@v7` |
| Docker login | `docker/login-action@v4` |
| Docker buildx setup | `docker/setup-buildx-action@v4` |
| Docker image tags/labels | `docker/metadata-action@v6` |
| GitHub API from a workflow | `actions/github-script@v9` |
| Path filtering | `dorny/paths-filter@v3` |

> [!NOTE]
> First-party `actions/*` are **independently versioned** — their current majors
> span five numbers — so there is no shared "generation" to track. Verify each
> against `https://github.com/<owner>/<repo>/releases/latest`; the enforced table
> lives in `PINNED_ACTIONS` in [`scripts/validate_course.py`](../scripts/validate_course.py).

### Contexts

Available expression contexts, and the ones people reach for that do not exist.

| Context | Holds | Notable |
| --- | --- | --- |
| `github.*` | Event and repository metadata | `github.event.*` is **attacker-controlled** — never interpolate into `run:` |
| `env.*` | Environment variables in scope | Workflow → job → step, narrowest wins |
| `vars.*` | Repository/org/environment variables | Non-sensitive configuration |
| `secrets.*` | Secrets in scope | Not available in a job-level `if:` |
| `job.*` | The current job | `job.status`, `job.container`, `job.services` |
| `jobs.*` | Reusable-workflow job results | Only inside `on.workflow_call.outputs` |
| `steps.*` | Completed steps in this job | Requires the step to have an `id:` |
| `needs.*` | Upstream job outputs and results | `needs.<id>.result`, `needs.<id>.outputs.*` |
| `runner.*` | The runner | `runner.os`, `runner.arch`, `runner.temp` |
| `strategy.*` | Matrix strategy | `strategy.job-index`, `strategy.fail-fast` |
| `matrix.*` | Current matrix leg | Only inside a job with a `strategy.matrix` |
| `inputs.*` | `workflow_dispatch` / `workflow_call` inputs | Typed for `workflow_call`, strings otherwise |

Commonly-assumed properties that **do not exist** — each evaluates to an empty
string rather than erroring, which is why they fail silently:

| Wrong | Right |
| --- | --- |
| `github.default_branch` | `github.event.repository.default_branch` |
| `github.branch` | `github.ref_name` |
| `github.pr_number` | `github.event.pull_request.number` |
| `steps.<id>.output` | `steps.<id>.outputs.<name>` |
| `secrets.*` in a job-level `if:` | Set an output in an earlier job, gate on that |

All context values are **strings**. `if: steps.x.outputs.flag` is truthy even
when the value is the string `"false"` — compare with `== 'true'`.

### Runner Cost and Minute Multipliers

| Runner | Multiplier | Notes |
| --- | --- | --- |
| Linux (`ubuntu-*`) | 1× | Baseline |
| Windows (`windows-*`) | 2× | Same wall-clock time costs twice as much |
| macOS (`macos-*`) | 10× | Reserve for genuinely Apple-only work |
| Self-hosted | 0× | Consumes no billed minutes; you own the machine |

- Minutes are rounded up **per job**, not per workflow. Twelve 15-second jobs
  bill as 12 minutes, not 3.
- The default job timeout is **360 minutes** — one hung job bills six hours.
  Set `timeout-minutes` on every job.
- `concurrency` with `cancel-in-progress: true` stops paying for superseded runs.
- A matrix multiplies everything: 3 browsers × 4 servers is 12 billed jobs.
- Artifact storage is billed separately; `retention-days` defaults to 90.

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
