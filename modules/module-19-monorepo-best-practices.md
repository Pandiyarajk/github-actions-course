# Module 19: Monorepos, Enterprise Patterns, and Self-Hosted Runners

![Module](https://img.shields.io/badge/Module-19-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20B%20Applied-8957e5?style=flat-square) ![Level](https://img.shields.io/badge/Level-Advanced-cf222e?style=flat-square) ![Time](https://img.shields.io/badge/Time-150%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 18](./module-18-qa-automation.md) | [Next: Module 20](./module-20-notifications.md)
> Level: **Advanced** | Time: **150 min** | Example workflow: [`module-19-monorepo-best-practices.yml`](../examples/module-19-monorepo-best-practices.yml)

## Learning Objectives

- Use path filters and selective CI in a Selenium + Behave automation repo.
- Apply enterprise governance patterns.
- Use self-hosted runners (server1..server4) safely.

## Key Concepts

monorepos, path filtering, CODEOWNERS, self-hosted runners, runner labels

## Expected Outcome

You can keep large test-automation repositories and enterprise self-hosted runners maintainable and safe.

## Concept Flow

```text
Pull Request -> Changed Path Detection -> Selective Jobs -> Required Checks -> Safe Runner Selection
```

---

## ELI5 Explanation

A monorepo is one big repository with many parts. In a web automation suite that means `pageobjects/`, `features/steps/`, and `.github/scripts/` all living together. A self-hosted runner is your own machine (server1..server4) that GitHub can ask to run jobs.

## Technical Explanation

Automation repos for Selenium + Behave web suites and desktop/UI regression suites hold page objects, feature/step files, query helpers, and report scripts side by side. Path filters and selective jobs avoid running every static check and `behave` smoke run on unrelated changes. Enterprise workflows also include CODEOWNERS, branch protection, required checks, security scans, and self-hosted runners (server1..server4) for private test environments, browser access, special hardware, or compliance needs.

## Real-World Use Case

A pull request that edits only `pageobjects/` should run `pylint` and `check-duplicate-variables` against the page objects, but should not trigger a full Behave smoke run if no feature or step files changed.

## When To Use

- One repository contains page objects, features/steps, queries, and report scripts.
- Full CI (all static checks plus `behave` smoke) is too slow or expensive.
- Teams own different folders (`pageobjects/`, `features/steps/`, `.github/scripts/`).
- Jobs need a real browser (chrome/firefox/msedge), private network access, or a Windows host (server1..server4).

## When NOT To Use

- You cannot patch and secure self-hosted runners (server1..server4).
- GitHub-hosted `ubuntu-latest` runners are sufficient.
- Shared code (e.g., `reusables/queries.py`) changes affect many suites and path filtering may skip required checks.

## Common Mistakes

- Trusting path filters without testing edge cases (e.g., a shared `queries.py` edit).
- Running untrusted fork code on privileged self-hosted runners (server1..server4).
- Leaving self-hosted runners unpatched.
- Sharing runner labels too broadly across projects.

## Debugging Tips

- Print changed files during path-based workflows.
- Use separate labels (server1..server4) for runner purpose and machine.
- Restrict self-hosted runners to trusted repositories only.
- Use `pull_request_target` with extreme caution.

## Minimal Workflow Example

```yaml
name: Path Filter Demo

on:
  pull_request:
    paths:
      - "your-solution-root-folder-name/pageobjects/**"

jobs:
  pageobjects:
    runs-on: ubuntu-latest
    steps:
      - name: Run page object checks
        run: echo "Page objects changed"
```

### YAML Explanation

- `paths` limits the workflow to page object changes.
- The job runs only when files under `your-solution-root-folder-name/pageobjects/` change.
- This keeps pull request feedback focused.

### Step-by-Step Execution

1. Pull request updates files.
2. GitHub checks changed paths.
3. Workflow runs only if `your-solution-root-folder-name/pageobjects/**` changed.
4. Page object checks execute.

## Production Workflow Example

```yaml
name: Monorepo Selective CI

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read
  pull-requests: read

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      pageobjects: ${{ steps.filter.outputs.pageobjects }}
      steps: ${{ steps.filter.outputs.steps }}
      scripts: ${{ steps.filter.outputs.scripts }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v7
      - name: Detect changed areas
        id: filter
        uses: dorny/paths-filter@v3
        with:
          filters: |
            pageobjects:
              - 'your-solution-root-folder-name/pageobjects/**'
              - 'your-solution-root-folder-name/reusables/queries.py'
            steps:
              - 'your-solution-root-folder-name/features/**'
              - 'your-solution-root-folder-name/steps/**'
            scripts:
              - '.github/scripts/**'

  static-checks:
    needs: detect-changes
    if: ${{ needs.detect-changes.outputs.pageobjects == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - name: Run static analysis on page objects
        run: |
          pylint your-solution-root-folder-name/pageobjects/ your-solution-root-folder-name/reusables/queries.py
          python .github/scripts/check-duplicate-functions.py your-solution-root-folder-name/pageobjects/
          python .github/scripts/check-duplicate-variables.py your-solution-root-folder-name/pageobjects/

  behave-smoke:
    needs: detect-changes
    if: ${{ needs.detect-changes.outputs.steps == 'true' }}
    runs-on: [self-hosted, server1]
    steps:
      - uses: actions/checkout@v7
      - name: Run Behave smoke on self-hosted runner
        run: behave --tags=@smoke -f allure_behave.formatter:AllureFormatter -o allure-results
```

### YAML Explanation

- `dorny/paths-filter@v3` creates outputs for changed areas (page objects, steps, scripts).
- Jobs use `if` conditions so static checks and the `behave` smoke run only when their area changed.
- `runs-on: [self-hosted, server1]` targets an organization-controlled runner with a real browser.

### Expected Output

- Only affected jobs run.
- The Behave smoke job uses a self-hosted runner (server1).
- Pull request checks remain focused and faster.

## Path Filter Examples

### Pull Request on a Specific Folder

```yaml
name: Page Objects Pull Request Checks

on:
  pull_request:
    branches:
      - main
    paths:
      - "your-solution-root-folder-name/pageobjects/**"
      - ".github/workflows/pageobjects-pr.yml"

jobs:
  pageobjects-pr:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - run: pylint your-solution-root-folder-name/pageobjects/
```

### Push on a Specific Folder

```yaml
name: Page Objects Push Checks

on:
  push:
    branches:
      - main
      - "release/**"
    paths:
      - "your-solution-root-folder-name/pageobjects/**"

jobs:
  pageobjects-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - run: echo "Run page object checks after a folder-scoped push"
```

Use path filters to reduce unnecessary work, then document which folders own which checks so required status checks stay predictable.

## Self-Hosted Runners and Server Selection

These real-world projects run on Windows self-hosted runners labeled `server1`..`server4`. Use these patterns to run safely:

- Target a specific machine with combined labels: `runs-on: [self-hosted, server2]`.
- Keep runner labels narrow so a job does not accidentally land on the wrong host.
- Never run untrusted fork PR code on a self-hosted runner; restrict runners to trusted repositories and patch them regularly.
- For Behave web runs, the runner must have the target browser installed (chrome/firefox/msedge).

Let operators pick the runner at dispatch time with a `workflow_dispatch` choice input:

```yaml
name: On-Demand Behave Smoke

on:
  workflow_dispatch:
    inputs:
      runner:
        description: "Self-hosted runner to use"
        type: choice
        required: true
        default: server1
        options:
          - server1
          - server2
          - server3
          - server4
      browser:
        description: "Browser for the smoke run"
        type: choice
        required: true
        default: chrome
        options:
          - chrome
          - firefox
          - msedge

jobs:
  smoke:
    runs-on: [self-hosted, "${{ inputs.runner }}"]
    steps:
      - uses: actions/checkout@v7
      - name: Run Behave smoke
        run: behave --tags=@smoke -D browser=${{ inputs.browser }} -f allure_behave.formatter:AllureFormatter -o allure-results
      - name: Upload Allure results
        uses: actions/upload-artifact@v7
        with:
          name: allure-results-${{ inputs.runner }}
          path: allure-results
```

The `runner` choice input is interpolated into the `runs-on` label list, so the operator selects server1..server4 without editing the workflow.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Trigger workflow only for `your-solution-root-folder-name/pageobjects/**`. | Step-file changes do not run the workflow. |
| Intermediate | Add path filters for `pageobjects/`, `features/steps/`, and `.github/scripts/`. | Only affected jobs (pylint/check-duplicate-variables, behave smoke) run. |
| Challenge | Add a `workflow_dispatch` choice input to pick the self-hosted runner. | Behave smoke job targets the chosen `self-hosted` runner label (server1..server4). |

---

[Previous: Module 18](./module-18-qa-automation.md) | [Module Index](./README.md) | [Next: Module 20](./module-20-notifications.md)
