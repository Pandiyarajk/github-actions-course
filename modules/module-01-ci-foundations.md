# Module 1: CI/CD and GitHub Actions Foundations

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | Previous: none | [Next: Module 2](./module-02-workflow-syntax.md)
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

GitHub Actions is a robot assistant inside your repository. When something happens, such as pushing code or opening a pull request, the robot can run instructions: install dependencies, run tests, build the app, or deploy it.

## Technical Explanation

A GitHub Actions workflow is a YAML file stored in `.github/workflows/`. It is triggered by GitHub events such as `push`, `pull_request`, `workflow_dispatch`, or `schedule`. Each workflow contains jobs. Each job runs on a runner. Each job contains steps that either run shell commands or call reusable actions.

## Real-World Use Case

A team wants every pull request to automatically run unit tests before allowing merge.

## When To Use

- You want CI/CD directly integrated with GitHub.
- You need automated testing on pull requests.
- You want repeatable build, test, release, or deployment automation.

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
- Add `run: pwd && ls` to inspect runner state.

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
        uses: actions/checkout@v4

      - name: Print workflow context
        run: |
          echo "Repository: $GITHUB_REPOSITORY"
          echo "Branch: $GITHUB_REF"
          echo "Commit: $GITHUB_SHA"

      - name: Run validation
        run: echo "Run lint, tests, or build here"
```

### YAML Explanation

- `pull_request` runs checks before code is merged.
- `branches: [main]` limits the trigger to pull requests targeting `main`.
- `permissions: contents: read` applies least privilege.
- `actions/checkout@v4` downloads the repository onto the runner.
- The context step prints safe runtime metadata.
- The validation step is where real lint, test, or build commands go.

### Expected Output

- Workflow run appears on pull requests.
- The job completes successfully.
- Logs show repository, branch, and commit details.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create a workflow that prints your name. | Successful workflow with one log line. |
| Intermediate | Trigger the workflow on both `push` and `pull_request`. | Workflow runs for both events. |
| Challenge | Add a manual `workflow_dispatch` trigger with an input called `environment`. | Manual run accepts an environment value. |

---

Previous: none | [Module Index](./README.md) | [Next: Module 2](./module-02-workflow-syntax.md)
