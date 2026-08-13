# Module 10 — Solutions

![Module](https://img.shields.io/badge/Module-10-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 10](../modules/module-10-artifacts.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — C.** From v4 onwards an artifact is **immutable**: it is finalised when the
upload step ends, and the name is then taken for the rest of the run. The first
leg to finish creates `allure-results`; the others fail with a 409 conflict
reporting that an artifact with that name already exists on the workflow run.
**A** describes the pre-v4 behaviour, where uploads to one name accumulated into
a single artifact — that merge no longer happens and is the single most common
v3-to-v4 migration break. **B** is what `overwrite: true` looks like it buys you,
but overwrite deletes and recreates, so with parallel legs it is a race that loses
data rather than a merge. **D** is invented; nothing renames artifacts for you.
The fix is a unique name per leg plus a merging download:

```yaml
          name: allure-${{ matrix.browser }}
```

**2 — B.** `if: always()` runs the step regardless of earlier failures, including
after a failed `behave` step, which is exactly when screenshots matter. **A** and
**D** are the same thing — a step with no `if:` behaves as `if: success()`, so a
failing test run skips the upload and the evidence is lost with the runner.
**C** would collect screenshots on failure but skip them on a green run, so you
would never have a passing baseline to compare against.

**3 — D.** `actions/upload-artifact` exposes `artifact-id`, `artifact-url`, and
`artifact-digest`. There is no `artifact-name` output — you already know the name,
because you wrote it. Referencing `steps.up.outputs.artifact-name` does not error;
it silently evaluates to an empty string, which is how it survives review.

**4.** Give each leg a unique name on upload, then download by pattern and merge:

```yaml
  test:
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox, msedge]
    steps:
      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results-${{ matrix.browser }}
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30

  report:
    needs: test
    if: always()
    steps:
      - name: Download every leg's results into one directory
        uses: actions/download-artifact@v8
        with:
          pattern: allure-results-*
          merge-multiple: true
          path: allure-results
```

`pattern:` selects the matching artifacts and `merge-multiple: true` unpacks them
all into `allure-results/` instead of one subdirectory per artifact — which is
what Allure needs, since it expects one flat results directory.

**5.** `if-no-files-found` accepts `warn`, `error`, and `ignore`, and the default
is **`warn`**: a path that matches nothing logs a warning and the step still
succeeds. So the screenshots upload needs no change (or `ignore` if you want the
warning gone), because an empty screenshots folder is the normal outcome of a
passing run. The Allure results upload is the opposite case — empty results mean
`behave` never produced a report, which is a real failure you want surfaced:

```yaml
      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results
          path: your-solution-root-folder-name/reports/allure-results/
          if-no-files-found: error     # empty results means the run is broken

      - name: Upload failure screenshots
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: screenshots
          path: your-solution-root-folder-name/reports/screenshots/
          if-no-files-found: ignore    # absent on a green run, and that is fine
```

The choice is per upload, so pick it by asking whether "nothing matched" is
expected for *that* path.

## Lab 1 — Beginner

**Task:** Upload a single file with `retention-days: 7`.

<details>
<summary>Show solution</summary>

```yaml
name: Upload One File

on: workflow_dispatch

permissions:
  contents: read

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - name: Create a report
        run: |
          mkdir -p reports
          echo "passed: 12, failed: 1" > reports/summary.txt

      - name: Upload the report
        uses: actions/upload-artifact@v7
        with:
          name: summary
          path: reports/summary.txt
          retention-days: 7
```

**Why this works.** `path` points at one file, so the artifact contains that file
at the root of the zip — `upload-artifact` strips the longest common directory
prefix of everything it matched. `retention-days: 7` overrides the repository
default for this artifact only. The download is always `summary.zip`, never the
bare `summary.txt`.

**Verify the failure mode the lab asks for.** Change `path` to
`reports/summary.text` and re-run. The step still **succeeds**, with a warning in
the log that no files were found for the provided path, and no artifact appears on
the run page — because `warn` is the default for `if-no-files-found`. Add
`if-no-files-found: error` and re-run to turn that silent miss into a failed step.

**Common wrong answer.** Setting `retention-days: 0` to mean "repository
default". Valid values are 1–90; to accept the default you omit the key entirely.

</details>

## Lab 2 — Intermediate

**Task:** Upload a folder and a multi-path artifact in the same job.

<details>
<summary>Show solution</summary>

```yaml
name: Two Artifacts

on: workflow_dispatch

permissions:
  contents: read

env:
  ALLURE_RESULTS: your-solution-root-folder-name/reports/allure-results

jobs:
  evidence:
    runs-on: ubuntu-latest
    steps:
      - name: Generate sample evidence
        run: |
          mkdir -p "$ALLURE_RESULTS" your-solution-root-folder-name/reports/screenshots
          echo '{"passed": 12, "failed": 1}' > "$ALLURE_RESULTS/summary.json"
          echo "page load: 1.2s" > "$ALLURE_RESULTS/timing.txt"
          echo "fake-png-bytes" > your-solution-root-folder-name/reports/screenshots/login.png
          echo "behave --tags=smoke --no-capture" > behave-command.txt

      # Artifact 1 — a folder. The structure inside it is preserved.
      - name: Upload the Allure results folder
        uses: actions/upload-artifact@v7
        with:
          name: allure-results
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30

      # Artifact 2 — several paths, with a glob and an exclusion.
      - name: Upload the combined evidence bundle
        uses: actions/upload-artifact@v7
        with:
          name: combined-evidence
          path: |
            your-solution-root-folder-name/reports/**
            behave-command.txt
            !your-solution-root-folder-name/reports/**/*.tmp
          compression-level: 9
          retention-days: 7
```

**Why this works.** Two upload steps mean two artifacts, and the names differ, so
neither collides with the other. The folder upload keeps `summary.json` and
`timing.txt` side by side inside the zip. The multi-path upload takes a block
scalar: each line is a pattern, `**` recurses, and a leading `!` excludes.
`compression-level: 9` is worth it on text reports and wasted on already
compressed media such as PNG screenshots.

**Verify the failure mode the lab asks for.** Give both steps `name:
combined-evidence`. The first upload succeeds; the second fails with a 409
conflict saying an artifact with that name already exists on the workflow run —
artifacts are immutable, so a name is a one-shot resource per run. Note the shape
of the multi-path artifact too: because the common prefix of
`your-solution-root-folder-name/reports/**` and `behave-command.txt` is the
workspace root, the zip keeps the full `your-solution-root-folder-name/reports/`
path, unlike the folder-only artifact.

**Common wrong answer.** Writing the multiple paths as a YAML list:

```yaml
          path:
            - reports/**
            - behave-command.txt
```

`path` is a single string input, not a list. Every action input is a string, so
the multi-path form must be a `|` block with one pattern per line.

</details>

## Lab 3 — Challenge

**Task:** Add `if: always()` and `if: failure()` uploads behind a step that can
fail, and confirm the success-only upload is skipped.

<details>
<summary>Show solution</summary>

```yaml
name: Conditional Evidence

on:
  workflow_dispatch:
    inputs:
      force_failure:
        description: "Make the test step fail, to exercise the conditions"
        type: boolean
        default: false

permissions:
  contents: read

jobs:
  bdd:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Prepare report directories
        run: mkdir -p reports/allure-results reports/screenshots

      # The step under test. It fails when the input asks it to.
      - name: Run Behave suite
        id: behave
        env:
          # A boolean input still arrives as the STRING "true" or "false".
          FORCE_FAILURE: ${{ inputs.force_failure }}
        run: |
          echo '{"passed": 12}' > reports/allure-results/summary.json
          if [ "$FORCE_FAILURE" = "true" ]; then
            echo "fake-png-bytes" > reports/screenshots/login_failure.png
            echo "Simulated scenario failure" >&2
            exit 1
          fi
          echo "behave --tags=smoke --no-capture"

      - name: Upload the pass report (success only)
        if: success()
        uses: actions/upload-artifact@v7
        with:
          name: success-report
          path: reports/allure-results/
          retention-days: 7

      - name: Upload all evidence (pass or fail)
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: evidence-always
          path: reports/**
          if-no-files-found: warn
          retention-days: 14

      - name: Upload the debug bundle (failure only)
        if: failure()
        uses: actions/upload-artifact@v7
        with:
          name: failure-debug
          path: reports/screenshots/
          if-no-files-found: ignore
          retention-days: 30
```

**Why this works.** Each condition is evaluated against the job's status *at that
point*. On a green run: `success-report` and `evidence-always` upload, and
`failure-debug` is skipped. On a red run: `success-report` is skipped,
`evidence-always` and `failure-debug` upload, and the job still ends as failed —
`if: always()` rescues the step, not the job's verdict. `if-no-files-found:
ignore` on the failure bundle keeps a genuinely empty screenshots directory from
adding noise, and comparing `"$FORCE_FAILURE" = "true"` respects the fact that a
`boolean` input is still delivered as a string.

**Verify the failure mode the lab asks for.** Run twice from the Actions tab, once
with `force_failure` unchecked and once checked, and compare the artifact list on
each run page. Then remove `if: always()` from the evidence step and re-run with
the failure forced: the job fails at `behave` and every later step is skipped, so
the run page shows no evidence at all. That is the outcome the condition exists to
prevent.

**Common wrong answer.** Reaching for `continue-on-error: true` on the `behave`
step instead of `if: always()` on the uploads. The uploads then run — but the job
is reported green even though scenarios failed, so a broken suite merges. Use
`continue-on-error` only when you genuinely want the failure not to gate, and
express "collect evidence regardless" with `if: always()`. A related mistake is
assuming `always()` also covers cancellation politely — it does not, it forces the
step to run even when the run was cancelled. When a cancelled run should stop
cleanly, use `if: ${{ !cancelled() }}`; the `${{ }}` wrapper is required here
because a YAML scalar cannot start with a bare `!`.

</details>

---

[Solutions Index](./README.md) | [Module 10](../modules/module-10-artifacts.md) | [Course Home](../README.md)
