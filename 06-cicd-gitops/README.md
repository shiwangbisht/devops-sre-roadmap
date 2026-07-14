# 06 — CI/CD & GitOps

You've almost certainly *used* pipelines (deploying to App Runner/Amplify, K8s rollouts) but likely didn't design one from scratch. This module closes that gap.

## Depth checklist

- [ ] Pipeline stages: build → test → scan → package → deploy, and what belongs at each gate
- [ ] GitHub Actions (or your CI of choice): workflow triggers, reusable workflows, secrets handling, caching for speed
- [ ] Deployment strategies: rolling vs blue-green vs canary — know the rollback story for each, not just the happy path
- [ ] GitOps: the difference between "CI pushes to prod" vs "cluster pulls desired state" (ArgoCD/Flux) — and why the latter is considered more resilient
- [ ] Artifact management: image tagging strategy (never `:latest` in prod), registry scanning
- [ ] Rollback: how fast can you actually revert a bad deploy — this is one of the most common SRE interview questions

## Scenario projects

1. **Build a real pipeline for one of your Go packages** (`../GO/packages`) or a small app: on push → run tests → build Docker image → push to a registry. Start simple, add stages incrementally.
2. **Add a deploy stage to a kind/minikube cluster** using the manifests from `../workflows/workflow`, with a manual approval gate before "prod."
3. **Simulate a bad deploy and practice rollback** — time yourself reverting via both `kubectl rollout undo` and a Git-revert-triggered pipeline; compare speed and blast radius.
4. **Try GitOps for one service:** point ArgoCD (or Flux) at a Git repo containing your k8s manifests, make a change via Git only, and watch it reconcile — no `kubectl apply` at all.

## Where you already have evidence

- `../workflows/workflow` — existing manifests (`consumer.yml`, `getPanda-service.yml`) are natural deploy targets for the pipeline you build here.
- `../GO/packages` — natural build/test target for a CI pipeline's early stages.
