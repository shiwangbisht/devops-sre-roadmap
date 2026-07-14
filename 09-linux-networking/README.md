# 09 — Linux & Networking

Solid existing base (`master_linux` covers process internals). This module rounds out networking depth, which matters a lot given your SIP/telecom background — you likely already have strong intuition here that just needs structuring.

## Depth checklist

- [ ] Process internals (existing strength) — signals, zombie/orphan processes, process states, resource limits (ulimits, cgroups)
- [ ] TCP fundamentals: handshake, TIME_WAIT accumulation under high connection churn (very relevant to high-traffic SIP nodes), keepalive tuning
- [ ] DNS resolution path end-to-end, and how a misconfigured resolver shows up as an intermittent, hard-to-reproduce bug
- [ ] Common diagnostic tools: `ss`/`netstat`, `tcpdump` basics, `strace`/`lsof` for "why is this process doing that"
- [ ] Filesystem/disk: inode exhaustion vs disk space exhaustion (different symptoms, different fixes), disk I/O bottleneck diagnosis
- [ ] SIP-specific: since this is daily work, formalize it — SIP over UDP vs TCP/TLS tradeoffs, NAT traversal issues (a classic SIP pain point), how you'd diagnose one-way audio or call-setup failures at the network layer

## Where to learn

- man7.org/linux/man-pages — canonical Linux man pages online
- RFC 3261, the SIP standard: www.rfc-editor.org/rfc/rfc3261 — you troubleshoot this daily; reading the actual spec once will sharpen intuition you already have

## Scenario projects

1. **TIME_WAIT drill.** Generate a high rate of short-lived TCP connections against a test service, observe TIME_WAIT accumulation with `ss`, explain the OS-level fix (SO_REUSEADDR, tuning) vs the application-level fix (connection pooling/keepalive).
2. **DNS failure injection.** Point a test app at a broken resolver, observe the failure mode (usually looks like generic timeouts, not an obvious DNS error) — practice recognizing this pattern fast.
3. **Formalize a real SIP troubleshooting session** from work into a structured writeup (sanitized) using the postmortem template from module 08 — this is likely your single most differentiated interview story since most DevOps/SRE candidates have never touched SIP.
4. **Disk pressure drill:** fill a test filesystem's inodes (not space) with many small files, observe the distinct symptom vs a full disk, document both.

## Where you already have evidence

- `../master_linux/master_linux` — existing process-internals notes; extend with a `networking/` subfolder for the scenarios above.
- Daily SIP protocol troubleshooting at work — this is genuinely rare experience for a DevOps/SRE candidate; make sure it shows up explicitly in your resume and interview stories, not just "Kubernetes."

## Self-test — can you answer these cold?

1. A service under high connection churn shows a huge TIME_WAIT count — is that actually a problem, and what's the fix at each layer (OS vs app)?
2. Describe a DNS failure and explain why it usually looks like a generic timeout instead of an obvious DNS error.
3. Inode exhaustion vs disk space exhaustion — different `df`/`du` symptoms, different fixes. Name both.
4. One-way audio on a SIP call — walk through your diagnosis order at the network layer.
5. Why is NAT traversal specifically hard for SIP compared to plain HTTP traffic?
