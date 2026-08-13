# Module 9: Running Python, Shell, Bash, and CMD in Workflows

![Module](https://img.shields.io/badge/Module-9-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20A%20Components-1f6feb?style=flat-square) ![Level](https://img.shields.io/badge/Level-Beginner-2da44e?style=flat-square) ![Time](https://img.shields.io/badge/Time-90%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 8](./module-08-env-and-secrets.md) | [Next: Module 10](./module-10-artifacts.md)
> Level: **Beginner** | Time: **90 min** | Example workflow: [`module-09-running-scripts.yml`](../examples/module-09-running-scripts.yml)
> Solutions: [`module-09-solutions.md`](../solutions/module-09-solutions.md)

## Learning Objectives

- Run a Python `.py` file stored in the repository.
- Run inline Python using `python -c` and heredoc blocks.
- Run a shell `.sh` script and inline bash commands.
- Run Windows `cmd` and PowerShell commands.
- Choose the right `shell:` for each runner.

## Key Concepts

`run`, `shell`, default shells, script files, inline scripts, heredoc, `python -c`, exit codes

## Expected Outcome

You can execute logic in a workflow step using whichever language or shell fits the task and the runner OS.

## Concept Flow

```text
Step -> shell (bash / cmd / powershell) -> run: command or script -> exit code -> step status
```

---

## ELI5 Explanation

Every step in a workflow is like typing a command into a terminal. You can type a one-line command, paste a small program, or point at a file and say "run this." The runner just needs to know which language interpreter or shell to use.

## Technical Explanation

A step uses `run:` to execute commands. The interpreter is decided by the `shell:` key. If you do not set `shell:`, GitHub uses a default: **bash** on Linux and macOS, and **PowerShell** on Windows. You can run a script file (`python file.py`, `./script.sh`), an inline one-liner (`python -c "..."`), an inline multi-line block (a heredoc), or shell built-ins. The step succeeds when the command returns exit code `0` and fails otherwise.

## Real-World Use Case

A test automation repo runs `pylint` and `behave` from bash on Linux for static checks, but invokes a Python test runner from `cmd` on a self-hosted Windows server during regression. Both live in the same repo and use the same patterns shown here.

## When To Use

- Run a reusable `.py` or `.sh` file checked into the repo.
- Run quick inline logic without creating a file.
- Run OS-specific commands (`cmd`/PowerShell on Windows, bash on Linux).
- Pass workflow inputs or environment values into a script.

## When NOT To Use

- Complex logic that belongs in a tested, versioned script file rather than a long inline block.
- Secrets echoed into the log by careless `echo`/`Write-Host`.
- Cross-platform commands assumed to work on every runner without checking the shell.

## Common Mistakes

- Expecting bash syntax to work in a Windows step (default there is PowerShell).
- Using an unquoted heredoc marker so the shell expands `$variables` you meant to keep literal.
- Forgetting `chmod +x` before running a `.sh` file.
- Mixing GitHub `${{ }}` expressions and shell variables incorrectly.
- Assuming a non-zero exit code will be ignored — it fails the step.

## Debugging Tips

- Print the shell and OS: `echo $SHELL` / `$RUNNER_OS` (bash) or `$PSVersionTable` (PowerShell).
- Add `set -x` in bash to trace commands, or `set -euo pipefail` for strict failures.
- Run `pwd`/`ls` (bash) or `Get-Location`/`Get-ChildItem` (PowerShell) to confirm the working directory.
- Echo the exact command before running it so logs show what executed.

## Minimal Workflow Example

```yaml
name: Run Scripts Basics

on: workflow_dispatch

jobs:
  scripts:
    runs-on: ubuntu-latest
    steps:
      - name: Inline bash
        run: echo "Hello from bash"

      - name: Inline Python one-liner
        run: python -c "print('Hello from Python')"
```

### YAML Explanation

- The first step uses the default bash shell to `echo` a message.
- The second step runs Python directly with `python -c` for a one-liner.
- No files are needed for inline commands.

### Step-by-Step Execution

1. The workflow is started manually.
2. The runner runs the bash `echo`.
3. The runner runs the Python one-liner.
4. Both steps return exit code `0` and pass.

## Production Workflow Example

The full example covers every common pattern across Linux and Windows runners: a Python file, inline Python (`-c` and heredoc), a shell script, inline bash, `cmd`, and PowerShell. See [`module-09-running-scripts.yml`](../examples/module-09-running-scripts.yml).

### Run a Python `.py` file

```yaml
- name: Set up Python
  uses: actions/setup-python@v7
  with:
    python-version: "3.13"

- name: Run a Python script file
  run: python scripts/hello.py --tag "smoke"
```

The repo file [`examples/scripts/hello.py`](../examples/scripts/hello.py) reads a `--tag` argument and prints a Behave command.

### Inline Python with `python -c`

```yaml
- name: Inline Python one-liner
  run: python -c "import sys; print('Python', sys.version.split()[0])"
```

### Inline Python with a heredoc

```yaml
- name: Inline Python heredoc
  run: |
    python - <<'PY'
    import os
    tag = os.environ.get("TEST_TAG", "smoke")
    print(f"behave --tags={tag} --no-capture")
    PY
  env:
    TEST_TAG: smoke
```

Quote the marker as `'PY'` so the shell does not expand `$` inside the block. Use an unquoted `PY` only when you *want* shell expansion.

### Inline bash commands

```yaml
- name: Inline bash commands
  run: |
    echo "Working directory: $(pwd)"
    ls -la scripts/
    echo "Runner OS: $RUNNER_OS"
```

### Run a shell `.sh` script

```yaml
- name: Run a shell script file
  run: |
    chmod +x scripts/run-checks.sh
    ./scripts/run-checks.sh "smoke"
```

The repo file [`examples/scripts/run-checks.sh`](../examples/scripts/run-checks.sh) uses `set -euo pipefail` for safe failures.

### Windows `cmd` commands

```yaml
- name: Windows cmd commands
  shell: cmd
  run: |
    echo Current directory: %CD%
    dir scripts
```

`cmd` reads variables as `%VAR%`. You must set `shell: cmd` because the Windows default is PowerShell.

### PowerShell commands

```yaml
- name: PowerShell commands
  shell: powershell
  run: |
    Write-Host "Working directory: $(Get-Location)"
    Get-ChildItem scripts
```

PowerShell reads variables as `$env:VAR` and uses cmdlets like `Get-ChildItem`.

### Shell Selection Reference

| Runner OS | Default shell | Force a shell with |
| --- | --- | --- |
| Linux / macOS | `bash` | `shell: bash`, `shell: sh`, `shell: python` |
| Windows | `pwsh` / PowerShell | `shell: cmd`, `shell: powershell`, `shell: pwsh`, `shell: bash` |

You can also set `shell: python` to make the whole `run:` block a Python script:

```yaml
- name: Whole step is Python
  shell: python
  run: |
    print("This entire block runs through the Python interpreter")
```

### Expected Output

- The Python file prints the interpreter version and a Behave command.
- The inline Python and bash steps print runtime and directory info.
- The shell script prints its check steps.
- The `cmd` and PowerShell steps list files on the Windows runner.

## Quiz

1. A step on a `windows-latest` runner has no `shell:` key. Which interpreter runs its `run:` block?
   - **A.** `bash`, because GitHub normalises every runner to bash.
   - **B.** `cmd`, because that is the native Windows shell.
   - **C.** PowerShell (`pwsh`), the Windows default.
   - **D.** Whatever `defaults.run.shell` says — there is no built-in default.

2. A heredoc block feeds Python a line containing `$HOME`, and Python must receive the four characters `$HOME` unchanged. Which marker do you write?
   - **A.** `python - <<HOME`
   - **B.** `python - <<'PY'` — quoting the marker stops the shell expanding `$`.
   - **C.** `python - <<PY` — the shell never expands inside a heredoc.
   - **D.** `python - <<"PY"` is required; single quotes are invalid heredoc syntax.

3. A `run:` step calls a Python script that finishes with `sys.exit(1)`. What happens to the job?
   - **A.** The step is marked failed and the job stops there unless `continue-on-error: true` is set.
   - **B.** The step passes; only an uncaught exception fails a step.
   - **C.** The step is marked "skipped" and later steps still run.
   - **D.** Nothing — exit codes only matter for the last step in a job.

4. `run: ./scripts/run-checks.sh smoke` fails on `ubuntu-latest` with a permission error, even though the file is committed and the path is right. Explain why, and give two ways to fix it.

5. Explain the difference between `${{ inputs.tag }}` and `$TAG` inside a `run:` block — specifically *when* each one is resolved — and describe the safer pattern for getting a workflow input into a shell command.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a step that runs `python -c` to print today's date. | Logs show the printed date. |
| Intermediate | Add a `.sh` script that takes a tag argument and run it. | Script prints the tag and a behave command. |
| Challenge | Add a Windows job that runs the same Python file via `cmd` with `%VAR%`. | Windows step runs the script using a cmd environment variable. |

Solutions: [`solutions/module-09-solutions.md`](../solutions/module-09-solutions.md)

---

[Previous: Module 8](./module-08-env-and-secrets.md) | [Module Index](./README.md) | [Next: Module 10](./module-10-artifacts.md)
