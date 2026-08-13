# ✅ Assessments and Skill Checklist

![Section](https://img.shields.io/badge/Section-Assessment-2da44e?style=flat-square) ![Type](https://img.shields.io/badge/Type-Checklist%20%2B%20Checkpoint-1f6feb?style=flat-square) [![Course Home](https://img.shields.io/badge/⬅%20Course%20Home-555?style=flat-square)](../README.md)

Learners should be able to:

1. Design a complete workflow for CI, testing, deployment, approval, and rollback.
2. Explain when to use reusable workflows versus composite actions.
3. Secure a workflow using permissions, environments, and OIDC.
4. Debug a failed test or deployment pipeline from logs.
5. Optimize a slow workflow using caching, matrix tuning, and selective triggers.
6. Build a QA pipeline that produces useful evidence.
7. Explain how secrets should be rotated and scoped.
8. Create release automation with tags, artifacts, and notifications.
9. Author a composite action, and justify it over a reusable workflow (or the reverse).
10. Provide a job's dependencies with `container:` and `services:`, and address a service correctly.
11. Publish an image to a registry with layer caching, and consume it reproducibly by digest.
12. Audit a workflow for over-broad `permissions:`, expression injection, and unpinned third-party actions.
13. Explain what a green required status check does and does not prove.
14. Estimate and reduce a workflow's billed minutes without reducing coverage.

---

## Skill Checklist

The checklist mirrors the three parts of the course, then a mastery tier.

### Part A — Workflow Components (Modules 1-11)

- [ ] I can explain workflows, jobs, steps, and runners.
- [ ] I can create a workflow in `.github/workflows/`.
- [ ] I can name runs dynamically with `run-name`.
- [ ] I can trigger workflows on push, pull request, schedule, and manually.
- [ ] I can choose and target a runner (GitHub-hosted or self-hosted).
- [ ] I can split work into jobs with `runs-on`, `timeout-minutes`, and steps.
- [ ] I can set env variables and use repository secrets safely.
- [ ] I can run Python, shell, and other commands in a step.
- [ ] I can upload artifacts (including `if: always()`).
- [ ] I can apply core controls: concurrency, permissions, defaults.

### Part B — Applied CI/CD (Modules 12-20)

- [ ] I can use expressions, conditionals, and job outputs.
- [ ] I can build a secure pipeline with scoped permissions.
- [ ] I can use matrix builds and reusable workflows.
- [ ] I can build a multi-layer test pipeline and produce QA evidence.
- [ ] I can build Docker images and cache dependencies.
- [ ] I can automate releases with tags and artifacts.
- [ ] I can use path filtering in a monorepo.
- [ ] I can send notifications and write run summaries.

### Part C — Platform, Security, and Operations (Modules 21-26)

- [ ] I can write a composite action with typed `inputs` and `outputs`.
- [ ] I can explain why a local action needs the checkout to run first.
- [ ] I can choose between a composite action and a reusable workflow, and say why.
- [ ] I can run a job in a container with a service dependency and a real health check.
- [ ] I can address a service correctly from both a container job and a runner-hosted job.
- [ ] I can publish an image to GHCR with `type=gha` layer caching.
- [ ] I can consume an image by digest so a run is reproducible.
- [ ] I can explain what `GITHUB_TOKEN` is scoped to and when it expires.
- [ ] I can scope `permissions:` correctly, knowing that naming one scope resets the rest.
- [ ] I can recognise and defuse the `pull_request_target` fork-escalation pattern.
- [ ] I can rewrite an expression-injection risk to pass through `env:`.
- [ ] I can pin a third-party action to a commit SHA and resolve that SHA.
- [ ] I can gate a deployment behind an environment with required reviewers.
- [ ] I can explain why a `skipped` required check does not block a merge, and build a gate job that fixes it.
- [ ] I can lint a workflow with `actionlint` before pushing, and say what it cannot tell me.
- [ ] I can name the runner cost multipliers and the levers that reduce billed minutes.

### Mastery (Capstone + advanced)

- [ ] I can design deployment workflows with approvals.
- [ ] I can use OIDC for cloud authentication.
- [ ] I can configure self-hosted runners safely.
- [ ] I can apply security hardening.
- [ ] I can debug complex workflow failures.
- [ ] I can design enterprise workflow standards.

---

## Mid-Course Checkpoint

Create a pull request workflow that demonstrates Part A (Modules 1-11) — in particular triggers (Module 3), jobs and steps (Module 7), running a test command (Module 9), artifacts (Module 10), and a basic expression (Module 12):

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
