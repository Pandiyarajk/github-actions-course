# Module 5: Runners — What They Are and How Concurrent Runs Behave

![Module](https://img.shields.io/badge/Module-5-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20A%20Components-1f6feb?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-120%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 4](./module-04-scheduled-workflows.md) | [Next: Module 6](./module-06-runner-setup.md)
> Level: **Intermediate** | Time: **120 min** | Example workflow: [`module-05-runners.yml`](../examples/module-05-runners.yml)
> Solutions: [`module-05-solutions.md`](../solutions/module-05-solutions.md)

## Learning Objectives

- Explain what a runner is and the difference between GitHub-hosted and self-hosted.
- Understand what happens when the same workflow is triggered multiple times.
- Understand how the same job behaves across different runners.
- Use `concurrency` to queue or cancel overlapping runs.
- Reason about runner state, isolation, and parallelism.

## Key Concepts

runner, GitHub-hosted, self-hosted, runner labels, `RUNNER_NAME`/`RUNNER_OS`, queueing, parallelism, `concurrency`, workspace state

## Expected Outcome

You can choose the right runner, predict how multiple and parallel runs behave, and control overlap safely.

## Concept Flow

```text
Trigger -> Job needs a runner -> Scheduler finds a free runner matching runs-on -> Job executes -> Runner freed
```

---

## ELI5 Explanation

A runner is the worker computer that actually does the job. GitHub can lend you a brand-new computer for each job (GitHub-hosted), or you can plug in your own computer and label it (self-hosted). If you ask for work many times, the workers either grab jobs in parallel (if enough are free) or line up and take turns.

## Technical Explanation

A **runner** is a machine with the GitHub Actions runner agent installed. **GitHub-hosted** runners (`ubuntu-latest`, `windows-latest`, `macos-latest`) are fresh, isolated VMs created per job and destroyed after — no state carries over. **Self-hosted** runners are machines you register and select by labels (e.g. `server1`); they persist state between runs unless you clean it, and they can access private networks, licensed tools, and special hardware. `runs-on` matches a job to a runner by label.

When the **same workflow is triggered multiple times**, each trigger creates a separate run with its own `run_id` and incrementing `run_number`. Independent runs execute in parallel if enough runners are free; if not, they queue. A single self-hosted runner with one job slot executes one job at a time, so extra jobs wait. `concurrency` lets you cap this explicitly: runs in the same `group` either queue (`cancel-in-progress: false`) or cancel the older run (`cancel-in-progress: true`).

Across **different runners**, each runner is isolated: jobs do not share a filesystem, environment, or processes. Matrix jobs fan the same definition out to multiple runners that run in parallel and independently.

## Real-World Use Case

A web smoke suite runs on GitHub-hosted `ubuntu-latest` (clean every time), while a desktop/UI regression runs on a self-hosted Windows `server1` that has licensed tooling and keeps a working copy between runs. Triggering the regression twice on the same server queues the second run; triggering it on `server1` and `server2` runs both in parallel on different machines.

## When To Use

- **GitHub-hosted**: standard Linux/Windows jobs needing a clean environment.
- **Self-hosted**: licensed software, private network, browsers/hardware, long suites.
- **`concurrency`**: serialize runs that must not overlap on the same machine.
- **Matrix across runners**: run the same suite on several OSes/servers at once.

## When NOT To Use

- Self-hosted runners for untrusted fork PRs (security risk).
- One broad `self-hosted` label for every machine (no targeting).
- Relying on leftover files on a GitHub-hosted runner (it is wiped each job).

## Common Mistakes

- Assuming a self-hosted runner is clean — stale files/processes leak between runs.
- Expecting two jobs to share files just because they ran on the "same" label.
- Forgetting that one self-hosted runner with one slot serializes jobs.
- Cancelling an in-progress run by mis-setting `cancel-in-progress: true`.
- Not cleaning browser/test processes before a self-hosted run.

## Debugging Tips

- A job stuck on "Waiting for a runner to pick up this job" is almost always a label problem or a busy runner, not a YAML problem. Check **Settings > Actions > Runners** for a runner that is Idle *and* carries every label in `runs-on`.
- Print `$RUNNER_NAME` as the first step of every self-hosted job. When one machine in a pool misbehaves, the logs already tell you which one.
- Suspect leftover state before suspecting the test. `ls -la` (or `Get-ChildItem`) the workspace at the start of a self-hosted job; files from the previous run are the usual cause of a suite that only fails on one server.
- If a run vanished without a failure, look for "Canceled" rather than "Failed" — a newer run in the same `concurrency` group with `cancel-in-progress: true` cancels the older one, and the cancellation reads as a mysterious abort.
- Two jobs that "should" share files never do. Confirm by echoing `$RUNNER_NAME` in both: different names prove different machines, and a matching name still means a separate job with its own workspace lifecycle.
- Stale processes hold file locks. On a self-hosted Windows runner, `Get-Process chromedriver, chrome -ErrorAction SilentlyContinue` before the suite tells you whether the previous run really exited.

## Runner Reference

| Aspect | GitHub-hosted | Self-hosted |
| --- | --- | --- |
| Provisioned | Fresh VM per job | Your persistent machine |
| `runs-on` | `ubuntu-latest`, `windows-latest` | label(s): `server1` … `server4` |
| State between runs | None (wiped) | Persists unless cleaned |
| Network/tools | Public, standard images | Private network, licensed tools |
| Best for | Lint, unit, smoke | Long regression, UI, hardware |

### What happens on repeated / parallel triggers

| Situation | Behavior |
| --- | --- |
| Same workflow triggered twice, runners free | Both runs execute in parallel (separate `run_id`) |
| Same workflow, only one runner/slot free | Second run queues until a slot frees |
| Same `concurrency` group, `cancel-in-progress: false` | New run queues behind the current one |
| Same `concurrency` group, `cancel-in-progress: true` | Older run is cancelled, newer runs |
| Matrix over `[server1, server2]` | Same job runs in parallel on two machines |

## Minimal Workflow Example

```yaml
name: Runner Basics

on: workflow_dispatch

jobs:
  who:
    runs-on: ubuntu-latest
    steps:
      - name: Show runner
        run: |
          echo "Runner name: $RUNNER_NAME"
          echo "Runner OS:   $RUNNER_OS"
          echo "Run number:  ${{ github.run_number }}"
```

### YAML Explanation

- `runs-on: ubuntu-latest` requests a GitHub-hosted Linux runner.
- `RUNNER_NAME`/`RUNNER_OS` identify the machine that picked up the job.
- `github.run_number` increases each time the workflow is triggered.

### Step-by-Step Execution

1. The trigger creates a run and requests a runner.
2. A free `ubuntu-latest` VM picks up the job.
3. The step prints the runner identity and run number.

## Production Workflow Example

The full example shows runner identity, persistent vs fresh workspace, a serialized concurrency lane, and a matrix across runners. See [`module-05-runners.yml`](../examples/module-05-runners.yml).

### Selecting a Runner at Run Time

```yaml
run-name: Runners - ${{ inputs.runner || 'ubuntu-latest' }} | run ${{ github.run_number }}

concurrency:
  group: runner-demo-${{ inputs.runner || 'ubuntu-latest' }}
  cancel-in-progress: false   # queue repeated triggers per runner

jobs:
  who-am-i:
    runs-on: ${{ inputs.runner || 'ubuntu-latest' }}
```

### Runner Identity and Run Counters

```yaml
- name: Print runner identity
  run: |
    echo "Runner name : $RUNNER_NAME"
    echo "Run number  : ${{ github.run_number }}"   # increments per trigger
    echo "Run attempt : ${{ github.run_attempt }}"  # increments on re-run
    echo "Run ID      : ${{ github.run_id }}"        # unique per run
```

### Fresh vs Persistent Workspace

```yaml
- name: Demonstrate workspace state
  run: |
    if [ -f marker.txt ]; then
      echo "marker.txt exists -> persistent (self-hosted) runner"
    else
      echo "marker.txt not found -> fresh workspace (GitHub-hosted)"
    fi
    echo "created by run ${{ github.run_number }}" > marker.txt
```

On a GitHub-hosted runner `marker.txt` is never found (fresh VM); on a self-hosted runner it may persist between runs.

### Same Job Across Different Runners

```yaml
across-runners:
  strategy:
    fail-fast: false
    matrix:
      target: [ubuntu-latest, windows-latest]
  runs-on: ${{ matrix.target }}
  steps:
    - run: echo "Ran on ${{ matrix.target }} ($RUNNER_OS) — runners are isolated"
```

Each matrix copy runs on its own runner in parallel and shares nothing with the others.

### Expected Output

- The job prints which runner executed it and the run number.
- Repeated triggers in the same concurrency group queue rather than overlap.
- The matrix runs the same job on Ubuntu and Windows simultaneously.
- A self-hosted runner may show a persisted `marker.txt`; a hosted one never does.

## Quiz

1. Two pushes land 10 seconds apart on a workflow with `concurrency: { group: deploy, cancel-in-progress: true }`. What happens to the first run?
   - **A.** It finishes, and the second run queues behind it.
   - **B.** It is cancelled, and the second run proceeds.
   - **C.** Both run in parallel because they have different `run_id` values.
   - **D.** The second push is rejected with a concurrency error.

2. A job writes `reports/summary.txt` on `ubuntu-latest`. A later job in the same workflow, also `runs-on: ubuntu-latest`, cannot find the file. Why?
   - **A.** The file needs `chmod +x` before another job can read it.
   - **B.** Workflow-level `env` was not set, so the path resolved differently.
   - **C.** Each job gets its own fresh runner and workspace; use an artifact or a job output to move data between jobs.
   - **D.** `ubuntu-latest` is read-only outside `$GITHUB_WORKSPACE`.

3. Four jobs target `runs-on: server1`, where a single self-hosted runner is registered with one job slot. What is the observed behaviour?
   - **A.** All four run in parallel on the one machine.
   - **B.** They execute one at a time; the other three stay queued until a slot frees.
   - **C.** Three fail immediately with "no runner available".
   - **D.** GitHub silently falls back to `ubuntu-latest` for the extra three.

4. A BDD suite passes on GitHub-hosted `ubuntu-latest` but intermittently fails on self-hosted `server2` with browser sessions that will not start. Explain the most likely cause in terms of runner lifecycle, and name two steps you would add to the job.

5. `github.run_number`, `github.run_attempt`, and `github.run_id` all identify a run. Explain what each one counts, and say which of them is safe to use as a unique key for naming an artifact across re-runs.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Print `RUNNER_NAME`, `RUNNER_OS`, and `github.run_number`. | Logs show runner identity and run number. |
| Intermediate | Add a `concurrency` group and trigger the workflow twice quickly. | Second run queues behind the first. |
| Challenge | Add a matrix over two runners and write a marker file; observe state on a self-hosted runner. | Parallel runs on both runners; marker persists only on self-hosted. |

Solutions: [`solutions/module-05-solutions.md`](../solutions/module-05-solutions.md)

---

[Previous: Module 4](./module-04-scheduled-workflows.md) | [Module Index](./README.md) | [Next: Module 6](./module-06-runner-setup.md)
