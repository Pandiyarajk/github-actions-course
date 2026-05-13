# Module 10: Notifications, Observability, Debugging, and Governance

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 9](./module-09-monorepo-best-practices.md) | [Next: Capstones](../capstones/README.md)
> Level: **Advanced** | Time: **120 min** | Example workflow: [`module-10-notifications.yml`](../examples/module-10-notifications.yml)

## Learning Objectives

- Create actionable notifications and summaries.
- Debug workflows using logs, artifacts, and reruns.
- Apply production governance controls.

## Key Concepts

job summaries, notifications, observability, debug logging, governance

## Expected Outcome

You can make workflows easier to observe, debug, govern, and support in production.

## Concept Flow

```text
Workflow Result -> Job Summary -> Artifact Evidence -> Targeted Alert -> Debug / Rerun Decision
```

---

## ELI5 Explanation

Notifications tell the team what happened. Observability helps you understand why it happened. Governance keeps workflows safe, consistent, and maintainable.

## Technical Explanation

Production workflows should expose clear logs, artifacts, summaries, status notifications, concurrency controls, permissions, branch protections, required checks, and audit-friendly release evidence. Debugging strategies include grouped logs, step summaries, reruns with debug logging, artifacts, and targeted test isolation.

## Real-World Use Case

A failed deployment should notify Slack or Teams with the environment, commit, actor, workflow link, and rollback instructions.

## When To Use

- Failures need immediate team attention.
- Deployments need visibility.
- QA results must be shared.
- Multiple teams need shared workflow standards.

## When NOT To Use

- Every minor failure posts to a busy channel.
- The message does not include actionable details.
- Teams begin ignoring alerts.

## Common Mistakes

- Sending notifications for every successful CI run.
- Not including links to logs.
- Giving workflows excessive permissions.
- Missing `timeout-minutes` and `concurrency`.

## Debugging Tips

- Enable debug logging using repository secrets `ACTIONS_STEP_DEBUG` and `ACTIONS_RUNNER_DEBUG`.
- Add job summaries using `$GITHUB_STEP_SUMMARY`.
- Upload logs and reports as artifacts.
- Use `workflow_dispatch` inputs to reproduce failures.

## Minimal Workflow Example

```yaml
name: Workflow Summary

on: workflow_dispatch

jobs:
  summary:
    runs-on: ubuntu-latest
    steps:
      - name: Write job summary
        run: |
          echo "## Workflow Result" >> $GITHUB_STEP_SUMMARY
          echo "Commit: $GITHUB_SHA" >> $GITHUB_STEP_SUMMARY
```

### YAML Explanation

- `$GITHUB_STEP_SUMMARY` writes markdown to the workflow run summary.
- This gives readers useful information without opening every log.

### Step-by-Step Execution

1. Workflow starts manually.
2. Step writes markdown to `$GITHUB_STEP_SUMMARY`.
3. GitHub displays the summary in the workflow UI.

## Production Workflow Example

```yaml
name: Deployment Notification

on:
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        required: true
        default: "staging"

permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Deploy application
        run: echo "Deploying to ${{ inputs.environment }}"
      - name: Write deployment summary
        if: always()
        run: |
          echo "## Deployment Summary" >> $GITHUB_STEP_SUMMARY
          echo "- Environment: ${{ inputs.environment }}" >> $GITHUB_STEP_SUMMARY
          echo "- Commit: ${{ github.sha }}" >> $GITHUB_STEP_SUMMARY
          echo "- Actor: ${{ github.actor }}" >> $GITHUB_STEP_SUMMARY
          echo "- Status: ${{ job.status }}" >> $GITHUB_STEP_SUMMARY
      - name: Notify Slack on failure
        if: failure()
        run: |
          echo "Send Slack or Teams notification here"
          echo "Include workflow URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
```

### YAML Explanation

- `workflow_dispatch.inputs` lets operators choose an environment.
- `timeout-minutes` prevents runaway deployments.
- `if: always()` writes a summary for both success and failure.
- `if: failure()` avoids noisy success notifications.

### Expected Output

- Workflow summary includes deployment details.
- Failure notification includes actionable context.
- Job has timeout protection.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a workflow summary. | Summary appears in Actions UI. |
| Intermediate | Add notification step on failure only. | Notification step skips on success. |
| Challenge | Add concurrency, timeout, permissions, and debug notes. | Workflow follows production governance standards. |

---

[Previous: Module 9](./module-09-monorepo-best-practices.md) | [Module Index](./README.md) | [Next: Capstones](../capstones/README.md)
