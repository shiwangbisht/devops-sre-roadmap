# Terraform — built-in functions & expressions

HCL isn't a general-purpose language (no user-defined functions, no loops as statements), but it has a
rich set of built-in functions and expression forms that do the job — this is what turns static config
into something that reacts to inputs. An SRE should be fluent reading these even more than writing them
from scratch, since most real configs lean on them heavily.

## Common built-in functions

```hcl
merge(map1, map2)              # combine maps, later args win on key conflicts — classic for tags
lookup(map, key, default)      # safe map access with a fallback instead of an error on missing key
coalesce(a, b, c)              # first non-null/non-empty value in the list
concat(list1, list2)           # combine lists
length(list_or_map_or_string)  # count elements/characters
element(list, index)           # get item at index (wraps around for out-of-range index)
contains(list, value)          # true/false membership check
join(",", list)                # list -> delimited string
split(",", string)             # delimited string -> list
try(expr, default)             # evaluate expr, fall back to default if it errors (e.g. missing optional attribute)
jsonencode(value)               # HCL value -> JSON string (common for IAM policy documents)
file("path/to/file")           # read a file's contents into a string at plan time
```

```hcl
locals {
  common_tags = merge(
    { ManagedBy = "terraform", Team = "sre" },
    var.extra_tags   # caller-supplied tags layered on top
  )

  instance_type = lookup(var.instance_type_overrides, var.environment, "t3.micro")
}
```

## `for` expressions — transform a list/map into another list/map

```hcl
variable "names" {
  default = ["web", "api", "worker"]
}

locals {
  # list -> list, transformed
  upper_names = [for n in var.names : upper(n)]

  # list -> map
  name_lengths = { for n in var.names : n => length(n) }

  # filter with an `if`
  short_names = [for n in var.names : n if length(n) <= 3]
}
```

## Conditional expressions — `condition ? true_val : false_val`

The only form of "if" for a *value* in HCL (there's no `if` statement, only this ternary):

```hcl
resource "aws_instance" "web" {
  instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"
}
```

## `dynamic` blocks — generate repeated nested blocks from a collection

For nested blocks *inside* a resource (like multiple `ingress` rules in a security group) that need to
vary by input, instead of writing each one out by hand:

```hcl
variable "ingress_rules" {
  type = list(object({
    port        = number
    cidr_blocks = list(string)
  }))
  default = [
    { port = 443, cidr_blocks = ["0.0.0.0/0"] },
    { port = 22,  cidr_blocks = ["10.0.0.0/8"] },
  ]
}

resource "aws_security_group" "web" {
  name = "web-sg"

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
```

## String interpolation & heredoc

```hcl
name = "${var.project}-${var.environment}-web"   # interpolation (often unnecessary — `"${var.x}"` == `var.x` if it's the whole string)

user_data = <<-EOF
  #!/bin/bash
  echo "Deploying ${var.project}"
  EOF
```

---

## Interview questions (with the short answer you should be able to give cold)

1. *What does `merge()` do when two maps share a key?* — The later argument wins — `merge(a, b)` lets
   `b`'s value for a shared key overwrite `a`'s. Order matters, which is exactly why it's used for
   "defaults, then overrides" patterns like common tags + caller-supplied extras.
2. *Why use `lookup(map, key, default)` instead of `map[key]` directly?* — `map[key]` errors if the key
   doesn't exist; `lookup` lets you supply a fallback, which is safer for optional/environment-specific
   overrides where not every key is guaranteed to be present.
3. *What's a `for` expression, and how is it different from `count`/`for_each` on a resource?* — A `for`
   expression transforms one list/map into another *value* (used inside a `locals`/variable
   assignment); `count`/`for_each` on a resource control how many *resource instances* get created.
   They can work together — a `for` expression often builds the map that a resource's `for_each` consumes.
4. *There's no `if` statement in HCL — how do you conditionally set a value?* — The ternary conditional
   expression: `condition ? true_value : false_value`.
5. *What's a `dynamic` block for, and when would you need one?* — Generates repeated *nested* blocks
   inside a resource (like multiple `ingress` rules in a security group) from a list/map input, instead
   of hardcoding each nested block — needed whenever the number of nested blocks varies by input rather
   than being fixed.
6. *What does `try()` do, and give a realistic use case.* — Evaluates an expression and falls back to a
   default if it errors, instead of failing the whole plan — common when reading an optional attribute
   that might not exist on every object in a list (e.g. some entries have a `description` key, others don't).
7. *What's `jsonencode()` commonly used for in AWS Terraform code?* — Building IAM policy documents as
   native HCL maps/objects instead of a raw JSON heredoc string — keeps the policy readable and lets you
   use variables/expressions inside it, then converts to the JSON string the API expects.
8. *What does `file()` do, and when does it run?* — Reads a file's contents into a string, evaluated at
   `plan` time — commonly used for things like loading a startup script into `user_data` from a separate
   `.sh` file instead of inlining it as a heredoc.
9. *If you need to filter a list down to only elements matching a condition inside a `for` expression,
   how do you do it?* — Append an `if` clause: `[for x in list : x if <condition>]`.