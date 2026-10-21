# AWS — compute & auto scaling

## EC2 — the fundamentals beyond "it's a virtual machine"

- **Instance types** — the letter/family signals the workload shape: `t` (burstable, cheap, for
  variable/low-average load — has **CPU credits**, can run out under sustained load and get throttled —
  a real gotcha for anyone treating `t3.micro` as "small but reliable" under constant load), `m`
  (general purpose, balanced), `c` (compute-optimized), `r` (memory-optimized), `i`/`d` (storage-optimized,
  local NVMe), `g`/`p` (GPU).
- **Pricing models:**
  - **On-Demand** — pay per hour/second, no commitment, most expensive per-hour.
  - **Reserved Instances / Savings Plans** — commit to 1 or 3 years, significant discount, for
    predictable baseline load.
  - **Spot Instances** — bid on spare capacity, up to ~90% cheaper, **can be reclaimed by AWS with ~2
    minutes' warning** — only for genuinely interruptible workloads (batch processing, stateless
    autoscaled fleets with graceful handling of termination).
- **EBS vs. instance store** — EBS is network-attached, persists independently of the instance (survives
  stop/terminate if configured to), can be snapshotted/resized. Instance store is physically attached
  local disk, **gone the moment the instance stops or terminates** — only for genuinely ephemeral/
  cache-style data, never anything you need to survive an instance replacement.

## Lambda — the actual execution model

- **Cold start vs. warm start** — a cold start provisions a fresh execution environment (container
  init + runtime init + your code's init) before running your handler; a warm invocation reuses an
  already-initialized environment. Cold starts are the real, nameable latency tax — mitigated by
  **provisioned concurrency** (pre-warmed environments kept ready, at a standing cost) for
  latency-sensitive paths.
- **Concurrency limits** — account-level and per-function concurrency caps exist; hitting the limit
  causes **throttling** (`429`/throttle errors), not queuing by default for synchronous invocations — a
  real production failure mode under a sudden traffic spike if limits aren't sized/requested ahead of
  need.
- **Execution role** — every Lambda function has its own IAM role, scoped to exactly what that function
  needs — same least-privilege logic as everywhere else, and a common review finding when a function has
  broad `s3:*`/`dynamodb:*` instead of scoped actions/resources.
- **When Lambda is the wrong tool** — long-running processes (15-minute hard execution limit),
  workloads needing consistent low-latency with unpredictable traffic (cold starts), or anything needing
  persistent local state between invocations.

## Auto Scaling Groups (ASG)

- **Launch template** — defines what a new instance looks like (AMI, instance type, security groups,
  user data bootstrap script).
- **Scaling policies:**
  - **Target tracking** — "keep average CPU at 50%" — the simplest, most common, lets AWS compute the
    actual scale-in/out math.
  - **Step scaling** — explicit rules ("if CPU > 80% for 5 min, add 2 instances") — more control, more
    to tune.
  - **Scheduled scaling** — known traffic patterns (business hours, a known weekly batch job) — scale
    ahead of demand instead of reacting to it.
- **Health checks** — ASG can use EC2 status checks *or* ELB health checks; using only EC2 checks means
  an instance that's "up" but failing application health checks (hung process, bad deploy) **won't get
  replaced** — a classic production gap. Always use ELB health checks for anything behind a load balancer.
- **Cooldown period** — prevents the ASG from launching/terminating again immediately after a scaling
  action, giving new instances time to actually start serving before the next scaling decision is made
  — without it, an ASG can over-scale rapidly in response to metrics that haven't stabilized yet.

## ECS/Fargate vs. EKS — when AWS container orchestration doesn't mean Kubernetes

- **ECS** — AWS's own, simpler container orchestrator — less powerful/flexible than Kubernetes, but
  less operational overhead and tighter native AWS integration, no separate "learn Kubernetes" cost for
  a team that doesn't need its full feature surface.
- **Fargate** — serverless compute for containers (works with both ECS and EKS) — no EC2 instances to
  manage at all, pay per-task/pod resource allocation.
- **Pick ECS over EKS when:** the team doesn't need Kubernetes' ecosystem (Helm, operators, the broader
  portability story) and wants the lowest operational overhead — genuinely the right call for many teams,
  not just "the easy/wrong choice," despite Kubernetes' industry mindshare.

---

## Interview questions (with the short answer you should be able to give cold)

1. *A `t3.micro` instance runs fine for weeks, then suddenly gets noticeably slower under sustained
   load. What's likely happening?* — It's a burstable instance type — it accumulates CPU credits during
   idle periods and spends them under load; sustained load exhausts the credit balance and the instance
   gets throttled to its baseline performance, which can look like a sudden, unexplained slowdown.
2. *When is a Spot Instance the wrong choice, regardless of the cost savings?* — For anything stateful or
   that can't tolerate an abrupt ~2-minute-notice termination without graceful handling — a database
   primary, anything without idempotent/resumable processing, or a workload where losing in-flight work
   is costly.
3. *What happens to data on an EC2 instance store volume when the instance stops?* — It's gone — instance
   store is physically local disk tied to that specific instance's lifecycle; unlike EBS, it does not
   persist independently and isn't preserved across a stop (or any replacement).
4. *What's the actual mechanism behind Lambda cold starts, and how do you mitigate them for a
   latency-sensitive path?* — A cold start provisions and initializes a fresh execution environment
   (container, runtime, your code's init) before the handler runs; provisioned concurrency keeps
   pre-warmed environments ready at a standing cost, trading money for eliminating that latency on the
   paths that need it.
5. *An ASG is configured with only EC2 status checks, no ELB health checks. What failure mode does this
   miss?* — An instance that's technically "up" (passes EC2-level checks) but whose application is
   actually unhealthy (hung process, failed deploy, not responding on its port) won't get detected or
   replaced — ELB health checks are needed to catch application-level failure, not just instance-level failure.
6. *Why would a team deliberately choose ECS over EKS for container orchestration?* — Lower operational
   overhead and tighter native AWS integration, when the team doesn't need Kubernetes' broader ecosystem
   (Helm, the operator pattern, multi-cloud portability) — a legitimate choice for teams fully committed
   to AWS without that portability requirement, not just "the easier but inferior option."
7. *Why does an ASG have a cooldown period, and what would happen without one?* — Gives newly launched
   instances time to actually come up and start serving before the next scaling evaluation runs; without
   it, the ASG could react to metrics that haven't stabilized yet from the *previous* scaling action and
   over-scale rapidly in a feedback loop.