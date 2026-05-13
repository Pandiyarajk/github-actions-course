# Module Study Guide

Use this directory as the main study path. Each module is self-contained and includes objectives, ELI5 and technical explanations, real-world use cases, when to use and avoid the pattern, common mistakes, debugging tips, minimal YAML, production YAML, execution flow, labs, and expected outputs.

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
| Learning objectives | Build matrix jobs, reusable workflows, automated test pipelines, Docker builds, cached workflows, and releases. |
| Key concepts | Matrix strategy, reusable workflow, composite action, test report, Docker image, cache key, environment, release tag. |
| Hands-on exercises | Run version matrices, upload test reports, cache dependencies, publish a Docker image, create deployment tags. |
| Expected outcomes | Learners can design practical team CI/CD workflows with clear feedback and repeatable outputs. |

### Advanced: Modules 8-10

| Requirement | Study Focus |
| --- | --- |
| Learning objectives | Operate QA automation, monorepos, self-hosted runners, notifications, debugging workflows, and governance controls. |
| Key concepts | QA evidence, path filtering, runner labels, OIDC, least privilege, summaries, alerts, concurrency, timeout. |
| Hands-on exercises | Build nightly QA workflows, target self-hosted runners safely, write summaries, add failure notifications, harden permissions. |
| Expected outcomes | Learners can support production-grade automation with security, observability, and maintainability. |

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
