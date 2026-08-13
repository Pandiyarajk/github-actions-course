# Module 7 — Solutions

![Module](https://img.shields.io/badge/Module-7-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 7](../modules/module-07-jobs-and-steps.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — C.** `env` resolves from the narrowest scope outwards: step, then job, then
workflow. The step declared `TEST_TAGS` itself, so it sees `nightly`. **A**
inverts the rule — workflow level is the *default*, the thing every narrower scope
is free to override. **B** is the half-remembered version of the rule, correct
about job beating workflow but wrong about job beating step. **D** describes
nothing GitHub Actions does; a redefinition replaces, it never accumulates.

**2 — B.** The map key is the job ID, and it is the identifier everything
machine-readable uses: `needs:`, the `github.job` context, the REST API, and the
check-run name that branch protection's required checks are configured against.
`name:` is a label for humans. **A** is the belief that costs a repository a
broken merge queue — a required status check pinned to the old ID stays
permanently pending, because nothing will ever report under that name again. **C**
is backwards: the UI is the one place the rename is invisible, since it displays
`name:`. **D** is unrelated; `runs-on` does not consult the job ID.

**3 — C.** Jobs do not share a filesystem. `needs:` establishes ordering only, so
the second job starts on its own runner with an empty workspace. Move the file
with `actions/upload-artifact@v7` and `actions/download-artifact@v8`, or — if it
is a small value rather than a file — declare a job `outputs` entry. **A** treats
a race condition as the cause, but the first job had fully completed; ordering was
never the problem. **B** confuses env with storage: `env` propagates *values* to
jobs, not files. **D** is the most seductive answer, because "same runner label"
sounds like "same machine" — it is not, and even on a self-hosted runner where it
sometimes is, relying on it produces a suite that passes until a second runner
joins the pool.

**4.** With no `timeout-minutes`, the job takes the documented default of 360
minutes. The hung suite therefore sits on the browser dialog for six hours before
GitHub cancels it. On a self-hosted runner that is worse than a wasted job: the
runner has one job slot, so every other job targeting that label stays queued
behind a run that is doing nothing, and a nightly regression can still be blocking
the next morning's PR checks.

What to set instead — a bound derived from the job's own measured duration, plus
a margin:

```yaml
jobs:
  static-analysis:
    name: Static Analysis (pylint)
    runs-on: ubuntu-latest
    timeout-minutes: 15        # runs in ~3 min; 15 is already generous

  bdd-regression:
    name: BDD Regression
    needs: static-analysis
    runs-on: server1
    timeout-minutes: 240       # suite runs ~2.5h; anything past 4h is hung
    steps:
      - name: Run the suite
        timeout-minutes: 90    # bound the individual step that can hang
        run: behave --tags=regression
```

The values differ because the timeout is not a safety constant, it is an
assertion about *this* job: "if it takes longer than this, something is wrong."
Fifteen minutes on the lint job and four hours on the regression job encode the
same statement about two jobs with very different normal durations. The
step-level `timeout-minutes` is the part people forget, and it is what turns a
six-hour hang into a ninety-minute one with the failing step named.

**5.** The **job ID** is the key in the `jobs:` map. It is referenced by `needs:`,
exposed as `github.job`, used by the REST API, and reported as the check name
that branch protection matches. The **`name`** is the display string shown in the
Actions UI and in pull-request check summaries.

Using the wrong one, in each direction:

- Writing `needs: "BDD Regression on server4"` — the display name — fails workflow
  validation, because no job has that ID. The error says the job depends on an
  unknown job, which is at least loud and immediate.
- Editing `name:` on a job whose display name is a *required status check* in
  branch protection silently breaks merges instead. The job runs and passes under
  its new name, while the required check under the old name never reports, so the
  pull request waits on a check that no longer exists. This is the dangerous
  direction, because nothing fails — everything just stops merging.

## Lab 1 — Beginner

**Task:** Add a `name` and `timeout-minutes` to a job.

<details>
<summary>Show solution</summary>

```yaml
name: Jobs Basics

on: workflow_dispatch

jobs:
  smoke:                          # <- job ID: referenced by needs and the API
    name: Quick Smoke Suite       # <- display label in the Actions UI
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      TEST_TAGS: smoke
    steps:
      - name: Checkout
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Report the plan
        run: |
          echo "Would run: behave --tags=$TEST_TAGS"
```

**Why this works.** `smoke` and `Quick Smoke Suite` are two independent
identifiers with two audiences, and declaring both is what lets you rewrite the
label later without touching `needs:` references. `timeout-minutes: 10` replaces
the 360-minute default with a bound that matches what this job actually does.

**Verify the failure mode the lab asks for.** Set `timeout-minutes: 1` and add a
step that sleeps past it:

```yaml
      - name: Exceed the timeout deliberately
        run: sleep 120
```

After roughly a minute the job stops with a cancellation, and the run is
annotated that it exceeded its maximum execution time. Two details are worth
noticing: the conclusion is a *failure* caused by cancellation rather than a
command returning non-zero, and no later step runs unless it carries
`if: always()`. That is why cleanup steps in long jobs need that condition — a
timeout is exactly when cleanup matters most.

**Common wrong answer.** Assuming a job with no `timeout-minutes` runs
indefinitely, and therefore that adding one is optional hardening. The default is
finite but very long, which is the worst of both: long enough to waste a full
working day of runner capacity, short enough that nobody notices the setting is
missing.

</details>

## Lab 2 — Intermediate

**Task:** Add job-level `env` and use it in a step.

<details>
<summary>Show solution</summary>

```yaml
name: Env Scopes

on:
  workflow_dispatch:
    inputs:
      tags:
        description: "Behave tag expression."
        type: string
        default: smoke

env:
  REPORT_HOME: reports            # workflow level: default for every job

jobs:
  bdd:
    name: BDD (${{ inputs.tags }})
    runs-on: ubuntu-latest
    timeout-minutes: 30
    env:
      TEST_TAGS: ${{ inputs.tags }}     # job level: every step in this job
      BROWSER: chrome                   # job level default, overridden below
    steps:
      - name: Show the job env
        run: |
          echo "Reports : $REPORT_HOME"
          echo "Tags    : $TEST_TAGS"
          echo "Browser : $BROWSER"

      - name: Override for one step only
        env:
          BROWSER: firefox                # step level: wins here, nowhere else
        run: echo "This step targets $BROWSER"

      - name: Prove the override did not leak
        run: |
          echo "Back to the job default: $BROWSER"
```

**Why this works.** All three scopes are live at once and resolution goes from
narrowest to widest. The workflow-level `REPORT_HOME` reaches every step without
being repeated; the job-level `TEST_TAGS` turns a dispatch input into something
the shell can read as `$TEST_TAGS`; the step-level `BROWSER` shadows the job value
for exactly one step. Passing `inputs.tags` through `env` rather than
interpolating `${{ inputs.tags }}` directly into the `run:` script is also the
safer habit — the value arrives as an environment variable instead of being
pasted into the script text before the shell parses it.

**Verify the failure mode the lab asks for.** Run it and read the three steps in
order: `chrome`, then `firefox`, then `chrome` again. The third line is the
lab's real lesson — step-level `env` does not persist to the next step, so a
"temporary" override you intended to apply to the rest of the job silently
applies to one step. If you want a value to carry forward from a step, that is
`$GITHUB_ENV`, covered in [Module 8](../modules/module-08-env-and-secrets.md).

**Common wrong answer.** Trying to reach the job's `env` from a job-level key:

```yaml
    env:
      TARGET: server1
    runs-on: ${{ env.TARGET }}    # does not work
```

The `env` context is not available to `runs-on` (or to `timeout-minutes`), and the
workflow fails validation with an unrecognized-named-value error for `env`. Job
selection keys are evaluated before the job's environment exists; use `inputs`,
`vars`, or `matrix` there instead.

</details>

## Lab 3 — Challenge

**Task:** Add a second job with `needs` that runs on a self-hosted server label.

<details>
<summary>Show solution</summary>

Compare your answer with the shipped example,
[`module-07-jobs-and-steps.yml`](../examples/module-07-jobs-and-steps.yml).

```yaml
name: Analysis Then Regression

on:
  workflow_dispatch:
    inputs:
      server:
        description: "Self-hosted server to run the suite on."
        type: choice
        options: [server1, server2, server3, server4]
        default: server1
      tags:
        description: "Behave tag expression."
        type: string
        default: regression

permissions:
  contents: read

env:
  REPORT_HOME: reports

jobs:
  static-analysis:
    name: Static Analysis (pylint)
    runs-on: ubuntu-latest
    timeout-minutes: 15
    # A small value the next job needs -- passed as a job output, not a file.
    outputs:
      analysed-at: ${{ steps.stamp.outputs.at }}
    steps:
      - name: Checkout
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Install linters
        run: pip install pylint

      - name: Lint the suite
        run: pylint your-solution-root-folder-name/

      - name: Record when analysis passed
        id: stamp
        run: echo "at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_OUTPUT"

  bdd-regression:
    name: BDD Regression on ${{ inputs.server }}
    needs: static-analysis          # <- the job ID, never the display name
    runs-on: ${{ inputs.server }}
    timeout-minutes: 240
    env:
      TEST_TAGS: ${{ inputs.tags }}
      ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
    steps:
      - name: Checkout
        uses: actions/checkout@v7

      - name: Report the upstream result
        run: echo "Analysis passed at ${{ needs.static-analysis.outputs.analysed-at }}"

      - name: Install suite dependencies
        run: pip install behave selenium allure-behave

      - name: Run the suite
        timeout-minutes: 180
        working-directory: your-solution-root-folder-name
        env:
          BROWSER: chrome
        run: |
          behave --tags="$TEST_TAGS" \
            -D browser="$BROWSER" \
            -f allure_behave.formatter:AllureFormatter \
            -o "$REPORT_HOME/allure-results"

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-${{ inputs.server }}-${{ github.run_id }}-${{ github.run_attempt }}
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30
```

**Why this works.** `needs: static-analysis` gives the two jobs an order and,
because they are separate jobs, lets each pick its own runner and its own
timeout — fifteen minutes on Ubuntu for lint, four hours on a self-hosted server
for the suite. The `outputs`/`needs.<id>.outputs` pair is how a *value* crosses
the job boundary; a file would have needed an artifact instead. `if: always()` on
the upload is what makes a failing suite still produce a report, which is the
only version of the job that is worth debugging.

**Verify the failure mode the lab asks for.** Make analysis fail — introduce a
lint error, or note that `pylint` here deliberately has no `--exit-zero`, so any
finding above the threshold fails the step. Re-run and watch the run graph:
`static-analysis` goes red and `bdd-regression` is reported as **Skipped**, not
failed and not queued. It never requested a runner, so the self-hosted server was
never occupied. That is the behaviour you are buying with `needs:` — a gate, not
just an ordering. If you want the second job to run anyway, it needs an explicit
condition such as `if: always()`, and then you have to decide what a regression
run means when the code did not lint.

Then break it the other way: change `needs: static-analysis` to
`needs: "Static Analysis (pylint)"`. The workflow no longer loads at all, failing
validation because it depends on an unknown job. Loud, immediate, and much kinder
than the branch-protection version of the same mistake.

**Common wrong answer.** Having `static-analysis` write `pylint.txt` and expecting
`bdd-regression` to read it from the workspace. The second job starts on a
different machine with an empty workspace, so the file is simply absent — and on a
self-hosted runner it may be *present but stale*, left over from a previous run,
which is worse than missing because the job succeeds against the wrong data.
Cross a job boundary with an artifact for files and a job output for values, never
with the filesystem.

</details>

---

[Solutions Index](./README.md) | [Module 7](../modules/module-07-jobs-and-steps.md) | [Course Home](../README.md)
