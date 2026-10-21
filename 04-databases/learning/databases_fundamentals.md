# Databases — fundamentals for an SRE

Not a DBA-depth deep dive — the operational layer an SRE is actually expected to reason about: what
breaks, what the tradeoffs are, and what to check first during a database-related incident.

## SQL vs. NoSQL — the real decision criteria, not just "structured vs. unstructured"

- **SQL (relational)** — strong consistency, enforced schema, powerful multi-table joins/transactions.
  Right choice when data relationships matter and you need strong consistency guarantees (financial
  records, anything where "approximately correct" isn't acceptable).
- **NoSQL** — trades some of that (schema flexibility, eventual consistency in many cases) for horizontal
  scalability and performance at very high write/read volumes with simpler access patterns.
  - **Document** (MongoDB) — nested, schema-flexible documents, good for varied/evolving data shapes.
  - **Key-value** (DynamoDB, Redis) — simplest model, extremely fast for exact-key lookups, poor for
    complex queries/joins.
  - **Wide-column** (Cassandra) — optimized for very high write throughput across distributed nodes.
  - **Graph** (Neo4j) — relationship-heavy queries (social graphs, recommendation engines) that would be
    painfully slow as repeated SQL joins.
- **The actual interview-worthy framing:** this isn't "NoSQL is for scale, SQL is for everything else" —
  plenty of SQL databases scale to massive volume (sharding, read replicas). The real question is
  **consistency requirements vs. access pattern shape**, not raw scale alone.

## ACID — what each letter actually guarantees

- **Atomicity** — a transaction is all-or-nothing; a failure partway through rolls back everything, not
  leaving a half-applied state.
- **Consistency** — a transaction only moves the database from one valid state to another (constraints,
  foreign keys enforced).
- **Isolation** — concurrent transactions don't see each other's uncommitted intermediate state (the
  degree of this is tunable — see isolation levels below).
- **Durability** — once committed, a transaction's effect survives a crash (written to durable storage,
  not just memory).

## Isolation levels — the tradeoff most engineers can name but not actually explain

- **Read Uncommitted** — can see other transactions' uncommitted changes (**dirty reads**) — rarely used.
- **Read Committed** — only sees committed data, but a value can change between two reads in the same
  transaction (**non-repeatable read**).
- **Repeatable Read** — same row re-read within a transaction stays consistent, but new rows matching a
  query can appear on re-query (**phantom read**).
- **Serializable** — strongest — transactions behave as if fully sequential, no anomalies, at the cost
  of the most locking/lowest concurrency.
- **The real tradeoff:** stronger isolation = more correctness guarantees = more lock contention = lower
  throughput. Most production systems default to Read Committed (PostgreSQL's default) as the practical
  middle ground, only reaching for stricter levels where the specific anomaly they prevent is a genuine risk.

## Replication

- **Primary-replica (master-slave)** — writes go to the primary, replicate to one or more read replicas.
  Read replicas scale read throughput and provide failover capacity, but replication is typically
  **asynchronous** by default — a replica can lag behind the primary, meaning a read immediately after a
  write *might* not reflect it yet (**replication lag**, a very real production gotcha: "I just wrote
  this and then read it back and it's not there" is usually a replica read racing the write).
- **Synchronous replication** — the primary waits for the replica to confirm before acknowledging the
  write — stronger consistency, but added write latency and availability risk (write blocks if the
  replica is unreachable).
- **Multi-primary (multi-master)** — more than one node accepts writes — higher write availability, but
  real conflict-resolution complexity when two primaries accept conflicting writes to the same record.

## Indexing — why it matters beyond "it makes queries faster"

An index trades **write cost** (every insert/update also updates the index) and **storage** for **read
speed** on the indexed column(s). Over-indexing a write-heavy table is a real, common mistake — every
extra index slows every write, for columns that may rarely actually get queried. The practical judgment
call: index what's actually filtered/joined on in real query patterns, not defensively indexing every
column "just in case."

## Backups — the part that's actually tested, not just configured

- **Full vs. incremental** — full backup is the complete dataset; incremental only captures changes since
  the last backup — faster/cheaper, but **restore requires replaying the full backup plus every
  incremental since**, meaning longer restore time and more failure points in the chain.
- **Point-in-time recovery (PITR)** — restore to any specific timestamp (not just a backup snapshot
  boundary), using continuous transaction log shipping on top of periodic full backups — the real
  mechanism behind "restore to 2 minutes before the bad migration ran."
- **The actual SRE discipline: untested backups are not backups.** A backup that's never been restored
  is an assumption, not a guarantee — routine restore drills are what make "we have backups" a true
  statement under pressure, not just a checkbox.

## Connection pooling — the production gotcha that isn't obvious from a laptop

Each database connection has real overhead (memory, a backend process/thread on the DB side) — an
application opening a new connection per request exhausts the database's max-connections limit under
real load, a failure mode that never shows up in local testing with one user. A **connection pool**
(PgBouncer, application-framework-level pooling) maintains a reused set of connections instead, which is
why "we scaled up the app tier and the database started refusing connections" is such a common real
incident — more app instances, each with their own pool, compounds total connections against the
database's fixed limit.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the actual decision criteria for SQL vs. NoSQL, beyond "scale"?* — Consistency requirements
   and access pattern shape — strong relational consistency and complex joins favor SQL; flexible
   schema, simple high-volume key-based access patterns, or relationship-heavy graph queries favor
   different NoSQL models. Both can scale; the choice is about data shape and guarantees, not raw volume alone.
2. *What does "Consistency" in ACID actually mean, and how is it different from the "C" in CAP
   theorem?* — ACID consistency means a transaction only moves the database between valid states
   (constraints/foreign keys hold) — a single-node correctness guarantee. CAP's consistency is about all
   nodes in a distributed system seeing the same data at the same time — a different, distributed-systems-level concept, easy to conflate in an interview.
3. *What's a non-repeatable read, and which isolation level prevents it?* — Reading the same row twice
   within one transaction and getting different values because another transaction committed a change in
   between — prevented from Repeatable Read and above, but still possible at Read Committed.
4. *Why would "I just wrote this record and immediately read it back, and it's missing" happen even
   though the write succeeded?* — The read likely hit a read replica that hadn't yet caught up to the
   primary — asynchronous replication means replicas lag behind by some (often small but nonzero) amount,
   a real and common source of this exact symptom.
5. *Why is adding an index not a free performance win?* — Every index adds overhead to every write
   (insert/update/delete) to that table, since the index itself must be updated too, plus storage cost —
   indexing columns that are rarely actually queried trades real, constant write cost for read speed that's never used.
6. *What's the actual risk with relying only on incremental backups for disaster recovery?* — Restoring
   requires replaying the full backup plus every incremental since in sequence — a longer restore time
   and more points where a corrupted/missing link in the chain breaks the whole restore, compared to a
   more recent full backup.
7. *A team says "we have backups" but has never actually restored one. Why is that a real red flag?* —
   An untested backup is an assumption, not a verified guarantee — corruption, misconfiguration, or a
   missing piece of the restore process (credentials, infra to restore into) often only surfaces during
   an actual restore attempt, which by definition hasn't happened yet.
8. *After scaling up the number of application instances, the database starts refusing new connections.
   What's the likely cause?* — Each app instance maintains its own connection pool; more instances
   multiply total simultaneous connections against the database's fixed max-connections limit — the fix
   is typically a shared external connection pooler (e.g. PgBouncer) between the app tier and the
   database, not raising the database's connection limit indefinitely.