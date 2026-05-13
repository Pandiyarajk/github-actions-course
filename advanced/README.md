# Advanced Workflow Library

This folder extends the course with production-grade scenarios that go beyond the core ten modules. Copy any workflow into `.github/workflows/` inside the repo that will actually execute them.

## Inventory

| Capability | File | Highlights | Secrets / setup |
| --- | --- | --- | --- |
| Feature environments with automatic preview + teardown | `feature-environments-preview.yml` | PR-triggered preview deploys, GitHub Deployments metadata, auto cleanup on close | None required beyond default `GITHUB_TOKEN` |
| Nightly security pipelines (SAST, dependency review, container scan) | `nightly-security-pipelines.yml` | CodeQL polyglot scan, dependency review drift check, Trivy container scan, digest + issue escalation | Optional GHCR push (uses `GITHUB_TOKEN`) |
| Self-hosted GPU ML training with artifact tracking | `ml-gpu-training.yml` | Pre-flight config, GPU runner training, artifact uploads, registry hook | Optional `MODEL_REGISTRY_TOKEN` |
| Enterprise QA portal ingestion for flaky stats | `qa-flaky-portal.yml` | Scheduled GitHub API scrape, JSON artifact, portal POST, auto issue for high flake rate | `QA_PORTAL_TOKEN` for API push |
| Multi-cloud deployment orchestrator + reusable workflows | `multi-cloud-orchestrator.yml` + `reusables/*.yml` | Builds once, fans out to AWS/Azure/GCP via OIDC, toggleable clouds, shared release metadata | AWS/Azure/GCP federated credentials (see below) |

## Multi-cloud reusable workflows

Three reusable workflows live under `advanced/reusables/`:

- `aws-deploy.yml` — expects `secrets.aws_role_arn` and `secrets.aws_account_id`.
- `azure-deploy.yml` — expects `secrets.azure_client_id`, `azure_tenant_id`, `azure_subscription_id`.
- `gcp-deploy.yml` — expects `secrets.gcp_workload_identity_provider`, `gcp_service_account`.

The orchestrator (`multi-cloud-orchestrator.yml`) calls these with `uses: ./advanced/reusables/<provider>.yml` for demonstration. When running in a live repository, place the reusable files under `.github/workflows/` or publish them in a separate repo so that `uses:` can resolve correctly.

## Usage Notes

- Every workflow includes `workflow_dispatch` so instructors can demo the flow without waiting for schedules or tags.
- Secrets are optional unless specifically noted; each file contains inline comments showing where to plug in cloud CLIs or organization tooling.
- The YAML files are intentionally verbose (extra summaries, comments, artifact uploads) to make troubleshooting easier for learners exploring advanced scenarios.
