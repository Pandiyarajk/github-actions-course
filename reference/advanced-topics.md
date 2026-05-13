# Advanced Topics and Workflow Library

Need scenarios beyond the core ten modules? Browse the [`../advanced/`](../advanced/README.md) directory for production-grade references you can copy into `.github/workflows/`.

| Scenario | Workflow | Highlights |
| --- | --- | --- |
| Feature environments & preview teardown | [`../advanced/feature-environments-preview.yml`](../advanced/feature-environments-preview.yml) | Deploys preview stacks per PR, updates GitHub Deployments, auto-cleans on close. |
| Nightly security pipelines | [`../advanced/nightly-security-pipelines.yml`](../advanced/nightly-security-pipelines.yml) | CodeQL + dependency review + Trivy scans with issue escalation. |
| GPU-based ML training | [`../advanced/ml-gpu-training.yml`](../advanced/ml-gpu-training.yml) | Self-hosted GPU runners, training artifact upload, optional registry hooks. |
| Enterprise flaky-test portal | [`../advanced/qa-flaky-portal.yml`](../advanced/qa-flaky-portal.yml) | Scheduled GitHub API scrape, JSON artifact, portal ingest + alerting. |
| Multi-cloud deploy orchestrator | [`../advanced/multi-cloud-orchestrator.yml`](../advanced/multi-cloud-orchestrator.yml) | Builds once and fans out to AWS, Azure, and GCP via reusable workflows. |

Reusable building blocks for each cloud live under [`../advanced/reusables/`](../advanced/reusables).

---

## Advanced Topics Reference

### Reusable Workflows

Use `workflow_call` when one workflow should be called by another.

Best for shared CI templates, standardized deployment flows, and organization-wide quality gates. Avoid them when the abstraction makes local workflows hard to understand.

### Composite Actions

Composite actions package multiple steps into a reusable action.

```text
.github/actions/setup-project/
   action.yml
   scripts/
```

```yaml
name: Setup Project
description: Install dependencies and prepare project

runs:
  using: composite
  steps:
    - name: Print setup message
      shell: bash
      run: echo "Set up project here"
```

### Self-Hosted Runners

Use self-hosted runners when you need private network access, special hardware, large build machines, or compliance-controlled execution.

Security rules:

- Do not run untrusted fork code on privileged self-hosted runners.
- Patch runner machines regularly.
- Use narrow labels.
- Rotate credentials.
- Prefer ephemeral runners where possible.

### OIDC Authentication

OIDC allows GitHub Actions to authenticate to cloud providers without storing long-lived cloud secrets.

```text
Workflow -> GitHub OIDC Token -> Cloud Trust Policy
      -> Short-Lived Cloud Credentials -> Deploy / Terraform / Publish
```

```yaml
permissions:
  id-token: write
  contents: read
```

Use OIDC for AWS, Azure, GCP, and other providers that support federated identity.

### Security Hardening

- Use least-privilege `permissions`.
- Pin important third-party actions.
- Avoid printing secrets.
- Use environment protection rules.
- Prefer OIDC over long-lived cloud keys.
- Add dependency scanning and CodeQL.
- Restrict deployment branches.
- Review `pull_request_target` carefully.
- Use `concurrency` for deployments.

### Performance Optimization

- Cache dependencies using lock-file keys.
- Split slow jobs into parallel jobs.
- Use path filters in monorepos.
- Avoid unnecessary matrix combinations.
- Upload only useful artifacts.
- Use Docker layer caching.
- Run expensive suites nightly instead of on every commit.

### Workflow Debugging Strategy

```text
Failure Happens
   |
   v
Read Failing Step Logs
   |
   v
Check Trigger, Branch, Permissions, Secrets
   |
   v
Reproduce with workflow_dispatch
   |
   v
Add Debug Logging or Summaries
   |
   v
Upload Evidence Artifacts
   |
   v
Fix Workflow or Product Code
```

---

[Reference Index](./README.md) | [Course Home](../README.md)
