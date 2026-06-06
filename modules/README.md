# Module Study Guide

Use this directory as the main study path. Each module is self-contained and includes objectives, ELI5 and technical explanations, real-world use cases, when to use and avoid the pattern, common mistakes, debugging tips, minimal YAML, production YAML, execution flow, labs, and expected outputs.

All examples are oriented around **Python test automation** as used in real-world projects:

- **Web automation suite** — Selenium + Behave (Python BDD) web automation with Allure reporting, multi-browser (chrome/firefox/msedge), daily scheduled smoke tests, and SMTP email notifications.
- **Desktop/UI regression suite** — Windows-based regression automation on self-hosted runners (`server1`–`server4`), Python report generation, Zephyr Scale + Jira integration, and SMTP email reports.

Conventions used throughout: Python 3.13, Behave, Selenium, Allure, `pylint`, self-hosted runner labels `server1`–`server4`, and the generic placeholders `your-solution-root-folder-name/` and `your-domain.com`.

## Recommended Path

```text
Beginner:     Modules 1-3
Intermediate: Modules 4-7
Advanced:     Modules 8-10
Capstones:    Apply everything in realistic delivery scenarios
```

## Level Breakdown

### Beginner: Modules 1-3

| Requirement | Study Focus |
| --- | --- |
| Learning objectives | Understand CI/CD, workflow syntax, triggers, jobs, steps, secrets, variables, and basic debugging. |
| Key concepts | Workflow, event, runner, job, step, action, context, expression, secret, variable, artifact. |
| Hands-on exercises | Create first workflows, use manual inputs, run pull request checks, validate secrets, upload one artifact. |
| Expected outcomes | Learners can build and debug simple CI workflows without copying blindly. |

### Intermediate: Modules 4-7

| Requirement | Study Focus |
| --- | --- |
| Learning objectives | Build browser/server matrix jobs, reusable workflows, multi-layer Python test pipelines, Selenium Grid via Docker, cached workflows, and Zephyr release cycles. |
| Key concepts | Matrix strategy, reusable workflow, composite action, Allure report, Selenium Grid, pip cache key, environment, Zephyr test cycle. |
| Hands-on exercises | Run browser matrices, upload Allure reports, cache pip dependencies, run Behave against a Selenium Grid, create Zephyr release cycles. |
| Expected outcomes | Learners can design practical team test-automation workflows with clear feedback and repeatable outputs. |

### Advanced: Modules 8-10

| Requirement | Study Focus |
| --- | --- |
| Learning objectives | Operate nightly QA automation, monorepo path filtering, self-hosted runners, SMTP notifications, debugging workflows, and governance controls. |
| Key concepts | Allure evidence, path filtering, runner labels (`server1`–`server4`), least privilege, step summaries, SMTP alerts, concurrency, timeout. |
| Hands-on exercises | Build nightly Behave/Selenium QA workflows, target self-hosted runners safely, write step summaries, add SMTP failure notifications, harden permissions. |
| Expected outcomes | Learners can support production-grade test automation with security, observability, and maintainability. |

## Module Index

| # | Level | Module | Time | Runnable Example |
| --- | --- | --- | --- | --- |
| 1 | Beginner | [CI/CD and GitHub Actions Foundations](module-01-ci-foundations.md) | 90 min | [`module-01-ci-foundations.yml`](../examples/module-01-ci-foundations.yml) |
| 2 | Beginner | [Workflow Syntax, Jobs, Steps, and Expressions](module-02-workflow-syntax.md) | 120 min | [`module-02-syntax-and-expressions.yml`](../examples/module-02-syntax-and-expressions.yml) |
| 3 | Beginner | [Secrets, Variables, and Secure Pipelines](module-03-secrets-security.md) | 120 min | [`module-03-secrets-security.yml`](../examples/module-03-secrets-security.yml) |
| 4 | Intermediate | [Matrix Builds, Marketplace Actions, and Reusable Workflows](module-04-matrix-and-reuse.md) | 120 min | [`module-04-matrix-and-reuse.yml`](../examples/module-04-matrix-and-reuse.yml) |
| 5 | Intermediate | [Automated Testing Pipelines](module-05-multi-language-tests.md) | 120 min | [`module-05-multi-language-tests.yml`](../examples/module-05-multi-language-tests.yml) |
| 6 | Intermediate | [Docker, Artifacts, Caching, and Performance](module-06-docker-performance.md) | 150 min | [`module-06-docker-performance.yml`](../examples/module-06-docker-performance.yml) |
| 7 | Intermediate | [Deployment, Versioning, Tagging, and Release Automation](module-07-release-automation.md) | 150 min | [`module-07-release-automation.yml`](../examples/module-07-release-automation.yml) |
| 8 | Advanced | [QA Automation Workflows](module-08-qa-automation.md) | 150 min | [`module-08-qa-automation.yml`](../examples/module-08-qa-automation.yml) |
| 9 | Advanced | [Monorepos, Enterprise Patterns, and Self-Hosted Runners](module-09-monorepo-best-practices.md) | 150 min | [`module-09-monorepo-best-practices.yml`](../examples/module-09-monorepo-best-practices.yml) |
| 10 | Advanced | [Notifications, Observability, Debugging, and Governance](module-10-notifications.md) | 120 min | [`module-10-notifications.yml`](../examples/module-10-notifications.yml) |
| 11 | Beginner | [Running Python, Shell, Bash, and CMD in Workflows](module-11-running-scripts.md) | 90 min | [`module-11-running-scripts.yml`](../examples/module-11-running-scripts.yml) |
| 12 | Beginner | [Scheduling Workflow Runs with Cron](module-12-scheduled-workflows.md) | 90 min | [`module-12-scheduled-workflows.yml`](../examples/module-12-scheduled-workflows.yml) |
| 13 | Beginner | [The `on` Section — Workflow Triggers and Event Filters](module-13-workflow-triggers.md) | 120 min | [`module-13-workflow-triggers.yml`](../examples/module-13-workflow-triggers.yml) |
| 14 | Beginner | [Naming Workflows with `name` and Dynamic `run-name`](module-14-workflow-naming.md) | 90 min | [`module-14-workflow-naming.yml`](../examples/module-14-workflow-naming.yml) |
| 15 | Beginner | [Jobs, Job Naming, `timeout-minutes`, `runs-on`, `env`, and `steps`](module-15-jobs-and-steps.md) | 120 min | [`module-15-jobs-and-steps.yml`](../examples/module-15-jobs-and-steps.yml) |
| 16 | Beginner | [Environment Variables and Secrets — Setting and Using Them](module-16-env-and-secrets.md) | 120 min | [`module-16-env-and-secrets.yml`](../examples/module-16-env-and-secrets.yml) |
| 17 | Beginner | [Artifacts — Uploading Files, Folders, Retention, and Conditions](module-17-artifacts.md) | 120 min | [`module-17-artifacts.yml`](../examples/module-17-artifacts.yml) |
| 18 | Intermediate | [Essential Workflow Controls — Concurrency, Permissions, Defaults, and More](module-18-misc-features.md) | 120 min | [`module-18-misc-features.yml`](../examples/module-18-misc-features.yml) |
| 19 | Intermediate | [Runners — What They Are and How Concurrent Runs Behave](module-19-runners.md) | 120 min | [`module-19-runners.yml`](../examples/module-19-runners.yml) |
| 20 | Intermediate | [Runner Setup — Creating, Targeting, and Health-Checking Runners](module-20-runner-setup.md) | 150 min | [`module-20-runner-setup.yml`](../examples/module-20-runner-setup.yml) |

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
