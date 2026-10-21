# Kubernetes — scale limits & large-cluster tuning

Most of this module so far is "how does a single reasonably-sized cluster work." This file is "what
breaks first as a cluster grows, and what an SRE actually tunes" — mostly reading/judgment prep rather
than hands-on in the learning account (you can't realistically provision a 5,000-node cluster to
practice on), but this is exactly the kind of depth that separates a mid-level answer from a senior one
in an interview.

## The known ceiling: ~5,000 nodes per cluster

This isn't an arbitrary number — it's a tested/supported limit from real bottlenecks, not a config value
you can just raise indefinitely:
- **etcd** — every object (pods, Services, ConfigMaps, Events...) is a key in etcd; etcd is
  consensus-based (Raft) and write-heavy clusters feel it first as **write latency**, not out-of-space —
  etcd is explicitly recommended to stay well under a few GB and on fast, low-latency storage (NVMe SSD,
  not network-attached spinning disk).
- **API server watch load** — every controller, every `kubectl get -w`, every kubelet all hold open
  **watch connections** to the API server; at large node/object counts, the sheer number of concurrent
  watches and the churn rate (status updates, Events) becomes the bottleneck, not raw CPU.
- **Scheduler throughput** — scheduling decisions don't get free at scale; very large numbers of pending
  pods at once (e.g. all come back after an outage) can create real scheduling latency.

**What large orgs actually do instead of one giant cluster:** split by **failure domain and blast
radius**, not just raw capacity — multiple smaller clusters per region/team/environment, rather than one
cluster to rule them all. This is a direct echo of the Terraform "split state by blast radius" principle
from `state_management.md` — same underlying judgment, different tool.

## API Priority and Fairness (APF)

Without it, a buggy controller hammering the API server with requests can starve every other client
(including critical system components) of API access — a classic "one bad actor takes down everything"
failure mode. APF classifies and queues requests by priority (system components > normal workloads) and
enforces fairness within each priority level, so a runaway client degrades gracefully instead of
starving the whole API server.

## etcd operational practices an SRE should know by name

- **Regular snapshot backups** — `etcdctl snapshot save` — the actual disaster-recovery mechanism if
  etcd is lost/corrupted; this is the single highest-blast-radius data loss scenario in the whole
  system (lose etcd, lose the cluster's entire state).
- **Defrag** — etcd's storage can fragment over time (especially with heavy writes/deletes), periodic
  `etcdctl defrag` reclaims space; skipping this on a long-lived, write-heavy cluster is a real source
  of "etcd disk usage keeps growing and I don't know why" incidents.
- **Watch the `etcd_server_quota_backend_bytes` limit** — etcd has a hard storage quota (default 2GB);
  hitting it puts etcd into an alarm state that **blocks writes cluster-wide** — a real, sharp failure
  mode worth knowing proactively rather than discovering during an incident.

## Reducing API server/etcd load without adding more hardware

- **Reduce Event churn** — high-frequency, low-value Events (verbose controllers) add real API/etcd
  load at scale; some clusters tune Event TTL down or filter noisy sources.
- **Use `resourceVersion`-based list+watch correctly** in any custom controller — a controller that
  naively re-LISTs instead of watching adds unnecessary full-object-set load repeatedly.
- **Namespace/object count hygiene** — leftover completed Jobs, old ReplicaSets beyond
  `revisionHistoryLimit`, stale ConfigMaps/Secrets all add to etcd's total object count for no ongoing
  value — routine cleanup matters more at scale than it seems at small scale.

## Cluster upgrade strategy at scale — why it's not "click upgrade"

- **Control plane before nodes, always** — skewed versions are only supported within a narrow window
  (kubelet can be up to a few minor versions behind the API server, never ahead) — upgrading nodes before
  the control plane is unsupported and can break.
- **Node pool rotation, not in-place node upgrades** — the standard large-scale pattern is provisioning a
  new node pool on the new version, cordoning + draining the old pool's nodes gradually (respecting
  PodDisruptionBudgets), not upgrading the Kubernetes version on existing running nodes in place.
- **Why this ties directly back to `production_yaml_guide.md`'s PDB section** — a cluster-wide upgrade
  is exactly the kind of mass voluntary-disruption event a PDB is there to protect against; a cluster
  with no PDBs anywhere is exactly the cluster where a routine upgrade becomes an incident.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What actually breaks first as a Kubernetes cluster scales toward thousands of nodes — is it a hard
   technical ceiling or a judgment call?* — Mostly etcd write latency and API server watch load, not a
   single hard wall — it's a soft, tested limit (~5,000 nodes) past which performance degrades before
   anything technically "fails," which is why large orgs split into multiple clusters well before that
   point rather than pushing one cluster to the edge.
2. *Why would a large org run many smaller clusters instead of one very large one?* — Same logic as
   splitting Terraform state by blast radius — smaller clusters limit the failure domain of any single
   control-plane issue, upgrade, or misconfiguration, and avoid the etcd/API-server scaling pressure of
   one giant shared cluster.
3. *What does API Priority and Fairness protect against?* — A single misbehaving client (buggy
   controller, runaway script) hammering the API server and starving every other client — including
   critical system components — of API access; APF queues/prioritizes so one bad actor degrades
   gracefully instead of taking down API access cluster-wide.
4. *What's the actual disaster-recovery mechanism if etcd is lost or corrupted?* — Restoring from a
   regular `etcdctl snapshot save` backup — without recent snapshots, losing etcd means losing the
   cluster's entire state with no recovery path.
5. *Why does etcd have a storage quota, and what happens when a cluster hits it?* — Keeps etcd's
   performance predictable (it's explicitly designed to stay small and fast, not grow unbounded); hitting
   the quota puts etcd into an alarm state that **blocks all writes cluster-wide** — a sharp, total
   failure mode, not a graceful slowdown.
6. *Why must the control plane always be upgraded before worker nodes, never after?* — Kubernetes only
   supports a narrow version skew (kubelet can trail the API server by a few minor versions, never lead
   it) — upgrading nodes ahead of the control plane is unsupported and can break kubelet-to-API-server
   communication.
7. *What's the standard large-scale node upgrade pattern, and why not just upgrade Kubernetes in place
   on existing nodes?* — Provision a new node pool on the target version, then cordon and gradually drain
   the old pool (respecting PodDisruptionBudgets) rather than upgrading the OS/kubelet version in place —
   safer, reversible (old pool still exists until fully drained), and testable incrementally.
8. *Why does a cluster with no PodDisruptionBudgets anywhere make routine upgrades riskier?* — A node
   drain during upgrade is a mass voluntary-disruption event — with no PDBs, nothing limits how many
   replicas of any app can be evicted simultaneously, so an upgrade can take an app fully down even
   though it has multiple replicas, purely because they all happened to land on nodes being drained at once.