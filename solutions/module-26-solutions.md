# Module 26 — Solutions

![Module](https://img.shields.io/badge/Module-26-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 26](../modules/module-26-local-testing-cost.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** `actionlint` validates the workflow *schema*, the types of every
`${{ }}` expression against the real context objects, `runs-on` labels, and the
shell inside `run:` blocks via `shellcheck`. Whether a version tag is the newest
one upstream published is not in any of those categories — that answer lives on
GitHub's API, which a static linter does not consult. `actions/checkout@v3`
lints perfectly clean, and so does a pin that no longer exists at all.

**A** is the inference people actually draw, and it is the dangerous one: green
linter, therefore current versions. **C** invents a deprecation database
`actionlint` has no access to. **D** is backwards — it checks the reference you
wrote, not some other version.

**2 — B.** Twelve minutes. Billing is per-minute of runner time **rounded up per
job**, so a 15-second job bills as a full minute regardless of how many other
15-second jobs ran beside it. Twelve jobs, twelve billed minutes, for three
minutes of actual work — a 4× overhead created purely by the shape of the
workflow.

**A** is the intuitive total-work model, and it is what makes "split it into
smaller jobs for a nicer graph" quietly expensive. **C** confuses wall-clock
duration with billed minutes; parallelism shortens the wait and bills every leg.
**D** invents a free tier per job — there is a monthly free allowance on some
plans, but no per-job minimum-free rule.

**3 — C.** `act` runs Linux containers on your machine. `windows-latest` is not
something it can provide, and OIDC requires GitHub's own identity provider to
mint a token against a real run's claims — there is no run and no provider
locally. Service containers, caching, and `GITHUB_TOKEN` fall into the same
bucket: partially or wholly absent.

**A**, **B**, and **D** are precisely what `act` is good at — shell logic, step
ordering, and `env:` resolution are all local concerns, which is why `act`
answers "does my script work" well and "will this pass CI" badly.

**4.** Dependabot's `github-actions` ecosystem scans **only
`.github/workflows/`**. Everything else is invisible to it, no matter how many
`uses:` lines it contains:

- `examples/` and any other directory of illustrative workflows — the situation
  this very course is in.
- Composite and Docker actions under `.github/actions/*/action.yml`.
- Action references quoted inside documentation.
- Workflow files kept outside `.github/workflows/` for any reason.

So the absence of a PR is not evidence of currency. Dependabot is reporting
truthfully about the one directory it looked at.

There is a second, subtler cause worth ruling out: the reference may be a pin
that no longer *resolves*. A tag that was deleted, or an upstream that changed
its tagging scheme, gives Dependabot no successor version to compute an update
from, so it stays quiet while the reference is already broken.

To catch it, own the check yourself rather than delegating it. Extend
`directories:` so Dependabot at least sees the other trees:

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directories:
      - "/"
      - "/examples"
    schedule:
      interval: weekly
    groups:
      # A patch bump is a rubber stamp; a major needs release notes read.
      actions-minor-patch:
        patterns: ["*"]
        update-types: ["minor", "patch"]
```

and then enforce the versions you have decided on with a check that reads
*every* file, including markdown, on every push:

```yaml
      - name: Enforce pinned action versions
        run: python scripts/validate_course.py --check pins --check mutable
```

That is exactly what [`scripts/validate_course.py`](../scripts/validate_course.py)
does in this repository, and why a stale reference in a module's prose fails CI
here. The `action-version-review` skill covers verifying each version against
upstream releases rather than from memory.

**5.** The two highest-value changes, in order of effect:

1. **Move the suite off `windows-latest`.** Windows bills at **2×** the Linux
   rate for identical wall-clock time; macOS is **10×**. A 3 × 4 matrix is
   twelve billed jobs, so the multiplier applies twelve times over. If the
   Selenium suite genuinely needs Windows-only browsers, the alternative is a
   self-hosted Windows runner, which consumes **no billed minutes** at all.
2. **Set a realistic `timeout-minutes` on every job.** The default job timeout
   is **360 minutes**. One hung browser session therefore bills six hours — and
   at the Windows 2× rate across a matrix leg, a single hang can cost more than
   a month of healthy runs.

**The `timeout-minutes` change is the one that is safe to apply without
changing coverage.** It cannot alter what the tests exercise; it only bounds the
pathological case. Choose the value from observed durations with real headroom
(a suite that normally takes 22 minutes gets `timeout-minutes: 45`, not `25`) —
a timeout that fires on a healthy run is worse than no timeout, because it
converts a slow run into a red build.

The runner change is *not* automatically safe: browser availability, driver
behaviour, and font or display rendering differ, so it needs a verification run
before it is trusted. Two further levers worth adding while you are in the file:
`concurrency` with `cancel-in-progress: true` to stop paying for superseded runs,
and a lower artifact `retention-days` — the default is 90 days, and storage is
billed separately from minutes.

## Lab 1 — Beginner

**Task:** Install `actionlint` locally and run it over `examples/`. Introduce a
typo like `github.evnt.ref` and confirm it is caught.

<details>
<summary>Show solution</summary>

Local install, pinned — an unpinned linter can turn a green branch red with no
change of yours:

```bash
# Linux / macOS / Git Bash on Windows
VERSION="1.7.12"
curl -fsSL "https://github.com/rhysd/actionlint/releases/download/v${VERSION}/actionlint_${VERSION}_linux_amd64.tar.gz" \
  -o actionlint.tar.gz
tar -xzf actionlint.tar.gz actionlint
./actionlint examples/*.yml
```

The same check in CI, so nobody has to remember to run it:

```yaml
name: Lint Workflows

on:
  pull_request:
    paths:
      - ".github/**"
      - "examples/**"
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: lint-workflows-${{ github.ref }}
  cancel-in-progress: true

env:
  ACTIONLINT_VERSION: "1.7.12"

jobs:
  actionlint:
    name: actionlint
    runs-on: ubuntu-latest
    # The default is 360 minutes. A linter that runs longer than 5 is broken.
    timeout-minutes: 5
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Install actionlint
        run: |
          base="https://github.com/rhysd/actionlint/releases/download"
          asset="actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz"
          curl -fsSL "${base}/v${ACTIONLINT_VERSION}/${asset}" -o actionlint.tar.gz
          tar -xzf actionlint.tar.gz actionlint

      - name: Lint examples and workflows
        run: ./actionlint -color examples/*.yml .github/workflows/*.yml
```

**Why this works.** `actionlint` parses the workflow against the real schema and
type-checks every expression against the actual shape of the `github` context,
so `github.evnt.ref` is a type error rather than a string it cannot judge. The
version lives in `env` so a bump is a one-line, reviewable diff, and the binary
is downloaded rather than consumed as a third-party action — one less action to
pin and audit.

**Verify the failure mode the lab asks for.** Introduce the typo:

```yaml
      - name: Print the ref
        run: echo "ref is ${{ github.evnt.ref }}"
```

`actionlint` reports it as `file:line:col:` with a message naming the unavailable
property on the `github` context — and, usefully, suggests the near-miss
spelling. The column is the part to pay attention to: expression errors are
otherwise very hard to locate inside a long `run: |` block.

Then run the contrasting experiment, which is the real lesson. Change a workflow
to `actions/checkout@v3` and re-run the linter. It passes. `actionlint` has no
opinion on version currency, which is why this repository enforces versions with
a separate check:

```bash
python scripts/validate_course.py --check pins --check mutable
```

**Common wrong answer.** Reaching for `yamllint` alone. `yamllint` is worth
running — it catches indentation and duplicate keys — but `github.evnt.ref` is
perfectly valid YAML, so it passes silently. The two tools do not overlap:
`yamllint` judges the document, `actionlint` judges the workflow.

</details>

## Lab 2 — Intermediate

**Task:** Run one job from `examples/` locally with `act`, supplying a dummy
secret via `--secret-file`. Record which parts could not be reproduced.

<details>
<summary>Show solution</summary>

Start by asking `act` what it thinks exists, before trying to run anything:

```bash
act -l -W examples/module-18-qa-automation.yml
```

Create the secret file — placeholder values only, never a real credential — and
gitignore it before you write it, not after:

```bash
printf '.secrets\n' >> .gitignore

cat > .secrets <<'EOF'
JIRA_BASE_URL=https://jira.your-domain.com
JIRA_EMAIL=qa@your-domain.com
JIRA_API_TOKEN=placeholder-not-a-real-token
EOF

act workflow_dispatch \
  -W examples/module-18-qa-automation.yml \
  -j api-health \
  --secret-file .secrets \
  --container-architecture linux/amd64      # needed on Apple silicon
```

The record the lab asks for — what did not reproduce, and why:

| Not reproduced | Cause |
| --- | --- |
| `runs-on: server4` | A self-hosted label. `act` runs Linux containers and has no such runner; the job must be re-pointed or skipped locally. |
| `GITHUB_TOKEN` | Not minted. Anything calling the API needs a PAT passed in explicitly via `--secret`. |
| Repository / environment secrets | No secret store exists locally; every value must be supplied by `--secret` or `--secret-file`. |
| Windows and macOS runners | Unsupported entirely — `act` is Linux containers only. |
| `actions/cache@v6` behaviour | Caching is not meaningfully reproduced, so cache-hit paths cannot be exercised. |
| Service containers | Partially or wholly unsupported depending on the workflow. |
| OIDC | Requires GitHub's identity provider against a real run's claims; there is nothing to issue a token against. |
| Missing tools | `act`'s runner images approximate the GitHub-hosted images. A tool present on `ubuntu-latest` may simply be absent. |
| Environment approval gates | An `environment:` with required reviewers has no local equivalent (Module 25). |

To make the run possible at all, override the runner label rather than editing
the workflow:

```bash
act workflow_dispatch \
  -W examples/module-18-qa-automation.yml \
  -j api-health \
  -P ubuntu-latest=catthehacker/ubuntu:act-latest \
  --secret-file .secrets
```

**Why this works.** `act` reads the same workflow file GitHub does and executes
each `run:` block in a container, so step ordering, `env:` resolution, working
directories, and shell logic all behave as they will in CI. That is a large
fraction of the mistakes people make, available in seconds instead of a
push-and-wait cycle. `--secret-file` fills the one gap that would otherwise stop
the job immediately.

**Verify the failure mode the lab asks for.** Run the job *without*
`--secret-file`. Every secret expression resolves to an empty string — the same
silent behaviour as a missing environment secret on real runners — so the script
fails deep inside its HTTP call with an authentication error rather than at the
point of the mistake.

Then try `-j bdd-ui`, the job that needs `server4` and a real browser. The
failure you get is about the runner or a missing tool, not about your workflow.
Recognising that class of failure is the actual skill: an `act` error mentioning
a command that exists on GitHub's runners is an image difference, and changing
the workflow to satisfy `act` would break it in CI.

**Common wrong answer.** Concluding from a green `act` run that the workflow is
correct, and from a red one that it is broken. Neither follows. `act` cannot see
the trigger's real event payload, the token's permissions, the cache, or the
runner labels, so it validates your scripts and nothing about the platform
wiring around them. The other common mistake is committing `.secrets` — write
the `.gitignore` line first.

</details>

## Lab 3 — Challenge

**Task:** Take any workflow in `examples/` and reduce its projected billed
minutes without reducing coverage. Document each change and its mechanism.

<details>
<summary>Show solution</summary>

Take the nightly regression shape from
[`module-18-qa-automation.yml`](../examples/module-18-qa-automation.yml) in its
most expensive plausible form: a 3-browser × 4-server matrix on
`windows-latest`, no timeouts, no concurrency control, no caching, 90-day
artifacts.

**Before** — count the jobs before reading further. It is twelve.

```yaml
name: Nightly Regression (before)

on:
  schedule:
    - cron: "30 1 * * *"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  regression:
    # 3 browsers x 4 servers = 12 jobs, each billed at the Windows 2x rate,
    # each rounded up to a whole minute, each free to run for the default
    # 360-minute timeout.
    runs-on: windows-latest
    strategy:
      matrix:
        browser: [chrome, firefox, msedge]
        server: [server1, server2, server3, server4]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Install BDD dependencies
        run: pip install behave selenium allure-behave pylint

      - name: Run regression suite
        run: behave --tags=regression -D browser=${{ matrix.browser }}

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: results-${{ matrix.browser }}-${{ matrix.server }}
          path: reports/
```

**After** — same twelve legs of coverage, materially cheaper:

```yaml
name: Nightly Regression (after)

on:
  schedule:
    - cron: "30 1 * * *"
  workflow_dispatch:

permissions:
  contents: read

# Lever 4: a re-dispatch while the nightly is still running cancels the older
# run instead of paying for both.
concurrency:
  group: nightly-regression-${{ github.ref }}
  cancel-in-progress: true

jobs:
  regression:
    name: ${{ matrix.browser }} on ${{ matrix.server }}
    # Lever 1: Linux is the 1x baseline. windows-latest bills the identical
    # wall-clock time at 2x, applied across all twelve legs.
    runs-on: ubuntu-latest
    # Lever 2: replaces the 360-minute default. The suite runs in ~22 minutes,
    # so 45 leaves real headroom -- a timeout that fires on a healthy run is
    # worse than no timeout.
    timeout-minutes: 45
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox, msedge]
        server: [server1, server2, server3, server4]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          # Lever 3: pip's wheel cache is restored per leg, removing a
          # dependency download from every one of the twelve jobs.
          cache: pip

      - name: Install BDD dependencies
        run: pip install behave selenium allure-behave pylint

      - name: Run regression suite
        env:
          TEST_BROWSER: ${{ matrix.browser }}
          TEST_SERVER: ${{ matrix.server }}
        run: |
          behave --tags=regression \
            -D browser="$TEST_BROWSER" \
            -D server="$TEST_SERVER" \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          # Unique per leg. Two legs uploading the same name is an error, not a
          # merge, from v4 onward.
          name: results-${{ matrix.browser }}-${{ matrix.server }}
          path: reports/
          # Lever 5: storage is billed separately from minutes and defaults to
          # 90 days. Nightly results are worthless after a week.
          retention-days: 7

  # Lever 6: one job for both linters instead of two. Each job is rounded up to
  # a whole minute, so two 20-second jobs bill two minutes and one 40-second job
  # bills one.
  static-checks:
    name: Lint and workflow checks
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install linters
        run: pip install pylint yamllint

      - name: pylint
        working-directory: your-solution-root-folder-name
        run: pylint features steps

      - name: yamllint
        run: yamllint examples
```

The documentation the lab asks for:

| # | Change | Mechanism | Coverage affected? |
| --- | --- | --- | --- |
| 1 | `windows-latest` → `ubuntu-latest` | Removes the 2× Windows multiplier from all twelve legs | Yes — needs a verification run; browser and driver behaviour differ |
| 2 | `timeout-minutes: 45` | Replaces the 360-minute default, capping a hang at 45 min instead of 6 h | No |
| 3 | `cache: pip` | Removes a dependency download from every leg | No |
| 4 | `concurrency` + `cancel-in-progress` | Stops paying for superseded runs | No |
| 5 | `retention-days: 7` | Cuts artifact storage billing (default 90) | No |
| 6 | Merge two short lint jobs into one | Removes one per-job minute rounding | No |
| — | *Rejected:* drop `msedge` | Would remove 4 of 12 legs | **Yes** — out of scope |

**Why this works.** The levers divide cleanly into two kinds. Rate levers (1)
change what a minute costs. Volume levers (2)–(6) change how many minutes and
bytes you are billed for. Only rate and volume levers preserve coverage;
narrowing the matrix is a coverage decision wearing a cost decision's clothes,
which is why it is listed as rejected rather than quietly applied.

The arithmetic, on a 22-minute suite: before, 12 legs × 22 min × 2 (Windows) =
**528 billed minutes** per night, with a worst case of 12 × 360 × 2 = 8 640
minutes if a browser hangs on every leg. After, 12 × 22 × 1 = **264 billed
minutes**, worst case 12 × 45 × 1 = 540. The routine cost halves; the tail risk
drops by a factor of sixteen.

**Verify the failure mode the lab asks for.** Set `timeout-minutes: 20` on a
suite that genuinely needs 22 and watch the nightly go red on a perfectly
healthy run. That is the failure the "safe" lever still has, and it is why the
value comes from observed durations plus headroom rather than from optimism.

Then measure instead of guessing, before and after:

```bash
gh run list --limit 50 --json name,conclusion,createdAt,updatedAt
```

Sorting real runs by duration finds the expensive job in seconds. Guessing which
job is expensive is wrong often enough to be worth not doing.

**Common wrong answer.** "Split the suite into more, smaller jobs so it
finishes faster." Wall-clock time falls and the bill rises: each job is rounded
up to a whole minute, so twelve 15-second jobs bill twelve minutes for three
minutes of work, and every extra job repeats checkout and dependency install.
The second common wrong answer is deleting a matrix dimension and calling it a
cost saving — that is a reduction in coverage, and the lab explicitly forbids it.

</details>

---

[Solutions Index](./README.md) | [Module 26](../modules/module-26-local-testing-cost.md) | [Course Home](../README.md)
