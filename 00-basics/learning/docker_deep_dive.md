# Docker — deep dive

## Image layers & caching — why Dockerfile instruction order matters

Every instruction in a Dockerfile (`RUN`, `COPY`, `ADD`...) creates a new, **cached, immutable layer**.
On rebuild, Docker reuses cached layers up to the **first instruction whose content changed** — every
layer after that is rebuilt from scratch, even if its own content didn't change.

```dockerfile
# BAD: any source code change invalidates the dependency-install layer, re-running it every build
FROM node:20
COPY . .
RUN npm install
CMD ["node", "server.js"]
```
```dockerfile
# GOOD: dependency layer only rebuilds when package.json actually changes
FROM node:20
COPY package.json package-lock.json ./
RUN npm install          # cached unless package.json changed
COPY . .                  # source changes don't invalidate the npm install layer above
CMD ["node", "server.js"]
```
**Rule:** order instructions from **least-frequently-changing to most-frequently-changing** — exactly
why dependency manifests get copied and installed before application source code, in every language.

## Multi-stage builds

```dockerfile
FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN go build -o myapp .

FROM alpine:3.19
COPY --from=builder /app/myapp /usr/local/bin/myapp
ENTRYPOINT ["myapp"]
```
The `builder` stage has the entire Go toolchain (hundreds of MB); the final image only contains the
compiled binary copied out of it, on a minimal base — final image is tens of MB instead of ~1GB. This is
*the* production pattern, not an advanced trick — a single-stage build shipping a full compiler toolchain
to production is a real, common review finding.

## `CMD` vs `ENTRYPOINT`

- **`ENTRYPOINT`** — the fixed executable that always runs.
- **`CMD`** — default *arguments* to that executable, overridable at `docker run` time.
```dockerfile
ENTRYPOINT ["myapp"]
CMD ["--port", "8080"]
```
`docker run myimage --port 9090` overrides just the CMD args, `myapp` still always runs. Using `CMD`
alone (no `ENTRYPOINT`) means `docker run myimage anything` replaces the entire command — a common
source of "why did my container just run `bash` instead of my app" confusion.

## Networking modes

- **bridge** (default) — containers get their own private network, NAT'd through the host; need
  explicit port mapping (`-p 8080:80`) to be reachable from outside.
- **host** — container shares the host's network namespace directly — no NAT, no port mapping needed,
  but no network isolation either (and can't run two containers both binding the same port).
- **none** — no networking at all — used for isolated batch/compute workloads with no network need.

## Volumes vs. bind mounts

- **Named volume** — Docker-managed storage, lives outside any container's writable layer, survives
  container removal, portable across containers. The right choice for persistent application data.
- **Bind mount** — maps a specific host path directly into the container. Right choice for local
  development (live-editing source code mounted into a running container) or genuinely needing a
  specific host file/directory — wrong choice for production persistent data (ties the container to one
  specific host's filesystem layout).

## Health checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```
Without this, Docker only knows if the *process* is running, not if the *application* is actually
healthy — a hung-but-still-running process shows as healthy with no `HEALTHCHECK` defined. (This is the
container-level analog of a Kubernetes liveness probe — Kubernetes actually ignores Docker's own
`HEALTHCHECK` and uses its own probes instead, worth knowing so you don't assume they stack.)

## Image size & security hygiene

- Use minimal base images (`alpine`, `distroless`) where the app allows it — smaller attack surface,
  faster pulls.
- `.dockerignore` — exclude `.git`, `node_modules`, local `.env` files from the build context; a huge
  build context slows every build and risks accidentally `COPY`-ing secrets into a layer.
- **Secrets never belong in a layer** — even if a later layer deletes a file, it still exists in the
  earlier layer's history, retrievable via `docker history`/image export. Use build-time secret mounts
  (`RUN --mount=type=secret`) or runtime env injection, never `COPY secrets.txt .` followed by `RUN rm
  secrets.txt`.
- Run as a non-root user (`USER appuser` in the Dockerfile) — same least-privilege logic as everywhere
  else in this roadmap.

---

## Interview questions (with the short answer you should be able to give cold)

1. *Why does Dockerfile instruction order affect build speed, not just readability?* — Each instruction
   creates a cached layer; a rebuild reuses layers up to the first changed instruction, invalidating
   everything after it. Ordering from least- to most-frequently-changing (dependencies before source
   code) maximizes cache reuse on rebuilds.
2. *What problem does a multi-stage build solve?* — Keeps the final production image free of build-time
   tooling (compilers, full SDKs) that was only needed to produce the artifact — copying just the
   compiled output into a minimal final-stage image instead of shipping the entire build toolchain to production.
3. *What's the actual difference between `CMD` and `ENTRYPOINT`, and what breaks if you only use
   `CMD`?* — `ENTRYPOINT` is the fixed command that always runs; `CMD` provides default, overridable
   arguments to it. With only `CMD` and no `ENTRYPOINT`, any arguments passed to `docker run` replace the
   entire command instead of just overriding arguments — `docker run myimage bash` runs `bash` instead
   of the intended app.
4. *Why is `COPY secrets.txt . && RUN rm secrets.txt` not actually secure?* — Each instruction is its own
   immutable layer — deleting the file in a later layer doesn't remove it from the earlier layer's
   history; it's still retrievable from the image (`docker history`, exporting layers) even though it's
   not visible in the final running container's filesystem.
5. *When would you use `host` networking instead of the default `bridge` mode, and what's the
   tradeoff?* — When you need maximum network performance (no NAT overhead) or the app genuinely needs
   to bind to the host's network directly — tradeoff is losing network isolation entirely, and you can't
   run two containers both wanting the same port on host networking.
6. *Why shouldn't you use a bind mount for a production database's data directory?* — It ties the data
   to one specific host's filesystem path/layout, isn't portable if the container gets rescheduled to a
   different host, and doesn't get Docker's own volume lifecycle management — a named volume (or, in
   Kubernetes, a PVC) is the portable, managed equivalent.
7. *Does Kubernetes use a container's Dockerfile `HEALTHCHECK` for its liveness/readiness probes?* — No
   — Kubernetes ignores the image's own `HEALTHCHECK` entirely and uses its own
   `livenessProbe`/`readinessProbe` defined in the pod spec; the two mechanisms don't stack or share
   configuration, a common point of confusion for anyone coming from plain Docker.