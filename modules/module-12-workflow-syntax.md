# Module 12: Workflow Syntax, Jobs, Steps, and Expressions

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 11](./module-11-misc-features.md) | [Next: Module 13](./module-13-secrets-security.md)
> Level: **Beginner** | Time: **120 min** | Example workflow: [`module-12-workflow-syntax.yml`](../examples/module-12-workflow-syntax.yml)

## Learning Objectives

- Use workflow triggers, inputs, expressions, and contexts.
- Split work into jobs and connect them with dependencies.
- Apply conditions safely in real workflows.

## Key Concepts

contexts, expressions, inputs, conditionals, outputs, job dependencies

## Expected Outcome

You can author readable workflows that use jobs, expressions, and conditions correctly.

## Concept Flow

```text
Trigger -> Workflow Inputs -> Jobs -> Needs / Conditions -> Steps -> Outputs / Summary
```

---

## ELI5 Explanation

A workflow is a recipe. Jobs are sections of the recipe. Steps are individual instructions. Expressions are placeholders that GitHub fills in while the recipe runs.

## Technical Explanation

GitHub Actions YAML supports triggers, jobs, steps, contexts, expressions, environment variables, conditionals, outputs, and dependencies. Expressions use `${{ }}` and can access contexts such as `github`, `env`, `secrets`, `inputs`, `matrix`, and `needs`.

## Real-World Use Case

The web automation team wants pylint static analysis and the Behave smoke suite to run in separate jobs, with the Allure report publish step allowed only if both pass.

## When To Use

- Tasks can run independently.
- You want clearer logs.
- You need job-level dependencies.
- Different jobs require different runners or permissions.

## When NOT To Use

- The workflow becomes harder to understand.
- Jobs repeat expensive setup unnecessarily.
- Simple sequential steps would be enough.

## Common Mistakes

- Mixing shell variables and GitHub expressions incorrectly.
- Using secrets in `if:` conditions directly.
- Forgetting that each job starts on a fresh runner.
- Expecting files from one job to exist in another without artifacts or cache.

## Debugging Tips

- Print safe context values like `github.ref`.
- Use `needs.<job_id>.result` for dependency debugging.
- Group logs with `::group::` and `::endgroup::`.
- Use `continue-on-error` only when failure is acceptable.

## Minimal Workflow Example

```yaml
name: Syntax Basics

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
```

### YAML Explanation

- `workflow_dispatch` enables manual runs.
- `inputs` defines values the user provides at runtime.
- `${{ inputs.browser }}` reads the input before the step runs.

### Step-by-Step Execution

1. User manually starts the workflow.
2. GitHub asks for the `browser` input.
3. Runner starts.
4. The step prints the provided input.

## Production Workflow Example

```yaml
name: Multi Job Validation

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v6
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Run static analysis
        run: |
          pylint your-solution-root-folder-name/
          python your-solution-root-folder-name/scripts/check-duplicate-functions.py
          python your-solution-root-folder-name/scripts/check-duplicate-variables.py

  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v6
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Run Behave smoke suite
        run: behave --tags=smoke your-solution-root-folder-name/features

  summary:
    needs:
      - lint
      - test
    if: ${{ success() }}
    runs-on: ubuntu-latest
    steps:
      - name: Print success summary
        run: echo "Lint and smoke tests passed for ${{ github.sha }}"
```

### YAML Explanation

- `lint` and `test` are independent jobs.
- `summary` waits for both jobs using `needs`.
- `if: ${{ success() }}` prevents the summary from running after failure.
- `${{ github.sha }}` prints the commit being validated.

### Expected Output

- `lint` and `test` run independently.
- `summary` runs only after both pass.
- Pull request shows all checks.

## Trigger Examples Cookbook

Use these snippets as small building blocks. GitHub evaluates cron schedules in UTC, so convert local time before committing a schedule.

### Scheduled Workflows

```yaml
on:
  schedule:
    - cron: "0 * * * *"      # hourly, at minute 0
    - cron: "0 2 * * *"      # daily smoke run, 02:00 UTC
    - cron: "0 2 * * 1"      # weekly regression, Monday 02:00 UTC
    - cron: "0 2 1 * *"      # monthly, first day at 02:00 UTC
  workflow_dispatch:
```

### Push and Pull Request

```yaml
on:
  push:
    branches:
      - main
      - "release/**"
  pull_request:
    branches:
      - main
    types:
      - opened
      - synchronize
      - reopened
```

### Pull Request Review Events

```yaml
on:
  pull_request_review_comment:
    types:
      - created
  pull_request_review:
    types:
      - submitted
```

`pull_request_review_comment` runs when someone adds an inline review comment on code. `pull_request_review` with `submitted` runs when a reviewer submits an approval, change request, or general review.

### Branch Lifecycle Events

```yaml
on:
  create:
  delete:
```

Use `github.event.ref_type == 'branch'` when a workflow should ignore tag creation or deletion.

### Path-Scoped Pull Request and Push

```yaml
on:
  pull_request:
    paths:
      - "your-solution-root-folder-name/features/**"
      - ".github/workflows/web-smoke.yml"
  push:
    branches:
      - main
    paths:
      - "your-solution-root-folder-name/features/**"
```

Path filters are useful for monorepos, but remember that skipped workflows can affect required checks if branch protection expects them.

## Workflow Summary Example

Use `$GITHUB_STEP_SUMMARY` when you want important results on the workflow run page instead of buried in logs.

```yaml
name: Summary Demo

on:
  workflow_dispatch:

jobs:
  summarize:
    runs-on: ubuntu-latest
    steps:
      - name: Run check
        run: |
          echo "status=passed" >> "$GITHUB_ENV"

      - name: Add workflow summary
        if: always()
        run: |
          echo "## Behave Smoke Summary" >> "$GITHUB_STEP_SUMMARY"
          echo "" >> "$GITHUB_STEP_SUMMARY"
          echo "- Repository: ${{ github.repository }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- Branch: ${{ github.ref_name }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- Status: $status" >> "$GITHUB_STEP_SUMMARY"
```

The summary supports Markdown, so tables, bullet lists, links, and short report sections work well.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a second step that prints `github.actor`. | Logs show the triggering user. |
| Intermediate | Create two jobs where one depends on the other. | Second job waits for first job. |
| Challenge | Add an `if:` condition so the Allure publish step runs only on `main`. | Conditional step is skipped on other branches. |

---

[Previous: Module 11](./module-11-misc-features.md) | [Module Index](./README.md) | [Next: Module 13](./module-13-secrets-security.md)
