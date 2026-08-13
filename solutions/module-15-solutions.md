# Module 15 — Solutions

![Module](https://img.shields.io/badge/Module-15-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 15](../modules/module-15-multi-language-tests.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** A step with no `if:` carries an implicit `success()` condition: once
any earlier step in the job has failed, every following step is skipped. Since
Behave exits non-zero precisely when scenarios fail, the default behaviour throws
away the evidence for the only runs where you needed it. `if: always()` makes the
upload run regardless of the job's status. **A** misreads the ordering — steps are
sequential either way. **C** and **D** invent behaviour: `always()` has nothing to
do with compression, retention, or retries.

**2 — B.** `allure-behave` is a separate PyPI distribution that provides the
`allure_behave` package; installing `behave` alone does not bring it. The formatter
argument is resolved by import, so a missing distribution surfaces as
`ModuleNotFoundError` before any scenario executes. **A** describes a different
failure — the Allure *CLI* is a Java tool used later to render results, and its
absence fails the `allure generate` step, not Behave. **C** is wrong; the
`allure_behave.formatter:AllureFormatter` path is current. **D** is wrong because
Behave creates the `-o` directory itself.

**3 — B.** `needs:` is both an ordering constraint and a success condition. A
failed dependency leaves the dependent job **skipped**, not failed and not
executed. That is usually what you want — no reason to burn Selenium runners when
pylint is broken — but it has a consequence worth knowing: a skipped required
check does not satisfy branch protection, and a `summary` job that must run
anyway needs `if: always()` plus explicit inspection of `needs.<job>.result`.

**4.** `continue-on-error: true` on the job does not make the flake tolerable — it
makes the *entire job* report success no matter what fails inside it. The pull
request goes green, the check mark is meaningless, and a genuine Selenium
regression in any of the three browsers merges unnoticed. It converts one flaky
scenario into zero test signal.

Better handling, in order of preference: tag the scenario (`@flaky`) and exclude
it from the blocking run with `--tags=smoke,~flaky` while running it in a separate
non-blocking job so the data keeps accruing; fix the root cause, which for
Selenium is almost always an implicit sleep that should be an explicit
`WebDriverWait` on a condition; and if a retry is genuinely warranted, retry at
the scenario level with a Behave rerun file rather than re-running the whole job,
so the flake stays visible in the Allure history instead of being papered over.
The distinction to hold on to: `continue-on-error` hides a result, tagging
*reclassifies* it, and only one of those leaves you able to see the truth.

**5.** Names must be unique per leg, so include every varying dimension:
`name: allure-${{ matrix.browser }}`. From v4 onwards an artifact is sealed when
the upload completes, so two legs uploading the same name is an error rather than
a merge. A downstream job then collects them with a pattern:

```yaml
  report:
    needs: bdd-smoke
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Download every Allure artifact
        uses: actions/download-artifact@v8
        with:
          pattern: allure-*
          merge-multiple: true
          path: reports/allure-results
```

`merge-multiple: true` flattens all matching artifacts into one directory, which
is exactly the shape `allure generate` expects — Allure results are a directory of
independent JSON files, so concatenating three legs' output produces one report
covering all three browsers. Without `merge-multiple`, each artifact lands in its
own subdirectory and Allure sees nothing at the top level. `if: always()` on this
job is what keeps the report available for failing runs.

## Lab 1 — Beginner

**Task:** Add a pull-request workflow that runs one Behave command.

<details>
<summary>Show solution</summary>

```yaml
name: BDD Smoke

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Run Behave smoke suite
        working-directory: your-solution-root-folder-name
        run: behave features --tags=@smoke
```

**Why this works.** Three things have to be true before a test command can run,
and each is a separate step: the code is on the runner (`checkout`), an
interpreter exists (`setup-python` with the version quoted as `"3.13"`, since
unquoted `3.10` would parse as the number 3.1), and the suite's dependencies are
installed. `cache: pip` is handled by `setup-python` itself and keys on the
resolved `requirements.txt`, so no separate cache step is needed
([Module 16](../modules/module-16-docker-performance.md)). Behave's non-zero exit
on a failing scenario is what fails the step, which is what fails the check on
the pull request — no reporting plumbing required for that part.

**Verify the failure mode the lab asks for.** Delete the install step and re-run.
The step fails immediately:

```
behave: command not found
```

That is the most common cause of a red pipeline on day one, and it is worth
noticing how *unlike* a test failure it looks: no scenarios ran, no report was
produced, and the exit code is the shell's 127 rather than Behave's.

**Common wrong answer.** Relying on `working-directory` to also apply to
`requirements.txt` in the install step. `working-directory` is per step; the
install step above runs from the repository root, so the path must include
`your-solution-root-folder-name/`. Setting the path in one place and the working
directory in another produces a "No such file or directory" that reads like a
missing file rather than a wrong starting point.

</details>

## Lab 2 — Intermediate

**Task:** Upload the Allure results as an artifact, available after the run.

<details>
<summary>Show solution</summary>

```yaml
name: BDD Smoke with Allure

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: |
          pip install -r your-solution-root-folder-name/requirements.txt
          pip install allure-behave

      - name: Run Behave smoke suite
        working-directory: your-solution-root-folder-name
        run: |
          behave features --tags=@smoke \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results \
            --junit --junit-directory reports/junit

      - name: Upload test evidence
        # Runs even when the suite failed -- that is the run whose report matters.
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: smoke-evidence
          path: |
            your-solution-root-folder-name/reports/allure-results/
            your-solution-root-folder-name/reports/junit/
          retention-days: 30
          if-no-files-found: error
```

**Why this works.** Behave writes machine-readable output in two formats at once:
the Allure formatter emits a directory of JSON per scenario, and `--junit` emits
XML that most dashboards ingest directly. Both are ordinary files in the
workspace, so a single `upload-artifact` step with a multi-line `path:` captures
them. `if-no-files-found: error` is the part most people omit and later wish they
had — it converts a silently empty upload into a failure at the point where the
cause is obvious.

**Verify the failure mode the lab asks for.** Remove `if: always()`, then make a
scenario fail on purpose (assert something false in a step definition). The Behave
step goes red and the upload step is **skipped** — greyed out in the UI, no
artifact produced. You are left with a failing run and no evidence of why, which
is the exact scenario `always()` exists to prevent.

Then reproduce the second failure: restore `if: always()` but point `path:` at
`reports/allure-results/` without the `your-solution-root-folder-name/` prefix.
Because `path:` is resolved relative to the workspace root and not to any step's
`working-directory`, nothing matches. With `if-no-files-found: error` the step
fails and names the path; with the default `warn` it merely logs that no files
were found and produces no artifact — a green run with nothing attached.

**Common wrong answer.** Running `allure generate` in the same step and uploading
only the rendered HTML report. It works until a matrix arrives: rendered reports
cannot be merged, whereas raw `allure-results` directories can (see quiz answer
5). Upload the results; render once, later, from everything collected.

</details>

## Lab 3 — Challenge

**Task:** Split static analysis, API tests, and BDD smoke into separate jobs, with
a browser matrix on the smoke layer.

<details>
<summary>Show solution</summary>

```yaml
name: Layered Test Pipeline

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  # A new push to the same PR makes the in-flight run obsolete.
  group: tests-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  static-analysis:
    # Cheapest layer first: it gates the expensive ones.
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Run pylint
        run: pylint your-solution-root-folder-name/

      - name: Check duplicate functions
        run: python your-solution-root-folder-name/scripts/check-duplicate-functions.py

  api-tests:
    needs: static-analysis
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Run API scenarios
        working-directory: your-solution-root-folder-name
        run: |
          behave features --tags=@api \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Upload API evidence
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-api
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30

  bdd-smoke:
    needs: static-analysis
    runs-on: ubuntu-latest
    timeout-minutes: 45
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox, msedge]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Run Selenium BDD smoke on ${{ matrix.browser }}
        working-directory: your-solution-root-folder-name
        run: |
          behave features --tags=@smoke \
            -D browser=${{ matrix.browser }} \
            -D base_url=https://your-domain.com \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Upload smoke evidence
        if: always()
        uses: actions/upload-artifact@v7
        with:
          # Unique per leg -- see the failure mode below.
          name: allure-smoke-${{ matrix.browser }}
          path: |
            your-solution-root-folder-name/reports/allure-results/
            your-solution-root-folder-name/screenshots/
          retention-days: 30

  report:
    needs: [api-tests, bdd-smoke]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Collect every Allure artifact
        uses: actions/download-artifact@v8
        with:
          pattern: allure-*
          merge-multiple: true
          path: allure-results

      - name: Summarise the layers
        env:
          API_RESULT: ${{ needs.api-tests.result }}
          SMOKE_RESULT: ${{ needs.bdd-smoke.result }}
        run: |
          {
            echo "## Test layers"
            echo "| Layer | Result |"
            echo "| --- | --- |"
            echo "| API | ${API_RESULT} |"
            echo "| BDD smoke | ${SMOKE_RESULT} |"
          } >> "$GITHUB_STEP_SUMMARY"

      - name: Upload merged Allure results
        uses: actions/upload-artifact@v7
        with:
          name: allure-merged
          path: allure-results/
          retention-days: 30
```

**Why this works.** The layers are ordered by cost and by what each one can rule
out. `static-analysis` needs no browser and finishes in under a minute, so gating
the two expensive layers on it with `needs:` means a syntax error never consumes
Selenium capacity. `api-tests` and `bdd-smoke` both depend only on
`static-analysis`, so they run **in parallel** with each other — a diamond, not a
chain. The matrix belongs on the smoke layer alone, because browser variation is
only meaningful for UI scenarios. The `report` job carries `if: always()` and
reads `needs.<job>.result` explicitly, since without that it would be skipped in
exactly the failing runs where the summary is most useful. `concurrency` with
`cancel-in-progress` keeps a rapid series of pushes from queuing several full
matrices.

**Verify the failure mode the lab asks for.** Change the smoke artifact name to a
constant `allure-smoke`. The first leg to finish uploads fine; each subsequent leg
fails its upload step, because an artifact name is claimed exclusively once the
upload completes — a second upload under the same name is a conflict, not an
append. The confusing part is the symptom: two of three browsers report a failed
job while their Behave step was green, so the pull request blames the tests for a
packaging mistake.

Second failure worth provoking: break pylint deliberately. `static-analysis` goes
red and both `api-tests` and `bdd-smoke` are **skipped** rather than failed — and
because `report` declares `if: always()`, it still runs, with
`needs.bdd-smoke.result` equal to `skipped`. That is why the summary prints the
result values instead of assuming success or failure.

**Common wrong answer.** Chaining the layers linearly —
`bdd-smoke` with `needs: api-tests` — on the reasoning that tests should run in
order. It roughly doubles wall-clock time for no added signal: API and UI
scenarios are independent, and their only shared precondition is that the code
lints. The related mistake is adding `needs: bdd-smoke` to `report` without
`if: always()`, which deletes the report from every run that had something to
report.

</details>

---

[Solutions Index](./README.md) | [Module 15](../modules/module-15-multi-language-tests.md) | [Course Home](../README.md)
