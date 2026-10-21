# Scripting for SRE — Bash & Python patterns

Not a language tutorial — the specific patterns that come up constantly in SRE/ops work, and the
mistakes that turn a quick script into a production incident.

## Bash — the patterns that actually matter

### `set -euo pipefail` — the single most important line in any production bash script

```bash
#!/usr/bin/env bash
set -euo pipefail
```
- `set -e` — exit immediately if any command fails (default bash behavior silently continues past
  failures, which is how a script "succeeds" after actually failing partway through).
- `set -u` — error on use of an undefined variable, instead of silently substituting an empty string
  (a classic cause of `rm -rf $UNSET_VAR/` deleting `/` because the variable was empty).
- `set -o pipefail` — a pipeline's exit code reflects the **first** failing command, not just the last
  one — without it, `false | true` exits `0` (success), silently hiding the failure.

### Quoting — the other classic source of real incidents

```bash
rm -rf "$dir"/*     # correct: quoted, handles paths with spaces safely
rm -rf $dir/*        # dangerous: unquoted — word-splits on spaces, glob-expands unexpectedly
```
Unquoted variables undergo word splitting and globbing — a filename/path with a space in it silently
becomes two arguments. **Always quote variable expansions** unless you specifically need word-splitting
(rare, and should be deliberate with `$@`-style cases, not an oversight).

### Trap for cleanup — don't leave things half-done on failure/interrupt

```bash
tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT
# ... script logic using $tmpfile ...
```
`trap ... EXIT` runs the cleanup command whether the script exits normally, errors out (with `set -e`),
or gets interrupted (Ctrl+C) — the reliable way to guarantee temp files/locks get cleaned up instead of
only handling the happy path.

### Idempotency — the property every ops script actually needs

A script that creates a resource should check if it already exists first (or handle the "already
exists" error gracefully) — so re-running it after a partial failure doesn't error out or create
duplicates. This is the scripting-level version of Terraform's whole "declare desired state, converge
toward it on repeated runs" model — a one-shot, non-idempotent script is the thing that turns "the
deploy script failed halfway, just run it again" into a second, different failure.

### Common real gotchas

- `[ ]` vs `[[ ]]` — `[[ ]]` is bash-specific, supports `&&`/`||`/regex matching directly, and doesn't
  word-split unquoted variables inside it the way `[ ]` does — prefer `[[ ]]` in bash scripts (not
  `sh`/POSIX-portable scripts, where only `[ ]` exists).
- Arithmetic: `$((a + b))`, not string concatenation — easy to get wrong when a variable is unexpectedly
  a string.
- `local` inside functions — without it, a variable assigned inside a function is **global** by default
  in bash, a real source of a function silently clobbering a caller's variable of the same name.

## Python — where it beats bash for ops work

Reach for Python over bash once a script needs: real data structures (parsing/manipulating JSON/YAML
instead of `grep`/`awk`-ing text), real error handling (`try`/`except` with specific exception types,
not just checking exit codes), or calling cloud APIs directly (`boto3` for AWS) instead of shelling out
to the CLI and parsing its text output.

```python
import boto3
import sys

ec2 = boto3.client("ec2")

def stopped_instances():
    paginator = ec2.get_paginator("describe_instances")
    for page in paginator.paginate(Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]):
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                yield instance["InstanceId"]

if __name__ == "__main__":
    ids = list(stopped_instances())
    if not ids:
        print("no stopped instances found")
        sys.exit(0)
    print(f"found {len(ids)} stopped instances: {ids}")
```
**Why `boto3` over shelling out to `aws` CLI + `jq`:** typed responses, pagination handled for you
(`get_paginator`), real exceptions instead of parsing stderr text to detect failure modes, and no
double-parsing (JSON out of the CLI, then JSON out of `jq`).

### Error handling that actually distinguishes failure types

```python
import botocore.exceptions

try:
    ec2.terminate_instances(InstanceIds=[instance_id])
except botocore.exceptions.ClientError as e:
    code = e.response["Error"]["Code"]
    if code == "InvalidInstanceID.NotFound":
        print(f"{instance_id} already gone, treating as success")
    else:
        raise   # don't silently swallow unexpected errors
```
Catching broad `Exception` and logging-and-continuing hides real bugs; catching the **specific** error
you expect and genuinely handling it, while letting unexpected errors propagate, is what makes error
handling actually trustworthy instead of just quiet.

### Logging, not `print`, for anything that runs unattended

```python
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

logger.info("starting cleanup, found %d stale resources", len(resources))
```
`print` output is easy to lose (no level filtering, no timestamp by default, often swallowed by
whatever's running the script); structured logging with levels is what makes a cron-job/CI-triggered
script's output actually useful after the fact, especially for something that only runs occasionally and
needs investigating weeks later.

---

## Interview questions (with the short answer you should be able to give cold)

1. *Why should every production bash script start with `set -euo pipefail`?* — `-e` stops execution on
   any failing command instead of silently continuing past it; `-u` errors on undefined variables
   instead of substituting empty strings (a classic cause of accidental `rm -rf /`); `pipefail` makes a
   pipeline's exit code reflect any failing stage, not just the last one — without all three, a script
   can "succeed" (exit 0) after actually failing partway through.
2. *What's the actual risk of `rm -rf $dir/*` versus `rm -rf "$dir"/*`?* — Unquoted variable expansion
   undergoes word-splitting and globbing — a path containing a space becomes multiple arguments
   unexpectedly, and an empty/unset `$dir` (especially without `set -u`) can expand to something far
   broader than intended.
3. *What does `trap ... EXIT` actually guarantee that just putting cleanup code at the end of the script
   doesn't?* — It runs on every exit path — normal completion, an error exit under `set -e`, or an
   interrupt (Ctrl+C) — whereas cleanup code simply placed at the end of the script only runs if execution
   reaches that point, which a mid-script failure or interrupt would skip entirely.
4. *Why does idempotency matter for an ops/deployment script specifically?* — A script that fails
   partway through needs to be safely re-runnable without erroring on "already exists" conditions or
   creating duplicates — the same reasoning Terraform's "converge toward desired state on repeated runs"
   model is built on, just applied to a hand-written script instead of a declarative tool.
5. *When would you reach for Python over bash for an ops task?* — Once the task needs real data
   structure handling (parsing/manipulating JSON/YAML, not text-scraping), real typed error handling, or
   direct API calls (e.g. `boto3`) instead of shelling out to a CLI and parsing its text output — bash
   remains fine for simple, linear command-sequencing tasks.
6. *Why is `except Exception: log and continue` considered bad error handling in a script that manages
   real infrastructure?* — It silently swallows unexpected failures along with expected ones, hiding real
   bugs and letting the script report false success — catching the *specific* expected exception type and
   genuinely handling just that case, while letting anything unanticipated propagate and fail loudly, is
   what makes error handling trustworthy.
7. *Why use `logging` instead of `print` in a script meant to run unattended (cron, CI)?* — `print`
   output has no severity levels, no timestamps by default, and is easy to lose depending on how the
   script is invoked; structured logging with levels/timestamps is what makes output actually useful when
   investigating an unattended run's behavior after the fact, sometimes weeks later.