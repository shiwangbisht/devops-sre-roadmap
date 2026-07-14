# 07 — Scripting: Python, Go, Bash

This is not a "finish it and move on" module — treat it as ongoing practice woven through every other module. Interviews test "write a script that does X" far more than trivia, and your daily Ops work already generates real automation candidates.

## Depth checklist

- [ ] Bash: solid enough to write a safe automation script (set -euo pipefail, proper quoting, error handling, idempotency)
- [ ] Python: comfortable enough to write a boto3 script hitting AWS APIs, parse/transform JSON logs, and write a basic CLI tool (argparse/click)
- [ ] Go: you've already started (`../GO/packages`) — extend toward something with real utility: a CLI tool, or a small HTTP service with health checks (ties into module 08)
- [ ] Idempotency and dry-run patterns — any script that touches production should support `--dry-run` and be safe to re-run
- [ ] Basic testing for your own scripts (even simple assertion-based tests beat none)

## Scenario projects

1. **Automate one thing you currently do manually at work** (sanitized/generic version) — e.g., a script to check pod restart counts across namespaces and flag anomalies, or one to summarize CloudWatch alarm history. This produces the strongest "tell me about a time you automated something" answer because it's real.
2. **Python + boto3:** write a script that finds and reports unused/idle resources (e.g., unattached EBS volumes, idle RDS instances) — a classic cost-reduction interview-relevant project, and directly reusable for module 02's cost exercise.
3. **Extend `../GO/packages/bank.go`** (or write a new small Go program) into a CLI with subcommands and proper error handling — demonstrates Go beyond a single file.
4. **Log parser:** given a sample log file (from your ELK setup), write a script that extracts error patterns and produces a summary — connects scripting to module 03.

## Where you already have evidence

- `../GO/packages` — existing Go practice, extend rather than restart.
- Your daily Ops/Kubernetes/SIP troubleshooting work — the best script ideas come from "what do I do by hand every week that I could automate."
