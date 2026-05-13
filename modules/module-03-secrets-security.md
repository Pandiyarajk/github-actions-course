# Module 3: Secrets, Variables, and Secure Pipelines

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 2](./module-02-workflow-syntax.md) | [Next: Module 4](./module-04-matrix-and-reuse.md)
> Level: **Beginner** | Time: **120 min** | Example workflow: [`module-03-secrets-security.yml`](../examples/module-03-secrets-security.yml)

## Learning Objectives

- Choose between secrets, variables, and environments.
- Use least-privilege workflow permissions.
- Avoid exposing credentials in logs or pull requests.

## Key Concepts

secrets, variables, environments, permissions, masking, least privilege

## Expected Outcome

You can protect sensitive data and configure secure workflow boundaries.

## Concept Flow

```text
Protected Setting -> Secret / Variable -> Environment -> Job Permission -> Safe Runtime Use
```

---

## ELI5 Explanation

Secrets are locked notes. Your workflow can use them, but GitHub hides their values in logs so passwords and tokens are not exposed.

## Technical Explanation

GitHub Actions supports repository secrets, environment secrets, organization secrets, variables, and environment protection rules. Secrets are accessed using `${{ secrets.SECRET_NAME }}`. Variables are accessed using `${{ vars.VAR_NAME }}`. Production workflows should use least-privilege permissions, protected environments, and short-lived credentials where possible.

## Real-World Use Case

A deployment workflow needs an API key to deploy to staging, but only approved maintainers should be able to deploy to production.

## When To Use

- Storing tokens, passwords, API keys, or private credentials.
- Deploying to protected environments.
- Calling third-party APIs.

## When NOT To Use

- Non-sensitive configuration.
- Values that can safely live in repository variables.
- Cloud authentication when OIDC is available and preferred.

## Common Mistakes

- Printing secrets in logs.
- Using repository-wide secrets for production deployments.
- Giving workflows broad `write-all` permissions.
- Using long-lived cloud keys when OIDC is supported.

## Debugging Tips

- Print whether a secret exists, not the secret itself.
- Use environment-level secrets for deployment stages.
- Check environment approval rules.
- Verify workflow permissions before API calls.

## Minimal Workflow Example

```yaml
name: Secret Check

on: workflow_dispatch

jobs:
  check-secret:
    runs-on: ubuntu-latest
    steps:
      - name: Confirm secret is configured
        run: |
          if [ -z "${{ secrets.API_TOKEN }}" ]; then
            echo "API_TOKEN is missing"
            exit 1
          fi
          echo "API_TOKEN is configured"
```

### YAML Explanation

- `secrets.API_TOKEN` reads a GitHub secret.
- The script checks only whether the secret exists.
- The actual secret value is never printed.

### Step-by-Step Execution

1. User manually starts the workflow.
2. Runner checks whether `API_TOKEN` exists.
3. The workflow fails if the secret is missing.
4. The secret value remains hidden.

## Production Workflow Example

```yaml
name: Secure Staging Deploy

on:
  workflow_dispatch:

permissions:
  contents: read
  deployments: write

jobs:
  deploy-staging:
    environment: staging
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Validate required secret
        run: |
          if [ -z "${{ secrets.STAGING_API_TOKEN }}" ]; then
            echo "Missing STAGING_API_TOKEN"
            exit 1
          fi

      - name: Deploy to staging
        env:
          API_TOKEN: ${{ secrets.STAGING_API_TOKEN }}
          DEPLOY_URL: ${{ vars.STAGING_DEPLOY_URL }}
        run: |
          echo "Deploying to $DEPLOY_URL"
          echo "Use API_TOKEN here without printing it"
```

### YAML Explanation

- `environment: staging` uses environment-scoped secrets and approvals.
- `deployments: write` is required only if deployment records are written.
- `env` passes secret and variable values to the shell safely.
- `vars.STAGING_DEPLOY_URL` stores non-sensitive configuration.

### Expected Output

- Workflow requires access to the `staging` environment.
- Deployment uses an environment-scoped secret.
- Secret value remains masked.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create a repository secret and validate it exists. | Workflow passes when secret exists. |
| Intermediate | Move deployment config to repository variables. | Logs show non-sensitive config only. |
| Challenge | Add a protected environment with manual approval. | Deployment waits for approval. |

---

[Previous: Module 2](./module-02-workflow-syntax.md) | [Module Index](./README.md) | [Next: Module 4](./module-04-matrix-and-reuse.md)
