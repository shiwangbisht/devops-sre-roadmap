# Terraform — situations (the "what do you actually say" doc)

Not "what is X" — this is "a dev/PM asks you for something, mid-conversation, no time to go read docs.
What do you do, what do you say out loud, and what tradeoff are you actually making." The goal is being
able to answer these without a lead in the room.

---

### "Can you just add this one resource directly in the console real quick? We need it live in 5 minutes."

**What you say:** "I can, but then Terraform's state won't know about it — next `plan` will either try
to recreate it or show permanent drift. If it's genuinely urgent, I'll create it by hand now and import
it into Terraform right after, same day — not leave it undocumented."

**What you actually do:** create it manually if truly urgent, then `terraform import` + write matching
config before end of day, `plan` until the diff is empty. Never let "just this once" become permanent
untracked infra.

### "Why can't we just run `terraform apply` straight from your laptop, it's faster?"

**What you say:** "It works, but nobody else sees the diff before it's live, and it's tied to my personal
credentials instead of an auditable pipeline identity. If something breaks at 2am, nobody can tell what
was actually applied or by whom. The 2 minutes a PR-reviewed `plan` costs is cheap insurance."

### "The pipeline's apply failed halfway through, prod is half-broken, what do you do?"

**What you say:** "I don't start manually fixing things in the console first — that's how you turn a
partial apply into drift nobody can reconcile. I re-run `plan` to see Terraform's actual view of current
state, fix whatever caused the failure, and let `apply` converge it — that's what it's designed for."

### "Someone on the team 'quickly fixed' a security group in the console during an incident last night. What now?"

**What you say:** "First `plan -refresh-only` to see exactly what changed, in isolation from any other
config changes. Then decide: was the manual fix actually correct (import it / update config to match),
or was it a stopgap that needs to be replaced with config to avoid it quietly reverting on the next
apply? I don't just apply over it blind, and I don't just leave it as permanent drift either."

### "Dev wants a new environment (staging-2) spun up today, copy of staging."

**What you say:** "If staging is already a module with environment-specific `.tfvars`, this is a new
`.tfvars` file and a new state/workspace, not new code — should take under an hour, not a rebuild."
If it's *not* modularized yet: "This is a good forcing function to modularize staging now, instead of
copy-pasting `.tf` files — costs a bit more time today, saves it every time after."

### "Why do we need a whole separate state file for this, can't it just live with everything else?"

**What you say:** "Blast radius. If it's in the same state as prod network infra, every apply to this
new thing risks prod's `plan` picking up unrelated changes, and a lock on one blocks the other. Splitting
it costs one `terraform_remote_state` reference to share data, which is a small price for isolation."

---

<!-- Add new situations as they come up in real work or practice. Template:

### "<what the dev/PM said, close to verbatim>"

**What you say:** <the actual words, not theory>

**What you actually do:** <the mechanics, if different from what you say>

-->
