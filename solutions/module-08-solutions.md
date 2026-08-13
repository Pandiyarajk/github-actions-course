# Module 8 — Solutions

![Module](https://img.shields.io/badge/Module-8-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 8](../modules/module-08-env-and-secrets.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** `$GITHUB_ENV` is a *file*. Appending to it asks the runner to add the
variable to the environment it builds for **subsequent** steps; the shell already
executing has no way to change its own environment retroactively. So the `echo`
prints an empty line. **A** is the natural assumption if you picture
`$GITHUB_ENV` as an assignment rather than a message to the runner. **C** would
happen if you had written `$GITHUB_ENV` unquoted in a way that lost the
redirection, but the code as given redirects correctly. **D** is wrong: the file
is very much writable — appending is the entire mechanism. Within one step, use an
ordinary shell variable; across steps, use `$GITHUB_ENV`.

**2 — B.** In PowerShell, environment variables live in the `Env:` drive and are
read as `$env:TEST_TAGS`. `$TEST_TAGS` is a perfectly legal *PowerShell* variable
that simply has never been assigned, and PowerShell expands an unset variable to
an empty string inside a double-quoted string. **A** is the belief that produces
the bug: `$VAR` is bash syntax, not portable syntax. **C** is the outcome people
expect and wish for — an error would make this trivial to find; instead you get a
successful step with a missing value, which is why it survives code review. **D**
is wrong: job `env` is passed to every step regardless of shell, and the same
variable is readable as `$env:TEST_TAGS` in that very step. Add
`Set-StrictMode -Version Latest` if you want undefined variables to error.

**3 — C.** `run-name` becomes the run's title in the UI and the run list. Log
masking does not protect it, so a secret interpolated there is displayed as the
name of the run to anyone who can see the Actions tab. **A** is the correct,
intended way to hand a secret to a job — assignment to `env` is how scripts
receive credentials, and the value is masked if it ever reaches a log. **B**
prints only the words "API_TOKEN is set"; `test -n` inspects the value without
emitting it, which is exactly the pattern to use. **D** is also correct usage:
`os.environ` reads the variable in-process and nothing is written to stdout.

**4.** Two things to check first:

1. **The producing step has no `id:`.** Without one there is nothing to hang
   `steps.meta` on, so `steps.meta.outputs.report_name` has no producer.
2. **The key names differ.** The written key is `report_name`; the reference must
   match it exactly, including underscores versus hyphens. `report-name` in one
   place and `report_name` in the other is the single most common version of this.

Worth checking third: whether the producing step actually ran. A skipped or failed
step writes no output, and a later step reading its output is not itself skipped.

The failure is silent because an expression that cannot be resolved evaluates to
the **empty string** rather than raising. `${{ steps.meta.outputs.report_name }}`
is syntactically valid whether or not `meta` exists, so the workflow loads, the
step runs, and you get a command with a missing argument. The defence is to assert
rather than assume:

```yaml
      - name: Consume the step output
        env:
          REPORT_NAME: ${{ steps.meta.outputs.report_name }}
        run: |
          if [ -z "$REPORT_NAME" ]; then
            echo "::error::report_name output was empty -- check the producing step's id"
            exit 1
          fi
          echo "Report will be named: $REPORT_NAME"
```

**5.** Add a preflight guard as the job's first step, checking presence through
the environment and failing with a workflow error annotation:

```yaml
      - name: Preflight -- required secrets are present
        env:
          ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
        run: |
          missing=""
          for name in ZEPHYR_SCALE_TOKEN JIRA_API_TOKEN; do
            # Indirect expansion: check the value without ever expanding it inline.
            if [ -z "${!name}" ]; then
              missing="${missing} ${name}"
            fi
          done
          if [ -n "$missing" ]; then
            echo "::error::Missing required secret(s):${missing}"
            exit 1
          fi
          echo "All required secrets are present."
```

Why it belongs at the top: the failure is a *configuration* problem, and it should
be reported in the first ten seconds of the run with the secret's name, not forty
minutes later as a `KeyError` or an HTTP 401 from inside a Python upload step.
A fork or a freshly cloned repository hits this constantly, and the guard turns
"the pipeline is broken" into "add this secret".

Why it must not print the value: masking is a safety net over log *output*, not a
guarantee. It replaces exact matches, so a value that gets transformed on the way
to the log — base64-encoded, URL-escaped, split across lines, or embedded in a
JSON blob — can slip past it. Checking length or emptiness gives you everything
you need to diagnose the problem and nothing an observer can use. For the same
reason the check reads the environment rather than interpolating
`${{ secrets.X }}` into the script body, where the value would become part of the
command text and could surface in a shell trace.

## Lab 1 — Beginner

**Task:** Add a job-level env value and read it in a bash step.

<details>
<summary>Show solution</summary>

```yaml
name: Env Basics

on: workflow_dispatch

env:
  REPORT_HOME: reports            # workflow level: visible to every job

jobs:
  demo:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      TEST_TAGS: smoke            # job level: visible to every step here
    steps:
      - name: Read the env values
        run: |
          echo "Reports go to : $REPORT_HOME"
          echo "Behave tags   : $TEST_TAGS"
          echo "Combined      : behave --tags=$TEST_TAGS -o $REPORT_HOME"
```

**Why this works.** Job-level `env` is materialised as real environment variables
in every step of that job, so bash reads them with ordinary `$VAR` expansion — no
`${{ }}` needed, and no interpolation happening before the shell runs. The
workflow-level entry is inherited because nothing narrower redefines it.

**Verify the failure mode the lab asks for.** Add the same step again with a
Windows shell, without changing the script:

```yaml
      - name: The same script under PowerShell
        shell: powershell
        run: |
          Write-Host "Behave tags: $TEST_TAGS"
```

It prints `Behave tags:` and nothing else. The step succeeds — exit code zero, no
warning — because `$TEST_TAGS` is an unassigned PowerShell variable, not a syntax
error. Change it to `$env:TEST_TAGS` and the value appears. An empty value where
you expected one is almost always this, or the `$GITHUB_ENV` timing issue in
Lab 2; it is very rarely a secret or variable that failed to arrive.

**Common wrong answer.** Writing `run: echo "Tags: ${{ env.TEST_TAGS }}"`. It
works, so it looks equivalent — but it substitutes the value into the script text
*before* the shell runs, which means anything in that value (a quote, a `$`, a
newline, a `;`) is interpreted as script. For ordinary strings it is merely
unnecessary; applied to a secret or to user-controlled input it is a script
injection. Read variables through the shell, not through interpolation.

</details>

## Lab 2 — Intermediate

**Task:** Create a value with `$GITHUB_ENV` and use it in a later step.

<details>
<summary>Show solution</summary>

```yaml
name: Dynamic Env

on: workflow_dispatch

jobs:
  label-the-run:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Compute a run label
        run: |
          label="bdd-${{ github.run_number }}-$(date -u +%Y%m%d)"
          echo "RUN_LABEL=${label}" >> "$GITHUB_ENV"
          echo "Wrote RUN_LABEL=${label}"

      - name: Use it in a later step
        run: |
          echo "This run is labeled: $RUN_LABEL"
          mkdir -p "reports/$RUN_LABEL"

      - name: Multi-line values need a delimiter
        run: |
          {
            echo "SUITE_NOTES<<SUITE_EOF"
            echo "tags: regression"
            echo "browser: chrome"
            echo "SUITE_EOF"
          } >> "$GITHUB_ENV"

      - name: Read the multi-line value
        run: echo "$SUITE_NOTES"
```

**Why this works.** Each step's `run:` is a fresh shell, but the runner rebuilds
the environment between steps from whatever accumulated in `$GITHUB_ENV`. So the
first step's `label` shell variable dies with its shell, while `RUN_LABEL`
survives as an environment variable for every later step in the job. The
heredoc-style form is required for any value containing a newline: the plain
`KEY=value` syntax is line-based, so a multi-line value would be misparsed. Note
that the interpolated `${{ github.run_number }}` sits inside a quoted assignment
rather than at the start of a line, keeping the generated script well-formed.

**Verify the failure mode the lab asks for.** Add a read into the *same* step that
writes:

```yaml
      - name: Try to read it immediately
        run: |
          echo "RUN_LABEL=bdd-immediate" >> "$GITHUB_ENV"
          echo "Same step sees: [$RUN_LABEL]"
```

It prints `Same step sees: []`. The write succeeded — the next step would see it —
but the environment of the currently running shell was fixed when the step
started. The square brackets are worth keeping while debugging: they make an
empty value visibly empty instead of looking like a formatting quirk.

**Common wrong answer.** Using `export RUN_LABEL=...` and expecting the next step
to see it. `export` affects the current shell and its children, and the step's
shell exits when the step ends. Nothing carries over except `$GITHUB_ENV`,
`$GITHUB_OUTPUT`, `$GITHUB_PATH`, and the workspace on disk. The related mistake
is `echo "RUN_LABEL=x" > "$GITHUB_ENV"` with a single `>`, which truncates the file
and discards every variable earlier steps had written — always append with `>>`.

</details>

## Lab 3 — Challenge

**Task:** Pass a secret into env and verify it with Python without echoing it,
then expose a step output for a later step.

<details>
<summary>Show solution</summary>

Compare your answer with the shipped example,
[`module-08-env-and-secrets.yml`](../examples/module-08-env-and-secrets.yml).

```yaml
name: Secrets And Outputs

on: workflow_dispatch

permissions:
  contents: read

jobs:
  publish-results:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    env:
      # Secrets reach the job by assignment to env. Job level, not workflow level:
      # only this job needs them.
      ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
      JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
      JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
    steps:
      - name: Checkout
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Verify the secrets are present without printing them
        run: |
          python - <<'PY'
          import os
          import sys

          required = ("ZEPHYR_SCALE_TOKEN", "JIRA_API_TOKEN", "JIRA_BASE_URL")
          missing = [name for name in required if not os.environ.get(name)]
          if missing:
              print(f"::error::Missing required secret(s): {', '.join(missing)}")
              sys.exit(1)
          for name in required:
              # Length only -- enough to spot a truncated paste, useless to a reader.
              print(f"{name}: present ({len(os.environ[name])} chars)")
          PY

      - name: Build the report name as a step output
        id: meta
        run: |
          label="allure-${{ github.run_id }}-${{ github.run_attempt }}"
          echo "report_name=${label}" >> "$GITHUB_OUTPUT"
          echo "Report name will be: ${label}"

      - name: Consume the step output
        env:
          REPORT_NAME: ${{ steps.meta.outputs.report_name }}
        run: |
          if [ -z "$REPORT_NAME" ]; then
            echo "::error::report_name output was empty -- is id: meta present?"
            exit 1
          fi
          mkdir -p "reports/allure-results"
          echo "placeholder" > "reports/allure-results/.keep"
          echo "Prepared results for $REPORT_NAME"

      - name: Upload the results under the generated name
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: ${{ steps.meta.outputs.report_name }}
          path: reports/allure-results/
          retention-days: 30
```

**Why this works.** There are three separate mechanisms doing three jobs, and the
lab is really about not confusing them:

- **`env` from `secrets`** hands credentials to a process. Python reads them with
  `os.environ` — the value never becomes part of a command line, so it cannot
  appear in a shell trace or a process listing.
- **`$GITHUB_OUTPUT` plus `id:`** publishes one small value under a name later
  steps can reference. Unlike `$GITHUB_ENV` it is addressable (`steps.meta.…`),
  which is what makes it usable in a `with:` block.
- **The `$GITHUB_ENV`/`$GITHUB_OUTPUT` split**: use env when many steps need the
  value ambiently, use an output when a specific step needs a specific value.

Including `github.run_attempt` in the artifact name matters because artifacts are
immutable: a re-run that uploads the same name fails rather than replacing.

**Verify the failure mode the lab asks for.** Two things to reproduce, in order.

First, delete `id: meta`. `steps.meta.outputs.report_name` becomes an empty
string, the guard fires, and the step fails with your own error annotation naming
the cause. Remove the guard and try again to see what it was protecting you from:
`actions/upload-artifact@v7` now receives an empty `name` and fails inside the
action instead, with a validation message about the artifact name rather than
anything pointing at the missing `id`.

Second, deliberately leak the secret — `run: echo "$JIRA_API_TOKEN"`. The log
shows `***`, which proves masking works and is *also* the trap: masking is
post-processing over exact matches, so the same value transformed on the way out
(base64-encoded, URL-escaped, or embedded in a JSON body your script prints) is
not recognised and is not masked. Do not treat `***` as permission to print
secrets.

**Common wrong answer.** Declaring the secrets at **workflow** level so "every job
can have them". Every job then carries credentials it does not need, including
jobs whose logs are read far more casually, and a leak in any of them is a leak of
the release token. Scope secrets to the job that uses them — and scope them to a
`step`'s `env` if only one step needs them.

The other frequent wrong answer is `python -c "import os; print(os.environ['ZEPHYR_SCALE_TOKEN'])"`
as a "quick check that it arrived". It relies entirely on masking to save you, it
tells you nothing that a length check does not, and the moment someone adds a
pipe or a JSON wrapper around it the value is in the log in the clear.

</details>

---

[Solutions Index](./README.md) | [Module 8](../modules/module-08-env-and-secrets.md) | [Course Home](../README.md)
