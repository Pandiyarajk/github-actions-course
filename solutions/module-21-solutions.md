# Module 21 — Solutions

![Module](https://img.shields.io/badge/Module-21-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 21](../modules/module-21-composite-actions.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — C.** A composite action always runs on the caller's runner. Its steps are
spliced into the calling job, so there is no `runs-on` to set: `runs:` in
`action.yml` takes `using` and `steps`, not a runner. Sharing work that needs its
own runner is exactly the case for a reusable workflow.

**2 — B.** `uses: ./...` is a filesystem path resolved on the runner. Until
`actions/checkout` has run, the workspace is empty and `action.yml` does not
exist. The error message ("Can't find 'action.yml' under ...") reads like a typo
in the path, which is why this one costs people so much time.

**3 — B.** `shell:` is required on every `run:` step in a composite action and
optional in a workflow, where it defaults per runner. Omitting it fails when the
action is loaded, before any step executes.

**4.** Every action output is a **string**. A cache miss sets `cache-hit` to the
string `"false"`, and a non-empty string is truthy in a GitHub Actions
expression, so the condition is satisfied either way. The correct form compares
explicitly:

```yaml
if: steps.setup.outputs.cache-hit == 'true'
```

The same trap applies to any boolean-looking input or output — `inputs.enabled`,
`cache-hit`, `steps.x.outputs.changed`. The only values that are falsy are the
empty string, `0`, and `false` as an actual boolean, which action outputs never
are.

**5 — Reusable workflow.** Five jobs with ordering between them need `needs:`
and their own runners, neither of which a composite action can express; the
approval gate additionally needs a job-level `environment:`, which is a job
property.

## Lab 1 — Beginner

**Task:** Create `.github/actions/hello/action.yml` as a composite action taking
a `name` input, and call it from a `workflow_dispatch` workflow.

<details>
<summary>Show solution</summary>

`.github/actions/hello/action.yml`:

```yaml
name: Hello
description: Greet someone by name.

inputs:
  name:
    description: "Who to greet."
    required: true

runs:
  using: composite
  steps:
    - name: Greet
      shell: bash
      run: echo "Hello, ${{ inputs.name }}!"
```

`.github/workflows/hello.yml`:

```yaml
name: Hello Demo

on: workflow_dispatch

jobs:
  greet:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Say hello
        uses: ./.github/actions/hello
        with:
          name: Pandiyaraj
```

**Why this works.** `runs.using: composite` makes the `steps` list valid.
`inputs.name` is declared with `required: true`, so calling without `with.name`
fails validation rather than printing "Hello, !". The `uses: ./` path has no
`@ref` because it is a path, not a repository reference.

**Verify the failure mode the lab asks for.** Delete `shell: bash` and re-run.
You get a load-time error naming the step, before any output appears:

```
Error: (Line: 12, Col: 7): Required property is missing. shell
```

That it fails at *load* rather than at the step is the useful part — a composite
action is validated as a whole before anything executes.

**Common wrong answer.** Writing `uses: ./.github/actions/hello@v1`. Local
action references take no version — the version is whatever is in the current
checkout. Adding `@v1` produces "Can't find 'action.yml'".

</details>

## Lab 2 — Intermediate

**Task:** Extend the action with an output reporting the resolved Python
version, and have the caller print it via `steps.<id>.outputs`.

<details>
<summary>Show solution</summary>

`.github/actions/hello/action.yml`:

```yaml
name: Hello
description: Greet someone and report the Python version in use.

inputs:
  name:
    description: "Who to greet."
    required: true
  python-version:
    description: "Python version to provision."
    required: false
    default: "3.13"

outputs:
  resolved-python:
    description: "The exact Python version that was installed."
    # An action output's `value` is wired to a STEP output, which is why the
    # step below needs an `id`.
    value: ${{ steps.probe.outputs.version }}

runs:
  using: composite
  steps:
    - name: Set up Python
      uses: actions/setup-python@v7
      with:
        python-version: ${{ inputs.python-version }}

    - name: Probe version
      id: probe
      shell: bash
      run: |
        version="$(python -c 'import platform; print(platform.python_version())')"
        echo "version=${version}" >> "$GITHUB_OUTPUT"

    - name: Greet
      shell: bash
      run: echo "Hello, ${{ inputs.name }}!"
```

Calling workflow:

```yaml
      - name: Say hello
        id: hello                      # required for outputs to be reachable
        uses: ./.github/actions/hello
        with:
          name: Pandiyaraj

      - name: Print resolved version
        run: echo "Ran on Python ${{ steps.hello.outputs.resolved-python }}"
```

**Why this works.** There are two hops. Inside the action, a step writes to
`$GITHUB_OUTPUT`, producing `steps.probe.outputs.version`. The action's
`outputs.resolved-python.value` then forwards that to the caller as
`steps.hello.outputs.resolved-python`. Miss either hop and you get an empty
string with no error.

**Verify the failure mode the lab asks for.** Remove `id: hello` from the
calling step. `steps.hello.outputs.resolved-python` becomes an empty string and
the echo prints `Ran on Python` with nothing after it — no warning, no failure.
Silent empty expressions are the most common way action wiring goes wrong.

**Common wrong answer.** Writing `value: ${{ env.VERSION }}` after setting
`VERSION` via `$GITHUB_ENV` in a step. Action `outputs.value` is evaluated in the
action's own context where `env` set by its steps is not visible; it must read a
step output.

</details>

## Lab 3 — Challenge

**Task:** Extract the shared preamble from two existing `examples/` workflows
into one composite action, convert both, and record why it could not have been a
reusable workflow.

<details>
<summary>Show solution</summary>

Take [`module-15-multi-language-tests.yml`](../examples/module-15-multi-language-tests.yml)
and [`module-18-qa-automation.yml`](../examples/module-18-qa-automation.yml). Both
open with checkout, `setup-python`, then a `pip install`. The checkout stays in
the caller; the rest becomes the action.

The repository already ships the finished version of this extraction at
[`.github/actions/setup-python-suite/action.yml`](../.github/actions/setup-python-suite/action.yml).
Compare your answer against it — in particular how it handles a missing
requirements file and how it turns a space-separated `extra-packages` input into
separate `pip` arguments.

The converted caller:

```yaml
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      # Replaces: setup-python + pip install --upgrade pip + pip install -r ...
      - name: Set up Python suite
        uses: ./.github/actions/setup-python-suite
        with:
          python-version: "3.13"
          working-directory: your-solution-root-folder-name
          extra-packages: allure-behave

      # ... the workflow's own distinctive steps continue unchanged
```

The comment the lab asks for:

```yaml
      # This extraction is a composite action rather than a reusable workflow
      # because the shared work is a sequence of STEPS that must run inside this
      # job: the packages it installs have to be on the same runner, in the same
      # workspace, as the `behave` step below. A reusable workflow would run in
      # its own job on its own runner, so the installed dependencies would be
      # gone by the time this job's test step executed.
```

**Why this works.** The deciding question is never "how much is shared" but
"does the shared work need the caller's filesystem". Dependency installation
does, so it must be a composite action. Report generation does not — it consumes
uploaded artifacts — which is why
[`generate-allure-report.yml`](../.github/workflows/generate-allure-report.yml)
is a reusable workflow instead.

**Common wrong answer.** Moving the `actions/checkout` step into the composite
action too. It appears to work when the caller happens to have checked out
already, and fails confusingly when it has not — the action cannot be loaded to
perform the checkout that would make it loadable. Checkout belongs in the
caller.

</details>

---

[Solutions Index](./README.md) | [Module 21](../modules/module-21-composite-actions.md) | [Course Home](../README.md)
