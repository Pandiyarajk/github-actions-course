# 🔧 Debugging Clinic

![Section](https://img.shields.io/badge/Section-Debugging%20Clinic-8957e5?style=flat-square) ![Use](https://img.shields.io/badge/Use-Symptom%20%E2%86%92%20Diagnosis-1f6feb?style=flat-square) [![Reference Library](https://img.shields.io/badge/⬅%20Reference-555?style=flat-square)](README.md) [![Course Home](https://img.shields.io/badge/⬅%20Course%20Home-555?style=flat-square)](../README.md)

> Navigation: [Course Home](../README.md) | [Reference Index](./README.md) | [Cheat Sheet](./cheatsheet.md)

Every case below is a real symptom, taken from a defect that actually occurred in
this repository or in the workflows its modules teach. They are collected here
because in each one **the diagnosis is not the obvious one**: the error message
points at the wrong line, at the wrong file, or at nothing at all. Several
produce no error whatsoever — the workflow goes green while doing less than you
think.

Snippets that are deliberately invalid are fenced as `text` rather than `yaml`,
so the repository's own validator can still parse every real example on this
page.

## Case 1 — One step name breaks the whole file

**Symptom.** A workflow stops appearing in the Actions tab entirely, or fails
before any job starts with a parse error naming a line you did not touch.

```text
      - name: Optional: push to registry
        run: echo "pushing"
```

**Diagnosis.** Not a workflow problem at all — a YAML problem. In a plain
(unquoted) scalar, the two-character sequence `": "` is a key/value separator.
The parser reads `Optional` as a key and `push to registry` as its value, so
`name:` becomes a nested mapping instead of a string, and the step no longer has
a valid `name`. The reported error frequently lands on a *later* line, because
that is where the resulting structure first becomes impossible.

**Fix.** Quote any scalar containing a colon followed by a space.

```yaml
      - name: "Optional: push to registry"
        run: echo "pushing"
```

**Why it misleads.** The line is readable English and looks nothing like a syntax
error, and the parser blames somewhere else.

## Case 2 — A `run:` block ends early

**Symptom.** A multi-line `run:` block fails to parse, or the parser complains
about a mapping key it found in the middle of what you thought was a shell
script.

```text
      - name: Report the ref
        run: |
          echo "starting"
${{ github.ref_name }}
          echo "done"
```

**Diagnosis.** A block scalar (`|`) is terminated by the first line that is
indented *less* than the block's established indentation. An expression written
at column 0 does exactly that. YAML ends the script at `echo "starting"` and then
tries to read `${{ github.ref_name }}` as a new mapping key at the document's top
level. Note that this happens **before** any expression substitution — YAML is
parsed first, so the value of `github.ref_name` is irrelevant.

**Fix.** Keep every line of the block indented, and prefer passing values through
`env:` so the shell, not the YAML layer, does the interpolation.

```yaml
      - name: Report the ref
        env:
          REF_NAME: ${{ github.ref_name }}
        run: |
          echo "starting"
          echo "$REF_NAME"
          echo "done"
```

**Why it misleads.** It reads as an expression problem, so people go looking at
contexts and permissions instead of at indentation.

## Case 3 — "Can't find 'action.yml'" for a path that exists

**Symptom.** A local action reference fails immediately, complaining it cannot
find `action.yml` under a path you can see in the repository.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      # FIRST step in the job.
      - name: Set up Python suite
        uses: ./.github/actions/setup-python-suite

      - name: Checkout repository
        uses: actions/checkout@v7
```

**Diagnosis.** `uses: ./...` is a **filesystem path on the runner**, not a
repository reference. Until `actions/checkout` has run, the workspace is empty,
so `action.yml` genuinely does not exist yet. The file being present on GitHub is
irrelevant. This cannot be worked around inside the action either — the action
would have to be loaded in order to perform the checkout that makes it loadable.

**Fix.** Checkout always comes first, and belongs in the caller.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python suite
        uses: ./.github/actions/setup-python-suite
        with:
          python-version: "3.13"
          working-directory: your-solution-root-folder-name
```

**Why it misleads.** The message reads exactly like a typo in the path, so people
re-check spelling instead of ordering. A related trap: local references take no
`@ref`, and adding one produces the same error.

## Case 4 — A composite action fails before its first step

**Symptom.** A job using a composite action fails with a "required property is
missing" error and a line number inside `action.yml`. No step from the action
appears in the log at all.

```text
runs:
  using: composite
  steps:
    - name: Install dependencies
      run: pip install behave selenium allure-behave
```

**Diagnosis.** `shell:` is **required** on every `run:` step in a composite
action, while in a workflow it is optional and defaults per runner. The action is
validated as a whole when it is loaded, so the failure happens at **load time**,
before any step executes — which is why the log shows nothing running.

**Fix.**

```yaml
runs:
  using: composite
  steps:
    - name: Install dependencies
      shell: bash
      run: pip install behave selenium allure-behave
```

**Why it misleads.** The identical step works fine when pasted into a workflow,
so the omission looks correct by precedent — and "no steps ran" suggests a runner
or permissions problem rather than a schema one.

## Case 5 — `actions/checkout` starts returning 403

**Symptom.** A workflow that has run for months suddenly fails at checkout with
a 403, in a commit whose only change was adding a `permissions:` block for a new
publishing step.

```yaml
name: Publish

on: workflow_dispatch

# Intended as "additionally allow package writes".
permissions:
  packages: write

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7
```

**Diagnosis.** `permissions:` is not additive. Declaring any scope replaces the
entire token grant, and **every scope you did not list becomes `none`** — so
`contents` is now `none` and checkout cannot read the repository. The 403 is
correct behaviour for a token that has no `contents` scope.

**Fix.** Enumerate every scope the workflow needs, including the ones you were
previously getting by default.

```yaml
permissions:
  contents: read
  packages: write
```

**Why it misleads.** Nothing about checkout changed, so the blame lands on the
action, a token expiry, or an org policy. The habit that avoids it entirely is a
top-level `permissions: contents: read` from day one, widened per job.

## Case 6 — A cache-miss step runs on a cache hit

**Symptom.** A step guarded by a `cache-hit` condition runs every single time,
whether the cache hit or missed. Dependencies are reinstalled on every run and
the cache appears useless.

```yaml
      - name: Restore dependencies
        id: setup
        uses: actions/cache@v6
        with:
          path: ~/.cache/pip
          key: pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        # Runs unconditionally.
        if: steps.setup.outputs.cache-hit
        run: pip install -r requirements.txt
```

**Diagnosis.** Every action output is a **string**. A cache miss sets `cache-hit`
to the string `"false"`, and a non-empty string is truthy in a GitHub Actions
expression — so the condition is satisfied either way. The only falsy values are
the empty string, `0`, and an actual boolean `false`, which an action output
never is.

**Fix.** Compare explicitly.

```yaml
      - name: Install dependencies
        if: steps.setup.outputs.cache-hit != 'true'
        run: pip install -r requirements.txt
```

**Why it misleads.** The expression looks like a boolean test and reads like
correct code in every other language. The same trap applies to
`inputs.enabled`, `steps.x.outputs.changed`, and any other boolean-looking
input or output.

## Case 7 — Connection refused to a service that started fine

**Symptom.** A service container's log shows it started and became healthy, but
the test step cannot connect. It looks as though the service never came up.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container: python:3.13-slim
    services:
      selenium:
        image: selenium/standalone-chrome:latest
        ports:
          - 4444:4444
    steps:
      # Wrong host: this job runs INSIDE a container.
      - name: Run UI suite
        env:
          SELENIUM_URL: http://localhost:4444/wd/hub
        run: behave --tags=smoke
```

**Diagnosis.** The hostname depends on where the *job* runs, not where the
service runs. A job running **in a container** shares a Docker network with the
services and must address them by their **label** (`selenium`) on the container's
own port; `localhost` there is the job's own container. A job running **on the
runner** is the mirror image: it must use `localhost` with the **mapped** port,
because the label does not resolve. Getting it backwards produces a connection
refusal identical to a service that failed to start.

**Fix.** For a containerised job, use the label and drop the port mapping — port
mapping exists for the runner-hosted case.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container: python:3.13-slim
    services:
      selenium:
        image: selenium/standalone-chrome:latest
    steps:
      - name: Run UI suite
        env:
          SELENIUM_URL: http://selenium:4444/wd/hub
        run: behave --tags=smoke
```

**Why it misleads.** The service's own log is green, so attention goes to
readiness, health checks, and startup timing rather than to name resolution.

## Case 8 — Docker layer caching that silently does nothing

**Symptom.** A build declares GitHub Actions cache export, the workflow passes,
and build times never improve. No warning, no error, no cache entries.

```yaml
      - name: Build image
        uses: docker/build-push-action@v7
        with:
          context: .
          push: false
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

**Diagnosis.** The default Docker driver does not support cache export.
`type=gha` requires the `docker-container` driver, which
`docker/setup-buildx-action` installs; without it the cache directives are
**accepted and ignored**. There is nothing to grep for in the log because
nothing failed.

**Fix.** Add the buildx setup step before the build.

```yaml
      - name: Set up Buildx
        uses: docker/setup-buildx-action@v4

      - name: Build image
        uses: docker/build-push-action@v7
        with:
          context: .
          push: false
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

**Why it misleads.** A green run with the right keys present looks like working
configuration. The only evidence is the absence of a speed-up, which is easy to
attribute to the build being genuinely slow.

## Case 9 — Second matrix leg fails on upload

**Symptom.** One matrix leg uploads its artifact successfully; the others fail
during upload with a conflict over the artifact name.

```yaml
    strategy:
      matrix:
        browser: [chrome, firefox, msedge]
    steps:
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          # Identical across all three legs.
          name: allure-results
          path: reports/allure-results
```

**Diagnosis.** From v4 onward artifacts are **immutable**. Uploading a second
artifact under a name that already exists in the run is an error, not a merge —
the v3 behaviour of appending files into a shared artifact no longer exists. The
first leg to finish wins and the rest fail, so which legs fail varies run to run.

**Fix.** Make the name unique per leg, and merge afterwards if a single artifact
is genuinely wanted.

```yaml
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-results-${{ matrix.browser }}
          path: reports/allure-results
          retention-days: 7
```

A downstream job can then collect them all with a pattern:

```yaml
      - name: Download every leg's results
        uses: actions/download-artifact@v8
        with:
          pattern: allure-results-*
          merge-multiple: true
          path: reports/allure-results
```

**Why it misleads.** It is intermittent and leg-dependent, so it reads like a
race condition or a flaky uploader rather than a deliberate API change.

## Case 10 — A required check that does not block anything

**Symptom.** Branch protection requires the `test` check, yet a pull request with
obviously untested changes merges cleanly.

```yaml
name: Test

on:
  pull_request:
    paths:
      - "your-solution-root-folder-name/**"

jobs:
  test:
    name: test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Run smoke suite
        run: behave --tags=smoke
```

**Diagnosis.** A job excluded by a path filter (or by an `if:`) reports a
conclusion of **`skipped`**, and a skipped required status check **does not block
a merge**. That is intended for a docs-only change — and it means the rule is
also silently unenforced on any pull request where the filter is subtly wrong.
Compounding it: required checks are matched by **job name**, so renaming the job
detaches the protection rule with no warning at all.

**Fix.** Require a single always-run aggregator instead, and let it decide.

```yaml
jobs:
  gate:
    name: PR gate
    if: always()
    needs: [lint, test]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Verify upstream results
        run: |
          for result in "${{ needs.lint.result }}" "${{ needs.test.result }}"; do
            case "$result" in
              success|skipped) ;;
              *) echo "::error::Upstream job concluded '$result'"; exit 1 ;;
            esac
          done
```

**Why it misleads.** The settings page states the check is required and the PR
shows the check listed, so protection looks active. See
[Module 25](../modules/module-25-environments-approvals.md) for the full
treatment.

## Case 11 — A gate job that never fails

**Symptom.** The aggregator gate from Case 10 passes on a pull request whose
`test` job clearly failed. The gate itself shows as skipped in the run graph.

```yaml
jobs:
  gate:
    name: PR gate
    # Wrong: this cannot ever evaluate to false.
    if: needs.test.result == 'success'
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - name: Confirm
        run: echo "upstream ok"
```

**Diagnosis.** The default job condition already requires all `needs:` to have
succeeded. When `test` fails, the expression is never reached — the job is marked
**`skipped`** because a dependency failed. And by Case 10's rule, a skipped
required check does not block a merge. So the gate passes on exactly the pull
requests it exists to stop, which is worse than having no gate, because the tick
looks legitimate.

**Fix.** `if: always()` to guarantee the job *reports*, plus an explicit
assertion to decide *what* it reports.

```yaml
jobs:
  gate:
    name: PR gate
    if: always()
    needs: [test]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Verify upstream results
        run: |
          result="${{ needs.test.result }}"
          case "$result" in
            success|skipped) ;;
            *) echo "::error::test concluded '$result'"; exit 1 ;;
          esac
```

Allowlist `success|skipped` and fail everything else. Enumerating failures
instead lets `cancelled`, `timed_out`, and any future conclusion string through.

**Why it misleads.** The condition names the exact thing you want to check, so it
reads as correct. A gate that passes when it should fail is nearly always missing
`if: always()`.

## Case 12 — A pin that reviewed and linted clean, then vanished

**Symptom.** An unchanged workflow starts failing at runtime, unable to resolve
an action. Nothing in the repository changed. `actionlint` passes, and the
version number looks entirely reasonable.

```yaml
      - name: Scan image for vulnerabilities
        uses: aquasecurity/trivy-action@0.21.3
        with:
          image-ref: ghcr.io/your-org/your-image:latest
```

**Diagnosis.** The pin is a **nonexistent ref**. Upstream moved to a
`v`-prefixed tagging scheme and now publishes tags like `v0.36.0`; the old
unprefixed tag is no longer resolvable. Two independent tools give false comfort
here: a human review sees `0.21.3` and compares it numerically against the
release notes' `0.36.0`, concluding "a bit behind, not broken"; and `actionlint`
validates schema, expressions and shell, but has **no opinion on whether a
version exists or is current** — a stale or deleted ref lints clean, exactly as
`actions/checkout@v3` does. Dependabot may also stay silent, because a tag it
cannot resolve gives it no successor version to compute an update from — and
because the `github-actions` ecosystem scans only `.github/workflows/`, so a
reference in `examples/`, in a composite action, or quoted in documentation is
invisible to it.

**Fix.** Verify the ref against the upstream releases page rather than from
memory, and prefer a full commit SHA with the human-readable version in a
trailing comment for third-party actions.

```yaml
      - name: Scan image for vulnerabilities
        uses: aquasecurity/trivy-action@v0.36.0
        with:
          image-ref: ghcr.io/your-org/your-image:latest
```

Then leave a machine check behind so the repository cannot drift again:

```bash
python scripts/validate_course.py --check pins --check mutable
```

**Why it misleads.** Every signal you would normally trust — a numeric version,
a clean linter, a quiet Dependabot — reports fine, and the only failure arrives
at runtime in a workflow nobody edited.

## Triage order

When a workflow fails, work down this list. Each step rules out a whole class of
cause, and the order is deliberate: the cheapest and most commonly wrong things
come first.

1. **Did it parse?** If the workflow vanished from the Actions tab or failed
   before any job appeared, it is YAML — quoting (Case 1) or block-scalar
   indentation (Case 2). Run `actionlint` and `yamllint` locally before reading
   anything else.
2. **Did the job start at all?** No steps in the log means load-time validation:
   a composite action missing `shell:` (Case 4), or a local `uses:` resolved
   before checkout (Case 3).
3. **Is it a permissions story?** Any 401/403 on a first-party action — check the
   `permissions:` block for the replace-not-merge trap (Case 5) and whether the
   job declares the `environment:` its secrets live on.
4. **Is a value empty rather than wrong?** Unresolvable secrets, missing step
   `id`s, and undeclared environments all yield the empty string with no error.
   Print lengths, never values.
5. **Is a condition doing what you think?** Action outputs are strings, so
   `if: steps.x.outputs.flag` is always true (Case 6). Compare against
   `'true'`.
6. **Is it green but not actually doing the work?** The silent class: cache
   export without buildx (Case 8), a gate that can only be skipped (Case 11), a
   path-filtered required check (Case 10). Ask what evidence you have that the
   step had an effect.
7. **Is it a network or naming boundary?** Service addressing depends on whether
   the job runs in a container or on the runner (Case 7).
8. **Is it an artifact or version contract?** Duplicate artifact names in a
   matrix (Case 9), or a pin that no longer resolves (Case 12). Check the ref
   against upstream releases rather than from memory.
9. **Only now, re-read the error message.** By this point you know which layer
   owns the failure, and the message usually makes sense — the reason it did not
   at first is that most of these errors are reported by a layer downstream of
   the actual mistake.

---

[Course Home](../README.md) | [Reference Index](./README.md) | [Cheat Sheet](./cheatsheet.md) | [Module Index](../modules/README.md)
