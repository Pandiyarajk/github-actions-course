# Module 17: Artifacts — Uploading Files, Folders, Retention, and Conditions

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 16](./module-16-env-and-secrets.md) | [Next: Module 18](./module-18-misc-features.md)
> Level: **Beginner** | Time: **120 min** | Example workflow: [`module-17-artifacts.yml`](../examples/module-17-artifacts.yml)

## Learning Objectives

- Upload a single file, a folder, or multiple paths as artifacts.
- Control how long artifacts are kept with `retention-days`.
- Understand that artifacts download as a `.zip` and tune `compression-level`.
- Upload conditionally with `if: success()`, `if: always()`, and `if: failure()`.
- Produce multiple artifacts from one job and handle missing files.

## Key Concepts

`actions/upload-artifact@v7`, `path`, `retention-days`, `compression-level`, `if-no-files-found`, `if:` conditions, multiple uploads

## Expected Outcome

You can save test evidence (Allure results, screenshots, logs) reliably, keep it for the right duration, and capture it even when a run fails.

## Concept Flow

```text
Step produces files -> upload-artifact (path + name) -> zipped + stored -> downloadable for retention-days
```

---

## ELI5 Explanation

An artifact is a box you pack at the end of a run so you can open it later. You choose what goes in (a file, a folder, or several paths), how long the box is kept, and whether to pack it even when the run failed (so you still have the evidence).

## Technical Explanation

`actions/upload-artifact` saves files from the runner to GitHub storage. `path` accepts a single file, a folder (structure preserved), or multiple lines with globs. `name` is the artifact name; downloads always arrive as `name.zip`. `retention-days` sets how long GitHub keeps it (repository default, up to 90 days). `compression-level` (0–9) trades speed for size. `if-no-files-found` chooses `error`/`warn`/`ignore` when nothing matches. Because each upload is its own step, you can produce several artifacts per job and gate each with `if:` — `success()` (default behavior), `always()` (even on failure), or `failure()` (only on failure). Use `always()` for evidence you must keep regardless of outcome.

## Real-World Use Case

A nightly BDD job uploads the Allure results folder for 30 days, the screenshots folder with high compression, and — using `if: always()` — the run logs even when scenarios fail, so QA can triage failures from the downloaded zip.

## When To Use

- Saving test reports, Allure results, screenshots, and logs.
- Passing build output between jobs (with `download-artifact`).
- Preserving failure evidence with `if: always()` / `if: failure()`.

## When NOT To Use

- Storing secrets, credentials, or `.env` files in artifacts.
- Uploading huge workspaces when only a report folder is needed.
- Long retention for large artifacts that inflate storage cost.

## Common Mistakes

- Expecting a raw folder instead of a `.zip` on download.
- Using only `if: success()` and losing evidence when the run fails.
- Letting `if-no-files-found: error` (the default) fail the step when a path is empty.
- Reusing the same artifact `name` across steps (names must be unique per run).
- Packaging sensitive files into the artifact.

## Options Reference

| Option | Purpose | Values |
| --- | --- | --- |
| `name` | Artifact name (download is `name.zip`) | string, unique per run |
| `path` | File, folder, or multiple paths/globs | single line or `\|` block |
| `retention-days` | How long to keep it | 1–90 (repo default if omitted) |
| `compression-level` | Zip compression | 0 (store) … 9 (smallest); default 6 |
| `if-no-files-found` | When nothing matches | `error` (default), `warn`, `ignore` |
| `overwrite` | Replace an existing artifact of the same name | `true` / `false` |

### Conditional upload patterns

| Condition | Runs when |
| --- | --- |
| (no `if`) | Only if previous steps succeeded |
| `if: success()` | Explicitly only on success |
| `if: always()` | Always, including after failures |
| `if: failure()` | Only when a previous step failed |

## Minimal Workflow Example

```yaml
name: Artifact Basics

on: workflow_dispatch

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - name: Create a report
        run: |
          mkdir -p reports
          echo "passed: 12, failed: 1" > reports/summary.txt

      - name: Upload the report
        uses: actions/upload-artifact@v7
        with:
          name: summary
          path: reports/summary.txt
          retention-days: 7
```

### YAML Explanation

- The first step creates `reports/summary.txt`.
- `upload-artifact` saves it as the `summary` artifact (downloaded as `summary.zip`).
- `retention-days: 7` keeps it for one week.

### Step-by-Step Execution

1. The job creates a report file.
2. The upload step zips and stores it.
3. The artifact appears on the run page for 7 days.

## Production Workflow Example

The full example shows single-file, folder, multi-path, compression, and conditional uploads. See [`module-17-artifacts.yml`](../examples/module-17-artifacts.yml).

### Single File, Folder, and Multiple Paths

```yaml
- name: Upload a single file
  uses: actions/upload-artifact@v7
  with:
    name: behave-command
    path: behave-command.txt

- name: Upload a whole folder
  uses: actions/upload-artifact@v7
  with:
    name: allure-results
    path: reports/allure-results
    retention-days: 30

- name: Upload multiple paths
  uses: actions/upload-artifact@v7
  with:
    name: combined-evidence
    path: |
      reports/**
      behave-command.txt
    retention-days: 7
```

### Compression and Missing Files

```yaml
- name: Upload with max compression
  uses: actions/upload-artifact@v7
  with:
    name: screenshots
    path: reports/screenshots
    compression-level: 9        # 0 (store) .. 9 (smallest)
    if-no-files-found: warn     # error | warn | ignore
    retention-days: 14
```

### Conditional Uploads

```yaml
- name: Upload report on success only
  if: success()
  uses: actions/upload-artifact@v7
  with:
    name: success-report
    path: reports/run.log

- name: Upload evidence always
  if: always()                  # keep evidence even when the run failed
  uses: actions/upload-artifact@v7
  with:
    name: evidence-always
    path: reports/**
    if-no-files-found: ignore

- name: Upload debug bundle on failure
  if: failure()                 # only when something failed
  uses: actions/upload-artifact@v7
  with:
    name: failure-debug
    path: reports/**
```

Pair `if: always()` with a step that has `continue-on-error: true` so the upload runs whether tests passed or failed.

### Notes on Size and Zips

- Every artifact is delivered as a `.zip`; a folder keeps its structure inside.
- Keep artifacts focused (a report folder, not the whole workspace) to stay within storage limits and keep downloads fast.
- Higher `compression-level` produces smaller zips but takes longer to pack.

### Expected Output

- Multiple named artifacts appear on the run page.
- Folder artifacts preserve their internal structure inside the zip.
- On a failed run, `evidence-always` and `failure-debug` are still uploaded; `success-report` is skipped.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Upload a single file with `retention-days: 7`. | Artifact appears and expires in 7 days. |
| Intermediate | Upload a folder and a multi-path artifact in the same job. | Two named artifacts with the right contents. |
| Challenge | Add `if: always()` and `if: failure()` uploads behind a step that can fail. | Evidence uploads on failure; success-only upload is skipped. |

---

[Previous: Module 16](./module-16-env-and-secrets.md) | [Module Index](./README.md) | [Next: Module 18](./module-18-misc-features.md)
