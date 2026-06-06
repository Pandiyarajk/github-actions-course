# Module 1: CI/CD and GitHub Actions Foundations

![Module](https://img.shields.io/badge/Module-1-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20A%20Components-1f6feb?style=flat-square) ![Level](https://img.shields.io/badge/Level-Beginner-2da44e?style=flat-square) ![Time](https://img.shields.io/badge/Time-90%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | Previous: none | [Next: Module 2](./module-02-workflow-naming.md)
> Level: **Beginner** | Time: **90 min** | Example workflow: [`module-01-ci-foundations.yml`](../examples/module-01-ci-foundations.yml)

## Learning Objectives

- Explain the CI/CD role of GitHub Actions.
- Create a basic workflow in `.github/workflows/`.
- Read workflow logs and identify runner, job, and step behavior.

## Key Concepts

workflow, event, runner, job, step, action, artifact

## Expected Outcome

You can create and run a basic GitHub Actions workflow with confidence.

## Concept Flow

```text
Code Change -> GitHub Event -> Workflow File -> Runner -> Job -> Step -> Status Check
```

---

## ELI5 Explanation

GitHub Actions is a robot assistant inside your repository. When something happens, such as pushing code or opening a pull request, the robot can run instructions: install Python dependencies, run your Behave (BDD) suites, drive Selenium browsers, or email an Allure report.

## Technical Explanation

A GitHub Actions workflow is a YAML file stored in `.github/workflows/`. It is triggered by GitHub events such as `push`, `pull_request`, `workflow_dispatch`, or `schedule`. Each workflow contains jobs. Each job runs on a runner. Each job contains steps that either run shell commands or call reusable actions. In real-world projects, web automation jobs run Selenium + Behave on GitHub-hosted `ubuntu-latest`, while desktop/UI regression jobs run on Windows self-hosted runners labeled `server1` through `server4`.

## Real-World Use Case

A team wants every pull request to automatically run the smoke suite (`behave --tags=smoke`) before allowing merge, so broken UI flows never reach `main`.

## When To Use

- You want CI/CD directly integrated with GitHub.
- You need automated Behave/Selenium testing on pull requests.
- You want repeatable test, report, and notification automation (Allure reports, SMTP email, Zephyr Scale + Jira updates).

## When NOT To Use

- Your organization requires a different centralized CI platform.
- Your workload needs specialized infrastructure unavailable through GitHub-hosted or self-hosted runners.
- Your workflow requires extremely long-running jobs beyond platform limits.

## Common Mistakes

- Placing workflow files outside `.github/workflows/`.
- Using invalid YAML indentation.
- Forgetting to commit the workflow file.
- Assuming a workflow runs without a matching event trigger.

## Debugging Tips

- Check the Actions tab for workflow run logs.
- Verify the workflow file exists on the branch where the event happened.
- Use `workflow_dispatch` while learning so you can trigger manually.
- Add `run: pwd && ls` to inspect runner state (use `run: cd your-solution-root-folder-name && ls` to confirm your suite was checked out).

## Minimal Workflow Example

```yaml
name: Hello CI

on: push

jobs:
  hello:
    runs-on: ubuntu-latest
    steps:
      - name: Print message
        run: echo "Hello from GitHub Actions"
```

### YAML Explanation

- `name` is the workflow name shown in the Actions UI.
- `on: push` starts the workflow whenever code is pushed.
- `jobs` contains work to run.
- `hello` is the job ID.
- `runs-on` selects the runner image.
- `steps` contains the commands or actions.
- `run` executes a shell command.

### Step-by-Step Execution

1. A developer pushes code.
2. GitHub detects the `push` event.
3. The workflow starts.
4. GitHub provisions an Ubuntu runner.
5. The job runs the echo command.
6. Logs appear in the Actions tab.

## Production Workflow Example

```yaml
name: Pull Request CI

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"

      - name: Print workflow context
        run: |
          echo "Repository: $GITHUB_REPOSITORY"
          echo "Branch: $GITHUB_REF"
          echo "Commit: $GITHUB_SHA"

      - name: Install dependencies
        working-directory: your-solution-root-folder-name
        run: pip install -r requirements.txt

      - name: Run smoke suite
        working-directory: your-solution-root-folder-name
        run: behave --tags=smoke
```

### YAML Explanation

- `pull_request` runs checks before code is merged.
- `branches: [main]` limits the trigger to pull requests targeting `main`.
- `permissions: contents: read` applies least privilege.
- `actions/checkout@v6` downloads the repository onto the runner.
- `actions/setup-python@v6` with `python-version: "3.13"` provisions the interpreter the Behave/Selenium suite expects.
- The context step prints safe runtime metadata.
- The validation step is where real Behave runs, `pylint`, or duplicate checks go.

### Expected Output

- Workflow run appears on pull requests.
- The job completes successfully.
- Logs show repository, branch, and commit details, followed by the `behave --tags=smoke` scenario results.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create a workflow that prints your name. | Successful workflow with one log line. |
| Intermediate | Trigger the workflow on both `push` and `pull_request`, set up Python 3.13, and run `behave --tags=smoke`. | Workflow runs for both events and executes the smoke suite. |
| Challenge | Add a manual `workflow_dispatch` trigger with an input called `browser` (chrome/firefox/msedge). | Manual run accepts a browser value used by the Selenium suite. |

---

Previous: none | [Module Index](./README.md) | [Next: Module 2](./module-02-workflow-naming.md)
