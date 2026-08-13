# Module 23 — Solutions

![Module](https://img.shields.io/badge/Module-23-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 23](../modules/module-23-docker-publish.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** `packages: write` is **not** part of the default `GITHUB_TOKEN`
grant, so the login succeeds — the token is a valid credential — and the *push*
is refused. That split is what makes the diagnosis hard: `denied` arrives at the
end of a build that authenticated cleanly, so it reads as a credentials problem.
**A** is wrong in a way worth naming: `GITHUB_TOKEN` genuinely does expire, but
it is minted fresh for every run and cannot be "regenerated" by you, and an
expired token fails authentication rather than authorisation. **C** is simply
false — GHCR accepts `GITHUB_TOKEN` for packages owned by the same repository,
which is the whole reason no PAT is needed. **D** invents a requirement; a
separate `GHCR_TOKEN` secret is only needed when pushing to a *different*
repository's or organisation's namespace, and reaching for it here fixes nothing
while adding a long-lived credential to the repository. Check `permissions:`
before you touch credentials.

**2 — B.** `type=gha` is a BuildKit cache backend, and BuildKit comes from
`docker/setup-buildx-action`. Without that step, `build-push-action` falls back
to the legacy builder, which accepts `cache-to` and does nothing with it — no
warning, no error, just a build that is never faster. **A** is a real mistake
(export-only caching gives you nothing on the next run) but the question says
builds are never faster while `cache-to` is set, and the missing *import* would
be the obvious thing the author checked; more importantly, without buildx neither
direction works, so B is the root cause that also explains A. **C** is unrelated
— `provenance` attaches attestations and has no bearing on caching. **D** is the
conclusion people reach right before giving up on GHA caching, and it is almost
never true. The one-line confirmation is to look for `importing cache manifest`
in the build log; if it is absent, the cache was never read at all.

**3 — C.** The digest is a content hash of the image manifest, so
`ghcr.io/<owner>/<repo>/test-runner@sha256:...` can only ever resolve to the
exact bytes that release published. `docker/build-push-action` exposes it as
`steps.<id>.outputs.digest`, which is why the example workflow wires that into
the downstream `container:`. **A** is the worst option — `latest` is re-pointed
by the next release, so a re-run of an old workflow silently uses a new image.
**B** looks safe but a semver *tag* is still a mutable pointer: nothing prevents
`1.4.0` being force-pushed to a rebuilt image, and in practice that happens when
someone patches a release. **D** has the same problem for the same reason: the
short-SHA tag names the *source commit*, not the built artefact, and the same
commit rebuilt with a newer base image produces a different image under the same
tag.

**4.** GHCR requires image names to be **lowercase**, and
`${{ github.repository }}` returns the repository path with its original
capitalisation preserved — `Pandiyarajk/GitHub-Actions-Course`. Using it
directly produces `ghcr.io/Pandiyarajk/GitHub-Actions-Course`, which the registry
rejects as an invalid reference. The failure happens at push time, after a
successful build, and the message is about the name rather than about case, so it
is easy to read as a typo.

The fix is to normalise the name once and reuse it. In bash, `${VAR,,}`
lowercases a variable, and `GITHUB_REPOSITORY` is available as an environment
variable, so no expression is needed:

```yaml
      - name: Compute lowercase image name
        id: name
        run: |
          echo "image=ghcr.io/${GITHUB_REPOSITORY,,}/test-runner" >> "$GITHUB_OUTPUT"

      - name: Build and push
        id: build
        uses: docker/build-push-action@v7
        with:
          context: .
          push: true
          tags: ${{ steps.name.outputs.image }}:latest
```

Two notes. `${VAR,,}` is a bash feature, so it needs `shell: bash` on a Windows
runner (and would not work in `sh`). And do not "fix" this by hardcoding a
lowercase literal — that breaks the moment the workflow is copied to another
repository, which is exactly the scenario this pattern exists for.

**5.** Both effects come from the same change, and both are expected.

**Build time roughly doubles** because a multi-platform build is genuinely two
builds. Every layer is produced once per platform, and the `linux/arm64` half
runs on an `amd64` runner under QEMU emulation via
`docker/setup-qemu-action@v4`. Emulated compilation and package installation are
substantially slower than native, so "roughly double" is the optimistic figure
for an image that compiles anything. It also doubles the cache footprint against
the repository's shared Actions cache budget.

**`docker load` starts failing** because a multi-platform build does not produce
an image — it produces an **image index** (a manifest list) that points at one
manifest per platform. The local Docker image store the `docker` CLI reads from
holds single-platform images, so there is nothing coherent for `docker load` to
import, and buildx refuses rather than silently picking one architecture. In
`build-push-action` terms, `load: true` is incompatible with a multi-platform
`platforms:` value.

The fix depends on what the `docker load` step was for. If it was a smoke test of
the built image, either build the host platform only for that check, or push
first and then pull by digest — which is what
[`module-23-docker-publish.yml`](../examples/module-23-docker-publish.yml) does,
because pulling by digest also proves the published artefact works rather than a
local copy of it. If arm64 is not actually needed, the honest fix is to drop it:
paying double build time for an architecture nobody runs is a common and
expensive habit.

## Lab 1 — Beginner

**Task:** Publish a minimal image containing Python 3.13 and `behave` to GHCR on
push to `main`. The package should appear under the repository, and removing
`packages: write` should reproduce the `denied` error.

<details>
<summary>Show solution</summary>

`docker/Dockerfile.test-runner`:

```dockerfile
# Author: Pandiyaraj Karuppasamy
# Date: Aug-13-2026
FROM python:3.13-slim

RUN pip install --no-cache-dir --disable-pip-version-check \
      behave \
      selenium \
      allure-behave

WORKDIR /work
CMD ["behave", "--version"]
```

`.github/workflows/lab-23-1-publish.yml`:

```yaml
name: Lab 23-1 Publish Test Runner

on:
  push:
    branches:
      - main

# `packages: write` is NOT in the default token grant. `contents: read` must be
# listed too -- naming any scope sets every unnamed scope to `none`, which would
# break checkout (see Module 24).
permissions:
  contents: read
  packages: write

jobs:
  publish:
    name: Build and publish
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Compute lowercase image name
        id: name
        run: |
          # GHCR rejects uppercase names, and GITHUB_REPOSITORY keeps the
          # repository's own capitalisation. ${VAR,,} is bash lowercasing.
          echo "image=ghcr.io/${GITHUB_REPOSITORY,,}/test-runner" >> "$GITHUB_OUTPUT"

      # Must come BEFORE build-push-action for any BuildKit feature to work.
      - name: Set up Buildx
        uses: docker/setup-buildx-action@v4

      - name: Log in to GHCR
        uses: docker/login-action@v4
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v7
        with:
          context: .
          file: ./docker/Dockerfile.test-runner
          push: true
          tags: ${{ steps.name.outputs.image }}:latest

      - name: Record the digest
        run: |
          echo "Published digest:"
          echo "${{ steps.build.outputs.digest }}"
```

**Why this works.** Four things are load-bearing and each has its own failure if
omitted. `permissions: packages: write` is what lets the run's token push at all.
`contents: read` is listed explicitly because naming one scope zeroes the rest.
`setup-buildx-action` precedes the build, so BuildKit is the builder. And the
image name is lowercased from `GITHUB_REPOSITORY` rather than interpolated from
`${{ github.repository }}`, so the workflow survives being copied into a
repository whose name has capitals.

**Verify the failure mode the lab asks for.** Delete the `packages: write` line
and re-run. The `Log in to GHCR` step still succeeds — this is the part that
misleads people — the build runs to completion, and the push is refused with a
`denied` error. Nothing about the message points at `permissions:`. Put the line
back and confirm the same commit pushes cleanly, which isolates the cause to the
permission rather than the credential. While you are there, check the run log's
"GITHUB_TOKEN Permissions" block: it lists exactly what the token was granted,
and reading it is faster than reasoning about the defaults.

**Common wrong answer.** Creating a personal access token, storing it as a
secret, and passing it as the registry password. It appears to fix the problem,
because a PAT with the right scope can push regardless of the workflow's
`permissions:`. What you have actually done is add a long-lived credential to the
repository to work around a one-line configuration gap — strictly worse on every
axis, and it hides the lesson.

</details>

## Lab 2 — Intermediate

**Task:** Add `docker/metadata-action` and a `v*.*.*` tag trigger so a tag push
produces semver, short-SHA, and `latest` tags. A tag push should yield the full
tag set, and `steps.meta.outputs.tags` printed in the log should match.

<details>
<summary>Show solution</summary>

```yaml
name: Lab 23-2 Tagged Publish

on:
  push:
    tags:
      - "v*.*.*"
  workflow_dispatch:
    inputs:
      push:
        description: "Push the image, or build only"
        type: boolean
        default: false

permissions:
  contents: read
  packages: write

concurrency:
  group: lab-23-2-${{ github.ref }}
  # Never cancel midway through a layer upload -- a cancelled push can leave a
  # partially-written manifest behind.
  cancel-in-progress: false

jobs:
  publish:
    name: Build and publish
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.name.outputs.image }}
      digest: ${{ steps.build.outputs.digest }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Compute lowercase image name
        id: name
        run: |
          echo "image=ghcr.io/${GITHUB_REPOSITORY,,}/test-runner" >> "$GITHUB_OUTPUT"

      - name: Decide whether to push
        id: decide
        run: |
          # Push on a tag, or when a manual run explicitly asks for it.
          if [ "$GITHUB_REF_TYPE" = "tag" ] || [ "$WANT_PUSH" = "true" ]; then
            echo "push=true" >> "$GITHUB_OUTPUT"
          else
            echo "push=false" >> "$GITHUB_OUTPUT"
          fi
        env:
          WANT_PUSH: ${{ inputs.push }}

      - name: Set up Buildx
        uses: docker/setup-buildx-action@v4

      - name: Log in to GHCR
        if: steps.decide.outputs.push == 'true'
        uses: docker/login-action@v4
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # Derives the whole tag set from the git ref. v1.4.0 becomes 1.4.0, 1.4,
      # 1, plus sha-<short>, plus latest on the default branch.
      - name: Derive tags and labels
        id: meta
        uses: docker/metadata-action@v6
        with:
          images: ${{ steps.name.outputs.image }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha,format=short
            type=raw,value=latest,enable={{is_default_branch}}
          labels: |
            org.opencontainers.image.title=BDD test runner
            org.opencontainers.image.description=Python 3.13 + Behave + Selenium + Allure

      # Print the computed tags BEFORE the build. Inferring them from the push
      # output means guessing at collapsed log lines.
      - name: Show computed tags
        run: |
          echo "Tags that will be applied:"
          echo "${{ steps.meta.outputs.tags }}"

      - name: Build and push
        id: build
        uses: docker/build-push-action@v7
        with:
          context: .
          file: ./docker/Dockerfile.test-runner
          push: ${{ steps.decide.outputs.push == 'true' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

Pushing `v1.4.0` produces exactly this in the `Show computed tags` step:

```text
ghcr.io/<owner>/<repo>/test-runner:1.4.0
ghcr.io/<owner>/<repo>/test-runner:1.4
ghcr.io/<owner>/<repo>/test-runner:1
ghcr.io/<owner>/<repo>/test-runner:sha-1a2b3c4
```

Note what is *absent*: no `latest`. `enable={{is_default_branch}}` is false on a
tag push, because a tag ref is not a branch. That surprises people, and it is
correct behaviour — decide deliberately whether a release tag should move
`latest`, and if it should, use `type=raw,value=latest` with your own condition
rather than `is_default_branch`.

**Why this works.** `metadata-action` reads the git ref and emits a newline-
separated tag list plus a set of OCI labels, both of which `build-push-action`
accepts directly as multi-line values. The `type=semver` entries only fire on a
tag ref that parses as semver, which is why the `v*.*.*` trigger and the tag
patterns belong together — with a branch-only trigger the semver entries produce
nothing and you get an empty tag list, which fails the build rather than
publishing something wrong. Splitting the version into `1.4.0`, `1.4`, and `1`
is what lets a consumer choose its own update cadence.

**Verify the failure mode the lab asks for.** Compare the `Show computed tags`
output against what actually landed under the repository's Packages tab. Then
push a tag that does *not* match semver — `release-4` — and watch the semver
entries contribute nothing, leaving only the `sha-` tag. That is the whole
argument for printing the tags before the build: the tag set is computed, not
declared, and the only way to know what it computed is to look.

**Common wrong answer.** Hand-writing `tags: ${{ steps.name.outputs.image }}:${{
github.ref_name }}`. It works on a tag push and produces `v1.4.0` — with the
leading `v`, which is not the conventional image tag — and produces a tag named
after a branch on any other trigger. There is then no `1.4` or `1` to pin
against, and no way to answer "which image did that failing run use". The
related wrong answer is publishing only `latest`, which has the same consequence
in a more obvious form.

</details>

## Lab 3 — Challenge

**Task:** Add `type=gha` layer caching with `mode=max`, run the workflow twice
unchanged, and record the build-time difference and the log line proving the
cache was imported.

<details>
<summary>Show solution</summary>

The Dockerfile has to be multi-stage for `mode=max` to be worth anything —
that is the point of the exercise:

```dockerfile
# Author: Pandiyaraj Karuppasamy
# Date: Aug-13-2026
ARG PYTHON_VERSION=3.13

# Stage 1: build the dependency set. This is the expensive stage, and it is
# exactly the stage `mode=min` throws away.
FROM python:${PYTHON_VERSION}-slim AS deps
COPY your-solution-root-folder-name/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check \
      --prefix=/install -r /tmp/requirements.txt

# Stage 2: the runtime image, carrying only the installed packages.
FROM python:${PYTHON_VERSION}-slim AS runtime
COPY --from=deps /install /usr/local
WORKDIR /work
CMD ["behave", "--version"]
```

The caching additions, on top of Lab 2's workflow:

```yaml
      - name: Set up Buildx
        # Without this step the legacy builder is used, `cache-to` is accepted
        # and silently discarded, and this whole lab measures nothing.
        uses: docker/setup-buildx-action@v4

      - name: Build and push
        id: build
        uses: docker/build-push-action@v7
        with:
          context: .
          file: ./docker/Dockerfile.test-runner
          push: ${{ steps.decide.outputs.push == 'true' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          # `mode=max` caches intermediate stages too. The default `mode=min`
          # stores only the final layer, so the `deps` stage above -- the only
          # slow part -- would be rebuilt every run.
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            PYTHON_VERSION=3.13
        env:
          # Plain progress output, so the cache lines are readable instead of
          # collapsed into an animated summary.
          BUILDKIT_PROGRESS: plain
```

The write-up the lab asks for:

| Run | Cache state | `pip install` stage | Total build step |
| --- | --- | --- | --- |
| 1 (cold) | nothing to import; exports on completion | executed in full | ~2m 40s |
| 2 (unchanged) | imported | reported `CACHED` | ~20s |
| 3 (after editing only test code) | imported | reported `CACHED` | ~25s |

The log line proving the import, from the start of run 2's build:

```text
importing cache manifest from gha:...
```

and, against the `deps` stage:

```text
CACHED [deps 3/3] RUN pip install --no-cache-dir --disable-pip-version-check --prefix=/install -r /tmp/requirements.txt
```

Treat the absence of `importing cache manifest` as the diagnostic. It means the
cache was never read, and the cause is almost always a missing
`setup-buildx-action` rather than anything about the cache configuration.

**Why this works.** `cache-to: type=gha` exports BuildKit's layer blobs into the
Actions cache service at the end of the build; `cache-from: type=gha` imports
them at the start, so BuildKit can match layer digests and skip work. Both are
BuildKit-only features, which is what makes `setup-buildx-action` non-optional.
`mode=max` is what makes it useful on a multi-stage Dockerfile: `mode=min` stores
only the layers present in the final image, and the `deps` stage's layers are not
in the final image — only its `/install` output is copied in — so `mode=min`
would rebuild the expensive stage on every run while still reporting a cache
hit for the trivial final layers.

Two properties of the `type=gha` backend govern what you will actually measure.
It is **branch-scoped** like every Actions cache, so a PR branch can read the
default branch's cache but writes only to its own scope — the first build on a
new branch imports, but the second build on that branch is the first to hit its
own export. And an entry unused for **7 days is evicted**, so a cold run after a
quiet week is expected and is not a misconfiguration.

**Verify the failure mode the lab asks for.** Do it twice. First remove
`mode=max`, leaving `cache-to: type=gha`, and run twice: the final layers report
`CACHED` and the `pip install` stage still runs, so the total time barely moves —
which is precisely the observation that makes people conclude GHA caching does
not work. Then remove the `setup-buildx-action` step entirely with `mode=max`
restored: the build still succeeds, `cache-to` raises no error at all, and
`importing cache manifest` never appears. Two different silent failures with the
same symptom, distinguished only by that log line.

**Common wrong answer.** Concluding the cache is broken and adding
`cache-from: type=gha,scope=${{ github.ref_name }}` or similar scope tuning. That
addresses a problem you do not have and makes things worse, because a per-branch
scope stops the branch from reading the default branch's warm cache at all. Fix
the builder and the mode first; only reach for `scope=` when you have a specific
reason to isolate two build variants that would otherwise overwrite each other's
entries.

</details>

---

[Solutions Index](./README.md) | [Module 23](../modules/module-23-docker-publish.md) | [Course Home](../README.md)
