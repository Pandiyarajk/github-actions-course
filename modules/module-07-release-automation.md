# Module 7: Deployment, Versioning, Tagging, and Release Automation

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 6](./module-06-docker-performance.md) | [Next: Module 8](./module-08-qa-automation.md)
> Level: **Intermediate** | Time: **150 min** | Example workflow: [`module-07-release-automation.yml`](../examples/module-07-release-automation.yml)

## Learning Objectives

- Separate build and deployment stages.
- Use environments, approvals, tags, and release evidence.
- Create deployment workflows with rollback awareness.

## Key Concepts

environments, approvals, concurrency, immutable artifacts, tags, releases

## Expected Outcome

You can design deployment pipelines with audit trails, approvals, and release markers.

## Concept Flow

```text
Main Branch -> Build Artifact -> Staging Deploy -> Approval Gate -> Production Deploy -> Tag / Release
```

---

## ELI5 Explanation

Deployment is moving your app to a place where users can use it. A release is a labeled package of changes. Tags are bookmarks pointing to exact versions of your code.

## Technical Explanation

Deployment workflows often use environments, approvals, concurrency, version tags, release notes, artifacts, and rollback plans. Production pipelines should separate build and deploy, promote immutable artifacts, and use manual approvals for high-risk environments.

## Real-World Use Case

When code merges to `main`, the app deploys to staging automatically. Production deployment requires manual approval and creates a GitHub release.

## When To Use

- Deployment steps are repeatable.
- You need audit trails.
- You want approval gates.
- You need release notes and versioning.

## When NOT To Use

- The system is not tested enough.
- Rollback is manual or unclear.
- Compliance requires stricter human approval.

## Common Mistakes

- Deploying directly from untested source.
- No concurrency control.
- Rebuilding separately for staging and production.
- Missing rollback strategy.

## Debugging Tips

- Use environments to track deployments.
- Add `concurrency` to prevent overlapping deploys.
- Store deployment artifacts.
- Log deployed version and commit SHA.

## Minimal Workflow Example

```yaml
name: Manual Deploy

on: workflow_dispatch

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Run sample deployment command
        run: echo "Deploying commit ${{ github.sha }}"
```

### YAML Explanation

- `workflow_dispatch` makes deployment manual.
- The job runs on an Ubuntu runner.
- `${{ github.sha }}` identifies the exact commit being deployed.

### Step-by-Step Execution

1. User manually starts workflow.
2. Runner starts deployment job.
3. Command prints the deployed commit.
4. In real systems, this step calls deployment scripts.

## Production Workflow Example

```yaml
name: Staging and Production Deploy

on:
  push:
    branches:
      - main

permissions:
  contents: write
  deployments: write

concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Build application
        run: |
          mkdir -p dist
          echo "build from $GITHUB_SHA" > dist/version.txt
      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: app-build
          path: dist/

  deploy-staging:
    needs: build
    environment: staging
    runs-on: ubuntu-latest
    steps:
      - name: Download build artifact
        uses: actions/download-artifact@v4
        with:
          name: app-build
          path: dist/
      - name: Deploy to staging
        run: echo "Deploy staging using dist/"

  deploy-production:
    needs: deploy-staging
    environment: production
    runs-on: ubuntu-latest
    steps:
      - name: Download build artifact
        uses: actions/download-artifact@v4
        with:
          name: app-build
          path: dist/
      - name: Deploy to production
        run: echo "Deploy production using approved artifact"
      - name: Create release tag
        run: |
          git tag "release-${{ github.run_number }}"
          git push origin "release-${{ github.run_number }}"
```

### YAML Explanation

- `concurrency` prevents overlapping deployments.
- `build` creates one artifact.
- Staging and production deploy the same artifact.
- `environment: production` can require approval.
- The release tag identifies the deployed run.

### Expected Output

- Build artifact is created once.
- Staging deploy runs first.
- Production waits for environment approval.
- Release tag points to deployed commit.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create a manual deployment workflow. | Manual deploy runs successfully. |
| Intermediate | Add staging and production environments. | Production waits for approval. |
| Challenge | Create a release tag after production deploy. | Tag appears in repository. |

---

[Previous: Module 6](./module-06-docker-performance.md) | [Module Index](./README.md) | [Next: Module 8](./module-08-qa-automation.md)
