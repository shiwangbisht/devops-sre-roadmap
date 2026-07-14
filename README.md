# DevOps → SRE Roadmap

**Goal:** go from "Ops support, 3 YOE" to a DevOps/SRE who can answer *"what would you do if..."* with the same confidence as a lead — not just name the tool, but reason about the tradeoff.

## How this repo works

- Each numbered folder is a module. `00` is a fast revision pass on fundamentals — do it first. Modules `01-04` and `09` build on things you already run in production or in your practice repos — the work there is to go from "I've used it" to "I can explain every failure mode and defend a design decision about it." Modules `05-08` are new ground.
- Every module README has three sections: **Depth checklist** (what "I actually know this" looks like), **Scenario projects** (build/break/fix — this is what produces interview-ready reasoning), and **Where you already have evidence** (pointers into your other repos/production experience).
- Work modules roughly in order, but `01` (Kubernetes) and `02` (AWS) can run in parallel with `08` (SRE fundamentals) since fundamentals reframe how you talk about the hands-on work.
- Close a module by: finishing its scenario projects, writing 1 short "incident writeup" per module (see `08-sre-fundamentals`) in your own words, and checking its box below.

## Learning order

Start with basics, then go deep — a revision pass on fundamentals before the production-depth material, so the depth actually sticks instead of being memorized commands on shaky footing. After that, two tracks run the whole time and everything else is sequential and dependency-driven — each step deliberately builds on artifacts from the one before it so scenario projects get more realistic as you go, instead of disconnected toy exercises.

**Step 0 (do first, revision pass):** [00 — DevOps Fundamentals](00-basics/README.md) — Linux, networking, Git, Docker, and cloud basics. Most of this is stuff you already know from 3 years of Ops work; the point is confirming the mechanism, not the command.

**Continuous track (start alongside 00, never "finish"):** [08 — SRE fundamentals](08-sre-fundamentals/README.md) (it's vocabulary, low effort, reframes everything else immediately) + [07 — Scripting](07-scripting/README.md) (you'll want it for every later scenario project).

**Sequential track (depth, after step 0):**

1. **[01 — Kubernetes & container SRE](01-kubernetes-sre/README.md)** — start here. It's your daily driver already, so it's the fastest path to a confident interview story, and every later module (CI/CD, observability) needs a cluster to target.
2. **[05 — Terraform / IaC](05-terraform-iac/README.md)** — codify the cluster/infra you just got sharp on in step 1. Doing IaC *after* you're confident in the target system is easier than learning both at once.
3. **[02 — AWS cloud](02-aws-cloud/README.md)** — you already have broad exposure; now you have the IaC skill from step 2 to formalize it as reproducible code instead of console clicks.
4. **[06 — CI/CD & GitOps](06-cicd-gitops/README.md)** — now that you have a cluster (1) and IaC (2) to deploy, build the pipeline that deploys to them for real instead of a toy repo.
5. **[03 — Observability](03-observability/README.md)** — once 1–4 give you real running services, observability has something real to watch instead of a synthetic demo.
6. **[04 — Databases](04-databases/README.md)** — slot in here; you can also wire DB metrics into the alerting you just built in step 5.
7. **[09 — Linux & networking](09-linux-networking/README.md)** — do the deep-dive/writeup pass last, especially the SIP postmortem — it benefits most from the SRE vocabulary you've been building since day one in track 08, and it's your strongest differentiator, so end on it.

## Progress tracker

| Order | Module | Status |
|---|---|---|
| 0 | [DevOps Fundamentals](00-basics/README.md) *(do first)* | ☐ Not started |
| ~ | [SRE fundamentals](08-sre-fundamentals/README.md) *(continuous)* | ☐ Not started |
| ~ | [Scripting](07-scripting/README.md) *(continuous)* | ☐ Not started |
| 1 | [Kubernetes & container SRE](01-kubernetes-sre/README.md) | ☐ Not started |
| 2 | [Terraform / IaC](05-terraform-iac/README.md) | ☐ Not started |
| 3 | [AWS cloud](02-aws-cloud/README.md) | ☐ Not started |
| 4 | [CI/CD & GitOps](06-cicd-gitops/README.md) | ☐ Not started |
| 5 | [Observability](03-observability/README.md) | ☐ Not started |
| 6 | [Databases](04-databases/README.md) | ☐ Not started |
| 7 | [Linux & networking](09-linux-networking/README.md) | ☐ Not started |

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

You already sit on something most candidates don't have: **real production incidents on high-traffic SIP/telecom infra.** Every module's scenario projects are a substitute for real incidents — but your actual incidents are worth more. After you resolve a real prod issue at work, spend 15 minutes writing it up using the template in [08-sre-fundamentals](08-sre-fundamentals/README.md) (sanitized, no company/customer data). That folder becomes your strongest interview material — it's the difference between "I know Kubernetes" and "here's a rollout that took down a node pool and how I found it."
