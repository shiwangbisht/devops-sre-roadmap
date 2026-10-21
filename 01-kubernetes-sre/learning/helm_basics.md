# Kubernetes — Helm basics

## What problem Helm actually solves

Raw YAML doesn't parameterize — deploying the same app to dev/stage/prod means either copy-pasting 3
near-identical manifest sets (drift risk) or a pile of `sed`/`envsubst` hacks. Helm is a **templating +
release management** layer on top of raw manifests:
- **Templating** — one set of manifest templates + a `values.yaml` per environment, instead of N copies.
- **Release management** — `helm install`/`upgrade` tracks *what's actually deployed* as a versioned
  "release," so `helm rollback` can revert to any prior release version, and `helm history` shows what
  changed when — Kubernetes' raw `kubectl apply` has no native concept of this.

## Chart structure

```
mychart/
  Chart.yaml          # chart metadata: name, version, appVersion
  values.yaml          # default values, overridable per environment
  templates/
    deployment.yaml     # Go-templated manifest, references .Values.*
    service.yaml
    _helpers.tpl         # reusable template snippets/functions
  charts/               # subchart dependencies, if any
```

```yaml
# values.yaml
replicaCount: 3
image:
  repository: my-registry/payments-api
  tag: v2.4.1
resources:
  requests:
    cpu: 250m
    memory: 256Mi
```

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-payments-api
spec:
  replicas: {{ .Values.replicaCount }}
  template:
    spec:
      containers:
        - name: payments-api
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

## Core commands

```bash
helm install myapp ./mychart                              # deploy, creates a new "release" named myapp
helm install myapp ./mychart -f values-prod.yaml           # override defaults with an env-specific file
helm upgrade myapp ./mychart --set image.tag=v2.4.2        # update a running release, one-off value override
helm rollback myapp 3                                       # revert to release revision 3
helm history myapp                                           # list every revision of this release
helm uninstall myapp                                          # remove everything the release created
helm template ./mychart                                        # render manifests locally WITHOUT installing — the fastest way to sanity-check templating before touching a cluster
helm diff upgrade myapp ./mychart -f values-prod.yaml           # (needs the helm-diff plugin) preview exactly what would change — the closest thing Helm has to `terraform plan`
```

**SRE habit:** `helm template` (or `helm diff` with the plugin) before `upgrade`, same instinct as
`terraform plan` before `apply` — don't apply a chart change blind.

## Helm vs. Kustomize vs. raw YAML — when to reach for which

- **Raw YAML** — fine for a handful of simple, rarely-changing manifests. No templating overhead, but
  doesn't scale to multiple environments without copy-paste or external tooling.
- **Kustomize** (built into `kubectl` via `kubectl apply -k`) — patch-based, not templated: you keep a
  `base/` manifest set and `overlays/` per environment that patch specific fields. No new templating
  language to learn, but less powerful for deeply parameterized/conditional logic.
- **Helm** — full templating language (Go templates) + packaging + release/rollback tracking. The
  standard choice for anything distributed/reused (public charts for Prometheus, cert-manager, etc. are
  virtually all Helm), or when you need real release history, not just "what does the YAML look like now."

**Practical default:** reach for Kustomize first if your variation between environments is simple field
overrides (replica count, image tag, resource sizing); reach for Helm when you need real templating
logic, you're consuming/publishing charts others will reuse, or you specifically want release-history/
rollback semantics `kubectl apply` doesn't give you.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What does Helm give you that `kubectl apply` on raw YAML doesn't?* — Templating (one chart,
   parameterized per environment via `values.yaml`, instead of copy-pasted manifest sets) and release
   management — a versioned history of what was actually deployed, with `helm rollback` to revert to any
   prior revision.
2. *What's the Helm equivalent of `terraform plan`, and why does it matter?* — `helm template` (render
   locally without installing) or `helm diff upgrade` with the diff plugin (shows exactly what would
   change) — same habit as reviewing a Terraform plan before `apply`: see the change before it's live.
3. *What's actually in a chart's `values.yaml` versus its `templates/`?* — `values.yaml` holds the
   default, overridable input data (image tag, replica count, resource sizing); `templates/` holds the
   Go-templated manifest structure that references those values — same separation of concerns as
   Terraform's `variables.tf` vs. the resource blocks that consume them.
4. *When would you choose Kustomize over Helm?* — When environment differences are simple field-level
   overrides (not complex conditional logic) and you'd rather not introduce a templating language/release
   abstraction for something `kubectl apply -k` with patch overlays already handles cleanly.
5. *A `helm upgrade` makes things worse. What's your recovery path?* — `helm rollback <release>
   <previous-revision>` — Helm tracks revision history natively, so recovery is a built-in command, not
   manually re-applying old YAML you happened to have saved somewhere.
6. *Why would a platform team publish their own internal apps as Helm charts instead of just keeping raw
   YAML in a repo?* — Parameterization across environments without drift, versioned/rollback-able
   releases, and a packaging format other teams can consume consistently (`helm install` + their own
   `values.yaml`) instead of everyone hand-editing a shared YAML template.