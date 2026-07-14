#!/usr/bin/env python3
"""
Break each module's Depth checklist into individual sub-issues (one per subtopic),
each carrying its own description + where-to-learn, filed as a GitHub sub-issue of
that module's tracking issue, added to the DevOps_learning project board, and
placed into the Iteration matching the module's position in the learning order.

Idempotent: skips creating a sub-issue whose title already exists as an open issue.

Requires: gh CLI authenticated with repo+project scopes.
"""
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = "shiwangbisht"
PROJECT_NUMBER = "1"
REPO = "shiwangbisht/devops-sre-roadmap"

# module dir -> (parent issue number, short label used in sub-issue titles)
MODULES = {
    "00-basics": (69, "Basics"),
    "01-kubernetes-sre": (1, "K8s"),
    "02-aws-cloud": (2, "AWS"),
    "03-observability": (3, "Observability"),
    "04-databases": (4, "DB"),
    "05-terraform-iac": (5, "Terraform"),
    "06-cicd-gitops": (6, "CI/CD"),
    "07-scripting": (7, "Scripting"),
    "08-sre-fundamentals": (8, "SRE"),
    "09-linux-networking": (9, "Linux/Net"),
}

# Sequential learning order (matches root README) -> the existing pre-configured
# iterations on the board. Only 5 iterations exist right now; whatever falls
# past the 5th slot is left with no iteration until more are added.
SEQUENTIAL_ORDER = [
    "00-basics",
    "01-kubernetes-sre",
    "05-terraform-iac",
    "02-aws-cloud",
    "06-cicd-gitops",
    "03-observability",
    "04-databases",
    "09-linux-networking",
]
ITERATION_IDS = [
    "381c7c80",  # Iteration 1 (2026-07-13)
    "54cf5c95",  # Iteration 2 (2026-07-27)
    "d2c335bc",  # Iteration 3 (2026-08-10)
    "b6a8f1bb",  # Iteration 4 (2026-08-24)
    "955c1297",  # Iteration 5 (2026-09-07)
]
MODULE_ITERATION = dict(zip(SEQUENTIAL_ORDER, ITERATION_IDS))
# Everything past position 5 (03-observability onward) intentionally gets no
# iteration yet - not enough iterations configured on the board.
# 07-scripting and 08-sre-fundamentals are the continuous track: no iteration.

# Modules that previously had an iteration assigned (from before 00-basics was
# inserted at the front, shifting everything else back by one slot) but no
# longer map to one - their existing sub-issues need the field explicitly
# cleared, not just left alone.
CLEAR_ITERATION_MODULES = {"03-observability"}

PROJECT_ID = "PVT_kwHOCHADX84BdVJl"
STATUS_FIELD_ID = "PVTSSF_lAHOCHADX84BdVJlzhX3cg0"
BACKLOG_OPTION_ID = "f75ad846"
ITERATION_FIELD_ID = "PVTIF_lAHOCHADX84BdVJlzhX3cuY"


def run(cmd, input_text=None, retries=4):
    last_err = ""
    for attempt in range(1, retries + 1):
        result = subprocess.run(cmd, capture_output=True, text=True, input=input_text)
        if result.returncode == 0:
            return result.stdout.strip()
        last_err = result.stderr
        wait = 2 ** attempt
        print(f"  (retry {attempt}/{retries} after error: {last_err.strip()[:200]}, waiting {wait}s)", file=sys.stderr)
        time.sleep(wait)
    print(f"FAILED after {retries} retries: {' '.join(cmd)}\n{last_err}", file=sys.stderr)
    raise SystemExit(1)


def parse_section(text, heading):
    """Return the list of top-level bullet lines under a '## heading' section."""
    pattern = rf"## {re.escape(heading)}\n(.*?)(?=\n## |\Z)"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return []
    lines = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith("- "):
            lines.append(line[2:].strip())
    return lines


def clean_checklist_item(item):
    # strip a leading "[ ] " checkbox marker
    return re.sub(r"^\[ \]\s*", "", item)


def short_title(item, limit=70):
    head = item.split(":", 1)[0].strip()
    if len(head) < len(item) and len(head) <= limit:
        head = head.strip("*").strip()
        return head
    cleaned = item.strip("*").strip()
    return (cleaned[: limit - 1] + "…") if len(cleaned) > limit else cleaned


def existing_issue_url(title):
    out = run([
        "gh", "issue", "list", "--repo", REPO,
        "--search", f'in:title "{title}"', "--state", "open",
        "--json", "url,title",
    ])
    for row in json.loads(out):
        if row["title"] == title:
            return row["url"]
    return None


def main():
    for module_dir, (parent_issue, label) in MODULES.items():
        readme = ROOT / module_dir / "README.md"
        text = readme.read_text()
        checklist = [clean_checklist_item(i) for i in parse_section(text, "Depth checklist")]
        resources = parse_section(text, "Where to learn")
        resources_block = "\n".join(f"- {r}" for r in resources) or "See module README."

        iteration_id = MODULE_ITERATION.get(module_dir)

        print(f"\n=== {module_dir} ({len(checklist)} subtopics) ===")
        for item in checklist:
            title = f"[{label}] {short_title(item)}"
            url = existing_issue_url(title)
            if url:
                print(f"  exists: {title} -> {url}")
            else:
                body = (
                    f"Part of Module #{parent_issue} ({module_dir}).\n\n"
                    f"### What to learn\n{item}\n\n"
                    f"### Where to learn\n{resources_block}\n\n"
                    f"### Self-test\nSee the self-test section in `{module_dir}/README.md` "
                    f"(or parent issue #{parent_issue}) — you should be able to answer the "
                    f"related question(s) cold, no notes, before marking this done."
                )
                with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
                    f.write(body)
                    body_path = f.name
                url = run([
                    "gh", "issue", "create", "--repo", REPO,
                    "--title", title, "--body-file", body_path,
                    "--label", "learning", "--parent", str(parent_issue),
                    "-p", "DevOps_learning",
                ])
                print(f"  created: {title} -> {url}")

            item_id = run([
                "gh", "project", "item-add", PROJECT_NUMBER, "--owner", OWNER,
                "--url", url, "--format", "json", "--jq", ".id",
            ])
            run([
                "gh", "project", "item-edit", "--id", item_id, "--project-id", PROJECT_ID,
                "--field-id", STATUS_FIELD_ID, "--single-select-option-id", BACKLOG_OPTION_ID,
            ])
            if iteration_id:
                run([
                    "gh", "project", "item-edit", "--id", item_id, "--project-id", PROJECT_ID,
                    "--field-id", ITERATION_FIELD_ID, "--iteration-id", iteration_id,
                ])
            elif module_dir in CLEAR_ITERATION_MODULES:
                run([
                    "gh", "project", "item-edit", "--id", item_id, "--project-id", PROJECT_ID,
                    "--field-id", ITERATION_FIELD_ID, "--clear",
                ])


if __name__ == "__main__":
    main()
