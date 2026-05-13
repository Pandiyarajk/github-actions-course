# Module 8: QA Automation Workflows

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 7](./module-07-release-automation.md) | [Next: Module 9](./module-09-monorepo-best-practices.md)
> Level: **Advanced** | Time: **150 min** | Example workflow: [`module-08-qa-automation.yml`](../examples/module-08-qa-automation.yml)

## Learning Objectives

- Build scheduled and manual QA automation workflows.
- Collect API, UI, and contract test evidence.
- Design pipelines that help QA triage failures quickly.

## Key Concepts

smoke tests, regression suites, Selenium, Newman, Pact, evidence bundles

## Expected Outcome

You can operate QA automation workflows that produce reliable failure evidence.

## Concept Flow

```text
Schedule / Manual Trigger -> API Tests + UI Tests + Contract Tests -> Evidence Artifacts -> QA Summary
```

---

## ELI5 Explanation

QA workflows are automated test inspectors. They run API tests, browser tests, contract tests, and collect evidence like screenshots, videos, and reports.

## Technical Explanation

QA automation workflows orchestrate services, test data, browsers, API clients, test reports, artifacts, retries, and notifications. They can run on pull requests, nightly schedules, release branches, or manual triggers.

## Real-World Use Case

Every night, the QA pipeline runs API regression tests, Selenium UI tests, and contract tests, then uploads reports and alerts the team if something fails.

## When To Use

- You need repeatable regression testing.
- Test evidence must be stored.
- Multiple test suites need orchestration.
- QA needs scheduled or release-based automation.

## When NOT To Use

- Tests are slow or flaky and should not block every pull request.
- The environment is shared and unstable.
- The feedback loop becomes too slow for developers.

## Common Mistakes

- Running UI tests without capturing screenshots.
- Not uploading reports on failure.
- Treating flaky tests as normal failures forever.
- Running all tests at the same frequency.

## Debugging Tips

- Use `if: always()` for artifact upload.
- Capture browser screenshots and videos.
- Separate smoke, regression, and nightly jobs.
- Store test logs with timestamps.

## Minimal Workflow Example

```yaml
name: QA Smoke Test

on: pull_request

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - name: Run sample smoke test
        run: echo "Run API or UI smoke tests here"
```

### YAML Explanation

- Pull requests run a fast smoke test.
- A single job keeps the first QA check simple.
- Replace the sample command with your real smoke test command.

### Step-by-Step Execution

1. Pull request triggers workflow.
2. Smoke test job runs.
3. Results appear as PR checks.
4. Team sees quick quality feedback.

## Production Workflow Example

```yaml
name: Nightly QA Automation

on:
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout tests
        uses: actions/checkout@v4
      - name: Run Newman API tests
        run: |
          mkdir -p reports/api
          echo "newman run collection.json --reporters junit"
          echo "<testsuite></testsuite>" > reports/api/newman.xml
      - name: Upload API report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: api-test-report
          path: reports/api/

  ui-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout tests
        uses: actions/checkout@v4
      - name: Run Selenium tests
        run: |
          mkdir -p reports/ui screenshots
          echo "Run Selenium tests here"
          echo "sample screenshot evidence" > screenshots/home.txt
      - name: Upload UI evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ui-test-evidence
          path: |
            reports/ui/
            screenshots/

  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout contracts
        uses: actions/checkout@v4
      - name: Run Pact contract tests
        run: echo "Run pact verification here"
```

### YAML Explanation

- `schedule` runs the regression suite nightly.
- `workflow_dispatch` lets QA rerun manually.
- API, UI, and contract tests are separate jobs.
- Artifacts preserve evidence for debugging and audit.

### Expected Output

- Nightly workflow runs automatically.
- API, UI, and contract tests are separated.
- Reports and screenshots are uploaded as artifacts.

## Self-Hosted Runner Execution Examples

These examples are useful when QA jobs must run on a named self-hosted machine, call a Windows executable, or run a command installed from a Python package.

### Choose a Runner by Name or Label

```yaml
name: Manual Runner Selection

on:
  workflow_dispatch:
    inputs:
      runner:
        description: "Runner label to use"
        type: choice
        options:
          - qa-runner-1
          - qa-runner-2
        default: qa-runner-1

run-name: QA on ${{ inputs.runner }}

jobs:
  qa:
    runs-on:
      - self-hosted
      - windows
      - ${{ inputs.runner }}
    steps:
      - name: Print selected runner
        shell: pwsh
        run: |
          "Selected label: ${{ inputs.runner }}"
          "Actual runner name: $env:RUNNER_NAME"
```

You cannot rename a runner from workflow YAML. Set the runner name when registering the self-hosted runner, then target it with a stable label.

### Run a Windows Executable

```yaml
jobs:
  desktop-check:
    runs-on:
      - self-hosted
      - windows
      - qa-runner-1
    steps:
      - name: Run installed desktop checker
        shell: pwsh
        run: |
          & "C:\Tools\desktop-checker\desktop-checker.exe" `
            --config ".\config\qa.json" `
            --output ".\reports\desktop-check.json"
```

Quote executable paths that contain spaces and let PowerShell's call operator `&` execute the file.

### Install and Run a Pip Package With Parameters

```yaml
jobs:
  package-command:
    runs-on: ubuntu-latest
    steps:
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install package command
        run: |
          python -m pip install --upgrade pip
          python -m pip install generic-report-cli

      - name: Run package command with parameters
        run: |
          generic-report \
            --suite regression \
            --browser chrome \
            --output reports/generic-report.json
```

Pin package versions for production workflows when reproducibility matters.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a smoke test workflow. | Smoke test runs on PR. |
| Intermediate | Upload QA reports as artifacts. | Reports are available after failure or success. |
| Challenge | Create nightly API + UI + contract test jobs. | Scheduled QA workflow runs daily. |

---

[Previous: Module 7](./module-07-release-automation.md) | [Module Index](./README.md) | [Next: Module 9](./module-09-monorepo-best-practices.md)
