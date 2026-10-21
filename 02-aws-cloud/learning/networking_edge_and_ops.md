# AWS — load balancing, DNS/CDN, and operational tooling

## Load balancer types — which one and why

- **ALB (Application Load Balancer)** — L7, understands HTTP/HTTPS, routes by host/path/header —
  the right choice for web applications/APIs, supports target groups per microservice behind one ALB.
- **NLB (Network Load Balancer)** — L4, extremely low latency/high throughput, preserves client source
  IP natively, handles millions of requests/sec — the right choice for raw TCP/UDP workloads or when ALB's
  latency overhead matters (e.g. gaming, high-frequency trading-adjacent workloads) — not needed for most web apps.
- **CLB (Classic Load Balancer)** — legacy, avoid for new work; mentioned only because it still shows up
  in older infra you might inherit.
- **Target groups + health checks** — a load balancer routes only to targets passing their configured
  health check (path, interval, thresholds) — an unhealthy target is automatically pulled from rotation,
  the AWS-managed-infra analog of a Kubernetes readiness probe pulling a pod from Service endpoints.

## Route 53 — DNS plus routing policies that matter operationally

- **Simple routing** — one record, no logic.
- **Weighted routing** — split traffic by percentage across multiple endpoints — canary releases or
  gradual migration between two backends.
- **Latency-based routing** — route to whichever region gives the lowest latency for that requester.
- **Failover routing** — primary/secondary with health checks — automatic DNS-level failover if primary
  fails its health check. **Real limitation worth knowing:** DNS failover is bounded by record **TTL** —
  clients/resolvers caching the old answer won't see the failover until their cache expires, which is
  *why* DR runbooks lower TTL in advance of a planned failover test/cutover.
- **Health checks** — Route 53 can health-check an endpoint directly and only return it in
  answers if healthy — this is what makes failover routing actually work, not just a routing policy
  label.

## CloudFront (CDN) — what it actually buys you beyond "faster"

- **Edge caching** — serves cached content from edge locations close to the requester, reducing both
  latency and **origin load** (fewer requests actually reach your backend).
- **Origin Access Control (OAC)** — lets CloudFront be the *only* path to a private S3 bucket (bucket
  stays fully private, no public access needed) — the correct pattern for "serve static assets from S3
  via CDN" instead of making the bucket itself public (referenced in `s3.md`'s scenario questions).
- **Cache invalidation** — forces CloudFront to drop cached copies and re-fetch from origin; costs money
  per invalidation past a free tier and isn't instant globally — better to version asset URLs
  (`app.v2.js`) so changes get a new cache key naturally, rather than relying on invalidation for every deploy.

## CloudWatch — the operational nervous system

- **Metrics** — numeric time-series (CPU, request count, custom app metrics via the CloudWatch agent or
  SDK `PutMetricData`).
- **Logs** — CloudWatch Logs, with **Log Insights** for querying across log groups without exporting
  data elsewhere.
- **Alarms** — threshold-based, can trigger an SNS notification, an Auto Scaling action, or a Lambda
  directly — the mechanism underneath most AWS-native alerting.
- **Composite alarms** — combine multiple alarms with AND/OR logic — reduces alert noise (e.g. only page
  if *both* error rate is high *and* it's not a known deploy window) instead of one alarm per metric
  independently paging.

## Cost management — the tools an SRE is actually expected to use, not just finance

- **Cost Explorer** — visualize/filter spend by service, tag, time range — the first stop for "why did
  the bill go up."
- **Cost allocation tags** — tag resources (`Team`, `Environment`, `Project`) so spend can actually be
  attributed — without consistent tagging, cost investigation is guesswork across a shared account.
- **Budgets** — proactive alerts when spend crosses a threshold, rather than discovering overspend only
  at month-end billing.
- **Trusted Advisor** — flags idle/underutilized resources (unattached EBS volumes, oversized instances,
  idle load balancers) — the practical tool for "where is money being wasted" beyond just watching the
  top-line bill.
- **Savings Plans / Reserved Instances** — covered in `compute_and_scaling.md`; the cost-management angle
  is right-sizing *before* committing — committing to a 1-3 year reservation on an over-provisioned
  instance size locks in waste for the full term.

---

## Interview questions (with the short answer you should be able to give cold)

1. *When would you choose an NLB over an ALB?* — When you need raw L4 (TCP/UDP) handling, extremely low
   latency, native preservation of client source IP, or very high throughput — ALB's L7 routing
   (host/path-based) isn't needed and its added processing overhead isn't worth it for that workload.
2. *Why is DNS-based failover (Route 53) not instant, even with health checks configured correctly?* —
   Bounded by the DNS record's TTL — clients/resolvers that already cached the old answer won't query
   again until their cached copy expires, so failover propagation speed is a direct function of TTL, not
   of how fast Route 53 itself detects the failure.
3. *What's Origin Access Control for, and what problem does it solve versus just making an S3 bucket
   public?* — Lets CloudFront be the only path allowed to read a private S3 bucket — keeps the bucket
   itself fully private (no public access needed at all) while still serving its content globally via
   the CDN, instead of the common anti-pattern of making the bucket public just so a CDN/frontend can read it.
4. *Why might a team avoid relying on CloudFront cache invalidation for every deploy, and use versioned
   asset filenames instead?* — Invalidation costs money past a free tier, isn't instantaneous globally,
   and doesn't scale well to frequent deploys; versioned filenames (`app.v2.js`) get a fresh cache key
   automatically on every change, achieving the same effect without needing active invalidation at all.
5. *What's a composite CloudWatch alarm for, and why would you use one instead of several independent
   alarms?* — Combines multiple conditions with AND/OR logic so you only page on a more specific,
   meaningful combination (e.g. high error rate AND not during a known deploy window) — reduces alert
   noise/false pages compared to every underlying metric alarming independently.
6. *A team's AWS bill is higher than expected and nobody can say which team/project is responsible. What's
   the root operational gap?* — Missing or inconsistent cost allocation tagging — without tags like
   `Team`/`Project` on resources, Cost Explorer can show spend by service but can't attribute it to who's
   actually responsible, making the investigation guesswork instead of a direct lookup.
7. *Why would committing to a 3-year Reserved Instance on an over-provisioned instance size be a real
   financial mistake, not just a technical one?* — It locks in the wasted capacity's cost for the entire
   commitment term — right-sizing (checking actual utilization, e.g. via Trusted Advisor/CloudWatch) needs
   to happen *before* committing, since a reservation makes correcting the oversizing much more costly to
   unwind than an on-demand instance would be.