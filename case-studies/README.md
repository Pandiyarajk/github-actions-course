# 🔍 Production Workflow Case Studies

![Section](https://img.shields.io/badge/Section-Case%20Studies-1f6feb?style=flat-square) ![Count](https://img.shields.io/badge/Case%20Studies-5-2da44e?style=flat-square) ![Difficulty](https://img.shields.io/badge/Difficulty-★%20to%20★★★-d29922?style=flat-square) [![Course Home](https://img.shields.io/badge/⬅%20Course%20Home-555?style=flat-square)](../README.md)

These case studies are public-safe teaching material rebuilt from production workflow patterns. They intentionally remove project names, internal architecture, real URLs, real environments, real secret names, and identifiable business logic.

Use this section after the core modules. Each page shows how a production workflow pattern can be simplified for learning and then rebuilt as a generic production-quality example.

## How To Use These Case Studies

Each case study has a **Simple Version** (read this first to get the idea) and a **Production Version** (the realistic shape). Start with the Simple Version, run or adapt it, then study the Production Version one step at a time. The dense, real-world scripting is moved into small helper scripts under [`scripts/`](scripts/) and called from one step, so the workflow YAML stays easy to read.

Difficulty is uneven, so read them easiest-first rather than in number order:

```text
Recommended order:  CS01  ->  CS05  ->  CS03  ->  CS02  ->  CS04
                    (★)      (★)       (★★)       (★★)       (★★★)
```

## Case Study Index

| # | Difficulty | Case Study | What You'll Learn | Suggested Modules |
| --- | --- | --- | --- | --- |
| 1 | ★ | [CI Quality Gates and Build Artifacts](01-ci-quality-gates-and-builds.md) | Gate PRs with quality checks and run expensive checks only when matching files change. | Modules 7, 10, 15 |
| 2 | ★★ | [Self-Hosted QA Regression Workflows](02-self-hosted-qa-regression.md) | Run long regression on self-hosted runners with flexible test selection (full / batch / rerun). | Modules 5, 6, 18 |
| 3 | ★★ | [Pull Request and Branch Lifecycle Automation](03-pr-branch-lifecycle.md) | React to branch/PR events and read the right ref variable for each event. | Modules 3, 19 |
| 4 | ★★★ | [PR Maintenance, Auto-Fix, and Workflow Cleanup](04-pr-maintenance-cleanup.md) | Automate open-PR upkeep and clean old runs safely with a dry-run guard. | Modules 11, 20 |
| 5 | ★ | [AI-Assisted Pull Request Review](05-ai-assisted-review.md) | Run an external review assistant on a PR diff and post concise comments. | Modules 3, 20 |

## Workflow Coverage Map

| Generic Workflow Type | Case Study |
| --- | --- |
| Static code analysis for changed files | [CI Quality Gates and Build Artifacts](01-ci-quality-gates-and-builds.md) |
| Pre-commit pull request checks | [CI Quality Gates and Build Artifacts](01-ci-quality-gates-and-builds.md) |
| Custom script and spreadsheet validation | [CI Quality Gates and Build Artifacts](01-ci-quality-gates-and-builds.md) |
| Windows executable packaging | [CI Quality Gates and Build Artifacts](01-ci-quality-gates-and-builds.md) |
| Embedded firmware artifact build | [CI Quality Gates and Build Artifacts](01-ci-quality-gates-and-builds.md) |
| Self-hosted runner environment setup | [Self-Hosted QA Regression Workflows](02-self-hosted-qa-regression.md) |
| Runner-specific regression workflows | [Self-Hosted QA Regression Workflows](02-self-hosted-qa-regression.md) |
| Scheduled regression workflow | [Self-Hosted QA Regression Workflows](02-self-hosted-qa-regression.md) |
| Failed-test rerun workflow | [Self-Hosted QA Regression Workflows](02-self-hosted-qa-regression.md) |
| Test-cycle reset workflow | [Self-Hosted QA Regression Workflows](02-self-hosted-qa-regression.md) |
| Manual runner maintenance and targeted test execution | [Self-Hosted QA Regression Workflows](02-self-hosted-qa-regression.md) |
| Branch lifecycle alerts | [Pull Request and Branch Lifecycle Automation](03-pr-branch-lifecycle.md) |
| PR open and merge automation | [Pull Request and Branch Lifecycle Automation](03-pr-branch-lifecycle.md) |
| Pull request review comments and submitted reviews | [Pull Request and Branch Lifecycle Automation](03-pr-branch-lifecycle.md) |
| Folder-scoped pull request and push workflows | [Pull Request and Branch Lifecycle Automation](03-pr-branch-lifecycle.md) |
| Checkout depth, ref comparison, and workflow summaries | [Pull Request and Branch Lifecycle Automation](03-pr-branch-lifecycle.md) |
| Commit metadata tracking | [Pull Request and Branch Lifecycle Automation](03-pr-branch-lifecycle.md) |
| Generic comparison reporting | [Pull Request and Branch Lifecycle Automation](03-pr-branch-lifecycle.md) |
| Open PR update and conflict reporting | [PR Maintenance, Auto-Fix, and Workflow Cleanup](04-pr-maintenance-cleanup.md) |
| Scheduled PR auto-fix | [PR Maintenance, Auto-Fix, and Workflow Cleanup](04-pr-maintenance-cleanup.md) |
| Workflow run cleanup | [PR Maintenance, Auto-Fix, and Workflow Cleanup](04-pr-maintenance-cleanup.md) |
| Automated PR review with external assistant | [AI-Assisted Pull Request Review](05-ai-assisted-review.md) |

## Course Integration

| Level | How to Use These Case Studies |
| --- | --- |
| Beginner | Read the simple YAML examples to understand the minimum useful workflow. |
| Intermediate | Compare simple and production versions to learn artifacts, cache, conditions, permissions, and summaries. |
| Advanced | Study self-hosted runners, long-running QA workflows, PR automation, cleanup jobs, and review governance. |

## Gaps These Case Studies Add to the Course

- Safer self-hosted runner design and runner label strategy.
- Workflow permissions and token scope selection.
- Pull request automation risks, especially forks and protected branches.
- External system integration with retries, rate limits, and non-secret logging.
- Reusable workflows to remove duplicate runner-specific YAML.

---

[Course Home](../README.md) | [Module Study Guide](../modules/README.md) | [Reference Library](../reference/README.md)
