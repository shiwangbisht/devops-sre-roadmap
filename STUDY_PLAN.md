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

## Phase 2 — Kubernetes (01-kubernetes-sre) — self-managed AND managed, both

Updated 2026-10-21: both cluster types now, not an either/or — see `cluster_setup.md`. Reading material
for this whole phase: `Core_concepts.md`, `cluster_setup.md`, `production_yaml_guide.md`,
`networking.md`, `storage_and_autoscaling.md`, `helm_basics.md` (all written, read ahead of the day
that needs them or the night before).

- [ ] **Day 6** — Self-managed cluster: kubeadm on 3 EC2 instances in the learning AWS account —
      `cluster_setup.md` Part 1, step by step, by hand. Confirm `kubectl get nodes` shows all Ready.
- [ ] **Day 7** — Managed cluster: EKS via console — `cluster_setup.md` Part 2. Compare `kubectl get
      pods -n kube-system` output directly against Day 6's — note what's missing and why.
- [ ] **Day 8** — Deploy the production-grade manifest set from `production_yaml_guide.md` (Deployment +
      Service + PDB + HPA) to both clusters. Note anything that behaves differently between them.
- [ ] **Day 9** — Scenario: bad rollout. Ship a broken readiness probe on purpose, diagnose from
      `kubectl describe`/`logs`/events only — no peeking at the manifest first.
- [ ] **Day 10** — Scenario: resource starvation + autoscaling. Set memory limit too low → watch
      OOMKilled → tune it. On EKS: install metrics-server if not present, get HPA actually scaling
      something under load, time the lag per `storage_and_autoscaling.md`'s breakdown.
- [ ] **Day 11** — Scenario: networking. Break a Service selector or NetworkPolicy on purpose (apply the
      default-deny example from `networking.md`), time yourself finding it via the diagnosis order.
      Add what you learned to `situations.md`.
- [ ] **Day 12** — Storage practical: dynamic PVC provisioning via the EBS CSI driver on EKS, then a
      small StatefulSet (e.g. a single-node Postgres) using `volumeClaimTemplates`.
- [ ] **Day 13** — Helm: convert one manifest set into a chart with environment-specific `values.yaml`,
      practice `install` → `upgrade` → `rollback`.
- [ ] **Day 14** — RBAC + security: a dedicated ServiceAccount with a least-privilege Role, confirm
      what it can/can't do via `kubectl auth can-i --as`. Apply a default-deny NetworkPolicy namespace-wide.
### Phase 2B — production-at-scale topics (added 2026-10-21, for senior/high-scale interview depth)

- [ ] **Day 15** — Admission control / policy as code — `admission_control.md`. Set
      `pod-security.kubernetes.io/enforce: restricted` on a namespace, confirm a privileged pod gets
      rejected. Install Kyverno, write a policy requiring resource limits, test it in `Audit` then
      `Enforce` mode against a bad manifest.
- [ ] **Day 16** — CRDs & Operators — `crds_and_operators.md`. Install a real operator (Prometheus
      Operator is a good first one), inspect the CRD it registers (`kubectl get crd`), create a custom
      resource and watch the operator reconcile it into real objects.
- [ ] **Day 17** — Service mesh — `service_mesh.md`. Install Linkerd (lighter to start with than Istio)
      on one cluster, confirm mTLS is active between two pods, try a basic traffic split between two
      versions of a deployment.
- [ ] **Day 18** — GitOps — `gitops_argocd.md`. Install ArgoCD, point an `Application` at a git repo
      with Day 8's manifests, make a change via git push instead of `kubectl apply`, watch it sync.
      Test `selfHeal` by manually editing a resource and watching ArgoCD revert it.
- [ ] **Day 19** — Scale limits & cluster upgrade strategy — `scale_and_limits.md`. Mostly reading/
      judgment prep (can't provision a 5,000-node cluster in the learning account) — but do run
      `etcdctl snapshot save` on the Day 6 kubeadm cluster for real, and practice explaining the node
      pool rotation upgrade pattern out loud, unscripted.
- [ ] **Day 20** — Full capstone wrap-up: self-test cold across all 11 Kubernetes files, no notes.
      **Tear down both clusters** (EC2 instances + EKS cluster/node group + anything Day 15–18 installed)
      to stop billing.

## Phase 3 — Linux fundamentals (09-linux-networking) — compressed, not zero-to-hero

- [ ] **Day 21** — Shell/filesystem/permissions refresher — target gaps, not a full re-teach given your
      ops background; `09-linux-networking/linux/` already has a placeholder file to fill in.
- [ ] **Day 22** — Processes & systemd — signals, process states, service management.
- [ ] **Day 23** — Networking: subnetting, DNS resolution path, TCP handshake/states — this is the part
      most SRE interviews actually probe, worth real time.
- [ ] **Day 24** — Diagnostic tooling drill: `strace`, `tcpdump`, `netstat`/`ss`, `lsof` — on a real
      broken-on-purpose scenario, not just flag memorization.
- [ ] **Day 25** — Namespaces/cgroups (ties directly back into *why* containers/Kubernetes work the way
      they do) + wrap-up self-test.

## Phase 4 — 00-basics (Git, Docker, cloud fundamentals)

- [ ] **Day 26** — Git beyond the basics (rebase, bisect, reflog recovery) — skip what you already know cold.
- [ ] **Day 27** — Docker: build a multi-stage Dockerfile for something real, understand layer caching.
- [ ] **Day 28** — Cloud computing fundamentals review + wrap-up self-test.

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
