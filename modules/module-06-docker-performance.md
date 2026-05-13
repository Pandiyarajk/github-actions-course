# Module 6: Docker, Artifacts, Caching, and Performance

> Navigation: [Course Home](../README.md) | [Module Index](./README.md) | [Previous: Module 5](./module-05-multi-language-tests.md) | [Next: Module 7](./module-07-release-automation.md)
> Level: **Intermediate** | Time: **150 min** | Example workflow: [`module-06-docker-performance.yml`](../examples/module-06-docker-performance.yml)

## Learning Objectives

- Build and tag Docker images in Actions.
- Use artifacts and cache intentionally.
- Optimize slow builds without hiding failures.

## Key Concepts

Docker Buildx, GHCR, dependency cache, layer cache, artifacts, timeouts

## Expected Outcome

You can package applications, preserve useful outputs, and reduce workflow runtime.

## Concept Flow

```text
Source Code -> Docker Buildx -> Layer Cache -> Image Tag -> Artifact / GHCR Publish
```

---

## ELI5 Explanation

Docker packages your app into a box that runs the same way everywhere. Artifacts are files saved from a workflow. Cache is a shortcut that saves downloaded dependencies so future runs are faster.

## Technical Explanation

Docker workflows build container images, test them, and optionally push them to registries such as GHCR. Artifacts preserve outputs like reports, binaries, screenshots, and logs. Caching reduces runtime by restoring dependencies. Performance optimization includes dependency caching, job parallelization, selective triggers, and avoiding unnecessary work.

## Real-World Use Case

A backend service should build a Docker image on every pull request and push the image only after merging to `main`.

## When To Use

- Your app deploys as a container.
- You need consistent runtime environments.
- You want to scan or publish images.
- Dependency installation is slow and cache keys can use lock files.

## When NOT To Use

- The project does not deploy as a container.
- A language-native build is enough.
- Dependencies change so often that cache hit rate is poor.
- Cache restore risks stale state.

## Common Mistakes

- Pushing images from pull requests from forks.
- Not using lock files in cache keys.
- Uploading huge artifacts unnecessarily.
- Building images without tags that identify commit or version.

## Debugging Tips

- Use `docker build --progress=plain`.
- Print cache hit status.
- Keep artifacts small and named clearly.
- Use `timeout-minutes` for expensive jobs.

## Minimal Workflow Example

```yaml
name: Docker Build

on: push

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t my-app:${{ github.sha }} .
```

### YAML Explanation

- The workflow runs on every push.
- `checkout` downloads the Dockerfile and source.
- `docker build` creates an image tagged with the commit SHA.

### Step-by-Step Execution

1. Push triggers workflow.
2. Runner checks out code.
3. Docker builds the image.
4. Image is tagged with commit SHA.

## Production Workflow Example

```yaml
name: Docker Build and Publish

on:
  push:
    branches:
      - main
  pull_request:

permissions:
  contents: read
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Login to GitHub Container Registry
        if: ${{ github.event_name == 'push' }}
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Build image for pull requests
        if: ${{ github.event_name == 'pull_request' }}
        uses: docker/build-push-action@v6
        with:
          context: .
          push: false
          tags: ghcr.io/${{ github.repository }}/app:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      - name: Build and push image on main
        if: ${{ github.event_name == 'push' }}
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/app:${{ github.sha }}
            ghcr.io/${{ github.repository }}/app:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### YAML Explanation

- Pull requests build images but do not push them.
- Pushes to `main` log in to GHCR and publish images.
- `packages: write` allows publishing to GitHub Packages.
- Buildx cache improves future image build speed.

### Expected Output

- Pull requests build but do not push images.
- Main branch pushes image to GHCR.
- Docker layer cache improves future build speed.

## Labs

| Difficulty | Task | Expected Output |
| --- | --- | --- |
| Beginner | Build a Docker image on push. | Docker build succeeds. |
| Intermediate | Upload build logs or reports as artifacts. | Artifact appears after run. |
| Challenge | Push image to GHCR only from `main`. | PRs build only; main publishes. |

---

[Previous: Module 5](./module-05-multi-language-tests.md) | [Module Index](./README.md) | [Next: Module 7](./module-07-release-automation.md)
