# 02 — AWS Cloud

You've already touched most of this list building startup infra. The gap is usually depth on *why* a service was chosen and what breaks at scale/failure — that's what separates "I set this up" from "I'd defend this design."

## Depth checklist

Group by the services you listed, plus the reasoning layer interviewers actually probe:

- [ ] **Compute:** EC2 instance types/pricing (on-demand/spot/reserved) and when to use each; App Runner vs ECS/Fargate vs EC2 — tradeoffs, not just "App Runner is easier"
- [ ] **Networking:** VPC design (subnets, route tables, NAT vs IGW), Route53 routing policies (failover/weighted/latency), WAF rule types and what they actually block
- [ ] **Serverless/eventing:** Lambda cold starts and concurrency limits, SQS (standard vs FIFO, visibility timeout, DLQ design), SNS fan-out patterns, when SQS+Lambda beats a long-running consumer
- [ ] **Logging/observability pipeline:** your Firehose → S3 pipeline — know the failure modes (buffering, throttling, partial delivery) and how CloudWatch alerting is actually wired (metric filters, alarm actions, composite alarms)
- [ ] **Data:** RDS Postgres — failover (Multi-AZ), read replicas, connection pooling under load, backup/restore RTO/RPO
- [ ] **Identity/secrets:** Cognito user pools vs identity pools, Secrets Manager rotation, IAM least-privilege design (this comes up constantly in interviews — be ready to write a policy from scratch)
- [ ] **Cost:** be able to explain how you'd reduce cost on a service you've run (this is a very common SRE/DevOps interview question)

## Scenario projects

1. **Design doc, not deployment.** Pick one startup infra piece you built and write a 1-page design doc: why this service, what alternative you rejected and why, what the failure mode is, how you'd detect it (ties into module 08).
2. **Break the logging pipeline on purpose.** Throttle Firehose or misconfigure the S3 destination policy; diagnose from CloudWatch alone.
3. **IAM policy from scratch.** Write a least-privilege policy for a Lambda that only needs to read one S3 prefix and write to one SQS queue — no wildcards.
4. **RDS failover drill.** Force a Multi-AZ failover on a test instance, measure the actual downtime, explain what the application needs to handle (connection retry) to survive it.
5. **Cost teardown.** Take one real service you run and produce a cost breakdown + 2 concrete reduction ideas (right-sizing, reserved capacity, lifecycle policies on S3, etc.).

## Where you already have evidence

- `../AWS_VPC/AWS_VPC` — VPC peering practice, extend with route table / NAT scenarios.
- Startup infra + migrations you've already built — mine these for the design-doc exercise above instead of building new toy examples; real systems make far better interview stories than tutorials.
