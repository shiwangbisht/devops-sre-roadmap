# Observability — metrics, logs, traces, and alerting

## Monitoring vs. observability — a real distinction, not a buzzword swap

**Monitoring** answers questions you already thought to ask in advance (a dashboard, a known alert
threshold). **Observability** is the ability to answer questions you **didn't** anticipate, by exploring
the system's actual output (high-cardinality metrics, structured logs, traces) after the fact — "why is
*this specific* customer's request slow" when you never built a dashboard for that exact question. A
system can be heavily monitored and still not observable if its telemetry can't be sliced ad hoc.

## The three pillars

- **Metrics** — numeric time-series, cheap to store, great for trends/alerting/dashboards, but
  aggregated by nature — can tell you "error rate is up" but not "which specific request failed and why."
- **Logs** — discrete, timestamped events, rich detail per occurrence, more expensive to store/query at
  volume. **Structured logging (JSON, not free text)** is the difference between logs being queryable
  data and logs being something you `grep` and hope — e.g. `{"level":"error","user_id":"123",
  "latency_ms":450}` is filterable/aggregable; `"ERROR: slow request for user 123"` isn't, not at scale.
- **Traces** — follow **one request** across every service it touches, with timing for each hop
  (spans). The only pillar that directly answers "which specific downstream call made this particular
  request slow" in a microservices architecture — metrics/logs alone can't reconstruct a
  multi-service call path for one request.

## Prometheus — the metrics model worth actually understanding

- **Pull-based** — Prometheus scrapes `/metrics` endpoints on a configured interval, rather than
  services pushing metrics to it. Simpler service-side (just expose an endpoint), and Prometheus itself
  can tell if a target is down (scrape failed) — a push model can't distinguish "service is down" from
  "service has nothing to report" as cleanly.
- **Metric types:**
  - **Counter** — only increases (requests served, errors) — use `rate()` to get a meaningful per-second
    value, a raw counter value alone is rarely useful.
  - **Gauge** — goes up or down (current memory usage, active connections).
  - **Histogram** — buckets observations (request latency) — lets you compute percentiles (p50/p95/p99)
    server-side, critical because **averages hide tail latency** — an average latency can look fine
    while p99 is terrible for a meaningful slice of real users.
- **PromQL** — `rate(http_requests_total{status="500"}[5m])` — rate of 5xx errors over a 5-minute
  window; `histogram_quantile(0.99, ...)` for p99 latency from histogram buckets.
- **Why Prometheus alone doesn't scale to very large/long-retention setups** — single-node storage by
  default; **Thanos** or **Cortex/Mimir** add long-term storage, global query view across multiple
  Prometheus instances, and horizontal scalability — worth knowing by name even without hands-on depth.

## ELK/EFK stack — the logging side

**Elasticsearch** (storage + search/indexing) + **Logstash** or **Fluentd/Fluent Bit** (collection +
parsing/enrichment) + **Kibana** (visualization/query UI). The practical operational concern at scale
isn't the stack's capability, it's **cost and retention** — indexing everything forever gets expensive
fast; real deployments define retention tiers (hot/warm/cold) and often sample or filter low-value logs
(verbose debug logs in prod) rather than keeping everything indefinitely.

## Distributed tracing — the concept beneath "Jaeger/Zipkin/X-Ray"

- **Trace** — the full journey of one request across services.
- **Span** — one unit of work within that trace (one service call, one DB query) — has a start time,
  duration, and parent span (building the call tree).
- **Context propagation** — the mechanism that makes this work at all: a trace ID generated at the
  entry point gets passed along in request headers to every downstream call, so each service's spans
  can be stitched back into one trace. **If a service doesn't propagate the trace header forward, the
  trace breaks at that hop** — a very real, common integration bug, not just a theoretical gap.

## SLI / SLO / error budgets — the quantitative framing behind "is this healthy"

(Deeper operational/incident framing lives in `08-sre-fundamentals/learning/sre_fundamentals.md` — this
is the measurement side.)
- **SLI (Service Level Indicator)** — the actual measured metric (e.g. "% of requests served in under
  300ms").
- **SLO (Service Level Objective)** — the target for that SLI (e.g. "99.9% of requests under 300ms, over
  a rolling 30 days").
- **Error budget** — `100% - SLO` — the *allowed* amount of failure (0.1% in the example above) before
  you're out of budget. The real operational value: an error budget converts "should we deploy this risky
  change" from a subjective argument into a quantitative one — if there's budget left, ship it; if it's
  exhausted, freeze risky changes and focus on reliability until it recovers.

## Alerting — what actually makes an alert good

- **Alert on symptoms, not causes** — "error rate > 1%" (a symptom users feel) rather than "CPU > 80%"
  (a cause that may or may not actually be hurting anyone) — alerting on causes produces noisy pages for
  things that never become real problems.
- **Every alert should be actionable** — if a page doesn't require a human to actually do something,
  it shouldn't be a page (maybe a dashboard, maybe nothing). Non-actionable pages are exactly what cause
  real alert fatigue — the state where people start ignoring pages because most of them are meaningless.
- **Alert fatigue is a reliability risk in itself** — a team desensitized by noisy, low-value paging
  will miss (or respond slower to) the genuinely critical one buried among them.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the actual difference between monitoring and observability?* — Monitoring answers questions
   you anticipated in advance (known dashboards/alerts); observability is the ability to answer questions
   you *didn't* anticipate, by exploring telemetry ad hoc after the fact — a heavily-dashboarded system
   can still not be observable if it can't be sliced for an unforeseen question.
2. *Why can't metrics alone tell you why one specific user's request was slow?* — Metrics are aggregated
   by nature (rates, percentiles across many requests) — they show *that* something's wrong in
   aggregate, not the specific path of one individual request; that requires a trace, which follows one
   request's actual journey across services.
3. *Why would you use `rate()` on a Prometheus counter instead of reading its raw value?* — A counter
   only ever increases (e.g. total requests since process start) — its raw value is just "how many since
   the process started," not meaningful on its own; `rate()` converts it into a meaningful per-second
   value over a time window.
4. *Why do averages hide real latency problems, and what's the fix?* — An average can look acceptable
   while a meaningful fraction of requests (the tail) are actually slow — a few very fast requests can
   offset many moderately slow ones in an average. Histograms + percentiles (p95/p99) surface the tail
   directly instead of masking it.
5. *What's context propagation in distributed tracing, and what happens if one service doesn't do it?*
   — The mechanism (trace ID passed via request headers) that lets spans from different services be
   stitched into one trace; if a service doesn't forward the trace header to its downstream calls, the
   trace breaks at that hop — everything downstream of that gap becomes untraced, a real, common
   integration bug.
6. *What does an error budget actually let a team do that an SLO alone doesn't?* — Converts "should we
   ship this risky change right now" into a quantitative decision — if budget remains, proceed; if it's
   exhausted, that's a concrete, pre-agreed signal to pause risky changes and prioritize reliability work
   instead of relying on subjective judgment calls each time.
7. *Why is "alert on CPU > 80%" often considered a worse alert than "alert on error rate > 1%"?* — CPU
   usage is a *cause* that may or may not ever translate into real user-facing impact — alerting on it
   pages people for things that often resolve themselves or never actually hurt anyone. Error rate is a
   *symptom* users actually feel — alerting on symptoms keeps pages tied to real impact.
8. *A team's on-call engineers have started silencing/ignoring a large share of pages. What's the actual
   underlying reliability risk, beyond the engineers' quality of life?* — Alert fatigue from noisy,
   non-actionable pages desensitizes the team, meaning the genuinely critical alert is more likely to be
   missed or responded to slowly when it does happen — it's a real reliability risk to the system, not
   just a team-morale issue.