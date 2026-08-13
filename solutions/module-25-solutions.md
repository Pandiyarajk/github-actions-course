# Module 25 — Solutions

![Module](https://img.shields.io/badge/Module-25-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 25](../modules/module-25-environments-approvals.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** An environment's approval gate holds the job in a *waiting* state
before the runner is even assigned, so no step has executed — not the deploy
step, not `actions/checkout`. There is no output to inspect because nothing has
produced any. A reviewer is therefore approving a **commit**, not a preview of
what the job will do.

**A** is the tempting one: it assumes the sequence is "run, then approve, then
reveal logs", which is how a manual release script usually works. Actions does
the opposite. **C** invents a permission — `actions: read` governs the API's
access to run data, not gate ordering. **D** is a plausible-sounding org-policy
story, but log visibility follows repository read access and has nothing to do
with gating.

**2 — B.** A job excluded by a path filter (or by an `if:`) reports a conclusion
of `skipped`, and **a skipped required status check does not block a merge**.
The PR merges. That is usually what you want for a docs-only change, and it is
exactly what bites you when the filter is subtly wrong: the check that was
supposed to protect `src/**` contributes nothing and reports no problem.

**A** describes what most people expect — a check that never reports green must
block — but `skipped` *is* a report, and it is treated as satisfying the rule.
**C** is wrong because branch protection does not override a workflow's own
triggers; it cannot force a filtered job to run. **D** describes the behaviour
of a check that is *pending* forever, which is a different state entirely.

**3 — B.** Only the timing. Repository secrets are readable by every job in
every workflow in the repository, so the staging job, the nightly regression
job, and any new job someone adds tomorrow can already read the production
credential. Adding `environment: production` makes the *deployment* wait for a
human, and does nothing whatever to the credential's blast radius. To actually
scope the credential you must delete the repository secret and recreate it as an
environment secret on `production`.

**A** is the belief the whole exercise is built on — that declaring an
environment retroactively scopes secrets. It does not; scoping is a property of
where the secret is *stored*. **C** compounds A. **D** confuses
`environment.url`, which is cosmetic, with the protection rules.

**4.** The gate is skipped exactly when it is needed, so it never fails.

`if: needs.test.result == 'success'` is evaluated under the default job
condition, which already requires all `needs:` to have succeeded. When `test`
fails, the runner does not evaluate the expression and reach `false` — it marks
`gate` as `skipped` because an upstream dependency failed. `gate` therefore
reports `skipped`, and by the rule from question 2 a skipped required check does
not block the merge. The result is a branch protection rule that passes on
precisely the pull requests it exists to stop, which is worse than no rule at
all because the tick looks legitimate.

The fix is `if: always()`, plus an explicit assertion in the body, because
`always()` makes the job run but does not make it fail:

```yaml
jobs:
  gate:
    name: Release gate
    if: always()
    needs: [lint, test]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Verify upstream results
        run: |
          for result in "${{ needs.lint.result }}" "${{ needs.test.result }}"; do
            case "$result" in
              success|skipped) ;;
              *) echo "::error::Upstream job concluded '$result'"; exit 1 ;;
            esac
          done
```

Note the two halves. `if: always()` guarantees the gate *reports*;
the `case` statement decides *what* it reports. `success|skipped` passes because
an intentionally filtered job must not block; `failure` and `cancelled` fall
through to `exit 1`. Also note the diagnostic value of requiring only `gate`:
renaming `lint` or `test` later cannot silently detach branch protection,
because the protection rule names `Release gate`, which does not change.

**5.** The workflow is almost certainly missing `on: merge_group`.

A merge queue does not re-run the pull request's `pull_request` checks. It
creates a temporary branch combining the queued PRs and dispatches the
**`merge_group`** event against it. A workflow triggered only by
`pull_request` therefore has nothing to run for a queue entry, the queue finds
no required checks reporting for that run, and it merges. The tests did pass —
on the PR, before queueing — which is why this looks like the queue is ignoring
protection rather than like a missing trigger.

The one-line fix, added alongside the existing triggers:

```yaml
on:
  pull_request:
  merge_group:
```

Two follow-ups worth doing at the same time. First, any `if:` in the workflow
that keys on `github.event_name == 'pull_request'` will now silently disable
itself for queue runs — audit those. Second, `github.event.pull_request.*` is
unavailable under `merge_group`, so steps reading the PR number need a fallback.

## Lab 1 — Beginner

**Task:** Create a `staging` environment and a job that declares it, then add a
1-minute wait timer and observe the pause.

<details>
<summary>Show solution</summary>

The environment itself is repository configuration, not YAML: **Settings →
Environments → New environment**, name it `staging`, and set **Wait timer** to
`1`. The workflow only has to name it.

```yaml
name: Staging Wait Timer Demo

on: workflow_dispatch

permissions:
  contents: read

jobs:
  deploy-staging:
    name: Deploy to staging
    runs-on: ubuntu-latest
    timeout-minutes: 10
    # Naming the environment is what subjects this job to the environment's
    # protection rules. The wait timer is configured in Settings, not here.
    environment:
      name: staging
      url: https://staging.your-domain.com
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Record when the job actually started
        run: |
          echo "Steps began at $(date --utc '+%H:%M:%SZ')."
          echo "Compare this against the run's queued time in the UI."

      - name: Deploy
        run: echo "Deploying to staging.your-domain.com"
```

**Why this works.** `environment:` is the only hook the workflow needs. GitHub
resolves the named environment when the job is created, applies whatever
protection rules it carries, and only then assigns a runner. The wait timer is
deliberately not expressible in YAML — if it were, anyone who could push a
commit could shorten it, which would make it worthless as a control.

**Verify the failure mode the lab asks for.** Watch the run graph rather than
the log. `deploy-staging` sits in *waiting* for a minute with no steps listed at
all — the step list does not exist yet. When it releases, the timestamp printed
by the first step is roughly a minute after the run's own start time. Now delete
the `environment:` block and re-run: the job starts immediately, because with no
environment declared there is no rule to apply. The pause comes from the
environment, not from the workflow file.

**Common wrong answer.** Trying to express the delay in the workflow, usually as
a `sleep 60` step or an invented `environment.wait-timer:` key. The `sleep`
version burns a billed minute (Module 26) and pauses *inside* the job, after
checkout and after secrets have been made available — so it delays the
deployment without gating anything. The invented key is rejected as an
unexpected value under `environment`.

</details>

## Lab 2 — Intermediate

**Task:** Create a `production` environment with yourself as a required
reviewer and an environment secret. Prove a job without `environment: production`
reads the secret as empty.

<details>
<summary>Show solution</summary>

Configuration first: **Settings → Environments → production**, add yourself
under **Required reviewers**, then add an **environment secret** named
`DEPLOY_TOKEN` with any placeholder value. Do *not* also create a repository
secret of that name — the whole point is that the name resolves only inside the
environment.

```yaml
name: Environment Secret Scope Proof

on: workflow_dispatch

permissions:
  contents: read

jobs:
  # Declares the environment. Pauses for approval, then reads the secret.
  scoped:
    name: With environment
    runs-on: ubuntu-latest
    timeout-minutes: 10
    environment: production
    steps:
      - name: Report secret length
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        # Never echo the value itself. A length is enough to prove resolution
        # and cannot leak the credential.
        run: |
          echo "characters resolved: ${#DEPLOY_TOKEN}"
          if [ -z "$DEPLOY_TOKEN" ]; then
            echo "::error::expected a value here"
            exit 1
          fi

  # No environment. Same expression, same repository, empty string.
  unscoped:
    name: Without environment
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Report secret length
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: |
          echo "characters resolved: ${#DEPLOY_TOKEN}"
          if [ -n "$DEPLOY_TOKEN" ]; then
            echo "::error::this job should not be able to read the secret"
            exit 1
          fi
          echo "Empty, as expected: the secret is scoped to the environment."
```

**Why this works.** `secrets.<NAME>` is resolved against the union of
organisation and repository secrets plus — and only if the job declares one —
the environment's secrets. `unscoped` has no environment in that union, so the
name matches nothing. Printing `${#DEPLOY_TOKEN}` rather than the value itself
gives you the proof without putting the credential in a log where masking is
your only defence.

**Verify the failure mode the lab asks for.** `unscoped` prints
`characters resolved: 0` and passes, while `scoped` waits for your approval and
then prints a non-zero length. The important detail is that `unscoped` produced
**no warning and no error** — an unresolvable secret expression becomes an empty
string, exactly like a typo'd secret name. That is why a deployment against a
missing environment secret fails deep inside a CLI with an authentication error
rather than at the point of the mistake.

Then run the same proof the wrong way round: delete the environment secret and
add `DEPLOY_TOKEN` as a **repository** secret instead. Both jobs now print a
non-zero length, and `scoped` still pauses for approval. That is question 3 made
visible — the gate now guards only timing.

**Common wrong answer.** Concluding from the empty string that the secret name
is wrong, and "fixing" it by promoting the secret to a repository secret. The
job goes green and the scoping is gone. The correct diagnosis of an empty
environment secret is always to check for a missing `environment:` declaration
first.

</details>

## Lab 3 — Challenge

**Task:** Add an always-run `gate` job that depends on two path-filtered jobs,
make it the only required check, then verify a docs-only PR passes while a
broken code PR fails.

<details>
<summary>Show solution</summary>

The filtering has to happen per job, not on `on.pull_request.paths` — a
workflow-level path filter would stop the whole workflow, `gate` included, and
you would be back to a check that never reports. Use
[`dorny/paths-filter`](https://github.com/dorny/paths-filter) or, as here, a
`changes` job that computes the filter itself so the whole mechanism is visible.

```yaml
name: Aggregated Required Check

on:
  pull_request:
  merge_group:

permissions:
  contents: read

jobs:
  changes:
    name: Detect changed areas
    runs-on: ubuntu-latest
    timeout-minutes: 5
    outputs:
      code: ${{ steps.filter.outputs.code }}
      docs: ${{ steps.filter.outputs.docs }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7
        with:
          # Need the base commit to diff against.
          fetch-depth: 0

      - name: Classify the diff
        id: filter
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
        run: |
          base="${BASE_SHA:-HEAD~1}"
          changed="$(git diff --name-only "$base" HEAD)"
          echo "$changed"
          # Outputs are STRINGS. Consumers must compare against 'true'.
          if echo "$changed" | grep -q '^your-solution-root-folder-name/'; then
            echo "code=true" >> "$GITHUB_OUTPUT"
          else
            echo "code=false" >> "$GITHUB_OUTPUT"
          fi
          if echo "$changed" | grep -q '\.md$'; then
            echo "docs=true" >> "$GITHUB_OUTPUT"
          else
            echo "docs=false" >> "$GITHUB_OUTPUT"
          fi

  lint:
    name: Lint changed code
    needs: changes
    if: needs.changes.outputs.code == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python suite
        uses: ./.github/actions/setup-python-suite
        with:
          python-version: "3.13"
          working-directory: your-solution-root-folder-name
          extra-packages: pylint

      - name: pylint
        working-directory: your-solution-root-folder-name
        run: pylint features steps

  test:
    name: Behave smoke suite
    needs: changes
    if: needs.changes.outputs.code == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python suite
        uses: ./.github/actions/setup-python-suite
        with:
          python-version: "3.13"
          working-directory: your-solution-root-folder-name
          extra-packages: allure-behave

      - name: Run smoke suite
        working-directory: your-solution-root-folder-name
        run: behave --tags=smoke -f allure_behave.formatter:AllureFormatter -o allure-results

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results-smoke
          path: your-solution-root-folder-name/allure-results
          retention-days: 7

  # THE ONLY REQUIRED STATUS CHECK.
  #
  # `if: always()` is load-bearing: without it this job would be skipped
  # whenever `lint` or `test` failed, and a skipped required check does not
  # block a merge -- so the gate would pass on exactly the pull requests it
  # exists to stop.
  gate:
    name: PR gate
    if: always()
    needs: [changes, lint, test]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Verify upstream results
        run: |
          failed=0
          for job in changes lint test; do
            case "$job" in
              changes) result="${{ needs.changes.result }}" ;;
              lint)    result="${{ needs.lint.result }}" ;;
              test)    result="${{ needs.test.result }}" ;;
            esac
            echo "${job}: ${result}"
            case "$result" in
              # `skipped` is acceptable ONLY because these jobs are skipped by
              # a deliberate path filter. Never blanket-allow it on a job that
              # has no `if:`.
              success|skipped) ;;
              *) echo "::error::${job} concluded '${result}'"; failed=1 ;;
            esac
          done
          [ "$failed" -eq 0 ]

      - name: Summarise
        if: always()
        run: |
          {
            echo "## PR gate"
            echo
            echo "| Job | Result |"
            echo "| --- | --- |"
            echo "| changes | ${{ needs.changes.result }} |"
            echo "| lint | ${{ needs.lint.result }} |"
            echo "| test | ${{ needs.test.result }} |"
          } >> "$GITHUB_STEP_SUMMARY"
```

Then in **Settings → Branches** (or a ruleset), require exactly one check:
`PR gate`. Not `lint`, not `test`, not `Detect changed areas`.

The explanation the lab asks for, recorded next to the rule:

```yaml
      # Requiring `lint` and `test` directly does not work, for two independent
      # reasons.
      #
      # 1. They are path-filtered. On a docs-only PR each reports `skipped`,
      #    and a skipped required check satisfies the rule -- so the rule is
      #    already unenforced on some PRs by design, and silently unenforced on
      #    any PR where the filter is subtly wrong.
      #
      # 2. A required check is matched by JOB NAME. Renaming `test` to
      #    `Behave regression suite` detaches the rule with no warning; the
      #    branch keeps merging while the settings page still claims to be
      #    protecting it.
      #
      # `PR gate` fixes both: it always reports, it asserts the upstream
      # results itself, and its name is a stable contract that inner refactors
      # cannot break.
```

**Why this works.** The gate converts N conditional checks into one
unconditional one. Skipping moves inside the workflow, where it is expressed as
data (`needs.<job>.result`) that a step can reason about, instead of being
expressed to branch protection as a conclusion it interprets generously. And
because the required check's name is now decoupled from the job doing the work,
the protection rule survives renames, splits, and matrix changes.

**Verify the failure mode the lab asks for.** Three pull requests:

1. **Docs only** — touch a `.md` file. `lint` and `test` report `skipped`,
   `gate` runs, prints `skipped` for both, and passes. Merge allowed, no test
   minutes burned.
2. **Broken code** — introduce a `pylint` violation under
   `your-solution-root-folder-name/`. `lint` fails, `gate` still *runs* because
   of `always()`, hits `failure` in the `case`, and exits non-zero. Merge
   blocked.
3. **The instructive one** — change `gate`'s condition to
   `if: needs.lint.result == 'success'` and re-push the broken-code PR. `gate`
   is now reported as `skipped`, and the PR becomes mergeable despite a failing
   `lint`. That single line is the difference between a real gate and a
   decorative one.

**Common wrong answer.** Writing the assertion as
`if: needs.lint.result == 'failure'` on a step that calls `exit 1`, with the job
itself left on `if: always()`. This is closer, but it enumerates the failure
modes instead of the success ones: `cancelled`, `timed_out`, and a future
conclusion string all fall through and the gate passes. Always allowlist
`success|skipped` and fail everything else — the unknown case must be a
failure, not a pass.

</details>

---

[Solutions Index](./README.md) | [Module 25](../modules/module-25-environments-approvals.md) | [Course Home](../README.md)
