# Module 3 — Solutions

![Module](https://img.shields.io/badge/Module-3-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 3](../modules/module-03-workflow-triggers.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** `closed` is the only activity type GitHub emits when a pull request
ends, and it covers both outcomes: merged and closed-without-merging. The payload
distinguishes them, so the job needs
`if: github.event.pull_request.merged == true`. Option A is the common bug — a
deploy wired to bare `closed` fires when somebody abandons a PR, which is
exactly when you least want it. There is no `merged` activity type (C). Option D
is not wrong as an *alternative design* — `push` to `main` does approximate
"something merged" — but the `if:` in D can never be true, because within a
`push` run `github.event_name` is `push`.

**2 — C.** `branches` and `branches-ignore` are mutually exclusive on the same
event; supplying both is a schema violation and the workflow fails to load
rather than resolving a precedence rule. The same holds for the `paths` /
`paths-ignore` pair, and for `tags` / `tags-ignore`. Pick the one that expresses
the intent with fewer entries; if you need "all branches except main, plus
release branches", that is a `branches` list with negative patterns
(`["**", "!main"]`) rather than two keys.

**3 — B.** `create` and `delete` fire for any ref, and a tag is a ref. The
payload carries `ref_type`, which is `branch` or `tag`, so branch-only logic must
be guarded with `if: github.event.ref_type == 'branch'`. There is no
`branches`/`types` filter available on `create` and `delete` (A, C) — they are
among the events that take no filters at all, which is precisely why the guard
has to live in an `if:`. Option D changes the event: `push` with `tags-ignore`
would not fire on branch creation the way `create` does, and it fires on every
commit rather than only when a branch appears.

**4.** A `choice` input renders a dropdown limited to the declared `options:`,
so the set of legal values is part of the workflow definition. The value is
validated by the platform before the run is created, and the options list is
self-documenting — the engineer running the workflow does not need to know that
the valid environments are `staging` and `production`, they can see them.

`required: true` on a `string` input is a different guarantee entirely: it only
means the field cannot be submitted empty. `Production`, `prod`, `staging ` (with
a trailing space) and `stging` all satisfy `required: true`. Each of those then
fails deep inside the run — a Behave step that cannot resolve a base URL, or
worse, a deploy that silently targets the wrong place because the code
lower-cased the string and matched a substring. Validation at the form is
cheaper than validation in the job, and far cheaper than no validation.

Use `string` when the value genuinely is free-form (a Behave tag expression, a
Jira key). Use `choice` whenever the set is known and small; use the
`environment` type when the value must name a configured GitHub environment.

**5.** For `push`, the `paths` filter is evaluated against the files changed by
the commits in that push. For `pull_request`, it is evaluated against the pull
request's **diff** — head against base — not against the files touched by the
latest commit. So a `synchronize` event whose newest commit touches nothing
relevant will still run the workflow if any earlier commit in the same PR
changed a matching file.

The inverse is the situation that looks like a bug. You edit
`your-solution-root-folder-name/features/login.feature` in a PR, the workflow
runs, and then you revert that file in a later commit of the same PR. The next
`synchronize` skips the workflow, because the *net* PR diff no longer contains a
matching path, even though your most recent commit clearly touched the file.

Two consequences worth knowing:

- A path-filtered workflow that is also a **required status check** will block
  merges on PRs that never trigger it, because a check that does not run is not
  reported as passing. The standard workaround is a companion job with the same
  name that runs unfiltered and immediately succeeds.
- For very large pushes GitHub may be unable to compute the changed-file list;
  in that case path filters do not apply and the workflow runs. The failure is
  toward running, not skipping.

## Lab 1 — Beginner

**Task:** Add a `push` trigger with `branches-ignore: [main]`.

<details>
<summary>Show solution</summary>

```yaml
name: Branch Checks

on:
  push:
    branches-ignore:
      - main

jobs:
  show:
    runs-on: ubuntu-latest
    steps:
      - name: Print event details
        run: |
          echo "Event:  ${{ github.event_name }}"
          echo "Ref:    ${{ github.ref }}"
          echo "Branch: ${{ github.ref_name }}"
```

**Why this works.** `branches-ignore` is a negative filter on the `push` event:
every branch fires the workflow except the listed ones. Patterns are glob-style,
so `branches-ignore: ["main", "release/**"]` would exclude release branches too.
Because the workflow file is read from the branch the push happened on, a
feature branch that does not yet contain this file will not run it — add the
workflow, push, and the *same* push triggers it.

**Verify the failure mode the lab asks for.** Add a `branches:` key alongside the
existing `branches-ignore:`:

```yaml
on:
  push:
    branches:
      - main
    branches-ignore:
      - main
```

Push it. The workflow does not run and the Actions tab shows a load error for
the file — the two keys cannot coexist on one event, and GitHub rejects the
definition rather than picking a winner. Note that the error surfaces in the
Actions tab, not as a failed run, because the workflow never started.

**Common wrong answer.** `branches-ignore: main` (a bare scalar rather than a
list) happens to be accepted by YAML as a string, but the filter keys expect a
sequence; write it as a list. A more consequential wrong answer is
`on: push` with `if: github.ref != 'refs/heads/main'` on the job. That works,
but it still creates a run for every push to `main` — a skipped job, billed
minutes for the queue, and a noisy history. Filtering at the trigger prevents
the run existing at all.

</details>

## Lab 2 — Intermediate

**Task:** Add a `pull_request` trigger with `types: [opened, closed]` targeting
`main`.

<details>
<summary>Show solution</summary>

```yaml
name: PR Lifecycle

on:
  pull_request:
    types: [opened, closed]
    branches:
      - main

permissions:
  contents: read

jobs:
  lifecycle:
    runs-on: ubuntu-latest
    steps:
      - name: Report the activity type
        run: |
          echo "Event:  ${{ github.event_name }}"
          echo "Action: ${{ github.event.action }}"
          echo "Merged: ${{ github.event.pull_request.merged }}"

      - name: Run smoke suite on open
        if: github.event.action == 'opened'
        run: echo "behave --tags=smoke"

      # `closed` covers merged AND abandoned. Only one of them deserves a deploy.
      - name: Post-merge task
        if: github.event.action == 'closed' && github.event.pull_request.merged == true
        run: echo "PR was merged into main"

      - name: Cleanup after abandonment
        if: github.event.action == 'closed' && github.event.pull_request.merged == false
        run: echo "PR closed without merging"
```

**Why this works.** `types:` narrows the `pull_request` event to two of its
activity types; without it, the default set is `opened`, `synchronize`, and
`reopened` — note that the default does **not** include `closed`, which is why
`closed` has to be listed explicitly. `branches: [main]` filters on the PR's
*base* (target) branch, not its head, so a PR from `feature/x` into `main`
matches and a PR into `develop` does not. `github.event.action` then routes work
within the run.

**Verify the failure mode the lab asks for.** Delete the
`github.event.pull_request.merged == true` clause from the post-merge step, open
a pull request against `main`, and close it **without** merging. The post-merge
step runs anyway and logs as if a merge happened. Substitute a real deploy for
the echo and the consequence is a production deploy triggered by someone tidying
up stale pull requests. There is no error to read here — the run is green, which
is what makes it dangerous.

**Common wrong answer.** Writing `types: [merged]`, which is not a valid
activity type for `pull_request`; the workflow fails to load. The second common
attempt, `if: github.event.pull_request.merged` without `== true`, is more
subtle. Here it happens to be correct — `merged` is a real JSON boolean in the
payload, so it is genuinely `false` on an abandoned PR. But the same shape
applied to `github.event.inputs.*` or an action output is a bug, because those
are strings and `"false"` is truthy. Comparing explicitly costs nothing and
never misleads the next reader.

</details>

## Lab 3 — Challenge

**Task:** Add a `workflow_dispatch` form with a `choice` dropdown, a text input,
and a boolean, then echo all three.

<details>
<summary>Show solution</summary>

The full version, with the other events alongside it, is in
[`module-03-workflow-triggers.yml`](../examples/module-03-workflow-triggers.yml).

```yaml
name: Manual Test Run

on:
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        type: choice
        options:
          - staging
          - production
        default: staging
        required: true
      test_tag:
        description: "Behave tag expression to run"
        type: string
        default: smoke
        required: true
      run_regression:
        description: "Also run the full regression suite"
        type: boolean
        default: false
        required: false

permissions:
  contents: read

jobs:
  manual:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Show manual inputs
        env:
          ENVIRONMENT: ${{ inputs.environment }}
          TEST_TAG: ${{ inputs.test_tag }}
          RUN_REGRESSION: ${{ inputs.run_regression }}
        run: |
          echo "Environment: ${ENVIRONMENT}"
          echo "Test tag:    ${TEST_TAG}"
          echo "Regression:  ${RUN_REGRESSION}"

      - name: Install dependencies
        working-directory: your-solution-root-folder-name
        run: pip install -r requirements.txt

      - name: Run selected suite
        working-directory: your-solution-root-folder-name
        env:
          TEST_TAG: ${{ inputs.test_tag }}
          BASE_URL: "https://${{ inputs.environment }}.your-domain.com"
        run: behave --tags="${TEST_TAG}" -D "base_url=${BASE_URL}"

      # A typed boolean input can be tested directly in the `inputs` context.
      - name: Run full regression
        if: inputs.run_regression
        working-directory: your-solution-root-folder-name
        run: behave --tags=regression --no-capture
```

**Why this works.** Each input declares a `type`, which decides the widget:
`choice` plus `options:` gives a dropdown, `string` gives a text box, `boolean`
gives a checkbox. `default:` pre-fills the form and `required:` decides whether
it can be submitted blank.

Values reach the steps through `env:` rather than being interpolated into the
`run:` line. `test_tag` is free text, so a value like
`smoke; curl http://evil.example` would otherwise be substituted into the shell
command before the shell ever ran — expression interpolation happens first, so
the injected text becomes part of the script. Passing it as an environment
variable and quoting the expansion keeps it data. Note also that the `${{ }}`
expressions all sit on `env:` values, never at column 0 inside a `run: |` block.

`if: inputs.run_regression` works because for `workflow_dispatch` the typed
`inputs` context preserves the boolean.

**Verify the failure mode the lab asks for.** Change the regression guard to
read from the event payload instead of the typed context:

```yaml
        if: github.event.inputs.run_regression
```

Dispatch the workflow with the checkbox **unticked**. The regression step runs
anyway. `github.event.inputs.*` values are strings — the unticked box arrives as
the string `"false"`, and any non-empty string is truthy in an expression. The
correct payload-based form is
`github.event.inputs.run_regression == 'true'`; the correct typed form is
`inputs.run_regression`.

Then reproduce the schema failure: delete `options:` from the `environment`
input while leaving `type: choice`. The workflow no longer loads, because a
`choice` input without options has no legal values. A third one worth seeing:
set `default: prod` on the `environment` input. The default must be one of the
declared options, so this is rejected too — the platform validates the form
definition, not just the submission.

**Common wrong answer.** Interpolating the free-text input straight into the
command as `run: behave --tags=${{ inputs.test_tag }}`. It works for every value
you would type by hand, which is what makes it survive review, and it is a
script-injection hole for every value you would not. The other frequent slip is
reaching for `inputs.*` in a step of a run triggered by `push` or `schedule` —
the context is empty there, so guard with
`if: github.event_name == 'workflow_dispatch'` or supply `|| 'default'`
fallbacks.

</details>

---

[Solutions Index](./README.md) | [Module 3](../modules/module-03-workflow-triggers.md) | [Course Home](../README.md)
