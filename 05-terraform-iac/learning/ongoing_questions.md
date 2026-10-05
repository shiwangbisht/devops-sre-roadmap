why ansible is used instead of terraform for config management..?

- They solve different layers, not competing solutions for the same job.
- **Terraform = provisioning** — creates/destroys the infra itself (VM, VPC, load balancer, managed DB).
- **Ansible = configuration management** — once a server *exists*, logs in (SSH, agentless) and
  configures what's inside it: installs packages, writes config files, starts services.
- Terraform is **declarative + stateful** — tracks exactly what it created, diffs against desired config.
- Ansible is **procedural/task-based** — a list of steps run in order, no real "state" concept (though
  most modules are written to be idempotent, so re-running is safe).
- Terraform *can* bootstrap a server (`user_data`, `provisioner "remote-exec"`), but Terraform's own
  docs call provisioners a last resort — not trackable/idempotent like resources are.
- Terraform has no good way to express "install these 12 packages, ensure this file has this exact
  content" as a resource graph — that's exactly the shape of problem Ansible is built for.
- **SRE shorthand:** Terraform = "what infra exists," Ansible/Packer/cloud-init = "what's configured on
  top of it."
- Common real pairing: Terraform provisions the VM, Ansible (or a pre-baked AMI via Packer) configures
  the inside.
- In container/Kubernetes-heavy environments this gap often shrinks — "configuration" is just a
  container image, so Ansible has less to do.

---

what is use of terraform import..?

- Brings an **existing** real-world resource (created by hand, by another tool, or before this config
  existed) under Terraform's management — **without recreating it**.
- It just adds an entry to state pointing at the resource's real ID.

```bash
terraform import aws_instance.web i-0123456789abcdef0
```

- **Why needed:** without importing first, Terraform doesn't know the resource already exists — `apply`
  tries to *create a new one*, which either fails (ID/name collision) or creates a duplicate.
- **Always a 3-step workflow, not just the one command:**
  1. `terraform import aws_instance.web i-0123456789abcdef0` — adds it to state.
  2. Write a matching `resource "aws_instance" "web" { ... }` block.
  3. Run `terraform plan` repeatedly, adjusting config, until the diff is **empty**.
- An empty plan = confirmation that config now exactly matches the real resource — so a future `apply`
  won't accidentally change/destroy it based on a wrong guess.
- **SRE use case:** codifying something built by hand in the console into Terraform, safely, with zero
  downtime or recreation.

---

What happens whe we are creating a vpc as an resource and we want use same in EC2 below in code.. so we will use data on taht case..?

- Not quite — common mix-up, worth being precise on.
- **If the VPC is created by a `resource` block in this same config/state → reference it directly.** No
  `data` block needed.
- `data` is only for looking up something Terraform **isn't managing** in this config.

**Case 1 — VPC created in this same config (most common):**
```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id   # direct reference
  cidr_block = "10.0.1.0/24"
}

resource "aws_instance" "web" {
  subnet_id = aws_subnet.public.id
}
```
- Direct reference also makes Terraform infer creation order automatically (VPC before subnet before
  instance) — no `depends_on` needed.

**Case 2 — VPC created elsewhere** (separate state, created by hand, or owned by another team):
```hcl
data "aws_vpc" "existing" {
  tags = {
    Name = "prod-vpc"
  }
}

resource "aws_instance" "web" {
  subnet_id = data.aws_vpc.existing.id   # read-only lookup, Terraform never owns this VPC
}
```

- **The deciding rule:** if *this* `apply` created the VPC → direct `resource` reference.
- Reach for `data` only when the VPC's lifecycle is owned elsewhere — a different Terraform state (see
  `terraform_remote_state` in [state_management.md](state_management.md)), another team, or something
  that was never Terraform-managed at all.
