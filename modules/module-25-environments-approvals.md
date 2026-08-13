# Module 25: Environments, Approvals, and Branch Protection

![Module](https://img.shields.io/badge/Module-25-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20C%20Platform-bf3989?style=flat-square) ![Level](https://img.shields.io/badge/Level-Advanced-cf222e?style=flat-square) ![Time](https://img.shields.io/badge/Time-150%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 24](./module-24-supply-chain-security.md) | [Next: Module 26](./module-26-local-testing-cost.md)
> Level: **Advanced** | Time: **150 min** | Example workflow: [`module-25-environments-approvals.yml`](../examples/module-25-environments-approvals.yml)
> Solutions: [`module-25-solutions.md`](../solutions/module-25-solutions.md)

## Learning Objectives

- Gate a job behind an environment with required reviewers and a wait timer.
- Scope secrets to an environment rather than the whole repository.
- Configure required status checks so a green tick actually means something.
- Explain why a skipped job can silently satisfy a required check.

## Key Concepts

environment, required reviewers, wait timer, deployment branch policy, environment secret, required status check, ruleset, merge queue

## Expected Outcome

You can build a release pipeline that pauses for human approval, holds production credentials that staging jobs cannot read, and cannot be merged around.

## Concept Flow

```text
PR opened
  |
  +--> required status checks  ------> must pass before merge (branch protection)
  |
  +--> merge queue  -----------------> re-tests with other queued PRs
                                          |
Tag pushed ------> deploy-staging ------> deploy-production
                   env: staging           env: production
                   (auto)                 (required reviewers -> PAUSES)
                                          (deployment branch policy: tags only)
```

---

## ELI5 Explanation

An environment is a labelled door your job has to walk through. You can put a guard on the door who must say yes, a timer that makes everyone wait, and a rule about which branches are even allowed to knock. The keys hanging behind that door can only be picked up by jobs that walk through it.

Branch protection is the other half: it stops someone opening a side window instead.

## Technical Explanation

### Environments

`jobs.<id>.environment` attaches a job to a named environment configured in repository settings. Three protection rules are available:

- **Required reviewers** — up to six users or teams. The job enters a *waiting* state and the run pauses until someone approves. This is the only built-in manual gate in Actions.
- **Wait timer** — a fixed delay, up to 43 200 minutes (30 days), before the job starts.
- **Deployment branch policy** — restricts which branches or tags may deploy to this environment. This is what stops a feature branch reaching production.

**Environment secrets** are the feature that carries the most weight. A secret defined on the `production` environment is unreadable by any job that does not declare `environment: production`. Repository secrets, by contrast, are available to every job in every workflow. Moving production credentials to an environment secret means a compromised staging job cannot read them.

An important subtlety: the approval gate pauses the job **before** it starts, so nothing in that job — including `actions/checkout` — has run at the point of approval. A reviewer approving a deployment is approving the *commit*, not a preview of what the job will do.

### Required status checks

Branch protection (or a ruleset) can require named checks to pass before merge. The name is the **job name** as it appears in the checks list, so renaming a job silently detaches the requirement — the rule now waits for a check that will never report, and either blocks forever or, worse, is quietly dropped.

The footgun worth internalising: **a job skipped by an `if:` or a path filter reports a conclusion of `skipped`, and a skipped required check does not block a merge.** So a path-filtered test job protecting `src/**` contributes nothing on a PR that only touches docs — which is intended — but it also contributes nothing on a PR that touches `src/**` if the filter is subtly wrong. The standard remedy is a small always-run "gate" job that depends on the conditional ones and asserts their results:

```yaml
  gate:
    if: always()
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - name: Verify required jobs succeeded
        run: |
          # `skipped` must be treated as acceptable only where intended;
          # `failure` and `cancelled` must not pass.
          for result in "${{ needs.lint.result }}" "${{ needs.test.result }}"; do
            case "$result" in
              success|skipped) ;;
              *) echo "::error::Upstream job concluded '$result'"; exit 1 ;;
            esac
          done
```

Then require only `gate`. Renaming the inner jobs no longer breaks protection.

### Rulesets and merge queue

Rulesets are the newer, layerable form of branch protection: multiple rulesets can apply to the same branch, and they can target tags as well. A **merge queue** re-tests each PR against the other queued PRs before merging, which catches the case where two individually-green PRs conflict semantically. Queued runs use the `merge_group` event, so a workflow that should gate the queue must include `on: merge_group`.

## Real-World Use Case

The release workflow published a Zephyr Scale test cycle and deployed the staging site automatically, but production deployment needed the QA lead's sign-off. Adding a `production` environment with two required reviewers and a tags-only branch policy replaced a Slack message and a manual script. Moving the production SMTP and deployment credentials to environment secrets meant the nightly staging regression could no longer read them at all.

## When To Use

- A deployment needs a human decision before proceeding.
- Different stages need different credentials, and staging must not hold production keys.
- You want an auditable record of who approved which deployment.
- Multiple PRs merge per day and semantic conflicts are a real risk (merge queue).

## When NOT To Use

- As a substitute for tests. An approval gate asks a human to vouch for something they cannot see; it does not verify anything.
- For a wait that should be a readiness check — poll for readiness rather than guessing with a wait timer.
- Merge queues on a low-traffic repository add latency for a problem that is not occurring.
- Environment protection on a job whose real risk is the code it runs, not when it runs — that is Module 24's territory.

## Common Mistakes

- Expecting an approval gate to let the reviewer inspect the job's output. The job has not started; there is nothing to see.
- Putting production credentials in repository secrets and adding `environment: production` for appearance. The gate then guards nothing, because every other job can already read the secrets.
- Renaming a job that is a required status check, detaching the protection rule.
- Assuming a `skipped` required check blocks a merge. It does not.
- Forgetting `on: merge_group` so the merge queue has no checks to run and merges without gating.
- Setting a deployment branch policy but leaving the workflow triggerable by `workflow_dispatch` from any branch — the policy restricts the environment, so the job fails rather than being prevented, which is noisier than expected.
- Using `if: needs.x.result == 'success'` on the gate job without `if: always()`, so the gate itself is skipped when an upstream job fails and therefore never reports a failure.

## Debugging Tips

- A job stuck in *waiting* with no reviewer prompt usually means the environment has required reviewers but the actor cannot self-approve, or the reviewers list is a team with no members.
- "Branch is not allowed to deploy to <environment>" is a deployment branch policy rejection, not a permissions problem.
- If an environment secret reads as empty, confirm the job actually declares `environment:` — a missing declaration yields an empty string, not an error.
- To see what a required check is actually waiting for, open the PR's checks list and compare the exact strings against the protection rule; whitespace and case matter.
- `gh api repos/<owner>/<repo>/branches/<branch>/protection` prints the effective protection, which is faster than reading the settings UI.
- A gate job that passes when it should fail is nearly always missing `if: always()`.

## Reference: environment protection rules

| Rule | Configured in | Effect |
| --- | --- | --- |
| Required reviewers | Settings → Environments | Job waits for approval by up to 6 users/teams |
| Wait timer | Settings → Environments | Fixed delay before the job starts, max 30 days |
| Deployment branch policy | Settings → Environments | Restricts which branches/tags may use the environment |
| Environment secrets | Settings → Environments | Readable only by jobs declaring that environment |
| Environment variables | Settings → Environments | Same scoping, for non-sensitive values |

## Minimal Workflow Example

```yaml
name: Gated Deployment

on: workflow_dispatch

permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    # Attaches the job to the environment. If `production` has required
    # reviewers configured, the run pauses here before any step executes.
    environment: production
    steps:
      - name: Deploy
        env:
          # Readable ONLY because this job declares environment: production.
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: echo "Deploying with a token scoped to production."
```

### YAML Explanation

- `environment: production` is what both triggers the gate and unlocks the environment's secrets.
- The pause happens before the first step, so no checkout has occurred at approval time.
- `secrets.DEPLOY_TOKEN` resolves to the environment secret; without the `environment:` line it would be an empty string.
- `permissions: contents: read` keeps the token minimal — the gate is about credentials, not token scope.

### Step-by-Step Execution

1. Someone dispatches the workflow.
2. The `deploy` job is created and immediately enters *waiting*.
3. GitHub notifies the environment's required reviewers.
4. A reviewer approves; the approval is recorded against the run.
5. The runner starts and the environment's secrets become available to the job.
6. The deployment history for `production` gains an entry naming the approver.

## Production Workflow Example

```yaml
name: Staged Release

on:
  push:
    tags:
      - "v*.*.*"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  regression:
    name: Regression gate
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python suite
        uses: ./.github/actions/setup-python-suite
        with:
          python-version: "3.13"
          working-directory: your-solution-root-folder-name

      - name: Run regression suite
        working-directory: your-solution-root-folder-name
        run: behave --tags=regression

  deploy-staging:
    name: Deploy to staging
    needs: regression
    runs-on: ubuntu-latest
    # No protection rules on staging: it deploys automatically.
    environment:
      name: staging
      url: https://staging.your-domain.com
    steps:
      - name: Deploy
        env:
          # A staging-scoped credential. This job cannot read the production one.
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: echo "Deploying to staging."

  deploy-production:
    name: Deploy to production
    needs: deploy-staging
    runs-on: ubuntu-latest
    # `production` carries required reviewers AND a tags-only deployment branch
    # policy, so this pauses for approval and refuses to run from a branch.
    environment:
      name: production
      url: https://your-domain.com
    steps:
      - name: Deploy
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: echo "Deploying to production after approval."

      - name: Record the approver
        run: |
          {
            echo "## Production deployment"
            echo
            echo "| Field | Value |"
            echo "| --- | --- |"
            echo "| Tag | ${{ github.ref_name }} |"
            echo "| Triggered by | ${{ github.actor }} |"
          } >> "$GITHUB_STEP_SUMMARY"

  # Single required status check. Depends on everything, tolerates intentional
  # skips, and fails on any real failure -- so renaming an inner job cannot
  # silently detach branch protection.
  gate:
    name: Release gate
    if: always()
    needs: [regression, deploy-staging, deploy-production]
    runs-on: ubuntu-latest
    steps:
      - name: Verify upstream results
        run: |
          for result in \
            "${{ needs.regression.result }}" \
            "${{ needs.deploy-staging.result }}" \
            "${{ needs.deploy-production.result }}"
          do
            case "$result" in
              success|skipped) ;;
              *) echo "::error::Upstream job concluded '$result'"; exit 1 ;;
            esac
          done
          echo "All upstream jobs are acceptable."
```

### YAML Explanation

- `environment.url` makes the deployed URL a clickable link on the run and in the environment's history.
- `staging` and `production` both reference `secrets.DEPLOY_TOKEN`, but they resolve to different values — that is the point of environment secrets.
- `deploy-production` inherits the tags-only branch policy, so a `workflow_dispatch` from a branch fails at the environment check.
- `gate` uses `if: always()` so it still runs — and still fails — when an upstream job fails. Without it the gate would be skipped and report nothing.
- Only `gate` needs to be listed as a required status check.

### Expected Output

- A tag push runs the regression suite, deploys staging, then pauses.
- The run shows `deploy-production` as *waiting*, with reviewers notified.
- After approval, the environment's deployment history records the tag and approver.
- The `gate` job reports one check; forcing a regression failure makes `gate` fail too.

## Quiz

1. A reviewer wants to inspect the test output before approving a `production` deployment. Why can they not?
   - **A.** Approval happens after the job's steps run, but logs are hidden until approval.
   - **B.** The gate pauses the job before any step executes, so there is no output yet.
   - **C.** Log visibility requires `actions: read` on the environment.
   - **D.** Only organisation owners can view logs of a gated job.

2. A repository requires the status check `test` to pass. `test` has `paths: ['src/**']`. A PR changes only `README.md`. What happens?
   - **A.** The merge is blocked because `test` never reports.
   - **B.** `test` reports `skipped`, which does not block the merge.
   - **C.** `test` runs anyway because it is a required check.
   - **D.** The PR is blocked until someone overrides protection.

3. Production credentials are stored as **repository** secrets, and the production job declares `environment: production` with required reviewers. What does the gate protect?
   - **A.** The credentials, since the environment scopes them.
   - **B.** Nothing about the credentials — every job can already read repository secrets; only the timing is gated.
   - **C.** Both the credentials and the timing.
   - **D.** Only the deployment URL.

4. A `gate` job is written as `if: needs.test.result == 'success'` and required by branch protection. Explain the failure mode and give the correct condition.

5. A team enables a merge queue but PRs merge without their test workflow running. Give the most likely cause and the one-line fix.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create a `staging` environment and a job that declares it, then add a 1-minute wait timer and observe the pause. | The run shows the job waiting, then proceeding after the timer. |
| Intermediate | Create a `production` environment with yourself as a required reviewer and an environment secret. Prove a job without `environment: production` reads the secret as empty. | Two jobs: one prints a value, one prints an empty string. |
| Challenge | Add an always-run `gate` job that depends on two path-filtered jobs, make it the only required check, then verify a docs-only PR passes while a broken code PR fails. | Both PR outcomes recorded, plus an explanation of why requiring the inner jobs directly would not work. |

Solutions: [`solutions/module-25-solutions.md`](../solutions/module-25-solutions.md)

---

[Previous: Module 24](./module-24-supply-chain-security.md) | [Module Index](./README.md) | [Next: Module 26](./module-26-local-testing-cost.md)
