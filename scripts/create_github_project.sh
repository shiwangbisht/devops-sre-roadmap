#!/usr/bin/env bash
# One-time setup: push this repo to GitHub, file one issue per module (body = that
# module's README, so the issue already contains what to learn / where to learn /
# self-test), and add every issue to a GitHub Project board.
#
# Requires: `gh` CLI installed and authenticated (`gh auth login`).
# Safe to re-run for the issue/project steps if the repo already exists on GitHub —
# it skips repo creation when a remote is already configured.

set -euo pipefail

cd "$(dirname "$0")/.."

REPO_NAME="devops-sre-roadmap"
VISIBILITY="${VISIBILITY:-private}"   # set VISIBILITY=public before running to make it public instead
PROJECT_TITLE="DevOps/SRE Roadmap"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found. Install it first (see PROJECT_SETUP.md), then run: gh auth login" >&2
  exit 1
fi

gh auth status >/dev/null 2>&1 || { echo "Run 'gh auth login' first."; exit 1; }

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "Creating GitHub repo ($VISIBILITY) and pushing..."
  gh repo create "$REPO_NAME" --"$VISIBILITY" --source=. --remote=origin --push
else
  echo "Remote 'origin' already configured, skipping repo creation."
fi

echo "Creating project '$PROJECT_TITLE'..."
PROJECT_NUMBER=$(gh project create --owner "@me" --title "$PROJECT_TITLE" --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["number"])')
echo "Project number: $PROJECT_NUMBER"

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
  echo "Creating issue for $title..."
  url=$(gh issue create --title "$title" --body-file "$dir/README.md" --label learning)
  echo "  -> $url"
  gh project item-add "$PROJECT_NUMBER" --owner "@me" --url "$url"
done

echo
echo "Done. Open the project board with: gh project view $PROJECT_NUMBER --owner @me --web"
echo "The board's default Status field has Todo/In Progress/Done - rename the options"
echo "to Backlog/Learning/Practicing/Done from the project's web UI if you want the exact match."
