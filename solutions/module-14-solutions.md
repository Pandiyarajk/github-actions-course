# Module 14 — Solutions

![Module](https://img.shields.io/badge/Module-14-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 14](../modules/module-14-matrix-and-reuse.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** A reusable workflow is called from a `jobs:` list: the calling job's
body is `uses:` (plus optional `with:` and `secrets:`) and nothing else. It brings
its own jobs and its own `runs-on`, so it cannot be spliced into someone else's
job. **A** and **C** describe a composite action, which *is* called from `steps:`
and *does* require `shell:` on its `run:` steps
([Module 21](../modules/module-21-composite-actions.md)). **D** is the habit
reusable workflows exist to remove — a workflow in another repository is called by
reference, `owner/repo/.github/workflows/name.yml@ref`.

**2 — B.** Secrets do not cross the caller/callee boundary implicitly, not even
within one repository, because a reusable workflow is a separate trust boundary
with its own job. With no `secrets:` block the expression resolves to the empty
string and the run continues — the classic silent failure, surfacing later as a
401 from Zephyr Scale. Fix it either explicitly or wholesale:

```yaml
jobs:
  ci:
    uses: ./.github/workflows/reusable-bdd-ci.yml
    with:
      browser: chrome
    secrets:
      ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
```

or `secrets: inherit`, which passes every secret the caller can see. `inherit` is
convenient and blunt: prefer the explicit map when the reusable workflow lives in
a repository you do not control.

**3 — B.** `fail-fast` defaults to `true`, which cancels the remaining legs as
soon as one fails. For cross-browser results you need all of them, so set
`strategy.fail-fast: false`. **A** is worse than useless here: `continue-on-error`
makes the failing job *report success*, so the pull request goes green with a
broken browser. **C** limits concurrency, not cancellation. **D** applies to a
step and does nothing about matrix-level cancellation.

**4.** Two jobs joined by a job output. The first job reads the file and emits a
JSON array as an output; the second declares `needs:` on it and wraps the output
in `fromJSON()` inside its `strategy.matrix`:

```yaml
jobs:
  discover:
    runs-on: ubuntu-latest
    outputs:
      browsers: ${{ steps.read.outputs.browsers }}
    steps:
      - uses: actions/checkout@v7
      - name: Read the browser list
        id: read
        run: |
          browsers="$(python -c 'import json;print(json.dumps(json.load(open("browsers.json"))))')"
          echo "browsers=${browsers}" >> "$GITHUB_OUTPUT"

  test:
    needs: discover
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        browser: ${{ fromJSON(needs.discover.outputs.browsers) }}
    steps:
      - run: echo "Running against ${{ matrix.browser }}"
```

Two things make or break it. The output must be **one line of valid JSON** —
`["chrome","firefox","msedge"]` — because job outputs are strings and `fromJSON`
parses the whole value. And the matrix is expanded when the job is scheduled, so
the producing job must be in `needs:`; without it the expression cannot resolve
and the matrix is empty. An empty array produces zero jobs and a green run, which
is why a discovery job should fail loudly when it finds nothing.

**5 — Reusable workflow.** The shared unit owns a `runs-on` and a
`strategy.matrix`, and a composite action can express neither: its steps are
spliced into the caller's job, so there is no runner to choose and no matrix to
declare. The limit that applies is **four levels** of `workflow_call` nesting —
the top-level caller plus three further reusable workflows. (Had the answer been
the composite action, the relevant limit would be nine composite actions deep.)

## Lab 1 — Beginner

**Task:** Create a matrix over `chrome`, `firefox`, and `msedge` so three job runs
appear.

<details>
<summary>Show solution</summary>

```yaml
name: Browser Matrix

on:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  smoke:
    name: smoke (${{ matrix.browser }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox, msedge]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Run Behave smoke suite
        working-directory: your-solution-root-folder-name
        run: behave --tags=smoke -D browser=${{ matrix.browser }}
```

**Why this works.** `strategy.matrix` is a job-level key, and each value of the
single `browser` dimension produces one independent job on its own runner. The
explicit `name:` makes the three checks read as `smoke (chrome)` and so on, which
matters once you add branch protection and have to select required checks by
name. `fail-fast: false` is included from the start because the whole reason to
fan out across browsers is to learn which ones fail.

**Verify the failure mode the lab asks for.** Rename the matrix key to `browsers`
but leave the step referencing `${{ matrix.browser }}`. You still get three jobs,
and each one runs `behave --tags=smoke -D browser=` — the expression resolves to
an empty string. Behave accepts the empty userdata value and the suite either
falls back to its default browser or fails deep inside the driver setup. Nothing
warns you that a matrix reference did not resolve.

Now make it fail the other way: write the values as a single string,
`browser: "chrome, firefox, msedge"`. One job runs, with
`matrix.browser` equal to the whole comma-separated string. A matrix dimension
must be a YAML **list**; a string is a single value, not three.

**Common wrong answer.** Nesting `strategy:` under `steps:`, or indenting it
inside the step list. `strategy` is a sibling of `runs-on` and `steps` at the job
level; anywhere else it fails workflow validation with an unexpected-key error.

</details>

## Lab 2 — Intermediate

**Task:** Add `server1` and `server2` as a second dimension so six job runs
appear.

<details>
<summary>Show solution</summary>

```yaml
name: Browser x Server Matrix

on:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  smoke:
    name: ${{ matrix.browser }} on ${{ matrix.server }}
    runs-on: ${{ matrix.server }}
    strategy:
      fail-fast: false
      matrix:
        server: [server1, server2]
        browser: [chrome, firefox, msedge]
        # msedge is not provisioned on server2 -- drop that one leg rather than
        # shrinking either dimension.
        exclude:
          - server: server2
            browser: msedge
        # ... and add one leg that is not part of the cross product at all.
        include:
          - server: server1
            browser: chrome
            tags: smoke-and-regression
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Run Behave
        working-directory: your-solution-root-folder-name
        run: behave --tags=${{ matrix.tags || 'smoke' }} -D browser=${{ matrix.browser }}

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          # Every dimension that varies must appear in the name.
          name: allure-${{ matrix.browser }}-${{ matrix.server }}
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30
```

**Why this works.** Two dimensions produce the cross product — 2 servers x 3
browsers = 6 jobs — before `exclude` removes any leg matching all of the
key/value pairs it lists, leaving five. `include` behaves differently and trips
people up: an `include` entry whose keys match an existing leg *adds* its extra
keys to that leg (here `tags` is attached to chrome-on-server1); an entry that
matches nothing is appended as a brand-new leg. `runs-on: ${{ matrix.server }}`
turns the dimension into a runner label, which is how one job definition spreads
across self-hosted machines.

**Verify the failure mode the lab asks for.** Set the artifact `name:` back to a
constant such as `allure-results`. The first leg to finish uploads successfully;
the next leg to attempt the same name fails the step, because an artifact is
sealed once created and a second upload under the same name is a conflict rather
than a merge (see [Module 10](../modules/module-10-artifacts.md)). The result is
a run where some browsers report a spurious failure that has nothing to do with
the tests.

The second failure mode is worth provoking deliberately: add `server3` to the
dimension without a self-hosted runner carrying that label. Those legs do not
error — they queue indefinitely, showing as pending until the job's timeout
expires. A matrix that references a label no runner offers looks like a hung
pipeline, not a misconfiguration, which is the argument for `timeout-minutes` on
self-hosted jobs.

**Common wrong answer.** Using `exclude` with a partial match and expecting it to
behave like a filter — `exclude: - browser: msedge` removes msedge from *every*
server, because an `exclude` entry drops each leg that matches all the keys given.
Listing one key excludes far more than intended.

</details>

## Lab 3 — Challenge

**Task:** Move the Behave and Allure logic into a reusable workflow called with
`workflow_call`, and call it from a thin caller.

<details>
<summary>Show solution</summary>

`.github/workflows/reusable-bdd-ci.yml`:

```yaml
name: Reusable BDD CI

on:
  workflow_call:
    inputs:
      browser:
        description: "Browser to drive."
        required: true
        type: string
      tags:
        description: "Behave tag expression."
        required: false
        type: string
        default: smoke
      runner:
        description: "Runner label for the test job."
        required: false
        type: string
        default: ubuntu-latest
    secrets:
      ZEPHYR_SCALE_TOKEN:
        required: false
    outputs:
      artifact-name:
        description: "Name of the uploaded Allure artifact."
        value: ${{ jobs.bdd.outputs.artifact-name }}

permissions:
  contents: read

jobs:
  bdd:
    # The reusable workflow owns its runner -- this is the capability a composite
    # action does not have.
    runs-on: ${{ inputs.runner }}
    timeout-minutes: 45
    outputs:
      artifact-name: ${{ steps.names.outputs.artifact }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Compute artifact name
        id: names
        run: echo "artifact=allure-${{ inputs.browser }}" >> "$GITHUB_OUTPUT"

      - name: Run Behave
        working-directory: your-solution-root-folder-name
        env:
          ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
        run: |
          behave --tags=${{ inputs.tags }} \
            -D browser=${{ inputs.browser }} \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: ${{ steps.names.outputs.artifact }}
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30
```

`.github/workflows/call-bdd-ci.yml`:

```yaml
name: Call Reusable BDD CI

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  smoke:
    # The caller supplies the matrix; the callee runs one leg per call.
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox, msedge]
    uses: ./.github/workflows/reusable-bdd-ci.yml
    with:
      browser: ${{ matrix.browser }}
      tags: smoke
    secrets:
      ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}

  summary:
    needs: smoke
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Report the shared workflow's result
        env:
          SMOKE_RESULT: ${{ needs.smoke.result }}
        run: |
          echo "Reusable BDD CI finished with: ${SMOKE_RESULT}"
```

**Why this works.** The division of labour is the lesson. `workflow_call` inputs
are **typed** (`string`, `boolean`, `number`, `choice`) and validated, unlike
composite-action inputs which are all strings. The callee declares which secrets
it expects, so the interface is explicit in both directions. And because the
caller may put `strategy:` on a job whose body is `uses:`, the matrix lives in the
caller while the callee stays a single-browser workflow — one dimension of
variation, expressed once.

**Verify the failure mode the lab asks for.** Add `runs-on: ubuntu-latest` next to
`uses:` in the caller's `smoke` job. The workflow fails to load before anything
runs: a job that calls a reusable workflow may only carry `uses`, `with`,
`secrets`, `needs`, `if`, `strategy`, `permissions`, and `concurrency` — `runs-on`
and `steps` are rejected, because the runner is the callee's decision. This is the
most direct way to feel the difference between the two reuse mechanisms.

Then delete the caller's `secrets:` block. The run succeeds all the way through:
`ZEPHYR_SCALE_TOKEN` is the empty string inside the callee, Behave runs, and only
the Zephyr publish rejects it. Add `secrets: inherit` and it works again — which
is exactly why `inherit` is tempting and why an explicit map is the better default.

**Common wrong answer.** Trying to call the reusable workflow from a step:

```yaml
      - name: Run shared CI
        uses: ./.github/workflows/reusable-bdd-ci.yml   # wrong
```

The runner looks for an action at that path and reports that it cannot find an
`action.yml` — a message that sends people hunting for a missing file rather than
noticing that a workflow was invoked from the wrong level. A `steps:` list takes
actions; a `jobs:` list takes workflows.

The other frequent miss is nesting depth: a caller that calls a workflow which
calls a workflow which calls a workflow is fine, but adding a fifth level exceeds
the four-level `workflow_call` limit and the run fails to start.

</details>

---

[Solutions Index](./README.md) | [Module 14](../modules/module-14-matrix-and-reuse.md) | [Course Home](../README.md)
