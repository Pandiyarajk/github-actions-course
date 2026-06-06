# Module 11: Essential Workflow Controls — Concurrency, Permissions, Defaults, and More

![Module](https://img.shields.io/badge/Module-11-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20A%20Components-1f6feb?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-120%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 10](./module-10-artifacts.md) | [Next: Module 12](./module-12-workflow-syntax.md)
> Level: **Intermediate** | Time: **120 min** | Example workflow: [`module-11-misc-features.yml`](../examples/module-11-misc-features.yml)

## Learning Objectives

- Prevent overlapping runs with `concurrency` (cancel or queue).
- Scope the token with `permissions` (least privilege).
- Set workflow-wide `defaults` for shell and working directory.
- Use `continue-on-error`, `if:` conditions, and `timeout-minutes`.
- Pass data between jobs with `needs` and job `outputs`.
- Control matrices with `fail-fast` and `max-parallel`, and gate deploys with `environment`.

## Key Concepts

`concurrency`, `permissions`, `defaults`, `continue-on-error`, `if:`, `needs`, job `outputs`, `fail-fast`, `max-parallel`, `environment`, `*.result`

## Expected Outcome

You can apply the production controls that keep workflows safe, predictable, and efficient.

## Concept Flow

```text
concurrency + permissions + defaults (workflow level)
   -> jobs with needs/outputs, matrix limits, if conditions
   -> environment gates -> always() summary
```

---

## ELI5 Explanation

These are the dials and safety switches of a workflow: a switch so two runs do not collide (`concurrency`), a lock so the workflow only gets the keys it needs (`permissions`), shared defaults so you stop repeating yourself (`defaults`), and rules for when jobs run, stop, or keep going.

## Technical Explanation

`concurrency` groups runs by a key; `cancel-in-progress: true` cancels the older run, `false` queues the new one. `permissions` sets the `GITHUB_TOKEN` scopes (workflow or job level); start with `contents: read` and widen only where needed. `defaults.run` sets a default `shell` and `working-directory`. `continue-on-error` lets a step fail without failing the job. `if:` controls execution with `success()`/`always()`/`failure()`/`cancelled()` or custom expressions. Jobs pass data through `outputs` consumed by downstream jobs via `needs.<job>.outputs.<key>`, and `needs.<job>.result` exposes the upstream status. Matrices accept `fail-fast` (stop all on first failure) and `max-parallel` (limit concurrency). `environment` ties a job to protection rules and approvals.

## Real-World Use Case

A nightly health-check workflow uses `concurrency: { group: health-check, cancel-in-progress: false }` so a new trigger queues instead of killing an in-progress run. A matrix runs browsers with `fail-fast: false` so one flaky browser does not stop the others, and a `publish` job runs only on `main` behind a `production` environment with approval.

## When To Use

- `concurrency`: long jobs, deploys, or health checks that must not overlap.
- `permissions`: every workflow (least privilege by default).
- `defaults`: repos that standardize on bash or a subdirectory.
- `needs`/outputs: passing computed values between jobs.
- `environment`: gated production deployments.

## When NOT To Use

- `cancel-in-progress: true` for jobs that must finish (e.g. a running deploy).
- Broad `permissions: write-all` when read is enough.
- `continue-on-error` on steps whose failure should stop the job.

## Common Mistakes

- Cancelling an in-progress deploy by setting `cancel-in-progress: true`.
- Forgetting that `success()` is implied — adding steps after a failure without `always()`.
- Using `needs` outputs without declaring them in the producer job's `outputs`.
- Granting `write-all` instead of the specific scope needed.
- Expecting a `summary` job to run after failures without `if: always()`.

## Feature Reference

| Feature | Purpose | Example |
| --- | --- | --- |
| `concurrency` | Avoid overlapping runs | `group: health-check`, `cancel-in-progress: false` |
| `permissions` | Scope `GITHUB_TOKEN` | `contents: read` |
| `defaults.run` | Default shell / dir | `shell: bash`, `working-directory: .` |
| `continue-on-error` | Step may fail safely | `continue-on-error: true` |
| `if:` | Conditional execution | `if: always()` |
| `needs` + `outputs` | Pass data between jobs | `needs.setup.outputs.run_label` |
| `fail-fast` | Stop matrix on first failure | `fail-fast: false` |
| `max-parallel` | Limit matrix concurrency | `max-parallel: 2` |
| `environment` | Deployment gates/approvals | `name: production` |
| `needs.<job>.result` | Upstream status | `success`, `failure`, `skipped` |

## Minimal Workflow Example

```yaml
name: Concurrency Basics

on: workflow_dispatch

permissions:
  contents: read

concurrency:
  group: health-check
  cancel-in-progress: false   # queue overlapping runs instead of cancelling

jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Run health check
        run: echo "python scripts/hello.py --tag healthcheck"
```

### YAML Explanation

- `permissions: contents: read` gives the token the minimum scope.
- `concurrency.group` names the lane; only one run per group runs at a time.
- `cancel-in-progress: false` queues a new run rather than cancelling the current one.

### Step-by-Step Execution

1. A run starts and holds the `health-check` concurrency group.
2. A second trigger waits in the queue (not cancelled).
3. When the first finishes, the queued run starts.

## Production Workflow Example

The full example chains a producer job, a controlled matrix, a gated publish job, and an always-run summary. See [`module-11-misc-features.yml`](../examples/module-11-misc-features.yml).

### Concurrency, Permissions, and Defaults

```yaml
permissions:
  contents: read

concurrency:
  group: health-check-${{ github.ref }}
  cancel-in-progress: false

defaults:
  run:
    shell: bash
    working-directory: .
```

### Job Outputs Consumed via `needs`

```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      run_label: ${{ steps.meta.outputs.run_label }}
      should_deploy: ${{ steps.meta.outputs.should_deploy }}
    steps:
      - id: meta
        run: |
          echo "run_label=bdd-${{ github.run_number }}" >> "$GITHUB_OUTPUT"
          echo "should_deploy=${{ github.ref_name == 'main' }}" >> "$GITHUB_OUTPUT"

  publish:
    needs: setup
    if: ${{ needs.setup.outputs.should_deploy == 'true' && success() }}
    runs-on: ubuntu-latest
```

### Matrix `fail-fast` and `max-parallel`

```yaml
strategy:
  fail-fast: false      # let all browsers finish even if one fails
  max-parallel: 2       # at most 2 matrix jobs at once
  matrix:
    browser: [chrome, firefox, msedge]
```

### Step `continue-on-error` and `timeout-minutes`

```yaml
- name: Behave (non-blocking)
  continue-on-error: true
  timeout-minutes: 15
  run: echo "behave --tags=smoke -D browser=${{ matrix.browser }}"
```

### Environment-Gated Job

```yaml
publish:
  environment:
    name: production
    url: https://prod.your-domain.com
  permissions:
    contents: write       # widen token only for this job
```

### Always-Run Summary Using `needs.<job>.result`

```yaml
summary:
  needs: [setup, test-matrix, publish]
  if: always()
  runs-on: ubuntu-latest
  steps:
    - run: |
        {
          echo "## Run Summary"
          echo "- Matrix result: ${{ needs.test-matrix.result }}"
          echo "- Publish result: ${{ needs.publish.result }}"
        } >> "$GITHUB_STEP_SUMMARY"
```

### Expected Output

- Overlapping runs queue instead of cancelling.
- The matrix runs at most two browsers at once and finishes all three.
- `publish` runs only on `main` and waits for production approval.
- `summary` always runs and reports each job's result.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a `concurrency` group with `cancel-in-progress: false`. | A second run queues behind the first. |
| Intermediate | Add a producer job output and consume it in a downstream job. | Downstream job reads the output value. |
| Challenge | Add a matrix with `fail-fast: false` + `max-parallel`, and an `if: always()` summary using `needs.<job>.result`. | All matrix entries run; summary reports results even on failure. |

---

[Previous: Module 10](./module-10-artifacts.md) | [Module Index](./README.md) | [Next: Module 12](./module-12-workflow-syntax.md)
