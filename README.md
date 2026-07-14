# DevOps → SRE Roadmap

**Goal:** go from "Ops support, 3 YOE" to a DevOps/SRE who can answer *"what would you do if..."* with the same confidence as a lead — not just name the tool, but reason about the tradeoff.

## How this repo works

- Each numbered folder is a module. Modules `01-04` and `09` build on things you already run in production or in your practice repos — the work there is to go from "I've used it" to "I can explain every failure mode and defend a design decision about it." Modules `05-08` are new ground.
- Every module README has three sections: **Depth checklist** (what "I actually know this" looks like), **Scenario projects** (build/break/fix — this is what produces interview-ready reasoning), and **Where you already have evidence** (pointers into your other repos/production experience).
- Work modules roughly in order, but `01` (Kubernetes) and `02` (AWS) can run in parallel with `08` (SRE fundamentals) since fundamentals reframe how you talk about the hands-on work.
- Close a module by: finishing its scenario projects, writing 1 short "incident writeup" per module (see `08-sre-fundamentals`) in your own words, and checking its box below.

## Progress tracker

| # | Module | Status | Priority |
|---|---|---|---|
| 01 | [Kubernetes & container SRE](01-kubernetes-sre/README.md) | ☐ Not started | High — daily driver, biggest interview leverage |
| 02 | [AWS cloud](02-aws-cloud/README.md) | ☐ Not started | High — broad exposure already, needs structuring |
| 03 | [Observability (ELK/Prometheus/Grafana)](03-observability/README.md) | ☐ Not started | Medium — strong base, deepen alerting design |
| 04 | [Databases](04-databases/README.md) | ☐ Not started | Medium |
| 05 | [Terraform / IaC](05-terraform-iac/README.md) | ☐ Not started | **Gap — start early** |
| 06 | [CI/CD & GitOps](06-cicd-gitops/README.md) | ☐ Not started | **Gap — start early** |
| 07 | [Scripting (Python/Go/Bash)](07-scripting/README.md) | ☐ Not started | Gap — ongoing, not a "finish" module |
| 08 | [SRE fundamentals](08-sre-fundamentals/README.md) | ☐ Not started | **Gap — vocabulary that turns "Ops" into "SRE" on paper** |
| 09 | [Linux & networking](09-linux-networking/README.md) | ☐ Not started | Medium — solid base already |

Update the status column yourself as you go: ☐ Not started → ◐ In progress → ☑ Done.

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
