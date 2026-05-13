# Assessments and Skill Checklist

Learners should be able to:

1. Design a complete workflow for CI, testing, deployment, approval, and rollback.
2. Explain when to use reusable workflows versus composite actions.
3. Secure a workflow using permissions, environments, and OIDC.
4. Debug a failed test or deployment pipeline from logs.
5. Optimize a slow workflow using caching, matrix tuning, and selective triggers.
6. Build a QA pipeline that produces useful evidence.
7. Explain how secrets should be rotated and scoped.
8. Create release automation with tags, artifacts, and notifications.

---

## Skill Checklist

### Beginner

- [ ] I can explain workflows, jobs, steps, and runners.
- [ ] I can create a workflow in `.github/workflows/`.
- [ ] I can trigger workflows on push, pull request, and manually.
- [ ] I can read workflow logs.
- [ ] I can use repository secrets safely.

### Intermediate

- [ ] I can use matrix builds.
- [ ] I can split pipelines into multiple jobs.
- [ ] I can upload and download artifacts.
- [ ] I can cache dependencies.
- [ ] I can build Docker images.
- [ ] I can create reusable workflows.
- [ ] I can automate releases.

### Advanced

- [ ] I can design deployment workflows with approvals.
- [ ] I can use OIDC for cloud authentication.
- [ ] I can configure self-hosted runners safely.
- [ ] I can optimize slow workflows.
- [ ] I can create QA evidence pipelines.
- [ ] I can apply security hardening.
- [ ] I can debug complex workflow failures.
- [ ] I can design enterprise workflow standards.

---

## Mid-Course Checkpoint

Create a pull request workflow that demonstrates Modules 1-5:

- Runs on `pull_request`.
- Uses at least two jobs.
- Runs one real test command or a documented sample command.
- Uses one expression or conditional.
- Uploads one artifact with `if: always()`.

Expected evidence: workflow file, successful run link, and a short explanation of the job flow.

## Instructor Review Prompts

- Is the trigger appropriate for the goal?
- Are permissions minimal?
- Are secrets avoided or scoped correctly?
- Are logs and artifacts useful during failure?
- Can the learner explain why each job exists?

---

[Course Home](../README.md) | [Module Index](../modules/README.md) | [Capstones](../capstones/README.md)
