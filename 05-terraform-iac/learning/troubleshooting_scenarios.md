# Terraform — troubleshooting & incident scenarios

These are the situations that actually get you paged, and the ones SRE interviews probe hardest —
"you know the commands" is table stakes, "you know what to do when it's broken at 2am" is the real bar.

## "Error acquiring the state lock"

**What's happening:** another `plan`/`apply` holds the lock (DynamoDB row or backend-native lock) —
either genuinely still running, or left stuck by a killed process.

**What to do:** confirm no other run is actually in progress (check CI, check with teammates) *before*
touching anything. If confirmed stuck: `terraform force-unlock <LOCK_ID>`. Unlocking while something is
genuinely still running risks two concurrent applies corrupting state — this is the single most common
way to turn an annoyance into a real incident.

## Drift: `plan` shows changes you didn't make

**What's happening:** something changed real infra outside Terraform — a manual console fix during an
earlier incident, another automation (autoscaling adjusting capacity), or a provider default changing.

**What to do:** `terraform plan -refresh-only` to see *only* the drift, isolated from any config
changes. Decide per-attribute: should config be applied to revert the manual change, or should the
manual change be accepted (`apply -refresh-only` to pull it into state, and update config to match so it
doesn't show as drift again)? For attributes legitimately managed elsewhere (e.g. ASG `desired_capacity`),
add `ignore_changes` in `lifecycle` instead of fighting it every run.

## Cyclic dependency error

**What's happening:** two resources reference each other's attributes, so Terraform can't determine a
valid creation order (A needs B's output, B needs A's output).

**What to do:** break the cycle — usually one side of the "mutual" dependency isn't actually required at
create time and can be set via a separate `resource`/update afterward, or the shared value should come
from a third resource/data source both depend on, instead of depending on each other directly.

## "Resource already exists" on `apply`

**What's happening:** the real resource exists (created by hand, or by a previous run that updated state
inconsistently), but Terraform's state doesn't know about it, so it tries to create a duplicate and the
provider API rejects it (e.g. an S3 bucket name collision).

**What to do:** `terraform import` the existing resource into state instead of letting Terraform try to
create it again, then run `plan` until the diff is empty.

## Provider version conflicts after `init -upgrade`

**What's happening:** a provider released a breaking change (renamed attribute, changed default
behavior), and an unpinned/loosely pinned `required_providers` constraint picked it up.

**What to do:** pin provider versions deliberately (`~> 5.0` not unbounded) so upgrades are an explicit,
reviewed decision, not something that silently happens on the next `init`. If already broken: check the
provider's changelog for the breaking change, and either adjust config to match the new provider
behavior or pin back to the last known-good version while you plan the migration.

## `apply` fails halfway through

**What's happening:** partial apply — some resources created/updated successfully before a later
resource's API call failed (rate limit, invalid parameter, transient cloud API error). State reflects
whatever Terraform managed to record before the failure, not a clean "before" or "after" snapshot.

**What to do:** don't panic-rollback by hand. Re-run `terraform plan` to see the real current diff
(Terraform is designed to converge toward desired state on repeated runs) — fix whatever caused the
original failure, then `apply` again. Manual intervention in the console first, without checking state,
is how you turn a partial apply into a drifted mess.

## Destroy takes down more than expected

**What's happening:** usually a module/resource dependency wasn't understood — destroying a shared
resource (e.g. a VPC) cascades to everything depending on it, or `-target` wasn't used and a broader
`destroy` was run against a state file covering more than intended.

**What to do:** this is exactly what `prevent_destroy` in `lifecycle` exists for on critical resources,
and why splitting state by blast-radius boundary ([state_management.md](state_management.md)) matters —
prevention here is cheaper than any recovery.

---

## Interview questions (scenario-based, with the short answer you should be able to give cold)

1. *Your `apply` is hanging with "Error acquiring the state lock." Walk me through what you'd check
   before doing anything.* — Confirm whether another `plan`/`apply` is genuinely still running (CI
   dashboard, ask the team) before considering `force-unlock` — unlocking a lock that's actually in use
   risks two concurrent applies corrupting state, which is worse than a hung command.
2. *`plan` shows unexpected changes you're sure nobody made in config. What's your first diagnostic
   step?* — `terraform plan -refresh-only` to isolate drift from config changes, then decide per
   attribute whether to apply config over it (revert) or accept it into state (if the manual/automated
   change should stick).
3. *Two resources seem to need each other's outputs and Terraform errors on a dependency cycle. How do
   you resolve it?* — Identify which side of the "mutual" dependency isn't actually needed at creation
   time, and restructure so neither resource block directly references the other — often via a shared
   third resource/data source, or splitting the update into a separate step after both exist.
4. *An `apply` creating an S3 bucket fails with "bucket already exists," but you're sure you never
   created it through Terraform. What do you do?* — `terraform import` the existing bucket into state
   (someone/something else created it, possibly by hand), then `plan` repeatedly until the diff is empty
   and config genuinely matches the real resource.
5. *A provider upgrade silently broke your config after `init -upgrade`. How would you have prevented
   this, and how do you recover?* — Prevent: pin provider versions with a bounded constraint (`~> 5.0`)
   instead of leaving it unconstrained, so upgrades are a deliberate, reviewed action. Recover: check the
   provider changelog for the breaking change, then either adjust config or pin back to last known-good
   while planning the migration properly.
6. *`apply` fails after creating 3 of 5 resources in a batch. What's the state of your infra, and what's
   your recovery plan?* — Partial apply — the 3 successful resources are tracked in state as created, the
   2 failed ones are not. Recovery is re-running `plan`/`apply` after fixing the root cause of the
   failure — Terraform converges toward desired state on repeated runs — not manually patching things in
   the console first.
7. *How do you prevent a `destroy` from taking down more than intended?* — `prevent_destroy` in the
   `lifecycle` block on critical/shared resources, and structuring state so blast radius is naturally
   limited (splitting state by team/service boundary) rather than relying on remembering to use
   `-target` correctly every time.
8. *What's the actual difference between `terraform state rm` and `terraform destroy -target` when
   you're trying to "undo" Terraform managing a resource?* — `state rm` stops tracking it without
   touching real infra (resource keeps running, just unmanaged); `destroy -target` actually deletes the
   real resource. Confusing these is a classic way to either orphan infra silently or delete something
   you only meant to stop managing.