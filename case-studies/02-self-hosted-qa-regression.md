# Self-Hosted QA Regression Workflows

![Case Study](https://img.shields.io/badge/Case%20Study-2-1f6feb?style=flat-square) ![Difficulty](https://img.shields.io/badge/Difficulty-%E2%98%85%E2%98%85-cf222e?style=flat-square) ![Level](https://img.shields.io/badge/Level-Advanced-cf222e?style=flat-square) [![Case Studies](https://img.shields.io/badge/%E2%AC%85%20Case%20Studies-555?style=flat-square)](README.md)

> Level: **Advanced** | Suggested modules: **Module 5, Module 6, Module 18**

## 1. Title

Self-Hosted QA Regression Workflow for `web-service`

## 2. What This Workflow Does

This case study teaches how to run long QA automation on selected self-hosted runners. It generalizes patterns for runner setup, manual regression runs, scheduled suites, optional test batches, failed-test reruns, and test-cycle maintenance.

Real-world scenario: QA needs to run browser, desktop, or integration regression tests on controlled machines that have licensed software, test data, browsers, or private network access.

## 3. When to Use This

- Use it for long-running regression suites.
- Use it when tests require private infrastructure or licensed tools.
- Use it when QA needs manual control over runner selection.
- Use it when failed tests should be rerun without executing the full suite.

## 4. Workflow Breakdown

- **Trigger (`on`)**: `workflow_dispatch` lets QA choose runner and suite; `schedule` supports nightly regression.
- **Jobs**: One runner-bound job executes the selected test path.
- **Steps**: Checkout, prepare runner, resolve test selection, execute tests, upload evidence.
- **Actions used**: `actions/checkout`, `actions/upload-artifact`.
- **Conditions**: Batch execution runs only when a batch file or failed-test list exists.
- **Outputs**: Test IDs via `$GITHUB_OUTPUT`, reports as artifacts, and summaries via `$GITHUB_STEP_SUMMARY`.

## 5. ASCII Flow Diagram

```text
Manual / Scheduled Trigger
   |
   v
Choose Self-Hosted Runner
   |
   v
Prepare Test Machine
   |
   +--> Full Suite
   +--> Selected Batch
   +--> Failed-Test Rerun
   |
   v
Generate Report
   |
   v
Upload QA Evidence
```

## 6. Simple Version YAML

```yaml
name: Manual QA Regression

on:
  workflow_dispatch:
    inputs:
      runner:
        type: choice
        options:
          - qa-runner-1
          - qa-runner-2
        default: qa-runner-1
      suite:
        type: choice
        options:
          - smoke
          - regression
        default: smoke

jobs:
  regression:
    runs-on: ${{ inputs.runner }}
    timeout-minutes: 240
    steps:
      - name: Checkout tests
        uses: actions/checkout@v6

      - name: Run selected suite
        shell: pwsh
        run: ./scripts/run-tests.ps1 -Suite "${{ inputs.suite }}" -Output reports

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: qa-report
          path: reports/**
```

## 7. Production Version YAML

```yaml
name: Production QA Regression

on:
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:
    inputs:
      runner:
        type: choice
        options:
          - qa-runner-1
          - qa-runner-2
          - qa-runner-3
        default: qa-runner-1
      suite:
        type: choice
        options:
          - smoke
          - regression
          - api
        default: regression
      batch_file:
        type: string
        required: false
        default: ""
      rerun_failures:
        type: boolean
        default: false

permissions:
  contents: read

concurrency:
  group: qa-${{ inputs.runner || 'scheduled-runner' }}
  cancel-in-progress: false

jobs:
  regression:
    runs-on: ${{ inputs.runner || 'qa-runner-1' }}
    timeout-minutes: 720
    env:
      API_TOKEN: ${{ secrets.API_TOKEN }}
    steps:
      - name: Checkout tests
        uses: actions/checkout@v6

      - name: Prepare runner
        shell: pwsh
        run: |
          ./scripts/stop-test-processes.ps1
          New-Item -ItemType Directory -Force reports | Out-Null

      # The helper picks the test IDs: failed-tests.json (rerun), else the
      # chosen batch file, else empty = run the full suite. It writes
      # `test_ids` to the step output so the next two steps can branch on it.
      - name: Resolve test IDs
        id: tests
        shell: pwsh
        run: |
          ./scripts/resolve-test-ids.ps1 `
            -RerunFailures "${{ inputs.rerun_failures }}" `
            -BatchFile "${{ inputs.batch_file }}"

      - name: Run selected tests
        if: steps.tests.outputs.test_ids != ''
        shell: pwsh
        run: ./scripts/run-tests.ps1 -TestIds "${{ steps.tests.outputs.test_ids }}" -Output reports

      - name: Run full suite
        if: steps.tests.outputs.test_ids == ''
        shell: pwsh
        run: ./scripts/run-tests.ps1 -Suite "${{ inputs.suite || 'regression' }}" -Output reports

      - name: Write QA summary
        if: always()
        shell: pwsh
        run: |
          "## QA Regression Summary" >> $env:GITHUB_STEP_SUMMARY
          "- Runner: ${{ runner.name }}" >> $env:GITHUB_STEP_SUMMARY
          "- Suite: ${{ inputs.suite || 'scheduled' }}" >> $env:GITHUB_STEP_SUMMARY
          "- Status: ${{ job.status }}" >> $env:GITHUB_STEP_SUMMARY

      - name: Upload QA evidence
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: qa-evidence-${{ github.run_number }}
          path: reports/**
          retention-days: 30
```

## 8. Line-by-Line Explanation

- `workflow_dispatch.inputs` gives QA controlled choices.
- `schedule` supports unattended nightly regression.
- `runs-on` targets named self-hosted runner labels.
- `concurrency` prevents overlapping jobs on the same runner.
- `API_TOKEN` is the only generic secret and is scoped to the job.
- The preparation step clears stale processes and creates report folders.
- The test resolver supports failed-test reruns and named batches.
- Separate test steps make conditional paths easy to read.
- `if: always()` preserves reports even when tests fail.

## 9. Common Mistakes

- Running untrusted fork code on privileged self-hosted runners.
- Using one broad `self-hosted` label for every runner.
- Forgetting to clean stale browser or desktop processes.
- Printing secret values while validating runner setup.
- Letting long-running tests execute without a timeout.

## 10. Debugging Guide

- Confirm the selected runner is online and has the expected labels.
- Print selected inputs, runner name, and workspace path.
- Upload raw logs, screenshots, and reports on every run.
- Validate batch JSON before running tests.
- Use concurrency groups to avoid two jobs controlling the same machine.

## 11. Exercises

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create a manual workflow with a runner input. | Workflow runs on the selected self-hosted runner. |
| Intermediate | Add a batch file input and conditional test execution. | Batch tests run only when a batch file is provided. |
| Challenge | Add failed-test rerun support and QA evidence artifacts. | Failed tests rerun and reports upload even after failures. |

---

[Case Study Index](README.md) | [Course Home](../README.md)
