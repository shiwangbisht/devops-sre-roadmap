# Day-wise study plan (3 hrs/day)

Forward-looking schedule — check boxes off as days complete. What actually happened each day gets
logged in that module's `learning/practical_log.md` (the backward-looking record), and pushed to
GitHub at end of day per `CLAUDE.md`.

Order: finish Terraform practicals (momentum + real AWS account already set up) → Kubernetes
(daily-driver at work, highest ROI) → Linux fundamentals (foundational, but you're not starting from
zero given your ops background, so compressed vs. the README's full 13-level curriculum) → 00-basics →
then AWS/CI-CD/Observability/Databases once we're there. `07-scripting` and `08-sre-fundamentals`
(the README's "continuous track") get folded in as a 20–30 min starter most days rather than standalone
days — scripting practice attached to whatever that day's infra work is, SRE vocabulary picked up as it
becomes relevant.

## Phase 1 — Terraform (05-terraform-iac) — manual-first, then automate

- [ ] **Day 1** — Manual S3 bucket in the learning AWS account (console or CLI by hand) — versioning +
      lifecycle rule. Log what you observed in `practical_log.md`.
- [ ] **Day 2** — Codify Day 1's bucket: `terraform import` → write matching config → `plan` until the
      diff is empty. This is the import workflow from `about.md`/`ongoing_questions.md`, for real.
- [ ] **Day 3** — Break state on purpose: hand-edit the bucket in the console (change a tag, a lifecycle
      rule), then `plan -refresh-only` to see drift, reconcile it. Log the reasoning in `situations.md`.
- [ ] **Day 4** — Write one reusable module (e.g. "standard S3 bucket with lifecycle") and consume it
      with two different `.tfvars` (dev/prod-style). First real use of `variable`/`output`/`module`
      together instead of just reading about them.
- [ ] **Day 5** — Destroy-and-rebuild drill + `prevent_destroy` — practice tearing down and recreating
      safely, then deliberately try to destroy something with `prevent_destroy` set and watch it block
      you. Wrap up: review all of `05-terraform-iac/learning/` self-tests cold, no notes.

## Phase 2 — Kubernetes (01-kubernetes-sre) — needs a tooling decision first

- [ ] **Day 6** — Local environment setup (Docker + kind + kubectl + helm) *or* revisit the EKS-on-real-AWS
      option — flag this at the start of Day 6 rather than assuming kind, since it was left open.
- [ ] **Day 7** — Deploy a basic app by hand (`kubectl run`/raw YAML, no Helm yet) — Pod → Deployment →
      Service, manually, so the objects in `Core_concepts.md` stop being just definitions.
- [ ] **Day 8** — Scenario: bad rollout. Ship a broken readiness probe on purpose, diagnose from
      `kubectl describe`/`logs`/events only — no peeking at the manifest first.
- [ ] **Day 9** — Scenario: resource starvation. Set memory limit too low → watch OOMKilled → tune it.
      Separately oversubscribe a node's CPU requests, observe scheduling behavior.
- [ ] **Day 10** — Scenario: networking. Break a Service selector or NetworkPolicy on purpose, time
      yourself finding it. Add the diagnosis steps to `situations.md`.
- [ ] **Day 11** — Convert one manifest into a Helm chart with values for replicas/resources/image tag.
      Wrap up: self-test review.

## Phase 3 — Linux fundamentals (09-linux-networking) — compressed, not zero-to-hero

- [ ] **Day 12** — Shell/filesystem/permissions refresher — target gaps, not a full re-teach given your
      ops background; `09-linux-networking/linux/` already has a placeholder file to fill in.
- [ ] **Day 13** — Processes & systemd — signals, process states, service management.
- [ ] **Day 14** — Networking: subnetting, DNS resolution path, TCP handshake/states — this is the part
      most SRE interviews actually probe, worth real time.
- [ ] **Day 15** — Diagnostic tooling drill: `strace`, `tcpdump`, `netstat`/`ss`, `lsof` — on a real
      broken-on-purpose scenario, not just flag memorization.
- [ ] **Day 16** — Namespaces/cgroups (ties directly back into *why* containers/Kubernetes work the way
      they do) + wrap-up self-test.

## Phase 4 — 00-basics (Git, Docker, cloud fundamentals)

- [ ] **Day 17** — Git beyond the basics (rebase, bisect, reflog recovery) — skip what you already know cold.
- [ ] **Day 18** — Docker: build a multi-stage Dockerfile for something real, understand layer caching.
- [ ] **Day 19** — Cloud computing fundamentals review + wrap-up self-test.

## Phase 5 onward — planned at week-level, detailed when we arrive

- **Week 5–6: 02-aws-cloud** — now with real hands-on room in the learning account: VPC, IAM, S3,
  compute, in more depth than Terraform's module touched.
- **Week 7: 06-cicd-gitops** — build the plan→PR→apply pipeline described in Terraform's `workflow_cicd.md`
  for real, against this repo or a throwaway one.
- **Week 8: 03-observability** — instrument something from an earlier phase (the K8s app, or an AWS
  service) with real metrics/logs instead of a synthetic demo.
- **Week 9: 04-databases** — slot in here, wire DB metrics into the observability stack just built.

Each phase above gets its own day-wise breakdown (like Phases 1–4) once we actually get there — no
point over-planning weeks 5–9 in detail before Phase 1–4 reality-checks the pace.
