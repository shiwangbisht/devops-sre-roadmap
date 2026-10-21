# Kubernetes — admission control & policy as code

RBAC answers "who can call the API." Admission control answers a different question: **"even if
you're allowed to create this object, is its *content* allowed?"** — no privileged containers, every
pod must have resource limits, images must come from an approved registry. This is how large orgs
enforce standards across hundreds of teams without manually reviewing every manifest.

## Where admission control sits in the request path

```
kubectl apply → authentication → authorization (RBAC) → admission control → persisted to etcd
```
Two phases of admission control:
- **Mutating admission** — can *change* the object (e.g. inject a sidecar container, add a default
  label) before it's persisted.
- **Validating admission** — can only **accept or reject**, no changes — this is where policy
  enforcement ("deny if X") lives.

## Built-in: PodSecurityStandards (the baseline, no extra install)

Kubernetes ships a built-in admission controller for 3 standard levels, applied **per namespace** via a
label:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: payments
  labels:
    pod-security.kubernetes.io/enforce: restricted   # or: baseline, privileged
```
- **privileged** — no restrictions (default if unset).
- **baseline** — blocks known privilege-escalation holes (host namespaces, privileged containers).
- **restricted** — the hardened profile: non-root required, no privilege escalation, seccomp required,
  capabilities dropped. This is what the `securityContext` fields in `production_yaml_guide.md` exist
  to satisfy.

This is the first thing to reach for — it's free, built in, no extra controller to run — before
reaching for OPA/Kyverno for anything it doesn't cover.

## OPA Gatekeeper / Kyverno — for policy PodSecurityStandards can't express

PodSecurityStandards only covers pod security fields. For anything org-specific ("every Deployment must
have an `owner` label," "images must come from `123456789012.dkr.ecr.us-east-1.amazonaws.com`," "no
`LoadBalancer` Services outside the `ingress` namespace"), you need a general-purpose policy engine.

**Kyverno** (the easier on-ramp — policies are plain Kubernetes YAML, not a new language):
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
spec:
  validationFailureAction: Enforce    # vs. Audit — report-only without blocking, good for rollout
  rules:
    - name: check-resources
      match:
        resources:
          kinds: ["Pod"]
      validate:
        message: "every container must set resource limits"
        pattern:
          spec:
            containers:
              - resources:
                  limits:
                    memory: "?*"
                    cpu: "?*"
```

**OPA Gatekeeper** (more powerful, policies written in **Rego**, a real query language — steeper
learning curve, more expressive for complex cross-resource logic):
```rego
package k8srequiredlabels

violation[{"msg": msg}] {
  required := input.parameters.labels
  provided := input.review.object.metadata.labels
  missing := required[_]
  not provided[missing]
  msg := sprintf("missing required label: %v", [missing])
}
```

**Practical rule of thumb:** Kyverno for most teams — faster to write/read, covers the large majority of
real policy needs. Gatekeeper when you need Rego's expressiveness for genuinely complex, multi-resource
policy logic (and the team already has or wants to invest in Rego skill).

## `validationFailureAction: Audit` vs. `Enforce` — the real rollout pattern

Never ship a new policy straight to `Enforce` in a shared cluster — start in `Audit` mode (violations
are logged/visible but nothing is blocked), watch what it would have rejected across real traffic for a
while, fix the legitimate violations, *then* flip to `Enforce`. Going straight to enforce is how a
policy change becomes an outage.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the difference between RBAC and admission control?* — RBAC decides *who* can call which API
   actions; admission control decides whether the *content* of an allowed request is acceptable — a
   user can be fully authorized to create pods and still have a specific pod rejected for violating policy.
2. *What's the difference between mutating and validating admission webhooks?* — Mutating webhooks can
   modify the object before it's persisted (inject a sidecar, set a default); validating webhooks can
   only accept or reject, not change anything — policy enforcement lives in validating admission.
3. *When would PodSecurityStandards alone not be enough, and what would you reach for instead?* — When
   the policy isn't about pod security fields specifically — org-wide labeling requirements, approved
   registries, Service-type restrictions — anything PodSecurityStandards doesn't model needs a
   general-purpose engine like Kyverno or OPA Gatekeeper.
4. *Why would you choose Kyverno over OPA Gatekeeper for most teams?* — Kyverno policies are plain
   Kubernetes YAML, no new language to learn; Gatekeeper's Rego is more powerful for complex
   cross-resource logic but has a real learning curve most policy needs don't justify.
5. *You're about to roll out a new cluster-wide policy. What's the safe deployment sequence?* — Start in
   `Audit`/report-only mode, observe what it would reject against real traffic, fix legitimate
   violations, only then flip to `Enforce` — deploying straight to enforcing mode on a shared cluster
   risks blocking legitimate, previously-working deployments as an outage.
6. *A pod that should be blocked by the `restricted` PodSecurityStandard still got created. What would
   you check first?* — Whether the namespace actually has the
   `pod-security.kubernetes.io/enforce: restricted` label set — PodSecurityStandards is opt-in per
   namespace, not cluster-wide by default.