# CI Quality Gates and Build Artifacts

> Level: **Intermediate** | Suggested modules: **Module 5, Module 6, Module 7**

## 1. Title

CI Quality Gates and Build Artifacts for `sample-app`

## 2. What This Workflow Does

This case study teaches how to validate code quality, run lightweight custom checks, package build outputs, and preserve artifacts. It generalizes several production patterns into one public-safe learning scenario:

- Python static analysis.
- Pre-commit checks.
- Custom file validation.
- Windows packaging.
- Firmware or binary artifact upload.

Real-world scenario: a team wants every pull request to catch common quality problems while also providing manual build workflows for release candidates.

## 3. When to Use This

- Use it for pull request quality gates.
- Use it when changed files should control which checks run.
- Use it when builds produce downloadable artifacts.
- Use it when release candidates need repeatable packaging.

## 4. Workflow Breakdown

- **Trigger (`on`)**: `pull_request` runs validation before merge; `workflow_dispatch` supports manual builds.
- **Jobs**: Separate quality checks from artifact builds so logs and failures are clear.
- **Steps**: Checkout, setup runtime, install tools, detect changed files, run checks, build artifacts, upload results.
- **Actions used**: `actions/checkout`, `actions/setup-python`, `actions/upload-artifact`.
- **Conditions**: Run file-specific checks only when matching files changed.
- **Outputs**: Changed-file lists, build folders, reports, and packaged artifacts.

## 5. ASCII Flow Diagram

```text
Code Change
   |
   v
Pull Request Trigger
   |
   v
Detect Changed Files
   |
   +--> Python Formatting / Lint
   +--> JSON Validation
   +--> Script Checks
   |
   v
Optional Manual Build
   |
   v
Upload Artifact
```

## 6. Simple Version YAML

```yaml
name: Basic Quality Gate

on:
  pull_request:

permissions:
  contents: read

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install tools
        run: pip install black flake8

      - name: Check formatting
        run: black --check .

      - name: Run lint
        run: flake8 .
```

## 7. Production Version YAML

```yaml
name: Quality Gate and Artifact Build

on:
  pull_request:
    branches:
      - main
  workflow_dispatch:
    inputs:
      build_artifact:
        description: "Build release artifact"
        type: boolean
        default: false

permissions:
  contents: read

jobs:
  quality:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install quality tools
        run: pip install black flake8 pylint detect-secrets

      - name: Determine changed files
        id: changes
        shell: bash
        run: |
          git fetch origin main:main
          git diff --name-only main...HEAD > changed-files.txt
          cat changed-files.txt

      - name: Run Python formatting
        if: hashFiles('**/*.py') != ''
        run: black --check .

      - name: Run Python lint
        if: hashFiles('**/*.py') != ''
        run: flake8 .

      - name: Validate JSON files
        shell: bash
        run: |
          files=$(grep -E '\.json$' changed-files.txt || true)
          for file in $files; do
            python -m json.tool "$file" > /dev/null
          done

      - name: Scan for committed secrets
        run: detect-secrets scan --all-files

      - name: Upload quality evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: quality-evidence
          path: changed-files.txt

  build:
    if: github.event_name == 'workflow_dispatch' && inputs.build_artifact == true
    runs-on: windows-latest
    timeout-minutes: 30
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install build tool
        run: pip install pyinstaller

      - name: Build sample executable
        shell: pwsh
        run: |
          pyinstaller --onefile tools/sample-tool/main.py --name sample-tool --distpath dist/sample-tool

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: sample-tool-${{ github.run_number }}
          path: dist/sample-tool/**
          retention-days: 30
```

## 8. Line-by-Line Explanation

- `pull_request` protects `main` before merge.
- `workflow_dispatch` adds a manual build path without forcing every PR to build artifacts.
- `permissions: contents: read` keeps the default token limited.
- `fetch-depth: 0` allows branch comparison.
- `setup-python` with `cache: pip` speeds repeated installs.
- `changed-files.txt` makes custom checks easier to debug.
- `hashFiles('**/*.py')` avoids Python checks in repositories without Python files.
- `if: always()` preserves evidence when a check fails.
- The Windows build job runs only when manually requested.
- Artifact names include `github.run_number` for traceability.

## 9. Common Mistakes

- Running expensive checks for every file type on every change.
- Using shallow checkout when branch comparison is required.
- Uploading the entire workspace instead of the build output.
- Packaging secrets, certificates, or real environment files into artifacts.
- Making manual release builds run on every pull request.

## 10. Debugging Guide

- Print `changed-files.txt` to verify the diff base.
- Run lint commands locally with the same versions.
- Add `ls` or `Get-ChildItem` before artifact upload.
- Download the artifact and inspect its contents.
- Check the event type when an `if:` condition does not behave as expected.

## 11. Exercises

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add Black and flake8 to a PR workflow. | PR check fails when formatting or linting fails. |
| Intermediate | Validate only changed JSON files. | JSON validation runs only when JSON files changed. |
| Challenge | Add a manual Windows artifact build. | Manual run uploads a named artifact. |

---

[Case Study Index](README.md) | [Course Home](../README.md)
