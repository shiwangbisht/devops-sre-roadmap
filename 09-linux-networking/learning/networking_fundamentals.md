# Linux — networking fundamentals

The module most SRE interviews actually lean on hardest — not because it's exotic, but because it's the
layer where "the service is down" diagnosis actually starts.

## Subnetting — the math you should be able to do in your head

A CIDR block like `10.0.0.0/24` — the `/24` is how many bits are the **network** portion; the rest are
**host** bits. `/24` = 24 network bits, 8 host bits = 256 addresses (`2^8`), minus network address and
broadcast address = **254 usable hosts**.

- `/24` → 256 addresses (254 usable)
- `/25` → 128 addresses (126 usable) — splits a `/24` in half
- `/28` → 16 addresses (14 usable) — common for small subnets (e.g. a NAT gateway subnet)
- `/32` → exactly 1 address (a single host route)

**AWS-specific gotcha worth knowing cold:** AWS reserves **5** IPs per VPC subnet, not 2 — network
address, broadcast, VPC router, DNS, and future use — so a `/24` subnet in AWS gives you 251 usable, not
254.

## The TCP handshake and connection states

- **3-way handshake**: `SYN` (client) → `SYN-ACK` (server) → `ACK` (client) — connection established
  only after all three.
- **4-way close**: `FIN` → `ACK` → `FIN` → `ACK` — either side can initiate; this is *why* a connection
  can be "half-closed" (one side done sending, still receiving).
- **`TIME_WAIT`** — after closing, the side that sent the final `ACK` holds the socket in `TIME_WAIT` for
  a while (historically 2×MSL) to handle any delayed/duplicate packets. At high connection churn (lots
  of short-lived connections), a server can run out of ephemeral ports with thousands of sockets stuck
  in `TIME_WAIT` — a real, nameable production issue (`netstat -an | grep TIME_WAIT | wc -l` to check),
  fixed via connection reuse/keep-alive or tuning `net.ipv4.tcp_tw_reuse`.
- **`SYN_RECV` backlog filling up** — under a SYN flood (or just a genuinely overloaded server not
  `accept()`-ing fast enough), the kernel's half-open connection queue fills, new connections get
  dropped — this is the actual mechanism behind both DDoS impact and plain "server too slow to accept
  connections" symptoms.

## DNS resolution — the full path, not just "it's a hostname lookup"

1. Check local resolver cache (`systemd-resolved`, `nscd`, or the application's own cache).
2. Check `/etc/hosts` (static overrides, checked before any real DNS query, per `/etc/nsswitch.conf`'s
   ordering).
3. Query the configured resolver (`/etc/resolv.conf`) — usually a recursive resolver (your router, your
   cloud provider's resolver, or a public one like 8.8.8.8).
4. The recursive resolver walks the hierarchy if not cached: **root servers** → **TLD servers** (`.com`)
   → **authoritative nameservers** for the specific domain → returns the answer, which gets cached at
   each level per the record's **TTL**.
- **A record** (hostname → IPv4), **AAAA** (→ IPv6), **CNAME** (hostname → another hostname, not an IP
  directly), **MX** (mail routing), **TXT** (arbitrary text — SPF/DKIM, domain verification), **NS**
  (which servers are authoritative for this zone).
- **Why DNS caching/TTL matters operationally:** a low TTL means faster failover (e.g. during a DR
  cutover) but more query load on authoritative servers; a high TTL means stale records linger longer
  after a change — this exact tradeoff is why teams lower TTL *in advance* of a planned migration.

## Routing — how a packet actually decides where to go

Every host has a **routing table** (`ip route` / `route -n`) — for each outgoing packet, the kernel
picks the **most specific matching route** (longest prefix match), falling back to the **default
route** (`0.0.0.0/0`) if nothing more specific matches. A classic "why can't this instance reach the
internet" diagnosis is checking whether a default route even exists and points at the right gateway
(e.g. a NAT gateway for a private subnet).

## Firewalls — `iptables` mental model (even if `nftables`/cloud security groups are what you use daily)

Traffic passes through **chains** (`INPUT`, `OUTPUT`, `FORWARD` are the built-in ones) in order, each
containing **rules** evaluated top to bottom, first match wins, with a default **policy** (ACCEPT/DROP)
if nothing matches. Cloud security groups (AWS SG) are conceptually the same idea, simplified: **SGs are
stateful** (a reply to an allowed inbound request is automatically allowed back out, no explicit outbound
rule needed) while **NACLs are stateless** (you must explicitly allow both directions) — this exact
distinction is a very common AWS networking interview question.

## Systematic diagnosis order: "I can't reach this service"

1. **Can you resolve it?** `nslookup`/`dig <hostname>` — rules DNS in or out first.
2. **Can you reach the IP at all?** `ping` (ICMP — note some networks block ICMP, so a failed ping isn't
   conclusive on its own) or `traceroute`/`mtr` to see where the path breaks.
3. **Is the port actually open?** `telnet host port` or `nc -zv host port` — distinguishes "host
   unreachable" from "host reachable but nothing's listening/firewalled on this port."
4. **Capture the actual traffic** — `tcpdump -i eth0 host <ip> and port <port>` — see if packets are
   leaving, arriving, or getting a RST/no response at all; this is the "stop guessing, look at the
   wire" step.
5. **Only then** check application-layer logs — many engineers jump here first and waste time; confirm
   the network path works before assuming the bug is in application code.

---

## Interview questions (with the short answer you should be able to give cold)

1. *How many usable hosts are in a `/27` subnet, and how'd you get that?* — `/27` leaves 5 host bits →
   `2^5 = 32` addresses, minus network + broadcast = 30 usable (29 in an AWS VPC subnet, since AWS
   reserves 5, not 2).
2. *Why does AWS give you fewer usable IPs per subnet than the raw CIDR math suggests?* — AWS reserves 5
   IPs per subnet (network address, broadcast, VPC router, DNS, future use), not the standard 2 — a `/24`
   gives 251 usable in AWS, not 254.
3. *What's `TIME_WAIT`, and why can it become an operational problem?* — The state a closing connection
   sits in briefly to catch delayed/duplicate packets after close. At very high connection churn (many
   short-lived connections), a server can accumulate so many sockets in `TIME_WAIT` that it exhausts
   available ephemeral ports — fixed by connection reuse/keep-alive, not by "just waiting it out."
4. *Walk through what happens, step by step, when a host resolves a hostname it's never looked up
   before.* — Check `/etc/hosts` first, then query the configured resolver; if not cached anywhere, the
   resolver recursively queries root servers → TLD servers → the domain's authoritative nameservers,
   caching the answer at each level per the record's TTL on the way back.
5. *What's the practical operational reason to lower a DNS record's TTL before a planned migration?* —
   Lower TTL means cached records expire faster everywhere, so a cutover (changing the record to point
   at new infrastructure) propagates and takes effect faster — raising TTL afterward trades that fast-
   failover capability back for reduced query load once it's no longer needed.
6. *What's the real difference between AWS security groups and NACLs, beyond "one's at the instance
   level and one's at the subnet level"?* — Security groups are **stateful** — a reply to an allowed
   inbound connection is automatically permitted back out, no separate outbound rule needed. NACLs are
   **stateless** — you must explicitly allow both the inbound request and the outbound reply, or return
   traffic gets blocked even if the request itself was allowed in.
7. *`ping` to a host fails but the service is actually up and reachable on its port. What's the most
   likely explanation?* — ICMP is commonly blocked by firewalls/security groups independently of TCP
   traffic — a failed ping doesn't conclusively mean the host is unreachable; test the actual port
   directly (`nc -zv`) instead of relying on ping alone.
8. *Walk through your diagnosis order for "my application can't reach this downstream service."* — DNS
   resolution first, then basic reachability (ping/traceroute, caveat on ICMP), then whether the specific
   port is actually open/listening (`nc -zv`), then packet capture (`tcpdump`) if still unclear, and only
   then application-layer logs — network path confirmed working before assuming an app-level bug.