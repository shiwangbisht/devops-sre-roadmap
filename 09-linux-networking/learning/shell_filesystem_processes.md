# Linux — shell, filesystem, processes

Your ops background means most of this is review — the goal is filling the specific gaps that trip up
even experienced ops people in an SRE interview: permission bits math, what a process state actually
means, and signal handling beyond "kill -9 it."

## Filesystem & permissions

- **Permission bits**: `rwx` for owner/group/other, each a 3-bit number (r=4, w=2, x=1) — `755` =
  owner rwx, group r-x, other r-x. `chmod u+x file` vs `chmod 755 file` — symbolic vs. octal, same result.
- **`x` on a directory** means "can `cd` into it / traverse it," not "can list it" — that's `r`. A
  directory with `r-x` lets you `ls` and access known filenames but not traverse into subdirectories by
  name alone without `x`. Classic interview trap: `r--` on a directory lets you see filenames but not
  `cat` any file inside, because you can't traverse into it.
- **SUID/SGID/sticky bit** — SUID (`chmod u+s`) runs a binary as its *owner*, not the invoking user
  (classic example: `passwd` runs as root via SUID so a normal user can update `/etc/shadow`). Sticky
  bit (`chmod +t`, seen as `/tmp`'s permissions) means only a file's owner (or root) can delete it even
  if the directory is world-writable — exactly why `/tmp` is safe to be `777`.
- **Hard link vs. symlink** — a hard link is another directory entry pointing at the *same inode* (same
  data, can't cross filesystems, deleting one doesn't affect the other since the inode persists until
  the link count hits zero); a symlink is a separate file containing a *path string*, can cross
  filesystems/point to nonexistent targets, breaks if the target moves.
- **Inodes** — a filesystem can run out of inodes (max file count) while still having free disk space —
  `df -i` vs. `df -h` are checking two different things; "no space left on device" with free space
  showing is the classic symptom.

## Shell fundamentals worth being fluent in, not just "I've used bash"

- **Exit codes** — `0` = success, non-zero = failure, by convention (not enforced) — `$?` holds the last
  command's exit code; `&&` runs the next command only on success, `||` only on failure.
- **Redirection** — `>` overwrites, `>>` appends, `2>` redirects stderr, `2>&1` redirects stderr to
  wherever stdout currently points (order matters: `cmd > file 2>&1` vs `cmd 2>&1 > file` behave
  differently — the second one sends stderr to the *original* stdout, usually the terminal, since the
  redirect order is evaluated left to right).
- **Pipes vs. subshells** — `cmd1 | cmd2` runs both concurrently, connected by a pipe buffer; each side
  of a pipe runs in its own subshell, so `var=5 | echo $var` inside a pipeline won't see `var` set
  outside it afterward — a real gotcha for anyone writing a `while read` loop fed by a pipe.
- **`$()` vs. backticks** — functionally similar (command substitution), `$()` nests cleanly, backticks
  don't — prefer `$()` always.

## Processes

- **Process states**: `R` (running/runnable), `S` (sleeping, interruptible), `D` (uninterruptible
  sleep — usually waiting on disk I/O, **can't even be killed with `-9`** while in this state — a real
  interview-worthy fact), `Z` (zombie — process finished but parent hasn't reaped its exit status yet),
  `T` (stopped, e.g. via `Ctrl+Z`).
- **Zombie vs. orphan** — a **zombie** has exited but its exit status hasn't been collected by its
  parent (`wait()` not called) — it's just an entry in the process table, no resources held beyond that.
  An **orphan** is a process whose *parent* died first — it gets re-parented to `init`/PID 1, which
  reaps it automatically. Zombies are the parent's bug (not calling `wait()`), orphans are harmless by
  design.
- **Signals** — `SIGTERM` (15, default of `kill`, asks the process to shut down gracefully — can be
  caught/handled) vs. `SIGKILL` (9, cannot be caught/ignored, the kernel terminates it immediately, no
  cleanup) vs. `SIGHUP` (1, historically "terminal hung up," commonly repurposed by daemons to mean
  "reload config"). **Always try SIGTERM first** — SIGKILL skips any graceful shutdown logic (closing
  connections, flushing buffers), which is exactly why Kubernetes sends SIGTERM and waits
  `terminationGracePeriodSeconds` before escalating to SIGKILL.
- **systemd** — the init system (PID 1) on virtually every modern distro; manages service lifecycle via
  **unit files** (`/etc/systemd/system/myapp.service`).
  ```ini
  [Unit]
  Description=My App
  After=network.target

  [Service]
  ExecStart=/usr/local/bin/myapp
  Restart=on-failure
  User=myapp

  [Install]
  WantedBy=multi-user.target
  ```
  `systemctl start/stop/restart/status myapp`, `systemctl enable myapp` (start on boot),
  `journalctl -u myapp` (that unit's logs, integrated with systemd's own logging).

---

## Interview questions (with the short answer you should be able to give cold)

1. *A directory has `r--` permissions. Can you `cat` a file inside it if you know the exact filename?*
   — No — `r` on a directory lets you list its contents, but `x` is required to traverse into it at all,
   even to access a known filename directly.
2. *What's the practical difference between a hard link and a symlink?* — A hard link is another
   directory entry pointing at the same inode (same underlying data, same filesystem only); a symlink is
   a separate file holding a path string, can cross filesystems, and breaks if the target is moved/deleted.
3. *`df -h` shows plenty of free space but you're getting "no space left on device." What's going on?* —
   The filesystem has run out of **inodes** (max file count), not disk blocks — check `df -i`; common
   cause is a huge number of tiny files (e.g. runaway log rotation or a cache gone wrong).
4. *What's a zombie process, and is it dangerous?* — A process that has exited but whose parent hasn't
   called `wait()` to collect its exit status yet — it's just a process-table entry, holds no real
   resources. Not dangerous in small numbers; a huge pile of them usually means a parent process has a
   bug not reaping its children.
5. *Why can't you kill a process stuck in `D` state with `kill -9`?* — `D` (uninterruptible sleep) means
   the process is blocked on a kernel-level operation (usually disk I/O) that can't be interrupted even
   by SIGKILL — the process will only leave `D` state when that underlying I/O completes or times out.
6. *Why does SIGTERM get sent before SIGKILL in a graceful shutdown (e.g. Kubernetes pod termination)?*
   — SIGTERM can be caught and handled — the app gets a chance to close connections, flush buffers, exit
   cleanly. SIGKILL can't be caught at all — the kernel terminates immediately with no cleanup, used only
   as a last resort after a grace period.
7. *What does SUID on a binary like `/usr/bin/passwd` actually do, and why is it needed?* — Runs the
   binary with the *file owner's* privileges (root) rather than the invoking user's — needed because a
   normal user has no write access to `/etc/shadow`, but still needs to be able to change their own password.
8. *Why is `cmd 2>&1 > file` different from `cmd > file 2>&1`?* — Redirections are evaluated left to
   right. In the first, stderr is redirected to wherever stdout *currently* points (the terminal) before
   stdout is then redirected to the file — so stderr still goes to the terminal. In the second, stdout
   goes to the file first, then stderr is redirected to join it there — both end up in the file.