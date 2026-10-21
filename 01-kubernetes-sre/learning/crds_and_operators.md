# Kubernetes — CRDs & Operators

The reconciliation loop in `Core_concepts.md` ("watch actual state → diff against desired → act →
repeat") isn't special-cased for built-in objects like Deployment — it's a *general pattern* you can
extend to any resource type you invent. CRDs + Operators are how most production platforms actually
work under the hood — "install Prometheus" or "run a Postgres cluster" in most real clusters means
installing an Operator, not hand-writing 15 raw manifests.

## CustomResourceDefinition (CRD) — teaching the API server a new object type

A CRD registers a brand-new `kind` with the API server — e.g. `kind: Prometheus` or `kind:
PostgresCluster` — so you can `kubectl apply`/`kubectl get` it exactly like a built-in `Deployment`.
On its own, a CRD is just a **schema** — the API server will accept/store objects of that kind, but
nothing *does* anything with them yet.

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: postgresclusters.acid.zalan.do
spec:
  group: acid.zalan.do
  names:
    kind: PostgresCluster
    plural: postgresclusters
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                numberOfInstances: { type: integer }
                postgresql:
                  type: object
                  properties:
                    version: { type: string }
```

## Operator — the controller that makes a CRD actually do something

An **Operator** is a custom controller, running as a regular pod in the cluster, that watches objects of
your new CRD kind and runs the same reconciliation loop as built-in controllers — but with logic you
(or the vendor) wrote: "when someone creates a `PostgresCluster`, actually provision a StatefulSet, a
Service, PVCs, and handle primary/replica failover." The CRD is the **interface**; the Operator is the
**implementation**.

```yaml
apiVersion: acid.zalan.do/v1
kind: PostgresCluster
metadata:
  name: my-db
spec:
  numberOfInstances: 3
  postgresql:
    version: "16"
```
Applying this does nothing by itself without the operator running — the operator is what watches for
`PostgresCluster` objects and turns this 6-line spec into real StatefulSets/Services/PVCs/failover logic
underneath. This is the actual value proposition: you describe *intent* ("a 3-node Postgres cluster"),
the operator owns the *mechanics* (which could be dozens of interacting objects and operational
know-how you don't have to personally encode every time).

## Real operators worth knowing by name

- **Prometheus Operator** — manages Prometheus/Alertmanager deployments via `ServiceMonitor`/
  `PrometheusRule` CRDs instead of hand-editing scrape configs — the de facto standard for running
  Prometheus on Kubernetes.
- **cert-manager** — a `Certificate` CRD + operator that automates TLS cert issuance/renewal (Let's
  Encrypt or internal CAs) — almost every production cluster running HTTPS ingress uses this.
- **External Secrets Operator** — syncs secrets from AWS Secrets Manager/SSM into Kubernetes Secrets
  automatically, so secret values never get committed to a manifest at all.
- **Postgres/MySQL operators** (Zalando's, CloudNativePG, etc.) — manage stateful database clusters,
  including failover, backups, and scaling, as a CRD instead of hand-rolled StatefulSets.

## Operator pattern vs. just writing more YAML — why it exists

Running a stateful system (a database, a message queue) well involves *ongoing operational logic*, not
just initial creation — failover when the primary dies, safe version upgrades, backup scheduling. A
plain StatefulSet manifest describes a *static shape*; it has no logic for "the primary just died, promote
a replica." An Operator is software that encodes that operational runbook so it runs automatically,
continuously, instead of living in a wiki page a human has to execute by hand during an incident.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the difference between a CRD and an Operator?* — A CRD is just a schema registration — it
   teaches the API server a new object type and lets you store/retrieve objects of that kind. An
   Operator is the controller that actually *does something* when those objects are created/changed —
   the CRD is the interface, the Operator is the implementation.
2. *If you `kubectl apply` a CRD's custom object but the operator isn't running, what happens?* —
   Nothing beyond the object being stored in etcd — the API server accepts and persists it fine (it
   matches the registered schema), but no reconciliation happens because nothing is watching it.
3. *Why would a team build an Operator instead of just writing a more complex Helm chart?* — A Helm
   chart only handles initial templating/deployment — it has no ongoing runtime logic. An Operator
   handles continuous operational behavior (failover, backup scheduling, safe upgrades) that has to run
   automatically in response to live cluster state, not just at install/upgrade time.
4. *Give a concrete example of what an Operator does that a human runbook used to do manually.* — e.g.
   a Postgres operator detecting the primary instance is unhealthy and automatically promoting a replica
   to primary, updating the Service to point at the new primary — previously a paged human following a
   failover runbook by hand.
5. *What does the Prometheus Operator's `ServiceMonitor` CRD actually let you avoid doing?* — Manually
   editing Prometheus's scrape config and reloading it every time a new service needs to be monitored —
   instead, creating a `ServiceMonitor` object declares "scrape this" and the operator reconciles
   Prometheus's actual config to match, automatically.
6. *Why does cert-manager matter operationally, beyond "it gets a TLS cert"?* — Certificate *renewal*
   before expiry is the part that actually prevents outages — cert-manager automates renewal
   continuously, removing the classic "nobody remembered to rotate the cert and the site went down" failure mode.