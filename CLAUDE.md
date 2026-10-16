# Working agreement for this repo

This is Shiwang's personal DevOps/SRE learning roadmap. Standing process, authorized in advance so it
doesn't need to be re-confirmed every session:

## Daily study tracking

- Each study day's work (practical exercises, notes, situations) is logged **under the relevant
  module's `learning/` folder**, in that module's `practical_log.md` (dated entries, newest on top).
- At the **end of each study day**, commit and push whatever was added/changed that day to
  `origin/main` — this is a pre-authorized standing action, not something to ask permission for each
  time. Still review `git status`/diff before pushing (same care as always — don't push something that
  looks like it wasn't intended, and never commit secrets/credentials).

## AWS/Terraform practical work

- All hands-on AWS/Terraform practice uses **only** the learning account via
  `AWS_SHARED_CREDENTIALS_FILE=~/.aws/credentials_terraform` (account `003720987974`,
  `terraform-user`). **Never** the account that resolves as `515966498240` /
  `developer-user-v1` — that's Shiwang's company AWS account and is strictly out of bounds from this
  repo. Confirm `aws sts get-caller-identity` shows `003720987974` before any create/modify/destroy call.

## Learning method

- For each new practical topic: Shiwang does the **manual** approach first (console or raw CLI, no
  IaC) to build real understanding, then it gets automated (Terraform, scripts, etc.) afterward — not
  the other way around.
- Pair concept notes with a `situations.md` per module — not "what is X" but "a dev asks you for X,
  what do you actually say and do" — the goal is situational judgment and confidence to operate without
  a lead present, not just tool familiarity.
