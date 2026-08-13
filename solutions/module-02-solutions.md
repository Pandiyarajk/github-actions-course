# Module 2 — Solutions

![Module](https://img.shields.io/badge/Module-2-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 2](../modules/module-02-workflow-naming.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** The `inputs` context is populated from the event payload, and a
`schedule` event has no inputs. The expression evaluates to an empty string, so
the title renders as `Smoke - ` with a dangling dash. Option A is the tempting
one: an input's `default:` is applied by the **dispatch form**, not by the
expression engine, so it does nothing for an event that never rendered a form.
There is no load error (C) — an undefined context property is an empty string,
not a failure. And `run-name` is not skipped (D): GitHub only falls back to the
default event-based title when `run-name` resolves to nothing but whitespace,
which `Smoke - ` is not. The fix is `${{ inputs.browser || 'chrome' }}`.

**2 — C.** `run-name: Nightly: Scheduled` is a YAML error: a plain (unquoted)
scalar cannot contain `: ` , because the parser reads the second colon as another
key separator and rejects the line. B is fine because the value is quoted, and D
is fine because the colon is inside a quoted string *inside* the expression,
which the YAML parser never sees as structure. A has no colon at all. The rule
is not "avoid colons" but "quote any scalar containing a colon-space".

**3 — A.** `>-` and `>` are both folded block scalars: newlines in the block
become spaces, which is what lets a long `${{ }}` expression span lines
readably. The `-` is a chomping indicator that strips the final newline. With
plain `>` the folded value keeps a trailing newline, which can surface as odd
trailing whitespace in the rendered title. `>-` is the correct default for
`run-name`. B describes `|-` versus `|` (literal block scalars, which keep
newlines and would break a multi-line expression). C and D are inventions.

**4.** It cannot work because `run-name` is evaluated **once, when the run is
created** — before any job is scheduled, let alone finished. At that moment no
step has executed, so there is no result to read; the contexts available are the
event-time ones (`github.*`, `inputs.*`, `vars.*`), not `needs.*` or
`job.status`. `run-name` is also not re-evaluated later, so nothing can update
it mid-run.

What to do instead: the run's pass/fail state is already conveyed by the run's
status icon and conclusion, so duplicating it in the title adds nothing. For
detail beyond pass/fail, write to the job summary (`$GITHUB_STEP_SUMMARY`), which
*is* produced at step time and renders on the run page — see
[Module 20](../modules/module-20-notifications.md). Put the run's **parameters**
in `run-name` (branch, browser, tags, server) and its **outcome** in the summary.

**5.** One workable answer:

```yaml
run-name: >-
  ${{
    github.event_name == 'schedule'
      && 'Regression - Nightly'
      || github.event_name == 'workflow_dispatch'
      && format('Regression - {0}', inputs.tags || 'regression')
      || format('Regression - {0}', github.ref_name)
  }}
```

Features used, and why:

- **`>-` folded scalar** so the expression can be indented across lines without
  embedding newlines in the title.
- **`&&` / `||` chaining** as a stand-in for a ternary, which the expression
  language does not have. `A && B || C` yields `B` when `A` is true and `C`
  otherwise — but only because `B` here is a **non-empty** string. If the middle
  value can be empty or `false`, the chain silently falls through to `C`.
- **`format()`** rather than string concatenation, which the expression language
  also lacks.
- **`inputs.tags || 'regression'`** because the manual case must survive an
  optional input left blank. `inputs` is empty for `push` and `schedule`, and
  even on a dispatch a non-`required` field can arrive as an empty string; the
  `||` covers both. Note that `github.ref_name` needs no fallback — it is
  populated for every event.

## Lab 1 — Beginner

**Task:** Add a `run-name` that appends `github.ref_name`.

<details>
<summary>Show solution</summary>

```yaml
name: Static Code Analysis
run-name: Static Code Analysis - ${{ github.ref_name }}

on:
  push:
    branches-ignore:
      - main

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Lint
        run: pylint your-solution-root-folder-name/ --exit-zero
```

**Why this works.** `name` and `run-name` are both top-level workflow keys, and
they serve different surfaces: `name` labels the workflow in the sidebar and in
required-check lists, `run-name` titles each individual run in the history.
`github.ref_name` is the short ref (`feature/IDAK-123`) as opposed to
`github.ref` (`refs/heads/feature/IDAK-123`), so the title stays readable. The
expression resolves at run creation, which is fine here — the branch is known
from the event payload.

**Verify the failure mode the lab asks for.** Change the line to include an
unquoted colon:

```text
run-name: Static Analysis: ${{ github.ref_name }}
```

The workflow now fails to load, and the Actions tab reports a YAML syntax error
for the file rather than running anything — the parser hit `: ` inside a plain
scalar and stopped. Fix it either by quoting the whole value
(`run-name: "Static Analysis: ${{ github.ref_name }}"`) or by moving the colon
inside the expression via `format()`. Reproducing this once is worth it, because
the same rule bites later in `run:` one-liners and `if:` conditions.

**Common wrong answer.** Using `github.ref` and getting
`Static Code Analysis - refs/heads/feature/IDAK-123`, or reaching for
`github.head_ref` on a `push` event — `head_ref` is populated only for
`pull_request` events and is empty otherwise.

</details>

## Lab 2 — Intermediate

**Task:** Build a `run-name` from two inputs with `||` fallbacks.

<details>
<summary>Show solution</summary>

```yaml
name: Auto Trigger
run-name: Auto Trigger - Server 1 | ${{ inputs.batch || 'batch1' }} | ${{ inputs.browser || 'chrome' }}

on:
  schedule:
    - cron: "30 1 * * *"
  workflow_dispatch:
    inputs:
      batch:
        description: "Test batch to execute"
        type: choice
        options:
          - batch1
          - batch2
        default: batch1
        required: false
      browser:
        description: "Browser for the Selenium run"
        type: choice
        options:
          - chrome
          - firefox
          - msedge
        default: chrome
        required: false

jobs:
  run-batch:
    runs-on: ubuntu-latest
    steps:
      - name: Show resolved parameters
        env:
          BATCH: ${{ inputs.batch || 'batch1' }}
          BROWSER: ${{ inputs.browser || 'chrome' }}
        run: |
          echo "Batch:   ${BATCH}"
          echo "Browser: ${BROWSER}"
```

**Why this works.** `||` in the expression language returns its left operand if
that operand is truthy and the right one otherwise, which makes it a defaulting
operator rather than a boolean-only one. Falsy values are the empty string, `0`,
and boolean `false` — so a missing input (empty string) falls through to the
literal. The pipe characters in the title are plain text; they need no escaping
because the value contains no `: `.

The same `|| 'default'` pair is repeated in the step's `env:` deliberately. The
`run-name` fallback fixes only the *title*; the step needs its own default or it
will run with an empty parameter.

**Verify the failure mode the lab asks for.** Delete both `|| '...'` fallbacks
and let the nightly `schedule` entry fire (or dispatch the workflow and clear
both optional fields). The run history shows
`Auto Trigger - Server 1 |  | ` — two empty segments, no error, no warning. This
is the silent-empty-expression failure: `inputs` does not exist for a `schedule`
event, and an input's `default:` belongs to the dispatch form, so it never
applies to a scheduled run.

**Common wrong answer.** Writing `${{ inputs.batch or 'batch1' }}` or
`${{ inputs.batch ?? 'batch1' }}`. Neither `or` nor `??` exists in the GitHub
Actions expression language; the whole expression fails to parse and the
workflow does not load. A subtler variant is `${{ github.event.inputs.batch }}`
for a `boolean` input — `github.event.inputs.*` values are always strings, so a
`false` checkbox arrives as the string `"false"`, which is truthy and defeats the
`||`. Use the typed `inputs` context for dispatch inputs.

</details>

## Lab 3 — Challenge

**Task:** Use a folded `>-` expression to title runs differently for schedule vs
manual.

<details>
<summary>Show solution</summary>

The finished version ships in
[`module-02-workflow-naming.yml`](../examples/module-02-workflow-naming.yml).
The core of it:

```yaml
name: Smoke Tests

run-name: >-
  ${{
    github.event_name == 'schedule'
      && 'Daily Smoke Tests: Scheduled'
      || format(
           'Smoke Tests - {0} | {1} | {2}',
           inputs.server || 'server4',
           inputs.browser || 'chrome',
           inputs.tags || 'smoke'
         )
  }}

on:
  schedule:
    - cron: "30 1 * * *"
  workflow_dispatch:
    inputs:
      server:
        description: "Self-hosted runner label"
        type: choice
        options:
          - server1
          - server2
          - server3
          - server4
        default: server4
        required: false
      browser:
        description: "Browser for the Selenium run"
        type: choice
        options:
          - chrome
          - firefox
          - msedge
        default: chrome
        required: false
      tags:
        description: "Behave tag expression"
        type: string
        default: smoke
        required: false

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

      - name: Install dependencies
        working-directory: your-solution-root-folder-name
        run: pip install -r requirements.txt

      - name: Run Behave suite
        working-directory: your-solution-root-folder-name
        env:
          BROWSER: ${{ inputs.browser || 'chrome' }}
          TAGS: ${{ inputs.tags || 'smoke' }}
        run: behave --tags="${TAGS}" -D "browser=${BROWSER}"
```

**Why this works.** Three mechanisms combine:

1. `>-` folds the indented block into one line, so the expression can be laid
   out over eleven lines and still be a single scalar. The stripped trailing
   newline keeps the title clean.
2. `github.event_name == 'schedule' && A || B` is the ternary substitute. It is
   sound here only because `A` is the non-empty literal
   `'Daily Smoke Tests: Scheduled'`.
3. `'Daily Smoke Tests: Scheduled'` contains `: ` but sits inside the
   expression's own single quotes, so the YAML parser sees only `${{ ... }}` and
   never treats the colon as structure. The same string written bare after
   `run-name:` would be a parse error.

**Verify the failure mode the lab asks for.** Two failures are worth
reproducing, in this order.

First, swap `>-` for `|-` (literal instead of folded). The newlines are now
preserved inside the value, so the expression is no longer a single line; the
workflow fails to load with an expression/syntax error rather than producing an
ugly title. That is the concrete difference between the two block styles.

Second, invert the condition to
`github.event_name == 'workflow_dispatch' && inputs.tags || 'Scheduled'` and
dispatch the workflow with `tags` left blank. Every dispatched run is now titled
`Scheduled`, because the middle operand evaluated to an empty string and the
chain fell through to the `||` branch. Nothing errors — the title is simply
wrong. This is why `A && B || C` is safe only when `B` cannot be falsy, and why
wrapping the middle value in `format(...)` (which always returns a non-empty
string here) is the defensive form.

**Common wrong answer.** Trying to branch with `if:` at the workflow level, or
expecting a job-level `name:` to change the run title. `if:` is a job/step key
and does not exist at workflow level; a job's `name:` labels the job row inside
the run, not the run itself. The run title has exactly one lever, `run-name`,
and it is evaluated once at run creation.

</details>

---

[Solutions Index](./README.md) | [Module 2](../modules/module-02-workflow-naming.md) | [Course Home](../README.md)
