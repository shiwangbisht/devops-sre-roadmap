# 00 — DevOps Fundamentals (start here, revise before depth)

You already have 3 years of hands-on experience, so most of this will be revision, not new material — that's the point. The goal of this module is to make sure the *foundations underneath* everything in modules 01–09 are solid, so the depth material actually sticks instead of feeling like memorized commands. Move fast through what you already know; slow down only where you find a real gap.

## Depth checklist

- [ ] **Linux fundamentals:** filesystem hierarchy, users/groups/permissions (including sticky bit, umask), package management (apt/yum), process basics (ps, systemd/systemctl, how a service actually starts), file descriptors and redirection, environment variables
- [ ] **Shell basics:** navigating and scripting comfortably in Bash before you rely on it for automation (module 07 goes deep — this is just "no hesitation at a Linux terminal")
- [ ] **Networking fundamentals:** OSI/TCP-IP model in practical terms, IP addressing and subnetting (CIDR notation), ports and sockets, how HTTP/HTTPS actually works on the wire, basic DNS record types (A, CNAME, MX, TXT)
- [ ] **Git:** not just add/commit/push — branching strategies, rebase vs merge, resolving a real conflict, reverting a bad commit safely in a shared branch
- [ ] **Containers (Docker), before Kubernetes:** what a container actually is (namespaces + cgroups, at a conceptual level), image layers and caching, writing a decent Dockerfile, volumes vs bind mounts, container networking basics — this underpins everything in module 01
- [ ] **Cloud computing basics:** IaaS vs PaaS vs SaaS, what a region/availability zone actually is and why it matters for design, the shared responsibility model — the conceptual layer underneath module 02's AWS specifics
- [ ] **Basic systems concepts:** what a load balancer does, what a reverse proxy does, client-server vs peer-to-peer, synchronous vs asynchronous communication — vocabulary that every later module assumes you have

## Where to learn

- man7.org/linux/man-pages — canonical Linux reference (same one linked in module 09, worth knowing now)
- git-scm.com/book — the official Git book, free online
- docs.docker.com/get-started — official Docker fundamentals
- docs.aws.amazon.com — for the cloud-basics concepts (shared responsibility model, regions/AZs), even though the deep AWS content is module 02

## Scenario projects

1. **Terminal-only day.** Spend one session doing a normal task (find a file, check disk usage, find what's using a port, tail a log) using only the shell — no GUI file managers, no `top` shortcuts you don't understand. If anything makes you pause, that's your actual gap, not a hypothetical one.
2. **Write a real Dockerfile from scratch** for something small (a simple script or app) — multi-stage if you can, with a sane `.dockerignore` and a non-root user. Then explain out loud why each layer is ordered the way it is (build cache).
3. **Git conflict, on purpose.** Branch, make conflicting changes on two branches, merge, resolve the conflict by hand (not "accept theirs" blindly) — then do the same scenario with rebase instead of merge and compare what the history looks like afterward.
4. **Subnet a network on paper.** Given a CIDR block, work out the usable host range, broadcast address, and how you'd split it into 4 smaller subnets — no calculator/tool.

## Self-test — can you answer these cold, before moving to module 01?

1. What's the practical difference between a container and a VM — not the marketing answer, the actual mechanism?
2. Given `10.0.0.0/22`, how many usable host addresses are there, and what's the broadcast address?
3. `rebase` vs `merge` — what does each actually do to history, and when would picking the wrong one bite you on a shared branch?
4. What happens, step by step, when you type a URL into a browser and hit enter, down through DNS and TCP?
5. Why does a Docker image with `RUN apt-get update && apt-get install -y foo` in one layer build differently (and often better) than doing it as two separate `RUN` lines?
6. What's the shared responsibility model, in your own words, and where's the line for something like RDS vs EC2?

## Where you already have evidence

Almost everything here you've touched already through 3 years of Ops work and your startup infra builds — this module is a deliberate pass to convert "I've done this" into "I can explain the mechanism," which is exactly the gap the rest of the [roadmap](../README.md) is designed to close.
