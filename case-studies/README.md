# Production Workflow Case Studies

These case studies are public-safe teaching material rebuilt from production workflow patterns. They intentionally remove project names, internal architecture, real URLs, real environments, real secret names, and identifiable business logic.

Use this section after the core modules. Each page shows how a production workflow pattern can be simplified for learning and then rebuilt as a generic production-quality example.

## Case Study Index

| # | Level | Case Study | Source Pattern Covered | Suggested Module |
| --- | --- | --- | --- | --- |
| 1 | Intermediate | [CI Quality Gates and Build Artifacts](01-ci-quality-gates-and-builds.md) | Static analysis, pre-commit checks, custom validation, Windows packaging, firmware artifacts | Modules 5-7 |
| 2 | Advanced | [Self-Hosted QA Regression Workflows](02-self-hosted-qa-regression.md) | Environment setup, scheduled/manual regression, batch tests, failed-test reruns, test-cycle reset | Modules 8-9 |
| 3 | Advanced | [Pull Request and Branch Lifecycle Automation](03-pr-branch-lifecycle.md) | Branch create/delete alerts, PR open/merge automation, commit tracking, comparison reports | Modules 9-10 |
| 4 | Advanced | [PR Maintenance, Auto-Fix, and Workflow Cleanup](04-pr-maintenance-cleanup.md) | Updating open PRs, conflict reporting, scheduled auto-fix, workflow run cleanup | Module 10 |
| 5 | Advanced | [AI-Assisted Pull Request Review](05-ai-assisted-review.md) | Automated review comments using an external review assistant | Module 10 |

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
