# Module 20 — Solutions

![Module](https://img.shields.io/badge/Module-20-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 20](../modules/module-20-notifications.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** Debug logging is switched on outside the workflow file, by setting
`ACTIONS_STEP_DEBUG` (step-level diagnostics) and `ACTIONS_RUNNER_DEBUG` (runner
and job diagnostics) to `true` as repository **secrets or variables**. The
equivalent for a single run is the **Re-run jobs -> Enable debug logging**
checkbox in the UI, which sets the same flags for that run only.

**A** and **C** invent syntax. **D** is the interesting wrong answer: putting
`ACTIONS_STEP_DEBUG: true` in a job's `env:` block looks entirely reasonable and
does nothing, because the runner reads those flags when it starts the job, from
the repository's configuration, not from the workflow's environment. People often
conclude debug logging is broken.

**2 — B.** `workflow_run` is one of the triggers evaluated against the
**default branch's** copy of the workflow file, and the resulting run also
executes that default-branch version against the default branch. A notifier that
exists only on a feature branch is invisible to the trigger, so nothing fires and
there is no error anywhere to explain it. The same rule applies to `schedule`,
and it is why "it works after I merge" is the usual discovery path.

A consequence worth remembering: `github.ref` inside a `workflow_run` job is the
default branch, *not* the branch the watched run tested. Use
`github.event.workflow_run.head_sha` and `head_branch` when you need the tested
commit.

**A** is false — `workflow_run` with `types: [completed]` fires on failure and
cancellation too, which is the whole point. **C** is not required; `actions: read`
is what the notifier needs, to read the other run's artifacts. **D** is backwards:
the `workflows:` list matches the workflow's `name:`, not its filename.

**3 — B.** The artifact belongs to a different workflow run, so
`download-artifact` must be told which run to look in and given a token with
`actions: read`:

```yaml
      - uses: actions/download-artifact@v8
        with:
          name: qa-metrics
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          path: your-solution-root-folder-name/metrics
```

Without `run-id`, the action looks only in the *current* run — which uploaded
nothing — and fails to find the artifact. **A** is a reasonable-sounding
assumption with no mechanism behind it; artifacts are scoped to runs, not commits.
**C** solves a different problem (reassembling several artifacts matched by
`pattern`). **D** is impossible: you cannot re-upload what you have not yet
downloaded.

**4.** An actionable notification answers "what do I do now?" without opening
anything else. Concretely it carries: the conclusion, the pass rate, the
identifiers of what failed (Zephyr/Jira IDs or scenario names), the duration, the
commit, and a clickable link to the run and its Allure artifact. A notification
that says only "build failed" is a request to go and do research, which is why
those get filtered into a folder nobody opens.

Equally important is *when* it sends. Every green run emailing the team is how a
channel dies. Guard on the watched run's conclusion:

```yaml
      - name: Send failure email
        if: ${{ github.event.workflow_run.conclusion == 'failure' }}
        run: python your-solution-root-folder-name/scripts/send_report.py --status failure
```

A concise success email is defensible for a nightly run, where silence is
ambiguous — you cannot tell "all green" from "the scheduler never fired". If you
send one, make it plainly distinguishable in the subject line so the failure mail
still stands out.

**5.** Read the evidence you already have before you spend a re-run:

1. **The job summary** (`$GITHUB_STEP_SUMMARY`) — pass rate, conclusion, commit,
   run URL. No re-run.
2. **The failing step's log**, jumping to the failure via the group markers. No
   re-run.
3. **The Allure results artifact** — per-scenario status, the failing step, the
   stack trace, and any attached page source. No re-run.
4. **The failure screenshot artifact** — for a Selenium failure this is usually
   decisive, showing the modal, banner, or empty grid the locator hit. No re-run.
5. **The runner's identity** in the log (`RUNNER_NAME`) — the same scenario
   failing only on one of `server1`..`server4` points at the machine, not the
   test. No re-run.
6. **Re-run with debug logging enabled** — needs a re-run, and only now, because
   it is the first step that costs the suite's full runtime and can produce a
   different outcome on a flaky failure.
7. **Re-run a narrowed scenario** via `workflow_dispatch` inputs, with a Behave
   tag isolating the one feature. Needs a re-run, but a cheap one.

The order is the lesson: steps 1-5 read artifacts the original run already
produced, which is exactly why the run must upload them with `if: always()`. Teams
that skip straight to "re-run it and see" lose the original failure — on a flaky
scenario the re-run passes and the evidence is gone.

## Lab 1 — Beginner

**Task:** Add a `$GITHUB_STEP_SUMMARY` block to the QA run so a summary appears
in the Actions UI.

<details>
<summary>Show solution</summary>

```yaml
name: QA Run Summary

on: workflow_dispatch

permissions:
  contents: read

jobs:
  summary:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Write job summary
        if: always()
        env:
          BROWSER: chrome
        run: |
          {
            echo "## QA Run Result"
            echo ""
            echo "| Field | Value |"
            echo "| --- | --- |"
            echo "| Conclusion | ${{ job.status }} |"
            echo "| Browser | ${BROWSER} |"
            echo "| Commit | \`${GITHUB_SHA}\` |"
            echo "| Triggered by | ${GITHUB_ACTOR} |"
            echo "| Run | ${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID} |"
          } >> "$GITHUB_STEP_SUMMARY"
```

**Why this works.** `$GITHUB_STEP_SUMMARY` is a file path; anything you append is
rendered as GitHub-flavoured Markdown at the top of the run page. Grouping the
echoes in a `{ ... } >> "$GITHUB_STEP_SUMMARY"` block redirects once instead of
per line, which keeps the block readable and makes an accidental `>` (truncate)
instead of `>>` (append) a single visible mistake rather than a scattered one.
`if: always()` means the summary is written for failed runs too — the runs where
it matters.

**Verify the failure mode the lab asks for.** Change `>>` to `>` and add a second
summary step. Only the last write survives, because `>` truncates the file each
time — the earlier sections vanish with no warning. Then remove the quotes around
`"$GITHUB_STEP_SUMMARY"`: it still works here, but it breaks the moment the
runner's workspace path contains a space, which is common on Windows
self-hosted runners under `C:\actions-runner\_work`.

**Common wrong answer.** Using `echo "..." >> $GITHUB_STEP_SUMMARY` with a
`${{ }}` expression placed at **column 0** inside the `run: |` block. That
terminates the block scalar and the workflow fails to parse — the error points at
YAML syntax, not at the line you edited. Keep expressions indented, or better,
pass values through `env:` and reference shell variables.

</details>

## Lab 2 — Intermediate

**Task:** Add a Python `smtplib` failure email triggered via `workflow_run`, so
it sends on failure only and skips on success.

<details>
<summary>Show solution</summary>

The finished workflow is
[`module-20-notifications.yml`](../examples/module-20-notifications.yml).

`.github/workflows/qa-notify.yml` — on the **default branch**:

```yaml
name: QA Email Notification

on:
  workflow_run:
    workflows: ["Nightly QA Automation"]   # the watched workflow's `name:`
    types:
      - completed

permissions:
  contents: read
  actions: read

concurrency:
  group: qa-notify-${{ github.event.workflow_run.id }}
  cancel-in-progress: false

jobs:
  notify:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Download the watched run's metrics
        # The artifact belongs to ANOTHER run, hence run-id + github-token.
        uses: actions/download-artifact@v8
        with:
          name: qa-metrics
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          path: your-solution-root-folder-name/metrics

      - name: Write run summary
        if: always()
        env:
          SOURCE: ${{ github.event.workflow_run.name }}
          CONCLUSION: ${{ github.event.workflow_run.conclusion }}
          HEAD_SHA: ${{ github.event.workflow_run.head_sha }}
          RUN_URL: ${{ github.event.workflow_run.html_url }}
        run: |
          {
            echo "## QA Run Summary"
            echo "- Source workflow: ${SOURCE}"
            echo "- Conclusion: ${CONCLUSION}"
            echo "- Commit: ${HEAD_SHA}"
            echo "- Run URL: ${RUN_URL}"
          } >> "$GITHUB_STEP_SUMMARY"

      - name: Send failure email
        if: ${{ github.event.workflow_run.conclusion == 'failure' }}
        env:
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          RUN_URL: ${{ github.event.workflow_run.html_url }}
          HEAD_SHA: ${{ github.event.workflow_run.head_sha }}
        run: |
          python - <<'PY'
          import json
          import os
          import smtplib
          from email.mime.multipart import MIMEMultipart
          from email.mime.text import MIMEText

          metrics = {"pass_rate": "n/a", "failed_ids": [], "duration": "n/a"}
          path = "your-solution-root-folder-name/metrics/metrics.json"
          if os.path.exists(path):
              with open(path, encoding="utf-8") as handle:
                  metrics.update(json.load(handle))

          failed = ", ".join(metrics["failed_ids"]) or "see the Allure artifact"
          html = f"""
          <h2 style="color:#b00020">Nightly QA FAILED</h2>
          <ul>
            <li><b>Pass rate:</b> {metrics['pass_rate']}</li>
            <li><b>Failed IDs:</b> {failed}</li>
            <li><b>Duration:</b> {metrics['duration']}</li>
            <li><b>Commit:</b> {os.environ['HEAD_SHA']}</li>
            <li><b>Run:</b> <a href="{os.environ['RUN_URL']}">open the run</a></li>
          </ul>
          <p>Check the Allure artifact, then rerun on a healthy runner
          (server1..server4) or raise a defect in Jira.</p>
          """

          msg = MIMEMultipart("alternative")
          msg["Subject"] = "[FAILED] Nightly QA - web automation suite"
          msg["From"] = os.environ["EMAIL_FROM"]
          msg["To"] = os.environ["EMAIL_TO"]
          msg.attach(MIMEText(html, "html"))

          with smtplib.SMTP(os.environ["SMTP_HOST"],
                            int(os.environ["SMTP_PORT"]), timeout=30) as server:
              server.starttls()
              server.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"])
              server.sendmail(os.environ["EMAIL_FROM"],
                              os.environ["EMAIL_TO"].split(","),
                              msg.as_string())
          PY
```

**Why this works.** Decoupling matters: the test workflow's job is to test, and a
broken SMTP configuration must not turn a green suite red. The `workflow_run`
trigger gives the notifier its own run with its own permissions, and
`github.event.workflow_run.conclusion` is what makes the send conditional so
green runs are silent. Every value the Python needs arrives through `env:`, so
nothing is interpolated into the source text — a metrics field containing a quote
cannot break the script, and the quoted heredoc (`<<'PY'`) stops the shell
expanding anything either. `timeout=30` on the SMTP connection keeps a
non-responding mail server from consuming the whole job budget.

The email body is built to be actionable per quiz question 4: pass rate, failed
IDs, duration, commit, and a link — enough to decide "rerun" versus "raise a
defect" from a phone.

**Verify the failure mode the lab asks for.** Create the notifier on a feature
branch and let the nightly workflow complete. Nothing happens: no run appears,
no error is logged anywhere, because `workflow_run` is read from the default
branch's copy of the file. Merge it and the same completion fires the notifier.
Second thing to reproduce: change `workflows: ["Nightly QA Automation"]` to the
*filename* (`["nightly-qa.yml"]`). Again nothing fires — the list matches the
`name:` field. Both failures are silent, which is what makes them expensive.

**Common wrong answer.** Omitting `run-id` from `download-artifact`, on the
assumption that the notifier can see the artifacts of the run that triggered it.
It cannot: the download defaults to the current run, which uploaded nothing, and
the step fails with the artifact not found. The related miss is dropping
`actions: read` from `permissions` — with `run-id` correct but the scope missing,
the API call is refused instead.

</details>

## Lab 3 — Challenge

**Task:** Add concurrency, timeout, scoped permissions, and debug notes so the
workflow meets production governance standards.

<details>
<summary>Show solution</summary>

Take the Lab 2 notifier and add the governance layer.

```yaml
name: QA Email Notification

on:
  workflow_run:
    workflows: ["Nightly QA Automation"]
    types:
      - completed

# Least privilege at the TOP level: everything inherits this unless a job
# widens it. `actions: read` is the minimum needed to read another run's
# artifacts; nothing here needs write access to anything.
permissions:
  contents: read
  actions: read

# One notifier per watched run. Keyed on the run id rather than the ref,
# because the ref is always the default branch under `workflow_run` and would
# serialise unrelated notifications behind each other.
concurrency:
  group: qa-notify-${{ github.event.workflow_run.id }}
  cancel-in-progress: false

# Governance notes for future maintainers:
#
#   Debug logging is NOT configured here. Set the repository secrets or
#   variables ACTIONS_STEP_DEBUG=true and ACTIONS_RUNNER_DEBUG=true, or use
#   "Re-run jobs -> Enable debug logging" for a single run. Putting these in a
#   job `env:` block has no effect -- the runner reads them from repository
#   configuration when the job starts.
#
#   Under `workflow_run`, `github.ref` is the DEFAULT branch, not the branch
#   that was tested. Use `github.event.workflow_run.head_sha` and
#   `.head_branch` for anything that must describe the tested commit.
#
#   Secrets are masked in logs, but only when printed verbatim. Never echo a
#   secret, and never build a URL that embeds one.

jobs:
  notify:
    runs-on: ubuntu-latest
    # Hard stop: a hung SMTP connection must not hold a runner for six hours,
    # which is the default job limit.
    timeout-minutes: 10
    steps:
      - name: Checkout code
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Download the watched run's metrics
        id: metrics
        continue-on-error: true
        uses: actions/download-artifact@v8
        with:
          name: qa-metrics
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          path: your-solution-root-folder-name/metrics

      - name: Group the diagnostic context
        env:
          CONCLUSION: ${{ github.event.workflow_run.conclusion }}
          HEAD_BRANCH: ${{ github.event.workflow_run.head_branch }}
          HEAD_SHA: ${{ github.event.workflow_run.head_sha }}
          METRICS_OUTCOME: ${{ steps.metrics.outcome }}
        run: |
          echo "::group::Notification context"
          echo "conclusion=${CONCLUSION}"
          echo "head_branch=${HEAD_BRANCH}"
          echo "head_sha=${HEAD_SHA}"
          echo "metrics download outcome=${METRICS_OUTCOME}"
          echo "runner=${RUNNER_NAME}"
          echo "::endgroup::"

      - name: Warn when metrics are missing
        if: ${{ steps.metrics.outcome != 'success' }}
        run: |
          echo "::warning title=Metrics missing::The watched run uploaded no qa-metrics artifact; the email will fall back to defaults."

      - name: Write run summary
        if: always()
        env:
          CONCLUSION: ${{ github.event.workflow_run.conclusion }}
          HEAD_SHA: ${{ github.event.workflow_run.head_sha }}
          RUN_URL: ${{ github.event.workflow_run.html_url }}
        run: |
          {
            echo "## QA Run Summary"
            echo ""
            echo "| Field | Value |"
            echo "| --- | --- |"
            echo "| Conclusion | ${CONCLUSION} |"
            echo "| Commit | \`${HEAD_SHA}\` |"
            echo "| Run | ${RUN_URL} |"
          } >> "$GITHUB_STEP_SUMMARY"

      - name: Send failure email
        if: ${{ github.event.workflow_run.conclusion == 'failure' }}
        env:
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          RUN_URL: ${{ github.event.workflow_run.html_url }}
          HEAD_SHA: ${{ github.event.workflow_run.head_sha }}
        run: |
          python your-solution-root-folder-name/scripts/send_report.py \
            --metrics your-solution-root-folder-name/metrics/metrics.json \
            --status failure
```

**Why this works.** Four governance controls, each answering a specific failure:

- **`permissions` at the top level, read-only.** The notifier reads another run's
  artifacts and nothing more. Scoping at the workflow level means a future job
  added to this file starts least-privileged rather than inheriting write access
  somebody granted years earlier for a different reason.
- **`timeout-minutes: 10`.** The default job limit is six hours. A mail server
  that accepts the TCP connection and then never responds would hold a runner for
  that long, and the run would eventually report a timeout with no useful log.
- **`concurrency` keyed on the watched run id.** Two notifications for two
  different QA runs are unrelated and should not queue behind each other, so the
  key is the run id, not the ref — under `workflow_run` the ref is always the
  default branch and would collapse everything into one group.
  `cancel-in-progress: false` because a half-sent notification is worse than a
  late one.
- **Debug notes as comments.** The `ACTIONS_STEP_DEBUG` / `ACTIONS_RUNNER_DEBUG`
  mechanism lives in repository settings, so the workflow file is the only place
  a maintainer will look and find nothing. Recording *where* the switch is, and
  that a job-level `env:` does not work, saves the next person the hour it cost
  you.

`continue-on-error: true` plus `steps.metrics.outcome` is the pattern for an
optional input: a missing artifact degrades the email rather than suppressing it,
and `::warning title=...::` surfaces the degradation on the run page instead of
burying it. `::group::` collapses the diagnostic block so it is available without
crowding the log.

**Verify the failure mode the lab asks for.** Three checks:

1. Delete `timeout-minutes` and point `SMTP_HOST` at a host that accepts
   connections but never replies. The job hangs; with `timeout=30` in the Python
   it recovers, without it the run sits until the six-hour default kills it. The
   log ends mid-step with no error, which is why both timeouts exist.
2. Set `ACTIONS_STEP_DEBUG: true` in the job's `env:` block and re-run. The log
   is unchanged — no `::debug::` lines appear. Now set it as a repository variable
   and re-run: the debug lines appear. Same value, different place, completely
   different result.
3. Change `permissions` to `contents: read` only, dropping `actions: read`. The
   `download-artifact` step fails on the API call for the other run's artifacts,
   and because of `continue-on-error: true` the job *continues* and emails with
   fallback values — a degraded notification that looks fine. That is the
   argument for the explicit warning annotation.

**Common wrong answer.** Adding `permissions: write-all` "to make the artifact
download work". It does make it work, and it hands a token with write access to
contents, issues, packages, and deployments to a job whose only purpose is
sending mail. The correct scope is `actions: read`. The second frequent error is
`cancel-in-progress: true` on the notifier, reasoning by analogy with pull-request
workflows: here it means a burst of completions cancels notifications for runs
that already failed, so the failure nobody hears about is the one that arrived
second.

</details>

---

[Solutions Index](./README.md) | [Module 20](../modules/module-20-notifications.md) | [Course Home](../README.md)
