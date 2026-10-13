Master node: it is responsible for managing,plaining,scheduling & monitoring the nodes.

Worker node: it is responsinle for hosting pods or host applications as container.


>> Master nodes components:

1. Scheduler: It is responsible for scheduling application or container on nodes.

2. Controller: It is an background program that constantly watches your cluster and works to make sure the actual state mathces the desired state.

3. API server: It is responsible for orchestrating all oprations within the cluster.

4. ETCD: It is resposible for storing cluster data in key & pair format.

>> Worker nodes component:

1. Kubelet: It litsens for instructions for API server and manages the containers.

2. Kubeproxy: It enables & manages communication between services within the cluster.

3. Container run time engine: example container D.


>> Kubernetes Architecture:
https://kubernetes.io/docs/concepts/architecture/

---

## The reconciliation loop — the idea everything else sits on top of

Every controller in Kubernetes (Deployment controller, ReplicaSet controller, Node controller...) runs
the same pattern on a loop: **watch actual state → compare to desired state (what's in etcd) → take
action to close the gap → repeat.** This is *why* `kubectl apply` isn't "run a command once" — it's
"declare a desired state, and something keeps nudging reality toward it forever." Understanding this one
loop explains most "why did Kubernetes do that" questions (self-healing, rollouts, autoscaling all reduce
to the same loop).

## Core objects an SRE needs fluent, not just "I've typed the YAML"

- **Pod** — the smallest deployable unit; one or more containers sharing network namespace + storage.
  Pods are **disposable** — you almost never manage them directly, a higher-level controller does.
- **ReplicaSet** — ensures N copies of a pod are running. You rarely write these by hand; a Deployment
  manages a ReplicaSet for you.
- **Deployment** — manages ReplicaSets + rollout strategy (rolling update, `maxSurge`/`maxUnavailable`),
  rollback history (`kubectl rollout undo`). This is what you actually deploy with, not raw Pods/ReplicaSets.
- **Namespace** — a logical partition within one cluster (not a security boundary by itself — RBAC +
  NetworkPolicy are what actually enforce isolation between namespaces).
- **Service** — stable network identity (ClusterIP by default) in front of a changing set of pod IPs;
  routes traffic via label selectors, not pod names (pods are ephemeral, their IPs change on every restart).
  - `ClusterIP` — internal-only, default.
  - `NodePort` — exposes a static port on every node.
  - `LoadBalancer` — provisions a cloud load balancer (AWS ELB/NLB) in front of the Service.
- **ConfigMap** — non-secret config data injected into pods (env vars, mounted files).
- **Secret** — same idea, for sensitive data — base64-**encoded**, not encrypted, by default. Treat it
  as "obfuscated," not "secure," unless encryption-at-rest for etcd is enabled.
- **Probes** — how the kubelet knows if a container is healthy:
  - **Liveness** — "is it alive?" Fails → container is **killed and restarted**.
  - **Readiness** — "is it ready for traffic?" Fails → pod is **pulled from Service endpoints**, not restarted.
  - **Startup** — "has it finished booting?" Delays liveness/readiness checks for slow-starting apps so
    they don't get killed mid-startup. Misconfiguring these is one of the most common real-world causes
    of a "stuck" rollout.
- **Volumes / PV / PVC** — `Volume` is pod-lifecycle-scoped storage; `PersistentVolume` (PV) is
  cluster-level storage provisioned ahead of time or dynamically via a `StorageClass`;
  `PersistentVolumeClaim` (PVC) is a pod's *request* for a PV. On pod eviction/rescheduling, the PVC
  (and its data, if backed by durable storage like EBS) survives — only the pod is recreated and
  reattaches.

## Resource requests/limits & QoS classes

- **Request** — what the scheduler guarantees/reserves on a node; drives scheduling decisions.
- **Limit** — the hard ceiling; exceeding the **memory** limit gets a pod **OOMKilled**, exceeding the
  **CPU** limit gets the process **throttled** (not killed) — this asymmetry is a common interview trap.
- **QoS classes**, derived automatically from requests/limits, not set directly:
  - **Guaranteed** — requests == limits for every container. Last to be evicted under node pressure.
  - **Burstable** — requests set, limits higher or unset. Evicted before Guaranteed.
  - **BestEffort** — no requests/limits set at all. First to be evicted.

## Scheduling controls

- **Taints & tolerations** — a taint on a node *repels* pods unless they have a matching toleration
  (node says "don't schedule here unless you're okay with X").
- **Node affinity/anti-affinity** — a pod *attracts/avoids* nodes based on node labels (pod says "I want
  to run on/avoid nodes like this").
- **Pod affinity/anti-affinity** — same idea, but relative to *other pods* already running (e.g. spread
  replicas across AZs, or keep a cache pod co-located with its app pod).
- **Pod topology spread constraints** — more fine-grained than affinity for "spread evenly across
  zones/nodes," without the all-or-nothing rigidity of required anti-affinity.

## RBAC — the actual enforcement layer namespaces don't give you by themselves

- **Role** / **RoleBinding** — permissions scoped to one namespace.
- **ClusterRole** / **ClusterRoleBinding** — permissions cluster-wide (or reusable across namespaces).
- Principle: grant the narrowest Role that lets a ServiceAccount/user do its job — same least-privilege
  logic as IAM, just Kubernetes-native.

## Diagnosing common failure states (the vocabulary that actually matters in an incident)

- **CrashLoopBackOff** — container keeps starting and dying; Kubernetes backs off restart attempts with
  increasing delay. Check `kubectl logs --previous` (the crashed container's logs, not the new one).
- **OOMKilled** — container hit its **memory limit**, kernel OOM-killer killed it. Visible via
  `kubectl describe pod` → `Last State: Terminated, Reason: OOMKilled`.
- **Evicted** — the **node** ran low on a resource (memory/disk pressure), kubelet proactively evicted
  lower-QoS pods to protect node stability — this is a node-level decision, not a container hitting its
  own limit.
- Diagnosis order that matters in interviews *and* real incidents: `kubectl describe pod` (events first)
  → `kubectl logs` (current, then `--previous` if restarted) → check resource requests/limits + node
  pressure → check probes/readiness → only then start suspecting networking/DNS.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the core loop every Kubernetes controller runs, and why does it matter?* — Watch actual state
   → diff against desired state in etcd → act to close the gap → repeat. It's why `kubectl apply` is a
   *declaration*, not a one-time command — the system keeps enforcing it, which is also the mechanism
   behind self-healing and rollouts.
2. *Why doesn't a Service route to pods by IP or name directly?* — Pods are ephemeral — their IPs change
   every time they're rescheduled/restarted. A Service uses a label selector to always route to whatever
   pods currently match, regardless of identity churn.
3. *What's the practical difference between a liveness probe failing and a readiness probe failing?* —
   Liveness failure **kills and restarts** the container; readiness failure just **removes the pod from
   Service endpoints** (traffic stops routing to it) without touching the container itself.
4. *Why would misconfigured probes cause a rollout to get stuck?* — If the new pods' readiness probe
   never succeeds (e.g. too-short `initialDelaySeconds` for a slow-starting app), the Deployment
   controller won't consider them ready to receive traffic, so it won't proceed terminating old pods —
   the rollout stalls, looking "stuck" with old and new pods both present.
5. *A container exceeds its CPU limit vs. its memory limit — what happens in each case, and why is that
   asymmetric?* — CPU is a compressible resource — the container gets **throttled**, not killed. Memory
   is not compressible — the kernel **OOM-kills** the container when it exceeds its limit. This asymmetry
   is why CPU-limit issues show up as slowness, memory-limit issues show up as restarts.
6. *What determines a pod's QoS class, and why does it matter during node resource pressure?* — Derived
   from its requests vs. limits (Guaranteed: equal; Burstable: requests < limits; BestEffort: neither
   set). Under node memory pressure, kubelet evicts BestEffort pods first, then Burstable, Guaranteed
   last — it's the eviction priority order.
7. *OOMKilled vs. Evicted — what's the actual distinction, and how do you tell which happened?* —
   OOMKilled is the *container* hitting its own memory limit (kernel OOM-killer acts on that one
   container); Evicted is the *node* being under resource pressure and kubelet proactively removing
   pods to protect the node. Check `kubectl describe pod`: `Terminated, Reason: OOMKilled` vs. a
   `Status: Failed, Reason: Evicted` with a node-pressure message.
8. *Explain the difference between taints/tolerations and node affinity.* — Taint/toleration is the
   node repelling pods by default, unless the pod explicitly tolerates it (opt-in exception). Node
   affinity is the pod expressing a preference/requirement for certain node labels (pod-driven
   attraction). They're often combined: taint dedicates nodes to a workload, affinity steers that
   workload onto them.
9. *Why isn't a Namespace a security boundary by itself?* — It's a logical partition for organizing
   resources/quotas; without RBAC (who can act on what) and NetworkPolicy (what can talk to what),
   workloads in different namespaces can still freely reach each other and be modified by anyone with
   cluster-wide access.
10. *A Secret is base64-encoded — is that encryption?* — No — base64 is trivially reversible encoding,
    not encryption. Secrets are only genuinely protected at rest if etcd encryption is explicitly
    enabled, and access should still be RBAC-restricted regardless.
11. *What happens to a pod's data on eviction/rescheduling if it uses a PVC backed by durable storage
    (e.g. EBS)?* — The pod itself is destroyed and recreated elsewhere, but the PVC and its underlying
    PV/data persist and get reattached to the new pod — the data survives; only compute is ephemeral.
12. *Walk through your diagnosis order for a pod stuck in CrashLoopBackOff.* — `kubectl describe pod`
    for events first (often shows the real cause directly), then `kubectl logs --previous` (the crashed
    container's own logs, not the fresh restart's), then check resource limits/requests and node
    pressure, then probes — resist jumping straight to "it's a networking issue."
