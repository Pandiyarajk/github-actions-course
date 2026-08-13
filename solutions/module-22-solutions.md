# Module 22 — Solutions

![Module](https://img.shields.io/badge/Module-22-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 22](../modules/module-22-container-jobs.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** With `container:` set, the job's steps run inside a container that
GitHub attaches to the same Docker network as every service, so the service's
**label** is its DNS name and its **container** port is the one to use:
`db:5432`. **A** and **C** are the same wrong answer written two ways — inside a
container, `localhost` and `127.0.0.1` are that container's own loopback, and
nothing is listening on 5432 there, so the connection is refused. **D**
(`host.docker.internal`) points at the runner host, which is a Docker Desktop
convention rather than something the job network provides, and even if it
resolved, the service port is not published to the host because no `ports:` was
declared.

**2 — C.** The service container starts normally and its health check passes,
but a runner-hosted job sits outside the job's Docker network, so nothing in the
job can reach it: no DNS entry for the label, and no published port on
`localhost`. **A** is what would be true if the job ran in a container. **B**
requires `ports:`, which is exactly what was omitted. **D** is wrong and it is
the reason this failure costs so much time — omitting `ports:` is valid YAML and
valid configuration, so the workflow runs and only the connection fails.

**3 — B.** `options:` is passed verbatim to `docker create` for that service, so
`--health-cmd` runs **inside the service container**. That is why the health
command uses `localhost` even in workflows where your steps must use the label:
inside the service, `localhost` *is* the service. **A** is the common
misreading, and it is what leads people to "fix" a perfectly good health check by
rewriting `localhost` to the label — a change that makes the check depend on
network DNS to reach a port that is already on its own loopback, and buys
nothing. **C** is wrong because the job container may not even have `curl`. **D**
is wrong — GitHub polls the Docker health status; it does not execute anything
itself.

**4.** `container:` is **Linux-only**. The container support in the runner is
implemented against a Linux Docker daemon and Linux container images, and the
Windows and macOS hosted runners do not provide it — so a job with `container:`
and `runs-on: windows-latest` fails during job initialisation, before any step
runs. It is not a step failure, and the message does not say "use Linux", which
is why it reads as a broken image reference.

The two options for running the same suite on Windows:

1. **Drop `container:` and provision the toolchain on the runner.** Keep
   `runs-on: windows-latest`, add `actions/setup-python@v7` with
   `python-version: "3.13"`, and install the packages with `pip`. You pay the
   install cost every run and you lose the digest-pinned reproducibility the
   image gave you, but the suite runs natively on Windows. Note that `services:`
   is documented as requiring a Linux runner too, so the grid has to come from
   somewhere else — a real remote grid, or a browser installed directly on the
   runner and driven locally.
2. **Use a self-hosted Windows runner with the toolchain pre-installed.** The
   runner's own machine image takes the place of the container image: Python,
   the browsers and the drivers are baked in once, and the workflow declares no
   `container:` at all. This is the pattern to use when the suite genuinely
   needs Windows-only behaviour (a desktop application, or a browser
   configuration that only exists on Windows).

What you cannot do is keep `container:` and change the runner. If the suite is
Linux-compatible, the third option is the honest one: leave `runs-on:
ubuntu-latest` and stop trying to move it.

**5.** The sleep hides the **readiness contract**. A health check is a
statement of what "ready" means, and GitHub blocks the first step until that
statement is true. `sleep 30` replaces it with a guess about how long readiness
usually takes, and a guess has no relationship to the actual state of the
service. Three specific things it conceals:

- **Whether the service ever became ready at all.** With a health check, a
  service that fails to start makes the job fail at initialisation with the
  service named. With a sleep, the job proceeds and the first connection fails,
  so the failure surfaces as a test error and gets triaged as a test bug.
- **Why the service is unhealthy.** The health check's own output is visible via
  `docker inspect`; a sleep produces no diagnostic at all.
- **The service's logs.** These never reach the job log on their own, so without
  a health check *and* a `docker logs <label>` step on failure, there is no
  evidence on the grid side.

It fails under load because 30 seconds is a fixed budget against a variable
cost. Locally the image is already in the local Docker cache and the machine is
idle. In CI the container image may need pulling, the runner's CPU and disk are
shared with the job's own checkout and `pip install`, and a grid asked for more
concurrent sessions takes longer to come up. When the sum of those exceeds 30
seconds — which happens on some runs and not others — the first scenario hits a
connection refusal. That is the definition of an intermittent failure: a race
between a fixed wait and a variable startup.

The sleep is also wrong in the other direction. When the service is ready in
four seconds, the job still waits 30, so every run pays for the worst case. A
health check with `--health-interval 5s --health-retries 12` returns as soon as
the service answers and only spends the full 60 seconds when something is
actually wrong.

## Lab 1 — Beginner

**Task:** Add a `services:` block running `selenium/standalone-chrome` to a
runner-hosted job and `curl` its status endpoint. The status endpoint should
return `"ready": true`, and removing `ports:` should reproduce a connection
refusal.

<details>
<summary>Show solution</summary>

```yaml
name: Lab 22-1 Grid On The Runner

on: workflow_dispatch

permissions:
  contents: read

jobs:
  probe:
    name: Runner-hosted probe
    runs-on: ubuntu-latest

    services:
      selenium:
        # Pinned rather than :latest, so a grid upgrade is a deliberate commit.
        image: selenium/standalone-chrome:126.0
        # REQUIRED for a runner-hosted job: this job is outside the job's Docker
        # network, so the only way in is a port published on the host.
        ports:
          - 4444:4444
        options: >-
          --shm-size=2g
          --health-cmd "curl -f http://localhost:4444/wd/hub/status"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 12

    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      # No sleep and no retry loop: the health check has already passed by the
      # time this step is allowed to start.
      - name: Probe the grid via localhost
        run: |
          curl -sf http://localhost:4444/wd/hub/status \
            | python -c "import json,sys; print('ready:', json.load(sys.stdin)['value']['ready'])"

      - name: Show which containers exist
        if: always()
        run: docker ps
```

**Why this works.** Two independent things have to be true. The health check
makes GitHub wait until the grid answers `/wd/hub/status` *inside* the service
container, so the probe cannot run early. `ports: [4444:4444]` publishes the
container's 4444 onto the runner's 4444, which is what makes `localhost` a valid
address from steps that execute on the runner itself. The job has no
`container:`, so `python` comes from `actions/setup-python` and `curl` comes from
the `ubuntu-latest` image — both present because the steps are on the runner.

**Verify the failure mode the lab asks for.** Delete the `ports:` block and
re-run. The service still starts and still becomes healthy — the job log shows
it — but the probe step fails: `curl` cannot connect to `localhost:4444` because
nothing on the runner is listening there. Read the failure carefully, because
this is the trap: the service is *fine*, and the error is about the address. Add
a second step `run: curl -sf --max-time 5 http://selenium:4444/wd/hub/status` and
watch that fail too, with a DNS resolution error rather than a refusal — proof
that a runner-hosted job has neither route available without `ports:`.

**Common wrong answer.** Reaching for `sleep 30` before the probe when the first
attempt fails. If the address is wrong, waiting longer changes nothing, and the
step now takes 30 seconds to fail instead of one. Check whether the health check
passed before you touch either the hostname or the timing.

</details>

## Lab 2 — Intermediate

**Task:** Convert the same job to a container job using `python:3.13-slim`, and
change the service address accordingly. The suite should run inside the container
and reach the grid by label; using `localhost` should reproduce the failure.

<details>
<summary>Show solution</summary>

```yaml
name: Lab 22-2 Grid From A Container Job

on: workflow_dispatch

permissions:
  contents: read

jobs:
  bdd:
    name: Container job
    # Container jobs are Linux-only. windows-latest fails at initialisation.
    runs-on: ubuntu-latest

    container:
      image: python:3.13-slim
      # Chrome crashes on the default 64 MB /dev/shm, and the symptom is a
      # browser crash that reads as a flaky test rather than a resource limit.
      options: --shm-size=2g

    services:
      selenium:
        image: selenium/standalone-chrome:126.0
        # `ports:` REMOVED. This job is already on the service's network, so
        # publishing to the host would achieve nothing.
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

      # python:3.13-slim has no curl. In a container job the available tools are
      # the IMAGE's, not the runner's.
      - name: Install probe dependencies
        run: |
          apt-get update -qq
          apt-get install -y --no-install-recommends curl > /dev/null

      - name: Install suite dependencies
        working-directory: your-solution-root-folder-name
        run: |
          # No setup-python step: the image already supplies 3.13.
          python --version
          pip install --disable-pip-version-check -r requirements.txt

      - name: Probe the grid via the service label
        run: |
          curl -sf http://selenium:4444/wd/hub/status \
            | python -c "import json,sys; print('ready:', json.load(sys.stdin)['value']['ready'])"

      - name: Run BDD suite against the remote grid
        working-directory: your-solution-root-folder-name
        env:
          # Label, not localhost.
          SELENIUM_REMOTE_URL: http://selenium:4444/wd/hub
          BASE_URL: https://your-domain.com
        run: |
          behave --tags=regression \
            -D browser=chrome \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      # Grid-side errors never reach the job log on their own.
      - name: Capture grid logs on failure
        if: failure()
        run: docker logs selenium || echo "Service logs unavailable in this job."

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-container-job
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30
          if-no-files-found: error
```

The full worked version, running both addressing styles side by side in one
workflow, is [`module-22-container-jobs.yml`](../examples/module-22-container-jobs.yml).

**Why this works.** Three changes travel together, and the conversion is only
correct if you make all three. Adding `container:` puts the steps on the job's
Docker network, which is what makes `selenium` resolve. Removing `ports:` is
then correct rather than merely harmless — the mapping had no consumer. And
`actions/setup-python` goes away because the image supplies the interpreter;
leaving it in would install a second Python inside the container for no reason.

**Verify the failure mode the lab asks for.** Change
`SELENIUM_REMOTE_URL` to `http://localhost:4444/wd/hub` and re-run. Behave fails
to create a session with a connection refusal, because inside the job container
`localhost` is that container, and the grid is a *different* container. This is
the exact mirror of Lab 1's failure, and the two together are the whole lesson:
the same wrong answer produces a refusal in both directions. Keep both steps in
the workflow while you learn — run `curl http://selenium:4444/wd/hub/status` and
`curl http://localhost:4444/wd/hub/status` in one step and exactly one will
succeed, which tells you where your job is actually running.

**Common wrong answer.** Assuming the runner's tools come along into the
container, then debugging `curl: command not found` as though the image were
broken. A "command not found" for something `ubuntu-latest` definitely has is
the reliable tell that you are inside a container job. Either install the tool
(as above) or choose an image that already has it.

</details>

## Lab 3 — Challenge

**Task:** Add a health check with `--health-retries 1` and a deliberately
slow-starting service, observe the failure, then tune the retries until the job
is deterministic. Record what the failure looked like.

<details>
<summary>Show solution</summary>

Start from the broken version. `selenium/standalone-chrome` needs roughly ten to
twenty seconds before it answers, so a single retry at a two-second interval is
guaranteed to give up first:

```yaml
name: Lab 22-3 Health Check Tuning (BEFORE)

on: workflow_dispatch

permissions:
  contents: read

jobs:
  probe:
    runs-on: ubuntu-latest

    services:
      selenium:
        image: selenium/standalone-chrome:126.0
        ports:
          - 4444:4444
        # DELIBERATELY BROKEN. One attempt, two seconds in, against a service
        # that needs far longer than that to answer.
        options: >-
          --shm-size=2g
          --health-cmd "curl -f http://localhost:4444/wd/hub/status"
          --health-interval 2s
          --health-timeout 1s
          --health-retries 1

    steps:
      - name: Probe the grid
        run: curl -sf http://localhost:4444/wd/hub/status
```

Then the fixed version:

```yaml
name: Lab 22-3 Health Check Tuning (AFTER)

on: workflow_dispatch

permissions:
  contents: read

jobs:
  probe:
    runs-on: ubuntu-latest

    services:
      selenium:
        image: selenium/standalone-chrome:126.0
        ports:
          - 4444:4444
        # interval x retries is the total budget: 5s x 12 = 60s. Generous
        # enough to absorb a cold image pull and a busy runner, and it still
        # returns the moment the grid answers -- the budget is a ceiling, not a
        # wait.
        #
        # --health-start-period is the more precise tool: it says "failures
        # during this window do not count", so the retry budget covers only the
        # period in which the service is genuinely expected to be up.
        options: >-
          --shm-size=2g
          --health-cmd "curl -f http://localhost:4444/wd/hub/status"
          --health-start-period 10s
          --health-interval 5s
          --health-timeout 3s
          --health-retries 12

    steps:
      - name: Probe the grid
        run: |
          curl -sf http://localhost:4444/wd/hub/status \
            | python -c "import json,sys; print('ready:', json.load(sys.stdin)['value']['ready'])"

      - name: Record the health state for the write-up
        if: always()
        run: |
          docker inspect --format '{{json .State.Health}}' \
            "$(docker ps --filter "ancestor=selenium/standalone-chrome:126.0" --format '{{.Names}}' | head -n1)" \
            || echo "Service container not found."
```

The write-up the lab asks for:

| | Before | After |
| --- | --- | --- |
| `--health-interval` | `2s` | `5s` |
| `--health-timeout` | `1s` | `3s` |
| `--health-retries` | `1` | `12` |
| `--health-start-period` | not set | `10s` |
| Readiness budget | ~2s | up to 60s after a 10s grace |
| Outcome | job fails during initialisation; the failure is attributed to the service, not to a step | grid healthy in roughly 10–15s, probe passes on the first attempt |

**What the failure looked like.** The job did not reach the `Probe the grid`
step at all. The failure appeared in the service-initialisation section of the
log, before any step group, naming the `selenium` service — Docker marked the
container `unhealthy` after its single failed check, and the runner refused to
start the job's steps against an unhealthy service. The important observation is
*where* it failed: nothing in the step list ran, so there was no test output and
nothing that looked like a Selenium problem. `docker inspect --format '{{json
.State.Health}}'` on a re-run with a looser check showed the first probe exiting
non-zero with an empty response, confirming the grid was simply still booting
rather than misconfigured.

**Why this works.** `--health-interval` multiplied by `--health-retries` is the
total time Docker allows before declaring the container unhealthy, and GitHub
will not start the job's steps against an unhealthy service. So the retry count
is not a style preference — it is the readiness deadline. Setting it to cover
the slowest realistic start (cold pull, busy runner) makes the job deterministic
without slowing down the fast path, because the check succeeds and the job
proceeds as soon as the service answers. `--health-start-period` separates the
two concerns properly: startup failures inside the grace window are expected and
ignored, so the retry budget is reserved for real failures.

**Verify the failure mode the lab asks for.** Run the BEFORE workflow. Confirm
the job fails before the first step and that the log names the service. Then
raise only `--health-retries` to `12`, leaving the 2s interval, and it passes —
which proves the diagnosis was the deadline and not the health command, the
image, or the port mapping.

**Common wrong answer.** Deleting the health check because "it was the thing
that failed". The job then starts immediately, the probe races the grid, and the
failure moves from a deterministic initialisation error to an intermittent
connection refusal inside a test — strictly worse, because it is now
misattributed. A health check that fails is doing its job; the fix is to give it
a realistic deadline, not to remove the check.

</details>

---

[Solutions Index](./README.md) | [Module 22](../modules/module-22-container-jobs.md) | [Course Home](../README.md)
