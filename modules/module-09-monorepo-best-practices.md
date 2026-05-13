# Module 9: Monorepos, Enterprise Patterns, and Self-Hosted Runners

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 8](./module-08-qa-automation.md) | [Next: Module 10](./module-10-notifications.md)
> Level: **Advanced** | Time: **150 min** | Example workflow: [`module-09-monorepo-best-practices.yml`](../examples/module-09-monorepo-best-practices.yml)

## Learning Objectives

- Use path filters and selective CI in monorepos.
- Apply enterprise governance patterns.
- Use self-hosted runners safely.

## Key Concepts

monorepos, path filtering, CODEOWNERS, self-hosted runners, runner labels

## Expected Outcome

You can keep large repositories and enterprise runners maintainable and safe.

## Concept Flow

```text
Pull Request -> Changed Path Detection -> Selective Jobs -> Required Checks -> Safe Runner Selection
```

---

## ELI5 Explanation

A monorepo is one big repository with many projects. A self-hosted runner is your own machine that GitHub can ask to run jobs.

## Technical Explanation

Monorepo workflows use path filters, selective jobs, reusable workflows, and shared conventions to avoid running unnecessary pipelines. Enterprise workflows also include CODEOWNERS, branch protection, required checks, security scans, and self-hosted runners for private infrastructure, special hardware, or compliance needs.

## Real-World Use Case

A monorepo has a frontend, backend, and QA suite. A frontend-only change should not run backend deployment jobs.

## When To Use

- One repository contains many services.
- Full CI is too slow or expensive.
- Teams own different folders.
- Jobs need private network access, special hardware, or compliance-controlled execution.

## When NOT To Use

- You cannot patch and secure self-hosted runners.
- GitHub-hosted runners are sufficient.
- Shared code changes affect many projects and path filtering may skip required checks.

## Common Mistakes

- Trusting path filters without testing edge cases.
- Running untrusted fork code on privileged self-hosted runners.
- Leaving self-hosted runners unpatched.
- Sharing runner labels too broadly.

## Debugging Tips

- Print changed files during path-based workflows.
- Use separate labels for runner purpose.
- Restrict self-hosted runners to trusted repositories.
- Use `pull_request_target` with extreme caution.

## Minimal Workflow Example

```yaml
name: Path Filter Demo

on:
  pull_request:
    paths:
      - "frontend/**"

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - name: Run frontend checks
        run: echo "Frontend changed"
```

### YAML Explanation

- `paths` limits the workflow to frontend changes.
- The job runs only when files under `frontend/` change.
- This keeps pull request feedback focused.

### Step-by-Step Execution

1. Pull request updates files.
2. GitHub checks changed paths.
3. Workflow runs only if `frontend/**` changed.
4. Frontend checks execute.

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
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
      qa: ${{ steps.filter.outputs.qa }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Detect changed areas
        id: filter
        uses: dorny/paths-filter@v3
        with:
          filters: |
            frontend:
              - 'frontend/**'
            backend:
              - 'backend/**'
            qa:
              - 'tests/**'
              - 'qa/**'

  frontend-ci:
    needs: detect-changes
    if: ${{ needs.detect-changes.outputs.frontend == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - name: Run frontend CI
        run: echo "Run frontend build and tests"

  backend-ci:
    needs: detect-changes
    if: ${{ needs.detect-changes.outputs.backend == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - name: Run backend CI
        run: echo "Run backend build and tests"

  qa-ci:
    needs: detect-changes
    if: ${{ needs.detect-changes.outputs.qa == 'true' }}
    runs-on: self-hosted
    steps:
      - name: Run QA suite on self-hosted runner
        run: echo "Run QA tests requiring private test environment"
```

### YAML Explanation

- `dorny/paths-filter` creates outputs for changed areas.
- Jobs use `if` conditions to run only when their area changed.
- `runs-on: self-hosted` targets an organization-controlled runner.

### Expected Output

- Only affected jobs run.
- QA job uses a self-hosted runner.
- Pull request checks remain focused and faster.

## Path Filter Examples

### Pull Request on a Specific Folder

```yaml
name: API Pull Request Checks

on:
  pull_request:
    branches:
      - main
    paths:
      - "services/api/**"
      - ".github/workflows/api-pr.yml"

jobs:
  api-pr:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Run API pull request checks"
```

### Push on a Specific Folder

```yaml
name: API Push Checks

on:
  push:
    branches:
      - main
      - "release/**"
    paths:
      - "services/api/**"

jobs:
  api-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Run API checks after a folder-scoped push"
```

Use path filters to reduce unnecessary work, then document which folders own which checks so required status checks stay predictable.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Trigger workflow only for `frontend/**`. | Backend changes do not run workflow. |
| Intermediate | Add path filters for frontend and backend. | Only affected jobs run. |
| Challenge | Add a self-hosted runner job for QA tests. | QA job targets `self-hosted` runner label. |

---

[Previous: Module 8](./module-08-qa-automation.md) | [Module Index](./README.md) | [Next: Module 10](./module-10-notifications.md)
