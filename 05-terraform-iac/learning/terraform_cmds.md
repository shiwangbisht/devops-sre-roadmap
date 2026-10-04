# Terraform CLI — commands an SRE actually uses

> Note: this machine has **OpenTofu** installed (`tofu`, v1.12.5 — the open-source Terraform fork).
> Every command below works identically with `tofu` instead of `terraform`; syntax is a 1:1 match.

---

## Core workflow (the 90% you run daily)

```bash
terraform init                 # download providers/modules, set up backend — run after clone or backend/provider change
terraform plan                 # dry-run: show the diff between config and real state, change nothing
terraform plan -out=plan.tfplan   # save the plan to a file so `apply` executes EXACTLY what you reviewed
terraform apply                # execute the diff (prompts for confirmation)
terraform apply plan.tfplan    # apply a previously saved plan — no surprises, no re-prompt needed
terraform apply -auto-approve  # skip the confirmation prompt — CI pipelines only, never run by hand on prod
terraform destroy              # tear down everything in this state (prompts for confirmation)
```

**SRE habit:** in CI, always `plan -out=plan.tfplan` on PR, have a human review the diff, then
`apply plan.tfplan` on merge — never re-plan right before apply, since infra could have drifted
between review and apply.

## Scoping a change (blast radius control)

```bash
terraform plan  -target=aws_instance.web      # limit plan to one resource (and its dependents)
terraform apply -target=aws_instance.web      # limit apply likewise
terraform destroy -target=aws_instance.web    # destroy just one resource
```
Reaching for `-target` often = a sign the config/module boundaries need refactoring, not a habit to lean on.

## State inspection & management

```bash
terraform state list                     # list every resource Terraform is tracking
terraform state show aws_instance.web    # show the full attributes of one resource in state
terraform show                           # human-readable dump of the current state
terraform show -json                     # machine-readable state, for scripting/tooling
terraform refresh                        # reconcile state with real infra, without changing config (deprecated in favor of `plan -refresh-only`)
terraform plan -refresh-only             # show ONLY drift (state vs. reality), no config changes
terraform apply -refresh-only            # accept the drift into state without touching real infra

terraform state mv  aws_instance.old aws_instance.new   # rename/move a resource in state without destroying it
terraform state rm  aws_instance.web                    # stop tracking a resource (does NOT destroy it in real infra)
terraform state pull                     # download raw state (e.g. to inspect/back up remote state)
terraform state push                     # force-upload local state to remote backend — dangerous, last resort
```

**SRE habit:** `state rm` + a fresh `import` is how you fix "Terraform wants to destroy this but I
don't want it managed anymore" without actually deleting the real resource.

## Importing existing (hand-built) infra

```bash
terraform import aws_instance.web i-0123456789abcdef0   # adopt an existing resource into state by its real ID
```
Always followed by writing matching `.tf` config and re-running `plan` until the diff is empty —
an empty plan is how you confirm config now exactly matches reality.

## Forcing a resource to be recreated

```bash
terraform apply -replace="aws_instance.web"   # mark one resource for destroy+recreate on next apply (replaces old `terraform taint`)
terraform taint aws_instance.web              # legacy equivalent — deprecated, prefer -replace
terraform untaint aws_instance.web            # undo a taint
```
Used when a resource is "wrong" in a way config can't express (e.g. corrupted EC2 instance) and the
fix is simply: destroy it, let Terraform build a fresh one.

## Variables & output

```bash
terraform plan -var="instance_type=t3.micro"     # pass a single var on the CLI
terraform plan -var-file="prod.tfvars"           # pass a whole var file (common per-environment pattern)
terraform output                                 # show all root module outputs
terraform output instance_ip                     # show one specific output
terraform output -json                           # machine-readable outputs, for piping into other tooling/scripts
```

## Formatting, validation, linting

```bash
terraform fmt              # auto-format .tf files to canonical style — run before every commit
terraform fmt -check       # CI-friendly: exit non-zero if anything isn't formatted, don't rewrite
terraform validate         # check config is syntactically valid and internally consistent (no AWS calls)
```
**SRE habit:** `fmt -check` + `validate` as cheap, fast CI gates before the (slower, API-calling) `plan` step.

## Workspaces (environment separation)

```bash
terraform workspace list            # list all workspaces
terraform workspace new staging     # create + switch to a new workspace
terraform workspace select prod     # switch to an existing workspace
terraform workspace show            # print current workspace
```

## Providers & modules

```bash
terraform providers              # show which providers this config requires
terraform init -upgrade          # re-resolve provider/module versions to latest allowed by constraints
terraform get                    # download/update module dependencies without a full init
terraform providers lock -platform=linux_amd64   # pre-generate provider checksums for a target CI platform
```

## Debugging & troubleshooting

```bash
TF_LOG=DEBUG terraform apply     # verbose provider/API-call logging — biggest hammer for "why did this fail"
TF_LOG=TRACE terraform apply     # even more verbose (every internal step)
TF_LOG_PATH=./tf.log terraform apply   # write debug log to a file instead of stdout
terraform graph | dot -Tsvg > graph.svg   # visualize resource dependency graph (needs graphviz's `dot`)
terraform console                # interactive REPL to evaluate expressions against current state — great for checking interpolations without a full apply
```

## Misc

```bash
terraform version                # show Terraform/OpenTofu + provider versions in use
terraform force-unlock <LOCK_ID> # manually release a stuck state lock — only after confirming no other apply is actually running
```
**SRE habit:** `force-unlock` is the command you reach for during an incident when someone's `apply`
got killed mid-run and left the DynamoDB lock stuck — confirm first that nothing is still running,
or you'll get two concurrent applies corrupting state.

---

## Quick "what's safe to run anytime" reference

| Command | Changes real infra? | Changes state? | Safe to run freely |
|---|---|---|---|
| `plan` | No | No | Yes |
| `validate` / `fmt` | No | No | Yes |
| `state list` / `show` / `output` | No | No | Yes |
| `console` | No | No | Yes |
| `plan -refresh-only` | No | No | Yes |
| `apply` | **Yes** | Yes | Only after reading the plan |
| `apply -refresh-only` | No | Yes | Careful — accepts drift as "correct" |
| `import` | No | Yes | Careful — double-check the resource ID |
| `state mv` / `state rm` | No | Yes | Careful — easy to lose tracking of a resource |
| `destroy` / `apply -replace` | **Yes, destructive** | Yes | Only with a reviewed plan, never on prod by hand |
| `force-unlock` | No | Yes (lock) | Only after confirming no other apply is running |

---

## Interview questions (CLI-focused, with the short answer you should be able to give cold)

1. *What's the difference between `terraform plan` and `terraform apply`?* — `plan` is a read-only
   dry-run that computes and shows the diff between config and state/real infra; `apply` actually
   executes that diff. Never skip reading `plan` output before `apply`.
2. *Why would you run `plan -out=plan.tfplan` and then `apply plan.tfplan` instead of just
   `apply`?* — Guarantees apply executes *exactly* what was reviewed — infra could otherwise drift
   between a plain `plan` and a later plain `apply`, so what gets applied might not match what a
   reviewer approved.
3. *What does `terraform state rm` do, and how is it different from `destroy -target`?* — `state rm`
   stops Terraform from tracking a resource without touching the real infra at all; `destroy -target`
   actually deletes the real resource. Mixing these up is a classic way to either orphan a resource or
   accidentally delete one you meant to just stop managing.
4. *When would you use `terraform import`?* — To bring an existing, hand-created resource under
   Terraform management without recreating it — e.g. codifying infra that was originally built by hand
   in the console.
5. *What's `terraform apply -replace` for, and what did it replace?* — Forces one resource to be
   destroyed and recreated on the next apply, for cases config can't express (e.g. a corrupted
   instance). It replaces the older `terraform taint`/`untaint` commands, which are deprecated.
6. *What's the difference between `terraform refresh` (or `plan -refresh-only`) and a normal
   `plan`?* — A refresh-only plan shows *only* drift between state and real infra, without proposing
   any config-driven changes — useful for spotting out-of-band changes in isolation.
7. *Your `apply` fails partway and a teammate says the state lock is stuck. What do you do?* — Confirm
   no other `apply`/`plan` is genuinely still running (check CI, check with the team), only then run
   `terraform force-unlock <LOCK_ID>` — unlocking while something is actually running risks two
   concurrent applies corrupting state.
8. *How do you debug a provider API call that's failing with a cryptic error?* — `TF_LOG=DEBUG` (or
   `TRACE` for more detail) around `terraform apply`/`plan`, optionally `TF_LOG_PATH` to capture it to
   a file instead of scrolling stdout.
9. *What do `terraform fmt -check` and `terraform validate` each catch, and why run both in CI before
   `plan`?* — `fmt -check` catches style/formatting drift (no logic check); `validate` catches
   syntax/internal-consistency errors without calling any provider API. Both are fast and
   API-call-free, so they're cheap gates to fail fast before the slower `plan` step.
10. *What does `terraform console` let you do that `plan`/`apply` don't?* — An interactive REPL to
    evaluate expressions/interpolations against current state — lets you sanity-check something like
    `aws_instance.web.private_ip` without running a full plan or apply.
11. *How do you move a resource to a new address in config (e.g. after refactoring into a module)
    without Terraform destroying and recreating it?* — `terraform state mv` to update the resource's
    address in state to match the new config location, so Terraform sees it as "already exists here"
    instead of "needs creating."
12. *What's the practical difference between `-var` and `-var-file` on the CLI, and when do teams use
    `-var-file`?* — `-var` sets one value inline; `-var-file` loads a whole set, which is the standard
    way to separate per-environment values (`dev.tfvars`, `prod.tfvars`) from shared config.
