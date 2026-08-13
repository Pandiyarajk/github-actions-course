# Module 26: Local Testing, Linting, and Cost Control

![Module](https://img.shields.io/badge/Module-26-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20C%20Platform-bf3989?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-120%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 25](./module-25-environments-approvals.md) | [Next: Capstones](../capstones/README.md)
> Level: **Intermediate** | Time: **120 min** | Example workflow: [`module-26-local-testing-cost.yml`](../examples/module-26-local-testing-cost.yml)
> Solutions: [`module-26-solutions.md`](../solutions/module-26-solutions.md)

## Learning Objectives

- Lint workflows with `actionlint` before pushing them.
- Run a workflow locally with `act`, and know what it cannot reproduce.
- Keep action versions current with Dependabot.
- Reason about billed minutes, multipliers, and where the money actually goes.

## Key Concepts

`actionlint`, `act`, `yamllint`, Dependabot, minute multiplier, `timeout-minutes`, concurrency cancellation, `repository_dispatch`

## Expected Outcome

You can catch a broken workflow before pushing it, keep your action versions current automatically, and explain which change to a workflow would most reduce its cost.

## Concept Flow

```text
Author a workflow
      |
  actionlint + yamllint     -> schema, expressions, shell (seconds, local)
      |
  act                       -> does it actually run? (minutes, local, Linux only)
      |
  push                      -> real runners, real secrets, real cost
      |
  Dependabot                -> keeps the versions current afterwards
```

---

## ELI5 Explanation

Pushing a workflow to see if it works is the slowest possible way to find a typo. Two tools shorten the loop: one reads your workflow and tells you it is wrong without running it, and one actually runs it on your own machine. Neither is perfect, but between them most mistakes never reach GitHub.

The other half of the module is money. Every minute on a GitHub-hosted runner is billed, and some runners cost several times more per minute than others.

## Technical Explanation

### `actionlint`

`actionlint` is a static checker for workflow files. It knows the workflow schema, validates `${{ }}` expressions against the real context types, checks `runs-on` labels, and runs `shellcheck` over `run:` blocks. It catches things a YAML linter cannot: a typo'd `github.evnt.pull_request`, a `needs:` reference to a job that does not exist, a matrix variable used outside a matrix.

What it does **not** know is which action versions are current. `actions/checkout@v3` lints clean. Version currency is a separate audit — see the `action-version-review` skill.

Install it from its release binary and run it in CI:

```bash
curl -fsSL "https://github.com/rhysd/actionlint/releases/download/v1.7.12/actionlint_1.7.12_linux_amd64.tar.gz" \
  -o actionlint.tar.gz
tar -xzf actionlint.tar.gz actionlint
./actionlint .github/workflows/*.yml
```

Pin the version. An unpinned linter can turn a green branch red without any change of yours.

### `act`

`act` runs workflows locally in Docker containers. It is genuinely useful for iterating on step logic, and it is important to know its limits, because expecting parity leads to confusing results:

- **Runner images are approximations.** `act`'s images are not the GitHub-hosted images. Tools present on `ubuntu-latest` may be missing.
- **Secrets must be supplied** with `--secret` or `--secret-file`; there is no repository secret store.
- **`GITHUB_TOKEN` is not minted.** Anything calling the API needs a PAT passed in explicitly.
- **Windows and macOS runners are unsupported.** `act` is Linux containers only.
- **Service containers, caching, and OIDC** are partially or entirely unsupported.

Use it to answer "does my script work", not "will this pass CI".

```bash
act -l                                    # list jobs without running
act pull_request -j test                  # run one job for one event
act -j test --secret-file .secrets        # supply secrets
act -j test --container-architecture linux/amd64   # on Apple silicon
```

Keep `.secrets` in `.gitignore`.

### Dependabot

A `.github/dependabot.yml` with the `github-actions` ecosystem opens PRs when actions publish new versions. Two facts shape how useful it is:

- It scans **only `.github/workflows/`**. References in other directories, in composite actions under `.github/actions/`, or quoted in documentation are invisible to it. A repository that keeps example workflows elsewhere needs its own check.
- Grouping matters. A patch bump is a rubber stamp; a major needs release notes read. Grouping minor and patch together while leaving majors as individual PRs keeps the review proportionate.

### Cost

Billing is per-minute of runner time, rounded up per job, with a multiplier by runner type. Linux is the baseline; **Windows is billed at 2× and macOS at 10×** the Linux rate. Larger runners cost more again. Self-hosted runners consume no billed minutes.

Consequences worth internalising:

- **Rounding is per job, not per workflow.** Ten jobs that each take 20 seconds are billed as ten minutes, not three. Splitting work into many tiny jobs can cost far more than one job doing the same work.
- **A wide matrix multiplies everything.** A 3-browser × 4-server matrix is twelve billed jobs.
- **Moving a job from Windows to Linux halves its cost** for identical wall-clock time.
- **`timeout-minutes` is a cost control**, not just a hygiene setting. The default job timeout is 360 minutes, so one hung job can burn six hours of billed time. Set a realistic timeout on every job.
- **`concurrency` with `cancel-in-progress: true`** stops paying for superseded runs on a branch someone is pushing to repeatedly.

Storage is billed separately, which makes `retention-days` on artifacts a real lever — the default is 90 days.

### `repository_dispatch`

`GITHUB_TOKEN` pushes do not trigger workflows (Module 24), so chaining across repositories needs an explicit event. `repository_dispatch` accepts an API call carrying a `event_type` and a JSON payload:

```bash
gh api repos/<owner>/<repo>/dispatches \
  -f event_type=run-regression \
  -F 'client_payload[browser]=chrome'
```

The receiving workflow reads `github.event.client_payload.*`. Treat that payload as untrusted input, exactly like any other event data.

## Real-World Use Case

The nightly regression matrix ran 3 browsers × 4 servers on Windows self-hosted runners, and the PR smoke suite ran on `windows-latest` because it had historically been written for Windows. Moving the PR suite to `ubuntu-latest` halved its billed rate, and adding `timeout-minutes: 20` capped a recurring hung-browser failure that had twice consumed several hours of billed time before anyone noticed.

## When To Use

- `actionlint` and `yamllint`: on every workflow change, locally and in CI.
- `act`: while iterating on `run:` step logic, before the first push.
- Dependabot: on every repository with workflows.
- Cost review: when a matrix grows, when adding Windows or macOS jobs, or when the bill changes.

## When NOT To Use

- `act` for anything depending on OIDC, service containers, caching behaviour, or a Windows runner — it will mislead you.
- `act` as a substitute for CI. It proves your script runs, not that the workflow is correct.
- Dependabot alone as a version-currency guarantee if your action references live outside `.github/workflows/`.
- Aggressive `timeout-minutes` on a long regression suite — a timeout that fires on a healthy run is worse than no timeout.

## Common Mistakes

- Assuming `actionlint` passing means the action versions are current. It has no opinion on versions.
- Running an unpinned `actionlint` in CI, then being surprised when a new release fails an unchanged branch.
- Debugging an `act` failure that is really a missing tool in `act`'s runner image.
- Committing a `.secrets` file used by `act`.
- Expecting Dependabot to see `uses:` references in `examples/` or in documentation.
- Leaving the default 360-minute job timeout, so a hung job bills six hours.
- Splitting a workflow into many very short jobs without realising each is rounded up to a full minute.
- Adding a macOS job for convenience without noticing it bills at 10×.

## Debugging Tips

- `actionlint` output is `file:line:col: message`; the column matters for expression errors, which are otherwise hard to locate.
- `actionlint -shellcheck=` disables shell checking if `shellcheck` noise is drowning out schema errors while you triage.
- `act -l` confirms which jobs and events `act` believes exist; if a job is missing, the trigger is not what you think.
- "command not found" under `act` for something present on GitHub runners is an image difference, not your bug — verify on a real runner before changing the workflow.
- To find where minutes go, sort the run list by duration rather than guessing: `gh run list --limit 50 --json name,conclusion,createdAt,updatedAt`.
- Billing settings show usage by runner type; a surprising bill is usually a matrix that grew or a job that moved to Windows.

## Reference: cost levers, roughly ordered by effect

| Lever | Typical effect |
| --- | --- |
| Move a job from macOS to Linux | ~10× reduction in rate |
| Move a job from Windows to Linux | ~2× reduction in rate |
| Narrow a matrix (drop a redundant dimension) | proportional to legs removed |
| `concurrency` + `cancel-in-progress` | removes payment for superseded runs |
| Realistic `timeout-minutes` | caps the worst case, does not change the norm |
| Caching dependencies | cuts minutes per run |
| Merge several very short jobs into one | removes per-job rounding waste |
| Lower artifact `retention-days` | reduces storage billing, not minutes |

## Minimal Workflow Example

```yaml
name: Lint Workflows

on: pull_request

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    # A realistic cap. The default is 360 minutes, so a hung job otherwise
    # bills six hours.
    timeout-minutes: 5
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Install actionlint
        env:
          ACTIONLINT_VERSION: "1.7.12"
        run: |
          base="https://github.com/rhysd/actionlint/releases/download"
          asset="actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz"
          curl -fsSL "${base}/v${ACTIONLINT_VERSION}/${asset}" -o actionlint.tar.gz
          tar -xzf actionlint.tar.gz actionlint

      - name: Lint workflows
        run: ./actionlint -color .github/workflows/*.yml
```

### YAML Explanation

- `timeout-minutes: 5` bounds the cost of a hang; a linter that takes longer is broken.
- `ACTIONLINT_VERSION` is pinned in `env` so the bump is a visible one-line diff.
- The binary is downloaded rather than consumed as a third-party action, which removes an action to pin and audit.
- `-color` keeps the output readable in the Actions log.
- `permissions: contents: read` is all a linter needs.

### Step-by-Step Execution

1. A pull request touches a workflow file.
2. The runner checks out the repository.
3. The pinned `actionlint` binary is fetched and extracted.
4. Every workflow file is checked against the schema, expression types, and shellcheck.
5. Any finding fails the job with a `file:line:col` reference.

## Production Workflow Example

```yaml
name: Workflow Quality Gate

on:
  pull_request:
    paths:
      - ".github/**"
      - "examples/**"
  workflow_dispatch:
  # Lets another repository trigger this gate. GITHUB_TOKEN pushes do not start
  # workflows, so cross-repo chaining needs an explicit dispatch event.
  repository_dispatch:
    types: [validate-workflows]

permissions:
  contents: read

concurrency:
  group: workflow-quality-${{ github.ref }}
  # Stop paying for superseded runs while someone iterates on a branch.
  cancel-in-progress: true

env:
  ACTIONLINT_VERSION: "1.7.12"

jobs:
  lint:
    name: Lint ${{ matrix.target }}
    runs-on: ubuntu-latest
    timeout-minutes: 10
    strategy:
      fail-fast: false
      matrix:
        # Deliberately two legs, not one per file: each job is billed rounded up
        # to a whole minute, so a leg per file would multiply cost for no gain.
        target:
          - .github/workflows
          - examples
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python suite
        uses: ./.github/actions/setup-python-suite
        with:
          python-version: "3.13"
          extra-packages: yamllint

      - name: Install actionlint
        run: |
          base="https://github.com/rhysd/actionlint/releases/download"
          asset="actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz"
          curl -fsSL "${base}/v${ACTIONLINT_VERSION}/${asset}" -o actionlint.tar.gz
          tar -xzf actionlint.tar.gz actionlint

      - name: yamllint
        run: yamllint ${{ matrix.target }}

      - name: actionlint
        run: ./actionlint -color ${{ matrix.target }}/*.yml

      # actionlint has no opinion on whether versions are CURRENT, so the pin
      # table is enforced separately.
      - name: Enforce pinned action versions
        if: matrix.target == '.github/workflows'
        run: python scripts/validate_course.py --check pins --check mutable

  report-cost-shape:
    name: Report cost shape
    needs: lint
    if: always()
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Summarise the billing profile
        run: |
          {
            echo "## Cost shape of this run"
            echo
            echo "| Field | Value |"
            echo "| --- | --- |"
            echo "| Runner | ubuntu-latest (1x multiplier) |"
            echo "| Lint legs | 2 (each rounded up to a whole minute) |"
            echo "| Job timeout | 10 min, vs the 360 min default |"
            echo "| Superseded runs | cancelled by concurrency |"
            echo
            echo "Windows would bill this at 2x and macOS at 10x for the same"
            echo "wall-clock time."
          } >> "$GITHUB_STEP_SUMMARY"
```

### YAML Explanation

- `paths:` restricts the trigger so unrelated commits do not pay for this gate.
- `repository_dispatch.types` names the event another repository sends via `gh api .../dispatches`.
- `cancel-in-progress: true` is a cost control as much as a latency one.
- The matrix has two coarse legs rather than one per file, because per-job minute rounding punishes many short jobs.
- `timeout-minutes` on both jobs replaces the 360-minute default.
- The pin check runs only on the `.github/workflows` leg, since running it twice would duplicate work.

### Expected Output

- Two lint legs, each reporting `yamllint` and `actionlint` results independently.
- A pin-check failure names the exact `file:line` and the expected version.
- The summary job records the run's billing profile.
- Pushing twice in quick succession shows the first run cancelled rather than completing.

## Quiz

1. `actionlint` passes on a workflow using `actions/checkout@v3`. What does that tell you?
   - **A.** `v3` is the current version.
   - **B.** Nothing about currency — `actionlint` validates schema and expressions, not whether a version is current.
   - **C.** `v3` is deprecated but still supported.
   - **D.** `actionlint` only checks the newest action version.

2. A workflow is split into twelve jobs that each take about 15 seconds. How is it billed on Linux?
   - **A.** About 3 minutes, since the total work is 3 minutes.
   - **B.** 12 minutes, because each job is rounded up to a whole minute.
   - **C.** 1 minute, because the jobs run in parallel.
   - **D.** Nothing, because jobs under a minute are not billed.

3. Which of these can `act` **not** meaningfully reproduce locally?
   - **A.** A `run:` block's shell logic.
   - **B.** A job's step ordering.
   - **C.** OIDC authentication and a `windows-latest` runner.
   - **D.** Environment variables set via `env:`.

4. A repository has Dependabot configured for `github-actions`, yet a stale `uses:` reference persists for months without a PR being opened. Give the most likely reason and a way to catch it.

5. A nightly suite runs a 3-browser × 4-server matrix on `windows-latest` with no `timeout-minutes`. Name the two changes that would most reduce billed minutes, and say which is safe to apply without changing coverage.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Install `actionlint` locally and run it over `examples/`. Introduce a typo like `github.evnt.ref` and confirm it is caught. | A `file:line:col` finding for the typo, and a clean run once fixed. |
| Intermediate | Run one job from `examples/` locally with `act`, supplying a dummy secret via `--secret-file`. Record which parts could not be reproduced. | The job runs locally, plus a written list of what `act` could not do. |
| Challenge | Take any workflow in `examples/` and reduce its projected billed minutes without reducing coverage. Document each change and its mechanism. | A before/after with at least two levers applied — for example a runner change plus a realistic `timeout-minutes`. |

Solutions: [`solutions/module-26-solutions.md`](../solutions/module-26-solutions.md)

---

[Previous: Module 25](./module-25-environments-approvals.md) | [Module Index](./README.md) | [Next: Capstones](../capstones/README.md)
