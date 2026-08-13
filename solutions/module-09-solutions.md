# Module 9 — Solutions

![Module](https://img.shields.io/badge/Module-9-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 9](../modules/module-09-running-scripts.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — C.** With no `shell:` key, GitHub picks a default per runner OS: `bash` on
Linux and macOS, PowerShell (`pwsh`) on Windows. **A** is the misconception that
costs the most time — bash is *available* on the Windows runners, but only if you
ask for it with `shell: bash`. **B** is wrong because `cmd` is never the default;
you must set `shell: cmd` explicitly. **D** is wrong because `defaults.run.shell`
is optional — it *overrides* the built-in default rather than replacing the
concept of one.

**2 — B.** Quoting the heredoc marker (`<<'PY'`) tells the shell to pass the body
through literally, so `$HOME` reaches Python as four characters. With an unquoted
marker (**C**) the shell *does* expand `$VAR`, `` `cmd` `` and `\` sequences
inside the body — heredocs are not literal by default, which is the trap. **A**
uses `HOME` as the marker name, which works as a delimiter but is unquoted, so
expansion still happens. **D** is wrong on the facts: `<<"PY"` also suppresses
expansion, and `<<'PY'` is perfectly valid.

**3 — A.** A step's status is its command's exit code. `sys.exit(1)` propagates
`1` out of `python`, the step is marked failed, and the remaining steps are
skipped unless they carry `if: always()` (or the failing step carries
`continue-on-error: true`). **B** confuses Python-level and process-level
failure: an uncaught exception fails only because the interpreter *also* exits
non-zero. **C** and **D** describe behaviour that does not exist — there is no
"ignored exit code" position in a job.

**4.** The file is committed without its executable bit, so `./scripts/...`
cannot be executed and the shell reports a permission error (`Permission
denied`). Git stores only one permission bit, and a file added from Windows
usually lands as mode `100644`. Two fixes:

```yaml
# Fix 1 — set the bit on the runner, every run:
- name: Run checks
  run: |
    chmod +x scripts/run-checks.sh
    ./scripts/run-checks.sh smoke

# Fix 2 — do not execute the file at all; hand it to an interpreter:
- name: Run checks
  run: bash scripts/run-checks.sh smoke
```

A third, permanent fix is to record the bit in Git once with
`git update-index --chmod=+x scripts/run-checks.sh` and commit, after which
neither workaround is needed.

**5.** `${{ inputs.tag }}` is a **GitHub expression**. It is substituted by the
runner while the script is being generated, *before* any shell starts — the shell
never sees the `${{ }}`, only the resulting text. `$TAG` is a **shell variable**,
resolved by bash while the script runs. That ordering is why interpolating an
expression directly into a command is dangerous: a value like
`smoke"; rm -rf .; echo "` is pasted into the script verbatim and then executed.
The safe pattern moves the expression into `env:` and lets the shell read it:

```yaml
- name: Run the suite
  env:
    TEST_TAG: ${{ inputs.tag }}     # expression evaluated into an env var
  run: behave --tags="$TEST_TAG" --no-capture
```

The value now arrives as data through the environment rather than as source code,
and quoting `"$TEST_TAG"` protects against spaces.

## Lab 1 — Beginner

**Task:** Add a step that runs `python -c` to print today's date.

<details>
<summary>Show solution</summary>

```yaml
name: Print Today

on: workflow_dispatch

jobs:
  date:
    runs-on: ubuntu-latest
    steps:
      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Print today's date with inline Python
        run: python -c "import datetime; print('Today is', datetime.date.today().isoformat())"
```

**Why this works.** `python -c` takes the whole program as one argument, so no
file is needed. The outer double quotes are consumed by bash and Python receives
`import datetime; print(...)`; the inner quotes stay single so they survive that
pass. `actions/setup-python@v7` guarantees which interpreter answers to `python`
rather than relying on whatever the runner image ships.

**Verify the failure mode the lab asks for.** Swap the quoting so both levels use
double quotes:

```yaml
      - run: python -c "import datetime; print("Today is", datetime.date.today())"
```

Bash closes the string at the inner `"`, so Python receives
`import datetime; print(Today is, datetime.date.today())` and fails with a
`SyntaxError`. The lesson is that two languages are quoting the same line.

**Common wrong answer.** Using `run: date` and calling it done. It prints a date,
but it exercises the shell rather than Python, so nothing in the step would break
if `setup-python` were removed — the point of the lab is the Python invocation.

</details>

## Lab 2 — Intermediate

**Task:** Add a `.sh` script that takes a tag argument and run it.

<details>
<summary>Show solution</summary>

`scripts/run-suite.sh` (compare with the shipped
[`examples/scripts/run-checks.sh`](../examples/scripts/run-checks.sh)):

```bash
#!/usr/bin/env bash
# Author: Pandiyaraj Karuppasamy
# Date: Aug-13-2026
set -euo pipefail

TAG="${1:?usage: run-suite.sh <behave-tag>}"

echo "Behave tag: ${TAG}"
echo "pylint your-solution-root-folder-name/ --exit-zero"
echo "behave --tags=${TAG} --no-capture"
```

Workflow:

```yaml
name: Run Shell Script

on:
  workflow_dispatch:
    inputs:
      tag:
        description: "Behave tag to run"
        type: string
        default: smoke
        required: true

jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Run the shell script
        env:
          TEST_TAG: ${{ inputs.tag }}
        run: |
          chmod +x scripts/run-suite.sh
          ./scripts/run-suite.sh "$TEST_TAG"
```

**Why this works.** The checkout is what puts the script on disk. `chmod +x`
covers the committed-without-the-bit case. `set -euo pipefail` makes the script
fail loudly: `-e` aborts on any non-zero command, `-u` on an unset variable,
`pipefail` on a failure anywhere in a pipe. `${1:?...}` turns a missing argument
into an immediate, self-documenting failure instead of an empty tag.

**Verify the failure mode the lab asks for.** Call the script with no argument:

```yaml
      - run: ./scripts/run-suite.sh
```

`${1:?usage: ...}` aborts with a non-zero status and the usage text on stderr, so
the step fails. Now delete `set -euo pipefail` and change `${1:?...}` back to
`${1}` — the script prints `behave --tags= --no-capture` and *passes*, which is
the silent version of the same bug.

**Common wrong answer.** `run: scripts/run-suite.sh "$TEST_TAG"` without the
leading `./`. The current directory is not on `PATH` on the runner, so bash
reports `command not found` — which reads like the file is missing rather than
like a `PATH` issue.

</details>

## Lab 3 — Challenge

**Task:** Add a Windows job that runs the same Python file via `cmd`, passing the
tag through a `%VAR%` environment variable.

<details>
<summary>Show solution</summary>

```yaml
name: Cross-Platform Scripts

on:
  workflow_dispatch:
    inputs:
      tag:
        description: "Behave tag to run"
        type: string
        default: smoke
        required: true

permissions:
  contents: read

jobs:
  linux:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Run the Python file (bash reads $TEST_TAG)
        env:
          TEST_TAG: ${{ inputs.tag }}
        run: python examples/scripts/hello.py --tag "$TEST_TAG"

  windows:
    # A self-hosted Windows box would be `runs-on: [self-hosted, windows, server1]`.
    runs-on: windows-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Run the same Python file from cmd (reads %TEST_TAG%)
        shell: cmd
        env:
          TEST_TAG: ${{ inputs.tag }}
        run: |
          echo Current directory: %CD%
          python examples\scripts\hello.py --tag %TEST_TAG%
```

**Why this works.** One Python file serves both operating systems because the
*script* is portable and only the *invocation* differs. `env:` is shell-agnostic:
the same mapping is readable as `$TEST_TAG` in bash and `%TEST_TAG%` in `cmd`,
which is why passing values through the environment beats interpolating them into
the command. `shell: cmd` is mandatory on the Windows job — without it the block
is handed to PowerShell, where `%TEST_TAG%` is a meaningless literal and `%` is
the alias for `ForEach-Object`.

**Verify the failure mode the lab asks for.** Delete `shell: cmd` from the
Windows step. PowerShell runs the block, `%CD%` and `%TEST_TAG%` are not
expanded, and `--tag %TEST_TAG%` reaches `argparse` as that literal string — so
`hello.py` cheerfully prints `Selected Behave tag: %TEST_TAG%` and the step
*passes*. A passing step with wrong output is the failure mode worth internalising
here. Then try `run: python examples/scripts/hello.py` under `shell: cmd` with a
`$TEST_TAG` reference to see the opposite mistake fail outright.

**Common wrong answer.** Writing one job with `runs-on: ${{ matrix.os }}` and a
single bash-syntax step for both. It works — but only because bash is installed
on the Windows runner, so it proves nothing about `cmd`, and it hides the path
separator and variable-syntax differences the lab is about. If you do use a
matrix, branch the step with `if: runner.os == 'Windows'` so each shell gets its
own syntax.

</details>

---

[Solutions Index](./README.md) | [Module 9](../modules/module-09-running-scripts.md) | [Course Home](../README.md)
