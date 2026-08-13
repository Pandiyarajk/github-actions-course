# Module 16 — Solutions

![Module](https://img.shields.io/badge/Module-16-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 16](../modules/module-16-docker-performance.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** `cache-hit` is a step **output**, and every step output is a string.
A miss sets it to the string `"false"`, which is non-empty and therefore truthy in
a GitHub Actions expression, so the condition holds either way. Compare
explicitly:

```yaml
      - name: Install dependencies
        if: steps.pip-cache.outputs.cache-hit != 'true'
        run: pip install -r your-solution-root-folder-name/requirements.txt
```

**A** is wrong — the output is set on any runner. **C** and **D** are cargo cult:
`success()` is already implicit, and the `id` is arbitrary as long as the
expression uses the same one. The same trap applies to every boolean-looking
output in the course, which is why
[Module 21](../modules/module-21-composite-actions.md) repeats it for action
outputs.

**2 — B.** A cache entry is immutable once written. With a key that has no input
hash in it, the first run saves an entry under `pip-Linux` and every later run
gets an exact hit — so the post-job save step is skipped, and nothing that you
add to `requirements.txt` afterwards is ever written into the cache. Installs keep
working (pip downloads the new package each time) but the cache silently stops
paying for itself, and it will keep serving whatever mix of packages existed on
the day it was written. **A** is wrong: the cache restores perfectly, which is why
the problem is hard to spot. **C** is wrong — any string is a legal key. **D**
inverts the roles: `restore-keys` is a *fallback* for a missing exact key, not a
substitute for having one.

**3 — B.** `actions/setup-python@v7` accepts `cache: pip`, which locates the pip
cache directory for the platform, keys it on the hash of the discovered
`requirements.txt` (or use `cache-dependency-path:` to point it elsewhere), and
saves it after the job. It is one line and it cannot get the key wrong:

```yaml
      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip
          cache-dependency-path: your-solution-root-folder-name/requirements.txt
```

**A** caches the wrong thing: `site-packages` contains compiled paths and
interpreter-specific artifacts, so restoring it across runner images produces
subtly broken imports rather than a fast install. **C** is the anti-pattern from
question 2 in reverse — a date in the key guarantees a miss every day, so you pay
the save cost daily and gain almost nothing. **D** abuses artifacts as a cache;
artifacts are versioned evidence with a retention policy and a per-run identity,
and they are not restorable by key.

**4.** When the primary key misses, the action walks `restore-keys` in order and
restores the most recent entry whose key *starts with* one of those prefixes. So
`restore-keys: pip-Linux-` will restore yesterday's dependency set even though
`requirements.txt` changed today. That is a partial hit, not a hit: **`cache-hit`
is `"false"`**, because it reports only whether the exact primary key matched.
(`actions/cache/restore` additionally exposes `cache-matched-key` if you need to
know *what* was restored.)

It is still worth having, for two reasons. The restored directory is a warm
starting point — pip only downloads the packages that actually changed instead of
the whole tree, so a one-package bump costs seconds rather than a full install.
And because `cache-hit` is `"false"`, the post-job step still saves a **new**
entry under today's primary key, so the cache moves forward. Exact-hit-only
caching, by contrast, never updates (question 2). The pairing gives you
incremental warmth plus a self-refreshing cache.

**5.** In the order I would try them, cheapest and safest first:

1. **Dependency caching** (`cache: pip`). Minutes saved on every job, no
   behavioural change. Cost: nearly zero; the only risk is a stale cache when the
   key is wrong.
2. **Path filters and `concurrency` with `cancel-in-progress`**. Do not run the
   suite at all for documentation-only changes, and do not keep a superseded run
   alive when a new commit lands. Cost: a path filter can skip a run you needed,
   and a skipped required check blocks a merge until you account for it.
3. **Split the suite across a matrix** — by browser, by tag group, or by feature
   shard. This is the big lever: wall-clock time falls roughly linearly with the
   number of legs. Cost: total *billed* minutes go up, not down, and the results
   arrive as N artifacts that a later job must merge.
4. **Move the slowest layer out of the pull-request path** into a nightly
   scheduled run, keeping a tagged `@smoke` subset on the PR. Cost: real —
   regressions in the excluded scenarios are found the next morning, not at review
   time. This is a deliberate trade, not an optimisation.
5. **`timeout-minutes` on every job.** This saves nothing on a healthy run; it
   caps the damage of a hung Selenium session or a runner label no machine
   answers. Cost: a legitimately slow run gets killed, which is the point.

Two levers that look attractive and are not: `continue-on-error` (it buys time by
discarding signal — see
[Module 15](../modules/module-15-multi-language-tests.md)), and pre-baking the
whole suite into a container image to skip installs. The second can be right, but
the image itself now needs building and publishing, which is its own pipeline —
see [Module 22](../modules/module-22-container-jobs.md) for running a job inside a
container and [Module 23](../modules/module-23-docker-publish.md) for building and
pushing the image.

## Lab 1 — Beginner

**Task:** Start a Selenium Grid with Docker Compose and run one Behave scenario
against it.

<details>
<summary>Show solution</summary>

```yaml
name: Grid Smoke

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip
          cache-dependency-path: your-solution-root-folder-name/requirements.txt

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Start Selenium Grid
        run: docker compose -f your-solution-root-folder-name/docker-compose-grid.yml up -d

      - name: Wait for the grid to report ready
        run: |
          for attempt in $(seq 1 30); do
            if curl -sSf http://localhost:4444/wd/hub/status \
              | python -c "import json,sys; sys.exit(0 if json.load(sys.stdin)['value']['ready'] else 1)"; then
              echo "Grid ready after ${attempt} attempt(s)"
              exit 0
            fi
            sleep 2
          done
          echo "Grid never became ready"
          docker compose -f your-solution-root-folder-name/docker-compose-grid.yml logs
          exit 1

      - name: Run one Behave scenario against the grid
        working-directory: your-solution-root-folder-name
        run: behave features --tags=@smoke -D remote_url=http://localhost:4444/wd/hub

      - name: Tear the grid down
        if: always()
        run: docker compose -f your-solution-root-folder-name/docker-compose-grid.yml down -v
```

**Why this works.** `docker compose up -d` returns as soon as the containers are
*started*, which is not the same as the hub being *ready* — the browser nodes have
to register with it first, and that takes seconds. The readiness loop polls the
hub's status endpoint and parses `value.ready`, so the Behave step never begins
before a node can accept a session. The teardown carries `if: always()` because a
failed test must not leave containers holding the runner's ports; on a
GitHub-hosted runner the VM is discarded anyway, but on a self-hosted runner
(`server1`..`server4`) a leaked grid breaks the *next* run rather than this one.

**Verify the failure mode the lab asks for.** Delete the readiness loop and re-run.
Behave fails during driver setup while trying to create a remote session, with a
connection error against `localhost:4444` — a `WebDriverException` wrapping a
refused connection or a "no node supports the requested capabilities" response,
depending on how far the grid had got. The tell is the timing: the failure lands a
second or two into the run, long before any assertion, and re-running sometimes
passes. An intermittent failure at session creation is a readiness problem, not a
test problem.

**Common wrong answer.** Replacing the poll with `sleep 30`. It hides the problem
on a good day and reintroduces it on a loaded runner, while adding 30 seconds to
every fast run. A fixed sleep is both too long and too short — poll a condition
instead.

</details>

## Lab 2 — Intermediate

**Task:** Cache pip and upload the Allure results, so a rerun shows a cache hit
and the artifact appears after the run.

<details>
<summary>Show solution</summary>

Two ways to do it. The built-in is what you should ship:

```yaml
      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip
          cache-dependency-path: your-solution-root-folder-name/requirements.txt
```

The explicit form is what the lab asks you to build, because it makes the key and
the hit/miss reporting visible:

```yaml
name: Cached Grid Smoke

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Restore the pip cache
        id: pip-cache
        uses: actions/cache@v6
        with:
          path: ~/.cache/pip
          # The hash is what makes the key change when the inputs change.
          key: pip-${{ runner.os }}-py313-${{ hashFiles('your-solution-root-folder-name/requirements.txt') }}
          # Fallback: a warm, slightly stale cache still beats a cold one.
          restore-keys: |
            pip-${{ runner.os }}-py313-
            pip-${{ runner.os }}-

      - name: Report the cache outcome
        env:
          CACHE_HIT: ${{ steps.pip-cache.outputs.cache-hit }}
        run: |
          if [ "${CACHE_HIT}" = "true" ]; then
            echo "Exact cache hit - dependencies were fully restored."
          else
            echo "No exact hit (cache-hit=${CACHE_HIT:-unset}); pip will fetch what is missing."
          fi

      - name: Install dependencies
        # Always run: a partial restore still needs pip to reconcile the tree.
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Run Behave
        working-directory: your-solution-root-folder-name
        run: |
          behave features --tags=@smoke \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30
          if-no-files-found: error
```

**Why this works.** The key has three parts and each earns its place:
`runner.os` because a Linux wheel cache is useless on Windows, `py313` because
wheels are interpreter-specific, and `hashFiles(...)` because that is what makes a
changed dependency produce a *new* key and therefore a new saved entry. `path:`
points at pip's **download** cache, not the installed packages — restoring
downloads is safe across environments in a way that restoring `site-packages` is
not. The install step runs unconditionally: with a warm cache it resolves almost
entirely from disk, and skipping it on a hit would break the moment a restore-key
fallback served a partial tree.

**Verify the failure mode the lab asks for.** Guard the install step with
`if: steps.pip-cache.outputs.cache-hit`, then push a run with an empty cache. The
step is skipped even though nothing was restored, because `"false"` is a non-empty
string and therefore truthy. Behave then fails with `behave: command not found` —
a missing-dependency error whose actual cause is an expression that never
evaluates false. Change it to `!= 'true'` and it behaves.

Then confirm the hit/miss cycle end to end. Run once: "No exact hit". Re-run with
`requirements.txt` unchanged: "Exact cache hit", and the post-job save is skipped
because the entry already exists. Now add one package to `requirements.txt` and
run again: the primary key misses, `restore-keys` restores the previous entry,
`cache-hit` is `"false"`, pip downloads only the new package, and a fresh entry is
saved under the new key. That third run is the one that proves your key is right.

**Common wrong answer.** Caching the virtual environment or `site-packages`
directly for speed. It appears to work — until the runner image updates its patch
version of Python, at which point the restored packages point at an interpreter
path that no longer exists and imports fail with errors that have nothing to do
with your change. Cache downloads; let pip do the installing.

</details>

## Lab 3 — Challenge

**Task:** Add a firefox node, run chrome and firefox in parallel, and capture
`page_load_times`.

<details>
<summary>Show solution</summary>

```yaml
name: Parallel Grid Smoke

on:
  schedule:
    - cron: "0 2 * * 1-5"
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: grid-smoke-${{ github.ref }}
  cancel-in-progress: true

jobs:
  smoke:
    name: smoke (${{ matrix.browser }})
    runs-on: ubuntu-latest
    timeout-minutes: 45
    strategy:
      # Every browser's timing data is wanted, including the browsers that failed.
      fail-fast: false
      matrix:
        browser: [chrome, firefox]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip
          cache-dependency-path: your-solution-root-folder-name/requirements.txt

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Start the grid node for this leg
        # Each matrix leg is a separate runner, so it starts only the node it needs
        # rather than the whole grid.
        run: |
          docker compose -f your-solution-root-folder-name/docker-compose-grid.yml \
            up -d selenium-hub "${MATRIX_BROWSER}"
        env:
          MATRIX_BROWSER: ${{ matrix.browser }}

      - name: Wait for a node to register
        run: |
          for attempt in $(seq 1 30); do
            if curl -sSf http://localhost:4444/wd/hub/status \
              | python -c "import json,sys; sys.exit(0 if json.load(sys.stdin)['value']['ready'] else 1)"; then
              echo "Grid ready after ${attempt} attempt(s)"
              exit 0
            fi
            sleep 2
          done
          echo "Grid never became ready"
          docker compose -f your-solution-root-folder-name/docker-compose-grid.yml logs
          exit 1

      - name: Run Behave and record page load times
        working-directory: your-solution-root-folder-name
        env:
          # The suite writes one timing row per navigation to this path.
          PAGE_LOAD_TIMES_PATH: reports/page_load_times/${{ matrix.browser }}.json
        run: |
          mkdir -p reports/page_load_times
          behave features --tags=@smoke \
            -D browser=${{ matrix.browser }} \
            -D remote_url=http://localhost:4444/wd/hub \
            -D base_url=https://your-domain.com \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Upload evidence for this leg
        if: always()
        uses: actions/upload-artifact@v7
        with:
          # One name per leg. Two legs cannot share an artifact name.
          name: grid-evidence-${{ matrix.browser }}
          path: |
            your-solution-root-folder-name/reports/allure-results/
            your-solution-root-folder-name/reports/page_load_times/
            your-solution-root-folder-name/screenshots/
          retention-days: 30

      - name: Tear the node down
        if: always()
        run: docker compose -f your-solution-root-folder-name/docker-compose-grid.yml down -v

  timings:
    needs: smoke
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Collect both legs
        uses: actions/download-artifact@v8
        with:
          pattern: grid-evidence-*
          merge-multiple: true
          path: evidence

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Summarise page load times
        run: |
          python - <<'PY' >> "$GITHUB_STEP_SUMMARY"
          import json, pathlib, statistics
          root = pathlib.Path("evidence/page_load_times")
          print("## Page load times (seconds)\n")
          print("| Browser | Samples | Median | Slowest |")
          print("| --- | --- | --- | --- |")
          for path in sorted(root.glob("*.json")):
              samples = [float(row["seconds"]) for row in json.loads(path.read_text())]
              if not samples:
                  continue
              print(
                  f"| {path.stem} | {len(samples)} |"
                  f" {statistics.median(samples):.2f} | {max(samples):.2f} |"
              )
          PY

      - name: Publish the merged evidence
        uses: actions/upload-artifact@v7
        with:
          name: grid-evidence-merged
          path: evidence/
          retention-days: 30
```

**Why this works.** There are two ways to parallelise a grid run, and this picks
the one that scales. Running both browsers on *one* runner against a two-node grid
shares CPU, memory, and a single Docker daemon, so the two suites contend and the
timing data is polluted by the contention. A matrix gives each browser its own
runner and its own single-node grid, so wall-clock time is set by the slower
browser rather than by their sum, and `page_load_times` measures the page instead
of measuring the neighbour. `fail-fast: false` matters more here than usual: the
run whose timings you most want to see is often the one that timed out.

The timing hand-off is artifact-based because the legs share no filesystem. Each
leg writes a per-browser filename, so `merge-multiple: true` can flatten both into
one directory without collision, and the `timings` job renders a table into
`$GITHUB_STEP_SUMMARY` — visible on the run page itself rather than requiring an
artifact download.

**Verify the failure mode the lab asks for.** Have both legs write
`page_load_times.json` instead of `${{ matrix.browser }}.json`, and give both
uploads the same artifact `name:`. Two distinct failures appear, and they are worth
separating. The upload collision fails the step outright, because an artifact name
is claimed exclusively once its upload completes — the second leg cannot append to
it (see [Module 10](../modules/module-10-artifacts.md)). Keep unique artifact names
but leave the *filename* shared, and nothing fails at all:
`merge-multiple: true` flattens both artifacts into one directory, one
`page_load_times.json` overwrites the other, and the summary table silently reports
a single browser. A green run with half the data missing is the more dangerous of
the two.

**Common wrong answer.** Dropping the per-leg grid and instead adding
`services:` to the job in the belief that it is the same thing. Service containers
are a real and often better answer for this shape of problem — but they are a
different mechanism with different rules about networking, readiness, and port
mapping, and the hub/node registration a Selenium Grid needs does not map onto
them one-to-one without care. Learn that mechanism properly in
[Module 22](../modules/module-22-container-jobs.md) before swapping it in; do not
assume a `services:` block is a drop-in replacement for `docker compose up`.

</details>

---

[Solutions Index](./README.md) | [Module 16](../modules/module-16-docker-performance.md) | [Course Home](../README.md)
