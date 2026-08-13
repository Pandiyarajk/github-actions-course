# Module 6: Runner Setup — Creating, Targeting, and Health-Checking Runners

![Module](https://img.shields.io/badge/Module-6-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20A%20Components-1f6feb?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-150%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 5](./module-05-runners.md) | [Next: Module 7](./module-07-jobs-and-steps.md)
> Level: **Intermediate** | Time: **150 min** | Example workflow: [`module-06-runner-setup.yml`](../examples/module-06-runner-setup.yml)
> Solutions: [`module-06-solutions.md`](../solutions/module-06-solutions.md)

> [!NOTE]
> This module carries an extra **[Appendix: Runner Installation Runbook](#appendix-runner-installation-runbook)**
> with the copy-pasteable registration, verification, and removal commands. The
> lesson comes first; the runbook is reference material you will return to.

## Learning Objectives

- Register a self-hosted runner on Ubuntu and Windows.
- Target GitHub-hosted runner images: latest vs version-pinned.
- Recognize deprecated runner images and migrate off them.
- Verify a self-hosted runner is online from the client and from GitHub.
- List available runners and their labels.

## Key Concepts

self-hosted runner registration, runner labels, `runs-on` images, version pinning, deprecation, runner service, `gh api` runner listing

## Expected Outcome

You can stand up a runner, point a workflow at the right OS/version, confirm it is healthy, and keep it off deprecated images.

## Concept Flow

```text
Download runner -> config.sh/.cmd (register with token + labels) -> run.sh/.cmd or service
   -> appears Online in Settings > Actions > Runners -> jobs with matching runs-on execute
```

---

## ELI5 Explanation

A self-hosted runner is your own computer signed up to do GitHub's jobs. You download GitHub's little worker program, give it a one-time password (token) so GitHub trusts it, stick labels on it (like "server1, windows"), and start it. Then any job that asks for those labels lands on that machine.

## Technical Explanation

A self-hosted runner is registered against a repo or org using a short-lived registration token from **Settings > Actions > Runners > New self-hosted runner**. The downloaded package is configured with `config.sh` (Linux/macOS) or `config.cmd` (Windows), which records the URL, token, name, and **labels**. The runner then runs interactively (`run.sh`/`run.cmd`) or as a background service. GitHub-hosted runners are selected by image label such as `ubuntu-latest`/`ubuntu-24.04` or `windows-latest`/`windows-2025`; `-latest` tracks GitHub's current default and changes over time, while pinned labels stay fixed until deprecated. Deprecated images are removed on an announced schedule, so pin deliberately and migrate before removal.

The behaviour worth internalising is how `runs-on` matches. A **list** of labels requires a *single* runner carrying **all** of them — the labels are ANDed, not ORed. And a `runs-on` naming a label that no online runner has does not fail; the job **queues indefinitely**, waiting for a runner that may never appear. A typo in a label therefore produces a hang rather than an error, which is why it costs so much time to diagnose.

## Real-World Use Case

A QA team installs runners on four Windows servers, labels them `self-hosted, windows, server1` … `server4`, and runs them as services so they restart on reboot. Web smoke tests run on GitHub-hosted `ubuntu-latest`; long desktop/UI regressions target the specific server labels.

## When To Use

- The suite needs hardware, licensed software, or a desktop session that hosted runners cannot provide.
- Tests must reach an internal network or an environment behind a firewall.
- Run durations or volumes make hosted-runner minutes uneconomic — self-hosted runners consume no billed minutes.
- You need a specific OS build held stable for longer than a hosted image is supported.

## When NOT To Use

- For public repositories accepting fork pull requests. A fork PR running on your runner executes untrusted code on your hardware; the runner is not disposable, so compromise persists. See Module 24.
- When a hosted image already provides everything — you are then taking on patching, disk, and uptime for nothing.
- For jobs needing clean, isolated state every run, unless you add your own cleanup; a self-hosted workspace persists between jobs.
- As a workaround for a slow build that caching would fix (Module 16).

## Common Mistakes

- Reusing an expired registration token (generate a fresh one per machine).
- Running interactively (`run.cmd`) instead of as a service, so it dies on logout/reboot.
- Targeting `runs-on: [self-hosted, server1]` when no single runner has both labels — the job queues rather than failing.
- Assuming a runner can be addressed by *name*. Only labels are selectable; the name is for humans.
- Staying on a deprecated image until jobs suddenly fail.
- Running untrusted fork PRs on a self-hosted runner.
- Forgetting that the workspace persists, so a previous run's artifacts leak into the next one.

## Debugging Tips

- A job stuck in **queued** with no runner picking it up is nearly always a label mismatch. Compare `runs-on` against the labels in Settings → Actions → Runners character by character; there is no error message for this.
- List what actually exists rather than what you believe exists:
  `gh api repos/<owner>/<repo>/actions/runners --jq '.runners[] | {name, status, labels: [.labels[].name]}'`
- **Idle** means online and free, **Active** means running a job, **Offline** means the service is not connected. An Offline runner after a reboot points at interactive-mode registration.
- On the machine, `systemctl status actions.runner.*` (Linux) or `Get-Service "actions.runner.*"` (Windows) tells you whether the service is even running.
- Jobs failing with stale files from a previous run confirm workspace persistence; add an explicit cleanup step or use `actions/checkout` with `clean: true`.
- A sudden unknown-image failure on unchanged YAML means a hosted image was deprecated and removed — check the runner-images changelog rather than your workflow.

## GitHub-Hosted Images: Latest vs Version-Pinned

| `runs-on` | Meaning |
| --- | --- |
| `ubuntu-latest` | GitHub's current default Ubuntu (changes over time) |
| `ubuntu-24.04` / `ubuntu-22.04` | Pinned Ubuntu versions |
| `windows-latest` | GitHub's current default Windows Server |
| `windows-2025` / `windows-2022` | Pinned Windows Server versions |
| `macos-latest` / `macos-14` | Latest / pinned macOS |

- Use `-latest` for general jobs you want to stay current automatically.
- **Pin** a version when you need reproducibility or a tool tied to a specific OS.
- Watch the runner-images changelog; **deprecated images** (e.g. older `ubuntu-20.04`, `windows-2019`) are removed on a schedule — migrate before the cutoff or jobs will fail.

## Minimal Workflow Example

```yaml
name: Inspect Runner Image

on:
  workflow_dispatch:
    inputs:
      runner_label:
        description: "Hosted image to inspect"
        type: choice
        options: [ubuntu-latest, ubuntu-24.04, windows-latest, windows-2025]
        default: ubuntu-latest

jobs:
  inspect-hosted:
    runs-on: ${{ inputs.runner_label }}
    steps:
      - name: Report Linux image
        if: runner.os == 'Linux'
        run: |
          grep PRETTY_NAME /etc/os-release

      - name: Report Windows image
        if: runner.os == 'Windows'
        shell: powershell
        run: |
          (Get-CimInstance Win32_OperatingSystem).Caption
```

### YAML Explanation

- `type: choice` constrains the manual input to labels that actually exist, so a typo cannot queue the job forever.
- `runs-on: ${{ inputs.runner_label }}` shows that `runs-on` accepts an expression, not only a literal.
- `runner.os` is supplied by the runner itself and is one of `Linux`, `Windows`, or `macOS` — it lets one job serve both platforms.
- `shell: powershell` is required on Windows for the `Get-CimInstance` call; the default shell differs per platform (Module 9).

### Step-by-Step Execution

1. Someone dispatches the workflow and picks an image.
2. GitHub queues the job for that image label.
3. A hosted runner of that image picks it up.
4. `runner.os` selects exactly one of the two report steps.
5. The log prints the precise OS build, which is how you confirm what `-latest` currently resolves to.

## Production Workflow Example

```yaml
name: Verify Self-Hosted Pool

on:
  workflow_dispatch:
  schedule:
    # Every weekday at 06:00 UTC, so an offline runner is found before the
    # nightly regression needs it rather than after it has already failed.
    - cron: "0 6 * * 1-5"

permissions:
  contents: read

jobs:
  verify-self-hosted:
    name: Verify ${{ matrix.server }}
    strategy:
      fail-fast: false          # check every server, not just up to the first bad one
      matrix:
        server: [server1, server2, server3, server4]
    # A LIST ANDs the labels: one runner must carry all three. There is no
    # partial match, and no error if nothing matches -- the job just queues.
    runs-on: [self-hosted, windows, "${{ matrix.server }}"]
    timeout-minutes: 10         # bound the queue wait rather than hanging for 6 hours
    steps:
      - name: Report runner identity
        shell: powershell
        run: |
          Write-Host "Runner name: $env:RUNNER_NAME"
          Write-Host "Runner OS:   $env:RUNNER_OS"
          Write-Host "Workspace:   $env:GITHUB_WORKSPACE"

      - name: Confirm the runner service is healthy
        shell: powershell
        run: |
          $svc = Get-Service "actions.runner.*" | Select-Object -First 1
          Write-Host "Service $($svc.Name) is $($svc.Status)"
          if ($svc.Status -ne 'Running') { exit 1 }

      - name: Check free disk space
        shell: powershell
        run: |
          # A self-hosted workspace persists between jobs, so disks fill up
          # silently until a run fails for an unrelated-looking reason.
          $drive = Get-PSDrive C
          $freeGb = [math]::Round($drive.Free / 1GB, 1)
          Write-Host "Free space: $freeGb GB"
          if ($freeGb -lt 10) {
            Write-Host "::warning::Low disk space on $env:RUNNER_NAME"
          }
```

### YAML Explanation

- `fail-fast: false` matters here: the point is a full picture of the pool, so one dead server must not cancel the checks on the others.
- `runs-on: [self-hosted, windows, "${{ matrix.server }}"]` requires all three labels on one runner; the matrix produces one job per server.
- `timeout-minutes: 10` converts an indefinite queue into a visible failure. Without it a mislabelled runner leaves the job waiting against the 360-minute default.
- The disk-space check exists because self-hosted workspaces persist; hosted runners are discarded, so this class of failure is unique to self-hosted.
- `::warning::` surfaces the condition in the run summary without failing the job.

### Expected Output

- Four jobs, one per server, each naming the runner that executed it.
- A server whose runner is offline leaves its job queued until the 10-minute timeout, then fails — telling you which machine to look at.
- Low disk space appears as an annotation on the run rather than a hard failure.

## Quiz

1. A job declares `runs-on: [self-hosted, windows, server1]`. Your pool has one runner labeled `self-hosted, windows` and another labeled `self-hosted, server1`. What happens?
   - **A.** The job runs on whichever runner matches the most labels.
   - **B.** The job stays queued — a list requires one runner carrying **all** the listed labels.
   - **C.** The job splits its steps across both runners.
   - **D.** The job fails immediately with a label validation error.

2. Your runner works while you are logged into the server, but every job queues after the machine reboots. What is the most likely cause?
   - **A.** The registration token expired and must be regenerated.
   - **B.** The runner was started interactively with `run.cmd` instead of being installed as a service.
   - **C.** `runs-on` needs a `-latest` suffix on self-hosted labels.
   - **D.** Self-hosted runners must be re-registered after every reboot.

3. Which statement about `runs-on: ubuntu-latest` versus `runs-on: ubuntu-24.04` is correct?
   - **A.** They are aliases and will always resolve to the same image.
   - **B.** `ubuntu-latest` tracks GitHub's current default and changes over time; the pinned label stays fixed until that version is deprecated and removed.
   - **C.** `ubuntu-24.04` is a self-hosted label and needs a matching runner registration.
   - **D.** Pinned labels never stop working, so pinning removes all migration work.

4. Registration failed with an authentication error even though you copied the token from the runner setup page. Explain the two most likely reasons, and describe how you would confirm success from both the client machine and GitHub.

5. A workflow that has run green for a year suddenly fails on every job with an unknown-image error, and nobody changed the YAML. Explain what happened and describe a process that prevents it recurring.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Run a job on `ubuntu-latest` and print the OS version. | Logs show the current Ubuntu image version. |
| Intermediate | List repo runners with `gh api` and read their labels/status. | Output shows each runner's name, status, and labels. |
| Challenge | Register a self-hosted runner with labels and target it with composite `runs-on`. | The job runs only on the labeled, online runner. |

Solutions: [`solutions/module-06-solutions.md`](../solutions/module-06-solutions.md)

---

## Appendix: Runner Installation Runbook

Reference commands for standing up, checking, and removing a self-hosted runner.
This is operational detail rather than lesson content — it is kept here so the
module above reads as a lesson.

> Get a fresh registration token from **Repo/Org > Settings > Actions > Runners > New self-hosted runner**. Tokens expire quickly; generate one per machine.

### Registering on Ubuntu (Linux)

```bash
# 1) Create a working folder
mkdir actions-runner && cd actions-runner

# 2) Download the latest runner package (check the Releases page for the URL)
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.317.0/actions-runner-linux-x64-2.317.0.tar.gz

# 3) Extract
tar xzf actions-runner-linux-x64.tar.gz

# 4) Configure with your repo URL, token, name, and labels
./config.sh --url https://github.com/your-org/your-repo \
  --token YOUR_REGISTRATION_TOKEN \
  --name linux-runner-1 \
  --labels self-hosted,linux,ubuntu

# 5a) Run interactively
./run.sh

# 5b) Or install as a service so it survives reboots
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

### Registering on Windows (Server, Windows 10, Windows 11)

```powershell
# 1) Create a working folder
mkdir actions-runner; cd actions-runner

# 2) Download the latest runner package (check the Releases page for the URL)
Invoke-WebRequest -Uri https://github.com/actions/runner/releases/download/v2.317.0/actions-runner-win-x64-2.317.0.zip -OutFile actions-runner-win-x64.zip

# 3) Extract
Expand-Archive -Path actions-runner-win-x64.zip -DestinationPath .

# 4) Configure with repo URL, token, name, and labels
./config.cmd --url https://github.com/your-org/your-repo `
  --token YOUR_REGISTRATION_TOKEN `
  --name server1 `
  --labels self-hosted,windows,server1

# 5a) Run interactively
./run.cmd

# 5b) Or install as a Windows service (auto-start on boot)
./config.cmd --runasservice    # or use: ./svc.cmd install ; ./svc.cmd start
```

The same steps work on Windows Server, Windows 10, and Windows 11. Use distinct `--name` and label values per machine (e.g. `server1` … `server4`).

### Removing / Re-registering

```bash
# Linux
./config.sh remove --token YOUR_REMOVE_TOKEN
```

```powershell
# Windows
./config.cmd remove --token YOUR_REMOVE_TOKEN
```

### Verifying a Runner Is Online

**From GitHub (UI).** **Settings > Actions > Runners** lists each runner with a status of **Idle** (online, free), **Active** (running a job), or **Offline**. Labels are shown next to each runner.

**From GitHub (API / CLI).**

```bash
# List repo self-hosted runners (name, status, labels)
gh api repos/your-org/your-repo/actions/runners \
  --jq '.runners[] | {name: .name, status: .status, labels: [.labels[].name]}'

# Org-level runners
gh api orgs/your-org/actions/runners \
  --jq '.runners[] | {name, status}'
```

**From the client machine.**

```bash
# Linux: service status
sudo ./svc.sh status
systemctl status actions.runner.*.service
```

```powershell
# Windows: confirm the runner service is running
Get-Service "actions.runner.*" | Select-Object Name, Status
```

If a workflow targets a label but no matching runner is **Idle/Active**, the job stays **queued** until one comes online.

---

[Previous: Module 5](./module-05-runners.md) | [Module Index](./README.md) | [Next: Module 7](./module-07-jobs-and-steps.md)
