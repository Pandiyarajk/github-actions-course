# Module 23: Building and Publishing Docker Images

![Module](https://img.shields.io/badge/Module-23-1f6feb?style=flat-square) ![Part](https://img.shields.io/badge/Part%20C%20Platform-bf3989?style=flat-square) ![Level](https://img.shields.io/badge/Level-Intermediate-d29922?style=flat-square) ![Time](https://img.shields.io/badge/Time-150%20min-555?style=flat-square)

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 22](./module-22-container-jobs.md) | [Next: Module 24](./module-24-supply-chain-security.md)
> Level: **Intermediate** | Time: **150 min** | Example workflow: [`module-23-docker-publish.yml`](../examples/module-23-docker-publish.yml)
> Solutions: [`module-23-solutions.md`](../solutions/module-23-solutions.md)

## Learning Objectives

- Build and push an image to GHCR using `docker/build-push-action`.
- Authenticate to GHCR with `GITHUB_TOKEN` and the correct `permissions:`.
- Cache layers between runs with `cache-from`/`cache-to: type=gha`.
- Derive tags and labels automatically with `docker/metadata-action`.

## Key Concepts

buildx, BuildKit, GHCR, `packages: write`, layer cache, `type=gha`, `docker/metadata-action`, multi-arch, `platforms`

## Expected Outcome

You can publish a versioned test-runner image to GHCR on every tag push, with warm layer caching and tags derived from the git ref rather than hand-written.

## Concept Flow

```text
setup-buildx  ->  login (GHCR)  ->  metadata (tags/labels)  ->  build-push
                                                                  |
                                          cache-from: type=gha  <--+--> cache-to: type=gha
```

---

## ELI5 Explanation

A Docker image is a frozen computer you can hand to anyone. This module is about baking that image in CI and putting it on a shelf (a registry) with a sensible label, so a later job — or a colleague — can take it down and run it without installing anything.

The expensive part is baking. Layer caching means that if only your test code changed, the pip-install layer is reused instead of redone.

## Technical Explanation

Publishing an image from Actions has four moving parts.

**buildx.** `docker/setup-buildx-action` installs a BuildKit builder. This is what enables the `type=gha` cache backend, multi-platform builds, and build secrets. Without it, `build-push-action` falls back to the legacy builder and `cache-to` silently does nothing.

**Registry login.** GHCR (`ghcr.io`) accepts the automatically-minted `GITHUB_TOKEN`, so no PAT is needed for images owned by the same repository. It requires the job to declare `permissions: packages: write`, which is *not* in the default token grant. Missing that permission produces a `denied` on push, which reads as a credentials problem rather than a permissions one.

**Tags and labels.** `docker/metadata-action` turns the git ref into a tag set: a semver tag from `v1.2.3`, a branch tag, a `sha-` tag, and `latest` on the default branch. Hand-writing tags is where images end up published as `latest` only, with no way to roll back.

**Layer cache.** `cache-from: type=gha` and `cache-to: type=gha,mode=max` store layers in the Actions cache. `mode=max` caches intermediate layers too, which matters for multi-stage builds; the default `mode=min` caches only the final layer and gives most of the benefit away. Note this cache shares the repository's 10 GB Actions cache budget with everything else — see Module 16.

Two facts about the `type=gha` cache that catch people out: it is **branch-scoped** like all Actions caches, so a PR branch reads the default branch's cache but writes its own; and a cache entry unused for 7 days is evicted, so the first run after a quiet week is cold regardless of configuration.

## Real-World Use Case

The Behave/Selenium suite needs Python 3.13, Chrome, a matching chromedriver, and roughly forty pip packages. Installing all of that per run took just over four minutes on every one of fifteen workflows. Baking it into an image published on each release, then consuming that image as a `container:` job (Module 22), moved the cost to once per release and cut per-run setup to the time it takes to pull a cached layer.

## When To Use

- The environment takes longer to install than the tests take to run.
- Multiple workflows or repositories need an identical toolchain.
- You need the environment to be reproducible months later, pinned by digest.
- You are shipping the application itself as a container.

## When NOT To Use

- Setup is already fast — `setup-python` with `cache: pip` is simpler and needs no registry.
- The image would change on nearly every commit, so nothing is ever cached.
- You only need a service like a database or a browser grid; consume an existing published image via `services:` instead (Module 22).
- You cannot grant `packages: write`, and no other registry credentials are available.

## Common Mistakes

- Forgetting `permissions: packages: write`. The push fails with `denied`, which looks like bad credentials.
- Using `docker/build-push-action` without `setup-buildx-action`. `cache-to` is accepted and does nothing, so builds stay slow with no error.
- Writing `cache-to: type=gha` without `mode=max` on a multi-stage build, then concluding GHA caching does not work.
- Pushing only `latest`. There is then no way to say which image a failing run used.
- Adding `platforms: linux/amd64,linux/arm64` without realising it roughly doubles build time, and that a multi-arch build cannot be `load`ed into the local daemon.
- Interpolating `${{ github.event.* }}` into a Dockerfile build arg — the same script-injection vector as in `run:` blocks (Module 24).
- Capitalising the image name. GHCR requires lowercase; `${{ github.repository }}` on a repo with capitals must be lowercased first.
- Expecting `docker build` inside a `container:` job to work — the job container has no Docker daemon.

## Debugging Tips

- `denied: permission_denied` on push → check `permissions: packages: write` before touching credentials.
- Cache appearing not to work → confirm `setup-buildx-action` ran, then look for `importing cache manifest` in the build log; its absence means the cache was never read.
- A first-push failure on a brand-new package is often package visibility: the package is created private, and a later job pulling it needs either `packages: read` or the package made public.
- Add `--progress=plain` via `build-args` or set `BUILDKIT_PROGRESS: plain` in `env` to get readable, non-collapsed build logs.
- To see exactly which tags were computed, print `steps.meta.outputs.tags` before the build rather than inferring from the push output.
- If the build succeeds locally but not in CI, compare `.dockerignore` — a large context can change which layers invalidate.

## Reference: the action set

| Action | Pinned version | Purpose |
| --- | --- | --- |
| `docker/setup-buildx-action` | `v4` | Install the BuildKit builder; required for `type=gha` cache |
| `docker/login-action` | `v4` | Authenticate to GHCR or another registry |
| `docker/metadata-action` | `v6` | Derive tags and OCI labels from the git ref |
| `docker/build-push-action` | `v7` | Build and push, with cache and multi-arch support |
| `docker/setup-qemu-action` | `v4` | Only needed for cross-architecture builds |

## Minimal Workflow Example

```yaml
name: Publish Image

on:
  push:
    branches:
      - main

# `packages: write` is NOT part of the default token grant. Without it the push
# fails with `denied`.
permissions:
  contents: read
  packages: write

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Buildx
        uses: docker/setup-buildx-action@v4

      - name: Log in to GHCR
        uses: docker/login-action@v4
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v7
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
```

### YAML Explanation

- `permissions.packages: write` grants the token push access to GHCR; `contents: read` keeps everything else least-privilege.
- `secrets.GITHUB_TOKEN` is minted per run and needs no manual configuration.
- `setup-buildx-action` must precede the build for BuildKit features to be available.
- `context: .` is the build context; a `.dockerignore` controls what is actually sent.
- `push: true` distinguishes a publish from a build-only validation run.

### Step-by-Step Execution

1. A commit lands on `main`.
2. The repository is checked out and a BuildKit builder is created.
3. The runner logs in to `ghcr.io` with the run's token.
4. BuildKit builds the image from the Dockerfile.
5. The image is pushed as `ghcr.io/<owner>/<repo>:latest`.
6. The package appears under the repository's Packages tab, initially private.

## Production Workflow Example

```yaml
name: Publish Test Runner Image

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
  group: publish-image-${{ github.ref }}
  cancel-in-progress: false   # never cancel a half-finished push

jobs:
  publish:
    name: Build and publish
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.meta.outputs.tags }}
      digest: ${{ steps.build.outputs.digest }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      # GHCR rejects uppercase image names, and `github.repository` preserves the
      # repository's capitalisation. Normalise it rather than assuming.
      - name: Compute lowercase image name
        id: name
        run: |
          echo "image=ghcr.io/${GITHUB_REPOSITORY,,}/test-runner" >> "$GITHUB_OUTPUT"

      - name: Set up Buildx
        uses: docker/setup-buildx-action@v4

      - name: Log in to GHCR
        uses: docker/login-action@v4
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # Derives the full tag set from the ref instead of hand-writing it:
      # v1.2.3 -> 1.2.3, 1.2, 1, plus sha- and latest.
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

      - name: Show computed tags
        run: echo "${{ steps.meta.outputs.tags }}"

      - name: Build and push
        id: build
        uses: docker/build-push-action@v7
        with:
          context: .
          file: ./docker/Dockerfile.test-runner
          # On a manual run, default to build-only so the workflow can be
          # exercised without publishing.
          push: ${{ github.event_name == 'push' || inputs.push }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          # `mode=max` caches intermediate stages too. The default `mode=min`
          # keeps only the final layer and gives away most of the benefit on a
          # multi-stage build.
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: true

      - name: Record published digest
        run: |
          {
            echo "## Published image"
            echo
            echo "| Field | Value |"
            echo "| --- | --- |"
            echo "| Digest | \`${{ steps.build.outputs.digest }}\` |"
            echo "| Pushed | ${{ github.event_name == 'push' || inputs.push }} |"
            echo
            echo "Consume this image by digest for reproducibility:"
            echo
            echo '```yaml'
            echo "container:"
            echo "  image: ${{ steps.name.outputs.image }}@${{ steps.build.outputs.digest }}"
            echo '```'
          } >> "$GITHUB_STEP_SUMMARY"
```

### YAML Explanation

- `${GITHUB_REPOSITORY,,}` is bash lowercasing; GHCR rejects uppercase names.
- `cancel-in-progress: false` protects a push midway through uploading layers.
- `metadata-action` emits both `tags` and `labels`; the labels become OCI annotations that record source and revision.
- `push:` is an expression, so the same workflow serves as a tag-triggered publish and a manual build-only check.
- `steps.build.outputs.digest` is the immutable identifier — consuming an image by digest rather than tag is what makes a later run reproducible.
- `provenance: true` attaches build provenance attestation, which Module 24 uses.

### Expected Output

- A tag push of `v1.4.0` publishes `1.4.0`, `1.4`, `1`, `sha-<short>`, and `latest`.
- The second run against an unchanged Dockerfile shows `importing cache manifest` and finishes substantially faster.
- The job summary contains the digest and a copy-pasteable `container:` block.
- A manual run with `push: false` builds and caches without publishing.

## Quiz

1. A push to GHCR fails with `denied`. The `GITHUB_TOKEN` is being passed correctly. What is the most likely cause?
   - **A.** The token has expired and must be regenerated.
   - **B.** The job is missing `permissions: packages: write`.
   - **C.** GHCR requires a personal access token; `GITHUB_TOKEN` never works.
   - **D.** `docker/login-action` must be given a registry password from a secret named `GHCR_TOKEN`.

2. A workflow sets `cache-to: type=gha,mode=max` but builds are never faster. Which omission best explains it?
   - **A.** `cache-from` was not set to `type=gha`.
   - **B.** `docker/setup-buildx-action` was not run.
   - **C.** `provenance` was left at its default.
   - **D.** The Dockerfile has too few layers to cache.

3. Which value should a downstream `container:` job reference to guarantee it runs the exact image a release published?
   - **A.** The `latest` tag.
   - **B.** The semver tag, for example `1.4.0`.
   - **C.** The image digest from `steps.<id>.outputs.digest`.
   - **D.** The short SHA tag.

4. `${{ github.repository }}` is `Pandiyarajk/GitHub-Actions-Course`. Explain why using it directly as a GHCR image name fails, and give a fix.

5. A team adds `platforms: linux/amd64,linux/arm64` and their build time roughly doubles while a later `docker load` step starts failing. Explain both effects.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Publish a minimal image containing Python 3.13 and `behave` to GHCR on push to `main`. | The package appears under the repository; removing `packages: write` reproduces the `denied` error. |
| Intermediate | Add `docker/metadata-action` and a `v*.*.*` tag trigger so a tag push produces semver, short-SHA, and `latest` tags. | A tag push yields the full tag set; `steps.meta.outputs.tags` printed in the log matches. |
| Challenge | Add `type=gha` layer caching with `mode=max`, run the workflow twice unchanged, and record the build-time difference and the log line proving the cache was imported. | A documented before/after with the `importing cache manifest` line quoted. |

Solutions: [`solutions/module-23-solutions.md`](../solutions/module-23-solutions.md)

---

[Previous: Module 22](./module-22-container-jobs.md) | [Module Index](./README.md) | [Next: Module 24](./module-24-supply-chain-security.md)
