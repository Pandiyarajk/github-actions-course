# Module 11: Essential Workflow Controls — Concurrency, Permissions, Defaults, and More

![Module](https://img.shields.io/badge/Module-11-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20A%20Components-1f6feb?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-120%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 10](./module-10-artifacts.md) | [Next: Module 12](./module-12-workflow-syntax.md)
> Level: **Intermediate** | Time: **120 min** | Example workflow: [`module-11-misc-features.yml`](../examples/module-11-misc-features.yml)
> Solutions: [`module-11-solutions.md`](../solutions/module-11-solutions.md)

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

## Debugging Tips

- A run stuck in *Pending* with no runner message is usually waiting on its `concurrency` group — open the other run holding the group.
- A job that "never runs" is almost always **skipped**, not failed: check its `if:` and remember that `success()` is implied through `needs`.
- An empty `needs.<job>.outputs.<key>` means the producing job did not declare the value in its `outputs:` block, or its step is missing an `id:`.
- Echo boolean-looking outputs before comparing them; they are strings, so `== 'true'` is the only reliable test.
- A resource-not-accessible error from an API call is a `permissions` problem — widen the specific scope on that job, not the whole workflow.
- Add an `if: always()` summary step that prints every `needs.<job>.result` value; it makes skip-versus-fail obvious on the run page.

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

## Quiz

1. A deploy workflow must never be interrupted mid-deploy, but overlapping triggers must not run at the same time either. Which `concurrency` block is correct?
   - **A.** `group: deploy` with `cancel-in-progress: true`.
   - **B.** `group: deploy` with `cancel-in-progress: false`.
   - **C.** No `concurrency` block — GitHub already serialises deploys.
   - **D.** `group: ${{ github.run_id }}` with `cancel-in-progress: true`.

2. A `summary` job has `needs: [lint, test]` and no `if:`. The `test` job fails. What does `summary` do?
   - **A.** It runs and reports the failure, because `needs` only controls ordering.
   - **B.** It is skipped, because `success()` is implied on every job and step.
   - **C.** It fails immediately with a dependency error.
   - **D.** It runs, but `needs.test.result` is empty.

3. A producer job sets `should_deploy` to the value of `github.ref_name == 'main'`. The consumer writes `if: needs.setup.outputs.should_deploy`. On a feature branch the consumer job still runs. Why?
   - **A.** `needs` outputs are only readable inside steps, so the job-level `if:` is ignored.
   - **B.** The output is the string `"false"`, and any non-empty string is truthy in an Actions expression.
   - **C.** `github.ref_name` returns `refs/heads/<branch>`, so the comparison produced `true`.
   - **D.** Job-level `if:` requires the `${{ }}` wrapper to be evaluated at all.

4. A downstream job reads `needs.setup.outputs.run_label` and gets an empty string, with no error anywhere in the logs. Describe the two-hop wiring a job output requires and which hop is usually missing.

5. A Behave matrix runs `chrome`, `firefox`, and `msedge` on self-hosted runners labelled `server1`–`server4`, only two of which are free during the day. Explain what `fail-fast` and `max-parallel` each control, and give the values you would set here.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a `concurrency` group with `cancel-in-progress: false`. | A second run queues behind the first. |
| Intermediate | Add a producer job output and consume it in a downstream job. | Downstream job reads the output value. |
| Challenge | Add a matrix with `fail-fast: false` + `max-parallel`, and an `if: always()` summary using `needs.<job>.result`. | All matrix entries run; summary reports results even on failure. |

Solutions: [`solutions/module-11-solutions.md`](../solutions/module-11-solutions.md)

---

[Previous: Module 10](./module-10-artifacts.md) | [Module Index](./README.md) | [Next: Module 12](./module-12-workflow-syntax.md)
