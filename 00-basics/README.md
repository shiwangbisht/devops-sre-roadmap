# 00 — DevOps Fundamentals (Git, Docker, Cloud)

Linux and networking now have their own full zero-to-advanced curriculum in [09 — Linux, Zero to Advanced](../09-linux-networking/README.md) — do that module first. This module covers the rest of the foundational layer everything else in the roadmap assumes: Git beyond `add`/`commit`/`push`, containers before Kubernetes, and cloud computing vocabulary before the AWS-specific depth in module 02. Build these up from scratch — don't assume you already know them because you've used `git push` or run a container before; there's a difference between having used a tool and being able to explain what it's actually doing.

## Depth checklist

- [ ] **Git:** not just add/commit/push — branching strategies, rebase vs merge (what each actually does to history), resolving a real conflict by hand, reverting a bad commit safely on a shared branch
- [ ] **Containers (Docker), before Kubernetes:** what a container actually is (namespaces + cgroups conceptually — full depth is in module 09, Level 10), image layers and build caching, writing a decent Dockerfile, volumes vs bind mounts, container networking basics — this underpins everything in module 01
- [ ] **Cloud computing basics:** IaaS vs PaaS vs SaaS, what a region/availability zone actually is and why it matters for design, the shared responsibility model — the conceptual layer underneath module 02's AWS specifics
- [ ] **Basic systems concepts:** what a load balancer does, what a reverse proxy does, client-server vs peer-to-peer, synchronous vs asynchronous communication — vocabulary every later module assumes you have

## Where to learn

- [Pro Git book](https://git-scm.com/book/en/v2) — the official Git book, free online
- [Docker — Get started](https://docs.docker.com/get-started/) — official Docker fundamentals
- [AWS — What is cloud computing](https://aws.amazon.com/what-is-cloud-computing/) and [shared responsibility model](https://aws.amazon.com/compliance/shared-responsibility-model/) — for the cloud-basics concepts, even though the deep AWS content is module 02

## Scenario projects

1. **Write a real Dockerfile from scratch** for something small (a simple script or app) — multi-stage if you can, with a sane `.dockerignore` and a non-root user. Then explain out loud why each layer is ordered the way it is (build cache).
2. **Git conflict, on purpose.** Branch, make conflicting changes on two branches, merge, resolve the conflict by hand (not "accept theirs" blindly) — then do the same scenario with rebase instead of merge and compare what the history looks like afterward.

## Self-test — can you answer these cold, before moving to module 01?

1. What's the practical difference between a container and a VM — not the marketing answer, the actual mechanism?
2. `rebase` vs `merge` — what does each actually do to history, and when would picking the wrong one bite you on a shared branch?
3. Why does a Docker image with `RUN apt-get update && apt-get install -y foo` in one layer build differently (and often better) than doing it as two separate `RUN` lines?
4. What's the shared responsibility model, in your own words, and where's the line for something like RDS vs EC2?

## Related practice/reference

- This module's material builds directly toward module 01 (Kubernetes) and module 02 (AWS) — expect to revisit the Docker and cloud-basics sections when those modules get concrete.
