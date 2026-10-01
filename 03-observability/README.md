# 03 — Observability: ELK, Prometheus, Grafana

You have existing notes in `ELK_STACK` (shard recovery, buffering/queue config) — genuinely useful raw material, but treat the underlying concepts (metrics vs logs vs traces, PromQL, alert design) as new material to learn properly first, then go connect it back to those notes.

## Depth checklist

- [ ] Metrics vs logs vs traces — when each is the right tool, and how they connect during an actual incident
- [ ] Prometheus: scrape config, PromQL (rate/irate, histogram_quantile, aggregation), recording rules vs alerting rules, why counters reset and how `rate()` handles it
- [ ] Alertmanager: routing, grouping, inhibition, silences — designing alerts that page only on user-facing impact, not every blip
- [ ] Grafana: building a dashboard that answers "is the user affected" in one glance (the RED/USE method), not just raw metric dumps
- [ ] Elasticsearch: shard sizing, index lifecycle management, why a cluster goes yellow/red and the recovery order (you already have `elasticsearch-shard-recovery` — turn that into a checklist you could recite)
- [ ] Logstash/Filebeat: backpressure handling when the pipeline can't keep up — you already have `elk-buffering-and-queue-configuration.md`, know it well enough to explain the tradeoffs out loud
- [ ] Correlating a Kubernetes/AWS event with an ELK log spike and a Prometheus metric change during the same incident window

## Where to learn

- [Prometheus docs](https://prometheus.io/docs/introduction/overview/), [Grafana docs](https://grafana.com/docs/grafana/latest/), [Elasticsearch guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html) — official docs for each piece
- Official test/checkpoint: none as clean as CKA/AWS certs for this stack; use your own dashboards/alerts (scenario projects below) as the evidence instead.
- Per-subtopic links (Prometheus, Alertmanager, Grafana, Elasticsearch, Logstash/Filebeat) are in each subtopic's GitHub issue — see the [DevOps_learning](https://github.com/users/shiwangbisht/projects/1) board.

## Scenario projects

1. **Write 3 alerting rules with reasoning.** For a service you run, define: a symptom-based alert (user-facing, pages someone), a cause-based alert (informational, doesn't page), and one you'd deliberately *not* alert on and why.
2. **Simulate index pressure.** Fill a test ES index past a sane shard size, watch cluster health degrade, walk through your own `safe_restore.sh`/shard-recovery notes to fix it.
3. **Build one Grafana dashboard from a PromQL query you wrote yourself** (not copy-pasted) — e.g., p95 latency using `histogram_quantile`.
4. **Backpressure drill:** point Filebeat/Logstash at a deliberately slow output and observe/tune the queue behavior described in your `elk-buffering-and-queue-configuration.md`.

## Where you already have evidence

- `../ELK_STACK` — shard recovery README, buffering/queue config doc, common failure scenarios folder. This repo is already close to interview-ready; the main gap is Grafana/Prometheus alerting design, since your notes lean ELK-heavy.
- `../prometheus/dollarpe.yml` — existing Prometheus config to extend with recording/alerting rules.

## Self-test — can you answer these cold?

1. What's the difference between a Prometheus counter and a gauge, and why does that matter for `rate()`?
2. An ES cluster is yellow, not red — what does that specifically mean, and what's your recovery order?
3. Design one alert that pages someone and one that doesn't, for the same underlying failure — justify the split.
4. Your Logstash pipeline can't keep up with input volume — where does the backpressure show up first, and how do you relieve it?
5. Given a PromQL query using `histogram_quantile`, explain what it computes and why raw averages would mislead you here.
