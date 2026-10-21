# Kubernetes — GitOps (ArgoCD)

`workflow_cicd.md` in the Terraform module covers the general plan-on-PR/apply-on-merge pattern. GitOps
is that same idea's Kubernetes-native form, but with one structural difference worth being precise about.

## GitOps vs. a normal CI/CD pipeline — the actual difference

A normal pipeline is **push-based**: CI runs `kubectl apply`/`helm upgrade` *against* the cluster from
outside, using credentials that can reach it. GitOps is **pull-based**: an agent (ArgoCD) runs **inside**
the cluster, continuously watches a git repo, and pulls+applies changes itself — nothing external ever
needs direct `kubectl apply` access to the cluster at all.

```
Push-based:   CI pipeline --(credentials, kubectl apply)--> cluster
Pull-based:   Git repo <--(poll/watch)-- ArgoCD (running inside the cluster) --(applies)--> same cluster
```

**Why this matters, not just as a diagram:** no CI system needs standing credentials into the cluster —
drastically shrinks the attack surface. And the cluster's actual state and the git repo are
**continuously reconciled**, not just synced at deploy time — if someone manually `kubectl edit`s
something in prod, ArgoCD detects the drift and (depending on config) either flags it or auto-reverts it
back to match git. Git becomes the actual single source of truth for "what should be running," enforced
continuously, not just at deploy time.

## Core ArgoCD object: `Application`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payments-api
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/k8s-manifests
    targetRevision: main
    path: apps/payments-api        # could be raw YAML, a Helm chart, or a Kustomize overlay
  destination:
    server: https://kubernetes.default.svc
    namespace: payments
  syncPolicy:
    automated:
      prune: true        # delete resources removed from git
      selfHeal: true      # revert manual cluster changes back to match git automatically
```
`selfHeal: true` is the sharpest expression of "git is the source of truth" — turn it on deliberately,
understanding it means a manual `kubectl edit` in that namespace gets silently reverted on the next sync.

## The practical workflow, end to end

1. Dev wants to change `replicas: 3` → `replicas: 5`. They edit the YAML in the git repo (`apps/
   payments-api/deployment.yaml`), open a PR.
2. PR review happens the same as code review — the diff is readable, reviewable, approvable.
3. Merge to `main`.
4. ArgoCD (polling or via a git webhook) detects the repo changed, computes the diff against the live
   cluster state, and applies it — **no human ever ran `kubectl apply` or `helm upgrade` by hand.**
5. ArgoCD's UI/CLI shows sync status — in sync, out of sync (drift detected), or sync in progress —
   giving a live view of "does the cluster actually match git right now."

## Why this matters for an SRE specifically

- **Rollback is a git revert**, not a separate deployment mechanism to remember — `git revert` the
  merge, ArgoCD syncs the cluster back automatically.
- **Audit trail is git history** — "who changed this and when" is just `git log`/`git blame`, not a
  separate deploy-tool audit log to cross-reference.
- **Disaster recovery** — if a cluster is lost entirely, ArgoCD pointed at the same repo against a fresh
  cluster reconstructs the exact same state — the repo *is* the cluster's definition, not just a record
  of how it was once built.
- **Drift detection is continuous and automatic** — compare to Terraform, where drift is only visible
  when someone runs `plan`; ArgoCD's reconciliation loop means drift surfaces (and can self-heal)
  without anyone having to remember to check.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the structural difference between GitOps and a normal push-based CI/CD pipeline?* — Push-based:
   CI runs outside the cluster and pushes changes in using credentials that can reach it. GitOps:
   an agent running *inside* the cluster pulls changes from git itself — no external system needs
   standing apply access to the cluster.
2. *Why is "no CI system needs cluster credentials" a meaningful security improvement, not just a nice-to-have?*
   — It removes an entire class of credential — a leaked/compromised CI pipeline can no longer directly
   modify the cluster, since the pipeline never held apply access in the first place; the only path to
   changing the cluster is through reviewed, git-tracked changes.
3. *What does `selfHeal: true` actually do, and what's the operational tradeoff?* — Automatically reverts
   manual changes made directly against the cluster back to match git on the next sync — enforces git as
   the true source of truth, but means a legitimate emergency `kubectl edit` during an incident gets
   silently undone unless the fix is also committed to git (or sync is paused first).
4. *How is rollback different in a GitOps model compared to a traditional deploy pipeline?* — It's a
   `git revert` of the offending commit/merge, not a separate "redeploy the previous artifact" mechanism
   — the same mechanism that deploys forward also deploys backward, and it's auditable the same way any
   other git history is.
5. *If a cluster is lost entirely, what does recovery look like in a GitOps setup vs. a traditional
   one?* — Point ArgoCD at the same repo against a freshly created cluster — the repo fully describes
   desired state, so recovery is largely automatic reconciliation rather than manually replaying a
   deployment history or runbook.
6. *How does GitOps detect drift compared to Terraform's `plan`?* — Terraform drift is only visible when
   someone explicitly runs `plan`; ArgoCD continuously reconciles in the background, so drift is detected
   (and, if configured, auto-corrected) without anyone having to remember to check — proactive instead of
   on-demand.
7. *A dev wants to make an emergency manual change in prod during an incident, but the app's ArgoCD sync
   has `selfHeal: true`. What should they do?* — Either pause that Application's auto-sync first, make
   the manual change, then commit the equivalent change to git before re-enabling sync — or just commit
   the fix to git directly and let ArgoCD apply it normally, rather than fighting self-heal with an
   unmanaged `kubectl edit`.