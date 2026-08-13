# Module 6 — Solutions

![Module](https://img.shields.io/badge/Module-6-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 6](../modules/module-06-runner-setup.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** A list in `runs-on` is an AND, not an OR: the scheduler looks for one
runner that carries *every* label. Neither runner in the pool has all three, so
the job sits queued indefinitely. **A** is the intuition most people bring to it —
"best match wins" — and it is exactly wrong; there is no scoring, no partial
match, no fallback. **C** is impossible: a job is indivisible and runs entirely on
one runner. **D** is the cruel part — there is no validation error, because the
labels are perfectly legal and a matching runner might come online later. The job
simply waits, which reads like a hung queue rather than a configuration mistake.

**2 — B.** Started with `run.cmd` (or `run.sh`), the runner is an ordinary
foreground process owned by your session; logging out or rebooting kills it.
Installed as a service it starts at boot with no user logged in. **A** is the
plausible distractor, because expired tokens really are a common failure — but a
registration token is consumed once at `config` time and plays no part in
subsequent connections, so an expired one cannot explain a runner that already
worked. **C** is invented syntax: `-latest` is part of GitHub's hosted image
labels and means nothing on a self-hosted label. **D** is false — registration
persists in the runner's configuration files across reboots.

**3 — B.** `ubuntu-latest` is an alias GitHub repoints as its default Ubuntu moves
forward, so the same YAML gets a different image over time; a pinned label such
as `ubuntu-24.04` stays put until that version reaches end of life and is removed.
**A** is only *temporarily* true: the two labels do resolve to the same image
whenever the pinned version happens to be the current default, which is why the
difference goes unnoticed until a migration. **C** confuses hosted image labels
with self-hosted labels. **D** is the dangerous belief — pinning buys
reproducibility, not permanence; a pinned image is eventually removed, and then
it fails all at once instead of drifting gradually.

**4.** The two usual causes:

- **The token expired.** Registration tokens are short-lived. If you opened the
  setup page, went to lunch, and then ran `config`, the token is stale. Reload
  **Settings > Actions > Runners > New self-hosted runner** and copy a fresh one.
- **The token and the URL do not match scopes.** A repository-level registration
  token cannot register against an organisation URL, and an org token cannot
  register against a single repository. Generate the token from the same level as
  the `--url` you pass.

A third, less common cause: the same token already consumed by another machine —
generate one token per runner.

Confirm success from both ends:

```bash
# From the client machine (Linux)
sudo ./svc.sh status
systemctl status actions.runner.*.service
```

```powershell
# From the client machine (Windows)
Get-Service "actions.runner.*" | Select-Object Name, Status
```

```bash
# From GitHub -- the authoritative view
gh api repos/your-org/your-repo/actions/runners \
  --jq '.runners[] | {name: .name, status: .status, labels: [.labels[].name]}'
```

Both views matter. A runner service can be **Running** locally while GitHub shows
it **Offline**, which points at egress being blocked rather than at the runner
itself.

**5.** The pinned runner image the workflow named was deprecated and then removed
on GitHub's announced schedule. Nothing in the repository changed; the platform
did. Because every job references the same label, the failure arrives everywhere
simultaneously, which is why it feels like an outage rather than a config problem.

A process that prevents a repeat:

1. Keep image labels in **one** place — a workflow-level `env` value, a reusable
   workflow input, or a composite action — so migrating is a single edit rather
   than a repository-wide search.
2. Track the runner-images changelog and deprecation announcements; removals are
   announced months ahead, and warning annotations appear on jobs using a
   deprecated image well before it stops working.
3. Run one low-cost canary job on the *next* image on a schedule, so you learn
   your suite's incompatibilities before the migration is forced. See
   [Module 4](../modules/module-04-scheduled-workflows.md) for the `schedule`
   trigger.
4. Treat the deprecation warning in the job log as a failure to triage, not noise
   to scroll past — it is the only advance notice that lands in front of the team.

## Lab 1 — Beginner

**Task:** Run a job on `ubuntu-latest` and print the OS version.

<details>
<summary>Show solution</summary>

```yaml
name: Inspect Hosted Image

on:
  workflow_dispatch:
    inputs:
      runner_label:
        description: "Hosted image to inspect."
        type: choice
        options: [ubuntu-latest, ubuntu-24.04, windows-latest, windows-2025]
        default: ubuntu-latest

jobs:
  inspect-hosted:
    name: Inspect ${{ inputs.runner_label }}
    runs-on: ${{ inputs.runner_label }}
    timeout-minutes: 5
    steps:
      - name: Print Linux OS version
        if: runner.os == 'Linux'
        run: |
          grep PRETTY_NAME /etc/os-release
          echo "Runner OS: $RUNNER_OS"

      - name: Print Windows OS version
        if: runner.os == 'Windows'
        shell: powershell
        run: |
          (Get-CimInstance Win32_OperatingSystem).Caption
          Write-Host "Runner OS: $env:RUNNER_OS"
```

**Why this works.** `runs-on` accepts an expression, so a `choice` input lets one
workflow inspect several images without duplicating the job. `runner.os` is
resolved by the runner itself, which makes it the right guard for
OS-specific steps — it is available in `if:` at step level, unlike anything you
would have to compute first. Each step then uses its platform's own command and
its own shell's variable syntax.

**Verify the failure mode the lab asks for.** Drop the `if:` guards and dispatch
against `windows-latest`. The Linux step now runs on Windows and fails, because
`grep` and `/etc/os-release` do not exist there — PowerShell reports that `grep`
is not recognised as a cmdlet and the step exits non-zero. Re-add the guards and
the same workflow passes on both images. This is the mechanism behind most
"works on Ubuntu, fails on Windows" reports: not the tooling, just an
unguarded shell assumption.

**Common wrong answer.** Comparing `runner.os == 'linux'` in lowercase. The value
is `Linux`, `Windows`, or `macOS`, and expression string comparison is
case-insensitive for `==` — but the same lowercase habit applied to a shell
comparison such as `[ "$RUNNER_OS" = "linux" ]` is a genuine, silent no-match.
Print the value once rather than assuming its casing.

</details>

## Lab 2 — Intermediate

**Task:** List repo runners with `gh api` and read their labels and status.

<details>
<summary>Show solution</summary>

```yaml
name: Runner Inventory

on:
  workflow_dispatch:
  schedule:
    - cron: "0 6 * * 1"     # Monday 06:00 UTC -- a weekly inventory

permissions:
  contents: read

jobs:
  inventory:
    name: List self-hosted runners
    runs-on: ubuntu-latest
    timeout-minutes: 5
    env:
      # Listing runners needs repository administration rights, which the default
      # GITHUB_TOKEN is not given. Supply a token that has them.
      GH_TOKEN: ${{ secrets.RUNNER_ADMIN_TOKEN }}
    steps:
      - name: List runners with labels and status
        run: |
          gh api "repos/${{ github.repository }}/actions/runners" \
            --jq '.runners[] | {name: .name, status: .status, busy: .busy, labels: [.labels[].name]}'

      - name: Fail if any runner is offline
        run: |
          offline="$(gh api "repos/${{ github.repository }}/actions/runners" \
            --jq '[.runners[] | select(.status != "online") | .name] | join(", ")')"
          if [ -n "$offline" ]; then
            echo "::error::Offline runners: ${offline}"
            exit 1
          fi
          echo "All registered runners are online."
```

Output for a healthy pool looks like:

```json
{"busy":false,"labels":["self-hosted","Windows","X64","server1"],"name":"server1","status":"online"}
{"busy":true,"labels":["self-hosted","Windows","X64","server2"],"name":"server2","status":"online"}
```

**Why this works.** `gh` reads its credentials from `GH_TOKEN`, so putting the
token in `env` is all the authentication needed — no `gh auth login` step. `--jq`
filters server-side output down to the three fields that matter, and the second
step turns the inventory into a check: an offline runner becomes a failing
scheduled job instead of a surprise on the next release night. Note that
`status` is the API's `online`/`offline` string, while the UI's **Idle** and
**Active** correspond to `busy: false` and `busy: true`.

**Verify the failure mode the lab asks for.** Swap the token for the default one
(`GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}`) and re-run. The call fails with HTTP
403 and `gh` reports that the resource is not accessible by integration — the
self-hosted runner endpoints require repository administration rights that the
automatically provided token does not carry, no matter what you put in
`permissions:`. The org-level endpoint
(`orgs/your-org/actions/runners`) fails the same way and additionally needs
organisation-level admin rights.

**Common wrong answer.** Reaching for `curl` with a hand-built
`Authorization: Bearer` header. It works, but it also reintroduces every detail
`gh` already handles — API version header, pagination, error surfacing — and the
usual result is a script that silently succeeds on an error body. If you do use
`curl`, add `--fail-with-body`, or you will parse `{"message":"Not Found"}` as an
empty runner list and report the pool healthy.

</details>

## Lab 3 — Challenge

**Task:** Register a self-hosted runner with labels and target it with composite
`runs-on`.

<details>
<summary>Show solution</summary>

Compare your answer with the shipped example,
[`module-06-runner-setup.yml`](../examples/module-06-runner-setup.yml).

Register the runner, giving it one label per axis you will ever want to select on
— role, OS, and machine identity:

```powershell
# On the Windows machine, from the extracted runner folder.
./config.cmd --url https://github.com/your-org/your-repo `
  --token YOUR_REGISTRATION_TOKEN `
  --name server1 `
  --labels self-hosted,windows,server1 `
  --unattended

# Install as a service so it survives logout and reboot.
./svc.cmd install
./svc.cmd start
Get-Service "actions.runner.*" | Select-Object Name, Status
```

Then target it:

```yaml
name: Self-Hosted Health Check

on:
  workflow_dispatch:
    inputs:
      server:
        description: "Which server to check."
        type: choice
        options: [server1, server2, server3, server4]
        default: server1

# One check per machine at a time; a queued second check is fine, a cancelled
# one would leave you without an answer.
concurrency:
  group: runner-health-${{ inputs.server }}
  cancel-in-progress: false

jobs:
  verify-self-hosted:
    name: Verify ${{ inputs.server }}
    # ALL labels must be present on one runner. The input supplies the last one.
    runs-on: [self-hosted, windows, "${{ inputs.server }}"]
    timeout-minutes: 10
    steps:
      - name: Report identity
        shell: powershell
        run: |
          Write-Host "Runner name : $env:RUNNER_NAME"
          Write-Host "Runner OS   : $env:RUNNER_OS"
          Write-Host "Workspace   : $env:GITHUB_WORKSPACE"

      - name: Check out the suite
        uses: actions/checkout@v7

      - name: Confirm the Python toolchain is present
        shell: powershell
        run: |
          python --version
          python -m pip --version
```

**Why this works.** The label list is an AND, so `[self-hosted, windows, server1]`
resolves to exactly one machine while still reading as a description of what that
machine must be. Keeping `self-hosted` and `windows` in the list is not
redundancy — it is what stops the job from landing on a future Linux runner that
someone labels `server1`. The interpolated element is quoted because a bare `${{
}}` as a YAML sequence item is fragile to read and to lint; quoting makes it
unambiguously a string.

**Verify the failure mode the lab asks for.** Change the last label to a machine
that does not exist — `runs-on: [self-hosted, windows, server9]` — and dispatch.
The run is created, the job never starts, and the job page reports that it is
waiting for a runner to pick it up, listing the labels it is looking for. There
is no error and no timeout on the *queueing* itself; `timeout-minutes` only starts
counting once the job is running. Stop the runner service
(`./svc.cmd stop`) and re-run with the correct label to see the same symptom from
the other direction: the runner shows **Offline** in **Settings > Actions >
Runners** while the job waits.

**Common wrong answer.** Writing `runs-on: self-hosted, windows, server1` without
brackets. YAML parses that as one label whose text is the whole comma-separated
string, no runner carries a label with commas in it, and the job queues forever —
with the same "waiting for a runner" symptom as a genuine label mismatch, which is
why it takes so long to spot. The second frequent mistake is targeting the
runner's `--name` instead of a label: the name identifies the registration in the
UI and API, but only labels are matched by `runs-on`, so `runs-on: [self-hosted,
windows, server1]` works because `server1` was passed to `--labels`, not because
it was passed to `--name`.

</details>

---

[Solutions Index](./README.md) | [Module 6](../modules/module-06-runner-setup.md) | [Course Home](../README.md)
