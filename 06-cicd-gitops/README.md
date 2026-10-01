# 06 — CI/CD & GitOps

You've likely *used* pipelines (deploying to App Runner/Amplify, K8s rollouts) but designing one from scratch is a different skill. Build that here from the ground up.

## Depth checklist

- [ ] Pipeline stages: build → test → scan → package → deploy, and what belongs at each gate
- [ ] GitHub Actions (or your CI of choice): workflow triggers, reusable workflows, secrets handling, caching for speed
- [ ] Deployment strategies: rolling vs blue-green vs canary — know the rollback story for each, not just the happy path
- [ ] GitOps: the difference between "CI pushes to prod" vs "cluster pulls desired state" (ArgoCD/Flux) — and why the latter is considered more resilient
- [ ] Artifact management: image tagging strategy (never `:latest` in prod), registry scanning
- [ ] Rollback: how fast can you actually revert a bad deploy — this is one of the most common SRE interview questions

## Where to learn

- [GitHub Actions docs](https://docs.github.com/en/actions) — official
- [Argo CD docs](https://argo-cd.readthedocs.io/en/stable/) (GitOps), [Argo Rollouts docs](https://argo-rollouts.readthedocs.io/en/stable/) (canary/blue-green)
- Per-subtopic links (pipeline stages, GitHub Actions, deployment strategies, GitOps, artifacts, rollback) are in each subtopic's GitHub issue — see the [DevOps_learning](https://github.com/users/shiwangbisht/projects/1) board.

## Scenario projects

1. **Build a real pipeline for one of your Go packages** (`../GO/packages`) or a small app: on push → run tests → build Docker image → push to a registry. Start simple, add stages incrementally.
2. **Add a deploy stage to a kind/minikube cluster** using the manifests from `../workflows/workflow`, with a manual approval gate before "prod."
3. **Simulate a bad deploy and practice rollback** — time yourself reverting via both `kubectl rollout undo` and a Git-revert-triggered pipeline; compare speed and blast radius.
4. **Try GitOps for one service:** point ArgoCD (or Flux) at a Git repo containing your k8s manifests, make a change via Git only, and watch it reconcile — no `kubectl apply` at all.

## Where you already have evidence

- `../workflows/workflow` — existing manifests (`consumer.yml`, `getPanda-service.yml`) are natural deploy targets for the pipeline you build here.
- `../GO/packages` — natural build/test target for a CI pipeline's early stages.

## Self-test — can you answer these cold?

1. What's the actual difference between CI pushing to prod and GitOps pulling desired state — why is the latter considered more resilient?
2. Why should you never deploy an image tagged `:latest` to production?
3. Compare rollback speed and blast radius: `kubectl rollout undo` vs. a Git-revert-triggered pipeline.
4. Where would you put a manual approval gate in a pipeline, and why there specifically?
5. Canary vs blue-green — when would you pick one over the other?
