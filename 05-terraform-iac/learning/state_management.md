# Terraform — state management (deep dive)

`about.md` covers state at a high level; this is the part an SRE actually gets paged for — backend
choice, locking mechanics, splitting state, and moving state between backends without losing anything.

## Backends — where state actually lives

```hcl
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/network/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

- **Local backend** (default, no block at all) — state is a file on disk. Fine for a solo learning
  project, never for a team — no locking, no shared source of truth, one lost laptop = lost state.
- **S3 + DynamoDB** (the common AWS pattern) — S3 stores the state file (versioned + encrypted),
  DynamoDB provides the lock (prevents two concurrent `apply`s corrupting the same state).
- **Terraform Cloud/Enterprise** — managed backend with locking, state history UI, and run
  orchestration built in — less plumbing to own yourself.

**SRE habit:** the state bucket needs its *own* strict access control and versioning enabled — it's
effectively a credentials store (state can contain secrets in plaintext) and your only rollback path if
state gets corrupted.

## Locking — why `apply` sometimes waits or errors

Before writing new state, Terraform acquires a lock (DynamoDB row, or backend-native locking). A second
`apply` run concurrently will block or error (`Error acquiring the state lock`) rather than racing the
first one and corrupting state. If a run dies mid-apply (killed CI job, laptop sleep), the lock can be
left stuck — `terraform force-unlock <LOCK_ID>`, but only after confirming nothing else is actually running.

## Splitting state — one big state file vs. many small ones

A single state file for an entire org's infra means: every `plan` is slow (has to refresh everything),
every lock blocks every team, and one bad `apply` has an org-wide blast radius. The common fix is
splitting state **by boundary that changes independently** — e.g. `network/`, `eks-cluster/`,
`app-foo/` as separate state files/backends, wired together via outputs + `terraform_remote_state`:

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "my-org-terraform-state"
    key    = "prod/network/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_instance" "app" {
  subnet_id = data.terraform_remote_state.network.outputs.private_subnet_id
}
```
**SRE tradeoff:** smaller state = smaller blast radius and faster plans, but more moving pieces and
explicit cross-state wiring to keep straight — the right granularity is "things that are owned/deployed
by different teams or change on different cadences," not maximally split.

## Moving/migrating state

```bash
terraform state mv  aws_instance.old aws_instance.new    # rename within the same state
terraform state mv -state-out=new.tfstate aws_instance.web module.compute.aws_instance.web  # move into a module, or a different state file

# Changing backend config (e.g. migrating from local to S3, or renaming the S3 key):
terraform init -migrate-state
```
`init -migrate-state` is how you move an existing state file to a newly configured backend without
losing history — Terraform prompts to copy the state over.

## Reading state structure (what's actually in the file)

`terraform.tfstate` is JSON: a `version`, a `serial` (incrementing counter — used to detect
conflicting writes), and a `resources` array, each with its type, name, provider, and every attribute
Terraform knows about it (including ones never set in config, like computed IDs/ARNs). This is why
state can contain secrets: any attribute a provider returns — including a generated DB password — lands
here in plaintext unless the backend itself encrypts at rest.

---

## Interview questions (with the short answer you should be able to give cold)

1. *Why is a local backend unacceptable for a team, even a small one?* — No locking (two people can
   `apply` concurrently and corrupt state) and no shared source of truth — state lives on one person's
   disk, so a lost laptop means lost infra tracking.
2. *Walk me through what DynamoDB is doing in an S3 backend setup.* — It's not storing state — it holds
   a lock record during `plan`/`apply` so a second concurrent run blocks/errors instead of racing the
   first and corrupting the S3 state object.
3. *Why would you split one large state file into several smaller ones?* — Blast radius and speed — a
   single org-wide state means every `apply` risks every resource and every `plan` has to refresh
   everything; splitting by team/service/change-cadence boundary limits both.
4. *How do two separate Terraform configs (different state files) share data, like one needing another's
   VPC ID?* — `terraform_remote_state` data source reading the other state's outputs — this is why
   outputs matter even for "internal" configs, not just reusable modules.
5. *What's the risk of state containing secrets, and how do you mitigate it?* — Any attribute a provider
   returns (including generated values like a DB password) is stored in state as plaintext by default —
   mitigate via backend encryption at rest, strict IAM on the state bucket, and treating state access
   like credential access, not like reading a log file.
6. *How do you migrate state from a local backend to S3 without losing history?* — Add/change the
   `backend` block in the `terraform` block, then run `terraform init -migrate-state`, which prompts to
   copy existing state into the new backend.
7. *What does the `serial` field in a state file do?* — An incrementing counter used to detect
   conflicting writes — if two processes have stale serials, the backend can tell a write would
   overwrite newer state and reject it.
8. *You need to rename a resource in config without Terraform destroying and recreating it. What do you
   do?* — `terraform state mv` to update its address in state to match the new config name — the real
   infra is untouched, only Terraform's bookkeeping changes.
9. *What's the actual failure mode state locking prevents?* — Two concurrent `apply` runs both reading
   the same state, both computing a plan from it, and both writing back — the second write can silently
   clobber resources the first run just created/changed, leaving state that doesn't match either plan or reality.