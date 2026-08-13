# Module 2: Naming Workflows with `name` and Dynamic `run-name`

![Module](https://img.shields.io/badge/Module-2-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20A%20Components-1f6feb?style=flat-square) ![Level](https://img.shields.io/badge/Level-Beginner-2da44e?style=flat-square) ![Time](https://img.shields.io/badge/Time-90%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 1](./module-01-ci-foundations.md) | [Next: Module 3](./module-03-workflow-triggers.md)
> Level: **Beginner** | Time: **90 min** | Example workflow: [`module-02-workflow-naming.yml`](../examples/module-02-workflow-naming.yml)
> Solutions: [`module-02-solutions.md`](../solutions/module-02-solutions.md)

## Learning Objectives

- Set a static workflow `name`.
- Build a dynamic per-run title with `run-name`.
- Use expressions, `format()`, fallbacks, and event branching in `run-name`.
- Make run history self-describing for triage.

## Key Concepts

`name`, `run-name`, expressions, `format()`, `||` fallback, `github.event_name`, folded scalars (`>-`)

## Expected Outcome

You can give a workflow a clear static name and a dynamic run title that summarizes each run at a glance.

## Concept Flow

```text
name (static, in sidebar) + run-name (per run) -> Expression resolved at start -> Title in run history
```

---

## ELI5 Explanation

`name` is the label on the workflow's folder. `run-name` is the label you write on each individual run inside that folder — so instead of a list of identical names, each run can say what it actually did ("Smoke Tests - server1 | chrome | smoke").

## Technical Explanation

`name` is a static string shown in the Actions sidebar and required-check lists. `run-name` sets the title of each run and may contain `${{ }}` expressions evaluated when the run starts. Because expressions run at start time, `run-name` can read `github.event_name`, `inputs.*`, `github.ref_name`, and `github.event.*`. The `format('...{0}...', a)` function substitutes positional values, and `||` provides fallbacks for missing inputs (e.g. scheduled runs have no `inputs`). YAML folded scalars (`>-`) let a long expression span multiple lines for readability.

## Real-World Use Case

A smoke-test workflow runs both on a schedule and manually. Scheduled runs should read "Daily Smoke Tests: Scheduled," while manual runs should read "Smoke Tests - server1 | chrome | smoke" using the chosen inputs — so the run history is instantly understandable.

## When To Use

- Many runs of one workflow that need to be told apart.
- Runs parameterized by inputs (server, browser, tags, batch).
- Event-driven workflows where the event should appear in the title.

## When NOT To Use

- A workflow that runs rarely and needs no per-run distinction (static `name` is enough).
- Putting secrets or sensitive values into a run title (titles are visible).

## Common Mistakes

- Using `inputs.x` for scheduled runs (no inputs exist) without a `||` fallback.
- Forgetting that `run-name` expressions resolve at start, not per step.
- Mixing `>` (folded, keeps a trailing newline) vs `>-` (folded, strips it) and getting odd spacing.
- Putting a colon in plain text without quoting, breaking YAML.

## Debugging Tips

- A run titled with a dangling separator (`Smoke - `) means an expression resolved to an empty string — usually `inputs.*` on a `schedule` or `push` run. Add a `|| 'default'` fallback.
- If the whole `run-name` is missing and the run shows the default event title, the expression resolved to nothing but whitespace.
- A workflow that fails to load right after a `run-name` edit is almost always an unquoted `: ` in the value — quote the scalar or move the colon inside `format()`.
- `run-name` is evaluated once at run creation, so echo the same expression in a step to see exactly what it resolved to.
- Test title variants with `workflow_dispatch` rather than waiting for the real event.

## Naming Patterns Reference

| Goal | `run-name` |
| --- | --- |
| Static text + ref | `Static Code Analysis - ${{ github.ref_name }}` |
| Inputs with fallbacks | `Auto Trigger - Server 1 \| ${{ inputs.batch \|\| 'batch1' }} \| ${{ inputs.browser \|\| 'chrome' }}` |
| Schedule vs manual | folded expression choosing a title by `github.event_name` |
| Branch create/delete | folded expression using `format()` per event |

## Minimal Workflow Example

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
      - name: Lint
        run: echo "pylint your-solution-root-folder-name/ --exit-zero"
```

### YAML Explanation

- `name` is the static workflow name in the sidebar.
- `run-name` appends the branch (`github.ref_name`) so each run shows its branch.

### Step-by-Step Execution

1. A push to a feature branch starts the workflow.
2. `run-name` resolves to `Static Code Analysis - feature/IDAK-123`.
3. The run history shows that branch-specific title.

## Production Workflow Example

The full example sets `name: Smoke Tests` and a dynamic `run-name` that differs for scheduled vs manual runs. See [`module-02-workflow-naming.yml`](../examples/module-02-workflow-naming.yml).

### Schedule vs Manual Title

```yaml
name: Smoke Tests

run-name: >-
  ${{
    github.event_name == 'schedule'
      && 'Daily Smoke Tests: Scheduled'
      || format(
           'Smoke Tests - {0} | {1} | {2}',
           github.event.inputs.server || 'server4',
           github.event.inputs.browser || 'chrome',
           github.event.inputs.tags || 'smoke'
         )
  }}
```

- On a `schedule` run, the title is `Daily Smoke Tests: Scheduled`.
- On a manual run, `format()` builds `Smoke Tests - server1 | chrome | smoke` from the inputs, falling back to defaults when an input is empty.

### Inputs With Fallbacks

```yaml
run-name: Auto Trigger - Server 1 | ${{ inputs.batch || 'batch1' }} | ${{ inputs.browser || 'chrome' }}
```

`||` supplies a default when the input is empty, so scheduled or partial runs still get a readable title.

### Branch Create / Delete Title

```yaml
run-name: >-
  ${{
    github.event_name == 'create'
      && format('Branch created: {0}', github.ref_name)
      || github.event_name == 'delete'
      && format('Branch deleted: {0}', github.event.ref)
      || 'Branch Events'
  }}
```

This chooses a different title per event type, falling back to `Branch Events`.

### Folded Scalars: `>` vs `>-`

| Style | Meaning |
| --- | --- |
| `>-` | Fold newlines into spaces and strip the final newline (preferred for `run-name`). |
| `>` | Fold newlines into spaces but keep a trailing newline. |

Use `>-` for multi-line `run-name` expressions so the title has no trailing blank line.

### Expected Output

- The Actions sidebar shows `Smoke Tests`.
- Scheduled runs are titled `Daily Smoke Tests: Scheduled`.
- Manual runs are titled from their inputs, e.g. `Smoke Tests - server1 | chrome | smoke`.

## Quiz

1. A workflow runs on both `schedule` and `workflow_dispatch` with `run-name: Smoke - ${{ inputs.browser }}`. What do the scheduled runs show in the run history?
   - **A.** `Smoke - chrome`, because the input's `default` still applies.
   - **B.** `Smoke - ` with nothing after the dash, because a scheduled run has no `inputs` context to read.
   - **C.** The workflow fails to load, because `inputs` is undefined for `schedule`.
   - **D.** The static `name` is shown instead, because `run-name` is skipped.

2. Which `run-name` line is invalid YAML?
   - **A.** `run-name: Smoke Tests - ${{ github.ref_name }}`
   - **B.** `run-name: "Nightly: Scheduled"`
   - **C.** `run-name: Nightly: Scheduled`
   - **D.** `run-name: ${{ format('Nightly: {0}', github.ref_name) }}`

3. What is the difference between `>-` and `>` as the block style for a multi-line `run-name`?
   - **A.** `>-` folds newlines into spaces and strips the trailing newline; `>` folds but keeps a trailing newline, which can leave odd spacing in the title.
   - **B.** `>-` preserves newlines literally; `>` folds them.
   - **C.** `>-` allows `${{ }}` expressions; `>` does not.
   - **D.** They are identical; `-` is decorative.

4. A teammate wants `run-name` to say `Smoke Tests - PASSED` or `Smoke Tests - FAILED` depending on the suite result. Explain why that cannot work, and what they should do instead.

5. Write a single `run-name` for a workflow triggered by `push`, `schedule`, and `workflow_dispatch` that reads `Regression - <branch>` for pushes, `Regression - Nightly` for scheduled runs, and `Regression - <tags>` for manual runs. Explain which expression features you used and why the manual case needs a fallback.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add `run-name` that appends `github.ref_name`. | Run title includes the branch name. |
| Intermediate | Build a `run-name` from two inputs with `\|\|` fallbacks. | Run title shows the chosen or default values. |
| Challenge | Use a folded `>-` expression to title runs differently for schedule vs manual. | Scheduled and manual runs show distinct titles. |

Solutions: [`solutions/module-02-solutions.md`](../solutions/module-02-solutions.md)

---

[Previous: Module 1](./module-01-ci-foundations.md) | [Module Index](./README.md) | [Next: Module 3](./module-03-workflow-triggers.md)
