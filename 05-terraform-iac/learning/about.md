Terraform:
It is an tool which helps in building/changing/versioning the infra safely & efficiently.

What is IAC..?
Infrastructure as Code — defining and managing infrastructure (servers, networks, load balancers,
DNS, etc.) through machine-readable config files instead of manual console clicks or ad-hoc scripts.
The config is the single source of truth: it's versioned, reviewed (PRs), and reproducible — the same
file can stand up an identical environment every time, instead of "works on this one server I clicked
through by hand."

Terraform specifically is **declarative** (you describe the desired end state, Terraform figures out
how to get there) and **provider-agnostic** (AWS, GCP, Azure, Kubernetes, Datadog... one workflow,
many providers) — that's the main thing that separates it from an imperative tool (a bash script that
runs a fixed sequence of API calls).

---

## What an SRE needs to actually know (not just "I've used Terraform")

- **Core workflow** — `init` (download providers/modules, set up backend) → `plan` (dry-run diff
  against current state) → `apply` (execute the diff) → `destroy` (tear down). The habit that matters:
  **read every `plan` diff before applying it**, especially the `-/+` (destroy-and-recreate) lines —
  that's the one that takes down a resource you didn't mean to touch.
- **State** — Terraform's record of what it thinks exists (`terraform.tfstate`). It's not optional
  bookkeeping — Terraform diffs *against state*, not against real infra, so wrong/stale state means
  wrong plans.
  - **Remote state** (S3 + DynamoDB for locking, or Terraform Cloud) instead of local state: enables
    team collaboration and prevents two people applying at once and corrupting state.
  - **State locking** — DynamoDB (or equivalent) stops concurrent `apply`s from racing each other.
  - **Drift** — when real infra changes outside Terraform (someone edits a resource in the console).
    `terraform plan`/`refresh` surfaces the difference; reconciled via `terraform apply` (push config
    back over the change) or `terraform import` (adopt the manual change into state instead).
- **Resources vs. data sources** — `resource` blocks are things Terraform creates/owns/can destroy;
  `data` blocks are read-only lookups of things that already exist (e.g. an existing VPC ID) that
  Terraform does not manage.
- **Variables & outputs** — `variables.tf` is a module's *input* interface, `outputs.tf` is what it
  *exposes* to whatever calls it (root config or another module). This is what makes a module reusable
  instead of a copy-pasted block of `.tf` files.
- **Modules** — reusable, parameterized infra components. Know the difference between writing one
  (inputs/outputs, sensible defaults) and just consuming public ones from the registry.
- **Workspaces & environment strategy** — how you run the same config against dev/stage/prod: Terraform
  workspaces, or (more common at scale) separate state files / directories per environment with shared
  modules. Know the tradeoffs — workspaces are easy but share the same backend config, which can bite you.
- **Blast radius control** — `terraform plan/apply -target=<resource>` to scope a change; why reaching
  for `-target` often is itself a smell (config is too coupled) rather than a good habit.
- **Secrets** — never hardcode secrets in `.tf` files or let them land in state in plaintext where
  avoidable. Reference Secrets Manager / SSM Parameter Store / Vault instead. Remember: **state itself
  can contain secrets in plaintext** (e.g. a DB password passed as a resource arg) — this is why state
  files need the same access control as the secrets they might contain.
- **Locking down who can apply what** — least-privilege IAM for the Terraform execution role, separate
  from human AWS console access; CI/CD service accounts scoped per environment.
- **CI/CD integration** — running `plan` on PR (visible diff for review) and `apply` on merge to main,
  gated by approval. This is the real-world shape, not running `apply` from a laptop.
- **Lifecycle & failure handling** — `prevent_destroy`, `create_before_destroy`, `ignore_changes`; what
  happens to dependent resources when `apply` fails halfway through (partial apply) and how you recover.
- **Terraform vs. alternatives** — CloudFormation/CDK (AWS-only, imperative-ish via CDK) and Pulumi
  (real programming languages instead of HCL). Know *why* a team picks one, not just that alternatives exist.

---

## Interview questions (with the short answer you should be able to give cold)

**Basics**
1. *What problem does Infrastructure as Code solve?* — Manual/console-driven infra isn't reproducible,
   reviewable, or auditable; IaC makes infra changes go through the same version-control + review
   discipline as application code.
2. *What's the Terraform core workflow?* — `init` → `plan` → `apply` (→ `destroy`), with `plan` as the
   dry-run you always read before `apply`.
3. *Declarative vs. imperative IaC — where does Terraform sit?* — Declarative: you state desired end
   state, Terraform computes the diff and the steps to get there.

**State**
4. *What problem does remote state solve that local state doesn't?* — Team collaboration (shared source
   of truth) and locking (prevents concurrent applies corrupting state); local state also risks being
   lost if it only lives on one laptop.
5. *Someone changed a resource by hand in the console after you applied Terraform. What happens on the
   next `plan`, and how do you fix it?* — `plan` shows drift (diff between state and real infra).
   Reconcile either by applying config over the manual change (if the change should be reverted) or
   `terraform import`/`refresh` to adopt the manual change into state (if it should be kept).
6. *When would you use `terraform import` instead of just deleting and recreating a resource?* — When
   the resource is stateful/costly/risky to recreate (a database, a production load balancer) — import
   brings an existing resource under Terraform management without touching the real infra.
7. *Why does state sometimes need to be treated as sensitive data?* — It can contain secrets in
   plaintext (e.g. a password passed as a resource argument), so it needs encryption at rest + access
   control, not just "it's config."

**Modules & structure**
8. *What's the difference between a module's `variables.tf` and `outputs.tf`?* — `variables.tf` is
   the module's input interface; `outputs.tf` is what it exposes for the caller (root module or
   another module) to consume.
9. *How do you structure Terraform for multiple environments (dev/stage/prod)?* — Shared modules,
   separate state per environment (via workspaces or separate directories/backends), environment-specific
   `.tfvars`.

**Safety / operational judgment**
10. *Why is hardcoding a secret in a `.tf` file a problem even if the repo is private?* — It still ends
    up in git history (hard to fully purge), in everyone-with-repo-access's working copy, and often in
    CI logs — "private repo" isn't the same control boundary as "secret manager with audited access."
11. *What's `-target` for, and why is reaching for it often a bad sign?* — It scopes `plan`/`apply` to
    one resource to limit blast radius; using it often usually means the config has tangled
    dependencies that should be refactored into separate, smaller-blast-radius modules/states.
12. *An `apply` fails halfway through. What state is your infra in, and what do you do?* — Partially
    applied — some resources created/updated, others not; state reflects whatever Terraform managed to
    record before failing. Re-run `plan` to see the real current diff, fix the root cause, then `apply`
    again — Terraform is designed to converge toward desired state on repeated runs, not leave you
    needing a manual rollback.
13. *How do you prevent a critical resource (e.g. a production database) from being destroyed by an
    accidental `apply`?* — `prevent_destroy` lifecycle rule, plus requiring `plan` review/approval in
    CI before `apply` ever runs against prod.

**Scenario**
14. *Walk me through codifying an existing hand-built AWS resource into Terraform.* — `terraform import`
    the resource into state, write matching `.tf` config, run `plan` and iterate until the diff is empty
    (config matches reality exactly) before trusting Terraform to manage it going forward.
