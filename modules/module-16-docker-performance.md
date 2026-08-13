# Module 16: Docker, Artifacts, Caching, and Performance

![Module](https://img.shields.io/badge/Module-16-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20B%20Applied-8957e5?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-150%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 15](./module-15-multi-language-tests.md) | [Next: Module 17](./module-17-release-automation.md)
> Level: **Intermediate** | Time: **150 min** | Example workflow: [`module-16-docker-performance.yml`](../examples/module-16-docker-performance.yml)
> Solutions: [`module-16-solutions.md`](../solutions/module-16-solutions.md)

## Learning Objectives

- Run a Selenium Grid with Docker Compose in Actions.
- Use artifacts and pip cache intentionally.
- Optimize slow Behave runs without hiding failures.

## Key Concepts

Docker Compose, Selenium Grid (hub + browser nodes), pip dependency cache, Allure artifacts, timeouts

## Expected Outcome

You can spin up a browser grid, run Behave tests against it, preserve useful outputs, and reduce workflow runtime.

## Concept Flow

```text
Source Code -> docker compose up (hub + chrome/firefox nodes) -> pip cache -> behave against grid hub -> Allure results / screenshots artifact
```

---

## ELI5 Explanation

Docker Compose packages a Selenium Grid into boxes that run the same way everywhere: a hub plus browser nodes. Artifacts are files saved from a workflow, like Allure results and screenshots. Cache is a shortcut that saves downloaded pip packages so future runs are faster.

## Technical Explanation

Docker Compose workflows start a Selenium Grid (a `selenium/hub` container plus `chrome`/`firefox` node containers), run Behave tests against the grid hub URL, and tear the grid down afterwards. Artifacts preserve outputs like Allure results, screenshots, and logs. Caching reduces runtime by restoring pip packages keyed on `requirements.txt`. Performance optimization includes dependency caching, parallel browser nodes, selective triggers, and avoiding unnecessary work.

## Real-World Use Case

In a real-world web automation suite, the daily smoke suite runs Selenium + Behave against a Selenium Grid so chrome and firefox checks execute in parallel on GitHub-hosted runners, and page-load timing data (`page_load_times`) is captured for every run.

## When To Use

- Your web tests need consistent, isolated browser environments.
- You want chrome/firefox/msedge running in parallel grid nodes.
- You want to capture Allure results and screenshots as artifacts.
- Dependency installation is slow and cache keys can use `requirements.txt`.

## When NOT To Use

- TestComplete regression on Windows self-hosted runners (server1..server4), where the desktop tooling is not containerized.
- A single local browser run is enough.
- Dependencies change so often that cache hit rate is poor.
- Cache restore risks stale state.

## Common Mistakes

- Running Behave before the grid hub reports ready.
- Not using `requirements.txt` in cache keys.
- Uploading huge artifacts unnecessarily.
- Forgetting to tear the grid down, leaking containers between runs.

## Debugging Tips

- Use `docker compose logs selenium-hub` to inspect node registration.
- Print pip cache hit status.
- Keep Allure results small and named clearly.
- Use `timeout-minutes` for expensive jobs.

## Minimal Workflow Example

```yaml
name: Selenium Grid Smoke

on: push

jobs:
  behave:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v7
      - name: Start Selenium Grid
        run: docker compose -f your-solution-root-folder-name/docker-compose.yml up -d
      - name: Run Behave against grid
        run: behave -D remote_url=http://localhost:4444/wd/hub
```

### YAML Explanation

- The workflow runs on every push.
- `checkout` downloads the docker-compose file and Behave features.
- `docker compose up` starts the Selenium Grid hub and browser nodes.
- `behave` runs the BDD suite against the grid hub URL.

### Step-by-Step Execution

1. Push triggers workflow.
2. Runner checks out code.
3. Docker Compose starts the Selenium Grid.
4. Behave runs against the grid hub.

## Production Workflow Example

```yaml
name: Web Smoke (Selenium Grid)

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7
      - name: Setup Python
        uses: actions/setup-python@v7
        with:
          python-version: '3.13'
      - name: Cache pip packages
        uses: actions/cache@v6
        with:
          path: ~/.cache/pip
          key: pip-${{ runner.os }}-${{ hashFiles('your-solution-root-folder-name/requirements.txt') }}
          restore-keys: |
            pip-${{ runner.os }}-
      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt
      - name: Start Selenium Grid (hub + chrome/firefox nodes)
        run: docker compose -f your-solution-root-folder-name/docker-compose.yml up -d
      - name: Wait for grid hub to be ready
        run: |
          for i in $(seq 1 30); do
            if curl -sSf http://localhost:4444/wd/hub/status | grep -q '"ready": true'; then
              echo "Grid ready"; exit 0
            fi
            sleep 2
          done
          echo "Grid did not become ready"; docker compose logs selenium-hub; exit 1
      - name: Run Behave against the grid
        run: |
          behave \
            -D remote_url=http://localhost:4444/wd/hub \
            -D base_url=https://your-domain.com \
            -f allure_behave.formatter:AllureFormatter -o allure-results
      - name: Upload Allure results and screenshots
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results
          path: |
            allure-results/
            screenshots/
      - name: Tear down Selenium Grid
        if: always()
        run: docker compose -f your-solution-root-folder-name/docker-compose.yml down -v
```

### YAML Explanation

- Pull requests and pushes to `main` both run the smoke suite.
- `actions/cache@v6` restores pip packages keyed on `requirements.txt`.
- Parallel chrome/firefox grid nodes speed up the Behave run.
- The grid is torn down with `if: always()` so containers never leak.

### Expected Output

- Behave runs against the grid hub on both PRs and main.
- Allure results and screenshots are uploaded even when tests fail.
- pip caching and parallel browser nodes improve future run speed.

## Quiz

1. A step guarded with `if: steps.pip-cache.outputs.cache-hit` runs on every run, including cache misses. Why?
   - **A.** `cache-hit` is only set on self-hosted runners.
   - **B.** `cache-hit` is the string `"true"` or `"false"`, and a non-empty string is truthy — compare with `== 'true'`.
   - **C.** The condition needs to be wrapped in `success()`.
   - **D.** The step `id` must match the action name for outputs to resolve.

2. A cache key is written as `key: pip-${{ runner.os }}`, with no `hashFiles(...)` component. What goes wrong?
   - **A.** The cache is never restored, because the key must include a hash.
   - **B.** The first run saves an entry and every later run restores it; because a saved entry is immutable, added or upgraded packages are never written into the cache under that key.
   - **C.** GitHub rejects the key at load time.
   - **D.** Nothing — `restore-keys` compensates for the missing hash.

3. You only need the pip download cache for a normal `setup-python` + `pip install -r requirements.txt` job. What is the simplest correct approach?
   - **A.** `actions/cache@v6` on the installed `site-packages` directory.
   - **B.** `cache: pip` on `actions/setup-python@v7`, which handles the path and the `requirements.txt` hash for you.
   - **C.** `actions/cache@v6` with a key containing the current date, so the cache refreshes daily.
   - **D.** `actions/upload-artifact@v7` on `~/.cache/pip`, downloaded again at the start of the next run.

4. Explain what `restore-keys` gives you when the primary key misses, what `cache-hit` reports in that situation, and why the combination is still worth having.

5. The nightly smoke suite takes 40 minutes. List the levers you would pull, in the order you would try them, and say what each one costs.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Start a Selenium Grid with docker compose and run one Behave scenario. | Scenario passes against the grid hub. |
| Intermediate | Cache pip and upload Allure results as artifacts. | Cache hit on rerun; artifact appears after run. |
| Challenge | Add a firefox node and run chrome/firefox in parallel, capturing `page_load_times`. | Both browsers run; timing data uploaded. |

Solutions: [`solutions/module-16-solutions.md`](../solutions/module-16-solutions.md)

---

[Previous: Module 15](./module-15-multi-language-tests.md) | [Module Index](./README.md) | [Next: Module 17](./module-17-release-automation.md)
