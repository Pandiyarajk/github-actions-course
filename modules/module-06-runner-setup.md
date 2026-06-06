# Module 6: Runner Setup — Creating, Targeting, and Health-Checking Runners

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 5](./module-05-runners.md) | [Next: Module 7](./module-07-jobs-and-steps.md)
> Level: **Intermediate** | Time: **150 min** | Example workflow: [`module-06-runner-setup.yml`](../examples/module-06-runner-setup.yml)

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

## Real-World Use Case

A QA team installs runners on four Windows servers, labels them `self-hosted, windows, server1` … `server4`, and runs them as services so they restart on reboot. Web smoke tests run on GitHub-hosted `ubuntu-latest`; long desktop/UI regressions target the specific server labels.

## Registering a Self-Hosted Runner

> Get a fresh registration token from **Repo/Org > Settings > Actions > Runners > New self-hosted runner**. Tokens expire quickly; generate one per machine.

### Ubuntu (Linux)

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

### Windows (Server, Windows 10, Windows 11)

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

## Verifying a Runner Is Online

### From GitHub (UI)

**Settings > Actions > Runners** lists each runner with a status of **Idle** (online, free), **Active** (running a job), or **Offline**. Labels are shown next to each runner.

### From GitHub (API / CLI)

```bash
# List repo self-hosted runners (name, status, labels)
gh api repos/your-org/your-repo/actions/runners \
  --jq '.runners[] | {name: .name, status: .status, labels: [.labels[].name]}'

# Org-level runners
gh api orgs/your-org/actions/runners \
  --jq '.runners[] | {name, status}'
```

### From the client machine

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

## Example Workflow

The companion workflow inspects a hosted image and verifies a self-hosted runner answers. See [`module-06-runner-setup.yml`](../examples/module-06-runner-setup.yml).

### Target a Hosted Image by Label

```yaml
on:
  workflow_dispatch:
    inputs:
      runner_label:
        type: choice
        options: [ubuntu-latest, ubuntu-24.04, windows-latest, windows-2025]
        default: ubuntu-latest

jobs:
  inspect-hosted:
    runs-on: ${{ inputs.runner_label }}
    steps:
      - if: runner.os == 'Linux'
        run: cat /etc/os-release | grep PRETTY_NAME
      - if: runner.os == 'Windows'
        shell: powershell
        run: (Get-CimInstance Win32_OperatingSystem).Caption
```

### Verify a Self-Hosted Runner with Composite Labels

```yaml
jobs:
  verify-self-hosted:
    runs-on: [self-hosted, windows, server1]   # ALL labels must match one runner
    steps:
      - shell: powershell
        run: |
          Write-Host "Runner name: $env:RUNNER_NAME"
          Write-Host "Runner is online and healthy."
```

`runs-on` with a list requires a single runner that has **all** the listed labels.

### Expected Output

- The hosted job prints the exact OS caption/version for the chosen image.
- The self-hosted job runs only if a runner labeled `self-hosted, windows, server1` is online.
- A missing/offline runner leaves the job queued.

## Common Mistakes

- Reusing an expired registration token (generate a fresh one per machine).
- Running interactively (`run.cmd`) instead of as a service, so it dies on logout/reboot.
- Targeting `runs-on: [self-hosted, server1]` when no runner has both labels.
- Staying on a deprecated image until jobs suddenly fail.
- Running untrusted fork PRs on a self-hosted runner.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Run a job on `ubuntu-latest` and print the OS version. | Logs show the current Ubuntu image version. |
| Intermediate | List repo runners with `gh api` and read their labels/status. | Output shows each runner's name, status, and labels. |
| Challenge | Register a self-hosted runner with labels and target it with composite `runs-on`. | The job runs only on the labeled, online runner. |

---

[Previous: Module 5](./module-05-runners.md) | [Module Index](./README.md) | [Next: Module 7](./module-07-jobs-and-steps.md)
