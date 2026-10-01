# 09 — Linux: Zero to Advanced

**This is Step 1 of the whole roadmap, not the last stop — do this module first, before `00`.** (The folder is still numbered `09` so links elsewhere in the repo don't break; ignore the number.)

This module assumes you know **nothing** about Linux going in, and takes you through 13 levels to the point where you can hold your own in an SRE interview on OS internals, networking, and diagnostics — ending on a capstone that uses your real SIP/telecom work as the applied case study. Each level builds on the one before it; don't skip ahead even if a level looks easy, because later levels (namespaces, performance diagnosis) assume the vocabulary from earlier ones is automatic, not looked-up.

**How to use this:** each level has a short explanation (read it), commands to actually run (do it, don't just read them), a drill (prove you can do it without the instructions in front of you), and a mini self-test. Don't move to the next level until you can pass the mini self-test cold. A full self-test bank across all levels is at the bottom for a final pass before interviews.

**Setup, before level 1:** you need a real Linux terminal, not just reading about one. Easiest paths: [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) if you're on Windows, a free-tier cloud VM (AWS EC2 t2.micro / an Oracle Cloud free VM), or a local VM (VirtualBox/UTM) running **Ubuntu**. Ubuntu specifically — it's the most common distro in DevOps jobs and has the best beginner docs.

---

## Level 1 — Orientation: what Linux actually is

**Concept.** "Linux" strictly means the *kernel* — the program that talks to hardware (CPU, memory, disk, network) and decides which process gets what, when. What you actually use day to day is a **distro** (Ubuntu, Debian, RHEL/CentOS, Alpine, Amazon Linux): the same kernel plus a package manager, default tools, and configuration conventions layered on top. That's why `apt` works on Ubuntu but not RHEL (which uses `yum`/`dnf`) even though both run the Linux kernel underneath — the kernel is the same, the distro is different.

The **shell** (usually `bash`) is just a program that reads commands you type and asks the kernel to do things. It is not the OS — it's a translator sitting on top of it. This distinction matters later: when something breaks, "is this a shell problem or a kernel/OS problem" is the first fork in your diagnosis tree.

A core Unix philosophy you'll see everywhere: **"everything is a file."** Devices, running process info, even network sockets are exposed as files you can read/write with the same basic tools. This is why `cat /proc/cpuinfo` shows you CPU info, and why redirecting output with `>` works identically whether you're writing to a regular file or a device.

**Do this.**
```bash
whoami          # who am I
uname -a        # kernel version, architecture
pwd             # where am I in the filesystem
ls -la          # what's here, including hidden files (dotfiles)
man ls          # the manual for ls — press q to quit
ls --help       # shorter, quick-reference version
history | tail  # your last few commands
```
Command anatomy: `command -flags arguments` — e.g. `ls -la /home` is command `ls`, flags `-l` (long format) and `-a` (all, incl. hidden) combined as `-la`, argument `/home` (where to run it). Tab-complete filenames instead of typing them out; use the up arrow / `Ctrl+R` to reuse past commands instead of retyping.

**Drill.** Pick three commands you've never used (e.g. `whoami`, `id`, `uptime`), read their `man` pages, and explain in your own words what each does and one flag that changes its behavior.

**Mini self-test.** What's the difference between the kernel, a distro, and the shell? Give one concrete example of "everything is a file" beyond a regular text file.

---

## Level 2 — Filesystem & files

**Concept.** Linux has one filesystem tree starting at `/` (root) — no `C:\` drive letters. Everything, including other physical disks, gets *mounted* somewhere into that one tree. Key top-level directories and what actually lives there:

| Path | What's there |
|---|---|
| `/bin`, `/usr/bin` | executable programs |
| `/etc` | system-wide configuration files |
| `/home/<user>` | your personal files |
| `/var` | data that changes at runtime — logs (`/var/log`), caches |
| `/tmp` | scratch space, often cleared on reboot |
| `/proc` | a *virtual* filesystem — live kernel/process info, not real files on disk |
| `/dev` | device files (e.g. `/dev/sda` = a disk) |
| `/opt` | optional/third-party software |

Paths are either **absolute** (start with `/`, unambiguous from anywhere — `/home/alice/notes.txt`) or **relative** (relative to your current directory — `notes.txt` or `../notes.txt`). `.` means "here," `..` means "one level up," `~` means "my home directory."

Every file has an **inode** — a metadata record (permissions, owner, size, pointers to actual data blocks) separate from the filename. A filename is just a pointer to an inode. This is *why* a hard link (`ln`) and the original file are indistinguishable — they're two names pointing at the same inode — while a symlink (`ln -s`) is a separate small file that just contains a path string. Delete the original behind a symlink and the symlink breaks ("dangling"); delete one hard link and the data survives as long as another hard link (or open file handle) still references that inode. That last fact matters a lot later (Level 9's `lsof` trick).

**Do this.**
```bash
mkdir -p project/src project/docs      # -p creates parent dirs as needed
cd project && touch src/main.py docs/notes.md
cp src/main.py src/main_backup.py
mv docs/notes.md docs/README.md
ls -li src/                            # -i shows inode numbers
ln src/main.py src/hardlink.py         # hard link — same inode as main.py
ln -s src/main.py src/symlink.py       # symlink — points at a path
cat src/main.py; less docs/README.md   # less: q to quit, / to search
head -n 5 /etc/passwd; tail -n 5 /etc/passwd
find . -name "*.py"                    # find by name
find . -type f -mtime -1               # files modified in the last day
```

**Drill.** Build the `project/` tree above, confirm with `ls -li` that `main.py` and `hardlink.py` share an inode number but `symlink.py` doesn't. Delete `main.py` and observe what happens to each of the other two.

**Mini self-test.** What breaks a symlink that wouldn't break a hard link, and why — in terms of inodes? Name three things you'd expect to find under `/var/log` vs `/etc`.

---

## Level 3 — Users, permissions, and the security model

**Concept.** Linux is multi-user by design. Every user has a UID (user ID) and belongs to one or more groups (GID). `root` (UID 0) can do anything; everyone else is constrained by permissions. User/group definitions live in `/etc/passwd` and `/etc/group`; password hashes live in `/etc/shadow` (root-readable only, for obvious reasons).

Every file has three permission sets — **owner, group, other** — each with **read (r), write (w), execute (x)**. `ls -l` shows this as `rwxr-xr--`: owner can read/write/execute, group can read/execute, everyone else can only read. Each triplet also has a numeric (octal) value: r=4, w=2, x=1, summed per set — so `rwxr-xr--` is `754`. `chmod 750 file` sets owner=rwx, group=rx, other=nothing. This octal math is asked in interviews constantly — be able to do it without a calculator.

Three special bits worth knowing: **setuid** (a program runs as its *owner's* UID, not the caller's — how `passwd` lets a regular user update `/etc/shadow` safely), **setgid** on a directory (new files inside inherit the directory's group — useful for shared team directories), and the **sticky bit** on a directory (only a file's owner can delete it, even if others have write access — this is why `/tmp` is shared but you can't delete someone else's file in it).

`umask` controls the *default* permissions new files get (it subtracts from the max). `sudo` runs one command as another user (usually root) with logging and without sharing the root password; `su` switches your whole session to another user. Prefer `sudo` — least privilege, auditable, and you don't sit in a root shell longer than you need to.

**Do this.**
```bash
id                              # your UID, GID, and groups
cat /etc/passwd | head -3       # user:x:uid:gid:comment:home:shell
ls -l /etc/shadow               # note: unreadable as a normal user
chmod 750 somefile              # owner rwx, group r-x, other none
chmod g+s shared_dir/           # setgid — new files inherit the group
umask                           # see your current default
sudo whoami                     # runs as root, logged, password-gated
```

**Drill.** Create a directory, `chmod g+s` it, add a second user (or simulate with a group change) to its group, and confirm a file created inside inherits the group instead of the creator's default group. Compute the octal value for `rwxr-x---` by hand before checking with `stat -c '%a' file`.

**Mini self-test.** Convert `640` to symbolic (`rw-...`) and explain what each user class can do. Why does `/tmp` need the sticky bit specifically, and what would go wrong without it?

---

## Level 4 — Processes & job control

**Concept.** A running program is a **process**, identified by a PID (process ID), with a parent process (PPID) that spawned it. Linux creates new processes via `fork` (clone the calling process) and usually `exec` (replace that clone's memory with a new program) — this fork→exec pair is *how every process on the system comes to exist*, including your shell spawning `ls`.

A process moves through **states**: running, sleeping (waiting on I/O), stopped, and — the one that trips people up — **zombie**. A zombie is a process that has *finished* but whose exit status hasn't been collected by its parent yet; it's not "stuck," it's waiting to be reaped. If the parent dies first, the child becomes an **orphan** and gets re-parented to `init`/`systemd` (PID 1), which reaps it.

**Signals** are how you talk to a running process: `SIGTERM` (15, "please exit gracefully, cleanup allowed") vs `SIGKILL` (9, "die immediately, no cleanup, cannot be caught or ignored") is the distinction interviewers probe most — always try `SIGTERM` first, `SIGKILL` only when a process won't die. `SIGHUP` traditionally meant "the terminal hung up" and got repurposed by many daemons to mean "reload your config." A process can intercept most signals with a `trap` — except `SIGKILL` and `SIGSTOP`, which the kernel enforces unconditionally.

`&` backgrounds a job, `jobs` lists your shell's background jobs, `fg`/`bg` move them, `nohup command &` keeps a command running after you log out (immune to `SIGHUP`), `disown` detaches a job from the shell's job table entirely.

**systemd** is the modern init system (PID 1) on most distros — it starts services at boot, tracks dependencies between them, and restarts ones that crash if configured to. `systemctl status/start/stop/restart/enable <service>` manages a unit; `journalctl -u <service>` shows its logs. The boot sequence, roughly: firmware (BIOS/UEFI) → bootloader (GRUB) → kernel loads → kernel starts PID 1 (systemd) → systemd brings up targets/units in dependency order (mount filesystems, start networking, start services) until it reaches the default target (e.g. multi-user, graphical).

**Do this.**
```bash
ps aux | head              # every process, human-readable
ps aux --forest             # as a tree
pstree                      # cleaner tree view
top                         # live view — q to quit (htop if installed: nicer)
sleep 300 &                 # background a job
jobs; fg                    # bring it back to foreground, Ctrl+C to kill
kill -l                     # list all signal names/numbers
kill -TERM <pid>            # graceful
kill -KILL <pid>            # force
systemctl status ssh        # inspect a real service
journalctl -u ssh -n 20     # its last 20 log lines
```

**Drill.** Write a tiny script that traps `SIGTERM` and prints a message instead of exiting; run it, send `SIGTERM`, watch it survive, then `SIGKILL` it and watch it die immediately. Separately, write a script that forks a child and exits before the child does — find the resulting orphan/zombie with `ps aux | grep Z` (may need to engineer the timing).

**Mini self-test.** Why can't you `trap` `SIGKILL`? What's the actual difference between a zombie and an orphan process — which one is "a problem" and which one usually resolves itself?

---

## Level 5 — Shell fluency & the text-processing toolkit

**Concept.** Every process has three standard I/O streams: **stdin** (0, input), **stdout** (1, normal output), **stderr** (2, errors) — they're separate so you can redirect them independently. `>` overwrites stdout to a file, `>>` appends, `2>` redirects stderr, `&>` redirects both, `2>&1` means "send stderr wherever stdout is currently going" (order matters). A **pipe** (`|`) connects one command's stdout directly to the next command's stdin — this is the core of Unix composability: small tools, combined, instead of one tool doing everything.

Environment variables (`export VAR=value`) are inherited by child processes; plain shell variables (`VAR=value`, no export) are not. `PATH` is the environment variable that tells the shell where to look for commands — this is why `./script.sh` needs the `./` (current dir usually isn't on `PATH`) but `ls` doesn't. `.bashrc` runs for interactive non-login shells, `.bash_profile`/`.profile` for login shells — the practical upshot is "if my alias/export isn't showing up, I probably put it in the wrong one."

The essential text toolkit, because production troubleshooting is 80% "extract the one line I care about from a huge file":
- `grep` — find lines matching a pattern (`-i` case-insensitive, `-v` invert/exclude, `-E` extended regex, `-r` recursive, `-c` count)
- `sed` — stream-edit, most commonly find/replace: `sed 's/old/new/g' file`
- `awk` — column-oriented processing: `awk '{print $1, $3}'` prints columns 1 and 3
- `cut`, `sort`, `uniq -c` (count duplicates), `tr` (translate/delete characters), `wc -l` (count lines)
- `xargs` — take stdin lines and feed them as arguments to another command (`find . -name "*.log" | xargs rm`)

**Do this.**
```bash
echo "hello" > out.txt; echo "world" >> out.txt
ls nonexistent 2> err.txt; cat err.txt
grep -i "error" /var/log/syslog | tail -20
cat /var/log/auth.log 2>/dev/null | awk '{print $1,$2,$3}' | sort | uniq -c | sort -rn | head -5
export MY_VAR="test"; bash -c 'echo $MY_VAR'    # visible — it's exported
echo $PATH | tr ':' '\n'                         # see PATH entries, one per line
find . -name "*.tmp" | xargs rm -f
```

**Drill.** Given a log file with lines like `2024-01-01 10:23:01 192.168.1.5 GET /api/users 200`, write a single pipeline that prints the top 5 most frequent IP addresses. (This is a genuinely common interview live-coding question.)

**Mini self-test.** What's the practical difference between `2>&1 >file` and `>file 2>&1`? Why does an exported variable show up in a subshell but a non-exported one doesn't?

---

## Level 6 — Package management

**Concept.** A package manager installs software plus its dependencies, tracks versions, and lets you cleanly remove it later — the alternative (manually downloading and compiling everything) is how systems rot. Two major families you'll meet in DevOps work: **Debian-based** (Ubuntu, Debian) uses `apt` (high-level) over `dpkg` (low-level, one `.deb` at a time); **RHEL-based** (RHEL, CentOS, Amazon Linux, Rocky) uses `dnf`/`yum` over `rpm`. Alpine (common in minimal Docker images) uses `apk`. Same job, different tools — know the mapping conceptually rather than memorizing every flag in every family.

**Do this.**
```bash
sudo apt update                     # refresh package index (Debian/Ubuntu)
sudo apt install -y curl            # install
apt list --installed | grep curl    # confirm
dpkg -L curl | head                 # what files did this package put where
sudo apt remove curl                # remove
sudo apt autoremove                 # clean up now-unneeded dependencies
```

**Drill.** Install a package you've never used (e.g. `tree` or `jq`), find its files with `dpkg -L`/`rpm -ql`, use it once, then remove it cleanly and confirm it's gone.

**Mini self-test.** What's the difference between `apt` and `dpkg` — why does `apt` exist when `dpkg` already installs packages?

---

## Level 7 — Storage & filesystems

**Concept.** A physical disk gets divided into **partitions**, and each partition is formatted with a **filesystem** (ext4 and xfs are the common Linux ones) — the format that actually organizes bytes into files/directories on disk. A filesystem gets **mounted** onto a path in the tree (e.g. a second disk mounted at `/data`) before you can use it; `/etc/fstab` defines what mounts automatically at boot.

Two commands that look similar but answer different questions: `df -h` shows **disk space** used/free per mounted filesystem; `du -sh <dir>` shows how much space a specific directory actually uses (walks the tree, sums file sizes). A classic gotcha: `df` can show a filesystem as full while `du` on visible files doesn't add up — usually because a large file was deleted but a process still has it open (its space isn't freed until the file handle closes; see Level 9's `lsof`).

**Inode exhaustion** is a distinct failure mode from disk space exhaustion: a filesystem has a *fixed number of inodes* set at format time, and every file — no matter how small — consumes one. You can hit "no space left on device" with `df` showing plenty of free bytes, because you're actually out of inodes (classic cause: millions of tiny cache/session files). `df -i` shows inode usage separately from `df -h`'s byte usage — different command, different fix (delete files to free inodes; you can't "resize" inodes on a live ext4 filesystem the way you can add disk space).

**LVM** (Logical Volume Manager) adds a flexible layer between raw partitions and filesystems — Physical Volumes (raw disks/partitions) grouped into Volume Groups, sliced into Logical Volumes that filesystems sit on. The payoff: you can resize an LV (and its filesystem) without repartitioning, which is why most production Linux boxes use it instead of raw partitions.

**Do this.**
```bash
df -h                     # space usage per mounted filesystem
df -i                     # inode usage per mounted filesystem
du -sh /var/log/*         # what's actually eating space, by directory
mount | column -t         # what's mounted where, with what filesystem
cat /etc/fstab            # what mounts automatically at boot
iostat -x 1 5             # disk I/O stats, 1-second interval, 5 samples
```

**Drill (the inode-exhaustion scenario).** In a scratch/test directory (or a disposable VM — don't do this on a real system), write a loop that creates hundreds of thousands of empty small files until you can no longer create new ones. Run `df -h` (shows plenty of space free) alongside `df -i` (shows inodes exhausted) side by side and document the distinct symptom. Then clean up and, separately, fill actual disk space with one huge file and compare what `df -h` shows this time.

**Mini self-test.** A server reports "No space left on device" but `df -h` shows 40% free. What do you check next, and why might that be true?

---

## Level 8 — Networking fundamentals

**Concept.** Networking is usually explained top-down (OSI's 7 layers); practically, think bottom-up in terms of what tool operates where: physical/link (cables, MAC addresses, switches) → **IP** (Layer 3: addressing, routing — "which network is this on, how do packets get there") → **TCP/UDP** (Layer 4: "which specific application on that host") → **HTTP/DNS/SIP/etc.** (Layer 7: the actual application protocol). When something's broken, asking "which layer is this" is the fastest way to narrow the search.

**IP addressing & subnetting.** An IPv4 address (`192.168.1.10`) paired with a **CIDR** suffix (`/24`) tells you how many bits are network vs host — `/24` means the first 24 bits are fixed (the network), leaving 8 bits (256 addresses, 254 usable — first is network address, last is broadcast) for hosts. Practice the math directly: given `10.0.0.0/22`, that's a 22-bit network, 10 bits of host space = 1024 addresses, 1022 usable, broadcast is `10.0.3.255`. You should be able to do this on paper, not just recite it — it comes up constantly in both interviews and real VPC design (module 02).

**Ports & sockets.** A port is a 16-bit number identifying *which application* on a host a connection is for (80/443 for HTTP/HTTPS, 22 for SSH, 53 for DNS, 5060 for SIP). A **socket** is the tuple (protocol, local IP, local port, remote IP, remote port) that uniquely identifies one connection — this is why a server can handle thousands of simultaneous clients all hitting port 443: each client's remote IP/port makes its socket unique even though the server-side port never changes.

**DNS**, end to end: your app calls `getaddrinfo()` → asks the configured **resolver** (`/etc/resolv.conf`, often your router or a public resolver like 8.8.8.8) → if not cached, the resolver asks a **root** server → which delegates to the right **TLD** server (`.com`, etc.) → which delegates to the domain's **authoritative** server → which returns the actual record. Record types: `A` (hostname→IPv4), `AAAA` (→IPv6), `CNAME` (alias to another hostname), `MX` (mail server), `TXT` (arbitrary text — SPF/verification), `NS` (which servers are authoritative). The reason a broken resolver is such an insidious bug: the *symptom* is almost always a generic connection timeout deep in your app, not an obvious "DNS failed" error — because the app just never gets an IP to connect to and hangs waiting, and nothing logs "hey, it's DNS."

**TCP connection lifecycle.** The three-way handshake: client sends `SYN` → server replies `SYN-ACK` → client replies `ACK`, connection established. Closing is a 4-step teardown, and the side that closes first ends up in **TIME_WAIT** for a cooldown period (default often 60s+) to make sure no stray late packets from the old connection get misdelivered to a new one reusing the same port. Under a high rate of short-lived connections (very relevant to high-traffic SIP signaling), TIME_WAIT sockets can accumulate faster than they clear, eventually exhausting available local ports. Fixes exist at two layers and you should know both: **OS-level** (`SO_REUSEADDR`, tuning `net.ipv4.tcp_tw_reuse`, widening the ephemeral port range) and **application-level** (connection pooling/keepalive so you're not opening a fresh TCP connection per request in the first place — usually the better fix). **Keepalive** is a separate mechanism: periodic probes on an idle connection to detect a dead peer before the application layer would notice.

**HTTP/HTTPS on the wire, briefly:** DNS resolves the hostname → TCP handshake to the resolved IP:port → for HTTPS, a TLS handshake negotiates encryption and the server presents a certificate the client validates against a trusted chain → the HTTP request/response is sent over that now-encrypted connection. Most "SSL error" tickets are actually one of: expired cert, hostname doesn't match the cert (SAN mismatch), or an incomplete certificate chain — know these three before reaching for anything more exotic.

**Do this.**
```bash
ip addr                          # your interfaces and IPs (or `ifconfig`)
ip route                         # your routing table — where packets go by default
dig example.com                  # full DNS query/response, all the detail
dig +short example.com A         # just the A record
cat /etc/resolv.conf             # your configured resolver(s)
cat /etc/hosts                   # local static hostname overrides, checked before DNS
ss -tan | grep TIME_WAIT | wc -l # count current TIME_WAIT sockets
```

**Drill 1 — subnetting on paper.** Given `172.16.4.0/22`, work out (no calculator/tool) the usable host range, the broadcast address, and how you'd split it into 4 equal `/24` subnets. Check your work with a subnet calculator only after.

**Drill 2 — TIME_WAIT.** Write a small script/loop that opens and immediately closes many short-lived TCP connections against a local test server (e.g. `nc` or a tiny Python HTTP server), then watch `ss -tan state time-wait` accumulate in real time. Explain the OS-level fix and the app-level fix out loud.

**Drill 3 — DNS failure injection.** Point a test app or `curl` at a resolver you've deliberately broken (e.g. an unreachable IP in `/etc/resolv.conf` via a container, not your real machine) and observe that the failure looks like a generic timeout, not an obvious DNS error.

**Mini self-test.** Given `10.0.0.0/22`, what's the broadcast address and how many usable hosts? Walk through DNS resolution start to finish. Is a huge TIME_WAIT count automatically a problem — what determines whether it actually is?

---

## Level 9 — Diagnostic tooling: "why is this process/connection doing that"

**Concept.** Everything above gives you the vocabulary; this level gives you the tools to actually *find* what's wrong on a live system, which is most of what an SRE does day to day.

- **`ss`** (modern) / **`netstat`** (older, still everywhere) — what's listening on which port, what connections are established, in what state.
- **`tcpdump`** — capture raw packets on an interface and filter them (`tcpdump -i eth0 port 53` to watch DNS traffic go by). This is ground truth when you don't trust what the application layer is telling you.
- **`strace`** — trace the actual system calls a process makes (file opens, network calls, everything) — invaluable for "why is this process hanging" when logs tell you nothing. `ltrace` is the equivalent for library calls.
- **`lsof`** — list open files (remember: sockets and devices count as files too) held by a process. Classic use: `lsof +L1` finds files that were deleted but are still open (explains the `df`/`du` mismatch from Level 7), and `lsof -i :443` shows what's using a given port.

A systematic diagnosis order for "service A can't reach service B" (memorize this shape, not the exact wording): is B's process even running (`ps`/`systemctl status`)? Is it listening on the expected port (`ss -tlnp`)? Can you resolve B's hostname (`dig`)? Can you reach B's IP/port at all (`nc -zv host port` or `curl`)? If a connection is refused vs times out vs hangs, that's diagnostic — refused means something's listening but rejecting (wrong port, or a firewall actively rejecting), a hang usually means a firewall silently dropping packets or a routing problem.

**Do this.**
```bash
ss -tlnp                          # what's listening, and which process (needs sudo for full detail)
sudo tcpdump -i any port 80 -c 20 # capture 20 packets on port 80, any interface
strace -f -e trace=network curl -s example.com > /dev/null   # watch curl's network syscalls
lsof -i :22                       # what's using port 22
lsof +L1                          # files deleted but still held open by a process
nc -zv example.com 443            # quick "is this port reachable" check
```

**Drill.** Start a process that opens a file, then delete that file from another terminal while the process still holds it — confirm with `lsof +L1` that the space isn't freed (`df` still shows it used) until the process exits or closes the handle. Separately, use `strace` on a `curl` to a nonexistent domain and identify exactly where in the syscall trace it fails (DNS resolution, not the HTTP request).

**Mini self-test.** Walk through your diagnosis order, in words, for "my app can't connect to the database." What's the difference between a connection being *refused* and *timing out*, diagnostically?

---

## Level 10 — Advanced: namespaces, cgroups, and what a container actually is

**Concept.** This is the level that connects everything above to Kubernetes/Docker (module 01), so don't skip it even if containers feel like a "later" topic. A container is not a lightweight VM — it's a regular Linux process with restricted *visibility* and *resources*, using two kernel features:

- **Namespaces** control what a process can *see*: a PID namespace makes a process think it's PID 1 with no visibility into other processes on the host; a network namespace gives it its own private network interfaces/routing table; mount namespaces give it its own filesystem view; UTS namespace gives it its own hostname; user namespaces can remap UIDs. `docker run` (or a Kubernetes pod) is, underneath, a process launched into a fresh set of these namespaces.
- **cgroups** (control groups) control what a process can *use*: CPU shares/quota, memory limits, I/O bandwidth, all enforced by the kernel — this is how a container gets a "512MB memory limit" and gets OOM-killed by the kernel itself, not by Docker, when it exceeds it.

`ulimit` is the older, per-process/per-user resource limit mechanism (max open files, max processes) — narrower than cgroups, but still relevant (a common production bug: hitting `ulimit -n`, max open file descriptors, under high connection load).

**Do this.**
```bash
ulimit -a                                   # your current resource limits
unshare --pid --fork --mount-proc bash      # spawn a shell in a new PID namespace
ps aux                                      # inside it — notice how little you can see
exit
cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /proc/cgroups   # cgroup info (path varies by cgroup v1/v2)
```

**Drill.** Use `unshare` to put a shell in a new PID namespace and confirm `ps aux` inside it shows almost nothing compared to outside. If you have Docker available, run `docker run -m 50m --rm alpine sh -c 'while true; do :; done'`-style memory-pressure test and watch it get OOM-killed at the limit — then explain, using this level's vocabulary, what actually killed it (the kernel's OOM killer, enforcing the cgroup memory limit).

**Mini self-test.** In one sentence each: what does a namespace restrict, and what does a cgroup restrict? When a container hits its memory limit, what specifically kills it?

---

## Level 11 — Advanced networking & security

**Concept.** A **firewall** decides what traffic is allowed in/out at the packet level — `iptables` (older, still dominant) or `nftables` (newer replacement) define ordered rule chains; the safe default posture is **default-deny**: block everything, then explicitly allow only what's needed (SSH, your app's port), rather than default-allow with exceptions.

**NAT** (Network Address Translation) lets many private-IP hosts share one public IP by rewriting source addresses/ports on the way out and remembering the mapping for return traffic. This is *specifically* painful for **SIP**: SIP embeds IP addresses and ports inside its own message body (not just the outer IP packet), so a NAT device rewriting the outer packet doesn't fix the addresses SIP itself is telling the other side to use — the remote end tries to send media (RTP) to a private IP it can't reach, which is a textbook cause of one-way or no audio. Fixes include STUN/TURN, ALGs (application-layer gateways aware of SIP), or SIP-aware NAT traversal in the softswitch/SBC itself. This is worth understanding cold — most DevOps candidates have never touched it, and you troubleshoot it for real.

**SSH hardening**, the version that comes up in interviews: key-based auth instead of passwords, disable root login (`PermitRootLogin no`), disable password auth entirely once keys work (`PasswordAuthentication no`), and use a bastion/jump host (`ProxyJump`) rather than exposing every box to the internet directly.

**TLS**, at the level you need: a certificate binds a public key to a hostname, signed by a Certificate Authority the client already trusts (forming a chain up to a trusted root); the three failure modes that cover most real incidents are an **expired** cert, a **hostname mismatch** (cert doesn't cover the name being requested), and an **incomplete chain** (server didn't send the intermediate cert, so the client can't build trust up to a root it has).

SELinux (RHEL family) / AppArmor (Debian/Ubuntu) add mandatory access control on top of normal permissions — worth knowing they exist and that "permission denied even though `ls -l` looks fine" is a classic symptom of one of these being active, even if you don't go deep on policy authoring yet.

**Do this.**
```bash
sudo iptables -L -n -v                       # current rules (or nft list ruleset for nftables)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -j DROP               # default-deny after explicit allows
ssh-keygen -t ed25519 -C "you@example.com"   # generate a key pair
ssh-copy-id user@host                        # install your public key on a remote host
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null | openssl x509 -noout -dates -subject  # inspect a live cert
```

**Drill.** On a disposable test VM, write an iptables/nftables rule set that default-denies inbound traffic except SSH and one app port, and confirm with a scan/connection attempt from another host that everything else is blocked. Separately, generate an SSH key pair, install it on a test host, then disable password auth and confirm you can still log in with only the key.

**Mini self-test.** Explain, specifically, why NAT breaks SIP in a way it doesn't break plain HTTP. Name the three most common real-world causes of a "TLS/SSL error."

---

## Level 12 — Performance & troubleshooting playbooks

**Concept.** Bringing everything together into the checklist you actually run during an incident:

- **Load average** (`uptime`'s three numbers) is the average number of processes *runnable or waiting on I/O* over 1/5/15 minutes — it is not CPU percentage. A load average of 8 on a 4-core box means real contention; the same number on a 16-core box might be fine. Always read load average next to core count.
- **Memory** (`free -h`): the number that confuses everyone is "free" vs "available." Linux aggressively uses spare RAM for disk cache (`buff/cache`) because unused RAM is wasted RAM — that cache is reclaimed instantly under pressure, so "available" (free + reclaimable cache) is the number that tells you if you're actually low on memory, not "free." When a process demands more than is truly available, the kernel's **OOM killer** picks a victim (usually the largest/least-favored process) and kills it outright.
- **Disk I/O**: `iostat -x` shows `%util` (how busy the device is) and `await` (average wait time per I/O) — high `%util` with high `await` means the disk itself is the bottleneck, not the application.
- **Network**: from Level 8/9 — connection states, retransmits, TIME_WAIT counts.

A structured incident-diagnosis order that ties the whole module together: `uptime` (load) → `top`/`htop` (which process, CPU vs memory) → `free -h` (memory pressure, real or not) → `df -h && df -i` (space/inodes) → `ss -tan` (connection state) → `tcpdump`/`strace`/`lsof` if the above didn't localize it → logs (`journalctl`, `/var/log`) for the "why," once you know the "where."

**Do this.**
```bash
uptime                    # load average — read against `nproc` (core count)
nproc                     # how many cores you actually have
free -h                   # memory — read "available," not "free"
vmstat 1 5                # CPU/memory/IO summary, sampled
iostat -x 1 5             # per-device I/O stats
```

**Drill.** On a test box, generate synthetic load (a CPU-spin loop, a memory hog, and a disk-heavy `dd` write in parallel) and walk the full diagnosis order above out loud, narrating what each command told you and why you moved to the next one — this is exactly what a live-debugging interview looks like.

**Mini self-test.** A box shows load average 12 on 4 cores but `top` shows low CPU usage — what's your next hypothesis, and which command checks it? `free -h` shows 200MB "free" — is that box actually low on memory? How do you know?

---

## Level 13 — Applied capstone: SIP & telecom networking

This is where your real day job becomes your strongest interview material — most DevOps/SRE candidates have never touched SIP, and you troubleshoot it in production. Now that you have the OS/networking vocabulary from Levels 1–12, formalize what you already do by instinct into something you can explain precisely.

- **SIP over UDP vs TCP/TLS**: UDP is lighter and traditional for SIP signaling but has no delivery guarantee or congestion control (SIP has its own retransmission logic to compensate); TCP/TLS trades some overhead for reliable delivery and, with TLS, confidentiality — increasingly the default for anything crossing an untrusted network.
- **NAT traversal** (tie back to Level 11): why SIP embeds addressing info in its payload, and the practical fixes (STUN/TURN, SBC-based NAT handling).
- **Diagnosing one-way or no audio**: SIP signaling succeeding but RTP media failing is the single most common SIP production issue — walk the network layer systematically: did the SDP negotiate the right IP/ports, is that IP actually reachable from the other side (often a NAT problem), is a firewall blocking the RTP port range, is there packet loss/jitter on the path.
- **Call-setup failures**: work through SIP response codes methodically (4xx client error, 5xx server error, 6xx global failure) the same way you'd triage HTTP status codes.

**Reading.** [RFC 3261](https://www.rfc-editor.org/rfc/rfc3261) — the SIP standard itself. You troubleshoot this daily; reading the actual spec once will sharpen intuition you already have from the job into something you can articulate precisely.

**Capstone project.** Formalize a real SIP troubleshooting session from work into a structured, sanitized postmortem using the template in [08-sre-fundamentals](../08-sre-fundamentals/README.md) — no company/customer specifics. This single writeup is likely your most differentiated interview artifact in the entire roadmap.

---

## Full scenario project list (consolidated)

1. **Inode exhaustion drill** (Level 7) — fill a test filesystem's inodes with many small files, observe the distinct symptom vs a full disk via `df -h` vs `df -i`, document both.
2. **TIME_WAIT drill** (Level 8) — generate high-churn short-lived TCP connections, observe accumulation with `ss`, explain the OS-level fix vs the app-level fix.
3. **DNS failure injection** (Level 8) — point a test app at a broken resolver, observe the generic-timeout failure mode.
4. **Deleted-but-open file mystery** (Level 9) — delete a file a running process still holds open, show the `df`/`du` mismatch, resolve it with `lsof +L1`.
5. **Namespace/cgroup drill** (Level 10) — `unshare` into a new PID namespace; separately, OOM-kill a process via a cgroup memory limit and explain the mechanism.
6. **Default-deny firewall** (Level 11) — write an iptables/nftables rule set that blocks everything except SSH and one app port; verify from another host.
7. **Full diagnosis-order drill** (Level 12) — generate synthetic CPU/memory/disk load simultaneously, narrate the full diagnosis checklist live.
8. **SIP postmortem** (Level 13) — sanitized, structured writeup of a real production SIP incident.

## Self-test bank — full pass before an interview

1. Kernel vs distro vs shell — define each with one example.
2. What breaks a symlink that wouldn't break a hard link, in terms of inodes?
3. Convert `640` to symbolic permissions and explain each class's access. Why does `/tmp` need the sticky bit?
4. Why can't `SIGKILL` be trapped? Zombie vs orphan — which is "a problem"?
5. Difference between `2>&1 >file` and `>file 2>&1`, and why order matters.
6. What's the difference between `apt` and `dpkg`?
7. `df -h` shows free space but you get "No space left on device" — what do you check, and why?
8. Given `10.0.0.0/22`: usable host range and broadcast address, by hand.
9. Walk through DNS resolution end to end. Why does a bad resolver usually look like a generic timeout?
10. Is a large TIME_WAIT count automatically a problem? What's the fix at the OS layer vs the app layer?
11. Walk your diagnosis order for "app can't reach the database," and explain refused vs timed-out connections diagnostically.
12. What does a namespace restrict vs what a cgroup restricts? What actually kills a container that exceeds its memory limit?
13. Why does NAT specifically break SIP in a way it doesn't break plain HTTP?
14. Name the three most common causes of a real-world TLS/SSL error.
15. Load average is 12 on a 4-core box but CPU usage looks low in `top` — what's your next move?
16. `free -h` shows little "free" memory — is the box actually under memory pressure? How do you know for sure?
17. One-way audio on a SIP call — walk through your diagnosis order at the network layer.
18. Describe a real SIP troubleshooting session from work using at least 5 terms from this module, precisely — could a lead follow it without translation?

## Where to go deeper (reference, not primary teaching material)

- [man7.org — Linux man pages](https://man7.org/linux/man-pages/) — canonical reference for every command/syscall above
- [Linux Journey](https://linuxjourney.com/) — free, beginner-friendly, good for Levels 1–6 if you want a second explanation of something
- [*The Linux Command Line* by William Shotts](https://linuxcommand.org/tlcl.php) — free PDF, excellent for Levels 2, 5, 6
- [Julia Evans' zines](https://wizardzines.com/zines/) — short, excellent, very approachable for strace/tcpdump/networking topics (some free, some paid)
- [RFC 3261 — SIP](https://www.rfc-editor.org/rfc/rfc3261)
- Per-subtopic links (one per level, where useful) are also attached to each subtopic's GitHub issue — see the [DevOps_learning](https://github.com/users/shiwangbisht/projects/1) board.

## Where you have real-world application

- `../master_linux/master_linux` — your existing process-internals notes; a good place to extend with a `networking/` subfolder for the Level 8–12 drills above once you've done them.
- Daily SIP protocol troubleshooting at work — genuinely rare experience for a DevOps/SRE candidate. Once you've done Level 13, make sure it shows up explicitly in your resume and interview stories, not just "Kubernetes."
