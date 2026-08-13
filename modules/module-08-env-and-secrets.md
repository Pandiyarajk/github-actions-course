# Module 8: Environment Variables and Secrets — Setting and Using Them

![Module](https://img.shields.io/badge/Module-8-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20A%20Components-1f6feb?style=flat-square) ![Level](https://img.shields.io/badge/Level-Beginner-2da44e?style=flat-square) ![Time](https://img.shields.io/badge/Time-120%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 7](./module-07-jobs-and-steps.md) | [Next: Module 9](./module-09-running-scripts.md)
> Level: **Beginner** | Time: **120 min** | Example workflow: [`module-08-env-and-secrets.yml`](../examples/module-08-env-and-secrets.yml)
> Solutions: [`module-08-solutions.md`](../solutions/module-08-solutions.md)

## Learning Objectives

- Call secrets into `env` at workflow, job, and step level.
- Set static and dynamic environment variables.
- Pass values to later steps with `$GITHUB_ENV` and step outputs (`$GITHUB_OUTPUT`).
- Read env in bash (`$VAR`), PowerShell (`$env:VAR`), and cmd (`%VAR%`).
- Consume secrets without leaking them into logs.

## Key Concepts

`env`, `secrets` context, `$GITHUB_ENV`, `$GITHUB_OUTPUT`, step outputs, masking, scope precedence

## Expected Outcome

You can set environment variables anywhere they are needed, pull secrets in safely, and read them correctly on Linux and Windows runners.

## Concept Flow

```text
secrets / inputs / literals -> env (workflow|job|step) -> shell variable -> used in run command
                              \-> $GITHUB_ENV (dynamic, later steps)
                              \-> $GITHUB_OUTPUT (step output, referenced by id)
```

---

## ELI5 Explanation

Environment variables are labeled jars your steps can read from. Some jars you fill yourself (`env`), some you fill at runtime (`$GITHUB_ENV`), and some hold secret ingredients (`secrets`) that GitHub keeps hidden in the logs. Each step reads from the jars using the syntax its shell understands.

## Technical Explanation

`env` maps names to values and can be declared at workflow, job, or step level — the narrowest scope wins. Secrets live in the `secrets` context (`${{ secrets.NAME }}`) and are masked in logs; you expose a secret to a script by assigning it to an `env` entry. To create a variable **at runtime** so later steps can use it, append `KEY=VALUE` to the file referenced by `$GITHUB_ENV`. To hand a single value to a later step, append to `$GITHUB_OUTPUT` in a step with an `id`, then read `steps.<id>.outputs.<key>`. Inside a `run:` block, read variables with the shell's syntax: `$VAR` (bash), `$env:VAR` (PowerShell), `%VAR%` (cmd).

## Real-World Use Case

A BDD job needs `ZEPHYR_SCALE_TOKEN` and `JIRA_API_TOKEN` to publish results. These are stored as repository secrets, exposed to the job via `env`, and consumed by a Python script — verified for presence but never printed. The job also builds a `RUN_LABEL` at runtime and reuses it to name the Allure report artifact.

## When To Use

- Sharing config across steps (`REPORT_HOME`, `TEST_TAGS`).
- Passing tokens/credentials to scripts via `env`.
- Computing a value once and reusing it in later steps.

## When NOT To Use

- Storing secrets in plain workflow-level `env` you might echo.
- Hardcoding tokens in YAML instead of using `secrets`.
- Using step outputs for large blobs (use artifacts instead).

## Common Mistakes

- Echoing a secret (`echo "$TOKEN"`) — it may appear in logs.
- Using bash `$VAR` syntax in a Windows PowerShell/cmd step.
- Expecting a `$GITHUB_ENV` value to exist in the **same** step that set it (it applies to later steps).
- Forgetting an `id:` on a step whose `$GITHUB_OUTPUT` you want to read.
- Putting secrets in `run-name` or step names (they are visible).

## Debugging Tips

- When a variable looks empty, print its *length* rather than its value: `echo "len=${#API_TOKEN}"`. That distinguishes "never reached the job" from "wrong value" without revealing a secret.
- `env | sort` (bash) or `Get-ChildItem Env: | Sort-Object Name` (PowerShell) as a temporary step is the fastest way to see which scope actually won. Secret values are masked in that output, so it is safe to leave in while debugging.
- Three asterisks (`***`) in a log are not a bug — that is masking working. Seeing them where you did not expect them means a secret is being interpolated somewhere you did not intend.
- A `$GITHUB_ENV` value that reads as empty is nearly always being read in the *same* step that wrote it. Split the write and the read into two steps and it appears.
- A step output that resolves to nothing usually means the producing step has no `id:`, or the key name differs between the `>> "$GITHUB_OUTPUT"` line and the `steps.<id>.outputs.<key>` reference. Both fail silently rather than erroring.
- On Windows, an empty value in a `run:` block often just means the wrong syntax for the shell: `$VAR` is a bash-ism and expands to nothing in PowerShell, which needs `$env:VAR`.
- Multi-line values written to `$GITHUB_ENV` need heredoc delimiter syntax; a bare `KEY=line1\nline2` truncates at the first newline or errors on the stray line.

## Reference Tables

### Where to define env

| Scope | Visible to | Example |
| --- | --- | --- |
| Workflow `env` | All jobs and steps | `REPORT_HOME: reports` |
| Job `env` | One job's steps | `ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}` |
| Step `env` | That single step | `BROWSER: chrome` |
| `$GITHUB_ENV` | Later steps in the same job | `echo "RUN_LABEL=x" >> "$GITHUB_ENV"` |
| `$GITHUB_OUTPUT` | Steps that reference the step `id` | `echo "k=v" >> "$GITHUB_OUTPUT"` |

### Reading env per shell

| Shell | Read syntax | Example |
| --- | --- | --- |
| bash (Linux default) | `$VAR` | `echo "$TEST_TAGS"` |
| PowerShell (Windows default) | `$env:VAR` | `Write-Host $env:TEST_TAGS` |
| cmd | `%VAR%` | `echo %TEST_TAGS%` |

## Minimal Workflow Example

```yaml
name: Env Basics

on: workflow_dispatch

env:
  REPORT_HOME: reports          # workflow-level, shared everywhere

jobs:
  demo:
    runs-on: ubuntu-latest
    env:
      TEST_TAGS: smoke          # job-level
      API_TOKEN: ${{ secrets.API_TOKEN }}   # secret into env
    steps:
      - name: Use env values
        run: |
          echo "Reports go to: $REPORT_HOME"
          echo "Behave tags:   $TEST_TAGS"
          # Use the secret without printing it:
          test -n "$API_TOKEN" && echo "API_TOKEN is set"
```

### YAML Explanation

- Workflow `env.REPORT_HOME` is visible to every step.
- Job `env.TEST_TAGS` is a literal; `env.API_TOKEN` pulls a secret.
- The step reads each with `$VAR` and checks the secret is non-empty without echoing it.

### Step-by-Step Execution

1. The job starts with the workflow and job env applied.
2. The step prints the non-secret values.
3. It confirms `API_TOKEN` is set without revealing it.

## Production Workflow Example

The full example shows secrets into env, dynamic `$GITHUB_ENV`, step outputs, and reading env across bash, PowerShell, and cmd. See [`module-08-env-and-secrets.yml`](../examples/module-08-env-and-secrets.yml).

### Call Secrets Into Env

```yaml
jobs:
  linux-env:
    runs-on: ubuntu-latest
    env:
      ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
      JIRA_EMAIL: ${{ secrets.JIRA_EMAIL }}
      JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
      JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
```

Secrets are masked in logs. Assigning them to `env` is how scripts and tools receive them.

### Set a Dynamic Env Variable

```yaml
- name: Create a dynamic env variable
  run: echo "RUN_LABEL=bdd-${{ github.run_number }}" >> "$GITHUB_ENV"

- name: Use it in a later step
  run: |
    echo "This run is labeled: $RUN_LABEL"
```

`$GITHUB_ENV` makes the value available to **subsequent** steps, not the step that wrote it.

### Step-Level Env (override / add)

```yaml
- name: Step-scoped env
  env:
    BROWSER: chrome
  run: echo "Running $TEST_TAGS on $BROWSER"
```

### Consume a Secret Safely

```yaml
- name: Verify a secret without printing it
  run: |
    set +x
    python -c "import os; assert os.environ['ZEPHYR_SCALE_TOKEN'], 'missing token'"
    echo "ZEPHYR_SCALE_TOKEN is present (value hidden)"
```

`set +x` stops the shell from tracing the command with the value; never `echo` the secret itself.

### Pass a Value With Step Outputs

```yaml
- name: Produce a step output
  id: meta
  run: echo "report_name=allure-$RUN_LABEL" >> "$GITHUB_OUTPUT"

- name: Consume the step output
  run: |
    echo "Report will be named: ${{ steps.meta.outputs.report_name }}"
```

### Read Env on Windows

```yaml
- name: Read env in PowerShell
  shell: powershell
  run: |
    Write-Host "Behave tags: $env:TEST_TAGS"

- name: Read env in cmd
  shell: cmd
  run: |
    echo Behave tags: %TEST_TAGS%
```

### Expected Output

- Non-secret env values print normally.
- The secret check confirms presence without revealing the value.
- `RUN_LABEL` set via `$GITHUB_ENV` is readable in later steps.
- The step output feeds the artifact name.
- PowerShell and cmd read the same job env with their own syntax.

## Quiz

1. A step runs `echo "RUN_LABEL=bdd-42" >> "$GITHUB_ENV"` and then, in the **same** step, `echo "$RUN_LABEL"`. What is printed?
   - **A.** `bdd-42` — the file is read immediately.
   - **B.** An empty line — `$GITHUB_ENV` applies to subsequent steps, not the step that wrote it.
   - **C.** The literal text `RUN_LABEL=bdd-42`.
   - **D.** The step fails because `$GITHUB_ENV` is read-only.

2. A Windows step declares `shell: powershell` and runs `Write-Host "Tags: $TEST_TAGS"`, where `TEST_TAGS` is set in job-level `env`. What happens?
   - **A.** It prints the tags correctly; `$VAR` is portable across shells.
   - **B.** It prints `Tags:` with nothing after it — PowerShell needs `$env:TEST_TAGS`, since `$TEST_TAGS` is an undefined PowerShell variable.
   - **C.** The step fails with an undefined-variable error.
   - **D.** Job-level `env` is not visible to PowerShell steps at all.

3. Which of these actually leaks a secret's value where a reader can see it?
   - **A.** `env: API_TOKEN: ${{ secrets.API_TOKEN }}` on a job.
   - **B.** `test -n "$API_TOKEN" && echo "API_TOKEN is set"`.
   - **C.** `run-name: Deploy with ${{ secrets.API_TOKEN }}`.
   - **D.** Passing the token to a Python script through `os.environ`.

4. A step writes `echo "report_name=allure-nightly" >> "$GITHUB_OUTPUT"` and a later step reads `${{ steps.meta.outputs.report_name }}`, which resolves to nothing — with no error. List the two things you would check first, and explain why the failure is silent.

5. Your team wants a workflow to fail fast with a clear message when a required secret is missing, rather than failing deep inside a Python upload step. Describe how you would implement that check and why it must not print the secret.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a job-level env value and read it in a bash step. | Step prints the value. |
| Intermediate | Create a value with `$GITHUB_ENV` and use it in a later step. | Later step reads the runtime value. |
| Challenge | Pass a secret into env and verify it with Python without echoing it, then expose a step output for a later step. | Secret check passes silently; later step reads the output. |

Solutions: [`solutions/module-08-solutions.md`](../solutions/module-08-solutions.md)

---

[Previous: Module 7](./module-07-jobs-and-steps.md) | [Module Index](./README.md) | [Next: Module 9](./module-09-running-scripts.md)
