# DevOps → SRE Roadmap

**Goal:** build real DevOps/SRE depth from the ground up, starting from Linux fundamentals, until you can answer *"what would you do if..."* by reasoning about the tradeoff — not just naming a tool.

**Starting point:** ops support background, but treat every module as new material to actually learn, not revise. Where a module touches something you've been near at work (SIP/telecom infra, day-to-day Ops tickets), that's real experience worth mining for interview stories once you understand the mechanics underneath it — it is not a shortcut past learning the mechanics.

## How this repo works

- Each numbered folder is a module. The folder numbers are historical (kept stable so links/issues don't break) — they are **not** the learning order; see below for the actual order.
- Every module README has: a **Depth checklist** (what "I actually know this" looks like), **Scenario projects** (build/break/fix — this is what produces interview-ready reasoning), and a **Related practice/reference** section (pointers into sibling repos or real work experience you can apply the material to *after* you've learned it).
- Close a module by: finishing its scenario projects, writing 1 short "incident writeup" per module (see `08-sre-fundamentals`) in your own words, and checking its box below.

## Learning order

Linux first — everything else (Kubernetes, networking in AWS, CI/CD, observability) is built on top of OS and networking concepts, so shaky footing there makes every later module harder than it needs to be. After that, two tracks run the whole time and everything else is sequential and dependency-driven — each step deliberately builds on artifacts from the one before it so scenario projects get more realistic as you go, instead of disconnected toy exercises.

**Step 1 (do first, from zero):** [09 — Linux, Zero to Advanced](09-linux-networking/README.md) — a full 13-level curriculum: OS/shell basics → filesystem/permissions → processes → networking (subnetting, DNS, TCP) → diagnostic tooling → namespaces/cgroups → security → performance, ending on a SIP/telecom capstone. Despite the folder number, do this before `00`.

**Step 2:** [00 — DevOps Fundamentals](00-basics/README.md) — Git, Docker, and cloud basics, built up from scratch (Linux/networking now live entirely in step 1, so this module doesn't duplicate them).

**Continuous track (start alongside 00, never "finish"):** [08 — SRE fundamentals](08-sre-fundamentals/README.md) (vocabulary, low effort, reframes everything else immediately) + [07 — Scripting](07-scripting/README.md) (you'll want it for every later scenario project).

**Sequential track (depth, after step 2):**

1. **[01 — Kubernetes & container SRE](01-kubernetes-sre/README.md)** — start here. You touch this at work already, which makes it the fastest path to a confident interview story once you learn the internals properly, and every later module (CI/CD, observability) needs a cluster to target.
2. **[05 — Terraform / IaC](05-terraform-iac/README.md)** — codify the cluster/infra you just got sharp on in step 1. Doing IaC *after* you're confident in the target system is easier than learning both at once.
3. **[02 — AWS cloud](02-aws-cloud/README.md)** — you've touched pieces of this building startup infra; now you have the IaC skill from step 2 to formalize it as reproducible code instead of console clicks.
4. **[06 — CI/CD & GitOps](06-cicd-gitops/README.md)** — now that you have a cluster (1) and IaC (2) to deploy, build the pipeline that deploys to them for real instead of a toy repo.
5. **[03 — Observability](03-observability/README.md)** — once 1–4 give you real running services, observability has something real to watch instead of a synthetic demo.
6. **[04 — Databases](04-databases/README.md)** — slot in here; you can also wire DB metrics into the alerting you just built in step 5.

## Progress tracker

| Order | Module | Status |
|---|---|---|
| 1 | [Linux, Zero to Advanced](09-linux-networking/README.md) *(do first)* | ☐ Not started |
| 2 | [DevOps Fundamentals](00-basics/README.md) | ☐ Not started |
| ~ | [SRE fundamentals](08-sre-fundamentals/README.md) *(continuous)* | ☐ Not started |
| ~ | [Scripting](07-scripting/README.md) *(continuous)* | ☐ Not started |
| 3 | [Kubernetes & container SRE](01-kubernetes-sre/README.md) | ☐ Not started |
| 4 | [Terraform / IaC](05-terraform-iac/README.md) | ☐ Not started |
| 5 | [AWS cloud](02-aws-cloud/README.md) | ☐ Not started |
| 6 | [CI/CD & GitOps](06-cicd-gitops/README.md) | ☐ Not started |
| 7 | [Observability](03-observability/README.md) | ☐ Not started |
| 8 | [Databases](04-databases/README.md) | ☐ Not started |

Update the status column yourself as you go: ☐ Not started → ◐ In progress → ☑ Done. Once the GitHub Project (see below) is set up, that board is the source of truth — update this table or the board, not both independently.

## Tracking this on GitHub (Issues + Project board)

- `.github/ISSUE_TEMPLATE/learning-module.yml` — a GitHub Issue Form. Each field maps to what you asked for: what to learn, where to learn it, and how to self-test.
- `PROJECT_SETUP.md` — step-by-step to create the GitHub repo, the Project board (Backlog → Learning → Practicing → Done), and file one issue per module.
- `scripts/create_github_project.sh` — once you have the `gh` CLI installed and logged in, this one script creates the repo, all 9 module issues (pre-filled from the READMEs), and the Project board automatically.

## Related repos (sibling folders, not submodules — kept independent on purpose)

These already exist and each has its own GitHub remote. Treat them as your evidence/practice folders; the modules above link into them directly:

- `../DataBase` — SQL/NoSQL ops, backups, troubleshooting
- `../ELK_STACK` — Elasticsearch/Logstash/Kibana/Filebeat setup + shard recovery
- `../AWS_VPC/AWS_VPC` — VPC peering
- `../master_linux/master_linux` — Linux process internals
- `../workflows/workflow` — k8s/service-style YAML manifests
- `../GO/packages` — Go practice
- `../prometheus` — Prometheus config

## The one habit that matters most

You sit on something most candidates don't have: **real production exposure to high-traffic SIP/telecom infra.** Once you've built the underlying mechanics (starting with the Linux module above), that real-world exposure becomes genuinely differentiated interview material — but only once you can explain *why*, not just *what happened*. Every module's scenario projects are a substitute for real incidents; your actual incidents are worth more once you can talk about them precisely. After you resolve a real prod issue at work, spend 15 minutes writing it up using the template in [08-sre-fundamentals](08-sre-fundamentals/README.md) (sanitized, no company/customer data). That folder becomes your strongest interview material — it's the difference between "I know Kubernetes" and "here's a rollout that took down a node pool and how I found it."
