# Cloud computing — fundamentals

The vocabulary layer underneath every AWS-specific file in this repo — what these terms actually mean,
not just that they exist.

## Service models — IaaS / PaaS / SaaS

- **IaaS** (Infrastructure as a Service) — you manage the OS up; provider manages physical
  hardware/virtualization. EC2.
- **PaaS** (Platform as a Service) — you manage just your application/code; provider manages the OS,
  runtime, scaling. Elastic Beanstalk, Heroku.
- **SaaS** (Software as a Service) — you consume the whole application as a user; manage nothing.
  Gmail, Salesforce.
- **The general tradeoff:** more managed = less operational burden, less control. An SRE career lives
  mostly in IaaS and the infrastructure layer of PaaS (e.g. Kubernetes/EKS sits conceptually between
  IaaS and PaaS — you still manage workload scheduling/config, AWS manages the control plane).

## Shared Responsibility Model (AWS's framing, generalizes to every cloud provider)

**AWS is responsible for security *of* the cloud** (physical data centers, hardware, hypervisor,
managed service internals). **You are responsible for security *in* the cloud** (IAM policies, security
group rules, OS patching on EC2 you manage, data encryption choices, application-level security). This
split **moves** depending on the service: for EC2, you patch the OS; for RDS, AWS patches the OS and
you're responsible for IAM/network access and data; for Lambda, AWS manages everything except your code
and its IAM permissions. Knowing *where the line sits for a specific service* is the actual interview-worthy
version of this answer, not just reciting the model's name.

## Availability Zones vs. Regions

- **Region** — a geographic area (e.g. `us-east-1`), fully independent of other regions (separate
  control planes, no automatic cross-region replication of anything unless you set it up).
- **Availability Zone (AZ)** — one or more discrete, physically separate data centers *within* a
  region, connected by low-latency links, each with independent power/cooling/networking. Multi-AZ
  design protects against a single data center failure; multi-region protects against a whole region
  going down (and against regulatory/data-residency requirements), at the cost of real latency between
  regions and much harder data consistency.
- **Why "99.99% availability" architectures are always multi-AZ at minimum:** a single-AZ deployment's
  availability ceiling is bounded by that one AZ's own failure rate — no amount of redundancy *within*
  one AZ protects against the AZ itself going down.

## Elasticity & auto scaling — the actual value proposition

Not "it's cloud, so it scales" — the specific mechanism is **decoupling capacity from fixed hardware
provisioning**: an Auto Scaling Group adds/removes EC2 instances based on real-time demand (CPU,
request count, custom CloudWatch metrics), so you pay for roughly what you use instead of provisioning
for peak load 24/7. The operational tradeoff: scaling takes real time (instance launch + bootstrap), so
elasticity handles *gradual* demand changes well and sudden spikes poorly without pre-warming — same
underlying lag problem covered in `storage_and_autoscaling.md` for Kubernetes HPA, one layer down.

## CapEx vs. OpEx — why this matters beyond accounting trivia

On-prem: large upfront **capital expenditure** (buy servers, own them, depreciate over years), sized for
peak capacity you may rarely use. Cloud: **operational expenditure** — pay for what you use, scale down
when demand drops, no upfront hardware purchase. This is the actual business case cloud migrations are
pitched on, and it's a real, legitimate interview topic ("why would a company move to cloud" has a real
answer beyond "it's modern").

## Vendor lock-in — the honest tradeoff

Using a cloud provider's managed, proprietary services (DynamoDB, Lambda specifically, proprietary
queue services) gets you less operational burden and often better integration, at the cost of harder
migration to another provider later. Using more portable primitives (containers, Kubernetes, open-source
databases self-hosted on compute) costs more operational effort but keeps you more portable. Neither is
"correct" — it's a real architectural tradeoff a team makes deliberately, and being able to articulate
it (rather than reflexively avoiding or embracing lock-in) is what an interviewer is actually listening for.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the actual difference between IaaS, PaaS, and SaaS, with a concrete example of each?* — IaaS:
   you manage OS-and-up, provider manages hardware (EC2). PaaS: you manage just your app code, provider
   manages OS/runtime/scaling (Elastic Beanstalk). SaaS: you consume the whole application, manage
   nothing (Gmail).
2. *For an RDS database, where does AWS's responsibility end and yours begin, under the Shared
   Responsibility Model?* — AWS patches the underlying OS/database engine and manages the physical
   infrastructure; you're responsible for IAM access control, network/security group configuration,
   and the data itself (encryption choices, backups retention policy where configurable).
3. *Why does a single-AZ deployment have a hard ceiling on achievable availability, regardless of how
   much redundancy you add within that AZ?* — All redundancy within one AZ still shares that AZ's
   underlying failure domain (power, cooling, networking) — if the AZ itself goes down, every
   in-AZ-redundant instance goes down with it; only multi-AZ redundancy protects against that class of failure.
4. *Why does auto scaling handle gradual traffic growth well but struggle with sudden spikes?* —
   Scaling requires real time to provision and bootstrap new capacity (instance launch, app startup) —
   gradual growth gives scaling policies time to react ahead of demand; a sudden spike outpaces that
   provisioning lag unless capacity is pre-warmed above the immediate floor.
5. *What's the real business case for cloud migration, beyond "it's where the industry is headed"?* —
   Converting capital expenditure (buying hardware sized for peak capacity, depreciating over years) into
   operational expenditure (paying for actual usage, scaling down when demand drops) — a genuine
   financial/operational tradeoff, not just a technology trend.
6. *A team avoids every AWS-proprietary managed service (DynamoDB, Lambda, SQS) in favor of
   self-hosting open-source equivalents on EC2/Kubernetes. What are they actually trading for what?* —
   Trading lower operational burden and tighter integration (the managed services) for portability and
   reduced vendor lock-in (self-hosted), at the cost of owning more operational complexity themselves —
   neither choice is inherently correct, it depends on how much the team values portability versus
   operational simplicity.