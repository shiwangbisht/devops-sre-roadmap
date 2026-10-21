# Kubernetes — storage & autoscaling deep dive

Two different depth-checklist items bundled here because they share a theme: both are "the scheduler
and controllers are doing something dynamic behind the scenes, and you need to know the mechanism to
diagnose it when it's slow or wrong."

---

## Storage

### PV, PVC, StorageClass — the full chain

- **PersistentVolume (PV)** — a piece of real storage (an EBS volume, an NFS export...), cluster-scoped,
  exists independently of any pod.
- **PersistentVolumeClaim (PVC)** — a pod's *request* for storage ("give me 10Gi, ReadWriteOnce") —
  namespaced, this is what you actually reference in a pod spec.
- **StorageClass** — a template for **dynamically provisioning** a PV on demand when a PVC is created,
  instead of a cluster admin pre-creating PVs by hand. On EKS, a StorageClass backed by the **EBS CSI
  driver** is the standard default — a PVC triggers the CSI driver to actually call the AWS API and
  create a real EBS volume.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: gp3          # a StorageClass backed by the EBS CSI driver
  resources:
    requests:
      storage: 10Gi
```

### Access modes

- **ReadWriteOnce (RWO)** — one node can mount it read/write (EBS: this is the default and typical case
  — EBS volumes attach to exactly one EC2 instance at a time).
- **ReadOnlyMany (ROX)** — many nodes, read-only.
- **ReadWriteMany (RWX)** — many nodes, read/write simultaneously — **EBS cannot do this**; needs a
  genuinely shared filesystem like **EFS**. Picking EBS for a workload that needs RWX (e.g. multiple
  pods writing to the same volume) is a real, common design mistake worth catching before it ships.

### Reclaim policy — what happens to the data when the PVC is deleted

- **Delete** (common default for dynamically provisioned volumes) — the underlying EBS volume is
  destroyed when the PVC is deleted. Fine for ephemeral/recreatable data, **dangerous for anything you
  can't regenerate**.
- **Retain** — the PV (and underlying storage) survives PVC deletion, just becomes unbound/unavailable
  for new claims until manually reclaimed. The safe choice for anything stateful/important — set it
  explicitly rather than trusting the StorageClass default.

### StatefulSets — why they exist instead of just a Deployment + PVC

A Deployment's pods are interchangeable (any replica can be destroyed/recreated, gets a new random name
and a fresh/shared PVC). A **StatefulSet** gives each replica a **stable identity** (`app-0`, `app-1`,
`app-2` — not random) and, via `volumeClaimTemplates`, its **own dedicated PVC that follows it** across
rescheduling. Use for anything where "which replica has which data" matters — databases, anything with
per-replica state that can't just be any-replica-interchangeable.

### On pod eviction/rescheduling — what survives

The **pod** is destroyed and recreated (possibly on a different node); the **PVC and its underlying
PV/EBS volume survive** and reattach to wherever the new pod lands — this is the actual mechanism behind
"Kubernetes handles stateful workloads," not magic, just PVC/PV outliving the pod's own lifecycle.

---

## Autoscaling

### HPA (Horizontal Pod Autoscaler) — scales replica count

Watches a metric (CPU/memory via **metrics-server**, or custom/external metrics) and adjusts
`replicas`. Requires **metrics-server** running in the cluster (not installed by default on kubeadm,
pre-installed on EKS add-ons) — HPA simply does nothing, silently, if metrics-server isn't present or
isn't reporting.

### VPA (Vertical Pod Autoscaler) — adjusts requests/limits, not replica count

Watches actual usage and recommends (or, in `Auto` mode, applies) better `requests`/`limits` for
containers — right-sizing instead of scaling out. **Don't run HPA and VPA on the same metric for the
same workload** — they'll fight each other (VPA changing limits while HPA is scaling based on
utilization against those same limits creates feedback-loop instability). Common real pattern: VPA in
recommendation-only mode to inform what requests/limits *should* be, HPA doing the actual live scaling.

### Cluster Autoscaler vs. Karpenter — scaling the nodes themselves, not just pods

- **Cluster Autoscaler** — watches for unschedulable pods (pending because no node has capacity), scales
  an existing ASG/node group up; scales down nodes that are underutilized and whose pods could be moved
  elsewhere. Works in terms of pre-defined node groups/instance types.
- **Karpenter** (AWS-built, the modern EKS-recommended approach) — provisions nodes directly, not via
  pre-sized ASGs — picks the actual best-fit instance type/size for pending pods in real time, generally
  faster to react and more cost-efficient than fitting demand into fixed-shape node groups.

### Why an HPA-configured app can still be overloaded for 90 seconds after a traffic spike

This is the README's own self-test question — know every piece of the lag, not just "it takes time":
1. **Metrics scrape interval** — metrics-server/HPA polls on an interval (default ~15-30s), not
   instantly — there's inherent lag before HPA even *sees* the spike.
2. **Stabilization window** — HPA deliberately waits before acting on a scale-up signal to avoid
   flapping on noise (shorter for scale-up than scale-down by default, but still non-zero).
3. **Pod scheduling + image pull + container start** — a new pod isn't instantly serving traffic; image
   pull time (if not cached on the node) and app startup time (and `startupProbe` gating readiness) all
   add real seconds.
4. **If nodes also need to scale** (Cluster Autoscaler/Karpenter), add full node provisioning time (EC2
   launch + kubelet join + CNI readiness) on top of all of the above — this is usually the biggest single
   chunk of the 90 seconds, not the HPA decision itself.

**What you'd actually tune:** lower metrics scrape interval where supported, pre-warm capacity
(min replicas above the absolute floor, or over-provisioned "placeholder" low-priority pods to keep
spare node capacity warm), reduce image size/use image pre-pulling, tune `startupProbe` to not be overly
conservative.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the actual chain of objects from "pod needs storage" to "a real EBS volume exists"?* — PVC
   (the request) references a StorageClass → StorageClass tells the CSI driver how to provision → CSI
   driver calls the AWS API to create a real EBS volume → a PV object is created representing it and
   bound to the PVC.
2. *Why can't you use a plain EBS-backed PVC for a workload where multiple pods need to write to the
   same volume concurrently?* — EBS only supports ReadWriteOnce — one node at a time. RWX (multiple
   nodes, concurrent read/write) needs a genuinely shared filesystem like EFS instead.
3. *What's the practical risk of leaving reclaim policy at `Delete` for a stateful workload's
   StorageClass?* — Deleting the PVC (even accidentally, e.g. during a namespace cleanup) destroys the
   underlying EBS volume and its data permanently — `Retain` keeps the volume around, unbound, until
   someone deliberately reclaims or deletes it.
4. *Why would you use a StatefulSet instead of a Deployment for a database?* — Each replica needs a
   stable identity and its own dedicated, persistent volume that follows it specifically across
   rescheduling — a Deployment's pods are interchangeable and don't guarantee which replica gets which
   data on recreation.
5. *What happens to a pod's data when it's evicted and rescheduled to a different node, assuming it uses
   a PVC backed by EBS?* — The pod is destroyed and recreated; the PVC/PV (and the EBS volume itself)
   survive and get reattached to wherever the new pod lands — data isn't lost, only compute moved.
6. *Why does HPA sometimes just silently not scale at all?* — metrics-server isn't installed/running, or
   isn't successfully reporting metrics — HPA depends on it entirely and fails quietly rather than
   erroring loudly in an obvious way.
7. *Why shouldn't you run HPA and VPA on the same metric for the same workload?* — They can fight each
   other — VPA adjusting a container's resource limits while HPA is scaling replica count based on
   utilization against those same limits creates a feedback loop/instability, rather than cleanly
   complementary scaling.
8. *What's the core difference between Cluster Autoscaler and Karpenter?* — Cluster Autoscaler scales
   pre-defined node groups/ASGs up or down based on pending/underutilized pods; Karpenter provisions
   nodes directly, choosing the actual best-fit instance type for pending pods in real time rather than
   working within fixed node-group shapes — generally faster and more cost-efficient.
9. *Walk through every source of lag between a traffic spike and HPA-scaled pods actually serving
   traffic.* — Metrics scrape interval delay, HPA's stabilization window, pod scheduling + image pull +
   app startup time, and (if node capacity is also insufficient) full node provisioning time on top —
   node provisioning is usually the single biggest chunk if it's in the critical path.
10. *What's one concrete way to reduce that lag for a latency-sensitive app with bursty traffic?* —
    Keep some headroom already warm (higher `minReplicas`, or low-priority placeholder pods that get
    evicted to make room, keeping spare node capacity pre-provisioned) rather than scaling fully from a
    cold floor every time.