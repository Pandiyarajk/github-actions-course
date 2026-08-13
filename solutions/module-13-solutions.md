# Module 13 — Solutions

![Module](https://img.shields.io/badge/Module-13-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 13](../modules/module-13-secrets-security.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** Masking is a *log filter*. The runner registers each secret value and
replaces exact occurrences of it in the log stream with `***`. That is all it
does. It does not stop a step from reading the value, writing it to a file,
posting it to an endpoint, or defeating the filter by transforming it — a step
that base64-encodes or reverses a secret before printing produces output the
filter no longer recognises. **A** is the dangerous misreading: every step in the
job can read any secret exposed to it. **D** is equally wrong; the runner has
outbound network access and the secret exists in plaintext in the process
environment. The real control is not masking but scope — which secrets a job can
see at all (see Lab 3), and which third-party code runs in the job
([Module 24](../modules/module-24-supply-chain-security.md)).

**2 — B.** `GITHUB_TOKEN` is an installation token minted automatically at the
start of each workflow run and invalidated when the run finishes, and its
capabilities come from the `permissions:` block. That is why you never create it
yourself (**A**), why it is not shared across runs (**C**), and why it does not
carry the triggering user's rights (**D**) — a workflow with
`permissions: contents: read` cannot push, even when an admin triggered it.

**3 — B.** An issue title is attacker-controlled text. `${{ ... }}` is
substituted into the script *before* the shell parses it, so a title containing
shell metacharacters becomes shell code — quoting the expression does not help,
because the injected text can close the quote itself. Assigning it under `env:`
puts the value in the process environment instead, where the shell reads it as
data:

```yaml
      - name: Log the issue title safely
        env:
          ISSUE_TITLE: ${{ github.event.issue.title }}
        run: |
          echo "Title: ${ISSUE_TITLE}"
```

**C** is not a fix — `vars` cannot hold per-event data. **D** inverts the risk:
the payload comes *from GitHub* but its contents were typed by whoever opened the
issue.

**4.** What changes is **scope and gating**. A repository secret is readable by
every job in every workflow in the repository, including a job added in a pull
request by anyone with write access. An environment secret is readable only by a
job that declares `environment: production`, and that declaration is what makes
the environment's protection rules apply — required reviewers, a wait timer, and
a branch restriction on which refs may deploy. So the token becomes reachable
from one named job that a human has to release, rather than from anywhere.

What does *not* change: the value is still plaintext in that job's environment,
still visible to any step and any action running in it, and still only masked in
logs. Environment secrets narrow *who can start a job that holds the token*;
they do nothing about *what the job does once it holds it*.

**5.** The rule is sensitivity, not importance: if disclosure of the value causes
harm, it is a secret; if it is merely configuration, it is a variable. `EMAIL_PASS`
authenticates to the SMTP server, so it is a secret. `EMAIL_TO` is a distribution
list — knowing it grants nothing.

The concrete cost of hiding `EMAIL_TO` in a secret is that you lose the ability
to debug it. Secret values are masked in logs, so `echo "Sending to: ${EMAIL_TO}"`
prints `Sending to: ***`, and a typo in the address is invisible in every run
log. Secrets are also write-only in the UI — you cannot read back what is
configured, only overwrite it. A second cost is collateral masking: if the value
is a short common string, the masker will redact that string wherever else it
appears in the log.

## Lab 1 — Beginner

**Task:** Create the `ZEPHYR_SCALE_TOKEN` repository secret and validate that it
exists with a Python assertion — without printing it.

<details>
<summary>Show solution</summary>

Create the secret first: repository **Settings → Secrets and variables → Actions
→ New repository secret**, name `ZEPHYR_SCALE_TOKEN`.

`.github/workflows/verify-secret.yml`:

```yaml
name: Verify Zephyr Token

on: workflow_dispatch

permissions:
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Assert the token is configured
        env:
          # Read once, into the environment. The value never appears in the
          # command line, so it cannot leak through process listings either.
          ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
        run: |
          set +x
          python - <<'PY'
          import os, sys
          token = os.environ.get("ZEPHYR_SCALE_TOKEN", "")
          if not token:
              sys.exit("ZEPHYR_SCALE_TOKEN is not configured")
          print(f"ZEPHYR_SCALE_TOKEN is configured ({len(token)} characters)")
          PY
```

**Why this works.** The assertion tests a property of the value — is it non-empty
— and reports only a derived fact, its length. The secret itself is never an
argument to a command and never reaches stdout. `set +x` disables shell tracing
so the `env` assignment is not echoed, which matters on runners or scripts where
tracing has been switched on.

**Verify the failure mode the lab asks for.** Rename the secret in the repository
settings (or run the workflow from a fork, which receives no secrets) and re-run.
The step fails with your own message:

```
ZEPHYR_SCALE_TOKEN is not configured
```

The lesson is what did *not* happen: referencing a secret that does not exist is
not an error. `${{ secrets.MISSING }}` evaluates to the empty string silently, so
without this assertion the failure would surface much later as an unhelpful HTTP
401 from Zephyr Scale.

**Common wrong answer.** `run: echo "Token is ${{ secrets.ZEPHYR_SCALE_TOKEN }}"`
and calling the `***` in the log proof that it is safe. Two problems. The masking
is incidental, not a design — mask coverage breaks the moment the value is
transformed, split, or written into a filename. And interpolating a secret
directly into `run:` puts it into the rendered script on disk and into the
process's command line, which is the same class of mistake as interpolating
untrusted input (quiz question 3), just with the trust direction reversed.

</details>

## Lab 2 — Intermediate

**Task:** Move the `EMAIL_TO` / `EMAIL_CC` recipient configuration out of secrets
and into repository variables, keeping the credentials as secrets.

<details>
<summary>Show solution</summary>

Define `EMAIL_TO` and `EMAIL_CC` under **Settings → Secrets and variables →
Actions → Variables**, then delete the secrets of the same name so nothing keeps
reading the old source.

```yaml
name: Email Allure Report

on: workflow_dispatch

permissions:
  contents: read

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Show the resolved recipients
        env:
          EMAIL_TO: ${{ vars.EMAIL_TO }}
          EMAIL_CC: ${{ vars.EMAIL_CC }}
        run: |
          echo "Recipients: ${EMAIL_TO}"
          echo "Copied:     ${EMAIL_CC}"

      - name: Send the report
        working-directory: your-solution-root-folder-name/
        env:
          # Credentials stay secret ...
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          # ... routing configuration becomes visible, and therefore debuggable.
          EMAIL_FROM: ${{ vars.EMAIL_FROM }}
          EMAIL_TO: ${{ vars.EMAIL_TO }}
          EMAIL_CC: ${{ vars.EMAIL_CC }}
        run: |
          set +x
          python scripts/send_report.py
```

**Why this works.** `vars` and `secrets` are separate namespaces with separate
storage. Values in `vars` are readable in the UI and unmasked in logs, which is
the entire point for a recipient list: the "Show the resolved recipients" step
prints the real addresses, so a misrouted report is one glance at the log rather
than an investigation. Nothing about the credentials changes.

**Verify the failure mode the lab asks for.** Leave one reference behind as
`${{ secrets.EMAIL_TO }}` after deleting that secret. The run succeeds, the log
line reads `Recipients:` with nothing after it, and `send_report.py` is handed an
empty recipient list. Depending on the script that is either a silent no-op or an
SMTP error about a missing recipient — but never a workflow-level error pointing
at the real cause. Migrating between the two namespaces always risks this,
because both resolve unknown names to the empty string.

**Common wrong answer.** Referencing the variable as `${{ env.EMAIL_TO }}` at
workflow level, or expecting `vars` to be available as an environment variable
without declaring it. `vars` is a context, not an environment; it has to be
mapped through `env:` (or interpolated) before a script can see it. The failure
looks identical to the one above — an empty string, no error.

</details>

## Lab 3 — Challenge

**Task:** Put the reporting job behind a protected `production` environment with
manual approval, and give it environment-scoped secrets.

<details>
<summary>Show solution</summary>

Create the environment under **Settings → Environments → New environment**, name
it `production`, add yourself under **Required reviewers**, restrict deployment
branches to `main`, then add `ZEPHYR_SCALE_TOKEN` and `EMAIL_PASS` as
*environment* secrets.

```yaml
name: Secure Smoke Report

on:
  workflow_dispatch:
  schedule:
    - cron: "0 2 * * 1-5"

permissions:
  contents: read

jobs:
  smoke:
    # Unprotected: runs the tests, holds no production credentials.
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Run Behave smoke suite
        working-directory: your-solution-root-folder-name/
        run: |
          behave --tags=smoke \
            -D base_url=https://your-domain.com \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30

  publish:
    # Protected: this is the only job that can see the production secrets, and it
    # cannot start until a required reviewer releases it.
    needs: smoke
    if: always() && needs.smoke.result != 'cancelled'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt

      - name: Download Allure results
        uses: actions/download-artifact@v8
        with:
          name: allure-results
          path: reports/allure-results

      - name: Publish to Zephyr Scale and email the report
        env:
          ZEPHYR_SCALE_TOKEN: ${{ secrets.ZEPHYR_SCALE_TOKEN }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          EMAIL_TO: ${{ vars.EMAIL_TO }}
        run: |
          set +x
          python your-solution-root-folder-name/scripts/publish_zephyr.py
          python your-solution-root-folder-name/scripts/send_report.py
```

**Why this works.** Splitting the run into an unprotected test job and a
protected publish job is what makes the approval meaningful. Test execution needs
no production credentials, so it should not be blocked on a human; publishing
does, so it is the only job carrying `environment: production`. Because
environment secrets are resolved per job, the `smoke` job cannot read
`ZEPHYR_SCALE_TOKEN` at all — not by mistake, and not by a step someone adds
later. The artifact hand-off (`upload-artifact` → `download-artifact`) is what
lets the two jobs cooperate without sharing a runner. `if: always() && ...` keeps
the publish job reachable when the suite reports failures, since a failing smoke
run is exactly the result worth publishing.

**Verify the failure mode the lab asks for.** Trigger the workflow. `smoke` runs
to completion; `publish` then sits in a **Waiting** state showing "Review
pending" with a **Review deployments** button, and no step in it has executed.
Approve it and it proceeds.

Then reproduce the second, more instructive failure: delete
`environment: production` from the `publish` job but leave the secrets defined at
environment scope. The job now starts immediately with no approval — and
`${{ secrets.ZEPHYR_SCALE_TOKEN }}` is the empty string, because environment
secrets are only injected into a job that declares the environment. The Zephyr
call fails on authentication rather than on configuration, which is why the
explicit secret-validation step from Lab 1 belongs at the top of this job.

**Common wrong answer.** Setting `environment: production` on the *workflow* or
expecting `on: workflow_dispatch` plus a branch filter to provide the gate.
`environment:` is a **job**-level key only; there is no workflow-level equivalent,
and putting it under `on:` or at the top level fails validation. The related
wrong answer is protecting the branch instead of the environment — branch
protection governs what merges, not which run may hold a production credential.

</details>

---

[Solutions Index](./README.md) | [Module 13](../modules/module-13-secrets-security.md) | [Course Home](../README.md)
