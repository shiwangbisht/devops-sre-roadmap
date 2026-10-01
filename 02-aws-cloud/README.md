# 02 — AWS Cloud

You've touched pieces of this list building startup infra, but clicking through a console and being able to defend *why* a service was chosen and what breaks at scale/failure are different skills. Build the reasoning here from scratch, then apply it back to what you've already set up.

## Depth checklist

Group by the services you listed, plus the reasoning layer interviewers actually probe:

- [ ] **Compute:** EC2 instance types/pricing (on-demand/spot/reserved) and when to use each; App Runner vs ECS/Fargate vs EC2 — tradeoffs, not just "App Runner is easier"
- [ ] **Networking:** VPC design (subnets, route tables, NAT vs IGW), Route53 routing policies (failover/weighted/latency), WAF rule types and what they actually block
- [ ] **Serverless/eventing:** Lambda cold starts and concurrency limits, SQS (standard vs FIFO, visibility timeout, DLQ design), SNS fan-out patterns, when SQS+Lambda beats a long-running consumer
- [ ] **Logging/observability pipeline:** your Firehose → S3 pipeline — know the failure modes (buffering, throttling, partial delivery) and how CloudWatch alerting is actually wired (metric filters, alarm actions, composite alarms)
- [ ] **Data:** RDS Postgres — failover (Multi-AZ), read replicas, connection pooling under load, backup/restore RTO/RPO
- [ ] **Identity/secrets:** Cognito user pools vs identity pools, Secrets Manager rotation, IAM least-privilege design (this comes up constantly in interviews — be ready to write a policy from scratch)
- [ ] **Cost:** be able to explain how you'd reduce cost on a service you've run (this is a very common SRE/DevOps interview question)

## Where to learn

- [AWS docs](https://docs.aws.amazon.com)
- [AWS Skill Builder](https://aws.amazon.com/training) — free official training
- Official test/checkpoint: [AWS Certified DevOps Engineer – Professional](https://aws.amazon.com/certification/certified-devops-engineer-professional/) or [SysOps Administrator](https://aws.amazon.com/certification/certified-sysops-admin-associate/). Curriculum doubles as a scenario-reasoning syllabus even if you don't sit the exam yet.
- Per-subtopic links (EC2, VPC, Lambda, Firehose, RDS, Cognito, cost, etc.) are in each subtopic's GitHub issue — see the [DevOps_learning](https://github.com/users/shiwangbisht/projects/1) board.

## Scenario projects

1. **Design doc, not deployment.** Pick one startup infra piece you built and write a 1-page design doc: why this service, what alternative you rejected and why, what the failure mode is, how you'd detect it (ties into module 08).
2. **Break the logging pipeline on purpose.** Throttle Firehose or misconfigure the S3 destination policy; diagnose from CloudWatch alone.
3. **IAM policy from scratch.** Write a least-privilege policy for a Lambda that only needs to read one S3 prefix and write to one SQS queue — no wildcards.
4. **RDS failover drill.** Force a Multi-AZ failover on a test instance, measure the actual downtime, explain what the application needs to handle (connection retry) to survive it.
5. **Cost teardown.** Take one real service you run and produce a cost breakdown + 2 concrete reduction ideas (right-sizing, reserved capacity, lifecycle policies on S3, etc.).

## Where you already have evidence

- `../AWS_VPC/AWS_VPC` — VPC peering practice, extend with route table / NAT scenarios.
- Startup infra + migrations you've already built — mine these for the design-doc exercise above instead of building new toy examples; real systems make far better interview stories than tutorials.

## Self-test — can you answer these cold?

1. Why would you pick App Runner over ECS/Fargate for a service, and when would that choice be wrong?
2. Walk through what happens end-to-end when your Firehose → S3 pipeline gets throttled — where does data go, and how would you know?
3. Write (out loud, no editor) a least-privilege IAM policy for a Lambda reading one S3 prefix.
4. What's the actual downtime during an RDS Multi-AZ failover, and what must the application do to survive it gracefully?
5. Give one concrete cost-reduction change for a service you run, with the tradeoff it introduces.
6. SQS visibility timeout is set too low for your processing time — what breaks, and what's the symptom in production?
