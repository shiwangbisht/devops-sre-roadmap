# Terraform — core language blocks

## `terraform` block

Pins the Terraform version (`required_version`), declares `required_providers` (and their version
constraints), and configures the **backend** (where state lives — S3, Terraform Cloud, etc.). This is
the block that makes a config reproducible across machines/CI instead of "works on my laptop's version."

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/network/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"   # state locking
    encrypt        = true
  }
}
```

## `provider`

Configures a cloud or API (AWS, GCP, Azure, Kubernetes, Datadog, PagerDuty...) — credentials, region,
and any provider-specific settings. Know **aliases**: a way to configure the *same* provider more than
once in one config, for multi-region or multi-account setups.

```hcl
provider "aws" {
  region = "us-east-1"
}

# Second configuration of the same provider, for a different region
provider "aws" {
  alias  = "eu"
  region = "eu-west-1"
}

resource "aws_instance" "eu_app" {
  provider      = aws.eu       # explicitly use the aliased provider
  ami           = "ami-0abcd1234"
  instance_type = "t3.micro"
}
```

## `resource`

The thing being created (`aws_instance`, `google_compute_network`, `kubernetes_deployment`...). This is
the heart of Terraform — everything else in a config exists to configure, parameterize, or feed values
into resource blocks.

```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id   # often fed by a data source, see below
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
  }
}
```

## `data`

Reads existing infrastructure **without managing it** — looking up an AMI, an existing VPC, a secret
value, an account ID. Terraform will never create/modify/destroy what a `data` block reads; it's
read-only, evaluated fresh on every `plan`.

```hcl
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

data "aws_vpc" "existing" {
  tags = {
    Name = "prod-vpc"
  }
}
```

## `variable`

Inputs to a module (or the root config). Know all five pieces: `type`, `default`, `description`,
`validation`, and `sensitive`.

```hcl
variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "EC2 instance type for the web tier"

  validation {
    condition     = contains(["t3.micro", "t3.small", "t3.medium"], var.instance_type)
    error_message = "instance_type must be one of: t3.micro, t3.small, t3.medium."
  }
}

variable "db_password" {
  type      = string
  sensitive = true   # redacted from plan/apply CLI output and logs
}
```

## `output`

Exposes values to other modules, to the CLI (`terraform output`), or to remote-state consumers
(another config reading this one's state via `terraform_remote_state`).

```hcl
output "instance_public_ip" {
  value       = aws_instance.web.public_ip
  description = "Public IP of the web server"
}

output "db_endpoint" {
  value     = aws_db_instance.main.endpoint
  sensitive = true   # hides value from CLI output, still present in state
}
```

## `locals`

Computed values that keep code DRY — common tags, naming conventions, anything derived once and reused
across multiple resources instead of repeated inline.

```hcl
locals {
  common_tags = {
    Environment = var.environment
    Team        = "sre"
    ManagedBy   = "terraform"
  }

  name_prefix = "${var.project}-${var.environment}"
}

resource "aws_instance" "web" {
  # ...
  tags = merge(local.common_tags, { Name = "${local.name_prefix}-web" })
}
```

## `module`

Reusable packages of resources — the main way to standardize infrastructure across teams, instead of
every team copy-pasting and slowly diverging `.tf` files. A module is just a directory of `.tf` files
with its own `variable`/`output` blocks acting as its interface.

```hcl
# Calling a local module
module "vpc" {
  source = "./modules/vpc"

  cidr_block  = "10.0.0.0/16"
  environment = var.environment
}

# Calling a module from the public registry
module "s3_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 4.0"

  bucket = "${local.name_prefix}-artifacts"
  tags   = local.common_tags
}

# Consuming a module's output
resource "aws_instance" "web" {
  subnet_id = module.vpc.public_subnet_id   # "public_subnet_id" is an output of the vpc module
}
```

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the difference between a `resource` block and a `data` block?* — `resource` is something
   Terraform creates and manages the full lifecycle of (create/update/destroy); `data` is a read-only
   lookup of something that already exists — Terraform never modifies or destroys what a data source reads.
2. *Why would you use a provider `alias`?* — To configure the same provider more than once in one
   config — most commonly multi-region (e.g. us-east-1 + eu-west-1) or multi-account setups, where a
   single resource block needs to target a non-default provider configuration.
3. *What goes in `required_providers`, and why pin provider versions?* — The source and version
   constraint for every provider the config uses. Pinning avoids a provider releasing a breaking change
   and silently altering plans/applies on the next `init -upgrade` or fresh clone.
4. *What's the difference between `variable` and `locals`?* — `variable` is an external input the
   caller sets (has a type, can have a default, can be required); `locals` are values computed
   *inside* the config from other values — not settable from outside, used to avoid repeating an
   expression (like a tag map) across many resources.
5. *What does marking a variable `sensitive = true` actually do — and not do?* — Redacts the value from
   `plan`/`apply` CLI output and logs. It does **not** encrypt it in state — a sensitive variable's
   value is still stored in plaintext in the state file, so state access control still matters.
6. *What's a `variable` block's `validation` for, and when does it run?* — Enforces a constraint on an
   input value (e.g. "must be one of these instance types") at `plan` time, failing fast with a custom
   error message instead of letting a bad value reach the provider API and fail there with a less clear error.
7. *How do you expose a value from a module so the root config (or another module) can use it?* — An
   `output` block inside the module; the caller then references it as `module.<name>.<output_name>`.
8. *What's the difference between a module's `outputs.tf` and the root config's `output` blocks?* — A
   module's outputs are its public interface, consumed by whatever calls the module; the root config's
   outputs are what's exposed to the CLI (`terraform output`) and to other configs reading this state
   via `terraform_remote_state`.
9. *Why use `locals` for tags instead of repeating a tag map in every `resource` block?* — DRY —
   define the common tags once, `merge()` resource-specific tags on top; a single place to update
   when a tagging policy changes instead of hunting through every resource.
10. *What's the practical difference between a local module (`source = "./modules/vpc"`) and a registry
    module (`source = "terraform-aws-modules/s3-bucket/aws"`)?* — A local module is owned/versioned by
    this repo (via git, not a `version` constraint); a registry module is externally maintained and
    versioned — pin its `version` deliberately, since an upgrade can change its resources/outputs.
11. *Where would you reference an existing VPC's ID without letting Terraform manage that VPC?* — A
    `data "aws_vpc"` block, filtered by tags/name — read-only, so it can't accidentally modify or
    destroy infra Terraform doesn't own.
12. *Can an `output` depend on a resource that failed to create?* — No — Terraform builds a dependency
    graph; an output referencing a resource's attribute can't resolve until that resource is
    successfully created, so a failed `apply` leaves that output unset/unknown until the resource exists.
