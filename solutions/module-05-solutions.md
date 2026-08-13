# Module 5 — Solutions

![Module](https://img.shields.io/badge/Module-5-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 5](../modules/module-05-runners.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** `cancel-in-progress: true` means exactly that: when a new run enters an
occupied `concurrency` group, the in-progress one is cancelled and the new one
proceeds. **A** describes `cancel-in-progress: false`, which queues instead — the
two settings are the whole decision, and picking the wrong one is how a
long-running regression suite gets killed by a trivial follow-up push. **C**
confuses identity with scheduling: separate `run_id` values are why the runs are
distinct, not why they would both be allowed to proceed. **D** is not a thing —
concurrency shapes execution, it never rejects a trigger.

**2 — C.** Every job is assigned its own runner and its own workspace. On
GitHub-hosted runners that is a freshly provisioned VM; even on self-hosted
runners it is a separate job with no guarantee of landing on the same machine.
`runs-on: ubuntu-latest` names an *image*, not a specific computer, so two jobs
sharing that label share nothing else. **A** and **D** invent filesystem
restrictions that do not exist. **B** is the tempting one, because `env` really
is workflow-scoped — but `env` shares *values* between jobs, never files. Use
`actions/upload-artifact@v7` / `actions/download-artifact@v8`, or a job output
for a small value.

**3 — B.** A runner executes one job per job slot. A single registration with one
slot serialises: one job runs, the rest sit queued until it finishes. **A** would
require multiple runner registrations (or multiple slots) on that machine. **C**
is wrong because a matching-but-busy runner queues the job rather than failing —
jobs only sit unrunnable when *no* runner carries the labels, and even then they
queue rather than error. **D** never happens: GitHub does not substitute a
different runner for the one you asked for.

**4.** The suite is picking up leftover state, because a self-hosted runner is a
persistent machine. The usual culprit is a browser or driver process from the
previous run that never exited — it holds the user-data directory and the driver
port, so the next run's session creation fails. A GitHub-hosted runner cannot
show this because its VM is destroyed after every job.

Two steps to add:

```yaml
      # 1. Clean stray processes BEFORE the suite, not after -- the previous run
      #    may have been cancelled and never reached its own teardown.
      - name: Kill stray browser processes
        shell: powershell
        run: |
          Get-Process chrome, chromedriver -ErrorAction SilentlyContinue |
            Stop-Process -Force -ErrorAction SilentlyContinue
          exit 0

      # 2. Tear down unconditionally, so a failed or cancelled suite still cleans up.
      - name: Clean up after the suite
        if: always()
        shell: powershell
        run: Remove-Item -Recurse -Force reports/tmp -ErrorAction SilentlyContinue
```

The pre-step matters more than the post-step: cleanup that only runs at the end
is skipped precisely when the run died badly, which is when it was needed.

**5.** They count three different things:

- `github.run_number` — how many times *this workflow* has been triggered in this
  repository. It increments per run and is shared by every attempt of that run.
- `github.run_attempt` — how many times *this run* has been started. It is `1`
  normally and increments on each re-run.
- `github.run_id` — a unique identifier for the run, stable across attempts.

For an artifact name that must stay unique across re-runs, `run_id` alone is not
enough, precisely because it does not change when you re-run. Combine it with the
attempt:

```yaml
          name: allure-${{ github.run_id }}-${{ github.run_attempt }}
```

## Lab 1 — Beginner

**Task:** Print `RUNNER_NAME`, `RUNNER_OS`, and `github.run_number`.

<details>
<summary>Show solution</summary>

```yaml
name: Runner Identity

on: workflow_dispatch

jobs:
  who-am-i:
    runs-on: ubuntu-latest
    steps:
      - name: Print runner identity
        run: |
          echo "Runner name : $RUNNER_NAME"
          echo "Runner OS   : $RUNNER_OS"
          echo "Run number  : ${{ github.run_number }}"
          echo "Run attempt : ${{ github.run_attempt }}"
          echo "Run ID      : ${{ github.run_id }}"
```

**Why this works.** `RUNNER_NAME` and `RUNNER_OS` are default environment
variables the runner agent sets, so they are read with shell syntax inside
`run:`. `github.run_number` is not an environment variable — it comes from the
`github` context and is interpolated by the expression `${{ }}` before the shell
ever sees the script. Mixing the two syntaxes in one block is normal and correct.

**Verify the failure mode the lab asks for.** Change `runs-on` to
`windows-latest` and re-run without touching the script. The output becomes:

```
Runner name :
Runner OS   :
Run number  : 7
```

The default shell on a Windows runner is PowerShell, where `$RUNNER_NAME` is an
undefined *PowerShell* variable that expands to nothing — while the `${{ }}` line
still works, because it was substituted before execution. The fix is
`$env:RUNNER_NAME`, or `shell: bash` to keep the script portable.

**Common wrong answer.** Writing `${{ env.RUNNER_NAME }}`. The default
environment variables GitHub sets are not exposed through the `env` context; the
expression resolves to an empty string with no error. In an expression, use
`${{ runner.name }}` and `${{ runner.os }}`; in a shell, use the environment
variables.

</details>

## Lab 2 — Intermediate

**Task:** Add a `concurrency` group and trigger the workflow twice quickly.

<details>
<summary>Show solution</summary>

```yaml
name: Serialized Runs

on: workflow_dispatch

# One lane per branch. Two triggers on the same branch share the group; triggers
# on different branches do not, so unrelated work is never blocked.
concurrency:
  group: runner-demo-${{ github.ref }}
  cancel-in-progress: false   # queue rather than cancel

jobs:
  slow:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Occupy the lane
        run: |
          echo "Run ${{ github.run_number }} starting on $RUNNER_NAME"
          sleep 60
          echo "Run ${{ github.run_number }} done"
```

**Why this works.** The `concurrency` group is a named lane, and `group` is an
expression so you choose the granularity. Including `github.ref` scopes the lane
per branch, which is what you almost always want — a repository-wide constant
string would serialise every branch against every other. With
`cancel-in-progress: false`, a second run entering an occupied lane waits for the
first to complete instead of displacing it.

**Verify the failure mode the lab asks for.** Dispatch the workflow twice within
a few seconds. The first run executes; the second appears immediately in the run
list but its job does not start — the run page shows it as pending, with a note
that it is waiting on the concurrency group rather than waiting for a runner.
When the first run's `sleep 60` finishes, the second starts.

Then flip to `cancel-in-progress: true` and repeat. The first run stops
mid-`sleep` and its conclusion becomes **Cancelled**, not Failed. Recognising
that distinction in the run list is the point of the exercise: a cancelled run
looks like an inexplicable abort until you know a concurrency group did it.

**Common wrong answer.** `group: ${{ github.workflow }}` with no ref. It looks
tidier and passes the two-trigger test, but it serialises the workflow across
every branch and every pull request at once, so one long nightly run blocks
everyone's PR checks. Scope the group to what actually conflicts.

</details>

## Lab 3 — Challenge

**Task:** Add a matrix over two runners and write a marker file; observe state on
a self-hosted runner.

<details>
<summary>Show solution</summary>

Compare your answer with the shipped example,
[`module-05-runners.yml`](../examples/module-05-runners.yml).

```yaml
name: Runners Across Machines

on: workflow_dispatch

jobs:
  across-runners:
    strategy:
      fail-fast: false      # one runner's failure must not hide the other's result
      matrix:
        target: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.target }}
    timeout-minutes: 10
    steps:
      - name: Identify this leg
        shell: bash          # forced, so one script works on both targets
        run: |
          echo "Target      : ${{ matrix.target }}"
          echo "Runner name : $RUNNER_NAME"
          echo "Runner OS   : $RUNNER_OS"

      - name: Detect and refresh the marker
        shell: bash
        run: |
          if [ -f marker.txt ]; then
            echo "marker.txt found -> persistent workspace (self-hosted)"
            cat marker.txt
          else
            echo "marker.txt absent -> fresh workspace (GitHub-hosted)"
          fi
          echo "written by run ${{ github.run_number }} on $RUNNER_NAME" > marker.txt
```

To see the persistent case, change the matrix to your own labels — e.g.
`target: [server1, server2]` — and run it twice.

**Why this works.** `runs-on: ${{ matrix.target }}` is evaluated per leg, so one
job definition fans out to two runners that execute in parallel and share
nothing. `fail-fast: false` keeps both legs running to completion, which matters
here because the whole point is comparing their output. `shell: bash` makes the
same script valid on the Windows leg, where the default would otherwise be
PowerShell and `$RUNNER_NAME` would silently expand to nothing.

**Verify the failure mode the lab asks for.** Run the hosted matrix twice. Both
legs report "marker.txt absent" every single time — the VM that wrote the file
was destroyed when the job ended. Now point the matrix at `server1`/`server2` and
run twice: the second run reports "marker.txt found" and prints the previous
run's number, because a self-hosted runner's workspace survives between jobs.
That surviving workspace is also the mechanism behind most "it only fails on
server2" bugs.

**Common wrong answer.** Expecting the `ubuntu-latest` leg to see the marker
written by the `windows-latest` leg, and concluding the matrix is broken when it
does not. Matrix legs are independent jobs on independent runners; there is no
shared filesystem and no ordering between them. If a leg genuinely needs data
from another, upload it with `actions/upload-artifact@v7` and download it in a
job that `needs:` the first.

The second common wrong answer is treating a persisted `marker.txt` as a feature
to depend on. Runner cleanup, a re-registration, or a second runner joining the
label all make it vanish. Persistence on a self-hosted runner is a hazard to
clean up for, not a cache to rely on.

</details>

---

[Solutions Index](./README.md) | [Module 5](../modules/module-05-runners.md) | [Course Home](../README.md)
