# Module 4: Scheduling Workflow Runs with Cron

![Module](https://img.shields.io/badge/Module-4-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20A%20Components-1f6feb?style=flat-square) ![Level](https://img.shields.io/badge/Level-Beginner-2da44e?style=flat-square) ![Time](https://img.shields.io/badge/Time-90%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 3](./module-03-workflow-triggers.md) | [Next: Module 5](./module-05-runners.md)
> Level: **Beginner** | Time: **90 min** | Example workflow: [`module-04-scheduled-workflows.yml`](../examples/module-04-scheduled-workflows.yml)

## Learning Objectives

- Schedule workflows using `on: schedule` with cron expressions.
- Build schedules for hourly, daily, weekly, monthly, weekday, weekend, and every-6-hours cadences.
- Convert local time to UTC for correct scheduling.
- Branch logic based on which schedule triggered a run.

## Key Concepts

`on: schedule`, cron syntax, UTC, multiple schedules, `github.event.schedule`, `workflow_dispatch`

## Expected Outcome

You can schedule a workflow to run at any cadence and route logic based on the cron that fired.

## Concept Flow

```text
Cron Time Reached (UTC) -> schedule Event -> Workflow Run -> github.event.schedule -> Conditional Steps
```

---

## ELI5 Explanation

A cron schedule is an alarm clock for your workflow. You tell GitHub the times to "wake up," and it runs the workflow automatically — every hour, every night, every Monday, or once a month.

## Technical Explanation

The `schedule` trigger uses standard 5-field cron expressions, **always evaluated in UTC**. A workflow can declare several `cron:` entries; each one fires its own run. The exact cron string that triggered a run is available as `github.event.schedule`, so a single workflow can serve multiple cadences and branch with `if:` conditions. Scheduled workflows only run on the default branch, and GitHub may delay runs during periods of high load, so cron is best for "run around this time," not exact-second timing.

## Real-World Use Case

A QA team runs a nightly Behave smoke suite at 1:30 AM UTC, a lightweight API health check every hour, and a full regression every weekend — all from scheduled workflows so no one has to trigger them manually.

## When To Use

- Nightly or periodic regression and smoke suites.
- Recurring maintenance (cleanup, report refresh, dependency checks).
- Health checks at a fixed cadence.
- Reports that must be produced on a calendar (weekly, monthly).

## When NOT To Use

- Work that must run the instant code changes (use `push`/`pull_request`).
- Exact-time guarantees (cron can be delayed under load).
- Schedules on non-default branches (they will not run).

## Common Mistakes

- Writing schedules in local time instead of UTC.
- Expecting second-level or guaranteed on-time precision.
- Putting cron on a feature branch and wondering why it never runs.
- Using `*/30` in the hour field thinking it means "every 30 minutes" (minutes go in the first field).
- Forgetting `workflow_dispatch` so you cannot test the workflow manually.

## Debugging Tips

- Add `workflow_dispatch` so you can run the workflow on demand while testing.
- Print `github.event.schedule` to confirm which cron fired.
- Validate cron strings with a crontab helper before committing.
- Remember the schedule must be merged to the default branch to take effect.

## Cron Cookbook

| Cadence | Cron | Meaning (UTC) |
| --- | --- | --- |
| Hourly | `0 * * * *` | At minute 0 of every hour |
| Every 30 minutes | `*/30 * * * *` | At minute 0 and 30 of every hour |
| Every 6 hours | `0 */6 * * *` | 00:00, 06:00, 12:00, 18:00 |
| Daily | `30 1 * * *` | Every day at 01:30 |
| Weekly | `0 2 * * 1` | Every Monday at 02:00 |
| Weekdays | `0 3 * * 1-5` | Mon–Fri at 03:00 |
| Weekends | `0 4 * * 0,6` | Sat & Sun at 04:00 |
| Monthly | `0 5 1 * *` | 1st of the month at 05:00 |

Day-of-week values: `0` or `7` = Sunday, `1` = Monday, … `6` = Saturday.

## Minimal Workflow Example

```yaml
name: Nightly Schedule

on:
  schedule:
    - cron: "30 1 * * *"   # daily at 01:30 UTC
  workflow_dispatch:

jobs:
  nightly:
    runs-on: ubuntu-latest
    steps:
      - name: Run nightly task
        run: echo "Running nightly smoke suite"
```

### YAML Explanation

- `on: schedule` registers the cron trigger.
- `"30 1 * * *"` runs daily at 01:30 UTC.
- `workflow_dispatch` lets you also run it manually for testing.

### Step-by-Step Execution

1. At 01:30 UTC, GitHub fires the `schedule` event.
2. The workflow starts on the default branch.
3. The runner executes the nightly task.
4. You can also trigger the same workflow manually any time.

## Production Workflow Example

The full example declares every cadence in one workflow and branches on the cron that fired. See [`module-04-scheduled-workflows.yml`](../examples/module-04-scheduled-workflows.yml).

```yaml
on:
  schedule:
    - cron: "0 * * * *"        # Hourly
    - cron: "*/30 * * * *"     # Every 30 minutes
    - cron: "0 */6 * * *"      # Every 6 hours
    - cron: "30 1 * * *"       # Daily at 01:30 UTC
    - cron: "0 2 * * 1"        # Weekly (Monday)
    - cron: "0 3 * * 1-5"      # Weekdays
    - cron: "0 4 * * 0,6"      # Weekends
    - cron: "0 5 1 * *"        # Monthly (1st)
  workflow_dispatch:
```

### Branch on the Triggering Schedule

```yaml
- name: Run nightly regression (daily schedule only)
  if: github.event.schedule == '30 1 * * *'
  run: echo "behave --tags=regression --no-capture"

- name: Run hourly health check
  if: github.event.schedule == '0 * * * *'
  run: echo "python scripts/hello.py --tag healthcheck"
```

`github.event.schedule` is the exact cron string, so one workflow can run different work for different cadences.

### Time Zone Conversion

GitHub uses UTC. Convert before committing:

| Local time | Time zone | UTC cron |
| --- | --- | --- |
| 7:00 AM | IST (UTC+5:30) | `30 1 * * *` |
| 9:00 AM | EST (UTC-5) | `0 14 * * *` |
| 6:00 PM | PST (UTC-8) | `0 2 * * *` (next day) |

### Expected Output

- Each cron entry produces its own scheduled run.
- The run logs the cadence label for the cron that fired.
- Conditional steps run only for their matching schedule.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a daily schedule at your local 9:00 AM converted to UTC. | Workflow runs once per day at the correct UTC time. |
| Intermediate | Add weekday and weekend schedules that print different messages. | Weekday and weekend runs log different output. |
| Challenge | Add an every-6-hours schedule and branch logic using `github.event.schedule`. | Only the 6-hour cron triggers its dedicated step. |

---

[Previous: Module 3](./module-03-workflow-triggers.md) | [Module Index](./README.md) | [Next: Module 5](./module-05-runners.md)
