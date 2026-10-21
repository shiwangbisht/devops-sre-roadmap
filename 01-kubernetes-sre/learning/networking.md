# Kubernetes — networking deep dive

`Core_concepts.md` covers Service types at a high level; this is the "how does a packet actually get
from one pod to another" layer underneath — the part that turns "restart it and see" into real
diagnosis.

## The four networking problems Kubernetes actually solves

1. **Pod-to-pod**, same node or different nodes, without NAT — every pod gets its own real IP, flat
   address space across the whole cluster. This is the CNI's job.
2. **Pod-to-Service** — stable virtual IP + DNS name in front of a changing set of pod IPs. This is
   kube-proxy + CoreDNS's job.
3. **External-to-Service** — getting traffic from outside the cluster in. This is Service type
   (NodePort/LoadBalancer) or Ingress's job.
4. **Pod-to-pod access control** — who's allowed to talk to whom. This is NetworkPolicy's job (and by
   default, nobody is restricted — everything can reach everything).

## CNI — how pod IPs actually work

Kubernetes itself has **no built-in pod networking** — it delegates entirely to whatever CNI plugin is
installed (Calico, Cilium, AWS VPC CNI, Flannel...). Two broad approaches:
- **Overlay networking** (e.g. Flannel's VXLAN mode) — pod traffic is encapsulated inside node-to-node
  tunnels; pod IPs are virtual, not real on the underlying network. Simpler to set up, adds encapsulation
  overhead.
- **Native/BGP routing** (e.g. Calico in BGP mode, AWS VPC CNI) — pod IPs are real, routable IPs on the
  underlying network (AWS VPC CNI literally assigns pods real VPC IPs from the subnet). No encapsulation
  overhead, but ties you more tightly to the underlying network's addressing — AWS VPC CNI specifically
  is *why* EKS nodes can run out of pod IP capacity based on instance type (each ENI/instance type has a
  max IP count), a real operational gotcha worth knowing by name.

## kube-proxy — how a Service's virtual IP actually routes to a pod

A Service's ClusterIP isn't a real listening process anywhere — kube-proxy on every node programs rules
that intercept traffic to that IP and rewrite it to a real pod IP. Two modes:
- **iptables mode** (older default) — programs a chain of iptables rules; rule evaluation is roughly
  O(n) in number of Services, so very large clusters (thousands of Services) see real latency from this.
- **IPVS mode** — uses the kernel's IPVS load balancer instead, O(1) lookup regardless of Service count,
  built-in load balancing algorithms (round robin, least connection, etc.) instead of iptables' random
  selection. The better choice at scale; iptables is fine for small/medium clusters.

## DNS resolution path — what actually happens when a pod looks up `my-svc`

1. Pod's `/etc/resolv.conf` (auto-injected by kubelet) points at **CoreDNS**'s ClusterIP, with search
   domains like `<namespace>.svc.cluster.local`.
2. A lookup for just `my-svc` gets the namespace's search domain appended → resolves within the same
   namespace. Cross-namespace requires the full `my-svc.other-namespace.svc.cluster.local`.
3. CoreDNS answers from its watch of the Kubernetes API (Services/Endpoints), not a static zone file —
   it's always in sync with current Service state.
4. **Common real failure:** CoreDNS pods themselves getting OOMKilled or evicted under cluster-wide
   resource pressure takes down *all* in-cluster DNS resolution at once — a classic "everything is
   broken" incident whose root cause is one unrelated-looking component.

## Service types — the practical decision

- **ClusterIP** (default) — internal only. Use for anything that doesn't need to be reached from
  outside the cluster (most backend services).
- **NodePort** — opens a static port (30000–32767 range) on every node's IP. Rarely used directly in
  production — mostly a building block LoadBalancer Services use internally, or for quick debugging.
- **LoadBalancer** — provisions a real cloud load balancer (on EKS: an ALB/NLB via the AWS Load Balancer
  Controller) in front of the Service. The standard way to expose something externally on a cloud cluster.
- **Ingress** (not a Service type, but goes with this decision) — one L7 entry point routing by
  host/path to multiple Services, instead of one LoadBalancer per Service. Use when you have several
  HTTP services to expose and want host/path-based routing, TLS termination, etc. in one place rather
  than N cloud load balancers.

## NetworkPolicy — the access control layer almost nobody turns on by default

**Default behavior with no NetworkPolicy at all: every pod can reach every other pod**, cluster-wide,
regardless of namespace. NetworkPolicy is **allow-list based once any policy selects a pod** — the
moment one NetworkPolicy targets a pod, all traffic not explicitly allowed by some policy is denied.

```yaml
# Default-deny all ingress for every pod in this namespace (the recommended starting point)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: payments
spec:
  podSelector: {}     # applies to every pod in the namespace
  policyTypes: ["Ingress"]
---
# Then explicitly allow what's actually needed
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-api-gateway
  namespace: payments
spec:
  podSelector:
    matchLabels:
      app: payments-api
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api-gateway
      ports:
        - port: 8080
```
NetworkPolicy enforcement requires the CNI to actually support it — not all do (Flannel alone doesn't;
Calico/Cilium/AWS VPC CNI with policy enforcement enabled do). Writing a NetworkPolicy against a CNI
that doesn't enforce it silently does nothing — a real gotcha worth checking before relying on it.

## Systematic diagnosis order for "pod A can't reach pod B / Service"

1. **Do the pods exist and are they Ready?** `kubectl get pods -o wide` — a not-Ready pod won't be in a
   Service's Endpoints at all.
2. **Does the Service actually have endpoints?** `kubectl get endpoints <svc>` — empty endpoints almost
   always means the Service's `selector` doesn't match the pod's labels (a classic typo-class bug).
3. **Is it DNS or routing?** Exec into a pod and `nslookup my-svc` — if DNS resolves to a ClusterIP but
   the connection still fails, it's not DNS, move to routing/NetworkPolicy. If DNS itself fails, check
   CoreDNS pod health first.
4. **Is a NetworkPolicy blocking it?** `kubectl get networkpolicy -n <namespace>` — check if anything
   selects the destination pod and whether your source is in its allow list.
5. **Only then** suspect the CNI/kube-proxy itself (rare, but `kubectl get pods -n kube-system` to check
   CNI/kube-proxy pod health is the last stop, not the first guess).

---

## Interview questions (with the short answer you should be able to give cold)

1. *Does Kubernetes provide pod networking itself, or is that delegated?* — Delegated entirely to
   whatever CNI plugin is installed — Kubernetes defines the networking *model* (every pod gets a real,
   flat, routable IP) but relies on the CNI to actually implement it.
2. *What's the practical tradeoff between an overlay CNI (Flannel/VXLAN) and a native-routing CNI
   (Calico BGP, AWS VPC CNI)?* — Overlay is simpler to deploy and network-agnostic but adds encapsulation
   overhead; native routing has no overhead and gives pods real routable IPs, but ties pod networking
   capacity/addressing to the underlying network — e.g. AWS VPC CNI pod-IP limits are driven by EC2
   instance type's ENI/IP capacity.
3. *What's the difference between kube-proxy's iptables mode and IPVS mode, and when does it matter?* —
   iptables rule evaluation is roughly linear in Service count; IPVS gives O(1) lookup and real load
   balancing algorithms. Matters at scale (thousands of Services) — small/medium clusters won't notice
   the difference.
4. *A Service has healthy backing pods but `kubectl get endpoints` shows nothing. What's almost
   certainly wrong?* — The Service's label `selector` doesn't actually match the pods' labels — a
   mismatch/typo is the overwhelmingly common cause of a Service with zero endpoints despite healthy pods.
5. *A cross-namespace DNS lookup using just the short Service name fails, but the full name works. Why?*
   — The pod's `/etc/resolv.conf` search domain only auto-completes within its own namespace
   (`<ns>.svc.cluster.local`); cross-namespace lookups need the fully-qualified name since the short name
   won't resolve against another namespace's implicit search domain.
6. *CoreDNS pods get OOMKilled under cluster-wide memory pressure. What's the blast radius?* — Every
   in-cluster DNS resolution fails cluster-wide — any pod doing a Service-name lookup breaks, which can
   look like "everything is broken" even though only one component actually failed.
7. *When would you reach for Ingress instead of giving each Service its own LoadBalancer?* — When
   exposing multiple HTTP services externally — Ingress gives one entry point with host/path-based
   routing and centralized TLS termination, instead of provisioning (and paying for) N separate cloud
   load balancers.
8. *With no NetworkPolicy defined anywhere in a cluster, what's the default pod-to-pod access posture?*
   — Fully open — any pod can reach any other pod across any namespace by default; NetworkPolicy is
   opt-in, not a default-restrictive posture.
9. *You wrote a NetworkPolicy and traffic is still getting through that it should block. What's the
   first thing to check?* — Whether the CNI actually enforces NetworkPolicy at all — some CNIs (plain
   Flannel) don't enforce it, so an unenforced policy silently does nothing rather than erroring.
10. *Walk through your diagnosis order for "pod A can't reach Service B."* — Pod readiness first →
    Service endpoints (selector mismatch is the most common root cause) → DNS resolution vs. routing
    (exec in, `nslookup`) → NetworkPolicy → only then CNI/kube-proxy health as a last resort, not a
    first guess.