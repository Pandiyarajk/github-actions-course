# Module 15: Automated Testing Pipelines

![Module](https://img.shields.io/badge/Module-15-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20B%20Applied-8957e5?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-120%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 14](./module-14-matrix-and-reuse.md) | [Next: Module 16](./module-16-docker-performance.md)
> Level: **Intermediate** | Time: **120 min** | Example workflow: [`module-15-multi-language-tests.yml`](../examples/module-15-multi-language-tests.yml)
> Solutions: [`module-15-solutions.md`](../solutions/module-15-solutions.md)

## Learning Objectives

- Design fast pull request test pipelines for Python automation.
- Separate static analysis, API, BDD smoke, and UI test layers.
- Publish test evidence with Allure and JUnit-style artifacts.

## Key Concepts

test layers, Allure reports, artifacts, fail-fast feedback, flaky tests

## Expected Outcome

You can build Python test pipelines that give developers and QA useful feedback.

## Concept Flow

```text
Pull Request -> Install Dependencies -> Static Analysis (pylint) -> API Tests (behave @api) -> BDD Smoke (behave @smoke) -> Allure Report -> PR Status
```

---

## ELI5 Explanation

Automated tests are quality gates. GitHub Actions runs them every time code changes so bugs are caught before humans review or deploy the code.

## Technical Explanation

Testing workflows install Python dependencies, run test commands, publish reports, upload artifacts, and fail the pipeline when tests fail. Instead of splitting by language, a Python automation project splits by LAYER: static analysis (pylint, duplicate checks), API tests (Behave with `@api` tags), BDD smoke (Behave with `@smoke` tags), and Selenium UI tests, all reporting through Allure (`allure-behave`).

## Real-World Use Case

A pull request should not merge unless pylint passes, API behave scenarios pass, and the Selenium BDD smoke suite passes across chrome, firefox, and msedge.

## When To Use

- You want fast feedback on every pull request.
- You need regression protection for your Behave/Selenium suites.
- You want QA evidence stored as Allure artifacts.

## When NOT To Use

- The tests are slow and better suited for nightly runs.
- The test environment is unstable.
- The cost outweighs the signal.

## Common Mistakes

- Running behave without installing dependencies.
- Not uploading Allure results when tests fail.
- Combining all test layers into one huge job.
- Ignoring flaky Selenium tests instead of tracking them.

## Debugging Tips

- Upload Allure results and behave output with `if: always()`.
- Separate fast static checks from slow UI tests.
- Capture Selenium screenshots or logs for failing UI scenarios.
- Use clear job names for each test layer.

## Minimal Workflow Example

```yaml
name: Basic Tests

on: pull_request

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v7
      - name: Setup Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - name: Run sample tests
        run: echo "Use behave, pytest, or your project test command"
```

### YAML Explanation

- `pull_request` gives feedback before merge.
- `checkout` gets the code.
- The test step should be replaced with the project's real behave command.

### Step-by-Step Execution

1. Pull request opens or updates.
2. Workflow checks out the repository.
3. Behave test command runs.
4. Pull request shows pass or fail status.

## Production Workflow Example

```yaml
name: Multi Language Test Pipeline

on:
  pull_request:
    branches:
      - main

permissions:
  contents: read

jobs:
  static-analysis:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v7
      - name: Setup Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip
      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt
      - name: Run pylint
        run: pylint your-solution-root-folder-name/
      - name: Check duplicate functions
        run: python your-solution-root-folder-name/scripts/check-duplicate-functions.py
      - name: Check duplicate variables
        run: python your-solution-root-folder-name/scripts/check-duplicate-variables.py

  api-tests:
    runs-on: ubuntu-latest
    needs: static-analysis
    steps:
      - name: Checkout code
        uses: actions/checkout@v7
      - name: Setup Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip
      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt
      - name: Run API behave scenarios
        run: behave your-solution-root-folder-name/features --tags=@api -f allure_behave.formatter:AllureFormatter -o reports/allure-results --junit
      - name: Upload API reports
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: api-reports
          path: reports/

  bdd-smoke:
    runs-on: ubuntu-latest
    needs: static-analysis
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox, msedge]
    steps:
      - name: Checkout code
        uses: actions/checkout@v7
      - name: Setup Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip
      - name: Install dependencies
        run: pip install -r your-solution-root-folder-name/requirements.txt
      - name: Run Selenium BDD smoke (${{ matrix.browser }})
        run: behave your-solution-root-folder-name/features --tags=@smoke -D browser=${{ matrix.browser }} -f allure_behave.formatter:AllureFormatter -o reports/allure-results --junit
      - name: Upload smoke reports
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: smoke-reports-${{ matrix.browser }}
          path: reports/
```

### YAML Explanation

- Each test LAYER gets its own job for clearer failures, all Python/Behave.
- `actions/setup-python@v7` with `cache: pip` installs and caches the toolchain.
- The `bdd-smoke` matrix fans out the Selenium suite across chrome, firefox, and msedge.
- `if: always()` preserves Allure and JUnit reports even when tests fail.

### Expected Output

- Separate jobs for static analysis, API tests, and BDD smoke.
- Allure and JUnit reports upload even when tests fail.
- Pull request clearly shows which layer or browser failed.

## Quiz

1. Why must the Allure upload step carry `if: always()`?
   - **A.** Without it the upload runs before Behave finishes.
   - **B.** A step with no `if:` is skipped once an earlier step in the job has failed — which is exactly the run whose evidence you need.
   - **C.** `always()` compresses the artifact, so the upload is faster.
   - **D.** Artifacts are only retained when the step declares a condition.

2. `behave` fails immediately with `ModuleNotFoundError: No module named 'allure_behave'`, although `behave` itself runs. What is the cause?
   - **A.** The Allure command-line tool is not on `PATH`.
   - **B.** `allure-behave` is not installed — it is a separate package from `behave` and must be in `requirements.txt` or installed explicitly.
   - **C.** `-f allure_behave.formatter:AllureFormatter` is the wrong formatter name in current Behave versions.
   - **D.** The `-o` output directory does not exist yet.

3. `static-analysis` fails on a pylint error. `api-tests` declares `needs: static-analysis`. What happens to `api-tests`?
   - **A.** It runs anyway, because `needs:` only controls ordering.
   - **B.** It is skipped, and the pull request shows it as skipped rather than failed.
   - **C.** It is marked failed without executing any step.
   - **D.** It runs, but its artifacts are discarded.

4. One Selenium scenario fails roughly one run in five for timing reasons. A teammate proposes `continue-on-error: true` on the `bdd-smoke` job. Explain what that actually does to the pull request signal, and describe a better handling of a known-flaky scenario.

5. Three matrix legs each produce Allure results. Describe how to name the uploads so they do not collide, and how a later job collects all three into one report.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add a workflow that runs one behave command. | Test job appears on pull requests. |
| Intermediate | Upload an Allure results artifact. | Artifact is available after workflow run. |
| Challenge | Split static analysis, API, and BDD smoke into separate jobs with a browser matrix. | Each test layer has its own check. |

Solutions: [`solutions/module-15-solutions.md`](../solutions/module-15-solutions.md)

---

[Previous: Module 14](./module-14-matrix-and-reuse.md) | [Module Index](./README.md) | [Next: Module 16](./module-16-docker-performance.md)
