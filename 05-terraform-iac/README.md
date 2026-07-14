# 05 — Terraform / Infrastructure as Code

This is a real gap: you've built and migrated startup infra by hand (console/CLI), which is valuable operational experience but not what "IaC skills" means on a resume. This module converts what you already know how to build into reproducible code — should be one of the first two modules you start.

## Depth checklist

- [ ] Core workflow: `init`/`plan`/`apply`/`destroy`, and reading a plan diff critically before applying
- [ ] State: what state actually is, remote state (S3 + DynamoDB lock), why state drift happens and how to reconcile it (`terraform import`, `refresh`)
- [ ] Modules: writing a reusable module (inputs/outputs), vs just copy-pasting `.tf` files
- [ ] Blast radius thinking: why you scope `plan`/`apply` to a target, workspace strategy for multiple environments (dev/stage/prod)
- [ ] Secrets in IaC: never hardcoding — referencing Secrets Manager/SSM instead
- [ ] Alternative: if your org leans CDK/CloudFormation instead of Terraform, the same reasoning skills apply — pick the one your target jobs actually ask for (check job postings) rather than both at first

## Scenario projects

1. **Codify one thing you already built by hand.** Take your simplest startup service (e.g. a Lambda + SQS + S3 pipeline) and write it as Terraform from scratch — this is far more valuable than a tutorial project because you already know the "correct" end state to check against.
2. **Break state on purpose.** Manually change a resource in the AWS console after applying Terraform, then run `plan` and reconcile the drift. This is a very common real-world scenario and a good interview story.
3. **Write one reusable module** (e.g. "standard S3 bucket with lifecycle + encryption") and consume it from two different environments (dev/prod) with different variables.
4. **Destroy-and-rebuild drill.** Practice safely tearing down and recreating a small stack — builds the confidence to explain disaster-recovery-via-IaC in an interview.

## Where you already have evidence

- None yet in your repos — this module has no existing folder to link to. That's fine; it's the point of doing it early. Once you complete project 1, consider adding a new sibling repo (e.g. `terraform-aws-modules`) for ongoing IaC work rather than nesting it under practice repos.
