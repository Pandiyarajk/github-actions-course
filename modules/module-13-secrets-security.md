# Module 13: Secrets, Variables, and Secure Pipelines

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 12](./module-12-workflow-syntax.md) | [Next: Module 14](./module-14-matrix-and-reuse.md)
> Level: **Beginner** | Time: **120 min** | Example workflow: [`module-13-secrets-security.yml`](../examples/module-13-secrets-security.yml)

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

Secrets are locked notes. Your Behave/Selenium workflow can use them, but GitHub hides their values in logs so tokens like `ZEPHYR_SCALE_TOKEN` and `EMAIL_PASS` are not exposed.

## Technical Explanation

GitHub Actions supports repository secrets, environment secrets, organization secrets, variables, and environment protection rules. Secrets are accessed using `${{ secrets.SECRET_NAME }}`. Variables are accessed using `${{ vars.VAR_NAME }}`. In a Selenium + Behave web automation pipeline and a desktop/UI regression pipeline, secrets like `ZEPHYR_SCALE_TOKEN`, `JIRA_API_TOKEN`, and the SMTP/email credentials should use least-privilege permissions, protected environments, and short-lived tokens where possible.

## Real-World Use Case

The daily scheduled smoke-test workflow needs `ZEPHYR_SCALE_TOKEN` and `JIRA_API_TOKEN` to publish Behave results to Zephyr Scale and Jira, plus `EMAIL_USER`/`EMAIL_PASS`/`SMTP_HOST` to send the Allure report by email, but only approved maintainers should be able to run the production reporting stage.

## When To Use

- Storing tokens, passwords, API keys, or private credentials (Zephyr, Jira, SMTP).
- Publishing test results to protected environments.
- Calling third-party APIs such as Zephyr Scale or the Jira REST API.

## When NOT To Use

- Non-sensitive configuration (e.g. `EMAIL_TO`, `EMAIL_CC`, browser name).
- Values that can safely live in repository variables.
- Cloud authentication when OIDC is available and preferred.

## Common Mistakes

- Printing secrets in logs (for example echoing `JIRA_API_TOKEN`).
- Using repository-wide secrets for production reporting runs.
- Giving workflows broad `write-all` permissions.
- Using long-lived cloud keys when OIDC is supported.

## Debugging Tips

- Print whether a secret exists, not the secret itself.
- Use environment-level secrets for the production reporting stage.
- Check environment approval rules.
- Verify workflow permissions before calling Zephyr/Jira APIs.

## Minimal Workflow Example

```yaml
name: Secret Check

on: workflow_dispatch

jobs:
  check-secret:
    runs-on: ubuntu-latest
    steps:
      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"

      - name: Confirm secret is configured
        env:
          ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
        run: |
          set +x
          python -c "import os, sys; sys.exit(0 if os.environ.get('ZEPHYR_SCALE_TOKEN') else 1)" \
            && echo "ZEPHYR_SCALE_TOKEN is configured" \
            || { echo "ZEPHYR_SCALE_TOKEN is missing"; exit 1; }
```

### YAML Explanation

- `secrets.ZEPHYR_SCALE_TOKEN` reads a GitHub secret into an env var.
- The Python one-liner checks only whether the secret exists in `os.environ`.
- `set +x` keeps the value out of the log; the actual secret is never printed.

### Step-by-Step Execution

1. User manually starts the workflow.
2. Runner checks whether `ZEPHYR_SCALE_TOKEN` exists via a Python assertion.
3. The workflow fails if the secret is missing.
4. The secret value remains hidden.

## Production Workflow Example

```yaml
name: Secure Smoke Report

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  smoke-report:
    environment: production
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"

      - name: Validate required secrets
        env:
          ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
        run: |
          set +x
          python -c "import os, sys; missing=[k for k in ('ZEPHYR_SCALE_TOKEN','JIRA_API_TOKEN','EMAIL_PASS') if not os.environ.get(k)]; sys.exit('Missing: '+', '.join(missing)) if missing else None"

      - name: Publish results and email Allure report
        working-directory: your-solution-root-folder-name/
        env:
          ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
          ZEPHYR_CYCLE_ID: ${{ secrets.ZEPHYR_CYCLE_ID }}
          JIRA_EMAIL: ${{ secrets.JIRA_EMAIL }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
          JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          EMAIL_TO: ${{ vars.EMAIL_TO }}
          EMAIL_CC: ${{ vars.EMAIL_CC }}
        run: |
          set +x
          python scripts/publish_zephyr.py
          python scripts/send_report.py
```

### YAML Explanation

- `environment: production` uses environment-scoped secrets and approvals.
- The validation step asserts the required secrets exist using Python, never printing values.
- `env` passes Zephyr, Jira, and SMTP secrets to the report scripts safely; `set +x` prevents echoing.
- `vars.EMAIL_TO` and `vars.EMAIL_CC` store non-sensitive recipient configuration.

### Expected Output

- Workflow requires access to the `production` environment.
- Reporting uses environment-scoped secrets for Zephyr/Jira/SMTP.
- Secret values remain masked.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create the `ZEPHYR_SCALE_TOKEN` repository secret and validate it exists with a Python assertion. | Workflow passes when secret exists. |
| Intermediate | Move `EMAIL_TO`/`EMAIL_CC` recipient config to repository variables. | Logs show non-sensitive config only. |
| Challenge | Add a protected `production` environment with manual approval for the reporting job. | Reporting waits for approval. |

---

[Previous: Module 12](./module-12-workflow-syntax.md) | [Module Index](./README.md) | [Next: Module 14](./module-14-matrix-and-reuse.md)
