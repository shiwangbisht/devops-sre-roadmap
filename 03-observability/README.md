# 03 — Observability: ELK, Prometheus, Grafana

Strong existing base (ELK_STACK repo has shard recovery, buffering/queue config already — non-trivial stuff). The gap is usually alert *design* (signal vs noise) rather than dashboard-building.

## Depth checklist

- [ ] Metrics vs logs vs traces — when each is the right tool, and how they connect during an actual incident
- [ ] Prometheus: scrape config, PromQL (rate/irate, histogram_quantile, aggregation), recording rules vs alerting rules, why counters reset and how `rate()` handles it
- [ ] Alertmanager: routing, grouping, inhibition, silences — designing alerts that page only on user-facing impact, not every blip
- [ ] Grafana: building a dashboard that answers "is the user affected" in one glance (the RED/USE method), not just raw metric dumps
- [ ] Elasticsearch: shard sizing, index lifecycle management, why a cluster goes yellow/red and the recovery order (you already have `elasticsearch-shard-recovery` — turn that into a checklist you could recite)
- [ ] Logstash/Filebeat: backpressure handling when the pipeline can't keep up — you already have `elk-buffering-and-queue-configuration.md`, know it well enough to explain the tradeoffs out loud
- [ ] Correlating a Kubernetes/AWS event with an ELK log spike and a Prometheus metric change during the same incident window

## Scenario projects

1. **Write 3 alerting rules with reasoning.** For a service you run, define: a symptom-based alert (user-facing, pages someone), a cause-based alert (informational, doesn't page), and one you'd deliberately *not* alert on and why.
2. **Simulate index pressure.** Fill a test ES index past a sane shard size, watch cluster health degrade, walk through your own `safe_restore.sh`/shard-recovery notes to fix it.
3. **Build one Grafana dashboard from a PromQL query you wrote yourself** (not copy-pasted) — e.g., p95 latency using `histogram_quantile`.
4. **Backpressure drill:** point Filebeat/Logstash at a deliberately slow output and observe/tune the queue behavior described in your `elk-buffering-and-queue-configuration.md`.

## Where you already have evidence

- `../ELK_STACK` — shard recovery README, buffering/queue config doc, common failure scenarios folder. This repo is already close to interview-ready; the main gap is Grafana/Prometheus alerting design, since your notes lean ELK-heavy.
- `../prometheus/dollarpe.yml` — existing Prometheus config to extend with recording/alerting rules.
