# GitHub Actions Enablement Course

![Level](https://img.shields.io/badge/Level-Beginner%20to%20Advanced-blue)
![Audience](https://img.shields.io/badge/Audience-Developers%20%7C%20QA%20%7C%20SDETs-green)
![Format](https://img.shields.io/badge/Format-Self--Paced%20%2B%20Workshop-orange)
![Focus](https://img.shields.io/badge/Focus-CI%2FCD%20%7C%20Testing%20%7C%20Security%20%7C%20Deployment-purple)

A practical, industry-ready GitHub Actions course for developers, QA engineers, SDETs, and DevOps beginners. The course is now organized as study material instead of one long README: start here, follow the module path, complete the labs, then finish with capstones.

---

## Start Here

1. Read this page to understand the path.
2. Open the [Module Study Guide](modules/README.md).
3. Complete Modules 1-3 if you are new to GitHub Actions.
4. Complete Modules 4-7 if you need production CI/CD skills.
5. Complete Modules 8-10 and the [Capstones](capstones/README.md) if you support QA, deployment, security, or enterprise workflows.

```text
Code Change -> GitHub Event -> Workflow -> Runner -> Job -> Step
      -> Test / Build / Scan -> Artifact / Image -> Deploy / Notify
```

---

## Course Structure

| Area | Link | Purpose |
| --- | --- | --- |
| Study modules | [modules/](modules/README.md) | Main beginner-to-advanced learning path. |
| Runnable examples | [examples/](examples/) | YAML workflows paired with each module. |
| Capstones | [capstones/](capstones/README.md) | Realistic final projects and evaluation rubrics. |
| Assessments | [assessments/](assessments/README.md) | Final assessment, skill checklist, and review prompts. |
| Reference | [reference/](reference/README.md) | Cheat sheets, advanced topics, debugging, and production checklists. |
| Advanced workflow library | [advanced/](advanced/README.md) | Production-grade scenarios and reusable cloud deployment examples. |
| Production case studies | [case-studies/](case-studies/README.md) | Public-safe real-world workflow patterns rebuilt as learning modules. |

---

## Audience and Prerequisites

| Area | Details |
| --- | --- |
| Audience | Developers, QA automation engineers, SDETs, junior DevOps engineers, and technical leads. |
| Prerequisites | Git basics, command-line comfort, basic YAML, and one scripting or programming language. |
| Delivery | Self-paced study, live workshop, bootcamp, or internal engineering enablement. |
| Learning loop | Concept -> visual model -> workflow demo -> hands-on lab -> debugging clinic -> quiz. |
| Toolkit | GitHub Actions, GitHub CLI, Docker, Python 3.13, Behave (BDD), Selenium, Allure, pylint, Zephyr Scale, Jira, SMTP email. |

---

## Learning Path

| Level | Modules | Focus | Estimated Time |
| --- | --- | --- | --- |
| Beginner | 1-3 | Foundations, YAML, triggers, secrets | 5-6 hours |
| Intermediate | 4-7 | Matrix builds, testing, Docker, caching, releases | 8-10 hours |
| Advanced | 8-10 + capstones | QA automation, enterprise patterns, security, deployment | 8-12 hours |

```text
Beginner
   |
   v
Intermediate
   |
   v
Advanced
   |
   v
Capstone Project
```

---

## Module Roadmap

| # | Level | Module | Time |
| --- | --- | --- | --- |
| 1 | Beginner | [CI/CD and GitHub Actions Foundations](modules/module-01-ci-foundations.md) | 90 min |
| 2 | Beginner | [Workflow Syntax, Jobs, Steps, and Expressions](modules/module-02-workflow-syntax.md) | 120 min |
| 3 | Beginner | [Secrets, Variables, and Secure Pipelines](modules/module-03-secrets-security.md) | 120 min |
| 4 | Intermediate | [Matrix Builds, Marketplace Actions, and Reusable Workflows](modules/module-04-matrix-and-reuse.md) | 120 min |
| 5 | Intermediate | [Automated Testing Pipelines](modules/module-05-multi-language-tests.md) | 120 min |
| 6 | Intermediate | [Docker, Artifacts, Caching, and Performance](modules/module-06-docker-performance.md) | 150 min |
| 7 | Intermediate | [Deployment, Versioning, Tagging, and Release Automation](modules/module-07-release-automation.md) | 150 min |
| 8 | Advanced | [QA Automation Workflows](modules/module-08-qa-automation.md) | 150 min |
| 9 | Advanced | [Monorepos, Enterprise Patterns, and Self-Hosted Runners](modules/module-09-monorepo-best-practices.md) | 150 min |
| 10 | Advanced | [Notifications, Observability, Debugging, and Governance](modules/module-10-notifications.md) | 120 min |
| 11 | Beginner | [Running Python, Shell, Bash, and CMD in Workflows](modules/module-11-running-scripts.md) | 90 min |
| 12 | Beginner | [Scheduling Workflow Runs with Cron](modules/module-12-scheduled-workflows.md) | 90 min |
| 13 | Beginner | [The `on` Section — Workflow Triggers and Event Filters](modules/module-13-workflow-triggers.md) | 120 min |
| 14 | Beginner | [Naming Workflows with `name` and Dynamic `run-name`](modules/module-14-workflow-naming.md) | 90 min |
| 15 | Beginner | [Jobs, Job Naming, `timeout-minutes`, `runs-on`, `env`, and `steps`](modules/module-15-jobs-and-steps.md) | 120 min |
| 16 | Beginner | [Environment Variables and Secrets — Setting and Using Them](modules/module-16-env-and-secrets.md) | 120 min |
| 17 | Beginner | [Artifacts — Uploading Files, Folders, Retention, and Conditions](modules/module-17-artifacts.md) | 120 min |
| 18 | Intermediate | [Essential Workflow Controls — Concurrency, Permissions, Defaults, and More](modules/module-18-misc-features.md) | 120 min |
| 19 | Intermediate | [Runners — What They Are and How Concurrent Runs Behave](modules/module-19-runners.md) | 120 min |
| 20 | Intermediate | [Runner Setup — Creating, Targeting, and Health-Checking Runners](modules/module-20-runner-setup.md) | 150 min |

---

## What Learners Will Build

- Pull request CI workflows with clear checks.
- Secure secret and environment-based deployment workflows.
- Matrix builds across versions and operating systems.
- Multi-language automated test pipelines.
- Docker build and publish workflows with cache.
- QA automation pipelines with reports and screenshots.
- Reusable workflows and composite actions.
- OIDC-based deployment patterns.
- Self-hosted runner and monorepo strategies.
- Notifications, summaries, release tags, and rollback-aware deployment flows.

---

## Completion Criteria

Learners should finish the course able to:

- Explain workflows, events, jobs, runners, steps, actions, contexts, and expressions.
- Build CI pipelines that run tests and publish useful evidence.
- Secure workflows with least-privilege permissions, secrets, environments, and OIDC.
- Optimize slow workflows using caching, parallelization, path filters, and matrix tuning.
- Debug failed workflows from logs, summaries, artifacts, and reruns.
- Design production-ready deployment and QA automation workflows.

---

## Recommended Workshop Delivery

| Session | Content | Format |
| --- | --- | --- |
| 1 | Modules 1-2 | Foundations, syntax, first workflow lab |
| 2 | Modules 3-4 | Secrets, permissions, matrix, reusable workflows |
| 3 | Modules 5-6 | Automated tests, Docker, artifacts, caching |
| 4 | Modules 7-8 | Deployment, releases, QA automation |
| 5 | Modules 9-10 | Monorepos, self-hosted runners, notifications, debugging |
| 6 | Capstone | Team implementation, review, and presentation |

---

## Quick Links

- [Start the modules](modules/README.md)
- [Run workflow examples](examples/)
- [Review advanced workflows](advanced/README.md)
- [Complete capstones](capstones/README.md)
- [Use the reference library](reference/README.md)
- [Study production case studies](case-studies/README.md)
- [Check skills and assessments](assessments/README.md)

---

## Course Philosophy

A good GitHub Actions workflow is not just YAML that runs. It is a reliable engineering system.

It should be understandable, secure, observable, fast enough for the team, and boring in production. This course teaches those habits from the first workflow to the final deployment pipeline.
