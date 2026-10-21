# AWS — VPC networking & IAM

## VPC — the building blocks

- **VPC** — your own isolated virtual network within a region, you define its IP range (CIDR, e.g.
  `10.0.0.0/16`).
- **Subnet** — a slice of the VPC's CIDR, tied to **one specific AZ**. "Public" vs. "private" isn't a
  real AWS attribute — it's just **whether the subnet's route table sends `0.0.0.0/0` to an Internet
  Gateway** (public) or not (private).
- **Internet Gateway (IGW)** — attached to the VPC, gives public subnets a path to/from the internet.
- **NAT Gateway** — sits in a *public* subnet, lets instances in a *private* subnet reach the internet
  **outbound only** (e.g. to pull OS updates) without being directly reachable from the internet
  inbound. Billed per-hour plus data processed — a genuine, often-surprising cost line item at scale.
- **Route table** — per-subnet (or shared), decides where traffic goes based on destination CIDR,
  most-specific-match-wins, same logic as Linux routing in `networking_fundamentals.md`.

## Security groups vs. NACLs — worth repeating here, it's asked constantly

- **Security Group** — instance/ENI-level, **stateful** (reply traffic auto-allowed), only supports
  `ALLOW` rules (no explicit deny — just don't allow it).
- **NACL** — subnet-level, **stateless** (must explicitly allow both directions), supports both `ALLOW`
  and `DENY` rules, evaluated in rule-number order. Use a NACL deny rule when you need to explicitly
  block a specific known-bad IP/range regardless of what any security group says — SGs alone can't
  express an explicit deny.

## VPC Peering vs. Transit Gateway

- **VPC Peering** — direct, 1:1 connection between two VPCs, **not transitive** (if A peers with B and B
  peers with C, A cannot reach C through B) — fine for a handful of VPCs, becomes an unmanageable mesh
  of connections (`n*(n-1)/2`) past a certain count.
- **Transit Gateway** — a central hub, every attached VPC connects to *it*, not to each other directly —
  turns the same mesh problem into `n` connections instead of `n²`, the standard answer once you have
  more than a handful of VPCs needing to talk to each other.

## VPC Endpoints — private access to AWS services without the public internet

- **Gateway endpoint** (free) — S3 and DynamoDB only, adds a route table entry, no internet/NAT path
  needed for traffic to those two specific services.
- **Interface endpoint** (hourly + data cost, uses PrivateLink) — most other AWS services (Secrets
  Manager, SSM, ECR, etc.) — creates an ENI with a private IP in your subnet that proxies to the service.
- **Why this matters operationally:** a private subnet with no NAT Gateway *and* VPC endpoints for the
  AWS services it needs can reach those services with zero path to the public internet at all — tighter
  security posture and avoids NAT data processing charges for that traffic.

## IAM — the actual model, not just "policies grant permissions"

- **Principal** (who) + **Action** (what API call) + **Resource** (on what) + **Condition** (under what
  circumstance) = the shape of every IAM policy statement.
- **Identity-based policy** — attached to a user/role/group, defines what *that identity* can do.
- **Resource-based policy** — attached to the resource itself (S3 bucket policy, KMS key policy), defines
  who can access *this resource*, including cross-account — the only mechanism for granting access to
  an identity in a *different* AWS account.
- **Evaluation logic (the actual interview-tested part):** an explicit `Deny` anywhere (identity-based
  or resource-based) **always wins**, overriding any `Allow`. With no explicit deny, if *either* an
  identity-based policy *or* a resource-based policy allows the action, it's allowed (for same-account
  access) — but cross-account access requires **both** sides to allow it (the resource-based policy on
  the target AND the identity-based policy on the caller).
- **Roles vs. users** — a **role** has no long-term credentials; it's **assumed** temporarily (by a
  user, a service, another account) and issues short-lived STS tokens. This is why EC2
  instances/Lambda functions use **instance profiles/execution roles** instead of a user's access keys
  baked into the environment — no long-lived credential to leak.
- **Policy evaluation default: implicit deny.** Nothing is allowed unless something explicitly allows
  it — the baseline posture is zero access, same least-privilege logic as every other access-control
  system in this roadmap.

## Common real IAM mistakes worth naming in an interview

- `"Action": "*", "Resource": "*"` "to get it working" and never tightened — the single most common
  real-world IAM anti-pattern.
- Long-lived access keys on a human user instead of federated SSO + temporary role assumption.
- A resource-based policy accidentally granting broader access than intended because
  `"Principal": "*"` was used to "just make it work," effectively making a resource public.
- Not using **IAM Access Analyzer** (flags resources shared outside the account/org) or
  **Access Advisor** (shows *last-used* timestamps per permission — the actual tool for safely trimming
  over-broad policies based on real usage, not guesswork).

---

## Interview questions (with the short answer you should be able to give cold)

1. *What actually makes a subnet "public" in AWS?* — Nothing inherent to the subnet itself — it's purely
   whether its route table sends `0.0.0.0/0` traffic to an Internet Gateway. The same subnet with that
   route removed becomes effectively private.
2. *Why would a private subnet need a NAT Gateway, and what's the tradeoff vs. a VPC endpoint?* — NAT
   Gateway gives outbound-only internet access (e.g. OS updates) at an hourly + data-processing cost; a
   VPC endpoint gives private access to a *specific* AWS service without any internet path at all, free
   (Gateway type, for S3/DynamoDB) or at a lower interface-endpoint cost — use endpoints for AWS-service
   traffic specifically, NAT only for genuine internet-bound traffic.
3. *Why does VPC Peering become unmanageable past a handful of VPCs, and what replaces it?* — Peering is
   pairwise and non-transitive, so full connectivity between N VPCs needs `n*(n-1)/2` peering
   connections; Transit Gateway centralizes this into a hub-and-spoke model, needing only `n` attachments.
4. *An IAM policy statement has no explicit `Deny`, and one identity-based policy allows an S3 action
   while the bucket policy says nothing about it. Is the action allowed?* — Yes, within the same
   account — either the identity-based or resource-based policy allowing it is sufficient absent an
   explicit deny. Cross-account access is different: it requires **both** the resource-based policy (on
   the target) and the identity-based policy (on the caller) to allow it.
5. *Why do EC2 instances typically use an instance profile/IAM role instead of embedding an IAM user's
   access keys?* — Roles issue short-lived, automatically-rotated STS credentials with no long-term
   secret to leak or manually rotate — a far smaller blast radius than a static access key baked into an
   instance's environment or config file.
6. *What's the actual difference between a security group and a NACL that a job interview is testing
   for, beyond "instance-level vs subnet-level"?* — Statefulness (SG auto-allows return traffic, NACL
   doesn't) and the ability to explicitly `DENY` (NACLs can, SGs can only allow-or-not) — these aren't
   just location differences, they're fundamentally different enforcement models.
7. *How would you find out if an IAM policy is over-permissioned without just guessing and trimming
   blind?* — IAM Access Advisor shows last-used timestamps per granted permission/service — trim based
   on what's actually never used, rather than guessing what "seems unnecessary" and risking breaking
   something still in use.