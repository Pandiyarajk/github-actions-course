# Module 12 — Solutions

![Module](https://img.shields.io/badge/Module-12-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 12](../modules/module-12-workflow-syntax.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — A.** Every job runs on a freshly provisioned runner with an empty workspace.
`needs` orders jobs and passes *outputs*; it does not share a filesystem. To move
a file, upload it as an artifact in `lint` and download it in `test` (Module 10),
or re-create it. **B** confuses permissions with existence — the file is not there
to `chmod`. **C** invents a relationship: `fail-fast` is a matrix setting and has
nothing to do with workspaces. **D** is wrong because an absolute path on runner A
means nothing on runner B; the workspace root even differs between them.

**2 — B.** The `secrets` context is not available in a job-level `if:`, which
accepts only `github`, `needs`, `vars`, and `inputs`. The expression resolves to an
empty value, `'' != ''` is false, and the job is skipped. The fix is to make the
decision somewhere that *can* see secrets — a step-level `if:`, or a prior job
whose step writes a boolean to `$GITHUB_OUTPUT`:

```yaml
  detect:
    runs-on: ubuntu-latest
    outputs:
      has_token: ${{ steps.check.outputs.has_token }}
    steps:
      - id: check
        env:
          ALLURE_TOKEN: ${{ secrets.ALLURE_TOKEN }}
        run: |
          if [ -n "$ALLURE_TOKEN" ]; then
            echo "has_token=true" >> "$GITHUB_OUTPUT"
          else
            echo "has_token=false" >> "$GITHUB_OUTPUT"
          fi

  publish:
    needs: detect
    if: ${{ needs.detect.outputs.has_token == 'true' }}
```

**A** is wrong — masking affects log output, not comparisons. **C** and **D** are
false; `!=` is valid and `contains()` is unnecessary.

**3 — C.** Writes to `$GITHUB_ENV` are collected when the step ends and applied to
**subsequent** steps. Within the writing step, the shell's own environment is
unchanged, so `$status` is empty. Use a plain shell variable if you need the value
in the same step, and `$GITHUB_ENV` (or better, `$GITHUB_OUTPUT` with an `id:`) to
hand it to later steps. **A** invents syntax. **B** is a style convention, not a
rule. **D** is wrong in both halves: `${{ env.status }}` does work in a later
step's `run:`, and it is not required.

**4.** `${{ inputs.browser }}` is a **GitHub expression**, substituted by the
runner while the step's script is being written to disk — before any shell exists.
`$BROWSER` is a **shell variable**, resolved by bash as the script executes. So the
expression's *text* becomes part of your program, which is why interpolating
attacker-controlled values (a branch name, an issue title, a dispatch input) into a
`run:` block is a command-injection hole. The safe pattern passes the value as data
through the environment and quotes it:

```yaml
- name: Run the smoke suite
  env:
    BROWSER: ${{ inputs.browser }}      # expression evaluated into an env var
  run: behave --tags=smoke -D browser="$BROWSER" your-solution-root-folder-name/features
```

The value is now a string in the environment rather than source code, and the
quotes keep spaces from splitting it into extra arguments.

**5.** For a `push` event, restrict on the fully qualified ref or the short name:

```yaml
- name: Publish Allure report
  if: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
```

`if: github.ref == 'main'` never matches because `github.ref` is the full ref —
`refs/heads/main` for a branch push, `refs/tags/v1.2.3` for a tag, and
`refs/pull/42/merge` for a pull request. The short name lives in
`github.ref_name`, so `github.ref_name == 'main'` is the other correct form. Adding
the `github.event_name` check matters because on a `pull_request` targeting main
`github.ref_name` is `42/merge`, not `main` — but `github.base_ref` *is* `main`, so
a condition written only against the branch name can fire on the wrong event.

## Lab 1 — Beginner

**Task:** Add a second step that prints `github.actor`.

<details>
<summary>Show solution</summary>

```yaml
name: Context Basics

on:
  workflow_dispatch:
    inputs:
      browser:
        description: "Browser to run the smoke suite on"
        required: true
        default: "chrome"

jobs:
  greet:
    runs-on: ubuntu-latest
    steps:
      - name: Use workflow input
        run: echo "Running Selenium smoke tests on ${{ inputs.browser }}"

      - name: Print the triggering user
        run: echo "Triggered by ${{ github.actor }} on ${{ github.ref_name }}"
```

**Why this works.** `github.actor` is part of the `github` context, which is
populated for every event without any setup — no checkout, no token, no
permissions. `github.ref_name` is included to show the short branch name alongside
it.

**Verify the failure mode the lab asks for.** Write the step as
`run: echo "Triggered by $GITHUB_ACTOR"` and it still works, because the runner
also exports the default environment variables. Now write
`run: echo "Triggered by ${{ github.author }}"`. There is no `author` key, so the
expression resolves to an empty string and the log reads `Triggered by` with
nothing after it — misspelled context keys fail silently, they do not error.

**Common wrong answer.** Expecting `github.actor` to be the pull request author.
It is whoever *triggered this run*, so on a re-run or a `schedule` event it can be
a different person, or `github-actions[bot]`. The PR author is
`github.event.pull_request.user.login`.

</details>

## Lab 2 — Intermediate

**Task:** Create two jobs where one depends on the other.

<details>
<summary>Show solution</summary>

```yaml
name: Dependent Jobs

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    outputs:
      # Data crosses the job boundary as an output, not as a file.
      lint_status: ${{ steps.pylint.outputs.lint_status }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Run static analysis
        id: pylint
        run: |
          pylint your-solution-root-folder-name/ --exit-zero | tee reports-pylint.txt
          echo "lint_status=completed" >> "$GITHUB_OUTPUT"

      - name: Upload the pylint report
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: pylint-report
          path: reports-pylint.txt
          retention-days: 7

  test:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Read the upstream output
        run: echo "Lint reported ${{ needs.lint.outputs.lint_status }}"

      # The file from the lint job is NOT on this runner -- fetch it.
      - name: Download the pylint report
        uses: actions/download-artifact@v8
        with:
          name: pylint-report
          path: incoming

      - name: Run Behave smoke suite
        run: behave --tags=smoke your-solution-root-folder-name/features
```

**Why this works.** `needs: lint` gives ordering *and* an implied success
requirement, so `test` runs only after a green `lint`. Two kinds of data cross the
boundary, and they use different mechanisms: small values as job outputs, files as
artifacts. Note that `test` repeats checkout and `setup-python` — a fresh runner
means a fresh everything, which is the cost of splitting jobs.

**Verify the failure mode the lab asks for.** Delete the download step and add
`run: cat reports-pylint.txt` to `test`. It fails with
`cat: reports-pylint.txt: No such file or directory`, even though a step in `lint`
created it minutes earlier. Then drop `--exit-zero` so `pylint` exits non-zero:
`lint` fails and `test` is **skipped** rather than failed, since `success()` is
implied on `needs`.

**Common wrong answer.** Assuming `needs` makes the jobs run sequentially *on the
same machine*, and using `needs` where a second step in one job was all that was
required. Split into jobs when you need different runners, different permissions,
or parallelism — not merely for tidier logs, because each split re-pays the setup
cost.

</details>

## Lab 3 — Challenge

**Task:** Add an `if:` condition so the Allure publish step runs only on `main`.

<details>
<summary>Show solution</summary>

```yaml
name: Publish Allure On Main

on:
  push:
    branches:
      - main
      - "release/**"
  pull_request:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Run Behave smoke suite
        env:
          ALLURE_RESULTS: your-solution-root-folder-name/reports/allure-results
        run: |
          mkdir -p "$ALLURE_RESULTS"
          echo '{"passed": 12, "failed": 0}' > "$ALLURE_RESULTS/summary.json"
          echo "behave --tags=smoke your-solution-root-folder-name/features"

      # Evidence is kept for every branch and every event.
      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30

      # Publishing happens only for a push to main.
      - name: Publish Allure report
        if: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
        run: echo "Publishing the Allure report for ${{ github.sha }}"

      - name: Record why publishing was skipped
        if: ${{ github.ref != 'refs/heads/main' }}
        run: |
          {
            echo "## Allure publish skipped"
            echo ""
            echo "- Event: ${{ github.event_name }}"
            echo "- Ref: ${{ github.ref }}"
            echo "- Ref name: ${{ github.ref_name }}"
          } >> "$GITHUB_STEP_SUMMARY"
```

**Why this works.** The condition tests two independent facts: the *event* is a
push, and the *ref* is exactly `refs/heads/main`. Checking both is what stops the
step firing on a pull request whose merge ref or base branch happens to mention
main. Uploading the results without a branch condition — but publishing with one —
is the usual production split: evidence everywhere, side effects only from the
protected branch. The skip-explaining step writes to `$GITHUB_STEP_SUMMARY`, so
"why did this not publish" is answerable from the run page rather than from the
logs.

**Verify the failure mode the lab asks for.** Open a pull request against `main`.
The publish step shows as skipped, the upload still runs, and the summary reports
`Ref: refs/pull/<n>/merge`. Now change the condition to
`if: github.ref == 'main'` and push straight to `main`: the step is skipped there
too, because `github.ref` is `refs/heads/main` and never the bare branch name.
Seeing it skip on the branch it was meant to allow is the point.

**Common wrong answer.** Relying on the `on.push.branches` filter alone and
omitting the step condition. The filter decides whether the *workflow* runs, and
this workflow also runs for `release/**` pushes, pull requests, and manual
dispatches — so without the step-level `if:` the publish fires from a release
branch too. A second variant is using `github.head_ref` for the check: it is set
only on pull request events and is empty on a push, so the condition can never be
true where you need it.

</details>

---

[Solutions Index](./README.md) | [Module 12](../modules/module-12-workflow-syntax.md) | [Course Home](../README.md)
