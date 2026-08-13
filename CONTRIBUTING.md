# Contributing

![Contributions](https://img.shields.io/badge/Contributions-Welcome-2da44e?style=flat-square) [![Course Home](https://img.shields.io/badge/⬅%20Course%20Home-555?style=flat-square)](README.md)

This repository is teaching material, so a contribution is judged on whether a
learner ends up with a correct mental model — not only on whether the YAML runs.

## Before you start

Run the validator. It is fast, needs no network, and tells you what the CI will
say:

```bash
pip install pyyaml yamllint
python scripts/validate_course.py
```

| Check | What it enforces |
| --- | --- |
| `pins` | Every `uses:` matches the version table in `scripts/validate_course.py` |
| `mutable` | No `@main`-style refs, except documented allowlist entries |
| `yaml-blocks` | Every fenced YAML block in the docs actually parses |
| `links` | Every relative markdown link resolves |
| `structure` | Every module carries the full teaching template |
| `pairing` | Every module has a paired example and solutions file |

Run one at a time with `--check <name>`.

## The module template is not optional

Every file in `modules/` carries the same sections in the same order, and
`--check structure` enforces it. Twenty-six modules that each invent their own
shape is twenty-six blog posts; the identical template is what makes it a course.

If you add a module you need four files:

| File | Purpose |
| --- | --- |
| `modules/module-NN-<slug>.md` | The lesson, on the standard template |
| `examples/module-NN-<slug>.yml` | A runnable, heavily-commented workflow |
| `solutions/module-NN-solutions.md` | Quiz answers and all three lab solutions |
| A row in `modules/README.md` and `solutions/README.md` | Discoverability |

Copy [`modules/module-21-composite-actions.md`](modules/module-21-composite-actions.md)
and [`solutions/module-21-solutions.md`](solutions/module-21-solutions.md) as the
reference implementations.

## Content rules

**Comments explain *why*, not *what*.** `# checkout the repo` above
`uses: actions/checkout@v7` is noise. `# MUST come first: a local action is read
from the runner's filesystem, so the checkout is what makes it exist` is the
lesson.

**Teach the failure, not just the fix.** Every lab solution states the error to
reproduce and the plausible wrong answer. A learner who has only seen working
YAML has pattern-matched, not understood.

**Verify facts; do not recall them.** Action versions, default values, and error
messages go stale. Check the releases page or the action's own `action.yml`
before asserting a default. If you cannot confirm an error string exactly,
describe the failure instead of inventing quoted text.

**Genericise everything.** Use `your-solution-root-folder-name/`,
`your-domain.com`, and `server1`–`server4`. Never real company, project, or host
names. Never anything that looks like a real credential.

**Stay Python.** Examples use Python 3.13, Behave, Selenium, Allure, and pylint.
No Node.js, .NET, Maven, or other language toolchains — a learner should not have
to know a second stack to follow a lesson about triggers.

## Action versions

The pin table lives in `PINNED_ACTIONS` in
[`scripts/validate_course.py`](scripts/validate_course.py) and is mirrored in
prose in `CLAUDE.md`. Update both together.

First-party `actions/*` are **independently versioned** — their majors currently
span five numbers — so there is no single "generation" to track. Verify each one
against `https://github.com/<owner>/<repo>/releases/latest`.

Third-party actions outside the pin table must be pinned to a **full commit
SHA** with a trailing `# vX.Y.Z` comment:

```yaml
uses: some-org/some-action@6f3c981e7b77f235fd2702dd74af25fc4b72bf11 # v3.96.0
```

Resolve a SHA with `gh api repos/<owner>/<repo>/commits/<tag> --jq .sha`. Do not
use `git/ref/tags/<tag>` — for an annotated tag that returns the tag object's
SHA, not the commit's.

## Two YAML traps that will fail CI

Both appear in real workflows and both are caught by `--check yaml-blocks`.

**An unquoted scalar containing `": "` parses as a nested mapping**, invalidating
the file:

```yaml
# Broken
- name: Optional: push to registry
- run: echo "Tags: $TAGS"

# Fixed
- name: "Optional: push to registry"
- run: |
    echo "Tags: $TAGS"
```

**A `${{ }}` expression at column 0 inside a `run: |` block** terminates the
block scalar. Pass the value through `env:` instead — which is also the
injection-safe pattern:

```yaml
- env:
    STATS: ${{ steps.x.outputs.result }}
  run: |
    printf '%s\n' "$STATS" > out.json
```

To show intentionally-broken YAML in documentation, fence it as ```text so the
parser does not treat it as a defect.

## Pull requests

- Branch from `main`; keep the diff scoped to one concern.
- Run `python scripts/validate_course.py` and `yamllint .` before pushing.
- A version bump belongs in its own commit — mixing a repo-wide sweep into a
  content change makes both unreviewable.
- Say what you verified and how. "Checked `upload-artifact`'s `action.yml`; the
  default for `if-no-files-found` is `warn`, not `error`" is worth more than
  "fixed docs".

## Reporting a problem

Open an issue with the file, the line, and what a learner would conclude
incorrectly. Errors that teach the wrong model matter more than typos, and a
plausible-but-wrong explanation is the worst defect this repository can have.
