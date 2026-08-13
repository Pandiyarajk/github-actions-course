# Module 7: Jobs, Job Naming, `timeout-minutes`, `runs-on`, `env`, and `steps`

![Module](https://img.shields.io/badge/Module-7-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20A%20Components-1f6feb?style=flat-square) ![Level](https://img.shields.io/badge/Level-Beginner-2da44e?style=flat-square) ![Time](https://img.shields.io/badge/Time-120%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 6](./module-06-runner-setup.md) | [Next: Module 8](./module-08-env-and-secrets.md)
> Level: **Beginner** | Time: **120 min** | Example workflow: [`module-07-jobs-and-steps.yml`](../examples/module-07-jobs-and-steps.yml)
> Solutions: [`module-07-solutions.md`](../solutions/module-07-solutions.md)

## Learning Objectives

- Structure a workflow into one or more jobs.
- Give a job an ID and a friendly display `name`.
- Select runners with `runs-on` (GitHub-hosted and self-hosted).
- Bound runtime with `timeout-minutes`.
- Share configuration with `env` at workflow, job, and step levels.
- Compose `steps` that run actions and shell commands.

## Key Concepts

`jobs`, job ID vs `name`, `runs-on`, `timeout-minutes`, `env` scope, `steps`, `needs`

## Expected Outcome

You can author a multi-job workflow with clear names, correct runners, safe timeouts, scoped environment variables, and well-ordered steps.

## Concept Flow

```text
jobs -> job (id + name) -> runs-on + timeout-minutes + env -> steps -> actions / run commands
```

---

## ELI5 Explanation

A workflow is a project. Each job is a worker assigned to a machine (`runs-on`). The job has a name tag, a time limit so it cannot work forever (`timeout-minutes`), a shared toolbox of settings (`env`), and a checklist of tasks (`steps`).

## Technical Explanation

`jobs` is a map of job IDs to job definitions. The key is the **job ID** (used by `needs` and the API); the optional `name` is the human-readable label shown in the UI. `runs-on` chooses the runner — a GitHub-hosted image (`ubuntu-latest`, `windows-latest`) or self-hosted labels (`server1`). `timeout-minutes` cancels a job that exceeds it. `env` defines environment variables and can appear at workflow, job, or step level, with the narrowest scope winning. `steps` run in order; each is either a `uses:` action or a `run:` command, and a failing step fails the job unless `continue-on-error` is set.

## Real-World Use Case

A QA pipeline splits work into a fast `static-analysis` job on `ubuntu-latest` (15-minute timeout) and a long `bdd-regression` job on a self-hosted `server4` (12-hour timeout) that needs Zephyr/Jira secrets in its `env`. The second job runs only after the first passes (`needs`).

## When To Use

- Separate concerns into independent jobs (analysis vs execution).
- Target specific runners per job (Linux for lint, Windows servers for UI).
- Cap long jobs so a hung run does not block a runner indefinitely.
- Share secrets/config across a job's steps via `env`.

## When NOT To Use

- Splitting trivial work into many jobs that each repeat setup.
- Putting a huge `timeout-minutes` on everything (hung jobs hold runners).
- Defining workflow-level `env` for values only one step needs.

## Common Mistakes

- Renaming the **job ID** when you only meant to change the display label. The ID is referenced by `needs:`, by required status checks in branch protection, and by the API — renaming it silently breaks the dependency or leaves a required check permanently pending. Change `name:` instead.
- Expecting a later job to see files a previous job created. Each job gets its own runner and workspace; `needs:` orders jobs, it does not share a filesystem. Move data with artifacts or job outputs.
- Omitting `timeout-minutes` and relying on the default. A job with no timeout inherits the 360-minute default and can hold a self-hosted runner for six hours before it is cut off.
- Reading a job-level `env` value inside `runs-on:` or `timeout-minutes:`. The `env` context is not available in those job-level keys; use `inputs` or a workflow-level expression instead.
- Assuming a step-level `env` entry leaks into the next step. It does not — its scope is exactly one step.
- Using `continue-on-error: true` to silence a genuinely failing step. The job reports success and the failure disappears from the summary.
- Writing `needs: [static-analysis]` and expecting the second job to run when the first fails. A failed dependency skips the dependent job unless you add an `if: always()`-style condition.

## Debugging Tips

- "Job depends on unknown job" almost always means a `needs:` value is spelled with the display `name` rather than the job ID. Compare against the `jobs:` map keys, not the UI.
- A job that never starts is usually a `runs-on` label mismatch, not a syntax error. The Actions UI shows it as waiting for a runner, with the requested labels listed.
- To find out which `env` scope actually won, add `- run: env | sort` (or `Get-ChildItem Env: | Sort-Object Name` on Windows) as a temporary step. Guessing about precedence takes longer than printing it.
- A job cancelled at a suspiciously round number of minutes hit `timeout-minutes`; the log line names the timeout rather than a failing command.
- `env | sort` also confirms whether a secret reached the job — the value is masked, but a missing variable is absent entirely, which distinguishes "not set" from "wrong value".
- When a self-hosted job behaves differently from an identical hosted one, print `$RUNNER_NAME` and the tool versions early. The difference is almost always the pre-installed toolchain rather than the workflow.

## Scope and Naming Reference

| Element | Purpose | Example |
| --- | --- | --- |
| Job ID | Stable key for `needs` and the API | `bdd-regression` |
| Job `name` | Display label in the UI | `BDD Regression on server4` |
| `runs-on` | Runner selection | `ubuntu-latest`, `server1` |
| `timeout-minutes` | Cancel a slow/hung job | `15`, `720` |
| `env` (workflow) | Shared by all jobs | `REPORT_HOME: reports` |
| `env` (job) | Shared by one job's steps | `ZEPHYR_SCALE_TOKEN: ${{ secrets.* }}` |
| `env` (step) | Only that step | `BROWSER: chrome` |

## Minimal Workflow Example

```yaml
name: Jobs Basics

on: workflow_dispatch

jobs:
  smoke:
    name: Quick Smoke
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      TEST_TAGS: smoke
    steps:
      - name: Checkout
        uses: actions/checkout@v7
      - name: Run smoke
        run: echo "behave --tags=$TEST_TAGS"
```

### YAML Explanation

- `smoke` is the job ID; `name` is the display label.
- `runs-on: ubuntu-latest` picks a GitHub-hosted runner.
- `timeout-minutes: 10` cancels the job if it runs too long.
- Job-level `env.TEST_TAGS` is available to every step.
- The two steps checkout code and run a command using `$TEST_TAGS`.

### Step-by-Step Execution

1. The job is assigned to an Ubuntu runner.
2. The checkout step syncs the repo.
3. The run step echoes the Behave command using the job env.
4. The job ends; it would be cancelled if it passed 10 minutes.

## Production Workflow Example

The full example splits a fast analysis job and a long self-hosted BDD job, showing all three `env` scopes. See [`module-07-jobs-and-steps.yml`](../examples/module-07-jobs-and-steps.yml).

### Two Jobs with Names, Runners, and Timeouts

```yaml
jobs:
  static-analysis:
    name: Static Analysis (pylint + duplicates)
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - run: pip install pylint check-duplicate-functions
      - run: pylint your-solution-root-folder-name/ --exit-zero

  bdd-regression:
    name: BDD Regression on ${{ inputs.server }}
    needs: static-analysis
    runs-on: ${{ inputs.server }}
    timeout-minutes: 720
    env:
      ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
    steps:
      - uses: actions/checkout@v7
      - run: pip install behave selenium allure-behave
```

- `name` makes each job readable; the second name is dynamic from an input.
- `runs-on: ${{ inputs.server }}` targets a self-hosted server label.
- `timeout-minutes` is small for analysis and large for the long suite.
- `needs: static-analysis` runs BDD only after analysis passes.

### Env Scope: Workflow vs Job vs Step

```yaml
env:                       # workflow-level: all jobs
  REPORT_HOME: reports

jobs:
  bdd-regression:
    env:                   # job-level: this job's steps
      TEST_TAGS: ${{ inputs.tags }}
    steps:
      - name: Run Behave
        env:               # step-level: only this step
          BROWSER: chrome
        run: behave --tags=$TEST_TAGS -D browser=$BROWSER
```

The most specific scope wins if the same variable name is defined more than once.

### Selecting Runners

| `runs-on` | Runner |
| --- | --- |
| `ubuntu-latest` | GitHub-hosted Linux |
| `windows-latest` | GitHub-hosted Windows |
| `server1` … `server4` | Self-hosted labels |
| `${{ inputs.server }}` | Runner chosen at run time |

### Expected Output

- The Actions UI shows two named jobs.
- `static-analysis` runs on Ubuntu and finishes quickly.
- `bdd-regression` runs on the chosen server after analysis passes.
- Step-level `BROWSER` and job-level `TEST_TAGS` resolve correctly in the Behave command.

## Quiz

1. A workflow defines `TEST_TAGS: smoke` at workflow level, `TEST_TAGS: regression` on the job, and `TEST_TAGS: nightly` on one step. What does that step's `run:` block see in `$TEST_TAGS`?
   - **A.** `smoke` — the workflow level is the outermost scope and wins.
   - **B.** `regression` — job level always overrides step level.
   - **C.** `nightly` — the narrowest scope wins.
   - **D.** All three, concatenated in declaration order.

2. You rename a job from `bdd-regression:` to `bdd_regression:` because you prefer underscores, leaving `name: BDD Regression on server4` untouched. What breaks?
   - **A.** Nothing — the job ID is cosmetic once `name:` is set.
   - **B.** Any `needs: bdd-regression` reference and any branch-protection required check that names the old ID.
   - **C.** Only the API, since the UI reads `name:`.
   - **D.** `runs-on` stops resolving self-hosted labels.

3. A `static-analysis` job writes `pylint.txt`, and a `bdd-regression` job with `needs: static-analysis` cannot read it. What is the correct fix?
   - **A.** Add `timeout-minutes` to the first job so it finishes writing.
   - **B.** Declare `pylint.txt` in workflow-level `env`.
   - **C.** Upload it as an artifact in the first job and download it in the second, or pass the value as a job output.
   - **D.** Give both jobs the same `runs-on` label so they share a workspace.

4. A self-hosted BDD job with no `timeout-minutes` hangs on a browser dialog. Describe what happens to the job and to the runner, and explain what you would set instead and why the value differs from a lint job's.

5. Explain the difference between a job ID and a job `name`, and give one concrete situation for each where using the wrong one produces a confusing failure.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a `name` and `timeout-minutes` to a job. | UI shows the name; job cancels if it exceeds the timeout. |
| Intermediate | Add job-level `env` and use it in a step. | Step reads the job env variable. |
| Challenge | Add a second job with `needs` that runs on a self-hosted server label. | Second job runs only after the first passes, on the chosen runner. |

Solutions: [`solutions/module-07-solutions.md`](../solutions/module-07-solutions.md)

---

[Previous: Module 6](./module-06-runner-setup.md) | [Module Index](./README.md) | [Next: Module 8](./module-08-env-and-secrets.md)
