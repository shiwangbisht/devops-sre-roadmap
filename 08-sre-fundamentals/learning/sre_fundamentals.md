# SRE fundamentals — the vocabulary and operating model

The conceptual layer that reframes everything else in this repo — not a new tool, a different way of
reasoning about reliability as an engineering discipline rather than an ops afterthought.

## What SRE actually is (Google's original framing, still the clearest one)

"SRE is what happens when you ask a software engineer to design an operations function." The core
idea: apply **software engineering rigor** (automation, measurement, data-driven decisions) to
operations problems, instead of operations being a separate, less rigorous discipline bolted onto
engineering. The concrete mechanism that makes this real, not just a slogan, is the error budget below.

## SLI / SLO / SLA — three distinct things, constantly conflated

- **SLI (Service Level Indicator)** — the actual *measurement* ("% of requests under 300ms").
- **SLO (Service Level Objective)** — the internal *target* for that SLI ("99.9% under 300ms, rolling
  30 days") — a goal the team holds itself to.
- **SLA (Service Level Agreement)** — an *external, often contractual* commitment to a customer, usually
  with a financial/credit penalty for missing it. **SLAs are typically looser than internal SLOs** —
  you want to breach your own SLO (internal warning) well before you'd ever breach the SLA (external,
  costly consequence) — the SLO is the early-warning system protecting the SLA.

## Error budgets — the actual decision-making mechanism

`Error budget = 100% - SLO`. If the SLO is 99.9%, the error budget is 0.1% — a genuinely *spendable*
allowance for failure, not a target you should exceed. **The practical mechanism:** error budget
remaining becomes the deciding factor for how much risk the team can take — budget available → ship
features, take deploy risk; budget exhausted → freeze risky changes, prioritize reliability work until
it recovers. This turns a political/subjective "can we deploy this risky thing" conversation into a
data-driven one both engineering and product can agree on in advance.

## Toil — the specific, named concept, not just "annoying work"

Google's specific definition: work that is **manual, repetitive, automatable, tactical (not
strategic), and scales linearly with service growth** (as opposed to growing sublinearly through good
engineering). The reason this gets a precise definition instead of just "busywork": toil is identified
specifically so it can be **measured and deliberately reduced via automation** — SRE teams often track
toil as a percentage of time and set a ceiling on it (a common real number: no more than 50% of an
SRE's time should go to toil, the rest to engineering work that actually reduces future toil).

## Incident management — the operational discipline, not just "fix it"

- **Severity levels (SEV1/2/3...)** — a predefined, shared scale for how bad an incident is, so
  response urgency/escalation is consistent instead of ad hoc per-incident judgment calls.
- **Incident Commander (IC)** — a defined role whose job is **coordinating the response**, explicitly
  *not* personally debugging the issue — keeps one person tracking status/communication/decisions while
  others focus on the actual technical fix, instead of everyone debugging in an uncoordinated pile.
- **Communication cadence** — regular, predictable status updates (even "still investigating, no new
  info") to stakeholders during an incident — the absence of updates is itself damaging to trust, even
  if the actual technical response is going fine.
- **Blameless postmortems** — the actual discipline: focus on **systemic/process causes**, not
  individual blame ("why did the system allow this mistake to cause an outage," not "who made the
  mistake"). The practical reason this isn't just a nice HR practice: a blame-driven culture makes
  people **hide/minimize** incidents and near-misses instead of surfacing them, which directly reduces
  the organization's ability to actually learn from what happened and prevent recurrence.

## Toil vs. automation — the actual tradeoff worth naming

Not all manual work should be automated immediately — automating something that's genuinely rare or
likely to change soon can cost more (building + maintaining the automation) than it saves. The real
judgment call: automate what's frequent, stable, and currently consuming real recurring time — not
reflexively automating everything regardless of actual frequency/stability.

## On-call — the operational reality, not just "carry a pager"

- **Rotation design** — predictable schedules, reasonable shift length, and secondary/backup coverage
  matter as much as the technical runbooks — on-call burnout is a real reliability risk (a tired,
  burned-out on-call engineer makes worse decisions under incident pressure).
- **Runbooks** — documented, specific response steps for known failure modes — the goal is reducing
  cognitive load during a real incident (when stress is high and clear thinking is hardest), not
  documentation for its own sake.
- **Escalation paths** — a defined, known path for "I can't resolve this alone" that doesn't depend on
  personally knowing who to call at 3am — the organizational version of a readiness probe pulling an
  unhealthy instance out of rotation before it does real damage.

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the actual difference between an SLO and an SLA, and why would a team's internal SLO be
   stricter than its external SLA?* — SLO is an internal target the team holds itself to; SLA is an
   external, often contractual commitment with real consequences for breach. Keeping the SLO stricter
   means the team gets an internal warning and time to react *before* ever risking the costlier external
   SLA breach.
2. *How does an error budget change a "should we deploy this risky change" conversation?* — It converts
   a subjective, often political argument into a data-driven one agreed on in advance — if budget
   remains, the team has pre-agreed latitude to take the risk; if it's exhausted, the pre-agreed answer
   is no, prioritize reliability instead, without re-litigating it in the moment.
3. *What specifically qualifies work as "toil" in the SRE sense, versus just being tedious?* — It must
   be manual, repetitive, automatable, tactical rather than strategic, and scale linearly with service
   growth — a precise definition specifically chosen so toil can be measured and tracked as a percentage
   of time, not just a vague complaint.
4. *Why would a team deliberately choose NOT to automate a piece of manual work, even though it's
   technically toil?* — If it's genuinely rare or likely to change soon, the cost of building and
   maintaining the automation can exceed the time it would actually save — automation should target
   frequent, stable, currently-recurring toil, not be applied reflexively to everything manual.
5. *What's an Incident Commander's actual job during an incident?* — Coordinating the response —
   tracking status, managing communication, making/recording decisions — explicitly *not* personally
   debugging the technical issue, so the response stays organized instead of everyone independently
   troubleshooting with no coordination.
6. *Why does a blameless postmortem culture actually improve reliability, beyond being a nicer way to
   treat people?* — A blame-driven culture causes people to hide or minimize incidents/near-misses out of
   fear — which directly reduces the organization's visibility into what's actually going wrong and its
   ability to prevent recurrence. Blameless postmortems surface more real information to learn from.
7. *Why might a team send a status update during an incident that just says "still investigating, no new
   information"?* — Communication cadence itself matters, independent of whether there's new technical
   information — silence during an incident damages stakeholder trust even when the technical response
   is proceeding fine; a predictable update cadence manages that trust regardless of progress.
8. *Why is on-call rotation design (schedule length, backup coverage) treated as a reliability concern,
   not just an HR/scheduling one?* — A burned-out, fatigued on-call engineer makes worse decisions under
   real incident pressure — the human factor in incident response is itself part of the system's overall
   reliability, not separate from it.