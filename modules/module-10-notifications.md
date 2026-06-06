# Module 10: Notifications, Observability, Debugging, and Governance

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 9](./module-09-monorepo-best-practices.md) | [Next: Module 11](./module-11-running-scripts.md)
> Level: **Advanced** | Time: **120 min** | Example workflow: [`module-10-notifications.yml`](../examples/module-10-notifications.yml)

## Learning Objectives

- Create actionable email notifications and run summaries for the QA suites.
- Debug Python/Behave workflows using logs, Allure artifacts, and reruns.
- Apply production governance controls.

## Key Concepts

job summaries, SMTP email notifications, observability, debug logging, governance

## Expected Outcome

You can make desktop/UI and web automation workflows easier to observe, debug, govern, and support in production.

## Concept Flow

```text
QA Workflow Result -> Job Summary -> Allure Artifact Evidence -> SMTP Email Alert -> Debug / Rerun Decision
```

---

## ELI5 Explanation

Notifications tell the QA team what happened on the nightly run. Observability helps you understand why it happened. Governance keeps workflows safe, consistent, and maintainable.

## Technical Explanation

Production workflows should expose clear logs, artifacts, summaries, status notifications, concurrency controls, permissions, branch protections, required checks, and audit-friendly release evidence. These projects DO NOT use Slack or Teams; they send Python SMTP email reports (`smtplib` + `email.mime.multipart.MIMEMultipart`, HTML body) on workflow completion or failure. The notification workflow is decoupled from the test workflow using a `workflow_run` trigger that watches the nightly QA workflow from Module 8. Debugging strategies include grouped logs, step summaries, reruns with debug logging, Allure artifacts, and targeted scenario isolation with Behave tags.

## Real-World Use Case

When the nightly web automation smoke suite fails, the team needs an email to qa-team@your-domain.com with the pass rate, failed Zephyr/Jira IDs, run duration, and a link to the run so they can decide whether to rerun on a healthy `server1..server4` runner or open a defect.

## When To Use

- Failures need immediate QA team attention.
- Nightly Selenium/Behave or TestComplete results must be shared.
- Deployments and regression runs need visibility.
- Multiple teams need shared workflow standards.

## When NOT To Use

- Every successful CI run sends an email to qa-team@your-domain.com.
- The message does not include pass rate, failed IDs, or a run link.
- Teams begin ignoring the report emails.

## Common Mistakes

- Sending email notifications for every successful run.
- Not including a link to the Allure report or the run logs.
- Giving workflows excessive permissions.
- Missing `timeout-minutes` and `concurrency`.

## Debugging Tips

- Enable debug logging using repository secrets `ACTIONS_STEP_DEBUG` and `ACTIONS_RUNNER_DEBUG`.
- Add job summaries using `$GITHUB_STEP_SUMMARY`.
- Upload Behave logs and the Allure results directory as artifacts with `actions/upload-artifact@v7`.
- Use `workflow_dispatch` inputs (tag, environment) to reproduce a failing scenario.

## Minimal Workflow Example

```yaml
name: Workflow Summary

on: workflow_dispatch

jobs:
  summary:
    runs-on: ubuntu-latest
    steps:
      - name: Write job summary
        run: |
          echo "## QA Run Result" >> $GITHUB_STEP_SUMMARY
          echo "Commit: $GITHUB_SHA" >> $GITHUB_STEP_SUMMARY
```

### YAML Explanation

- `$GITHUB_STEP_SUMMARY` writes markdown to the workflow run summary.
- This gives the QA team useful information without opening every log.

### Step-by-Step Execution

1. Workflow starts manually.
2. Step writes markdown to `$GITHUB_STEP_SUMMARY`.
3. GitHub displays the summary in the workflow UI.

## Production Workflow Example

This notification workflow lives in the web automation repository and is triggered by a `workflow_run` that watches the Module 8 nightly QA workflow. It downloads the metrics the QA workflow produced and sends an HTML email via Python `smtplib` (a failure variant and a success variant), using the `EMAIL_*` and `SMTP_*` secrets.

```yaml
name: QA Email Notification

on:
  workflow_run:
    workflows: ["Nightly QA Smoke"]   # name of the Module 8 QA workflow
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
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.13"

      - name: Download QA metrics artifact
        uses: actions/download-artifact@v8
        with:
          name: qa-metrics
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          path: your-solution-root-folder-name/metrics

      - name: Write run summary
        if: always()
        run: |
          echo "## QA Run Summary" >> $GITHUB_STEP_SUMMARY
          echo "- Source workflow: ${{ github.event.workflow_run.name }}" >> $GITHUB_STEP_SUMMARY
          echo "- Conclusion: ${{ github.event.workflow_run.conclusion }}" >> $GITHUB_STEP_SUMMARY
          echo "- Commit: ${{ github.event.workflow_run.head_sha }}" >> $GITHUB_STEP_SUMMARY
          echo "- Run URL: ${{ github.event.workflow_run.html_url }}" >> $GITHUB_STEP_SUMMARY

      - name: Send failure email
        if: ${{ github.event.workflow_run.conclusion == 'failure' }}
        env:
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
          EMAIL_CC: ${{ secrets.EMAIL_CC }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          RUN_URL: ${{ github.event.workflow_run.html_url }}
          HEAD_SHA: ${{ github.event.workflow_run.head_sha }}
          ACTOR: ${{ github.event.workflow_run.actor.login }}
        run: |
          python - <<'PY'
          import os, json, smtplib
          from email.mime.multipart import MIMEMultipart
          from email.mime.text import MIMEText

          metrics = {"pass_rate": "n/a", "failed_ids": [], "duration": "n/a"}
          path = "your-solution-root-folder-name/metrics/metrics.json"
          if os.path.exists(path):
              with open(path) as f:
                  metrics.update(json.load(f))

          failed = ", ".join(metrics["failed_ids"]) or "see Allure report"
          html = f"""
          <h2 style="color:#b00020">Nightly QA Smoke FAILED</h2>
          <ul>
            <li><b>Pass rate:</b> {metrics['pass_rate']}</li>
            <li><b>Failed IDs:</b> {failed}</li>
            <li><b>Duration:</b> {metrics['duration']}</li>
            <li><b>Commit:</b> {os.environ['HEAD_SHA']}</li>
            <li><b>Triggered by:</b> {os.environ['ACTOR']}</li>
            <li><b>Run:</b> <a href="{os.environ['RUN_URL']}">{os.environ['RUN_URL']}</a></li>
          </ul>
          <p>Review the Allure report artifact and decide whether to rerun on a healthy runner (server1..server4) or open a defect in Jira.</p>
          """

          msg = MIMEMultipart("alternative")
          msg["Subject"] = "[FAILED] Nightly QA Smoke - Web Automation Suite"
          msg["From"] = os.environ["EMAIL_FROM"]
          msg["To"] = os.environ["EMAIL_TO"]
          msg["Cc"] = os.environ.get("EMAIL_CC", "")
          msg.attach(MIMEText(html, "html"))

          recipients = [r for r in (os.environ["EMAIL_TO"] + "," + os.environ.get("EMAIL_CC", "")).split(",") if r]
          with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as s:
              s.starttls()
              s.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"])
              s.sendmail(os.environ["EMAIL_FROM"], recipients, msg.as_string())
          PY

      - name: Send success email
        if: ${{ github.event.workflow_run.conclusion == 'success' }}
        env:
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          RUN_URL: ${{ github.event.workflow_run.html_url }}
        run: |
          python - <<'PY'
          import os, json, smtplib
          from email.mime.multipart import MIMEMultipart
          from email.mime.text import MIMEText

          metrics = {"pass_rate": "100%", "duration": "n/a"}
          path = "your-solution-root-folder-name/metrics/metrics.json"
          if os.path.exists(path):
              with open(path) as f:
                  metrics.update(json.load(f))

          html = f"""
          <h2 style="color:#1b5e20">Nightly QA Smoke PASSED</h2>
          <ul>
            <li><b>Pass rate:</b> {metrics['pass_rate']}</li>
            <li><b>Duration:</b> {metrics['duration']}</li>
            <li><b>Run:</b> <a href="{os.environ['RUN_URL']}">{os.environ['RUN_URL']}</a></li>
          </ul>
          """

          msg = MIMEMultipart("alternative")
          msg["Subject"] = "[PASSED] Nightly QA Smoke - Web Automation Suite"
          msg["From"] = os.environ["EMAIL_FROM"]
          msg["To"] = os.environ["EMAIL_TO"]
          msg.attach(MIMEText(html, "html"))

          with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as s:
              s.starttls()
              s.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"])
              s.sendmail(os.environ["EMAIL_FROM"], os.environ["EMAIL_TO"].split(","), msg.as_string())
          PY
```

### YAML Explanation

- `workflow_run` watches the named Module 8 QA workflow and runs only after it completes, keeping notification logic out of the test workflow.
- `actions/download-artifact@v8` with `run-id` pulls the `qa-metrics` (pass rate, failed IDs, timing) produced by the QA run.
- `permissions` are scoped to `contents: read` and `actions: read` for governance.
- `concurrency` and `timeout-minutes` are governance controls preventing overlap and runaway jobs.
- The failure and success email steps are guarded by `github.event.workflow_run.conclusion` so success runs do not send noise.
- The inline Python uses `smtplib` + `MIMEMultipart` with an HTML body and the `EMAIL_*`/`SMTP_*` secrets.

### Expected Output

- Workflow summary includes pass rate, conclusion, commit, and run URL.
- Failure email to qa-team@your-domain.com includes pass rate, failed IDs, timing, and a run link.
- Success email is concise and sent only on green runs.
- Job has scoped permissions, concurrency, and timeout protection.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a `$GITHUB_STEP_SUMMARY` block to the QA run. | Summary appears in Actions UI. |
| Intermediate | Add a Python `smtplib` failure email triggered via `workflow_run`. | Email sends on failure only and skips on success. |
| Challenge | Add concurrency, timeout, scoped permissions, and debug notes. | Workflow follows production governance standards. |

---

[Previous: Module 9](./module-09-monorepo-best-practices.md) | [Module Index](./README.md) | [Next: Module 11](./module-11-running-scripts.md)
