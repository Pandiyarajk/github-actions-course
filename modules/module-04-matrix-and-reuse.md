# Module 4: Matrix Builds, Marketplace Actions, and Reusable Workflows

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 3](./module-03-secrets-security.md) | [Next: Module 5](./module-05-multi-language-tests.md)
> Level: **Intermediate** | Time: **120 min** | Example workflow: [`module-04-matrix-and-reuse.yml`](../examples/module-04-matrix-and-reuse.yml)

## Learning Objectives

- Run matrix builds across versions and operating systems.
- Evaluate marketplace actions before adopting them.
- Create and call reusable workflows with `workflow_call`.

## Key Concepts

strategy matrix, marketplace actions, reusable workflows, composite actions

## Expected Outcome

You can scale checks across environments and reuse workflow logic cleanly.

## Concept Flow

```text
Single Job Definition -> Matrix Values -> Parallel Job Copies -> Aggregated Result

Caller Workflow -> workflow_call -> Reusable Workflow -> Shared Jobs
```

---

## ELI5 Explanation

A matrix is like asking several robots to test your app in different rooms at the same time: one with Node 18, one with Node 20, one on Ubuntu, and one on Windows.

## Technical Explanation

A matrix strategy runs the same job with different combinations of variables. Marketplace actions provide reusable tasks maintained by GitHub or the community. Reusable workflows use `workflow_call` so one workflow can call another workflow, helping standardize CI/CD across repositories.

## Real-World Use Case

A library must support multiple Node versions and operating systems before publishing.

## When To Use

- Supporting multiple language versions.
- Testing across operating systems.
- Running browser or dependency combinations.
- Standardizing CI or deployment logic across repositories.

## When NOT To Use

- The combinations do not provide meaningful confidence.
- Runtime and cost increase without value.
- The workflow logic is unique to one repository and easier to keep local.

## Common Mistakes

- Creating too many matrix combinations.
- Forgetting `fail-fast: false` when you need all results.
- Passing secrets incorrectly to reusable workflows.
- Using unpinned third-party actions in sensitive pipelines.

## Debugging Tips

- Print matrix values in logs.
- Use `strategy.fail-fast: false` for test coverage visibility.
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
        node-version:
          - 18
          - 20
    steps:
      - name: Show matrix value
        run: echo "Testing Node ${{ matrix.node-version }}"
```

### YAML Explanation

- `strategy.matrix` defines values that create multiple job runs.
- `node-version` is a custom matrix variable.
- `${{ matrix.node-version }}` reads the current job's matrix value.

### Step-by-Step Execution

1. A push triggers the workflow.
2. GitHub creates two job runs.
3. One run uses Node 18 as the matrix value.
4. Another run uses Node 20 as the matrix value.

## Production Workflow Example

```yaml
name: Node Matrix CI

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read

jobs:
  test:
    name: Node ${{ matrix.node-version }} on ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os:
          - ubuntu-latest
          - windows-latest
        node-version:
          - 18
          - 20
    runs-on: ${{ matrix.os }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: npm
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test
```

### YAML Explanation

- `fail-fast: false` lets all matrix jobs finish even if one fails.
- `matrix.os` controls the runner image.
- `actions/setup-node@v4` installs the selected Node version.
- `cache: npm` enables dependency caching.

### Reusable Workflow Example

```yaml
name: Reusable CI

on:
  workflow_call:
    inputs:
      node-version:
        required: true
        type: string

jobs:
  node-ci:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
      - name: Install and test
        run: |
          npm ci
          npm test
```

Caller workflow:

```yaml
name: Call Reusable CI

on: pull_request

jobs:
  ci:
    uses: ./.github/workflows/reusable-ci.yml
    with:
      node-version: "20"
```

### Expected Output

- Matrix jobs run in parallel.
- Each OS and Node version appears as a separate check.
- Reusable workflow centralizes CI logic.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create a matrix for Node 18 and 20. | Two job runs appear. |
| Intermediate | Add Ubuntu and Windows to the matrix. | Four job runs appear. |
| Challenge | Move CI logic into a reusable workflow using `workflow_call`. | Caller workflow invokes shared workflow. |

---

[Previous: Module 3](./module-03-secrets-security.md) | [Module Index](./README.md) | [Next: Module 5](./module-05-multi-language-tests.md)
