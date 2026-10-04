# Terraform — meta-arguments

Meta-arguments aren't resource-type-specific attributes (like `ami` or `instance_type`) — they're
special arguments **every** `resource` and `module` block understands, because Terraform itself
interprets them, not the provider. This is the part that controls *how many* get created, *in what
order*, and *how a change is handled* — arguably more SRE-relevant day to day than knowing every
attribute of every resource type.

---

## `count` — create N identical-ish copies

Creates a list of N instances of a resource, indexed `0` to `N-1`. Good for simple "just N of the same
thing," but every resource is addressed by its *numeric index* — if you remove index `2` from the
middle, everything after it shifts and Terraform wants to destroy/recreate it. This is the #1 reason
SREs prefer `for_each` once a resource set can grow/shrink.

```hcl
resource "aws_instance" "web" {
  count         = 3
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  tags = {
    Name = "web-${count.index}"   # web-0, web-1, web-2
  }
}
```

## `for_each` — create one per map/set entry, keyed by a stable identifier

Same idea as `count`, but each instance is addressed by a **key** (string) instead of a numeric index.
Removing one entry only destroys *that* entry — the rest are untouched. This is the default choice for
any set that isn't guaranteed to be a fixed, never-changing count.

```hcl
variable "instances" {
  type = map(string)
  default = {
    web = "t3.micro"
    api = "t3.small"
  }
}

resource "aws_instance" "this" {
  for_each      = var.instances
  ami           = data.aws_ami.amazon_linux.id
  instance_type = each.value           # each.key == "web"/"api", each.value == the instance type

  tags = {
    Name = "server-${each.key}"
  }
}
```

**SRE rule of thumb:** `count` for a truly fixed number of identical resources (e.g. "always exactly 1
NAT gateway"); `for_each` for anything that maps to real-world named things (per-environment,
per-service, per-AZ) that could be added/removed over time.

## `depends_on` — explicit dependency, for things Terraform can't infer

Terraform normally infers ordering automatically from references (`aws_instance.web` referencing
`aws_security_group.web.id` already implies "create the security group first"). `depends_on` is for
the rare case where one resource depends on another but **doesn't reference any of its attributes** —
e.g. an IAM policy needing to exist before an app starts, even though no attribute is actually shared.

```hcl
resource "aws_iam_role_policy" "app" {
  # ...
}

resource "aws_instance" "app" {
  # no attribute of aws_iam_role_policy.app is referenced here, but the role
  # MUST exist before the instance boots and tries to assume it
  depends_on = [aws_iam_role_policy.app]
  # ...
}
```
**SRE habit:** reach for `depends_on` only when you've confirmed there's genuinely no attribute
reference to create the dependency implicitly — overusing it makes the dependency graph harder to
reason about than it needs to be.

## `lifecycle` — controls how a resource is changed/destroyed

The block SREs care about most, because it's directly about blast radius and avoiding unwanted outages.

```hcl
resource "aws_instance" "web" {
  # ...

  lifecycle {
    create_before_destroy = true        # bring up the replacement BEFORE destroying the old one
    prevent_destroy        = true       # `destroy`/`apply` that would delete this resource errors out instead
    ignore_changes          = [tags]    # Terraform stops caring if `tags` drifts (e.g. changed by another automation)
    replace_triggered_by    = [aws_ami.web.id]  # force recreate whenever this OTHER resource's value changes
  }
}
```

- **`create_before_destroy`** — critical for anything that can't have downtime between destroy and
  recreate (e.g. a launch template behind an ASG, a DNS record). Without it, Terraform's default is
  destroy-then-create, which means a gap with *nothing* serving.
- **`prevent_destroy`** — a safety rail on resources where an accidental destroy would be a real
  incident (prod database, the state bucket itself). `terraform destroy` or an `apply` that would
  remove this resource fails loudly instead of silently deleting it.
- **`ignore_changes`** — for attributes managed by something other than Terraform after creation
  (autoscaling adjusting `desired_capacity`, an operator tagging resources by hand) so `plan` doesn't
  show permanent, unactionable drift on every run.
- **`replace_triggered_by`** — force a resource to be recreated when *another* resource/value changes,
  even if nothing about this resource's own config changed (e.g. recreate instances whenever a new AMI
  is built).

## `provider` (meta-argument) — pick a non-default provider config

Covered in [code_components.md](code_components.md) from the provider-block side; as a meta-argument on
a `resource`/`module`, it's how you tell *that specific resource* to use an aliased provider instead of
the default one (multi-region/multi-account).

```hcl
resource "aws_instance" "eu_app" {
  provider = aws.eu   # use the aliased provider, not the default region
  # ...
}
```

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the difference between `count` and `for_each`, and when would you pick one over the
   other?* — `count` indexes by position (0, 1, 2...); `for_each` indexes by a stable key from a
   map/set. Prefer `for_each` whenever the set of resources can grow or shrink, because removing a
   middle element under `count` reshuffles every index after it and causes unnecessary
   destroy/recreate; `count` is fine for a genuinely fixed number of identical resources.
2. *You removed one entry from the middle of a `count`-based resource list. What does `plan` show, and
   why?* — It shows every resource *after* the removed index being destroyed and recreated — because
   `count` addresses resources by index, removing index 1 shifts what used to be index 2 into index 1's
   slot, which Terraform sees as "index 1 changed identity."
3. *When do you need `depends_on` instead of letting Terraform infer the dependency?* — Only when one
   resource genuinely depends on another but doesn't reference any of its attributes in config — e.g.
   ordering based on a side effect (an IAM policy existing) rather than a data dependency.
4. *What does `create_before_destroy` change about the default apply behavior, and why does it
   matter?* — Default behavior is destroy-then-create; `create_before_destroy` flips that to
   create-then-destroy, which avoids a gap with nothing serving traffic — essential for anything fronted
   by a load balancer, DNS record, or ASG launch config/template.
5. *What does `prevent_destroy` actually protect against, and what doesn't it protect against?* — It
   makes `destroy` or any `apply` that would delete that specific resource fail with an error. It does
   **not** protect against the resource being modified/replaced via `-replace`, and it doesn't prevent
   manual deletion outside Terraform (e.g. in the console).
6. *Why would you add an attribute to `ignore_changes`, and what's the downside?* — To stop `plan` from
   showing permanent drift on an attribute managed outside Terraform (e.g. autoscaling adjusting
   `desired_capacity`). Downside: Terraform will also ignore *unintentional* drift on that attribute —
   if someone changes it by mistake, Terraform won't flag or fix it anymore.
7. *What's `replace_triggered_by` for, and give a real example?* — Forces a resource to be recreated
   when a referenced value elsewhere changes, even though nothing in this resource's own config changed
   — e.g. recreating EC2 instances whenever a new AMI ID is produced by a separate `aws_ami` data source
   or build pipeline.
8. *Why might overusing `depends_on` be a code smell?* — It's an escape hatch for dependencies
   Terraform can't infer; relying on it heavily instead of structuring config so dependencies are
   implied by attribute references makes the dependency graph harder for the next person to reason
   about, and is often a sign resources should reference each other's outputs directly instead.
9. *What's the `provider` meta-argument used for on a resource, versus the `provider` block itself?* —
   The `provider` block declares/configures a provider (optionally aliased); the `provider =` meta-argument
   on a specific `resource`/`module` selects *which* provider configuration (default or aliased) that
   resource should use — needed for multi-region/multi-account setups.
10. *Can you use `count` and `for_each` on the same resource block?* — No — they're mutually exclusive
    on a single resource/module block; you pick one strategy per block.