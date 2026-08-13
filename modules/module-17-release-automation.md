# Module 17: Deployment, Versioning, Tagging, and Release Automation

![Module](https://img.shields.io/badge/Module-17-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20B%20Applied-8957e5?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-150%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 16](./module-16-docker-performance.md) | [Next: Module 18](./module-18-qa-automation.md)
> Level: **Intermediate** | Time: **150 min** | Example workflow: [`module-17-release-automation.yml`](../examples/module-17-release-automation.yml)
> Solutions: [`module-17-solutions.md`](../solutions/module-17-solutions.md)

## Learning Objectives

- Separate the regression-gate stage from the release stage.
- Use environments, approvals, tags, and release evidence (Allure reports, Zephyr cycles).
- Create release workflows with rollback awareness.

## Key Concepts

environments, approvals, concurrency, immutable Allure artifacts, tags, GitHub releases, Zephyr Scale test cycles

## Expected Outcome

You can design release pipelines for a test-automation suite with audit trails, approvals, and release markers.

## Concept Flow

```text
Main Branch -> Regression Gate (behave) -> Allure Artifact -> Approval Gate -> Zephyr Cycle -> Tag / GitHub Release
```

---

## ELI5 Explanation

In a test-automation context a "release" is not shipping an app, it is certifying a version. You run the full regression suite as a gate, label the results, and publish a record so everyone knows exactly which version was tested. Tags are bookmarks pointing to the exact commit that was certified.

## Technical Explanation

Release workflows for desktop/UI and web automation suites use environments, approvals, concurrency, version tags, release notes, Allure artifacts, and a rollback plan. A production release should separate the regression gate from the release step, promote the same immutable Allure artifact, and require manual approval before creating a Zephyr Scale test cycle and a GitHub Release with the `gh` CLI.

## Real-World Use Case

When code merges to `main`, the full Behave + Selenium regression suite runs automatically on a self-hosted runner (staging). A production release requires manual approval, then creates a Zephyr Scale test cycle for the release version and publishes a GitHub Release.

## When To Use

- The regression suite is repeatable and reliable.
- You need audit trails (which version was certified, by whom).
- You want approval gates before publishing a release.
- You need release notes, Zephyr cycles, and versioning.

## When NOT To Use

- The suite is flaky or not trusted yet.
- Rollback (re-running an older tagged suite) is manual or unclear.
- Compliance requires stricter human approval.

## Common Mistakes

- Releasing from a commit whose regression suite never passed.
- No concurrency control (two releases racing for the same Zephyr cycle).
- Re-running regression separately for staging and the release record.
- Missing rollback strategy (no tag to re-run the previous version).

## Debugging Tips

- Use environments to track who approved each release.
- Add `concurrency` to prevent overlapping release runs.
- Store the Allure report as an immutable artifact.
- Log the certified version and commit SHA in the release notes.

## Minimal Workflow Example

```yaml
name: Manual Release

on: workflow_dispatch

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Announce release candidate
        run: echo "Certifying commit ${{ github.sha }}"
```

### YAML Explanation

- `workflow_dispatch` makes the release manual.
- The job runs on a GitHub-hosted runner.
- `${{ github.sha }}` identifies the exact commit being certified.

### Step-by-Step Execution

1. User manually starts the workflow.
2. Runner starts the release job.
3. Command prints the certified commit.
4. In real pipelines, this step runs the regression gate and creates the release.

## Production Workflow Example

```yaml
name: Regression Gate and Production Release

on:
  push:
    branches:
      - main

permissions:
  contents: write
  deployments: write

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  regression-gate:
    runs-on: [self-hosted, server1]
    steps:
      - name: Checkout code
        uses: actions/checkout@v7
      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - name: Install dependencies
        run: |
          cd your-solution-root-folder-name
          pip install -r requirements.txt
          pip install behave selenium allure-behave
      - name: Run regression suite (gate)
        run: |
          cd your-solution-root-folder-name
          behave --tags=regression -f allure_behave.formatter:AllureFormatter -o allure-results
      - name: Upload Allure report
        uses: actions/upload-artifact@v7
        with:
          name: allure-report
          path: your-solution-root-folder-name/allure-results/

  release:
    needs: regression-gate
    environment:
      name: production
      url: https://prod.your-domain.com
    runs-on: [self-hosted, server1]
    steps:
      - name: Checkout code
        uses: actions/checkout@v7
      - name: Download Allure report
        uses: actions/download-artifact@v8
        with:
          name: allure-report
          path: allure-results/
      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - name: Create Zephyr Scale test cycle for release
        env:
          ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
          ZEPHYR_CYCLE_ID: ${{ secrets.ZEPHYR_CYCLE_ID }}
          JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
        run: |
          pip install zephyr-scale-test-cycle
          zephyr-scale-test-cycle create --name "Release ${{ github.run_number }}" --results allure-results/
      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release create "release-${{ github.run_number }}" \
            --title "Release ${{ github.run_number }}" \
            --notes "Regression certified on ${{ github.sha }}"
```

### YAML Explanation

- `concurrency` prevents overlapping release runs.
- `regression-gate` runs the full Behave suite once on `server1` and uploads the Allure report.
- The `release` job promotes the same Allure artifact instead of re-running tests.
- `environment: production` with a `url` can require manual approval.
- A Zephyr Scale cycle plus `gh release create` form the release record.

### Expected Output

- The Allure report is created once by the gate.
- The regression gate runs first and must pass.
- The release job waits for production environment approval.
- A Zephyr cycle and a GitHub Release tag point to the certified commit.

## Quiz

1. A release workflow must run automatically when a `v*` tag is pushed **and** be startable by hand for a hotfix. What is the correct `on:` block?
   - **A.** Only one trigger is allowed per workflow, so you need two workflow files.
   - **B.** `on:` with both `push: tags: ['v*']` and `workflow_dispatch:` — triggers are additive.
   - **C.** `on: push: tags: ['v*']` plus a `repository_dispatch` shim, because `workflow_dispatch` is ignored on tag-triggered workflows.
   - **D.** `on: release: types: [published]`, which covers manual runs automatically.

2. `gh release create` fails with a 403 from a workflow whose `permissions:` block reads `contents: read`. What is the fix?
   - **A.** Replace `GITHUB_TOKEN` with a personal access token; `GITHUB_TOKEN` can never create releases.
   - **B.** Raise the job or workflow permission to `contents: write`.
   - **C.** Add `releases: write`, the permission scope that governs releases.
   - **D.** Add `deployments: write`, since a release is a deployment.

3. You want a human to approve before the release job publishes. Where does that gate come from?
   - **A.** A job-level `environment:` whose required reviewers are configured in repository settings.
   - **B.** `approval: required` on the job.
   - **C.** `concurrency` with `cancel-in-progress: false`, which pauses the job for review.
   - **D.** A `workflow_dispatch` input named `approved`.

4. The regression gate and the release job each install dependencies and run `behave`. Explain why re-running the suite in the release job undermines the release record, and what the release job should do instead.

5. A release went out from a commit whose regression run had failed, because two release runs overlapped and the second one's tag pointed at the wrong commit. Name the two workflow-level controls that would have prevented this, and say what each one does.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create a manual release workflow. | Manual release runs successfully. |
| Intermediate | Add a regression-gate job and a production environment. | Release waits for approval. |
| Challenge | Create a Zephyr cycle and GitHub Release after the gate. | Cycle and release tag appear. |

Solutions: [`solutions/module-17-solutions.md`](../solutions/module-17-solutions.md)

---

[Previous: Module 16](./module-16-docker-performance.md) | [Module Index](./README.md) | [Next: Module 18](./module-18-qa-automation.md)
