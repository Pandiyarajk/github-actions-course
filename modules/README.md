# 📘 Module Study Guide

![Modules](https://img.shields.io/badge/Modules-26-2da44e?style=flat-square) ![Part A](https://img.shields.io/badge/Part%20A-Components%201--11-1f6feb?style=flat-square) ![Part B](https://img.shields.io/badge/Part%20B-Applied%2012--20-8957e5?style=flat-square) ![Part C](https://img.shields.io/badge/Part%20C-Platform%2021--26-bf3989?style=flat-square) [![Course Home](https://img.shields.io/badge/⬅%20Course%20Home-555?style=flat-square)](../README.md)

Use this directory as the main study path. Each module is self-contained and includes objectives, ELI5 and technical explanations, real-world use cases, when to use and avoid the pattern, common mistakes, debugging tips, minimal YAML, production YAML, execution flow, labs, and expected outputs.

All examples are oriented around **Python test automation** as used in real-world projects:

- **Web automation suite** — Selenium + Behave (Python BDD) web automation with Allure reporting, multi-browser (chrome/firefox/msedge), daily scheduled smoke tests, and SMTP email notifications.
- **Desktop/UI regression suite** — Windows-based regression automation on self-hosted runners (`server1`–`server4`), Python report generation, Zephyr Scale + Jira integration, and SMTP email reports.

Conventions used throughout: Python 3.13, Behave, Selenium, Allure, `pylint`, self-hosted runner labels `server1`–`server4`, and the generic placeholders `your-solution-root-folder-name/` and `your-domain.com`.

## Recommended Path

The modules are ordered to follow a workflow file top-to-bottom first, then applied CI/CD topics:

```text
Part A — Workflow components (Modules 1-11):
  name -> run-name -> on (triggers) -> schedule -> runners -> runner setup
  -> jobs / runs-on / timeout / steps -> env & secrets -> scripts -> artifacts -> core controls

Part B — Applied CI/CD (Modules 12-20):
  syntax & expressions -> secure pipelines -> matrix & reuse -> testing
  -> caching & performance -> releases -> QA automation -> monorepo -> notifications

Part C — Platform, Security & Operations (Modules 21-26):
  composite actions -> container & service jobs -> publishing images
  -> supply-chain security -> environments & approvals -> local testing & cost

Capstones: Apply everything in realistic delivery scenarios
```

## Level Breakdown

### Part A — Workflow Components (Modules 1-11)

| Requirement | Study Focus |
| --- | --- |
| Learning objectives | Read and author every part of a workflow file: `name`/`run-name`, `on` triggers, scheduling, runners, jobs/`runs-on`/`timeout-minutes`, `env`/secrets, running scripts, artifacts, and core controls (concurrency, permissions). |
| Key concepts | Workflow, event, trigger, runner, job, step, env, secret, artifact, concurrency, expression. |
| Hands-on exercises | Name runs dynamically, filter triggers, schedule with cron, target runners, scope env/secrets, run Python/shell/cmd, upload artifacts. |
| Expected outcomes | Learners can build and debug workflows component-by-component without copying blindly. |

### Part B — Applied CI/CD (Modules 12-20)

| Requirement | Study Focus |
| --- | --- |
| Learning objectives | Apply the components to real pipelines: expressions/outputs, secure pipelines, browser/server matrices, multi-layer Python test pipelines, Selenium Grid via Docker, releases, nightly QA, monorepos, and notifications. |
| Key concepts | Matrix strategy, reusable workflow, Allure report, Selenium Grid, pip cache key, environment, Zephyr cycle, path filtering, SMTP alerts. |
| Hands-on exercises | Run browser matrices, upload Allure reports, cache pip dependencies, run Behave against a Selenium Grid, create Zephyr release cycles, build nightly QA, add SMTP notifications. |
| Expected outcomes | Learners can design production-grade test-automation workflows with security, observability, and maintainability. |

### Part C — Platform, Security, and Operations (Modules 21-26)

| Requirement | Study Focus |
| --- | --- |
| Learning objectives | Work on the platform around the workflow: package logic as composite actions, run jobs in containers with service dependencies, publish and consume images, defend against fork-PR privilege escalation and expression injection, gate deployments behind environments, and control billed minutes. |
| Key concepts | `action.yml`, `runs.using: composite`, `container:`, `services:`, health check, GHCR, layer cache, `GITHUB_TOKEN`, `permissions:`, `pull_request_target`, script injection, SHA pinning, environment, required reviewers, required status check, `actionlint`, `act`, minute multiplier. |
| Hands-on exercises | Extract a repeated preamble into a composite action, run Behave against a `services:`-provided Selenium Grid, publish a test-runner image to GHCR and consume it by digest, audit a workflow for injection and over-broad permissions, build an approval-gated release, and reduce a workflow's billed minutes. |
| Expected outcomes | Learners can reason about a workflow as production infrastructure — its blast radius, its supply chain, its gates, and its cost. |

## Module Index

| # | Level | Module | Time | Runnable Example | Solutions |
| --- | --- | --- | --- | --- | --- |
| 1 | Beginner | [CI/CD and GitHub Actions Foundations](module-01-ci-foundations.md) | 90 min | [`module-01-ci-foundations.yml`](../examples/module-01-ci-foundations.yml) | [`module-01-solutions.md`](../solutions/module-01-solutions.md) |
| 2 | Beginner | [Naming Workflows with `name` and Dynamic `run-name`](module-02-workflow-naming.md) | 90 min | [`module-02-workflow-naming.yml`](../examples/module-02-workflow-naming.yml) | [`module-02-solutions.md`](../solutions/module-02-solutions.md) |
| 3 | Beginner | [The `on` Section — Workflow Triggers and Event Filters](module-03-workflow-triggers.md) | 120 min | [`module-03-workflow-triggers.yml`](../examples/module-03-workflow-triggers.yml) | [`module-03-solutions.md`](../solutions/module-03-solutions.md) |
| 4 | Beginner | [Scheduling Workflow Runs with Cron](module-04-scheduled-workflows.md) | 90 min | [`module-04-scheduled-workflows.yml`](../examples/module-04-scheduled-workflows.yml) | [`module-04-solutions.md`](../solutions/module-04-solutions.md) |
| 5 | Intermediate | [Runners — What They Are and How Concurrent Runs Behave](module-05-runners.md) | 120 min | [`module-05-runners.yml`](../examples/module-05-runners.yml) | [`module-05-solutions.md`](../solutions/module-05-solutions.md) |
| 6 | Intermediate | [Runner Setup — Creating, Targeting, and Health-Checking Runners](module-06-runner-setup.md) | 150 min | [`module-06-runner-setup.yml`](../examples/module-06-runner-setup.yml) | [`module-06-solutions.md`](../solutions/module-06-solutions.md) |
| 7 | Beginner | [Jobs, Job Naming, `timeout-minutes`, `runs-on`, `env`, and `steps`](module-07-jobs-and-steps.md) | 120 min | [`module-07-jobs-and-steps.yml`](../examples/module-07-jobs-and-steps.yml) | [`module-07-solutions.md`](../solutions/module-07-solutions.md) |
| 8 | Beginner | [Environment Variables and Secrets — Setting and Using Them](module-08-env-and-secrets.md) | 120 min | [`module-08-env-and-secrets.yml`](../examples/module-08-env-and-secrets.yml) | [`module-08-solutions.md`](../solutions/module-08-solutions.md) |
| 9 | Beginner | [Running Python, Shell, Bash, and CMD in Workflows](module-09-running-scripts.md) | 90 min | [`module-09-running-scripts.yml`](../examples/module-09-running-scripts.yml) | [`module-09-solutions.md`](../solutions/module-09-solutions.md) |
| 10 | Beginner | [Artifacts — Uploading Files, Folders, Retention, and Conditions](module-10-artifacts.md) | 120 min | [`module-10-artifacts.yml`](../examples/module-10-artifacts.yml) | [`module-10-solutions.md`](../solutions/module-10-solutions.md) |
| 11 | Intermediate | [Essential Workflow Controls — Concurrency, Permissions, Defaults, and More](module-11-misc-features.md) | 120 min | [`module-11-misc-features.yml`](../examples/module-11-misc-features.yml) | [`module-11-solutions.md`](../solutions/module-11-solutions.md) |
| 12 | Beginner | [Workflow Syntax, Jobs, Steps, and Expressions](module-12-workflow-syntax.md) | 120 min | [`module-12-workflow-syntax.yml`](../examples/module-12-workflow-syntax.yml) | [`module-12-solutions.md`](../solutions/module-12-solutions.md) |
| 13 | Beginner | [Secrets, Variables, and Secure Pipelines](module-13-secrets-security.md) | 120 min | [`module-13-secrets-security.yml`](../examples/module-13-secrets-security.yml) | [`module-13-solutions.md`](../solutions/module-13-solutions.md) |
| 14 | Intermediate | [Matrix Builds, Marketplace Actions, and Reusable Workflows](module-14-matrix-and-reuse.md) | 120 min | [`module-14-matrix-and-reuse.yml`](../examples/module-14-matrix-and-reuse.yml) | [`module-14-solutions.md`](../solutions/module-14-solutions.md) |
| 15 | Intermediate | [Automated Testing Pipelines](module-15-multi-language-tests.md) | 120 min | [`module-15-multi-language-tests.yml`](../examples/module-15-multi-language-tests.yml) | [`module-15-solutions.md`](../solutions/module-15-solutions.md) |
| 16 | Intermediate | [Docker, Artifacts, Caching, and Performance](module-16-docker-performance.md) | 150 min | [`module-16-docker-performance.yml`](../examples/module-16-docker-performance.yml) | [`module-16-solutions.md`](../solutions/module-16-solutions.md) |
| 17 | Intermediate | [Deployment, Versioning, Tagging, and Release Automation](module-17-release-automation.md) | 150 min | [`module-17-release-automation.yml`](../examples/module-17-release-automation.yml) | [`module-17-solutions.md`](../solutions/module-17-solutions.md) |
| 18 | Advanced | [QA Automation Workflows](module-18-qa-automation.md) | 150 min | [`module-18-qa-automation.yml`](../examples/module-18-qa-automation.yml) | [`module-18-solutions.md`](../solutions/module-18-solutions.md) |
| 19 | Advanced | [Monorepos, Enterprise Patterns, and Self-Hosted Runners](module-19-monorepo-best-practices.md) | 150 min | [`module-19-monorepo-best-practices.yml`](../examples/module-19-monorepo-best-practices.yml) | [`module-19-solutions.md`](../solutions/module-19-solutions.md) |
| 20 | Advanced | [Notifications, Observability, Debugging, and Governance](module-20-notifications.md) | 120 min | [`module-20-notifications.yml`](../examples/module-20-notifications.yml) | [`module-20-solutions.md`](../solutions/module-20-solutions.md) |
| 21 | Intermediate | [Composite Actions and Custom Actions](module-21-composite-actions.md) | 120 min | [`module-21-composite-actions.yml`](../examples/module-21-composite-actions.yml) | [`module-21-solutions.md`](../solutions/module-21-solutions.md) |
| 22 | Intermediate | [Container Jobs and Service Containers](module-22-container-jobs.md) | 120 min | [`module-22-container-jobs.yml`](../examples/module-22-container-jobs.yml) | [`module-22-solutions.md`](../solutions/module-22-solutions.md) |
| 23 | Intermediate | [Building and Publishing Docker Images](module-23-docker-publish.md) | 150 min | [`module-23-docker-publish.yml`](../examples/module-23-docker-publish.yml) | [`module-23-solutions.md`](../solutions/module-23-solutions.md) |
| 24 | Advanced | [Supply Chain Security and `GITHUB_TOKEN`](module-24-supply-chain-security.md) | 150 min | [`module-24-supply-chain-security.yml`](../examples/module-24-supply-chain-security.yml) | [`module-24-solutions.md`](../solutions/module-24-solutions.md) |
| 25 | Advanced | [Environments, Approvals, and Branch Protection](module-25-environments-approvals.md) | 150 min | [`module-25-environments-approvals.yml`](../examples/module-25-environments-approvals.yml) | [`module-25-solutions.md`](../solutions/module-25-solutions.md) |
| 26 | Intermediate | [Local Testing, Linting, and Cost Control](module-26-local-testing-cost.md) | 120 min | [`module-26-local-testing-cost.yml`](../examples/module-26-local-testing-cost.yml) | [`module-26-solutions.md`](../solutions/module-26-solutions.md) |

## How To Study Each Module

1. Read the ELI5 explanation first.
2. Study the technical explanation and ASCII flow.
3. Run or adapt the minimal YAML.
4. Compare it with the production example.
5. Complete the beginner, intermediate, and challenge labs.
6. Use the debugging tips to intentionally break and fix one workflow.

## Completion Criteria

- You can explain the module topic without reading the notes.
- You can author the minimal workflow from memory.
- You can identify when the production pattern is appropriate.
- You can debug one common failure for that module.

---

[Course Home](../README.md) | [Capstones](../capstones/README.md) | [Assessments](../assessments/README.md) | [Reference](../reference/README.md)
