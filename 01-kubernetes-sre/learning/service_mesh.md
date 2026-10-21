# Kubernetes — service mesh

`networking.md` covers how a packet gets from pod to pod at the L3/L4 level (CNI, kube-proxy, DNS). A
service mesh operates **one layer up**, at L7, injected into every pod — it's what gives you per-request
visibility, automatic mTLS, and traffic-shaping *without changing application code*.

## What a service mesh actually adds on top of plain Kubernetes networking

Plain Kubernetes gives you: a Service routes to healthy pods, that's it — no retries, no per-request
metrics, no encryption between pods unless the app does it itself. A service mesh (Istio, Linkerd)
injects a **sidecar proxy** (Envoy for Istio) into every pod, and *all* traffic in/out of the pod goes
through that proxy instead of directly. The proxy is what gives you, transparently, without app code
changes:
- **mTLS between every pod**, automatically — certs issued/rotated by the mesh, not something each app
  team implements themselves.
- **Retries, timeouts, circuit breaking** — configured declaratively, not hand-coded in every service.
- **Traffic splitting** — e.g. 95% of traffic to v1, 5% to v2, for canary releases, with zero app changes.
- **Per-request observability** — latency/error-rate/traffic metrics for every service-to-service call,
  automatically, because every call already passes through a proxy that can measure it.
- **Fine-grained authorization** — "service A can call service B's `/read` endpoint but not `/write`,"
  enforced at the proxy, independent of application-level auth.

## Sidecar injection — the mechanism

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: payments
  labels:
    istio-injection: enabled   # every pod created in this namespace automatically gets an Envoy sidecar
```
A mutating admission webhook (same mechanism as `admission_control.md`) intercepts pod creation and
injects the sidecar container automatically — you don't add it to your Deployment manifest by hand.
This is why `kubectl get pods` shows `2/2` containers running for what your manifest describes as a
single-container pod — the sidecar is there, injected, not written by you.

## Traffic splitting for canary releases (the practical payoff)

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: payments-api
spec:
  hosts: ["payments-api"]
  http:
    - route:
        - destination:
            host: payments-api
            subset: v1
          weight: 95
        - destination:
            host: payments-api
            subset: v2
          weight: 5
```
This is traffic-weighted canary — compare to a Deployment rollout, which replaces replicas wholesale
based on readiness, not a deliberate, controlled percentage of *live traffic*. A mesh gives you the
"5% of real users hit the new version" pattern that a raw Deployment rollout can't express on its own.

## The real cost — why not every cluster runs one

- **Resource overhead** — every pod now runs an extra sidecar container, multiplying CPU/memory
  footprint cluster-wide, non-trivial at scale.
- **Latency overhead** — every call now hops through a proxy twice (egress from caller, ingress to
  callee) — small per-hop, but adds up in deep call chains.
- **Operational complexity** — the mesh itself is a distributed system you now operate (control plane,
  cert rotation, upgrade compatibility) — a real ongoing cost, not a one-time install.

**Interview-ready framing:** a service mesh is worth it once you have enough services that
per-team-reimplemented retries/mTLS/observability becomes genuinely expensive and inconsistent — not a
default "every cluster should have one." A handful of services talking to each other rarely justifies
the overhead; dozens-to-hundreds of microservices with real cross-team ownership usually does.

## Istio vs. Linkerd — the practical difference

- **Istio** — more features (richer traffic management, multi-cluster support), more complex to operate,
  heavier resource footprint (Envoy sidecars are not lightweight).
- **Linkerd** — intentionally simpler, lighter-weight proxy (its own Rust-based `linkerd2-proxy`, not
  Envoy), faster to operate, covers the core mTLS/observability/retry use cases without Istio's full
  feature surface.
- **Rule of thumb:** Linkerd if you want the core benefits (mTLS, observability) with low operational
  overhead; Istio if you specifically need its advanced traffic-management/multi-cluster capabilities
  and are willing to own the added complexity.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What does a service mesh give you that plain Kubernetes Services/kube-proxy don't?* — L7
   capabilities without app code changes: automatic mTLS between pods, retries/timeouts/circuit
   breaking, weighted traffic splitting, and per-request observability — all handled by an injected
   sidecar proxy, not application logic.
2. *How does sidecar injection actually happen — do you add it to your Deployment manifest?* — No — a
   mutating admission webhook intercepts pod creation in a labeled namespace and injects the sidecar
   automatically; your manifest stays a single-container spec, the mesh adds the second container
   transparently at admission time.
3. *Why would you use a service mesh's traffic splitting instead of just doing a normal rolling
   Deployment update for a canary release?* — A Deployment rollout replaces replicas wholesale based on
   readiness, with no control over what *percentage of live traffic* hits the new version at a given
   moment; a mesh's weighted routing lets you deliberately send e.g. 5% of real traffic to v2 while 95%
   stays on v1, independent of how many replicas of each actually exist.
4. *What's the real cost of running a service mesh, and when is it not worth it?* — Extra CPU/memory per
   pod (sidecar overhead), added per-hop latency, and real operational complexity (the mesh control plane
   is itself a distributed system to run/upgrade). Not worth it for a small number of services — the
   overhead outweighs the benefit until you have enough services that reimplementing mTLS/retries/
   observability per-team becomes genuinely costly and inconsistent.
5. *Why does `kubectl get pods` show `2/2` containers for a pod whose Deployment manifest only defines
   one container?* — The service mesh's sidecar was injected automatically at admission time (via a
   mutating webhook) because the namespace is labeled for injection — it's not in your manifest, it's
   added transparently.
6. *When would you pick Linkerd over Istio?* — When you want the core benefits (mTLS, observability,
   basic traffic management) with a lighter resource footprint and lower operational complexity, and
   don't specifically need Istio's more advanced multi-cluster/traffic-management feature set.