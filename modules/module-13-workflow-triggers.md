# Module 13: The `on` Section — Workflow Triggers and Event Filters

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 12](./module-12-scheduled-workflows.md) | [Next: Module 14](./module-14-workflow-naming.md)
> Level: **Beginner** | Time: **120 min** | Example workflow: [`module-13-workflow-triggers.yml`](../examples/module-13-workflow-triggers.yml)

## Learning Objectives

- Understand the `on` section and how events start a workflow.
- Use `create`, `delete`, `push`, `pull_request`, review, issue, and `schedule` triggers.
- Filter events by `branches`, `branches-ignore`, `paths`, and `types`.
- Define manual `workflow_dispatch` inputs: text, dropdown (`choice`), boolean, with `default` and `required`.

## Key Concepts

`on`, events, `types`, `branches`, `branches-ignore`, `paths`, `workflow_dispatch`, inputs, `github.event_name`, `github.event.action`

## Expected Outcome

You can design the `on` section so a workflow runs for exactly the events you want and accepts the manual inputs you need.

## Concept Flow

```text
GitHub Event -> on: matches event + filters -> Workflow Run -> github.event_name / action -> Conditional Steps
```

---

## ELI5 Explanation

The `on` section is the list of "when should I wake up?" rules for a workflow. You can say "wake up when someone opens a pull request to main," "wake up when a branch is deleted," or "wake up when I press the run button and pick options from a menu."

## Technical Explanation

`on` declares one or more events. Each event can have filters:

- **`types`** narrows which sub-actions of an event fire it (e.g. `pull_request` `opened`, `closed`).
- **`branches` / `branches-ignore`** restrict which branches the event applies to (use one, not both).
- **`paths` / `paths-ignore`** restrict to changed file paths.
- **`workflow_dispatch.inputs`** define manual run parameters with a `type` (`string`, `choice`, `boolean`, `number`, `environment`), a `description`, a `default`, and `required`.

At runtime, `github.event_name` tells you the event, and `github.event.action` tells you the sub-type. Manual inputs are read with `${{ inputs.<name> }}`.

## Real-World Use Case

A QA repo runs static checks on every branch except `main` (push with `branches-ignore`), runs BDD checks on PRs targeting `main` (`pull_request` with `types: [opened, synchronize, reopened]`), and exposes a manual run where the engineer picks an environment and browser from dropdowns and types a Behave tag.

## When To Use

- You want a workflow to react to specific repository events.
- You need to limit runs to certain branches or file paths.
- You want manual runs with controlled, validated inputs.

## When NOT To Use

- Listening to every event when only one is needed (wasted runs).
- Combining `branches` and `branches-ignore` on the same event (invalid).
- Free-text inputs where a `choice` dropdown would prevent typos.

## Common Mistakes

- Treating every `pull_request: closed` as a merge (check `merged == true`).
- Using both `branches` and `branches-ignore` together.
- Forgetting that `create`/`delete` fire for both branches and tags (filter with `ref_type`).
- Expecting `paths` filters to apply to `pull_request` the same way as `push` (PR uses the diff).
- Forgetting `required` or `default` on `workflow_dispatch` inputs.

## Debugging Tips

- Print `github.event_name`, `github.event.action`, and `github.ref`.
- Use `workflow_dispatch` to test manually without waiting for an event.
- Echo each input value to confirm dropdown/text wiring.
- Check that `create`/`delete` steps guard on `github.event.ref_type == 'branch'`.

## Trigger Reference

| Event | Common `types` | Notes |
| --- | --- | --- |
| `push` | — | Filter with `branches` / `branches-ignore` / `paths` |
| `pull_request` | `opened`, `synchronize`, `reopened`, `closed` | `closed` + `merged == true` = merged |
| `create` / `delete` | — | Fires for branches and tags; filter with `ref_type` |
| `pull_request_review` | `submitted`, `edited`, `dismissed` | Review approval/changes/comment |
| `pull_request_review_comment` | `created`, `edited`, `deleted` | Inline code-review comment |
| `issues` | `opened`, `closed`, `labeled` | Issue lifecycle |
| `issue_comment` | `created`, `edited` | Comment on issue or PR conversation |
| `schedule` | — | Cron, UTC (see Module 12) |
| `workflow_dispatch` | — | Manual run with `inputs` |
| `workflow_call` | — | Reusable workflow (see Module 4) |

## Minimal Workflow Example

```yaml
name: Triggers Basics

on:
  push:
    branches-ignore:
      - main          # run on every branch except main
  pull_request:
    types: [opened, closed]
    branches:
      - main          # only PRs targeting main

jobs:
  show:
    runs-on: ubuntu-latest
    steps:
      - name: Print event
        run: |
          echo "Event: ${{ github.event_name }}"
          echo "Action: ${{ github.event.action }}"
```

### YAML Explanation

- `push.branches-ignore: [main]` runs the workflow on all branches except `main`.
- `pull_request.types: [opened, closed]` fires only when a PR is opened or closed.
- `pull_request.branches: [main]` restricts it to PRs targeting `main`.

### Step-by-Step Execution

1. A push to a feature branch fires the `push` event (main is ignored).
2. Opening a PR to `main` fires the `pull_request` `opened` action.
3. The step prints the event name and action.

## Production Workflow Example

The full example combines branch lifecycle, push, pull request, review, issue, schedule, and a rich manual-input form in one place. See [`module-13-workflow-triggers.yml`](../examples/module-13-workflow-triggers.yml).

### Filter Push by Branch and Path

```yaml
on:
  push:
    branches-ignore:
      - main
    paths:
      - "your-solution-root-folder-name/**"
      - "features/**"
```

Use `branches` to include only certain branches, or `branches-ignore` to exclude some — never both on the same event.

### Pull Request with Types and Target Branch

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, closed]
    branches:
      - main
      - "release/**"
```

### Branch Create and Delete

```yaml
on:
  create:
  delete:
```

```yaml
- name: Handle branch created
  if: github.event_name == 'create' && github.event.ref_type == 'branch'
  run: echo "Branch created: ${{ github.event.ref }}"
```

`create`/`delete` fire for tags too, so guard branch logic with `ref_type == 'branch'`.

### Manual Run with Typed Inputs

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:           # dropdown
        description: "Target environment"
        type: choice
        options:
          - staging
          - production
        default: staging
        required: true
      test_tag:              # free text
        description: "Behave tag to run"
        type: string
        default: smoke
        required: true
      run_regression:        # toggle
        description: "Also run full regression"
        type: boolean
        default: false
        required: false
```

Read them in steps:

```yaml
- name: Show manual inputs
  if: github.event_name == 'workflow_dispatch'
  run: |
    echo "Environment: ${{ inputs.environment }}"
    echo "Test tag:    ${{ inputs.test_tag }}"
    echo "Regression:  ${{ inputs.run_regression }}"
```

### Input Types

| `type` | UI shown | Use for |
| --- | --- | --- |
| `string` | Text box | Free-text values (tags, names) |
| `choice` | Dropdown | A fixed set of `options` |
| `boolean` | Checkbox | On/off toggles |
| `number` | Text box (numeric) | Counts, IDs |
| `environment` | Environment picker | Selecting a configured environment |

### Expected Output

- Pushes to non-`main` branches trigger the workflow when matching paths change.
- PRs to `main`/`release/**` trigger on the listed actions.
- Branch create/delete and review/issue events trigger their steps.
- Manual runs show a form with dropdowns, text, and a toggle.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a `push` trigger with `branches-ignore: [main]`. | Workflow runs on feature branches but not main. |
| Intermediate | Add a `pull_request` trigger with `types: [opened, closed]` targeting main. | Runs only on PR open and close events for main. |
| Challenge | Add a `workflow_dispatch` form with a `choice` dropdown, a text input, and a boolean, then echo all three. | Manual run shows the form and logs the selected values. |

---

[Previous: Module 12](./module-12-scheduled-workflows.md) | [Module Index](./README.md) | [Next: Module 14](./module-14-workflow-naming.md)
