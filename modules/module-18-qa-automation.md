# Module 18: QA Automation Workflows

![Module](https://img.shields.io/badge/Module-18-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20B%20Applied-8957e5?style=flat-square) ![Level](https://img.shields.io/badge/Level-Advanced-cf222e?style=flat-square) ![Time](https://img.shields.io/badge/Time-150%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 17](./module-17-release-automation.md) | [Next: Module 19](./module-19-monorepo-best-practices.md)
> Level: **Advanced** | Time: **150 min** | Example workflow: [`module-18-qa-automation.yml`](../examples/module-18-qa-automation.yml)

## Learning Objectives

- Build scheduled and manual QA automation workflows.
- Collect API health, BDD UI, and reporting evidence.
- Design pipelines that help QA triage failures quickly.

## Key Concepts

smoke tests, regression suites, Selenium, Behave (Python BDD), Allure reports, requests API health-checks, evidence bundles

## Expected Outcome

You can operate QA automation workflows that produce reliable failure evidence.

## Concept Flow

```text
Schedule / Manual Trigger -> API Health-Check (requests) -> BDD UI Tests (behave + selenium, browser matrix) -> Allure Report Analysis -> Email with Metrics
```

---

## ELI5 Explanation

QA workflows are automated test inspectors. They ping the API to make sure it is awake, drive real browsers through your scenarios, and collect evidence like screenshots and Allure reports so failures are easy to read.

## Technical Explanation

QA automation workflows orchestrate test data, browsers, API clients, Allure reports, artifacts, retries, and notifications. They can run on pull requests, nightly schedules, release branches, or manual triggers. For these projects the nightly chain layers a Python `requests` API health-check, a `behave` + `selenium` UI suite across a browser matrix on a self-hosted runner, Allure report analysis, and an SMTP email summarizing pass-rate and failed IDs.

## Real-World Use Case

Every night the web automation smoke suite runs against `your-domain.com`: a `requests` health-check confirms the API is up, `behave` + `selenium` execute the BDD scenarios across chrome and firefox on a `server1` self-hosted runner, Allure results are analyzed for pass-rate and failed scenario IDs, and the team receives an email summary. A heavier desktop/UI regression suite follows the same shape on `server1..server4`.

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
- Not uploading Allure results on failure.
- Treating flaky tests as normal failures forever.
- Running all tests at the same frequency.

## Debugging Tips

- Use `if: always()` for Allure results and screenshot upload.
- Capture browser screenshots on scenario failure (Behave `after_scenario` hook).
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
        run: echo "Run requests API health-check or behave smoke tags here"
```

### YAML Explanation

- Pull requests run a fast smoke test.
- A single job keeps the first QA check simple.
- Replace the sample command with your real `behave` smoke command.

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
    - cron: "30 1 * * *"
  workflow_dispatch:
    inputs:
      tags:
        description: "Behave tags filter (e.g. @smoke)"
        type: string
        default: "@smoke"
      browser:
        description: "Browser to run UI tests against"
        type: choice
        options:
          - chrome
          - firefox
          - msedge
        default: chrome

permissions:
  contents: read

jobs:
  api-health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout tests
        uses: actions/checkout@v6
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Cache pip
        uses: actions/cache@v5
        with:
          path: ~/.cache/pip
          key: pip-${{ hashFiles('your-solution-root-folder-name/requirements.txt') }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install requests
      - name: Run API health-check
        run: |
          python - <<'PY'
          import requests, sys
          r = requests.get("https://your-domain.com/health", timeout=30)
          print("status:", r.status_code)
          sys.exit(0 if r.ok else 1)
          PY

  ui-tests:
    needs: api-health-check
    runs-on:
      - self-hosted
      - windows
      - server1
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox]
    steps:
      - name: Checkout tests
        uses: actions/checkout@v6
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install behave selenium allure-behave webdriver-manager
      - name: Run BDD UI tests
        run: |
          behave your-solution-root-folder-name/features `
            --tags "${{ inputs.tags || '@smoke' }}" `
            -D browser=${{ matrix.browser }} `
            -f allure_behave.formatter:AllureFormatter `
            -o reports/allure-results/${{ matrix.browser }}
        shell: pwsh
      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results-${{ matrix.browser }}
          path: reports/allure-results/${{ matrix.browser }}
      - name: Upload failure screenshots
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: screenshots-${{ matrix.browser }}
          path: reports/screenshots/

  report-and-notify:
    needs: ui-tests
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Download Allure results
        uses: actions/download-artifact@v8
        with:
          pattern: allure-results-*
          path: reports/allure-results
          merge-multiple: true
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - name: Analyze Allure report
        run: |
          python -m pip install allure-report-analyzer
          allure-report-analyzer reports/allure-results --out reports/metrics.json
      - name: Email QA summary
        run: |
          python your-solution-root-folder-name/scripts/send_report.py \
            --metrics reports/metrics.json
        env:
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          EMAIL_USERNAME: ${{ secrets.EMAIL_USERNAME }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
```

### YAML Explanation

- `schedule` runs the smoke suite nightly at 1:30 AM UTC.
- `workflow_dispatch` inputs let QA rerun manually and pick the tags filter and browser.
- API health-check, BDD UI tests, and reporting are separate, dependent jobs.
- The browser matrix runs chrome and firefox in parallel on the `server1` self-hosted runner.
- `if: always()` preserves Allure results and screenshots even when scenarios fail.
- The final job analyzes Allure metrics and emails pass-rate / failed IDs over SMTP.

### Expected Output

- Nightly workflow runs automatically at 1:30 AM UTC.
- API health-check gates the UI tests.
- Allure results and screenshots are uploaded as artifacts.
- An email summary with pass-rate and failed scenario IDs is sent.

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
          - server1
          - server2
          - server3
          - server4
        default: server1

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

You cannot rename a runner from workflow YAML. Set the runner name when registering the self-hosted runner, then target it with a stable label such as `server1`.

### Run a Windows Executable

```yaml
jobs:
  regression-check:
    runs-on:
      - self-hosted
      - windows
      - server1
    steps:
      - name: Run TestExecute regression batch
        shell: pwsh
        run: |
          & "C:\Tools\TestExecute\TestExecute.exe" `
            ".\your-solution-root-folder-name\Regression.pjs" `
            /run /tags:smoke `
            /exportLog:".\reports\regression.mht"
```

Quote executable paths that contain spaces and let PowerShell's call operator `&` execute the file. This mirrors a typical desktop/UI regression flow driven by an executable test runner and batch files.

### Install and Run a Pip Package With Parameters

```yaml
jobs:
  package-command:
    runs-on: ubuntu-latest
    steps:
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"

      - name: Install package command
        run: |
          python -m pip install --upgrade pip
          python -m pip install allure-report-analyzer

      - name: Run package command with parameters
        run: |
          allure-report-analyzer \
            --suite regression \
            --browser chrome \
            --out reports/metrics.json
```

Pin package versions for production workflows when reproducibility matters.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a smoke test workflow. | Smoke test runs on PR. |
| Intermediate | Upload Allure results and screenshots as artifacts. | Evidence is available after failure or success. |
| Challenge | Create a nightly API health-check + BDD UI (browser matrix) + Allure report + email chain. | Scheduled QA workflow runs daily at 1:30 AM UTC. |

---

[Previous: Module 17](./module-17-release-automation.md) | [Module Index](./README.md) | [Next: Module 19](./module-19-monorepo-best-practices.md)
