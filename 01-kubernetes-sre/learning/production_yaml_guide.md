# Kubernetes — writing production-grade YAML

A manifest that works in `kind` and a manifest that's safe to run in production differ in maybe 15
lines, and almost nobody teaches those 15 lines explicitly — they get learned the hard way, from an
incident. This file is those 15 lines, explained, not just a syntax reference.

## The production-readiness checklist

Before any Deployment ships, it should have all of these — treat a manifest missing any of these as
"not done," the same way you'd treat code with no error handling:

- [ ] **Resource `requests` AND `limits`** on every container — no requests means the scheduler can't
  place it sanely (and it defaults to BestEffort QoS, first to be evicted); no memory limit means one
  runaway container can starve the whole node.
- [ ] **All three probes considered** (liveness, readiness, and startup if the app is slow to boot) —
  not just copy-pasted from another app; tuned to *this* app's actual startup/health characteristics.
- [ ] **A pinned image tag**, never `:latest` — `latest` makes rollouts non-reproducible (you can't
  redeploy the exact same thing twice) and breaks `kubectl rollout undo` (there's no "previous version"
  to go back to if the tag never changed).
- [ ] **`securityContext`** — run as non-root, drop unneeded Linux capabilities, read-only root
  filesystem where the app allows it.
- [ ] **Labels that actually mean something** — `app`, `component`, `environment` at minimum — not just
  enough to satisfy the selector, enough to filter/query the cluster meaningfully during an incident.
- [ ] **A `PodDisruptionBudget`** if the app can't tolerate all replicas going down at once — without
  one, a node drain (upgrade, autoscaler scale-down) can take out every replica simultaneously.
- [ ] **Pod anti-affinity or topology spread constraints** — so replicas aren't all scheduled onto the
  same node/AZ, which turns one node failure into a full outage instead of a partial one.
- [ ] **`maxSurge`/`maxUnavailable`** deliberately set, not left at Deployment defaults, based on
  whether this app can tolerate reduced capacity during a rollout.
- [ ] **Secrets referenced, never inlined** — `envFrom`/`valueFrom.secretKeyRef`, never a literal
  password in the manifest (same principle as Terraform's secrets rule).
- [ ] **A dedicated ServiceAccount**, not the default one, if the pod needs any API access —
  least privilege, same logic as IAM.
- [ ] **`imagePullPolicy: IfNotPresent`** (or `Always` only if you have a real reason) — with a pinned
  tag, `Always` just adds registry round-trips for no benefit.

---

## A full, stitched, production-grade example

Every field below has a reason — read the comments, don't just copy the shape.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments-api
  namespace: payments
  labels:
    app: payments-api
    component: backend
    environment: prod
spec:
  replicas: 3
  revisionHistoryLimit: 5          # how many old ReplicaSets to keep for rollback — default (10) is often more than needed
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1                  # can go 1 pod over desired count during rollout
      maxUnavailable: 0            # never drop below desired count — this app can't tolerate reduced capacity
  selector:
    matchLabels:
      app: payments-api
  template:
    metadata:
      labels:
        app: payments-api
        component: backend
        environment: prod
    spec:
      serviceAccountName: payments-api         # dedicated SA, not default
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: payments-api
                topologyKey: topology.kubernetes.io/zone   # spread replicas across AZs
      containers:
        - name: payments-api
          image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/payments-api:v2.4.1   # pinned, never :latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          startupProbe:                      # covers slow boot without weakening liveness sensitivity once running
            httpGet:
              path: /healthz
              port: 8080
            failureThreshold: 30
            periodSeconds: 2                 # up to 60s to boot before liveness checks even start
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            periodSeconds: 10
            failureThreshold: 3              # 30s of failure before restart — avoid killing on one blip
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            periodSeconds: 5
            failureThreshold: 2              # pulled from Service faster than it'd be restarted
          envFrom:
            - configMapRef:
                name: payments-api-config
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: payments-api-secrets
                  key: db-password
---
apiVersion: v1
kind: Service
metadata:
  name: payments-api
  namespace: payments
spec:
  selector:
    app: payments-api
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: payments-api
  namespace: payments
spec:
  minAvailable: 2          # tolerate 1 voluntary disruption (node drain, scale-down) at a time out of 3 replicas
  selector:
    matchLabels:
      app: payments-api
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: payments-api
  namespace: payments
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payments-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300   # avoid flapping — wait 5 min of sustained low load before scaling down
```

### Why `readinessProbe` and `livenessProbe` have different `failureThreshold`/`periodSeconds` above

Readiness failing just pulls the pod from the Service (cheap, reversible, should react fast); liveness
failing kills and restarts the container (expensive, should be conservative — a false-positive restart
under brief load is worse than a few seconds of a pod staying "not ready"). This asymmetry is one of the
most common things missing from copy-pasted manifests.

---

## Interview questions (with the short answer you should be able to give cold)

1. *Given a Deployment manifest with no resource `requests`/`limits`, what's actually wrong with it in
   production?* — No requests means the scheduler has no real basis to place it (and it lands in
   BestEffort QoS — first evicted under node pressure); no memory limit means a leak/runaway process in
   this container can starve or OOM the whole node, not just itself.
2. *Why is `:latest` a production anti-pattern even if the image genuinely is the latest build?* — It
   makes deployments non-reproducible (can't redeploy the exact same artifact twice, can't tell what's
   actually running from the manifest alone) and breaks `kubectl rollout undo`, since there's no
   distinct "previous" tag to roll back to.
3. *Why would you set `maxUnavailable: 0` on one app's rollout strategy but not another's?* — Depends on
   whether the app can tolerate running below its desired replica count during a rollout — a
   latency-sensitive payments API likely can't (set to 0, pair with `maxSurge` to go over instead); a
   low-traffic internal tool might tolerate it fine, trading rollout speed/simplicity for a brief
   capacity dip.
4. *What does a PodDisruptionBudget protect against that replica count alone doesn't?* — Voluntary
   disruptions — a node drain during a cluster upgrade or Cluster Autoscaler scale-down can otherwise
   evict multiple/all replicas of an app at once if they happen to land on the same node(s); a PDB caps
   how many can be evicted simultaneously, regardless of why the eviction is happening.
5. *Why use pod anti-affinity (or topology spread) instead of just trusting the scheduler's default
   spreading?* — The default scheduler does mildly prefer spreading, but it's not guaranteed — without
   an explicit anti-affinity/topology constraint, multiple replicas can end up on the same node or AZ,
   which turns a single node/AZ failure into a bigger outage than necessary.
6. *What's the practical difference in blast radius between a liveness probe failing and a readiness
   probe failing, and how should that shape how you configure each?* — Liveness failure restarts the
   container (expensive, should have a higher failure threshold/be conservative to avoid flapping);
   readiness failure just removes it from Service endpoints (cheap, reversible, can react faster/more
   sensitively without real cost).
7. *Why give a Deployment its own ServiceAccount instead of using `default`?* — Least privilege — the
   `default` ServiceAccount in a namespace is shared across every pod that doesn't specify one, so
   granting it any RBAC permissions implicitly grants them to everything else using the default too. A
   dedicated SA scopes exactly what this one workload can do via the API.
8. *A pod keeps getting OOMKilled right after a traffic increase, but its memory limit "looks generous."
   What would you actually check?* — Whether the limit matches real peak usage under load (not just idle
   — check `kubectl top pod` under load, or metrics history), and whether the app has a memory leak that
   only manifests under sustained traffic rather than a limit that's simply too low for legitimate peak
   usage — these need different fixes (raise the limit vs. fix the app).
9. *Why does the example set `startupProbe` in addition to `livenessProbe` instead of just giving
   liveness a long `initialDelaySeconds`?* — `initialDelaySeconds` is a fixed, static delay applied
   every time, even for fast restarts — `startupProbe` only holds off liveness/readiness checks *while
   genuinely still starting*, so a fast restart isn't penalized with the same long fixed wait a slow
   cold-start needs.