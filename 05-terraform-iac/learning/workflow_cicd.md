# Terraform — CI/CD workflow & policy as code

Running `terraform apply` from a laptop is how you learn the tool; running it in CI with review gates is
how real teams operate it. This is the operational/process knowledge an SRE is expected to bring, on top
of knowing the language.

## The standard pipeline shape

```
PR opened  -> CI runs: fmt -check, validate, plan -out=plan.tfplan
           -> plan output posted as a PR comment (so reviewers see the diff, not just the code diff)
           -> human review + approval
PR merged  -> CI runs: apply plan.tfplan   (the SAME plan that was reviewed, not a fresh one)
```

Why the saved plan matters: re-running `plan` right before `apply` on merge risks infra having drifted
since review — applying the file that was actually reviewed guarantees what gets executed is exactly
what a human signed off on.

## Who/what is allowed to apply

- **CI service account**, not individual human credentials — scoped IAM role per environment (a
  `prod`-apply role is not the same role used for `dev`-apply), least privilege, no standing admin access.
- **Humans applying from a laptop** should be the exception (break-glass/incident scenarios), not the
  norm, for anything beyond a personal sandbox — it bypasses the review trail CI gives you.
- **Environment promotion** — the same reviewed config/module version typically moves dev → stage →
  prod, rather than hand-editing config per environment at apply time.

## Policy as code — gating *what* can be applied, not just reviewing it by eye

Human review doesn't scale to catching every policy violation (e.g. "no S3 bucket may be public," "every
resource must have a `CostCenter` tag"). Policy-as-code tools evaluate the plan against rules before
apply is allowed to proceed:

- **Sentinel** (Terraform Cloud/Enterprise native) — policies written against the plan's JSON output.
- **Open Policy Agent (OPA) / Conftest** — same idea, open-source, policy in Rego.
- **tfsec / checkov** — static analysis of `.tf` files for security misconfigurations (public S3
  buckets, overly permissive security groups, unencrypted resources) — run earlier, on the raw config
  rather than the plan.

```bash
tfsec .            # scan config for known-bad security patterns
checkov -d .        # broader policy scanning, many built-in rule sets (CIS benchmarks, etc.)
```

## Drift detection

Infra can change outside Terraform (manual console fix during an incident, another automation). A
scheduled CI job running `terraform plan -refresh-only` (or `plan` with no apply) on a cadence, alerting
if it shows a non-empty diff, is the standard way to catch this before it silently diverges further —
this is a real operational pattern, not just an interview talking point.

## Tools worth knowing by name (even without hands-on depth yet)

- **Atlantis** — self-hosted tool that automates the plan-on-PR / apply-on-merge-comment workflow
  directly in GitHub/GitLab, without building that pipeline logic yourself in raw CI config.
- **Terraform Cloud/Enterprise** — managed runs, policy as code (Sentinel), state hosting, and a UI for
  plan review, as a packaged alternative to self-hosting all of this in your own CI.
- **Terragrunt** — a thin wrapper around Terraform for keeping multi-environment config DRY (reduces
  copy-pasted `backend`/`provider` boilerplate across dev/stage/prod directories).

---

## Interview questions (with the short answer you should be able to give cold)

1. *Why run `plan` on PR and `apply` on merge, instead of just running `apply` directly?* — Gives
   reviewers a visible diff of the actual infra change before it happens, same discipline as code
   review — catches destructive/unexpected changes before they execute, not after.
2. *Why apply the exact saved plan file instead of re-running `plan` right before `apply`?* — Infra can
   drift between PR review and merge; applying the saved plan guarantees what executes is exactly what
   a human reviewed, not a fresh (possibly different) diff.
3. *Should CI use a human's AWS credentials to run `apply`?* — No — a dedicated, least-privilege service
   account/role scoped to the environment it applies to, separate from any individual's standing access,
   so applies are auditable and not tied to whoever happened to be logged in.
4. *What's "policy as code" solving that PR review by eye doesn't scale to?* — Enforcing rules
   consistently across every plan/config (no public S3 buckets, required tags, allowed instance types)
   without relying on a human reviewer to remember and catch every violation by hand.
5. *What's the difference between tfsec/checkov and Sentinel/OPA in this pipeline?* — tfsec/checkov scan
   raw `.tf` config for known-bad patterns (static analysis, runs early/fast); Sentinel/OPA evaluate the
   actual *plan* (what will really change), which can catch issues static config scanning can't (e.g.
   a variable-driven value that only becomes risky at a specific environment's values).
6. *How do you catch infrastructure drift before it causes an incident?* — A scheduled CI job running a
   refresh-only or plain `plan` (no apply) that alerts when it shows a non-empty diff — catches
   out-of-band changes (manual console fixes, other automation) proactively instead of discovering them
   during the next real deploy.
7. *What problem does Atlantis solve that a hand-rolled CI pipeline doesn't automatically give you?* —
   It wires the PR-comment-driven plan/apply workflow (plan auto-runs on PR, apply triggered by a PR
   comment after approval) directly into the VCS without you building and maintaining that glue logic
   yourself in raw pipeline scripts.
8. *Why would prod and dev use different IAM roles for Terraform's CI apply step, rather than one shared
   role?* — Least privilege and blast radius — a compromised or misconfigured dev pipeline shouldn't be
   able to touch prod resources; separate roles also make audit logs clearly attributable per environment.
9. *What's the risk of letting engineers `apply` from their laptops routinely, even with the same
   config?* — No review trail, no guarantee the applied plan matches what anyone else has seen, and
   personal credentials (broader access, less auditable) doing production changes instead of a scoped,
   logged service identity.