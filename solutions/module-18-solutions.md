# Module 18 — Solutions

![Module](https://img.shields.io/badge/Module-18-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 18](../modules/module-18-qa-automation.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — C.** From `actions/upload-artifact@v4` onward an artifact is **immutable**
once created. A second upload to the same name in the same run fails the step
rather than merging or overwriting. The fix is to make the name unique per matrix
leg and reassemble on download:

```yaml
      - uses: actions/upload-artifact@v7
        with:
          name: allure-results-${{ matrix.browser }}
          path: reports/allure-results/${{ matrix.browser }}
```

```yaml
      - uses: actions/download-artifact@v8
        with:
          pattern: allure-results-*
          merge-multiple: true
          path: reports/allure-results
```

**A** describes the pre-v4 behaviour, where uploads to one name accumulated into
a single archive — this is exactly the habit that breaks on upgrade. **B** and
**D** are what people assume when they see one leg's results and not the other's;
neither happens, and the give-away is that the *step* is red, not the artifact.

**2 — B.** A job stops at the first failed step unless a later step opts out with
a condition. `behave` exits non-zero when a scenario fails, so every step after
it is skipped — including the uploads. `if: always()` makes them run regardless:

```yaml
      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
```

**A** is false; `behave` leaves its results directory in place. **C** is not a
real default — omitting `retention-days` uses the repository setting, typically
90 days, never zero. **D** invents a self-hosted limitation.

**3 — B.** `runs-on` with a list of labels is an **AND**: the job is dispatched
only to a runner that carries every label. `[self-hosted, windows, server1]`
therefore means "the Windows self-hosted machine labelled server1".

**A** looks tempting because the label *is* unique, but bare `runs-on: server1`
omits the `self-hosted` label that distinguishes your fleet from GitHub-hosted
labels, and it is fragile the moment anything else gains that label. **C**
invents a `runner-name` key — you cannot select or rename a runner by name from
YAML; the name is fixed at registration time and only labels are targetable.
**D** misreads AND as OR: no single runner carries both `server1` and `server2`,
so that job queues forever.

**4.** The reporting job needs two things:

```yaml
  report-and-notify:
    needs: ui-tests
    if: always()
```

`needs: ui-tests` supplies the *ordering* and, critically, the artifact
availability — it must not start until the matrix legs have uploaded. But `needs`
alone also supplies a *condition*: by default a job is skipped when any of its
dependencies did not succeed. `if: always()` overrides that default so the job
runs on failure too. Without it, the run that most needs an email is precisely
the run that sends none.

Two refinements worth stating. Inside the job, `needs.ui-tests.result` tells you
what actually happened, so the email body can distinguish failure from
cancellation. And if you want the notifier to run on failure but *not* on
cancellation, `if: ${{ !cancelled() }}` is the more precise condition.

**5.** Do not delete the coverage and do not leave it in the gate. Split by
reliability, not by feature:

- **Tag the flaky scenarios** (`@flaky` in Behave) and exclude them from the
  suite whose result gates anything: `--tags=@smoke --tags=~@flaky`.
- **Run them in a separate job** that reports its own result and is explicitly
  non-blocking, either as its own workflow or with `continue-on-error: true`, so
  a flake cannot turn the nightly red.
- **Make the flake visible rather than invisible** — the quarantined job should
  still upload Allure results and appear in the summary, with an owner and a
  review date, so quarantine is a queue and not a graveyard.
- **Fix the underlying cause**, which for timing flakes is almost always an
  implicit wait or `time.sleep` standing in for an explicit
  `WebDriverWait(...).until(...)` on the condition the step actually depends on.

The point is that the email's red/green must mean something. A channel that is
red one run in four teaches the team to ignore it, and then a real regression
goes unnoticed — the module's "treating flaky tests as normal failures forever"
mistake.

## Lab 1 — Beginner

**Task:** Add a smoke test workflow that runs on pull requests.

<details>
<summary>Show solution</summary>

`.github/workflows/qa-smoke.yml`:

```yaml
name: QA Smoke Test

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read

concurrency:
  group: qa-smoke-${{ github.head_ref }}
  cancel-in-progress: true

jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Checkout tests
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Cache pip
        uses: actions/cache@v6
        with:
          path: ~/.cache/pip
          key: pip-${{ runner.os }}-${{ hashFiles('your-solution-root-folder-name/requirements.txt') }}
          restore-keys: |
            pip-${{ runner.os }}-

      - name: Install dependencies
        working-directory: your-solution-root-folder-name
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt
          python -m pip install requests

      - name: Run API health-check
        run: |
          python - <<'PY'
          import sys
          import requests

          response = requests.get("https://your-domain.com/health", timeout=30)
          print("status:", response.status_code)
          sys.exit(0 if response.ok else 1)
          PY
```

**Why this works.** The pull-request smoke check stays on `ubuntu-latest` and
does no browser work, so it finishes fast enough to be a required check.
`concurrency` keyed on `github.head_ref` with `cancel-in-progress: true` means a
second push to the same branch cancels the stale run — correct for PR checks,
and the opposite of what you want for releases. The heredoc is quoted
(`<<'PY'`), so the shell does not expand anything inside the Python.

**Verify the failure mode the lab asks for.** Point the health-check at a path
that does not exist, e.g. `https://your-domain.com/no-such-endpoint`. The script
prints `status: 404` and exits 1, the step goes red, and the pull request shows a
failed check. Compare that with dropping the `sys.exit` line: the request still
404s, the log still prints the status, and the check goes **green** — a health
check that never fails is worse than no health check, because it manufactures
confidence.

**Common wrong answer.** Using `requests.get(url)` with no `timeout=`. On a hung
endpoint the call blocks until the job's own limit kills it, so a 30-second
diagnosis becomes a 20-minute one and the log says only "cancelled". Always pass
`timeout=`, and always set `timeout-minutes` on the job as a backstop.

</details>

## Lab 2 — Intermediate

**Task:** Upload Allure results and failure screenshots as artifacts so evidence
survives both failure and success.

<details>
<summary>Show solution</summary>

```yaml
  ui-tests:
    needs: smoke
    runs-on:
      - self-hosted
      - windows
      - server1
    timeout-minutes: 90
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox]
    steps:
      - name: Checkout tests
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install behave selenium allure-behave

      - name: Run BDD UI tests
        shell: pwsh
        run: |
          behave your-solution-root-folder-name/features `
            --tags "@smoke" `
            -D browser=${{ matrix.browser }} `
            -f allure_behave.formatter:AllureFormatter `
            -o reports/allure-results/${{ matrix.browser }}

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          # Unique per matrix leg: artifacts are immutable, so a shared name errors.
          name: allure-results-${{ matrix.browser }}
          path: reports/allure-results/${{ matrix.browser }}
          retention-days: 30
          if-no-files-found: error

      - name: Upload failure screenshots
        if: failure()
        uses: actions/upload-artifact@v7
        with:
          name: screenshots-${{ matrix.browser }}
          path: reports/screenshots/
          retention-days: 30
          if-no-files-found: ignore
```

The screenshots only exist if the suite captures them. In
`your-solution-root-folder-name/features/environment.py`:

```python
"""Behave hooks: capture a screenshot when a scenario fails."""

import os


def after_scenario(context, scenario):
    """Save a PNG for any failed scenario so CI can upload it as evidence."""
    if scenario.status != "failed":
        return
    driver = getattr(context, "driver", None)
    if driver is None:
        return
    os.makedirs("reports/screenshots", exist_ok=True)
    safe_name = scenario.name.replace(" ", "_").replace("/", "_")
    driver.save_screenshot(f"reports/screenshots/{safe_name}.png")
```

**Why this works.** Four choices carry the weight. `fail-fast: false` keeps the
firefox leg running when chrome fails, so you get evidence from both.
`if: always()` on the Allure upload survives a red `behave` step, while
`if: failure()` on the screenshots skips the upload on green runs where the
directory is empty. The artifact names embed `matrix.browser`, so the two legs
never collide. And `if-no-files-found: error` on the results makes a silent
path typo loud — its default is `warn`, which produces an empty artifact and a
warning nobody reads.

**Verify the failure mode the lab asks for.** Change both upload names to a
constant `allure-results` and re-run. Whichever leg finishes second fails at the
upload step with a conflict on the already-created artifact — the job goes red
for a reason unrelated to the tests. Then remove `if: always()` and force one
scenario to fail: the `behave` step is red, both upload steps show as
**skipped**, and the run has no evidence at all. That second case is the one that
costs a night of triage, because the run looks like a normal failure.

**Common wrong answer.** Relying on `continue-on-error: true` on the `behave`
step instead of `if: always()` on the uploads. It does make the later steps run,
but it also reports the job as **successful** — the failing suite no longer
blocks anything, which is the opposite of what a gate is for.

</details>

## Lab 3 — Challenge

**Task:** Build the nightly chain — API health-check, BDD UI browser matrix,
Allure report analysis, and an email summary — running daily at 1:30 AM UTC.

<details>
<summary>Show solution</summary>

The finished workflow is
[`module-18-qa-automation.yml`](../examples/module-18-qa-automation.yml); the
structure that matters is below.

```yaml
name: Nightly QA Automation

on:
  schedule:
    - cron: "30 1 * * *"
  workflow_dispatch:
    inputs:
      tags:
        description: "Behave tags filter (e.g. @smoke)"
        type: string
        default: "@smoke"

permissions:
  contents: read

concurrency:
  group: nightly-qa-${{ github.ref }}
  cancel-in-progress: false

jobs:
  api-health-check:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install requests
      - name: Run API health-check
        run: |
          python - <<'PY'
          import sys
          import requests

          response = requests.get("https://your-domain.com/health", timeout=30)
          print("status:", response.status_code)
          sys.exit(0 if response.ok else 1)
          PY

  ui-tests:
    needs: api-health-check
    runs-on: [self-hosted, windows, server1]
    timeout-minutes: 120
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox]
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install behave selenium allure-behave
      - name: Run BDD UI tests
        shell: pwsh
        run: |
          behave your-solution-root-folder-name/features `
            --tags "${{ inputs.tags || '@smoke' }}" `
            -D browser=${{ matrix.browser }} `
            -f allure_behave.formatter:AllureFormatter `
            -o reports/allure-results/${{ matrix.browser }}
      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results-${{ matrix.browser }}
          path: reports/allure-results/${{ matrix.browser }}
          retention-days: 30

  report-and-notify:
    needs: ui-tests
    # Must run even when the matrix is red -- that is the run worth emailing.
    if: always()
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v7

      - name: Download every matrix leg's Allure results
        uses: actions/download-artifact@v8
        with:
          pattern: allure-results-*
          merge-multiple: true
          path: reports/allure-results

      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Analyze Allure results
        run: |
          python -m pip install --upgrade pip
          python -m pip install allure-report-analyzer
          allure-report-analyzer reports/allure-results \
            --out reports/metrics.json

      - name: Write run summary
        if: always()
        env:
          UI_RESULT: ${{ needs.ui-tests.result }}
        run: |
          {
            echo "## Nightly QA Summary"
            echo "- UI matrix result: ${UI_RESULT}"
            echo "- Commit: ${GITHUB_SHA}"
            echo "- Run: ${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"
          } >> "$GITHUB_STEP_SUMMARY"

      - name: Email QA summary
        if: always()
        env:
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          EMAIL_USERNAME: ${{ secrets.EMAIL_USERNAME }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
          UI_RESULT: ${{ needs.ui-tests.result }}
        run: |
          python your-solution-root-folder-name/scripts/send_report.py \
            --metrics reports/metrics.json \
            --result "${UI_RESULT}"
```

**Why this works.** The chain is three jobs because each has a different runner
and a different failure meaning. The health-check is cheap and gates the
expensive matrix, so a down environment costs ten minutes instead of two hours.
The matrix legs write to per-browser directories and upload under per-browser
names, and `download-artifact` reassembles them with
`pattern: allure-results-*` plus `merge-multiple: true` — which is only safe
*because* the names were unique. `if: always()` plus `needs.ui-tests.result`
gives the notifier both the permission to run and the information to describe
what it is reporting. `concurrency` with `cancel-in-progress: false` keeps a
manual re-run from colliding with the scheduled one on the same self-hosted
machine.

Note that `inputs.tags` is empty on a scheduled run, hence
`${{ inputs.tags || '@smoke' }}` — scheduled events carry no dispatch inputs.

**Verify the failure mode the lab asks for.** Force one scenario to fail and
watch the whole chain. With `if: always()` present, `ui-tests` is red,
`report-and-notify` still runs, and the email arrives labelled with
`failure`. Now delete `if: always()` and re-run: `report-and-notify` shows as
**skipped**, the summary is empty, and no email is sent. The run is red in the
UI, so a human watching the Actions tab sees it — but nobody is watching at 1:30
AM, which is the entire reason the email exists.

Second failure mode worth reproducing: point `cron` at `"30 1 * * *"` and check
when it actually fires. `cron` is **always UTC**, never the repository's or your
own timezone, and scheduled runs are queued on a best-effort basis — a few
minutes of drift under load is normal, so never build a schedule that assumes
minute-exact starts.

**Common wrong answer.** Putting the whole chain in one job with three phases.
It appears simpler and it is strictly worse: the health-check no longer gates
anything (a hung environment burns the full timeout), the browser matrix cannot
fan out, the self-hosted Windows runner ends up doing the reporting work it has
no reason to do, and a single failed step takes the reporting phase down with it
so you are back to relying on `if: always()` everywhere. The other common miss is
uploading each leg's results to a shared name and then wondering why
`merge-multiple` has nothing to merge.

</details>

---

[Solutions Index](./README.md) | [Module 18](../modules/module-18-qa-automation.md) | [Course Home](../README.md)
