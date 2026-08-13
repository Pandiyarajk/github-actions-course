# Module 14: Matrix Builds, Marketplace Actions, and Reusable Workflows

![Module](https://img.shields.io/badge/Module-14-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20B%20Applied-8957e5?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-120%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 13](./module-13-secrets-security.md) | [Next: Module 15](./module-15-multi-language-tests.md)
> Level: **Intermediate** | Time: **120 min** | Example workflow: [`module-14-matrix-and-reuse.yml`](../examples/module-14-matrix-and-reuse.yml)
> Solutions: [`module-14-solutions.md`](../solutions/module-14-solutions.md)

## Learning Objectives

- Run matrix builds across browsers and test servers.
- Evaluate marketplace actions before adopting them.
- Create and call reusable workflows with `workflow_call`.

## Key Concepts

strategy matrix, marketplace actions, reusable workflows, composite actions

## Expected Outcome

You can scale Behave/Selenium checks across browsers and runners and reuse workflow logic cleanly.

## Concept Flow

```text
Single Job Definition -> Matrix Values -> Parallel Job Copies -> Aggregated Result

Caller Workflow -> workflow_call -> Reusable Workflow -> Shared Jobs
```

---

## ELI5 Explanation

A matrix is like asking several robots to run your Selenium tests at the same time: one driving Chrome, one driving Firefox, one driving Edge, and some running on server1 while others run on server2.

## Technical Explanation

A matrix strategy runs the same job with different combinations of variables. Marketplace actions provide reusable tasks maintained by GitHub or the community. Reusable workflows use `workflow_call` so one workflow can call another workflow, helping standardize CI across multiple test automation repositories.

## Real-World Use Case

A web automation suite must pass on Chrome, Firefox, and Edge before a release, and the regression suite must be able to fan out across self-hosted runners (server1, server2) to finish faster.

## When To Use

- Validating the same Behave suite across chrome, firefox, and msedge.
- Spreading long regression runs across server1..server4.
- Running browser or environment combinations.
- Standardizing CI or Allure report logic across repositories.

## When NOT To Use

- The combinations do not provide meaningful confidence.
- Runtime and self-hosted runner cost increase without value.
- The workflow logic is unique to one repository and easier to keep local.

## Common Mistakes

- Creating too many browser x server combinations.
- Forgetting `fail-fast: false` when you need every browser's result.
- Passing secrets incorrectly to reusable workflows.
- Using unpinned third-party actions in sensitive pipelines.

## Debugging Tips

- Print matrix values (browser, server) in logs.
- Use `strategy.fail-fast: false` for full cross-browser visibility.
- Start with a small matrix, then expand.
- Pin important actions to trusted versions or SHAs.

## Minimal Workflow Example

```yaml
name: Matrix Basics

on: push

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        browser:
          - chrome
          - firefox
          - msedge
    steps:
      - name: Show matrix value
        run: echo "Running Behave against ${{ matrix.browser }}"
```

### YAML Explanation

- `strategy.matrix` defines values that create multiple job runs.
- `browser` is a custom matrix variable.
- `${{ matrix.browser }}` reads the current job's matrix value.

### Step-by-Step Execution

1. A push triggers the workflow.
2. GitHub creates three job runs.
3. One run drives Chrome as the matrix value.
4. Another run drives Firefox, and a third drives Edge.

## Production Workflow Example

```yaml
name: Selenium BDD Matrix CI

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read

jobs:
  test:
    name: ${{ matrix.browser }} on ${{ matrix.server }}
    strategy:
      fail-fast: false
      matrix:
        server:
          - server1
          - server2
        browser:
          - chrome
          - firefox
          - msedge
    runs-on: ${{ matrix.server }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7
      - name: Setup Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - name: Cache pip
        uses: actions/cache@v6
        with:
          path: ~/.cache/pip
          key: pip-${{ hashFiles('your-solution-root-folder-name/requirements.txt') }}
      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt
      - name: Run Behave regression
        run: behave --tags=regression -D browser=${{ matrix.browser }}
        working-directory: your-solution-root-folder-name
```

### Refining a Matrix: `include` and `exclude`

The matrix above produces 2 servers × 3 browsers = 6 jobs. Two keys reshape that
product rather than replacing it, and the order they are applied is what confuses
people: **`exclude` is applied first, then `include`** — so an `include` can add
back a combination `exclude` just removed.

```yaml
    strategy:
      fail-fast: false
      matrix:
        server: [server1, server2]
        browser: [chrome, firefox, msedge]

        # Removes combinations from the product. msedge only exists on server1,
        # so the server2 leg would queue forever against a runner that cannot
        # serve it. 6 legs becomes 5.
        exclude:
          - server: server2
            browser: msedge

        # Two distinct behaviours, depending on whether the entry matches an
        # existing leg:
        include:
          # MATCHES an existing leg -> adds a variable to just that leg.
          # Does not create a new job.
          - server: server1
            browser: chrome
            tags: regression-extended

          # Matches NO existing leg -> creates one additional job. 5 becomes 6.
          - server: server3
            browser: chrome
            tags: smoke
```

`matrix.tags` is then defined on some legs and an empty string on others, which
is the usual reason a "matrix variable is empty" bug appears. Give it a default
in the step rather than assuming every leg has it:

```yaml
      - name: Run suite
        env:
          TAGS: ${{ matrix.tags || 'regression' }}
        run: |
          behave --tags="$TAGS" -D browser="${{ matrix.browser }}"
```

### Dynamic Matrix from a Job Output

A matrix does not have to be hard-coded. `fromJSON()` turns a JSON string into a
real matrix, which lets one job decide what the next one fans out over — useful
when the browser list lives in a config file, or when only changed feature areas
should be tested.

```yaml
jobs:
  discover:
    runs-on: ubuntu-latest
    outputs:
      # A job output is always a STRING. It carries JSON as text; fromJSON in
      # the consumer is what turns it back into a list.
      browsers: ${{ steps.pick.outputs.browsers }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Decide which browsers to run
        id: pick
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            browsers='["chrome"]'                        # fast PR feedback
          else
            browsers='["chrome","firefox","msedge"]'     # full nightly sweep
          fi
          echo "browsers=${browsers}" >> "$GITHUB_OUTPUT"

  test:
    needs: discover
    strategy:
      fail-fast: false
      matrix:
        browser: ${{ fromJSON(needs.discover.outputs.browsers) }}
    runs-on: ubuntu-latest
    steps:
      - name: Run suite on ${{ matrix.browser }}
        run: |
          behave --tags=regression -D browser="${{ matrix.browser }}"
```

Two failure modes worth knowing. If the output is not valid JSON, the error names
the *expression*, not the producing job, so it reads as a syntax error in the
consumer. And if the JSON array is **empty**, the `test` job is skipped entirely
rather than failing — which, if `test` is a required status check, means the gate
silently passes (see Module 25).

### YAML Explanation

- `fail-fast: false` lets all matrix jobs finish even if one browser fails.
- `matrix.server` selects which self-hosted runner (server1, server2) executes the job.
- `actions/setup-python@v7` installs Python 3.13.
- `actions/cache@v6` caches the pip download directory.

### Reusable Workflow Example

```yaml
name: Reusable BDD CI

on:
  workflow_call:
    inputs:
      browser:
        required: true
        type: string
      environment:
        required: false
        type: string
        default: qa

jobs:
  bdd-ci:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v7
      - name: Setup Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - name: Install and run Behave
        run: |
          pip install -r your-solution-root-folder-name/requirements.txt
          behave --tags=smoke -D browser=${{ inputs.browser }} -D env=${{ inputs.environment }}
        working-directory: your-solution-root-folder-name
      - name: Generate Allure report
        run: allure generate your-solution-root-folder-name/allure-results -o allure-report --clean
      - name: Upload Allure report
        uses: actions/upload-artifact@v7
        with:
          name: allure-report-${{ inputs.browser }}
          path: allure-report
```

Caller workflow:

```yaml
name: Call Reusable BDD CI

on: pull_request

jobs:
  ci:
    uses: ./.github/workflows/reusable-bdd-ci.yml
    with:
      browser: "chrome"
      environment: "qa"
```

### Expected Output

- Matrix jobs run in parallel.
- Each browser and server combination appears as a separate check.
- Reusable workflow centralizes Behave and Allure logic.

## Quiz

1. Which statement about calling a reusable workflow is correct?
   - **A.** It is called from a `steps:` list with `uses:`, like any Marketplace action.
   - **B.** It is called from a `jobs:` list with `uses:`, and it brings its own `runs-on`.
   - **C.** It can be inserted in the middle of an existing job's steps as long as `shell:` is declared.
   - **D.** It must be copied into the caller repository before it can be used.

2. A reusable workflow references `${{ secrets.ZEPHYR_SCALE_TOKEN }}`. The caller passes no `secrets:` block at all. What happens?
   - **A.** The secret is inherited automatically, because the caller and the reusable workflow are in the same repository.
   - **B.** The expression evaluates to an empty string; you must map the secret explicitly or use `secrets: inherit`.
   - **C.** The run fails at load time with a missing-secret error.
   - **D.** Secrets can never be reached inside a reusable workflow.

3. Your `chrome`, `firefox`, and `msedge` legs run in one matrix. Chrome fails early and the other two legs are cancelled before finishing. What is the correct fix if you need every browser's result?
   - **A.** Add `continue-on-error: true` to the job.
   - **B.** Add `strategy.fail-fast: false`.
   - **C.** Add `strategy.max-parallel: 3`.
   - **D.** Add `if: always()` to the Behave step.

4. You want the browser list to come from a JSON file in the repository instead of being hard-coded in `strategy.matrix`. Describe the mechanism: what the first job must produce, and how the second job consumes it.

5. Your suite already has a composite action for the Python setup preamble. Now you want to share the whole "run Behave, generate Allure, upload the report" sequence — including its own runner and browser matrix — across four repositories. Reusable workflow or composite action? Justify it, and state the nesting limit that applies to the answer you chose.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create a matrix for chrome, firefox, and msedge. | Three job runs appear. |
| Intermediate | Add server1 and server2 to the matrix. | Six job runs appear. |
| Challenge | Move the Behave/Allure logic into a reusable workflow using `workflow_call`. | Caller workflow invokes shared workflow. |

Solutions: [`solutions/module-14-solutions.md`](../solutions/module-14-solutions.md)

---

[Previous: Module 13](./module-13-secrets-security.md) | [Module Index](./README.md) | [Next: Module 15](./module-15-multi-language-tests.md)
