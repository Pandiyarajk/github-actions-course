# Module 5: Automated Testing Pipelines

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 4](./module-04-matrix-and-reuse.md) | [Next: Module 6](./module-06-docker-performance.md)
> Level: **Intermediate** | Time: **120 min** | Example workflow: [`module-05-multi-language-tests.yml`](../examples/module-05-multi-language-tests.yml)

## Learning Objectives

- Design fast pull request test pipelines.
- Separate unit, integration, API, UI, and contract tests.
- Publish test evidence with artifacts.

## Key Concepts

test stages, reports, artifacts, fail-fast feedback, flaky tests

## Expected Outcome

You can build test pipelines that give developers and QA useful feedback.

## Concept Flow

```text
Pull Request -> Install Dependencies -> Unit Tests -> Integration / API Tests -> Reports -> PR Status
```

---

## ELI5 Explanation

Automated tests are quality gates. GitHub Actions runs them every time code changes so bugs are caught before humans review or deploy the code.

## Technical Explanation

Testing workflows install dependencies, run test commands, publish reports, upload artifacts, and fail the pipeline when tests fail. Teams often separate unit, integration, API, UI, and contract tests into different jobs with different triggers.

## Real-World Use Case

A pull request should not merge unless backend unit tests, frontend tests, and API tests pass.

## When To Use

- You want fast feedback on every pull request.
- You need regression protection.
- You want QA evidence stored as artifacts.

## When NOT To Use

- The tests are slow and better suited for nightly runs.
- The test environment is unstable.
- The cost outweighs the signal.

## Common Mistakes

- Running tests without installing dependencies.
- Not uploading reports when tests fail.
- Combining all tests into one huge job.
- Ignoring flaky tests instead of tracking them.

## Debugging Tips

- Upload test reports with `if: always()`.
- Separate fast and slow tests.
- Capture screenshots or logs for UI tests.
- Use clear job names for test categories.

## Minimal Workflow Example

```yaml
name: Basic Tests

on: pull_request

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Run sample tests
        run: echo "Use pytest, npm test, dotnet test, or your project test command"
```

### YAML Explanation

- `pull_request` gives feedback before merge.
- `checkout` gets the code.
- The test step should be replaced with the project's real command.

### Step-by-Step Execution

1. Pull request opens or updates.
2. Workflow checks out the repository.
3. Test command runs.
4. Pull request shows pass or fail status.

## Production Workflow Example

```yaml
name: Multi Language Test Pipeline

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read

jobs:
  python-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - name: Install Python dependencies
        run: pip install -r requirements.txt
      - name: Run pytest
        run: pytest --junitxml=reports/pytest.xml
      - name: Upload pytest report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pytest-report
          path: reports/pytest.xml

  node-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
      - name: Install dependencies
        run: npm ci
      - name: Run JavaScript tests
        run: npm test

  dotnet-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Setup .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: "8.0.x"
      - name: Run .NET tests
        run: dotnet test --logger trx
```

### YAML Explanation

- Each language gets its own job for clearer failures.
- Setup actions install the required toolchain.
- Caching speeds up dependency installation.
- `if: always()` preserves test reports even when tests fail.

### Expected Output

- Separate jobs for Python, Node, and .NET.
- Test reports upload even when tests fail.
- Pull request clearly shows which stack failed.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a workflow that runs one test command. | Test job appears on pull requests. |
| Intermediate | Upload a test report artifact. | Artifact is available after workflow run. |
| Challenge | Split unit, integration, and API tests into separate jobs. | Each test type has its own check. |

---

[Previous: Module 4](./module-04-matrix-and-reuse.md) | [Module Index](./README.md) | [Next: Module 6](./module-06-docker-performance.md)
