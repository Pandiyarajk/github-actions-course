# Module 17 — Solutions

![Module](https://img.shields.io/badge/Module-17-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 17](../modules/module-17-release-automation.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** `on:` is a map of triggers and they are additive — a workflow fires if
*any* listed event matches. `push: tags:` and `workflow_dispatch:` coexist
happily in one file:

```yaml
on:
  push:
    tags:
      - "v*"
  workflow_dispatch:
```

**A** is the classic misconception that one workflow means one trigger. **C**
invents a restriction: `workflow_dispatch` is unaffected by the presence of a tag
filter, though note the manual run still needs a ref chosen in the UI. **D** is
worse than wrong — `release: types: [published]` fires *after* a release exists,
so it cannot be the workflow that creates one, and it does not enable manual
dispatch.

**2 — B.** Releases are governed by the `contents` scope, so the token needs
`contents: write`. With `contents: read` the API call is rejected before it
reaches the release logic.

```yaml
permissions:
  contents: write
```

**A** is false: the built-in `GITHUB_TOKEN` creates releases fine once it has
`contents: write`. A PAT is only needed when the release must trigger *other*
workflows, because events raised by `GITHUB_TOKEN` do not start new workflow
runs. **C** invents a `releases:` scope — there is no such permission key. **D**
confuses two things; `deployments: write` governs deployment statuses, which a
release does not create.

**3 — A.** The gate is a job-level `environment:` whose **required reviewers**
are configured in repository settings (Settings -> Environments). The YAML only
names the environment; the human requirement lives in the settings, which is why
copying the YAML into a fresh repo produces a job that does not wait. See
[Module 25](../modules/module-25-environments-approvals.md) for the full
mechanics.

**B** invents syntax. **C** is a real feature solving a different problem —
`concurrency` serialises runs, it never pauses for a human. **D** is
security theatre: an input the triggering user types themselves is not an
approval by anybody else.

**4.** Two separate `behave` runs produce two separate result sets, so the
artifact you publish as evidence is not the run that gated the release. The
second run can pass where the first failed (or the reverse) on flaky timing, on a
different browser build, or on a changed test environment — at which point the
release record certifies something that was never actually verified. It also
doubles the runtime of the slowest part of the pipeline.

The release job should **promote the same immutable artifact**: the gate job runs
the suite once and uploads the Allure results, and the release job downloads
them with `actions/download-artifact@v8`. The gate's `needs:` relationship is
what guarantees a red suite blocks the release; the artifact is what proves which
run did the gating.

**5.** Two controls:

- **`needs:`** — the release job declares `needs: regression-gate`. A job whose
  dependency failed does not run, so a commit with a failed suite cannot reach
  the release step. (Only an explicit `if: always()` or
  `if: ${{ !cancelled() }}` on the release job would defeat this — which is why
  you never put one there.)
- **`concurrency:`** with `cancel-in-progress: false` — a concurrency group keyed
  on the ref queues the second release run behind the first instead of letting
  them interleave. Without it, two runs can race to create the same tag or the
  same Zephyr cycle, and the loser either errors or writes over the winner.

```yaml
concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false
```

`cancel-in-progress: true` would be wrong here: cancelling a half-finished
release leaves a tag with no release record.

## Lab 1 — Beginner

**Task:** Create a manual release workflow.

<details>
<summary>Show solution</summary>

`.github/workflows/manual-release.yml`:

```yaml
name: Manual Release

on:
  workflow_dispatch:
    inputs:
      version:
        description: "Version to certify, e.g. v1.4.0"
        type: string
        required: true

run-name: Release ${{ inputs.version }} from ${{ github.ref_name }}

permissions:
  contents: write

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  release:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Announce release candidate
        run: |
          echo "Certifying ${{ inputs.version }} at commit ${GITHUB_SHA}"

      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          VERSION: ${{ inputs.version }}
        run: |
          gh release create "${VERSION}" \
            --title "Release ${VERSION}" \
            --notes "Certified commit ${GITHUB_SHA}"
```

**Why this works.** `workflow_dispatch` makes the run deliberate and lets the
operator name the version instead of deriving it from a run number.
`permissions: contents: write` is what allows `gh release create` to write; the
`gh` CLI is preinstalled on GitHub-hosted runners and authenticates from
`GH_TOKEN`. The version arrives through `env:` rather than being interpolated
directly into the shell, so a value containing shell metacharacters cannot
change what the command does.

**Verify the failure mode the lab asks for.** Change the permissions block to
`contents: read` and re-run. `gh release create` exits non-zero and reports an
HTTP 403 from the releases endpoint — the token was minted with read-only
`contents`, so the request is refused. Nothing about the message mentions
`permissions:`, which is why this one is worth reproducing once. Run it a second
time with `contents: write` restored but the same version string: it now fails
because the tag already exists.

**Common wrong answer.** Adding `releases: write` to the `permissions:` block.
There is no `releases` scope; an unknown key makes the workflow invalid, so you
get a load-time error instead of the 403 you were trying to fix.

</details>

## Lab 2 — Intermediate

**Task:** Add a regression-gate job and a production environment, so the release
waits for approval.

<details>
<summary>Show solution</summary>

```yaml
name: Regression Gate and Release

on:
  push:
    tags:
      - "v*"
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  regression-gate:
    runs-on: [self-hosted, windows, server1]
    timeout-minutes: 120
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Install dependencies
        working-directory: your-solution-root-folder-name
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt
          python -m pip install behave selenium allure-behave

      - name: Run regression suite (gate)
        working-directory: your-solution-root-folder-name
        run: |
          behave --tags=regression \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results-gate
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 90

  release:
    needs: regression-gate
    runs-on: ubuntu-latest
    timeout-minutes: 15
    # The approval gate. The reviewer list lives in repository settings, NOT here.
    environment:
      name: production
      url: https://prod.your-domain.com
    permissions:
      contents: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Download the certified Allure results
        uses: actions/download-artifact@v8
        with:
          name: allure-results-gate
          path: allure-results/

      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release create "${GITHUB_REF_NAME}" \
            --title "Release ${GITHUB_REF_NAME}" \
            --notes "Regression certified on ${GITHUB_SHA}"
```

Then, in the repository: **Settings -> Environments -> New environment ->
`production`**, tick **Required reviewers**, and add the approvers.

**Why this works.** Three mechanisms stack. `needs:` makes a red suite block the
release. `environment: production` pauses the `release` job before its first step
and posts a "Review deployments" prompt. Workflow-level `permissions` stay
`contents: read` and only the `release` job elevates to `contents: write`, so the
long-running test job holds no write token. Uploading the results with
`if: always()` means a *failed* gate still leaves evidence to triage.

**Verify the failure mode the lab asks for.** Push the tag without having
configured required reviewers on the `production` environment. The release job
runs straight through with no pause — the YAML is identical, so the only thing
that made it a gate was the settings page. This is the failure people report as
"`environment:` does not work". Then add a reviewer and re-run: the job now
shows as **Waiting**, and the run stays open until someone approves or rejects
it. Rejecting it marks the run failed and the tag stays with no release attached.

**Common wrong answer.** Putting `environment:` at the *step* level, or at the
workflow level. `environment` is a job property only; a step-level key is a
load-time validation error, and there is no workflow-level equivalent. The other
frequent miss is re-running `behave` in the `release` job "to be safe", which
recreates exactly the problem quiz question 4 describes.

</details>

## Lab 3 — Challenge

**Task:** Create a Zephyr Scale test cycle and a GitHub Release after the gate,
with the release notes recording the certified commit.

<details>
<summary>Show solution</summary>

Building on Lab 2, replace the `release` job's steps. See the finished shape in
[`module-17-release-automation.yml`](../examples/module-17-release-automation.yml).

```yaml
  release:
    needs: regression-gate
    runs-on: ubuntu-latest
    timeout-minutes: 20
    environment:
      name: production
      url: https://prod.your-domain.com
    permissions:
      contents: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Download the certified Allure results
        uses: actions/download-artifact@v8
        with:
          name: allure-results-gate
          path: allure-results/

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Resolve the version being certified
        id: version
        run: |
          if [ "${GITHUB_REF_TYPE}" = "tag" ]; then
            version="${GITHUB_REF_NAME}"
          else
            version="v0.0.0-run${GITHUB_RUN_NUMBER}"
          fi
          echo "value=${version}" >> "$GITHUB_OUTPUT"

      - name: Create Zephyr Scale test cycle for the release
        env:
          ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
          JIRA_BASE_URL: ${{ secrets.JIRA_BASE_URL }}
          VERSION: ${{ steps.version.outputs.value }}
        run: |
          python -m pip install --upgrade pip
          python -m pip install zephyr-scale-test-cycle
          zephyr-scale-test-cycle create \
            --name "Regression ${VERSION}" \
            --results allure-results/

      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          VERSION: ${{ steps.version.outputs.value }}
        run: |
          {
            echo "Regression suite certified on commit ${GITHUB_SHA}."
            echo ""
            echo "- Gate run: ${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"
            echo "- Approved via the production environment."
            echo "- Zephyr Scale cycle: Regression ${VERSION}"
          } > release-notes.md

          gh release create "${VERSION}" \
            --title "Release ${VERSION}" \
            --notes-file release-notes.md
```

**Why this works.** The release record is assembled entirely from evidence the
gate produced: the downloaded Allure results feed the Zephyr cycle, and the
notes carry the certified SHA plus a link back to the gate run. Anyone auditing
the release six months later can walk from tag to run to results without
trusting anybody's memory.

Two details matter for rollback. Because the tag is created from the certified
commit, re-running the previous tag's suite is `gh workflow run` against that
ref — the tag *is* the rollback handle. And `concurrency` with
`cancel-in-progress: false` (inherited from Lab 2) is what stops two release runs
from creating the same Zephyr cycle twice.

Note the shell-variable style throughout: `${VERSION}` read from `env:` rather
than `${{ ... }}` pasted mid-script, and no expression at column 0 inside the
`run: |` block — a `${{` at column 0 would terminate the block scalar and make
the file invalid.

**Verify the failure mode the lab asks for.** Trigger the workflow twice for the
same version. The second run's `gh release create` fails because the tag already
exists; the Zephyr step, which ran *before* it, has by then already created a
duplicate cycle. That ordering is the lesson — put the irreversible external
call after the cheap, idempotent-checkable one, or make the Zephyr step check for
an existing cycle first. Separately, remove `needs: regression-gate` and force
the suite to fail: the release now publishes from an uncertified commit, which is
the exact incident the module's Common Mistakes list opens with.

**Common wrong answer.** Deriving the version from `github.run_number`. It is
monotonic but meaningless — it changes when workflows are renamed or the repo is
migrated, it carries no semantic ordering, and re-running a release produces a
*different* "version" for the same code. Derive the version from the tag
(`github.ref_name`) or from a version file in the repository, so the version and
the commit are bound to each other.

</details>

---

[Solutions Index](./README.md) | [Module 17](../modules/module-17-release-automation.md) | [Course Home](../README.md)
