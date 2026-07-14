#!/usr/bin/env bash
# One-time setup: push this repo to GitHub, file one issue per module (body = that
# module's README, so the issue already contains what to learn / where to learn /
# self-test), and add every issue to your existing "DevOps_learning" GitHub Project
# (github.com/users/<you>/projects/1), placed in its Backlog column.
#
# Requires: `gh` CLI installed and authenticated (`gh auth login`), and the
# "DevOps_learning" project already created on GitHub (it already is, per your board).
#
# Safe to re-run: skips repo creation if a remote already exists, and skips an
# issue if one with the same title is already open in this repo.

set -euo pipefail

cd "$(dirname "$0")/.."

REPO_NAME="devops-sre-roadmap"
VISIBILITY="${VISIBILITY:-private}"   # set VISIBILITY=public before running to make it public instead
PROJECT_TITLE="${PROJECT_TITLE:-DevOps_learning}"
BACKLOG_OPTION="${BACKLOG_OPTION:-Backlog}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found. Install it first (see PROJECT_SETUP.md), then run: gh auth login" >&2
  exit 1
fi

gh auth status >/dev/null 2>&1 || { echo "Run 'gh auth login' first."; exit 1; }

OWNER=$(gh api user --jq .login)

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "Creating GitHub repo ($VISIBILITY) and pushing..."
  gh repo create "$REPO_NAME" --"$VISIBILITY" --source=. --remote=origin --push
else
  echo "Remote 'origin' already configured, skipping repo creation."
fi

echo "Looking up existing project '$PROJECT_TITLE' for $OWNER..."
PROJECT_JSON=$(gh project list --owner "$OWNER" --format json)
PROJECT_NUMBER=$(python3 -c '
import json, sys
data = json.load(sys.stdin)
title = sys.argv[1]
for p in data.get("projects", []):
    if p["title"] == title:
        print(p["number"])
        break
' "$PROJECT_JSON" "$PROJECT_TITLE")

if [ -z "${PROJECT_NUMBER:-}" ]; then
  echo "Couldn't find a project named '$PROJECT_TITLE' for $OWNER." >&2
  echo "Set PROJECT_TITLE=<exact name> if yours is named differently, or create it on github.com first." >&2
  exit 1
fi
echo "Found project #$PROJECT_NUMBER."

PROJECT_ID=$(gh project view "$PROJECT_NUMBER" --owner "$OWNER" --format json --jq .id)

# Find the "Status" field and the option id matching $BACKLOG_OPTION, so new items
# land directly in your Backlog column instead of unsorted.
FIELDS_JSON=$(gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json)
STATUS_FIELD_ID=$(python3 -c '
import json, sys
data = json.load(sys.stdin)
for f in data.get("fields", []):
    if f.get("name") == "Status":
        print(f["id"])
        break
' "$FIELDS_JSON")
BACKLOG_OPTION_ID=$(python3 -c '
import json, sys
data = json.load(sys.stdin)
target = sys.argv[1]
for f in data.get("fields", []):
    if f.get("name") == "Status":
        for o in f.get("options", []):
            if o["name"] == target:
                print(o["id"])
                break
' "$FIELDS_JSON" "$BACKLOG_OPTION")

declare -a MODULES=(
  "01-kubernetes-sre:Module 01 - Kubernetes & container SRE"
  "02-aws-cloud:Module 02 - AWS cloud"
  "03-observability:Module 03 - Observability"
  "04-databases:Module 04 - Databases"
  "05-terraform-iac:Module 05 - Terraform / IaC"
  "06-cicd-gitops:Module 06 - CI/CD & GitOps"
  "07-scripting:Module 07 - Scripting"
  "08-sre-fundamentals:Module 08 - SRE fundamentals"
  "09-linux-networking:Module 09 - Linux & networking"
)

gh label create learning --color BFD4F2 --description "Roadmap learning task" 2>/dev/null || true

for entry in "${MODULES[@]}"; do
  dir="${entry%%:*}"
  title="${entry#*:}"

  existing=$(gh issue list --search "in:title \"$title\"" --state open --json url --jq '.[0].url // empty')
  if [ -n "$existing" ]; then
    echo "Issue already exists for $title -> $existing"
    url="$existing"
  else
    echo "Creating issue for $title..."
    url=$(gh issue create --title "$title" --body-file "$dir/README.md" --label learning)
    echo "  -> $url"
  fi

  ITEM_ID=$(gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" --url "$url" --format json --jq .id)

  if [ -n "$STATUS_FIELD_ID" ] && [ -n "$BACKLOG_OPTION_ID" ]; then
    gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" \
      --field-id "$STATUS_FIELD_ID" --single-select-option-id "$BACKLOG_OPTION_ID"
  fi
done

echo
echo "Done. Open the board with: gh project view $PROJECT_NUMBER --owner $OWNER --web"
