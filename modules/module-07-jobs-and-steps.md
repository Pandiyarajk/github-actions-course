# Module 7: Jobs, Job Naming, `timeout-minutes`, `runs-on`, `env`, and `steps`

![Module](https://img.shields.io/badge/Module-7-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20A%20Components-1f6feb?style=flat-square) ![Level](https://img.shields.io/badge/Level-Beginner-2da44e?style=flat-square) ![Time](https://img.shields.io/badge/Time-120%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 6](./module-06-runner-setup.md) | [Next: Module 8](./module-08-env-and-secrets.md)
> Level: **Beginner** | Time: **120 min** | Example workflow: [`module-07-jobs-and-steps.yml`](../examples/module-07-jobs-and-steps.yml)

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

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a `name` and `timeout-minutes` to a job. | UI shows the name; job cancels if it exceeds the timeout. |
| Intermediate | Add job-level `env` and use it in a step. | Step reads the job env variable. |
| Challenge | Add a second job with `needs` that runs on a self-hosted server label. | Second job runs only after the first passes, on the chosen runner. |

---

[Previous: Module 6](./module-06-runner-setup.md) | [Module Index](./README.md) | [Next: Module 8](./module-08-env-and-secrets.md)
