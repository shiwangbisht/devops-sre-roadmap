# Linux — diagnostic tooling, namespaces/cgroups, security

## Diagnostic tooling — what to reach for and why

- **`strace`** — traces every **system call** a process makes (file opens, reads, network calls...).
  Reach for it when a process is hanging/failing and you don't know *why* at the kernel-interaction
  level — e.g. `strace -p <pid>` on a hung process often shows it blocked on a specific `read()`/`connect()`
  call, pointing straight at a stuck file handle or an unreachable dependency.
- **`tcpdump`** — captures raw packets off an interface. The "stop guessing, look at the wire" tool —
  `tcpdump -i eth0 host 10.0.1.5 and port 443` filters to exactly the conversation you care about.
- **`ss` (modern) / `netstat` (legacy)** — show socket state: what's listening, what's connected, what's
  in `TIME_WAIT`. `ss -tulpn` (TCP+UDP, listening, show process) is the fast "what's actually bound to
  this port" check.
- **`lsof`** — "list open files," but in Linux *everything* is a file-like descriptor, so `lsof -p <pid>`
  shows a process's open files, sockets, and more. `lsof -i :8080` answers "what process is holding this
  port" directly — faster than `ss` + cross-referencing PID when you already know the port.
- **`top`/`htop`** — live resource usage; know to sort by memory (`M` in top) vs. CPU (`P`) depending on
  what you're chasing, and that **`%CPU` can exceed 100%** on multi-core systems (a process using 2 full
  cores shows `200%`).
- **`vmstat`** — system-wide CPU/memory/swap/IO at a glance; the `wa` (I/O wait) column is the one most
  people forget to check — high `wa` with low actual CPU usage means the bottleneck is disk, not compute.
- **`iostat`** — per-device disk I/O stats; `%util` near 100% on a device means that disk is the
  bottleneck, not the application.
- **`dmesg`** — kernel ring buffer — the first place to check for OOM-killer activity
  (`dmesg | grep -i "killed process"`), hardware errors, or filesystem issues the application layer
  never sees directly.

## Namespaces & cgroups — the two primitives containers are actually built from

Containers aren't a special kernel feature — they're a *combination* of two existing Linux primitives,
and understanding this is what separates "I've used Docker" from "I know what a container actually is."

- **Namespaces** — provide **isolation**: each namespace type makes a process see its own private view
  of something that's actually shared system-wide.
  - `PID` namespace — process sees its own PID 1, can't see host processes.
  - `NET` namespace — own network interfaces, routing table, ports (why two containers can both bind
    port 8080 without conflict).
  - `MNT` namespace — own filesystem mount view.
  - `UTS` — own hostname.
  - `IPC` — own inter-process communication (shared memory, semaphores).
  - `USER` — own user/group ID mapping (lets a process be "root" inside the namespace while mapped to an
    unprivileged user on the host — the mechanism behind rootless containers).
- **cgroups (control groups)** — provide **resource limiting**: CPU shares/quota, memory limits, I/O
  bandwidth, for a group of processes. This is literally the mechanism behind a Kubernetes pod's
  `resources.limits` — the kubelet configures a cgroup, the kernel enforces it.
- **Put together:** a "container" is a process started with its own namespaces (isolation) and placed
  into a cgroup (resource limits) — `docker run`/the container runtime is orchestrating `unshare()` +
  cgroup setup, not inventing a new kernel concept.

## Security fundamentals an SRE is expected to know

- **Capabilities** — root's power is actually a bundle of ~40 discrete **capabilities**
  (`CAP_NET_BIND_SERVICE` to bind ports <1024, `CAP_SYS_ADMIN`, etc.), not one monolithic "root" bit.
  Dropping all capabilities except the few a process actually needs (`capabilities.drop: ["ALL"]` in a
  Kubernetes `securityContext`) is real least-privilege, not just "don't run as root."
- **SELinux / AppArmor** — mandatory access control (MAC) layered on top of normal discretionary
  permissions (`rwx`) — even a process running as root can be confined to only the specific files/actions
  its policy allows. Know the name and purpose even if you haven't hand-written policies.
- **seccomp** — restricts which **syscalls** a process can make at all, regardless of permissions —
  the mechanism behind Kubernetes' `seccompProfile: RuntimeDefault`, blocking an entire class of kernel
  attack surface a container process shouldn't need (e.g. raw socket creation).
- **sudo vs. SUID** — `sudo` is auditable, policy-controlled (`/etc/sudoers`), per-command privilege
  elevation with logging; SUID is a blunt, always-on privilege escalation baked into a binary's
  permission bits with no audit trail — why `sudo` is preferred for anything operational.

## Performance — the "is it CPU, memory, disk, or network" triage

- **High CPU, low wait** → actually CPU-bound — check `top`/process-level CPU, look for a hot loop/busy
  process.
- **High `wa` (I/O wait) in `vmstat`** → disk-bound, not CPU-bound — check `iostat`'s `%util`, look for a
  process doing excessive/synchronous I/O.
- **High memory, swapping active** (`si`/`so` columns in `vmstat` non-zero) → memory pressure — the
  system is actively swapping, which itself causes a secondary I/O-driven slowdown; this is why "just
  add more RAM" sometimes fixes what looked like a CPU problem — the CPU was actually spent waiting on swap I/O.
- **Load average higher than CPU count, but CPU usage looks low** → processes stuck waiting (often `D`
  state, disk I/O) are counted in load average even though they're not consuming CPU — load average
  measures "runnable + uninterruptible" processes, not just CPU-busy ones, a classic point of confusion.

---

## Interview questions (with the short answer you should be able to give cold)

1. *A process appears hung — not crashing, just stuck. What's your first diagnostic tool and why?* —
   `strace -p <pid>` — shows exactly which system call it's blocked on (a stuck `read()`/`connect()`
   often points directly at the dependency or resource it's waiting on), rather than guessing from
   symptoms alone.
2. *What's the fastest way to find out which process is holding a specific port?* — `lsof -i :<port>` —
   directly maps the port to the owning process in one command, versus `ss -tulpn` plus manually
   cross-referencing the PID.
3. *`top` shows a process at 250% CPU — is that an error?* — No — on a multi-core system `%CPU` can
   exceed 100%; 250% means it's actively using roughly 2.5 cores' worth of CPU time.
4. *What are the two Linux kernel primitives containers are actually built from, and what does each do?*
   — Namespaces (isolation — each namespace type gives a process its own private view of something
   normally shared system-wide, e.g. PIDs, network interfaces) and cgroups (resource limiting — CPU/
   memory/IO quotas enforced by the kernel for a group of processes).
5. *How does a Kubernetes pod's `resources.limits.memory` actually get enforced at the OS level?* — The
   kubelet configures a **cgroup** for the container with that memory limit; the kernel enforces it
   directly — OOM-killing the container's process(es) if it's exceeded. It's not a Kubernetes-invented
   mechanism, it's the same primitive `docker run --memory` uses.
6. *What's the difference between `sudo` and a SUID binary, from a security-posture standpoint?* —
   `sudo` is policy-controlled and audited per command (`/etc/sudoers`, logged); SUID is a static,
   always-on privilege escalation baked into a binary's permission bits with no inherent audit trail —
   `sudo` is the preferred, more controllable mechanism operationally.
7. *What does `seccomp` restrict that capabilities/SELinux don't?* — The specific set of **syscalls** a
   process is allowed to make at all — a much lower-level restriction than "what files can you touch"
   (SELinux/AppArmor) or "what privileged operations can you perform" (capabilities); it shrinks the
   kernel attack surface directly.
8. *A server's load average is 8 on a 4-core machine, but `top` shows CPU usage is low. What's actually
   happening?* — Load average counts processes that are runnable **or** in uninterruptible sleep
   (usually waiting on disk I/O) — a pile of processes stuck in `D` state waiting on slow disk I/O
   inflates load average without actually consuming CPU; check `vmstat`'s `wa` column and `iostat` next,
   not more CPU profiling.
9. *A system feels slow and `vmstat` shows nonzero `si`/`so` columns. What's going on, and why might it
   look like a CPU problem at first glance?* — The system is actively swapping memory to/from disk under
   memory pressure — swapping itself is I/O-heavy and slow, so the resulting slowdown can masquerade as
   general sluggishness/high load before you check `vmstat` and realize memory, not CPU, is the real
   bottleneck.