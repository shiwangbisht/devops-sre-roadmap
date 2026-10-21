# CI/CD — fundamentals

GitOps specifically (ArgoCD, pull-based deployment) is covered in depth in
`01-kubernetes-sre/learning/gitops_argocd.md`. This file is the broader CI/CD layer underneath that —
pipeline mechanics, deployment strategies, and what actually makes a pipeline trustworthy.

## CI vs. CD vs. Continuous Deployment — three different commitments

- **Continuous Integration (CI)** — every change is automatically built + tested on merge/PR, catching
  integration problems early, frequently. The actual point: integrating in small, frequent increments is
  cheaper to debug than integrating a month of divergent work at once.
- **Continuous Delivery (CD)** — every change that passes CI is automatically prepared for release
  (built, tested, packaged) and is **always in a deployable state** — but the actual production deploy
  is a deliberate, usually manual, trigger.
- **Continuous Deployment** — every change that passes all automated checks **deploys to production
  automatically**, no manual gate at all. Requires real confidence in the test suite — this is the
  "deploy 50 times a day" model, and it's earned through test coverage/rollback speed, not just tooling choice.

## Pipeline stages — the standard shape

```
commit → build → unit tests → (security scan) → integration tests → artifact publish → deploy to
staging → (manual approval) → deploy to prod → smoke test
```
Each stage is a **gate** — failing any stage stops the pipeline before the next one runs. The ordering
matters: cheap/fast checks (lint, unit tests) run before expensive/slow ones (full integration tests,
deploy), so a pipeline fails fast on the cheap stuff instead of burning 20 minutes before hitting an
obvious lint error.

## Deployment strategies — the actual mechanics and tradeoffs

- **Rolling deployment** — replace instances/pods gradually (this is what a Kubernetes Deployment does
  by default). Simple, no extra infrastructure, but a bad deploy is live (serving some real traffic)
  before it's fully rolled out and caught.
- **Blue-green** — two full, identical environments; traffic switches entirely from "blue" (old) to
  "green" (new) at once, usually via a load balancer/DNS switch. Instant rollback (switch back), but
  **double the infrastructure cost** while both environments exist, and any stateful component
  (database) needs careful handling since both environments may briefly need to work against it.
- **Canary** — route a small percentage of real traffic to the new version first (this is exactly what
  `service_mesh.md`'s weighted `VirtualService` or a Kubernetes-native tool like Flagger automates),
  watch real metrics, then gradually increase. Catches problems with minimal blast radius, but is slower
  and needs good per-version metrics to actually judge "is the canary healthy" automatically rather than
  by feel.
- **Feature flags** — decouple *deploy* from *release* entirely — code ships to production dark (behind
  a flag, off by default), and gets turned on for a subset of users/traffic independently of any
  deployment event. The most granular control, but adds code complexity (flag checks, stale flag cleanup
  debt) that the infra-only strategies above don't.

## What makes a pipeline actually trustworthy (the part interviews probe for)

- **Tests that would actually catch a real regression** — a green pipeline with weak/no real test
  coverage is worse than a known-slow pipeline, because it creates false confidence.
- **Fast feedback** — a 45-minute pipeline gets bypassed/ignored under deadline pressure; a 5-minute one
  gets respected and actually used as intended.
- **Rollback that's genuinely fast** — if rolling back takes as long as rolling forward, the "safety" of
  a staged rollout strategy is largely theoretical under real incident pressure.
- **The pipeline's own credentials follow least privilege** — same logic as `workflow_cicd.md`'s
  Terraform CI section: a prod-deploy pipeline identity shouldn't be the same scope as a dev-deploy one.

## Artifact versioning & immutability

Every build produces one **immutable, uniquely-tagged artifact** (container image digest, versioned
package) — the same artifact that passed staging is the exact one promoted to production, never
rebuilt at each stage. Rebuilding at each stage (even from "the same" source) risks a dependency
resolving differently between builds — "it passed staging" stops meaning anything if prod runs a
different actual artifact.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the actual difference between Continuous Delivery and Continuous Deployment?* — Continuous
   Delivery means every passing change is *ready* to deploy, but production release is a deliberate
   (often manual) trigger; Continuous Deployment removes that manual gate entirely — every passing
   change deploys to production automatically.
2. *Why does pipeline stage ordering matter, not just which stages exist?* — Fast, cheap checks (lint,
   unit tests) should run before slow, expensive ones (full integration tests, deploy) so failures are
   caught and reported as early/cheaply as possible, instead of burning significant pipeline time before
   hitting a trivial failure.
3. *What's the core tradeoff of blue-green deployment versus rolling deployment?* — Blue-green gives
   instant, clean rollback (switch traffic back to the still-running old environment) at the cost of
   running double the infrastructure simultaneously; rolling deployment is cheaper (no duplicate
   environment) but a bad version is live serving real traffic incrementally before being caught.
4. *How does canary deployment limit blast radius compared to a straight rolling update?* — Only a small,
   controlled percentage of real traffic hits the new version initially, with metrics watched before
   increasing exposure — a straight rolling update has no equivalent "small controlled exposure" phase,
   the new version receives traffic from whatever fraction of replicas have already been updated, with
   no deliberate traffic-percentage control.
5. *What do feature flags let you do that no deployment strategy alone can?* — Decouple *deploying* code
   from *releasing* it to users entirely — new code can be live in production, dark/inactive, and turned
   on for a specific subset of traffic independently of any deploy event, which no purely
   infrastructure-level rollout strategy (rolling/blue-green/canary) can express on its own.
6. *Why is rebuilding "the same" artifact fresh at each pipeline stage risky, instead of promoting one
   immutable build through every stage?* — Dependency resolution isn't guaranteed identical between two
   separate builds (a transitive dependency could resolve to a newer version between builds) — if prod
   runs a different actual build than what passed staging, "it passed staging" no longer reliably
   predicts production behavior.
7. *A team's pipeline takes 45 minutes and engineers have started merging with `--no-verify` or skipping
   it under deadline pressure. What's the actual root-cause problem, and what's the fix?* — The pipeline
   is too slow to be respected/used as intended under real pressure — the fix is making it fast (parallel
   stages, faster feedback on the cheap checks first) rather than just telling engineers to stop bypassing it.