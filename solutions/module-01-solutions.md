# Module 1 — Solutions

![Module](https://img.shields.io/badge/Module-1-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 1](../modules/module-01-ci-foundations.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** GitHub only reads workflow definitions from `.github/workflows/`.
A file in `.github/workflow/`, `.github/actions/`, or a nested subdirectory such
as `.github/workflows/ci/ci.yml` is not a workflow at all — it is an ordinary
file in the repository. There is no error, no warning, and no entry in the
Actions tab, which is what makes this mistake expensive: the YAML is perfectly
valid, it is just in a place nothing reads. A missing `workflow_dispatch` (A) is
irrelevant when no trigger is being read in the first place, there is no
24-hour workflow cache (C), and the filename is free-form (D).

**2 — B.** A **job** declares `runs-on`, so a job is what maps to one runner.
Steps (A) execute sequentially inside that job and share its filesystem — they
cannot pick their own machine. An action (C) is code a step calls. A workflow
(D) can contain many jobs, each on a different runner, so the workflow is not
the owning unit. This distinction is the reason two steps can share a `pip
install` but two jobs cannot without artifacts or a cache.

**3 — C.** Triggers are matched by event, not by file presence. The workflow
declares only `pull_request`, so a bare push to the feature branch matches
nothing. Opening (or pushing to) a pull request whose **target** is `main` is
what fires it. Note the nuance in D: for `pull_request` and `push`, GitHub uses
the workflow file **from the branch where the event happened**, so a workflow on
a feature branch does run for a PR from that branch — it is `schedule` that is
restricted to the default branch (Module 4).

**4.** `run:` executes shell commands on the runner. `uses:` invokes a
pre-packaged action — a directory containing an `action.yml`, referenced either
from a repository (`actions/setup-python@v7`) or from a local path (`./...`).
Both are step-level keys and a single step may use one or the other, never both.

Prefer `uses: actions/setup-python@v7` because it does considerably more than
installing an interpreter: it resolves the version against the runner's tool
cache (so an already-present 3.13 costs seconds, not a download), puts that
exact interpreter first on `PATH` so `python` and `pip` are unambiguous, sets up
`pip` caching when asked, and exposes the resolved version as a step output. A
hand-rolled `run:` block that fetches and builds Python is slower, differs
between runner images, and silently drifts when the image changes.

**5.** `permissions:` sets the scopes on the automatically-provisioned
`GITHUB_TOKEN` that every job receives as `secrets.GITHUB_TOKEN`. Declaring
`contents: read` reduces the token to read-only access to repository contents
and sets **every other scope to `none`** — so a compromised or buggy step cannot
push commits, open or comment on issues, edit pull requests, or publish
packages.

Leaving it out means the token gets the repository's or organisation's default
permission set, which you do not control from the workflow file and which is
permissive (write to contents) in older repositories. Declaring it explicitly
makes the blast radius a property of the workflow you can review in a diff,
rather than a setting somebody may change later. See
[Module 24](../modules/module-24-supply-chain-security.md) for the full
treatment.

## Lab 1 — Beginner

**Task:** Create a workflow that prints your name.

<details>
<summary>Show solution</summary>

`.github/workflows/hello-name.yml`:

```yaml
name: Hello Name

# workflow_dispatch while learning: you can press "Run workflow" instead of
# pushing a commit every time you want to test.
on:
  workflow_dispatch:
  push:

jobs:
  greet:
    runs-on: ubuntu-latest
    steps:
      - name: Print my name
        run: echo "Pandiyaraj Karuppasamy"
```

**Why this works.** The three things GitHub needs are all present: the file is
under `.github/workflows/`, it declares at least one event under `on:`, and it
has at least one job with a `runs-on` and a `steps:` list. Nothing is checked
out because nothing in the job touches the repository — `actions/checkout` is
only needed when a step reads repository files.

**Verify the failure mode the lab asks for.** Move the file to
`.github/hello-name.yml` (or to `.github/workflows/demo/hello-name.yml`),
commit, and push. There is no error anywhere — the Actions tab simply shows no
run, because GitHub never looked at the file. That silence is the lesson: with
workflows, "nothing happened" is a location or trigger problem far more often
than a YAML problem.

A second failure worth reproducing: keep the file in the right place but delete
the `on:` block. Now GitHub *does* read it and reports a load error in the
Actions tab, along the lines of the workflow not being valid because no `on`
key is present. The contrast between the two — silence versus a red error — is
how you learn to tell "not found" from "found and rejected".

**Common wrong answer.** Editing the workflow in the GitHub web editor, seeing
it appear correct, and never committing — or committing to a branch and then
looking at the default branch's Actions history. The workflow that runs is the
one committed on the branch where the event happened.

</details>

## Lab 2 — Intermediate

**Task:** Trigger the workflow on both `push` and `pull_request`, set up Python
3.13, and run `behave --tags=smoke`.

<details>
<summary>Show solution</summary>

```yaml
name: Smoke CI

on:
  push:
    branches-ignore:
      - main
  pull_request:
    branches:
      - main

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          # Quoted: unquoted 3.10 would be read as the number 3.1.
          python-version: "3.13"

      - name: Install dependencies
        working-directory: your-solution-root-folder-name
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run smoke suite
        working-directory: your-solution-root-folder-name
        run: behave --tags=smoke
```

**Why this works.** `on:` takes a mapping of several events, so `push` and
`pull_request` coexist and each keeps its own filters. `actions/checkout@v7`
must come before anything that reads repository files — `requirements.txt` and
the `features/` directory only exist on the runner after it. `working-directory`
is applied per step, so both the install and the `behave` run start from the
suite root; without it, `pip install -r requirements.txt` fails to find the
file. Filtering `push` with `branches-ignore: [main]` and `pull_request` with
`branches: [main]` avoids running the same suite twice for the same commit once
a PR is open.

**Verify the failure mode the lab asks for.** Remove the `actions/checkout`
step and re-run. The install step fails immediately, because the runner's
workspace is empty — `pip` reports that it could not open the requirements file
(`Could not open requirements file`), and `behave` would report no features
directory. The error names the file, not the checkout, so read it as "the
repository is not here" rather than "the path is wrong".

Then reproduce the version trap: change `python-version: "3.13"` to
`python-version: 3.10` (unquoted). YAML parses that as the float `3.1`, and
`setup-python` goes looking for Python 3.1. Quoting is not a style preference
here.

**Common wrong answer.** Setting `working-directory` once at step level for
`behave` but running `pip install` from the repository root, then wondering why
`behave` cannot import a Selenium page-object module. Both steps run in fresh
shells but share one filesystem, so the install location matters — and if
requirements live in the suite folder, both steps need the same
`working-directory`. Declaring it once per job with `defaults.run.working-directory`
is the tidier fix.

</details>

## Lab 3 — Challenge

**Task:** Add a manual `workflow_dispatch` trigger with an input called
`browser` (chrome/firefox/msedge).

<details>
<summary>Show solution</summary>

```yaml
name: Smoke CI

on:
  push:
    branches-ignore:
      - main
  workflow_dispatch:
    inputs:
      browser:
        description: "Browser for the Selenium run"
        type: choice
        options:
          - chrome
          - firefox
          - msedge
        default: chrome
        required: true

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Install dependencies
        working-directory: your-solution-root-folder-name
        run: pip install -r requirements.txt

      - name: Run smoke suite
        working-directory: your-solution-root-folder-name
        env:
          # `|| 'chrome'` supplies the value on push runs, where `inputs` is empty.
          BROWSER: ${{ inputs.browser || 'chrome' }}
        run: behave --tags=smoke -D "browser=${BROWSER}"
```

**Why this works.** `workflow_dispatch.inputs` renders a form in the Actions UI;
`type: choice` with `options:` makes it a dropdown, so an engineer cannot type
`chromium` and get a confusing WebDriver error twenty minutes later. The value
is read as `${{ inputs.browser }}`.

The input is passed through `env:` rather than interpolated directly into the
`run:` line. That keeps the expression off the shell command line, so the shell
never sees the raw value as code — the habit that matters once inputs are
free-text (see [Module 13](../modules/module-13-secrets-security.md)). Note the
expression sits on the `env:` value, not at column 0 inside the `run:` block.

**Verify the failure mode the lab asks for.** Trigger the workflow by pushing a
commit instead of dispatching it. `inputs` is empty for a `push` event, so
without the `|| 'chrome'` fallback `BROWSER` becomes an empty string and the
command degrades to `behave --tags=smoke -D "browser="` — the suite runs but
picks a default browser (or fails inside the driver factory) with nothing in the
Actions log pointing at the trigger as the cause. Delete the fallback, push, and
read the log to see how quiet the failure is.

Then reproduce the schema error: remove `options:` while keeping
`type: choice`. The workflow now fails to load, because a `choice` input is
meaningless without a list of options.

**Common wrong answer.** Using `type: string` with `default: chrome` and relying
on `required: true` to keep the value clean. `required: true` only guarantees
the field is non-empty; it validates nothing about the content, so
`Chrome`, `chrome `, and `crome` all pass. A `choice` input makes the set of
legal values part of the workflow definition.

</details>

---

[Solutions Index](./README.md) | [Module 1](../modules/module-01-ci-foundations.md) | [Course Home](../README.md)
