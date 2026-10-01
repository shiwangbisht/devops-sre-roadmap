# 04 — Databases

You have a structured repo (`DataBase/`) with scripts in it, but running a backup/restore script and being able to reason about consistency, replication lag, and recovery under pressure are different skills — build that reasoning here first, then apply it back to that repo.

## Depth checklist

- [ ] Postgres: replication (streaming, logical), read replica lag and its user-facing consequences, connection pooling (PgBouncer) under high concurrency, `EXPLAIN ANALYZE` basics for a slow query
- [ ] Backup/restore: RTO vs RPO, point-in-time recovery, and — critically — when you last *tested* a restore, not just took a backup
- [ ] MongoDB/Redis/DynamoDB (from your DB repo's structure): know at least one deep failure mode for each — e.g., Redis eviction policies under memory pressure, DynamoDB hot partition throttling, Mongo replica set election behavior
- [ ] Migration strategy: how you'd migrate a live database with near-zero downtime (dual-write, CDC, cutover) — you've done infra migrations for startups, formalize that experience into a repeatable pattern
- [ ] Locking/contention: what a long-running transaction does to concurrent writers, deadlock diagnosis

## Where to learn

- [PostgreSQL docs](https://www.postgresql.org/docs/current/index.html), [Redis docs](https://redis.io/docs/latest/), [MongoDB docs](https://www.mongodb.com/docs/manual/) — official docs
- [DynamoDB — Partition key design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html) — partitioning/throttling behavior
- Per-subtopic links (Postgres, backup/restore, Mongo/Redis/DynamoDB, migration, locking) are in each subtopic's GitHub issue — see the [DevOps_learning](https://github.com/users/shiwangbisht/projects/1) board.

## Scenario projects

1. **Simulate replica lag and its blast radius.** Set up Postgres primary + replica, generate lag artificially (throttle or heavy write load), then have an app read from the lagging replica — observe the stale-read bug and describe how you'd detect it in production (metric + alert).
2. **Restore drill.** Take a real backup, actually restore it to a fresh instance, time the whole thing. If you've never timed a restore, this alone is a strong interview answer ("I test my restores, here's the RTO I measured").
3. **Slow query autopsy.** Write a deliberately bad query (missing index, N+1 pattern), use `EXPLAIN ANALYZE` to diagnose, fix it, capture before/after.
4. **Migration plan.** Write a design doc for migrating one of your real startup DBs with near-zero downtime, even if hypothetical — dual-write window, cutover trigger, rollback plan.

## Where you already have evidence

- `../DataBase` — existing structure for sql/nosql/scripts/monitoring; slot these scenario projects into the matching subfolder (e.g., restore drill under `scripts/restore/`).

## Self-test — can you answer these cold?

1. What's the actual difference between RTO and RPO, and what are yours for a real database you run?
2. A replica is lagging 30 seconds behind primary — describe one real bug this causes for an application reading from it.
3. Walk through diagnosing a slow query using `EXPLAIN ANALYZE` — what are you looking for first?
4. When would you choose logical replication over streaming replication?
5. Describe a near-zero-downtime migration plan for a live production database, including your rollback trigger.
