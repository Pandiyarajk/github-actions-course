# Module 19 — Solutions

![Module](https://img.shields.io/badge/Module-19-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 19](../modules/module-19-monorepo-best-practices.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** A workflow filtered out by `paths` does not run, and a job that never
ran reports no status. Branch protection is waiting for a check named
`behave-smoke` to report success; "did not run" is not success, so the pull
request sits with the check **Expected — Waiting for status to be reported**
indefinitely. This is the single most common way path filtering breaks a repo,
and it looks like a branch-protection bug rather than a filter problem.

**A** has it backwards — required checks have no influence on whether a workflow
triggers. **C** is false; `paths` works on both `push` and `pull_request`. **D**
misreads the glob: `**/features/**` requires a `features` path segment, which
`README.md` does not have.

**2 — B.** The native `on.pull_request.paths` filter is evaluated *before* the
workflow starts and decides whether the **entire workflow run** happens. It is
all-or-nothing and, per question 1, produces no status for anything inside.
`dorny/paths-filter@v3` runs *inside* a job, compares the changed files itself,
and exposes one output per named filter, so downstream jobs can be gated
individually:

```yaml
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      pageobjects: ${{ steps.filter.outputs.pageobjects }}
    steps:
      - uses: actions/checkout@v7
      - id: filter
        uses: dorny/paths-filter@v3
        with:
          filters: |
            pageobjects:
              - 'your-solution-root-folder-name/pageobjects/**'
```

Crucially, the workflow *did* run in this version, so every required check
reports a result — which is why this is the pattern to reach for when checks are
required. **A**, **C** and **D** are all inventions; both mechanisms support
globs and both events.

**3 — B.** `pull_request_target` runs with the **base** repository's token and
secrets. Checking out the fork's head SHA under that trigger executes untrusted
contributor code with privileged credentials, and doing it on a self-hosted
runner adds a persistent machine to the blast radius: the runner's filesystem,
cached credentials, network position, and anything the next job on that box
touches. That combination is the reason the module says to use
`pull_request_target` with extreme caution.

**A** is normal and fine — `push` to `main` is trusted code. **C** is a
convenience feature with no security implication; the operator dispatching the
workflow already has write access. **D** is the *mitigation*, not the risk.

**4.** On a pull request editing only `reusables/queries.py`, the `pageobjects`
filter matches (it lists the file) so `static-checks` runs, but the `steps`
filter does not match, so `behave-smoke` is skipped. The helper is imported by
the step files too, so a change that breaks the step definitions ships with a
green pull request — the smoke suite that would have caught it never ran. The
symptom appears on the next unrelated PR, or on the nightly run, far from the
commit that caused it.

The fix is to make shared code belong to **every** filter that depends on it:

```yaml
          filters: |
            shared: &shared
              - 'your-solution-root-folder-name/reusables/**'
            pageobjects:
              - *shared
              - 'your-solution-root-folder-name/pageobjects/**'
            steps:
              - *shared
              - 'your-solution-root-folder-name/features/**'
              - 'your-solution-root-folder-name/steps/**'
```

`dorny/paths-filter` supports YAML anchors in the `filters` block, so the shared
list is declared once and referenced. The general rule: a path filter is a claim
about the dependency graph, and it is only as correct as that claim. Anything
imported widely must either be listed widely or be excluded from filtering
entirely.

**5.** You keep the expensive job conditional and add a small **aggregator job**
that is the required check. It depends on the real jobs, always runs, and passes
when they either succeeded or were legitimately skipped:

```yaml
  ci-required:
    needs: [detect-changes, static-checks, behave-smoke]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Verify no dependency failed
        env:
          STATIC: ${{ needs.static-checks.result }}
          SMOKE: ${{ needs.behave-smoke.result }}
        run: |
          for result in "${STATIC}" "${SMOKE}"; do
            case "${result}" in
              success|skipped) ;;
              *) echo "Dependency reported: ${result}"; exit 1 ;;
            esac
          done
          echo "All required areas passed or were not affected."
```

Branch protection requires `ci-required` and nothing else. Because it has
`if: always()` and no `paths` filter of its own, it *always* reports a status, so
the pull request is never stuck. Because it fails on any dependency result other
than `success` or `skipped`, a genuinely broken job still blocks the merge.

Two things make this work that are easy to get wrong. `if: always()` is
mandatory — without it the aggregator inherits the default "skip when a
dependency did not succeed" and becomes just as unreportable as the jobs it
wraps. And treating `skipped` as acceptable is only safe when your filters are
correct, which is exactly what question 4 is about: the aggregator makes required
checks *reportable*, it does not make a wrong filter right.

## Lab 1 — Beginner

**Task:** Trigger the workflow only for changes under
`your-solution-root-folder-name/pageobjects/**`, so step-file changes do not run
it.

<details>
<summary>Show solution</summary>

`.github/workflows/pageobjects-pr.yml`:

```yaml
name: Page Objects Pull Request Checks

on:
  pull_request:
    branches:
      - main
    paths:
      - "your-solution-root-folder-name/pageobjects/**"
      # Include the workflow itself, so edits to the checks are checked.
      - ".github/workflows/pageobjects-pr.yml"

permissions:
  contents: read

jobs:
  pageobjects-pr:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Install linters
        run: |
          python -m pip install --upgrade pip
          python -m pip install pylint

      - name: Lint page objects
        run: pylint your-solution-root-folder-name/pageobjects/
```

**Why this works.** `paths` is evaluated against the pull request's changed-file
list before any runner is allocated, so an unrelated pull request costs nothing
at all. Listing the workflow file itself in `paths` is the detail people leave
out: without it, a change to the lint configuration is never exercised by the
check it configures.

**Verify the failure mode the lab asks for.** Open a pull request that touches
only `your-solution-root-folder-name/steps/login_steps.py`. The Actions tab shows
no run for this workflow — correct behaviour. Now make `pageobjects-pr` a
required status check in branch protection and open the same pull request again.
It cannot be merged: the check is listed as expected but never reports, so the
merge button stays disabled with a check waiting for a status that will never
arrive. That is quiz question 1 reproduced on your own repository, and it is
worth seeing once before you rely on path filters anywhere.

**Common wrong answer.** Writing `paths: ["pageobjects/**"]` when the folder sits
under a solution root. `paths` globs are matched from the **repository root**, not
from any working directory, so that pattern matches nothing and the workflow
silently never runs. A filter that matches nothing and a filter that is absent
look identical in the UI — both show no runs.

</details>

## Lab 2 — Intermediate

**Task:** Add path filters for `pageobjects/`, `features/steps/`, and
`.github/scripts/` so only affected jobs run.

<details>
<summary>Show solution</summary>

The finished workflow is
[`module-19-monorepo-best-practices.yml`](../examples/module-19-monorepo-best-practices.yml).

```yaml
name: Monorepo Selective CI

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read
  pull-requests: read

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    outputs:
      pageobjects: ${{ steps.filter.outputs.pageobjects }}
      steps: ${{ steps.filter.outputs.steps }}
      scripts: ${{ steps.filter.outputs.scripts }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Detect changed areas
        id: filter
        uses: dorny/paths-filter@v3
        with:
          filters: |
            shared: &shared
              - 'your-solution-root-folder-name/reusables/**'
            pageobjects:
              - *shared
              - 'your-solution-root-folder-name/pageobjects/**'
            steps:
              - *shared
              - 'your-solution-root-folder-name/features/**'
              - 'your-solution-root-folder-name/steps/**'
            scripts:
              - '.github/scripts/**'

      - name: Print what changed
        env:
          PAGEOBJECTS: ${{ steps.filter.outputs.pageobjects }}
          STEPS: ${{ steps.filter.outputs.steps }}
          SCRIPTS: ${{ steps.filter.outputs.scripts }}
        run: |
          echo "pageobjects=${PAGEOBJECTS} steps=${STEPS} scripts=${SCRIPTS}"

  static-checks:
    needs: detect-changes
    # Outputs are STRINGS -- compare, never rely on truthiness.
    if: ${{ needs.detect-changes.outputs.pageobjects == 'true' }}
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - name: Install linters
        run: |
          python -m pip install --upgrade pip
          python -m pip install pylint
      - name: Run static analysis on page objects
        run: |
          pylint your-solution-root-folder-name/pageobjects/ \
            your-solution-root-folder-name/reusables/queries.py
          python .github/scripts/check-duplicate-functions.py \
            your-solution-root-folder-name/pageobjects/
          python .github/scripts/check-duplicate-variables.py \
            your-solution-root-folder-name/pageobjects/

  behave-smoke:
    needs: detect-changes
    if: ${{ needs.detect-changes.outputs.steps == 'true' }}
    runs-on: [self-hosted, windows, server1]
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v7
      - name: Run Behave smoke on self-hosted runner
        run: |
          behave --tags=@smoke \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results
      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results-smoke
          path: reports/allure-results/
          retention-days: 14

  ci-required:
    needs: [detect-changes, static-checks, behave-smoke]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Verify no dependency failed
        env:
          STATIC: ${{ needs.static-checks.result }}
          SMOKE: ${{ needs.behave-smoke.result }}
        run: |
          for result in "${STATIC}" "${SMOKE}"; do
            case "${result}" in
              success|skipped) ;;
              *) echo "Dependency reported: ${result}"; exit 1 ;;
            esac
          done
          echo "All required areas passed or were not affected."
```

**Why this works.** The workflow always runs, so statuses are always reported;
the *jobs* are what get skipped. `detect-changes` publishes one output per area,
each a string, which is why the conditions compare against `'true'` rather than
testing truthiness — `'false'` is a non-empty string and therefore truthy, so
`if: ${{ needs.detect-changes.outputs.steps }}` would run the smoke suite
unconditionally. The `shared` anchor puts `reusables/**` in both dependent
filters, per quiz question 4. `ci-required` is the single required check, so
branch protection never waits on a skipped job.

The `Print what changed` step is not decoration — path-filter bugs are almost
impossible to diagnose without seeing the resolved outputs, and it costs a
second.

**Verify the failure mode the lab asks for.** Change the smoke job's condition to
`if: ${{ needs.detect-changes.outputs.steps }}` and open a pull request that
touches only `.github/scripts/`. The smoke job runs anyway, because the output is
the string `'false'`. The log shows `steps=false` immediately above a job that
started regardless — the two facts side by side are what make the string-truthiness
rule stick. Then edit only `reusables/queries.py` with the `shared` anchor removed
and observe `behave-smoke` skip, which is the real-world version of the same bug.

**Common wrong answer.** Combining the native `paths` filter with
`dorny/paths-filter`. Adding `on: pull_request: paths:` to this workflow reverts
you to all-or-nothing gating at the workflow level, so the careful per-job
conditions never get a chance to run and the required check goes unreported
again. Pick one mechanism: native `paths` when nothing in the workflow is
required, `paths-filter` plus an aggregator when something is.

</details>

## Lab 3 — Challenge

**Task:** Add a `workflow_dispatch` choice input so the operator picks the
self-hosted runner (`server1`..`server4`) the Behave smoke job targets.

<details>
<summary>Show solution</summary>

```yaml
name: On-Demand Behave Smoke

on:
  workflow_dispatch:
    inputs:
      runner:
        description: "Self-hosted runner to use"
        type: choice
        required: true
        default: server1
        options:
          - server1
          - server2
          - server3
          - server4
      browser:
        description: "Browser for the smoke run"
        type: choice
        required: true
        default: chrome
        options:
          - chrome
          - firefox
          - msedge

run-name: Behave smoke on ${{ inputs.runner }} (${{ inputs.browser }})

permissions:
  contents: read

concurrency:
  # One run per machine: two smoke runs on the same box would fight over
  # the browser session and the results directory.
  group: smoke-${{ inputs.runner }}
  cancel-in-progress: false

jobs:
  smoke:
    runs-on:
      - self-hosted
      - windows
      - "${{ inputs.runner }}"
    timeout-minutes: 60
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Show where this landed
        shell: pwsh
        run: |
          "Requested label : ${{ inputs.runner }}"
          "Actual runner   : $env:RUNNER_NAME"
          "Runner labels   : $env:RUNNER_LABELS"

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install behave selenium allure-behave

      - name: Run Behave smoke
        run: |
          behave --tags=@smoke \
            -D browser=${{ inputs.browser }} \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          # Name carries the runner, so parallel dispatches never collide.
          name: allure-results-${{ inputs.runner }}-${{ inputs.browser }}
          path: reports/allure-results/
          retention-days: 14
```

**Why this works.** `runs-on` accepts an expression in a label list, and
`workflow_dispatch` inputs are available at the point the job is created, so
`${{ inputs.runner }}` resolves before scheduling. Keeping `self-hosted` and
`windows` alongside it means the label is a *narrowing* choice rather than the
whole selection — if `server3` were ever attached to a Linux box, the job would
queue rather than run somewhere wrong. `run-name` puts the choice in the run list
so the Actions tab is readable a week later, and the artifact name carries both
inputs so two operators dispatching at once do not collide on an immutable
artifact name.

`concurrency` keyed on the runner, not the ref, is the non-obvious part: the
resource being contended is the *machine*, since two Selenium runs on one host
compete for the browser and the results path.

**Verify the failure mode the lab asks for.** Dispatch with `server4` while no
runner carries that label. The job does not fail — it sits in **Queued**
indefinitely, with the run page noting it is waiting for a runner matching the
requested labels, until the job timeout expires. A wrong label is a hang, not an
error, which is why `timeout-minutes` on self-hosted jobs is not optional. Then
try `runs-on: "${{ inputs.runner }}"` on its own with a matching label: it runs,
proving the label works, and hides the fact that you have lost the `self-hosted`
and `windows` constraints entirely.

**Common wrong answer.** Trying to select the machine by *name* — a
`runner-name:` key, or expecting `runs-on: server1` to match a runner registered
as `server1` when the label was never applied. You cannot rename or address a
runner by name from workflow YAML; the name is set at registration and only
labels are targetable. Apply a stable label at registration time and target that.

The second common miss is expecting `${{ inputs.runner }}` to work under a
`schedule` trigger too. Scheduled events carry no dispatch inputs, so the
expression resolves to an empty string, the label list becomes invalid, and the
job never gets scheduled. If one workflow must serve both, default the value
explicitly: `${{ inputs.runner || 'server1' }}`.

</details>

---

[Solutions Index](./README.md) | [Module 19](../modules/module-19-monorepo-best-practices.md) | [Course Home](../README.md)
