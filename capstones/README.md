# Capstone Projects

### Capstone 1: Cross-Language Service Pipeline

Build a monorepo pipeline for a Python API, React frontend, C# worker, Docker deployment, staging, production, release tagging, and notifications.

```text
Pull Request
   |
   v
Path Detection
   |
   +--> Python Tests
   +--> React Tests
   +--> C# Tests
   |
   v
Docker Build -> Security Scan -> Staging Deploy -> Approval -> Production Deploy
   |
   v
Release + Email Notification
```

Implementation plan:

1. Create `api/`, `frontend/`, and `worker/` folders.
2. Add separate test jobs for each component.
3. Add matrix builds where useful.
4. Build a Docker image after tests pass.
5. Push image to GHCR only from `main`.
6. Add staging deployment using GitHub Environments.
7. Add production approval.
8. Add release tag after production deployment.
9. Upload test reports and deployment evidence.
10. Add SMTP email failure notification.

Sample solution structure:

```text
.github/
  workflows/
    ci.yml
    docker-publish.yml
    deploy.yml
api/
frontend/
worker/
docs/
  runbook.md
```

Evaluation checklist:

| Area | Criteria |
| --- | --- |
| CI correctness | Tests run for all components. |
| Security | Secrets are scoped; permissions are minimal. |
| Deployment | Staging and production are separated. |
| Release | Tags or releases are created consistently. |
| Observability | Logs, summaries, and artifacts are useful. |
| Documentation | Runbook explains how to rerun and rollback. |

### Capstone 2: Unified QA Automation Hub

Build a QA pipeline that runs API, UI, and smoke tests and publishes evidence for audit and debugging.

```text
Schedule / Manual Trigger
   |
   v
Start Test Environment
   |
   +--> API Tests with Python requests / Behave @api
   +--> UI Tests with Selenium + Behave
   +--> Smoke Tests with Behave @smoke
   |
   v
Collect Allure Reports -> Upload Evidence -> Publish Summary -> Notify QA by Email
```

Implementation plan:

1. Create separate jobs for API, UI, and smoke testing with Behave.
2. Add scheduled nightly trigger.
3. Add manual trigger for reruns.
4. Store test reports under `reports/`.
5. Capture screenshots or logs for UI failures.
6. Upload all evidence using artifacts.
7. Add summary markdown using `$GITHUB_STEP_SUMMARY`.
8. Add failure-only team notification.
9. Add flaky test quarantine notes.
10. Document triage steps.

Sample solution structure:

```text
.github/
  workflows/
    qa-nightly.yml
features/
  api/
  ui/
  smoke/
steps/
reports/
  allure-results/
docs/
  qa-triage.md
```

Evaluation checklist:

| Area | Criteria |
| --- | --- |
| Test coverage | API, UI, and contract jobs exist. |
| Evidence | Reports and screenshots upload on failure. |
| Scheduling | Nightly and manual triggers work. |
| Debugging | Logs clearly identify failed suite. |
| QA usability | Summary is readable by QA and developers. |

### Capstone 3: Secure Deployment Playbook

Create a secure cloud deployment workflow using OIDC, Terraform plan/apply, approvals, release notes, and rollback.

```text
Push to Main -> Build Artifact -> Terraform Plan -> Security Scan
      -> Staging Apply -> Approval Gate -> Production Apply
      -> Release Notes -> Rollback Workflow Available
```

Implementation plan:

1. Add OIDC permissions.
2. Configure cloud trust policy.
3. Run Terraform format and validate.
4. Generate Terraform plan artifact.
5. Require approval before production apply.
6. Deploy using short-lived credentials.
7. Create release notes from commits.
8. Store deployment evidence.
9. Add rollback workflow using previous artifact or image tag.
10. Document emergency rollback process.

Sample solution structure:

```text
.github/
  workflows/
    terraform-plan.yml
    terraform-apply.yml
    rollback.yml
infra/
docs/
  deployment-playbook.md
```

Evaluation checklist:

| Area | Criteria |
| --- | --- |
| Authentication | Uses OIDC, not long-lived cloud keys. |
| Safety | Production requires approval. |
| Auditability | Plans and deployment logs are retained. |
| Rollback | Rollback process is documented and runnable. |
| Security | Permissions are minimal. |

---

## How To Submit a Capstone

1. Include workflow files under `.github/workflows/`.
2. Include a short runbook explaining triggers, required secrets, rerun steps, and rollback.
3. Attach workflow run links, screenshots, artifacts, or logs as evidence.
4. Explain one design trade-off you made.

## Review Rubric

| Category | Weight | What reviewers look for |
| --- | --- | --- |
| Correctness | 40% | Workflows run, jobs are ordered correctly, artifacts are usable. |
| Security | 20% | Least privilege, scoped secrets, OIDC where appropriate, safe runner usage. |
| Performance | 15% | Caching, parallelization, path filtering, and reasonable trigger design. |
| Observability | 15% | Logs, summaries, artifacts, notifications, and failure evidence are useful. |
| Documentation | 10% | Runbook is clear enough for another engineer to operate the pipeline. |

---

[Course Home](../README.md) | [Module Index](../modules/README.md) | [Assessments](../assessments/README.md)
