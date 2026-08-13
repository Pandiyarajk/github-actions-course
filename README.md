<div align="center">

# ⚙️ GitHub Actions Enablement Course

### Learn GitHub Actions the way real teams use it — workflow by workflow, from your first `name:` to production QA automation.

<br/>

[![Level](https://img.shields.io/badge/Level-Beginner→Advanced-1f6feb?style=for-the-badge)](modules/README.md)
[![Modules](https://img.shields.io/badge/Modules-26-2da44e?style=for-the-badge)](modules/README.md)
[![Format](https://img.shields.io/badge/Format-Self--Paced%20%2B%20Workshop-d29922?style=for-the-badge)](#-recommended-workshop-delivery)
[![License](https://img.shields.io/badge/License-MIT-8957e5?style=for-the-badge)](LICENSE)

<br/>

![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=flat-square&logo=selenium&logoColor=white)
![Behave](https://img.shields.io/badge/Behave_BDD-2C5BB4?style=flat-square&logo=cucumber&logoColor=white)
![Allure](https://img.shields.io/badge/Allure-FF6A00?style=flat-square&logo=qameta&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Jira](https://img.shields.io/badge/Jira-0052CC?style=flat-square&logo=jira&logoColor=white)

</div>

A practical, industry-ready GitHub Actions course for developers, QA engineers, SDETs, and DevOps beginners. It is organized as study material rather than one long README: **start here, follow the module path, complete the labs, then finish with capstones.**

> [!TIP]
> New to the repo? Jump straight to the **[Module Study Guide](modules/README.md)** and start with Module 1.

---

## 🚀 Start Here

1. Read this page to understand the path.
2. Open the [Module Study Guide](modules/README.md).
3. Work through Modules 1-11 to learn the workflow file top-to-bottom (`name`, `on`, scheduling, runners, jobs, env/secrets, scripts, artifacts, and core controls).
4. Continue with Modules 12-20 for applied CI/CD skills (syntax, secure pipelines, matrix/reuse, testing, caching, releases, QA automation, monorepos, observability).
5. Take Modules 21-26 for platform, security, and operations topics (composite actions, containers, image publishing, supply-chain security, approvals, cost control).
6. Finish with the [Capstones](capstones/README.md), checking your work against [Solutions](solutions/README.md) as you go.

```text
Code Change -> GitHub Event -> Workflow -> Runner
                                            |
                          +-----------------+-----------------+
                          |                 |                 |
                        Job A             Job B             Job C     (parallel by default;
                          |                 |                 |        `needs:` makes them wait)
                       Step ->           Step ->           Step ->
                    Test / Build / Scan / Lint / Publish
                          |                 |                 |
                          +-----------------+-----------------+
                                            |
                              Artifact / Image -> Deploy / Notify
```

> [!NOTE]
> Jobs run **in parallel** unless you declare `needs:`. Only *steps* are
> strictly sequential. Module 7 covers the distinction, and Module 26 covers why
> it matters for cost.

---

## 🗂️ Course Structure

| Area | Link | Purpose |
| --- | --- | --- |
| 📘 Study modules | [modules/](modules/README.md) | Main beginner-to-advanced learning path. |
| ▶️ Runnable examples | [examples/](examples/) | YAML workflows paired with each module. |
| 🔑 Solutions | [solutions/](solutions/README.md) | Worked answers for every quiz and lab, with the failure mode each one provokes. |
| 🏆 Capstones | [capstones/](capstones/README.md) | Realistic final projects and evaluation rubrics. |
| ✅ Assessments | [assessments/](assessments/README.md) | Final assessment, skill checklist, and review prompts. |
| 📑 Reference | [reference/](reference/README.md) | Cheat sheet, contexts table, advanced topics, debugging clinic, and production checklists. |
| 🧪 Advanced workflow library | [advanced/](advanced/README.md) | Production-grade scenarios and reusable cloud deployment examples. |
| 🔍 Production case studies | [case-studies/](case-studies/README.md) | Public-safe real-world workflow patterns rebuilt as learning modules. |

---

## 👥 Audience and Prerequisites

| Area | Details |
| --- | --- |
| Audience | Developers, QA automation engineers, SDETs, junior DevOps engineers, and technical leads. |
| Prerequisites | Git basics, command-line comfort, basic YAML, and one scripting or programming language. |
| Delivery | Self-paced study, live workshop, bootcamp, or internal engineering enablement. |
| Learning loop | Concept -> visual model -> workflow demo -> hands-on lab -> debugging clinic -> quiz. |
| Toolkit | GitHub Actions, GitHub CLI, Docker, Python 3.13, Behave (BDD), Selenium, Allure, pylint, Zephyr Scale, Jira, SMTP email. |

---

## 🧭 Learning Path

The 26 modules follow the workflow file top-to-bottom (**Part A**), apply it to real pipelines
(**Part B**), then cover the platform, security, and operational concerns that surround it
(**Part C**).

```text
Part A · Components (1–11)  ─▶  Part B · Applied CI/CD (12–20)  ─▶  Part C · Platform (21–26)  ─▶  🏆 Capstone
name → on → runners → jobs      syntax → security → matrix →        composite actions →
→ env → scripts → artifacts     testing → caching → release →       containers → image publish →
→ controls                      QA → monorepo → notifications       supply chain → approvals → cost
```

### Part A — Workflow Components

| # | Module | Level | ⏱️ Time |
| :-: | --- | :-: | :-: |
| 1 | [CI/CD and GitHub Actions Foundations](modules/module-01-ci-foundations.md) | 🟢 Beginner | 90 min |
| 2 | [Naming Workflows with `name` and Dynamic `run-name`](modules/module-02-workflow-naming.md) | 🟢 Beginner | 90 min |
| 3 | [The `on` Section — Workflow Triggers and Event Filters](modules/module-03-workflow-triggers.md) | 🟢 Beginner | 120 min |
| 4 | [Scheduling Workflow Runs with Cron](modules/module-04-scheduled-workflows.md) | 🟢 Beginner | 90 min |
| 5 | [Runners — What They Are and How Concurrent Runs Behave](modules/module-05-runners.md) | 🟡 Intermediate | 120 min |
| 6 | [Runner Setup — Creating, Targeting, and Health-Checking Runners](modules/module-06-runner-setup.md) | 🟡 Intermediate | 150 min |
| 7 | [Jobs, Job Naming, `timeout-minutes`, `runs-on`, `env`, and `steps`](modules/module-07-jobs-and-steps.md) | 🟢 Beginner | 120 min |
| 8 | [Environment Variables and Secrets — Setting and Using Them](modules/module-08-env-and-secrets.md) | 🟢 Beginner | 120 min |
| 9 | [Running Python, Shell, Bash, and CMD in Workflows](modules/module-09-running-scripts.md) | 🟢 Beginner | 90 min |
| 10 | [Artifacts — Uploading Files, Folders, Retention, and Conditions](modules/module-10-artifacts.md) | 🟢 Beginner | 120 min |
| 11 | [Essential Workflow Controls — Concurrency, Permissions, Defaults, and More](modules/module-11-misc-features.md) | 🟡 Intermediate | 120 min |

### Part B — Applied CI/CD

| # | Module | Level | ⏱️ Time |
| :-: | --- | :-: | :-: |
| 12 | [Workflow Syntax, Jobs, Steps, and Expressions](modules/module-12-workflow-syntax.md) | 🟢 Beginner | 120 min |
| 13 | [Secrets, Variables, and Secure Pipelines](modules/module-13-secrets-security.md) | 🟢 Beginner | 120 min |
| 14 | [Matrix Builds, Marketplace Actions, and Reusable Workflows](modules/module-14-matrix-and-reuse.md) | 🟡 Intermediate | 120 min |
| 15 | [Automated Testing Pipelines](modules/module-15-multi-language-tests.md) | 🟡 Intermediate | 120 min |
| 16 | [Docker, Artifacts, Caching, and Performance](modules/module-16-docker-performance.md) | 🟡 Intermediate | 150 min |
| 17 | [Deployment, Versioning, Tagging, and Release Automation](modules/module-17-release-automation.md) | 🟡 Intermediate | 150 min |
| 18 | [QA Automation Workflows](modules/module-18-qa-automation.md) | 🔴 Advanced | 150 min |
| 19 | [Monorepos, Enterprise Patterns, and Self-Hosted Runners](modules/module-19-monorepo-best-practices.md) | 🔴 Advanced | 150 min |
| 20 | [Notifications, Observability, Debugging, and Governance](modules/module-20-notifications.md) | 🔴 Advanced | 120 min |

### Part C — Platform, Security, and Operations

| # | Module | Level | ⏱️ Time |
| :-: | --- | :-: | :-: |
| 21 | [Composite Actions and Custom Actions](modules/module-21-composite-actions.md) | 🟡 Intermediate | 120 min |
| 22 | [Container Jobs and Service Containers](modules/module-22-container-jobs.md) | 🟡 Intermediate | 120 min |
| 23 | [Building and Publishing Docker Images](modules/module-23-docker-publish.md) | 🟡 Intermediate | 150 min |
| 24 | [Supply Chain Security and `GITHUB_TOKEN`](modules/module-24-supply-chain-security.md) | 🔴 Advanced | 150 min |
| 25 | [Environments, Approvals, and Branch Protection](modules/module-25-environments-approvals.md) | 🔴 Advanced | 150 min |
| 26 | [Local Testing, Linting, and Cost Control](modules/module-26-local-testing-cost.md) | 🟡 Intermediate | 120 min |

---

## 🛠️ What Learners Will Build

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

## 🎯 Completion Criteria

Learners should finish the course able to:

- Explain workflows, events, jobs, runners, steps, actions, contexts, and expressions.
- Build CI pipelines that run tests and publish useful evidence.
- Secure workflows with least-privilege permissions, secrets, environments, and OIDC.
- Optimize slow workflows using caching, parallelization, path filters, and matrix tuning.
- Debug failed workflows from logs, summaries, artifacts, and reruns.
- Design production-ready deployment and QA automation workflows.
- Package reusable logic as composite actions and reusable workflows, and choose correctly between them.
- Recognize and defuse the fork-PR privilege-escalation and expression-injection patterns.
- Gate deployments behind environments and reason about what a green required check actually proves.
- Keep action versions current and control billed runner minutes.

---

## 📅 Recommended Workshop Delivery

| Session | Content | Format |
| --- | --- | --- |
| 1 | Modules 1-4 | CI foundations, workflow naming, triggers, scheduling |
| 2 | Modules 5-7 | Runners, runner setup, jobs and steps |
| 3 | Modules 8-11 | Env and secrets, scripts, artifacts, core controls |
| 4 | Modules 12-14 | Syntax and expressions, secure pipelines, matrix and reuse |
| 5 | Modules 15-17 | Automated testing, Docker and caching, release automation |
| 6 | Modules 18-20 | QA automation, monorepos and self-hosted, notifications |
| 7 | Modules 21-23 | Composite actions, container and service jobs, publishing images |
| 8 | Modules 24-26 | Supply-chain security, environments and approvals, local testing and cost |
| 9 | Capstone | Team implementation, review, and presentation |

---

## 🔗 Quick Links

| | | |
| --- | --- | --- |
| 📘 [Start the modules](modules/README.md) | ▶️ [Run workflow examples](examples/) | 🧪 [Advanced workflows](advanced/README.md) |
| 🏆 [Complete capstones](capstones/README.md) | 📑 [Reference library](reference/README.md) | 🔍 [Production case studies](case-studies/README.md) |
| ✅ [Skills and assessments](assessments/README.md) | 🔑 [Lab solutions](solutions/README.md) | 🔧 [Debugging clinic](reference/debugging-clinic.md) |

---

## 💡 Course Philosophy

> A good GitHub Actions workflow is not just YAML that runs — it is a reliable engineering system.

It should be **understandable, secure, observable, fast enough for the team, and boring in production.** This course teaches those habits from the first workflow to the final deployment pipeline.

<div align="center">

---

⭐ **Star this repo if it helped you learn GitHub Actions.**

[Modules](modules/README.md) · [Examples](examples/) · [Solutions](solutions/README.md) · [Capstones](capstones/README.md) · [Reference](reference/README.md)

</div>
