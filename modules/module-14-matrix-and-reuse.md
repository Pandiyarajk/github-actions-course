# Module 14: Matrix Builds, Marketplace Actions, and Reusable Workflows

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 13](./module-13-secrets-security.md) | [Next: Module 15](./module-15-multi-language-tests.md)
> Level: **Intermediate** | Time: **120 min** | Example workflow: [`module-14-matrix-and-reuse.yml`](../examples/module-14-matrix-and-reuse.yml)

## Learning Objectives

- Run matrix builds across browsers and test servers.
- Evaluate marketplace actions before adopting them.
- Create and call reusable workflows with `workflow_call`.

## Key Concepts

strategy matrix, marketplace actions, reusable workflows, composite actions

## Expected Outcome

You can scale Behave/Selenium checks across browsers and runners and reuse workflow logic cleanly.

## Concept Flow

```text
Single Job Definition -> Matrix Values -> Parallel Job Copies -> Aggregated Result

Caller Workflow -> workflow_call -> Reusable Workflow -> Shared Jobs
```

---

## ELI5 Explanation

A matrix is like asking several robots to run your Selenium tests at the same time: one driving Chrome, one driving Firefox, one driving Edge, and some running on server1 while others run on server2.

## Technical Explanation

A matrix strategy runs the same job with different combinations of variables. Marketplace actions provide reusable tasks maintained by GitHub or the community. Reusable workflows use `workflow_call` so one workflow can call another workflow, helping standardize CI across multiple test automation repositories.

## Real-World Use Case

A web automation suite must pass on Chrome, Firefox, and Edge before a release, and the regression suite must be able to fan out across self-hosted runners (server1, server2) to finish faster.

## When To Use

- Validating the same Behave suite across chrome, firefox, and msedge.
- Spreading long regression runs across server1..server4.
- Running browser or environment combinations.
- Standardizing CI or Allure report logic across repositories.

## When NOT To Use

- The combinations do not provide meaningful confidence.
- Runtime and self-hosted runner cost increase without value.
- The workflow logic is unique to one repository and easier to keep local.

## Common Mistakes

- Creating too many browser x server combinations.
- Forgetting `fail-fast: false` when you need every browser's result.
- Passing secrets incorrectly to reusable workflows.
- Using unpinned third-party actions in sensitive pipelines.

## Debugging Tips

- Print matrix values (browser, server) in logs.
- Use `strategy.fail-fast: false` for full cross-browser visibility.
- Start with a small matrix, then expand.
- Pin important actions to trusted versions or SHAs.

## Minimal Workflow Example

```yaml
name: Matrix Basics

on: push

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        browser:
          - chrome
          - firefox
          - msedge
    steps:
      - name: Show matrix value
        run: echo "Running Behave against ${{ matrix.browser }}"
```

### YAML Explanation

- `strategy.matrix` defines values that create multiple job runs.
- `browser` is a custom matrix variable.
- `${{ matrix.browser }}` reads the current job's matrix value.

### Step-by-Step Execution

1. A push triggers the workflow.
2. GitHub creates three job runs.
3. One run drives Chrome as the matrix value.
4. Another run drives Firefox, and a third drives Edge.

## Production Workflow Example

```yaml
name: Selenium BDD Matrix CI

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read

jobs:
  test:
    name: ${{ matrix.browser }} on ${{ matrix.server }}
    strategy:
      fail-fast: false
      matrix:
        server:
          - server1
          - server2
        browser:
          - chrome
          - firefox
          - msedge
    runs-on: ${{ matrix.server }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Cache pip
        uses: actions/cache@v5
        with:
          path: ~/.cache/pip
          key: pip-${{ hashFiles('your-solution-root-folder-name/requirements.txt') }}
      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt
      - name: Run Behave regression
        run: behave --tags=regression -D browser=${{ matrix.browser }}
        working-directory: your-solution-root-folder-name
```

### YAML Explanation

- `fail-fast: false` lets all matrix jobs finish even if one browser fails.
- `matrix.server` selects which self-hosted runner (server1, server2) executes the job.
- `actions/setup-python@v6` installs Python 3.13.
- `actions/cache@v5` caches the pip download directory.

### Reusable Workflow Example

```yaml
name: Reusable BDD CI

on:
  workflow_call:
    inputs:
      browser:
        required: true
        type: string
      environment:
        required: false
        type: string
        default: qa

jobs:
  bdd-ci:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v6
      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Install and run Behave
        run: |
          pip install -r your-solution-root-folder-name/requirements.txt
          behave --tags=smoke -D browser=${{ inputs.browser }} -D env=${{ inputs.environment }}
        working-directory: your-solution-root-folder-name
      - name: Generate Allure report
        run: allure generate your-solution-root-folder-name/allure-results -o allure-report --clean
      - name: Upload Allure report
        uses: actions/upload-artifact@v7
        with:
          name: allure-report-${{ inputs.browser }}
          path: allure-report
```

Caller workflow:

```yaml
name: Call Reusable BDD CI

on: pull_request

jobs:
  ci:
    uses: ./.github/workflows/reusable-bdd-ci.yml
    with:
      browser: "chrome"
      environment: "qa"
```

### Expected Output

- Matrix jobs run in parallel.
- Each browser and server combination appears as a separate check.
- Reusable workflow centralizes Behave and Allure logic.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create a matrix for chrome, firefox, and msedge. | Three job runs appear. |
| Intermediate | Add server1 and server2 to the matrix. | Six job runs appear. |
| Challenge | Move the Behave/Allure logic into a reusable workflow using `workflow_call`. | Caller workflow invokes shared workflow. |

---

[Previous: Module 13](./module-13-secrets-security.md) | [Module Index](./README.md) | [Next: Module 15](./module-15-multi-language-tests.md)
