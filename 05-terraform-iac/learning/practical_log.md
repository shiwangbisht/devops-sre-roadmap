# Terraform — practical log

Running log of hands-on work in the learning-only AWS account (`003720987974`, `terraform-user` —
never the company account). Every entry: what we ran, what happened (including breakage), and the
reasoning behind any judgment call — this is what turns "I've used Terraform" into "I know why I'd do
it this way."

**Safety reminder before any `apply`/`destroy`:**
```bash
AWS_SHARED_CREDENTIALS_FILE=~/.aws/credentials_terraform aws sts get-caller-identity
# must show Account: 003720987974 — stop and check if it shows anything else
```

---

<!-- Newest entries on top. Template:

## YYYY-MM-DD — <what we built/broke>

**Goal:** <what we were trying to learn/verify>

**Commands run:**
```bash
...
```

**What happened:** <real output/behavior, including anything unexpected>

**Judgment call / why:** <the reasoning an SRE would need to defend in a room>

**Self-test tie-in:** <which depth-checklist/self-test item this now lets you answer cold>

-->
