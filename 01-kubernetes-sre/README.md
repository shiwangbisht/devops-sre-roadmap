# 01 — Kubernetes & Container SRE

You already do this daily in production (upgrades, rollouts, high-traffic nodes). The gap is usually not "have you used it" but "can you explain the failure mode underneath the command." This module turns daily-driver familiarity into interview-defensible depth.

## Depth checklist

- [ ] Scheduling: requests/limits, QoS classes (Guaranteed/Burstable/BestEffort), how the scheduler picks a node, taints/tolerations, node affinity/anti-affinity, pod topology spread constraints
- [ ] Rollouts: Deployment rolling update mechanics (maxSurge/maxUnavailable), readiness vs liveness vs startup probes and what breaks if you get them wrong, how a bad rollout gets stuck vs rolled back
- [ ] Networking: how Service (ClusterIP/NodePort/LoadBalancer), kube-proxy (iptables/IPVS), and CNI fit together; DNS resolution path inside the cluster; why a pod can't reach another pod (systematic diagnosis order)
- [ ] Storage: PV/PVC lifecycle, storage classes, what happens to state on pod eviction/rescheduling
- [ ] Autoscaling: HPA vs VPA vs Cluster Autoscaler, and where each one fails under sudden traffic spikes (relevant to your telecom traffic patterns)
- [ ] etcd & control plane: what actually breaks when etcd is slow/unavailable, API server behavior under load
- [ ] RBAC & multi-tenancy basics
- [ ] Resource pressure: OOMKilled vs evicted vs CrashLoopBackOff — know the diagnosis path for each, not just the symptom name
- [ ] Helm or Kustomize for templating what you currently apply manually/via YAML (your `workflows/workflow` repo already has raw manifests — good candidates to convert)

## Scenario projects (build/break/fix)

Use a local cluster (kind or minikube) so you can safely break things.

1. **Bad rollout, diagnose from symptoms only.** Deploy an app, then ship a version with a broken readiness probe. Practice diagnosing purely from `kubectl describe`/`kubectl logs`/events — no peeking at the manifest first. Write down your diagnosis steps in order.
2. **Resource starvation.** Set a pod's memory limit too low, watch it OOMKill, then tune it. Separately, oversubscribe a node's CPU requests and observe scheduling behavior.
3. **Network partition simulation.** Break a NetworkPolicy or Service selector mismatch on purpose; time yourself finding it.
4. **Traffic spike under HPA.** Load-test a deployment with HPA configured and watch scale-up lag — this maps directly to your SIP high-traffic experience; be ready to explain *why* there's lag (metrics scrape interval, cooldown, pod startup time) and what you'd tune.
5. **Convert one manifest from `../../workflows/workflow` (consumer.yml or getPanda-service.yml) into a Helm chart** with values for replicas/resources/image tag — real reusable artifact for your portfolio.

## Where you already have evidence

- Daily production rollouts and upgrades at your telecom job — this is your strongest raw material. After scenario 1–4 above, go back and re-describe a real production issue you handled using the vocabulary you just practiced (probe misconfig, resource pressure, scheduling, etc.) — that becomes an interview story.
- `../../workflows/workflow` — existing k8s/service-style manifests to build on rather than starting from scratch.
