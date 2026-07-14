# 08 — SRE Fundamentals

This is the vocabulary and reasoning framework that turns "3 years Ops support" into "SRE" on paper and in an interview room. You already do the *work* (production troubleshooting, upgrades under traffic) — this module gives you the language to talk about it the way your lead does.

## Depth checklist

- [ ] SLI/SLO/SLA — the actual difference, and how to pick a good SLI for a service (not just "uptime")
- [ ] Error budgets — what they're for (a policy for balancing reliability work vs feature work), how burn rate alerting works
- [ ] Incident management: severity levels, incident commander role, communication cadence during an incident
- [ ] Postmortems: blameless by design, timeline + root cause + contributing factors + action items — know why "human error" is never a root cause
- [ ] Toil: the SRE definition (manual, repetitive, automatable, no lasting value) and how reducing it is treated as a first-class engineering goal, not a side effect
- [ ] Capacity planning: how you'd forecast for a traffic-growth scenario (directly relevant to your telecom high-traffic experience)
- [ ] On-call sustainability: why alert fatigue matters and how symptom-based alerting (module 03) connects back to this

## Scenario projects

1. **Define an SLO for a real service you run.** Pick the SLI (e.g. request success rate, p95 latency), set a target (e.g. 99.9%), and calculate the resulting error budget in minutes/month. Explain what you'd do when the budget is nearly exhausted.
2. **Write a blameless postmortem for a real incident** you handled at work (sanitized — no company/customer specifics). Use the template below. This is the single highest-value artifact in this whole roadmap for interviews.
3. **Design an alert escalation policy** for one service: who gets paged first, what the runbook link would contain, what the fallback is if the first responder doesn't ack.

## Incident writeup template (reuse this from the root README's "one habit that matters most")

```
## Incident: <short title>
Date / Duration:
Severity:
Impact: <what broke, for whom, how many affected/how measured>

### Timeline
- HH:MM — detection (how was it noticed — alert? user report?)
- HH:MM — key diagnostic steps
- HH:MM — mitigation applied
- HH:MM — resolved

### Root cause
<the actual mechanism, not "human error">

### Contributing factors
<what made this worse or harder to catch — missing alert, unclear runbook, etc.>

### What went well
<detection speed, tooling that helped>

### Action items
- [ ] <concrete, owned, with a rough timeframe>
```

## Where you already have evidence

- Every production rollout, SIP troubleshooting session, and incident at your telecom job. This module has no code — it's the layer that makes modules 01–04 sound like SRE reasoning instead of a tool list. Do at least one real postmortem before your first interview.
