# Module 22: Container Jobs and Service Containers

![Module](https://img.shields.io/badge/Module-22-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20C%20Platform-bf3989?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-120%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 21](./module-21-composite-actions.md) | [Next: Module 23](./module-23-docker-publish.md)
> Level: **Intermediate** | Time: **120 min** | Example workflow: [`module-22-container-jobs.yml`](../examples/module-22-container-jobs.yml)
> Solutions: [`module-22-solutions.md`](../solutions/module-22-solutions.md)

## Learning Objectives

- Run a job's steps inside a container with `container:`.
- Attach sidecar containers with `services:` and wait for them to become healthy.
- Address a service correctly from both a container job and a runner-hosted job.
- Choose between `services:` and a Docker Compose file for a Selenium Grid.

## Key Concepts

`container:`, `services:`, sidecar, health check, `options:`, port mapping, Docker network, service hostname

## Expected Outcome

You can run a Behave suite against a Selenium Grid provided entirely by `services:`, with no manual `docker run` and no sleep-based waiting.

## Concept Flow

```text
                    Job runs ON the runner            Job runs IN a container
                    ----------------------            -----------------------
  Reach a service   localhost:<mapped host port>      <service label>:<container port>
  Needs `ports:`    YES - must map to the host        NO - same Docker network
  Runner support    Linux, Windows, macOS             Linux only
```

---

## ELI5 Explanation

A container job says "don't run my steps on the bare machine, run them inside this box that already has everything installed." A service container is a second box running alongside — a database, or a browser grid — that your steps can talk to. GitHub starts the boxes, waits until they answer, and throws them away when the job ends.

## Technical Explanation

`jobs.<id>.container` makes the runner pull an image and execute every step inside it. The workspace is bind-mounted, so `actions/checkout` output is visible, but the tools available are the image's, not the runner's. Container jobs run on **Linux runners only**.

`jobs.<id>.services` starts additional containers on a shared Docker network for the job's lifetime. GitHub waits for each service's health check before running the first step, which is what makes sleep-based waiting unnecessary.

The one thing worth memorising is **how you address a service**, because it differs by where the job runs:

- **Job in a container** — the job and the services share a Docker network, so the service is reachable at its *label* as hostname, on its *container* port: `http://selenium:4444`. No `ports:` mapping is needed.
- **Job on the runner** — the job is outside that network, so you must publish the port with `ports:` and connect via `localhost:<host port>`.

Getting this backwards is the single most common failure, and it presents as a connection-refused that looks like the service never started.

Health checks come from `options:`, passed straight to `docker create`:

```yaml
options: >-
  --health-cmd "curl -f http://localhost:4444/wd/hub/status"
  --health-interval 5s
  --health-timeout 3s
  --health-retries 10
```

Without a health check GitHub only waits for the container to *start*, not to be *ready* — which is how a suite ends up failing on the first connection while the grid is still booting.

## Real-World Use Case

The Selenium regression suite needs Chrome and Firefox nodes. Previously the workflow shelled out to `docker compose up`, then slept 30 seconds and hoped. Moving the grid into `services:` with a real health check removed the sleep, cut roughly 25 seconds per run, and turned an intermittent connection-refused into a deterministic start.

## When To Use

- The suite needs a backing service — Selenium Grid, a database, a message broker.
- You need a toolchain that the hosted runner image does not have, and installing it every run is slow.
- You want reproducible tool versions pinned by image digest rather than by whatever the runner image ships.
- You want GitHub to handle readiness waiting rather than writing retry loops.

## When NOT To Use

- You need Windows or macOS — `container:` is Linux-only.
- The service needs custom build steps or a multi-stage startup that a single image cannot express; Docker Compose is the better fit.
- Your job needs the runner's own Docker daemon for image builds — see Module 23 instead.
- The suite runs on a self-hosted runner without Docker installed.

## Common Mistakes

- Addressing a service as `localhost` from a **container** job. Inside the container, `localhost` is the container itself; use the service label.
- Addressing a service by its label from a **runner-hosted** job. There is no DNS entry for it outside the Docker network; map `ports:` and use `localhost`.
- Omitting `ports:` on a runner-hosted job and wondering why nothing listens.
- Omitting a health check and then adding `sleep 30` to compensate — this masks the problem and still fails under load.
- Assuming a container job can run on `windows-latest`. It cannot, and the error is not obvious.
- Expecting tools installed by `actions/setup-python` to be present — in a container job the image supplies Python, and `setup-python` may behave differently or be unnecessary.
- Forgetting that a private image needs `credentials:` with a username and token.

## Debugging Tips

- Connection refused on the first step almost always means a missing or too-lenient health check, not a wrong address — check whether the health check passes at all before changing hostnames.
- Run `docker ps` as a step to see which containers exist and what their published ports are.
- `docker inspect --format '{{json .State.Health}}' <name>` shows why a health check is failing.
- To decide whether it is an addressing problem, try both `curl http://selenium:4444/wd/hub/status` and `curl http://localhost:4444/wd/hub/status` in the same step; exactly one should work, and which one tells you where your job is running.
- If steps fail with "command not found" for something the runner normally has, you are in a container job and the image lacks it.
- Service container logs are not in the job log by default — add a step that runs `docker logs <service label>` on failure.

## Reference: `container:` and `services:` keys

| Key | Applies to | Purpose |
| --- | --- | --- |
| `image` | both | Image reference; pin by tag or digest |
| `credentials` | both | `username` / `password` for a private registry |
| `env` | both | Environment variables inside the container |
| `ports` | services | Publish a container port to the host — needed only for runner-hosted jobs |
| `volumes` | both | Extra mounts beyond the auto-mounted workspace |
| `options` | both | Raw `docker create` flags, including all `--health-*` settings |

## Minimal Workflow Example

```yaml
name: Service Container Demo

on: workflow_dispatch

jobs:
  probe:
    runs-on: ubuntu-latest
    services:
      selenium:
        image: selenium/standalone-chrome:126.0
        # The job runs ON the runner, so the port must be published.
        ports:
          - 4444:4444
        options: >-
          --health-cmd "curl -f http://localhost:4444/wd/hub/status"
          --health-interval 5s
          --health-retries 10
    steps:
      - name: Confirm the grid is reachable
        # localhost, because this job is on the runner, not in the network.
        run: curl -sf http://localhost:4444/wd/hub/status
```

### YAML Explanation

- `services.selenium` names the service; the name becomes its hostname on the Docker network.
- `ports: [4444:4444]` publishes the container's 4444 to the runner's 4444, which is what makes `localhost` work.
- `options` supplies the health check; GitHub blocks the first step until it passes.
- `--health-cmd` runs *inside* the service container, which is why it uses `localhost` there.
- The job has no `container:`, so steps execute directly on `ubuntu-latest`.

### Step-by-Step Execution

1. The workflow is dispatched.
2. GitHub provisions the runner and creates a Docker network for the job.
3. The `selenium` container starts; GitHub polls its health check.
4. Once healthy, port 4444 is published to the runner.
5. The first step runs and the `curl` succeeds.
6. At job end, the service container and network are removed.

## Production Workflow Example

```yaml
name: BDD Against Selenium Grid

on:
  schedule:
    - cron: "0 2 * * 1-5"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  bdd:
    runs-on: ubuntu-latest

    # Steps run INSIDE this image, so the service is addressed by label.
    container:
      image: python:3.13-slim
      options: --shm-size=2g

    services:
      selenium:
        image: selenium/standalone-chrome:126.0
        # No `ports:` needed -- the job container and this service share a
        # network, so publishing to the host would achieve nothing.
        env:
          SE_NODE_MAX_SESSIONS: "2"
        options: >-
          --shm-size=2g
          --health-cmd "curl -f http://localhost:4444/wd/hub/status"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 12

    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Install suite dependencies
        working-directory: your-solution-root-folder-name
        run: |
          # The image supplies Python 3.13, so no setup-python step is needed.
          pip install --disable-pip-version-check -r requirements.txt

      - name: Confirm grid readiness from inside the job container
        run: |
          # `selenium` is the service label. `localhost` would resolve to this
          # job container and refuse the connection.
          curl -sf http://selenium:4444/wd/hub/status

      - name: Run BDD suite against the remote grid
        working-directory: your-solution-root-folder-name
        env:
          SELENIUM_REMOTE_URL: http://selenium:4444/wd/hub
          BASE_URL: https://your-domain.com
        run: |
          behave --tags=regression \
            -D browser=chrome \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Capture service logs on failure
        if: failure()
        run: docker logs selenium || echo "Service logs unavailable."

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-grid-chrome
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30
          if-no-files-found: error
```

### YAML Explanation

- `container.image: python:3.13-slim` supplies the interpreter, so the workflow does not call `setup-python`.
- `--shm-size=2g` on both containers prevents Chrome from crashing on the default 64 MB `/dev/shm`, a failure that looks like a random browser crash.
- The service has no `ports:` because both containers are on the job's network.
- `SELENIUM_REMOTE_URL` points at `http://selenium:4444/wd/hub` — label, not localhost.
- The failure-only `docker logs` step surfaces grid errors that never reach the job log otherwise.
- `if-no-files-found: error` turns a silent empty upload into a visible failure.

### Expected Output

- The job log shows the grid becoming healthy before the first step runs.
- The readiness `curl` returns a JSON status with `"ready": true`.
- Behave scenarios execute against the remote grid and Allure results are uploaded.
- On failure, the run contains the grid's own container logs alongside the Behave output.

## Quiz

1. A job declares `container: { image: python:3.13-slim }` and a service labelled `db`. Which address reaches the service from a step?
   - **A.** `localhost:5432`
   - **B.** `db:5432`
   - **C.** `127.0.0.1:5432`
   - **D.** `host.docker.internal:5432`

2. A runner-hosted job (no `container:`) declares a service with no `ports:` mapping. What happens?
   - **A.** The service is reachable at its label as hostname.
   - **B.** The service is reachable on `localhost` at its container port.
   - **C.** The service starts but is unreachable from the job's steps.
   - **D.** The workflow fails validation before running.

3. Where does a service's `--health-cmd` execute?
   - **A.** On the runner host.
   - **B.** Inside the service container.
   - **C.** Inside the job container.
   - **D.** On GitHub's control plane.

4. A container job works on `ubuntu-latest` but fails immediately when `runs-on` is changed to `windows-latest`. Explain why, and give the two options for running the same suite on Windows.

5. A colleague replaces a `--health-cmd` with `run: sleep 30` before the first test step. The suite passes locally but still fails intermittently in CI. Explain both what the sleep hides and why it fails under load.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a `services:` block running `selenium/standalone-chrome` to a runner-hosted job and `curl` its status endpoint. | The status endpoint returns `"ready": true`; removing `ports:` reproduces a connection refusal. |
| Intermediate | Convert the same job to a container job using `python:3.13-slim`, and change the service address accordingly. | The suite runs inside the container and reaches the grid by label; using `localhost` reproduces the failure. |
| Challenge | Add a health check with `--health-retries 1` and a deliberately slow-starting service, observe the failure, then tune the retries until the job is deterministic. Record what the failure looked like. | A documented before/after showing the connection error and the retry count that fixed it. |

Solutions: [`solutions/module-22-solutions.md`](../solutions/module-22-solutions.md)

---

[Previous: Module 21](./module-21-composite-actions.md) | [Module Index](./README.md) | [Next: Module 23](./module-23-docker-publish.md)
