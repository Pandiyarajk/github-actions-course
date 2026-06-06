# 🏆 Capstone Projects

![Section](https://img.shields.io/badge/Section-Capstone-cf222e?style=flat-square) ![Projects](https://img.shields.io/badge/Projects-3-1f6feb?style=flat-square) ![Prereq](https://img.shields.io/badge/Prereq-Modules%201--20-d29922?style=flat-square) [![Course Home](https://img.shields.io/badge/⬅%20Course%20Home-555?style=flat-square)](../README.md)

Each capstone applies the modules end-to-end. Start small: build the **minimum viable** version first (it is enough to submit), then add the full-scope extras if you have time. Every capstone lists the modules it builds on so you can review them first.

### Capstone 1: Multi-Service Python Pipeline

Build a monorepo pipeline for several Python services with path-based test selection, Docker build, staging, production approval, release tagging, and notifications.

**Before you start:** review Modules 7 (jobs/steps), 14 (matrix & reuse), 16 (Docker & caching), 17 (release automation), 19 (monorepo path filtering), 20 (notifications).

**Minimum viable:** path detection + one Python test job + a Docker build on `main`.
**Full scope:** all three services tested in parallel, staging→approval→production, release tag, and email notification.

```text
Pull Request
   |
   v
Path Detection (api / worker / lib)
   |
   +--> api tests (behave/pytest)
   +--> worker tests
   +--> lib tests
   |
   v
Docker Build -> Security Scan -> Staging Deploy -> Approval -> Production Deploy
   |
   v
Release + Email Notification
```

Implementation plan:

1. Create `api/`, `worker/`, and `lib/` folders (all Python).
2. Add separate test jobs for each service, selected by `dorny/paths-filter`.
3. Add a matrix where useful (e.g. Python version or browser).
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
worker/
lib/
docs/
  runbook.md
```

Evaluation checklist:

| Area | Criteria |
| --- | --- |
| CI correctness | Tests run for each changed Python service. |
| Security | Secrets are scoped; permissions are minimal. |
| Deployment | Staging and production are separated. |
| Release | Tags or releases are created consistently. |
| Observability | Logs, summaries, and artifacts are useful. |
| Documentation | Runbook explains how to rerun and rollback. |

### Capstone 2: Unified QA Automation Hub

Build a QA pipeline that runs API, UI, and smoke tests and publishes evidence for audit and debugging.

**Before you start:** review Modules 10 (artifacts), 15 (testing pipelines), 18 (QA automation), 20 (notifications).

**Minimum viable:** one scheduled Behave smoke job that uploads an Allure report artifact.
**Full scope:** parallel API/UI/smoke jobs, screenshots on failure, step summary, and a failure-only email.

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
| Test coverage | API, UI, and smoke jobs exist. |
| Evidence | Reports and screenshots upload on failure. |
| Scheduling | Nightly and manual triggers work. |
| Debugging | Logs clearly identify failed suite. |
| QA usability | Summary is readable by QA and developers. |

### Capstone 3: Secure Deployment Playbook

Create a secure cloud deployment workflow using OIDC, Terraform plan/apply, approvals, release notes, and rollback.

**Before you start:** review Modules 13 (secure pipelines) and 17 (release automation), plus the [advanced OIDC reusables](../advanced/README.md).

**Minimum viable:** an OIDC-authenticated job that runs `terraform plan` and uploads the plan artifact.
**Full scope:** plan→approval→apply, release notes, retained evidence, and a runnable rollback workflow.

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
