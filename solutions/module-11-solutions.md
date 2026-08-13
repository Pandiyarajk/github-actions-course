# Module 11 — Solutions

![Module](https://img.shields.io/badge/Module-11-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 11](../modules/module-11-misc-features.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** A `concurrency` group serialises everything sharing the key;
`cancel-in-progress: false` makes a new run **queue** behind the running one
instead of killing it. **A** is the classic production incident: it is the right
setting for CI on a busy pull request, where superseded runs are waste, and the
wrong setting for a deploy, where cancelling mid-flight leaves the target
half-updated. **C** is false — without a `concurrency` block, runs execute in
parallel with no coordination at all. **D** keys the group by `github.run_id`,
which is unique per run, so every run gets its own group and nothing is ever
serialised.

**2 — B.** `success()` is the implied condition on every job and step, so a
downstream job whose dependency failed is **skipped**. This is why reporting jobs
need `if: always()` — the one job you most want after a failure is the one that is
skipped by default. **A** confuses `needs` with a pure ordering primitive; it
encodes both ordering *and* a success requirement. **C** is wrong: a skipped job
is not an error. **D** is wrong twice over — the job does not run, and when it
does run under `if: always()`, `needs.test.result` is populated with `failure`.

**3 — B.** Every job and step output is a **string**. `should_deploy` is the
string `"false"` on a feature branch, and a non-empty string is truthy in a
GitHub Actions expression, so the condition passes either way. Compare explicitly:

```yaml
    if: ${{ needs.setup.outputs.should_deploy == 'true' }}
```

**A** is wrong — job-level `if:` can read `needs`, that is its main use. **C** is
a real trap but a different one: `github.ref_name` gives the short name (`main`),
while `github.ref` gives `refs/heads/main`; here the comparison correctly produced
`false`, and the bug is the truthiness test. **D** is wrong because the `${{ }}`
wrapper is optional in `if:` — the value is evaluated as an expression either way.

**4.** A job output needs two hops, and the first one is usually missing.

Hop 1, inside the producing job, a step writes to `$GITHUB_OUTPUT` and **must**
have an `id`:

```yaml
    steps:
      - id: meta
        run: echo "run_label=bdd-${{ github.run_number }}" >> "$GITHUB_OUTPUT"
```

Hop 2, the job promotes that step output to a job output:

```yaml
    outputs:
      run_label: ${{ steps.meta.outputs.run_label }}
```

Only then is `needs.setup.outputs.run_label` populated. Omitting the `outputs:`
block on the producing job is the usual cause, and it fails silently: an
unresolvable expression evaluates to the empty string, so the consumer prints
nothing and the run stays green. Debug it by echoing the value in the *producing*
job first — that tells you which hop is broken. Note also that a matrix job's
outputs are overwritten by each leg that sets them, so there is no reliable way to
collect per-leg values this way; use artifacts for that.

**5.** They control different things and are not alternatives:

- `fail-fast` (default `true`) decides whether the **first failing leg cancels the
  others**. With three browsers you want all three verdicts, so set
  `fail-fast: false` — otherwise a flaky Firefox run cancels a Chrome run that was
  about to reveal a real bug.
- `max-parallel` caps **how many legs run at once**. With only two of
  `server1`–`server4` free during the day, `max-parallel: 2` keeps the matrix from
  queueing behind itself and starving other workflows of runners.

```yaml
    strategy:
      fail-fast: false
      max-parallel: 2
      matrix:
        browser: [chrome, firefox, msedge]
    runs-on: [self-hosted, windows, server1]
```

## Lab 1 — Beginner

**Task:** Add a `concurrency` group with `cancel-in-progress: false` and confirm a
second run queues behind the first.

<details>
<summary>Show solution</summary>

```yaml
name: Queued Health Check

on:
  workflow_dispatch:
  push:
    branches:
      - main

permissions:
  contents: read

concurrency:
  # One lane per ref, so main and a feature branch do not block each other.
  group: health-check-${{ github.ref }}
  cancel-in-progress: false     # queue, never cancel

jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Simulate a long health check
        run: |
          echo "python scripts/hello.py --tag healthcheck"
          sleep 90
```

**Why this works.** `concurrency` at workflow level admits one run per group.
Including `github.ref` in the group name scopes the lane per branch, which is
almost always what you want — a global group would make a feature branch wait on
`main`. `cancel-in-progress: false` is the queue-don't-cancel choice.
`timeout-minutes` matters more than usual here: a hung run holds the lane, so
every queued run waits behind it.

**Verify the failure mode the lab asks for.** Dispatch the workflow twice within
90 seconds. The second run appears with status *Pending*, showing that it is
waiting on the concurrency group, and starts only when the first finishes. Now flip
to `cancel-in-progress: true` and repeat: the first run immediately ends as
**cancelled**, mid-`sleep`. Imagining that `sleep` is a deploy is the whole
lesson.

**Common wrong answer.** `group: ${{ github.run_id }}`. It looks like a
per-workflow lane but `run_id` is unique to each run, so every run occupies its own
group and nothing is ever serialised — the block is decorative. Only expressions
that are *equal* across the runs you want serialised belong in the group key.

</details>

## Lab 2 — Intermediate

**Task:** Add a producer job output and consume it in a downstream job.

<details>
<summary>Show solution</summary>

```yaml
name: Job Outputs

on: workflow_dispatch

permissions:
  contents: read

jobs:
  setup:
    runs-on: ubuntu-latest
    # Hop 2: promote the step outputs to job outputs.
    outputs:
      run_label: ${{ steps.meta.outputs.run_label }}
      should_deploy: ${{ steps.meta.outputs.should_deploy }}
    steps:
      # Hop 1: the step needs an id, and writes to $GITHUB_OUTPUT.
      - name: Compute run metadata
        id: meta
        run: |
          echo "run_label=bdd-${{ github.run_number }}" >> "$GITHUB_OUTPUT"
          echo "should_deploy=${{ github.ref_name == 'main' }}" >> "$GITHUB_OUTPUT"

      - name: Echo what was produced
        run: echo "Producer set run_label=${{ steps.meta.outputs.run_label }}"

  publish:
    needs: setup
    # Compare against the STRING 'true' -- outputs are never booleans.
    if: ${{ needs.setup.outputs.should_deploy == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - name: Use the upstream output
        run: echo "Publishing ${{ needs.setup.outputs.run_label }}"
```

**Why this works.** The `id: meta` step writes `key=value` lines to the file named
by `$GITHUB_OUTPUT`, producing `steps.meta.outputs.*`. The job's `outputs:` block
forwards those to `needs.setup.outputs.*` in any job that declares
`needs: setup`. The `== 'true'` comparison is what makes the gate real; without it
`publish` would run on every branch.

**Verify the failure mode the lab asks for.** Delete the `outputs:` block from
`setup` but leave `publish` unchanged. `needs.setup.outputs.should_deploy` becomes
an empty string, `'' == 'true'` is false, and `publish` is **skipped** with no
error and nothing in the log explaining why. Restore the block and instead drop
`id: meta`: the workflow now fails to compile, because `steps.meta.outputs...` in
the `outputs:` block cannot be resolved to a step. One version fails loudly, the
other silently — recognising which is which saves hours.

**Common wrong answer.** Writing to `$GITHUB_ENV` instead of `$GITHUB_OUTPUT` and
expecting `needs.setup.outputs.run_label` to appear. `$GITHUB_ENV` sets environment
variables for later steps *in the same job*; environment variables do not cross job
boundaries and are not outputs. A close cousin is using the retired
`::set-output` command, which is disabled — `$GITHUB_OUTPUT` is the only supported
mechanism.

</details>

## Lab 3 — Challenge

**Task:** Add a matrix with `fail-fast: false` and `max-parallel`, plus an
`if: always()` summary job that reports each dependency's result.

<details>
<summary>Show solution</summary>

```yaml
name: Controlled Matrix With Summary

on:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: bdd-${{ github.ref }}
  cancel-in-progress: false

defaults:
  run:
    shell: bash

jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      run_label: ${{ steps.meta.outputs.run_label }}
    steps:
      - id: meta
        run: echo "run_label=bdd-${{ github.run_number }}" >> "$GITHUB_OUTPUT"

  test-matrix:
    needs: setup
    runs-on: ubuntu-latest
    timeout-minutes: 20
    strategy:
      fail-fast: false      # every browser reports its own verdict
      max-parallel: 2       # only two runners are free during the day
      matrix:
        browser: [chrome, firefox, msedge]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Run Behave on ${{ matrix.browser }}
        env:
          RUN_LABEL: ${{ needs.setup.outputs.run_label }}
          BROWSER: ${{ matrix.browser }}
        run: |
          echo "Run label: $RUN_LABEL"
          echo "behave --tags=smoke -D browser=$BROWSER --no-capture"
          # Simulate one flaky browser to prove fail-fast: false works.
          if [ "$BROWSER" = "firefox" ]; then
            echo "Simulated firefox failure" >&2
            exit 1
          fi

  summary:
    needs: [setup, test-matrix]
    if: always()            # the report is exactly what you need after a failure
    runs-on: ubuntu-latest
    steps:
      - name: Write the run summary
        env:
          SETUP_RESULT: ${{ needs.setup.result }}
          MATRIX_RESULT: ${{ needs.test-matrix.result }}
          RUN_LABEL: ${{ needs.setup.outputs.run_label }}
        run: |
          {
            echo "## Run Summary"
            echo ""
            echo "| Job | Result |"
            echo "| --- | --- |"
            echo "| setup | $SETUP_RESULT |"
            echo "| test-matrix | $MATRIX_RESULT |"
            echo ""
            echo "Run label: $RUN_LABEL"
          } >> "$GITHUB_STEP_SUMMARY"

      - name: Fail the run if the matrix failed
        if: ${{ needs.test-matrix.result != 'success' }}
        run: |
          echo "Matrix result was ${{ needs.test-matrix.result }}"
          exit 1
```

**Why this works.** `fail-fast: false` lets Chrome and Edge finish after Firefox
fails, so one run tells you which browsers are actually broken. `max-parallel: 2`
throttles the fan-out to the runners you really have. A matrix job appears to its
dependents as **one** node, so `needs.test-matrix.result` is a single rolled-up
value — `failure` if any leg failed. `if: always()` is what lets `summary` run at
all after that failure, and the final step re-fails the run deliberately, because
`if: always()` on the summary would otherwise let a red matrix end in a green
workflow.

**Verify the failure mode the lab asks for.** Run as written: three legs, at most
two concurrent, Firefox red and the other two green, and a summary table listing
`test-matrix | failure`. Then remove `if: always()` from `summary` and re-run — the
summary job is **skipped**, and the one artifact you wanted from the failed run does
not exist. Finally set `fail-fast: true` and re-run: whichever legs were still in
flight when Firefox failed end as **cancelled**, so you learn nothing about them.

**Common wrong answer.** Expecting per-leg results in the summary via something
like `needs.test-matrix.outputs.browser`. Matrix legs collapse into one `needs`
entry, and each leg's outputs overwrite the previous leg's, so there is no
per-browser data to read. If you need per-leg detail in the summary, have each leg
upload a small artifact (Module 10) with a leg-specific name and have the summary
job download them with `pattern:` and `merge-multiple: true`.

</details>

---

[Solutions Index](./README.md) | [Module 11](../modules/module-11-misc-features.md) | [Course Home](../README.md)
