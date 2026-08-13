# Module 21: Composite Actions and Custom Actions

![Module](https://img.shields.io/badge/Module-21-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20C%20Platform-bf3989?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-120%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 20](./module-20-notifications.md) | [Next: Module 22](./module-22-container-jobs.md)
> Level: **Intermediate** | Time: **120 min** | Example workflow: [`module-21-composite-actions.yml`](../examples/module-21-composite-actions.yml)
> Solutions: [`module-21-solutions.md`](../solutions/module-21-solutions.md)

## Learning Objectives

- Write a composite action with typed `inputs` and `outputs` in `action.yml`.
- Choose correctly between a composite action and a reusable workflow.
- Consume a local action with `uses: ./path`, and understand why the checkout must come first.
- Version and publish an action so consumers can pin it.

## Key Concepts

composite action, `action.yml`, `runs.using`, `inputs`, `outputs`, local action, published action, reusable workflow, `shell`

## Expected Outcome

You can extract a repeated block of steps into a composite action, call it from a workflow, and explain when a reusable workflow would have been the better tool.

## Concept Flow

```text
Repeated steps in many workflows
      |
      +--> Same STEPS inside one job?      --> Composite action  (action.yml)
      |                                          uses: ./.github/actions/<name>
      |
      +--> Whole JOBS, own runner/matrix?  --> Reusable workflow (workflow_call)
                                                 uses: ./.github/workflows/<name>.yml
```

---

## ELI5 Explanation

You keep writing the same four steps at the top of every workflow: get the code, install Python, restore the cache, install the packages. A composite action is a labelled box you put those four steps in, so every workflow can say "do the setup box" in one line. When you improve the box, every workflow improves at once.

A reusable workflow is a bigger box. It does not hold steps — it holds whole jobs, including which runner they use.

## Technical Explanation

A **composite action** is a directory containing an `action.yml` with `runs.using: composite`. Its `runs.steps` are spliced into the calling job, so they share that job's runner, filesystem, and environment. It is called from a `steps:` list with `uses:`.

A **reusable workflow** is a workflow file with an `on: workflow_call` trigger. It is called from a `jobs:` list with `uses:`, and it brings its own jobs and `runs-on`. It cannot be inserted into an existing job's step list.

That distinction drives everything else. Because a composite action lives inside someone else's job, it cannot choose a runner, cannot declare a matrix, and cannot contain `needs`. Because a reusable workflow owns its jobs, it can do all three — but it cannot be dropped in the middle of a sequence of steps.

Three rules that only apply inside `action.yml`:

- **Every `run:` step must declare `shell:`.** In a workflow the shell defaults per runner; in a composite action it is mandatory, and omitting it fails at load with a validation error.
- **Secrets are not inherited.** A composite action has no `secrets` context. Anything sensitive must arrive through `inputs:` or already be present in `env`.
- **All inputs and outputs are strings.** `default: true` is the string `"true"`. Compare with `== 'true'` rather than relying on truthiness.

Actions come in three flavours: `composite` (steps in YAML, what this module covers), `node20`/`node24` (a JavaScript entrypoint), and `docker` (a container). Composite is the right default when the logic is a sequence of shell commands and existing actions.

## Real-World Use Case

The Selenium/Behave suite is exercised by fifteen workflows — PR smoke, nightly regression, per-browser matrix, release gate. Every one of them opened with the same setup-python-plus-pip-install preamble. When the team moved to Python 3.13 they had to edit fifteen files and missed two, which silently kept testing on the old interpreter. Extracting the preamble into `.github/actions/setup-python-suite` made the next version bump a one-line change.

## When To Use

- The same sequence of steps appears in more than two workflows.
- You want to share setup logic across jobs that each need their own runner.
- You want one place to change a tool version, a cache key, or an install command.
- You are packaging a step for other repositories or the Marketplace.

## When NOT To Use

- The shared unit is a whole job with its own `runs-on`, matrix, or `needs` — use a reusable workflow.
- The steps need `secrets` directly rather than through inputs.
- The logic is used exactly once; an action adds indirection with no payoff.
- You need to fan out across a matrix from within the shared unit — a composite action has no `strategy`.

## Common Mistakes

- Omitting `shell:` on a `run:` step, which fails at load rather than at the step.
- Expecting a **local** action to work before `actions/checkout` has run. The action file is read from the runner's disk, so the checkout is what makes it exist.
- Referencing a local action with a Marketplace-style path (`uses: my-org/repo/.github/actions/x@v1`) when it lives in the current repo — local references must start with `./` and take no `@ref`.
- Using `${{ secrets.X }}` inside `action.yml`. There is no `secrets` context; pass it as an input.
- Treating `cache-hit` as a boolean. It is the string `"true"` or `"false"`.
- Putting the action in `.github/actions/` and expecting GitHub to publish it. Publishing requires `action.yml` at the **repository root**.
- Forgetting that a composite action's steps do not appear as separate entries in the Actions UI timeline — they collapse under the calling step, which is why the logging matters.

## Debugging Tips

- `uses: ./.github/actions/foo` failing with "Can't find 'action.yml'" almost always means the checkout is missing or ran after this step, not that the path is wrong.
- Add `- run: ls -R .github/actions` before the call to confirm what actually landed on the runner.
- A composite action that appears to ignore an input is usually receiving an empty string — echo the input as the first step rather than guessing.
- Set `ACTIONS_STEP_DEBUG=true` (repository variable) to see the composite action's internal step expansion in the logs.
- If the action works locally but not from another repository, check that the consuming workflow has `contents: read` on a private source repo — a local action in a *different* repo needs an explicit checkout of that repo.

## Composite Action vs Reusable Workflow

| Question | Composite action | Reusable workflow |
| --- | --- | --- |
| Declared with | `runs.using: composite` in `action.yml` | `on: workflow_call` in a workflow file |
| Called from | a `steps:` list | a `jobs:` list |
| Local reference | `uses: ./.github/actions/name` | `uses: ./.github/workflows/name.yml` |
| Chooses its own runner | No — inherits the caller's job | Yes, via its own `runs-on` |
| Can declare a matrix | No | Yes |
| Can declare `needs` | No | Yes |
| Receives secrets | Only via `inputs` | Via `secrets:` or `secrets: inherit` |
| `shell:` on `run:` steps | Required | Optional |
| Nesting depth | Actions may call actions | Max 4 levels of `workflow_call` |
| Shares a filesystem with the caller | Yes | No — separate job, separate runner |

## Minimal Workflow Example

```yaml
name: Composite Action Demo

on: workflow_dispatch

jobs:
  greet:
    runs-on: ubuntu-latest
    steps:
      # The checkout must come first: it is what puts the action file on disk.
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Run the local composite action
        uses: ./.github/actions/setup-python-suite
        with:
          python-version: "3.13"
```

With `.github/actions/setup-python-suite/action.yml`:

```yaml
name: Set up Python test suite
description: Provision Python and install suite dependencies.

inputs:
  python-version:
    description: "Python version to provision."
    required: false
    default: "3.13"

runs:
  using: composite
  steps:
    - uses: actions/setup-python@v7
      with:
        python-version: ${{ inputs.python-version }}

    - name: Install dependencies
      shell: bash          # required in a composite action, unlike in a workflow
      run: pip install -r requirements.txt
```

### YAML Explanation

- `runs.using: composite` declares this as a composite action rather than a JavaScript or Docker one.
- `inputs.python-version.default` is the string `"3.13"` — quoting matters, since `3.13` unquoted is a float and `3.10` would become `3.1`.
- `${{ inputs.python-version }}` reads the input inside the action; the caller's `with:` supplies it.
- `shell: bash` is mandatory on the `run:` step.
- `uses: ./.github/actions/setup-python-suite` is a path, not a Marketplace reference, so it carries no `@version`.

### Step-by-Step Execution

1. The workflow is dispatched manually.
2. `actions/checkout@v7` clones the repository onto the runner, including `.github/actions/`.
3. The runner reads `.github/actions/setup-python-suite/action.yml`.
4. The action's steps are spliced into the `greet` job and run in order.
5. `setup-python` provisions 3.13; the install step runs in the same workspace.
6. The Actions UI shows one step, "Run the local composite action", with the inner steps nested beneath it.

## Production Workflow Example

```yaml
name: BDD Regression

on:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  bdd:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox, msedge]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      # One line replaces the four-step preamble, in every matrix leg.
      - name: Set up Python suite
        id: setup
        uses: ./.github/actions/setup-python-suite
        with:
          python-version: "3.13"
          working-directory: your-solution-root-folder-name
          extra-packages: allure-behave

      - name: Report whether the cache helped
        # `cache-hit` is the STRING "true", so compare rather than coerce.
        if: steps.setup.outputs.cache-hit == 'true'
        run: echo "Dependencies restored from cache."

      - name: Run BDD suite on ${{ matrix.browser }}
        working-directory: your-solution-root-folder-name
        run: |
          behave --tags=regression \
            -D browser=${{ matrix.browser }} \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          # Unique per matrix leg -- artifacts are immutable from v4 onwards, so
          # two legs sharing a name is an error, not a merge. See Module 10.
          name: allure-${{ matrix.browser }}
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30
```

### YAML Explanation

- The composite action is called once per matrix leg, because it lives inside the job rather than above it.
- `id: setup` makes the action's declared `outputs` reachable as `steps.setup.outputs.*`.
- `working-directory` is passed as an input; a composite action cannot see the caller's `defaults.run.working-directory`.
- The artifact name includes `matrix.browser`, keeping each leg's upload distinct.
- Had the shared unit needed to own the matrix instead of run inside it, this would have been a reusable workflow.

### Expected Output

- Three jobs, one per browser, each showing a collapsed "Set up Python suite" step.
- The job summary lists the resolved Python version and whether the cache was restored.
- On a second run against an unchanged requirements file, the cache-hit step runs and install time drops noticeably.
- Three distinct artifacts: `allure-chrome`, `allure-firefox`, `allure-msedge`.

## Quiz

1. A composite action needs to run its steps on a Windows self-hosted runner while the calling job runs on `ubuntu-latest`. How do you configure that?
   - **A.** Add `runs-on: self-hosted` to the action's `runs:` block.
   - **B.** Pass the runner label as an input.
   - **C.** You cannot — a composite action always runs on the caller's runner. Use a reusable workflow.
   - **D.** Set `runs.using: composite-windows`.

2. Why does `uses: ./.github/actions/my-action` fail if it is the first step in a job?
   - **A.** Local actions must be referenced with an `@ref`.
   - **B.** The repository has not been checked out, so the action file does not exist on the runner.
   - **C.** Local actions are only allowed in reusable workflows.
   - **D.** `.github/actions/` is reserved by GitHub.

3. Which of these is **required** in a composite action but optional in a workflow?
   - **A.** `permissions:` on each step.
   - **B.** `shell:` on each `run:` step.
   - **C.** `timeout-minutes` on each step.
   - **D.** An `id:` on each step.

4. An action declares `outputs.cache-hit`. A caller writes `if: steps.setup.outputs.cache-hit`. The step runs even when nothing was cached. Explain why, and give the correct condition.

5. Your team wants to share a five-job release pipeline (build, scan, stage, approve, deploy) across four repositories. Composite action or reusable workflow? Justify the choice in one sentence.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Create `.github/actions/hello/action.yml` as a composite action taking a `name` input, and call it from a `workflow_dispatch` workflow. | The log prints the greeting; removing `shell:` reproduces the load-time validation error. |
| Intermediate | Extend the action with an output that reports the resolved Python version, and have the calling workflow print it via `steps.<id>.outputs`. | The workflow prints the exact version; omitting `id:` makes the output unreachable. |
| Challenge | Take the preamble from any two existing example workflows in `examples/`, extract it into one composite action, and convert both workflows to use it. Then explain in a comment why the same extraction could not have been a reusable workflow. | Both workflows behave identically to before, with the duplicated steps gone and the reasoning recorded. |

Solutions: [`solutions/module-21-solutions.md`](../solutions/module-21-solutions.md)

---

[Previous: Module 20](./module-20-notifications.md) | [Module Index](./README.md) | [Next: Module 22](./module-22-container-jobs.md)
