#!/usr/bin/env python3
"""
Break each module's Depth checklist into individual sub-issues (one per subtopic),
each carrying its own description + a resource list curated for THAT subtopic
specifically (not the whole module's reading list), filed as a GitHub sub-issue
of that module's tracking issue, added to the DevOps_learning project board, and
placed into the Iteration matching the module's position in the learning order.

Idempotent: if a sub-issue with the same title already exists, its body is
refreshed in place (gh issue edit) instead of creating a duplicate - safe to
re-run any time the resource curation below changes.

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
CLEAR_ITERATION_MODULES = {"03-observability"}

PROJECT_ID = "PVT_kwHOCHADX84BdVJl"
STATUS_FIELD_ID = "PVTSSF_lAHOCHADX84BdVJlzhX3cg0"
BACKLOG_OPTION_ID = "f75ad846"
ITERATION_FIELD_ID = "PVTIF_lAHOCHADX84BdVJlzhX3cuY"

# Per-subtopic resources: (module_dir, short_title(item)) -> [(label, url), ...]
# Curated deliberately narrow - one or two links that actually cover THIS
# subtopic, not the module's whole reading list.
RESOURCES = {
    ("00-basics", "Linux fundamentals"): [
        ("man7.org - Linux man pages", "https://man7.org/linux/man-pages/"),
        ("Linux Journey (free, beginner-friendly)", "https://linuxjourney.com/"),
    ],
    ("00-basics", "Shell basics"): [
        ("GNU Bash Reference Manual", "https://www.gnu.org/software/bash/manual/bash.html"),
    ],
    ("00-basics", "Networking fundamentals"): [
        ("MDN - How the Web works (HTTP overview)", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview"),
        ("RFC 1035 - DNS", "https://www.rfc-editor.org/rfc/rfc1035"),
    ],
    ("00-basics", "Git"): [
        ("Pro Git book (free, official)", "https://git-scm.com/book/en/v2"),
        ("Git reference docs", "https://git-scm.com/docs"),
    ],
    ("00-basics", "Containers (Docker), before Kubernetes"): [
        ("Docker - Get started", "https://docs.docker.com/get-started/"),
        ("Dockerfile best practices", "https://docs.docker.com/build/building/best-practices/"),
    ],
    ("00-basics", "Cloud computing basics"): [
        ("AWS - What is cloud computing", "https://aws.amazon.com/what-is-cloud-computing/"),
        ("AWS shared responsibility model", "https://aws.amazon.com/compliance/shared-responsibility-model/"),
    ],
    ("00-basics", "Basic systems concepts"): [
        ("MDN Glossary - Load balancing", "https://developer.mozilla.org/en-US/docs/Glossary/Load_Balancing"),
        ("MDN Glossary - Proxy server", "https://developer.mozilla.org/en-US/docs/Glossary/Proxy_server"),
    ],
    ("01-kubernetes-sre", "Scheduling"): [
        ("Kubernetes - kube-scheduler", "https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/"),
        ("Kubernetes - Resource requests/limits & QoS", "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"),
    ],
    ("01-kubernetes-sre", "Rollouts"): [
        ("Kubernetes - Deployments", "https://kubernetes.io/docs/concepts/workloads/controllers/deployment/"),
        ("Kubernetes - Configure probes", "https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"),
    ],
    ("01-kubernetes-sre", "Networking"): [
        ("Kubernetes - Service", "https://kubernetes.io/docs/concepts/services-networking/service/"),
        ("Kubernetes - DNS for Services and Pods", "https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/"),
    ],
    ("01-kubernetes-sre", "Storage"): [
        ("Kubernetes - Persistent Volumes", "https://kubernetes.io/docs/concepts/storage/persistent-volumes/"),
    ],
    ("01-kubernetes-sre", "Autoscaling"): [
        ("Kubernetes - Autoscaling workloads", "https://kubernetes.io/docs/concepts/workloads/autoscaling/"),
        ("Kubernetes - Horizontal Pod Autoscaling", "https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/"),
    ],
    ("01-kubernetes-sre", "etcd & control plane"): [
        ("Kubernetes - Components", "https://kubernetes.io/docs/concepts/overview/components/"),
    ],
    ("01-kubernetes-sre", "RBAC & multi-tenancy basics"): [
        ("Kubernetes - Using RBAC Authorization", "https://kubernetes.io/docs/reference/access-authn-authz/rbac/"),
    ],
    ("01-kubernetes-sre", "Resource pressure"): [
        ("Kubernetes - Node-pressure eviction", "https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/"),
        ("Kubernetes - Troubleshoot applications", "https://kubernetes.io/docs/tasks/debug/debug-application/"),
    ],
    ("01-kubernetes-sre", "Helm or Kustomize for templating what you currently apply manually/vi…"): [
        ("Helm docs", "https://helm.sh/docs/"),
        ("Kustomize docs", "https://kubectl.docs.kubernetes.io/guides/introduction/kustomize/"),
    ],
    ("02-aws-cloud", "Compute"): [
        ("EC2 - Instance types & concepts", "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html"),
        ("App Runner - What is App Runner", "https://docs.aws.amazon.com/apprunner/latest/dg/what-is-apprunner.html"),
    ],
    ("02-aws-cloud", "Networking"): [
        ("Amazon VPC - What is Amazon VPC", "https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html"),
        ("Route 53 - Routing policies", "https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html"),
    ],
    ("02-aws-cloud", "Serverless/eventing"): [
        ("Lambda developer guide", "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html"),
        ("SQS developer guide", "https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html"),
        ("SNS developer guide", "https://docs.aws.amazon.com/sns/latest/dg/welcome.html"),
    ],
    ("02-aws-cloud", "Logging/observability pipeline"): [
        ("Kinesis Firehose - What is this service", "https://docs.aws.amazon.com/firehose/latest/dev/what-is-this-service.html"),
        ("CloudWatch - What is CloudWatch", "https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html"),
    ],
    ("02-aws-cloud", "Data"): [
        ("RDS User Guide", "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html"),
    ],
    ("02-aws-cloud", "Identity/secrets"): [
        ("Cognito - What is Amazon Cognito", "https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html"),
        ("Secrets Manager - Intro", "https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html"),
        ("IAM - Introduction", "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html"),
    ],
    ("02-aws-cloud", "Cost"): [
        ("AWS Cost Management", "https://aws.amazon.com/aws-cost-management/"),
    ],
    ("03-observability", "Metrics vs logs vs traces — when each is the right tool, and how they…"): [
        ("OpenTelemetry - Signals (metrics/logs/traces)", "https://opentelemetry.io/docs/concepts/signals/"),
    ],
    ("03-observability", "Prometheus"): [
        ("Prometheus - Querying basics", "https://prometheus.io/docs/prometheus/latest/querying/basics/"),
        ("Prometheus - Metric types", "https://prometheus.io/docs/concepts/metric_types/"),
    ],
    ("03-observability", "Alertmanager"): [
        ("Prometheus - Alertmanager", "https://prometheus.io/docs/alerting/latest/alertmanager/"),
    ],
    ("03-observability", "Grafana"): [
        ("Grafana docs", "https://grafana.com/docs/grafana/latest/"),
    ],
    ("03-observability", "Elasticsearch"): [
        ("Elasticsearch reference guide", "https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html"),
        ("Elasticsearch - Cluster health", "https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-health.html"),
    ],
    ("03-observability", "Logstash/Filebeat"): [
        ("Logstash reference guide", "https://www.elastic.co/guide/en/logstash/current/index.html"),
        ("Filebeat reference guide", "https://www.elastic.co/guide/en/beats/filebeat/current/index.html"),
    ],
    ("03-observability", "Correlating a Kubernetes/AWS event with an ELK log spike and a Promet…"): [
        ("Prometheus docs (for cross-referencing metrics)", "https://prometheus.io/docs/introduction/overview/"),
    ],
    ("04-databases", "Postgres"): [
        ("PostgreSQL - High availability & replication", "https://www.postgresql.org/docs/current/high-availability.html"),
        ("PostgreSQL - Using EXPLAIN", "https://www.postgresql.org/docs/current/using-explain.html"),
    ],
    ("04-databases", "Backup/restore"): [
        ("PostgreSQL - Backup and restore", "https://www.postgresql.org/docs/current/backup.html"),
    ],
    ("04-databases", "MongoDB/Redis/DynamoDB (from your DB repo's structure)"): [
        ("MongoDB - Replication", "https://www.mongodb.com/docs/manual/replication/"),
        ("Redis docs", "https://redis.io/docs/latest/"),
        ("DynamoDB - Partition key design", "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html"),
    ],
    ("04-databases", "Migration strategy"): [
        ("AWS Database Migration Service - What is DMS", "https://docs.aws.amazon.com/dms/latest/userguide/Welcome.html"),
    ],
    ("04-databases", "Locking/contention"): [
        ("PostgreSQL - Explicit locking", "https://www.postgresql.org/docs/current/explicit-locking.html"),
    ],
    ("05-terraform-iac", "Core workflow"): [
        ("Terraform - Core workflow", "https://developer.hashicorp.com/terraform/intro/core-workflow"),
    ],
    ("05-terraform-iac", "State"): [
        ("Terraform - State", "https://developer.hashicorp.com/terraform/language/state"),
        ("Terraform - Remote state", "https://developer.hashicorp.com/terraform/language/state/remote"),
    ],
    ("05-terraform-iac", "Modules"): [
        ("Terraform - Module development", "https://developer.hashicorp.com/terraform/language/modules/develop"),
    ],
    ("05-terraform-iac", "Blast radius thinking"): [
        ("Terraform - Core workflow (plan/apply)", "https://developer.hashicorp.com/terraform/intro/core-workflow"),
    ],
    ("05-terraform-iac", "Secrets in IaC"): [
        ("Terraform - Sensitive data in state", "https://developer.hashicorp.com/terraform/language/state/sensitive-data"),
    ],
    ("05-terraform-iac", "Alternative"): [
        ("AWS CDK v2 Developer Guide", "https://docs.aws.amazon.com/cdk/v2/guide/home.html"),
    ],
    ("06-cicd-gitops", "Pipeline stages"): [
        ("GitHub Actions - Understanding GitHub Actions", "https://docs.github.com/en/actions/about-github-actions/understanding-github-actions"),
    ],
    ("06-cicd-gitops", "GitHub Actions (or your CI of choice)"): [
        ("GitHub Actions - Understanding GitHub Actions", "https://docs.github.com/en/actions/about-github-actions/understanding-github-actions"),
    ],
    ("06-cicd-gitops", "Deployment strategies"): [
        ("Argo Rollouts docs (canary/blue-green)", "https://argo-rollouts.readthedocs.io/en/stable/"),
    ],
    ("06-cicd-gitops", "GitOps"): [
        ("Argo CD - Core concepts", "https://argo-cd.readthedocs.io/en/stable/core_concepts/"),
    ],
    ("06-cicd-gitops", "Artifact management"): [
        ("GitHub Packages - Introduction", "https://docs.github.com/en/packages/learn-github-packages/introduction-to-github-packages"),
    ],
    ("06-cicd-gitops", "Rollback"): [
        ("Kubernetes - Rolling update & rollback", "https://kubernetes.io/docs/tasks/run-application/rolling-update-deployment/"),
    ],
    ("07-scripting", "Bash"): [
        ("GNU Bash Reference Manual", "https://www.gnu.org/software/bash/manual/bash.html"),
    ],
    ("07-scripting", "Python"): [
        ("Python tutorial (official)", "https://docs.python.org/3/tutorial/index.html"),
        ("boto3 (AWS SDK for Python) docs", "https://boto3.amazonaws.com/v1/documentation/api/latest/index.html"),
    ],
    ("07-scripting", "Go"): [
        ("A Tour of Go", "https://go.dev/tour/"),
        ("Effective Go", "https://go.dev/doc/effective_go"),
    ],
    ("07-scripting", "Idempotency and dry-run patterns — any script that touches production…"): [
        ("GNU Bash Reference Manual (set -e, error handling)", "https://www.gnu.org/software/bash/manual/bash.html"),
    ],
    ("07-scripting", "Basic testing for your own scripts (even simple assertion-based tests…"): [
        ("Python - unittest", "https://docs.python.org/3/library/unittest.html"),
        ("Go - testing package", "https://pkg.go.dev/testing"),
    ],
    ("08-sre-fundamentals", "SLI/SLO/SLA — the actual difference, and how to pick a good SLI for a…"): [
        ("SRE Book - Service Level Objectives", "https://sre.google/sre-book/service-level-objectives/"),
    ],
    ("08-sre-fundamentals", "Error budgets — what they're for (a policy for balancing reliability …"): [
        ("SRE Book - Embracing Risk (error budgets)", "https://sre.google/sre-book/embracing-risk/"),
    ],
    ("08-sre-fundamentals", "Incident management"): [
        ("SRE Book - Managing Incidents", "https://sre.google/sre-book/managing-incidents/"),
    ],
    ("08-sre-fundamentals", "Postmortems"): [
        ("SRE Book - Postmortem Culture", "https://sre.google/sre-book/postmortem-culture/"),
    ],
    ("08-sre-fundamentals", "Toil"): [
        ("SRE Book - Eliminating Toil", "https://sre.google/sre-book/eliminating-toil/"),
    ],
    ("08-sre-fundamentals", "Capacity planning"): [
        ("SRE Book - Capacity Planning", "https://sre.google/sre-book/capacity-planning/"),
    ],
    ("08-sre-fundamentals", "On-call sustainability"): [
        ("SRE Book - Being On-Call", "https://sre.google/sre-book/being-on-call/"),
    ],
    ("09-linux-networking", "Process internals (existing strength) — signals, zombie/orphan proces…"): [
        ("man7.org - signal(7)", "https://man7.org/linux/man-pages/man7/signal.7.html"),
    ],
    ("09-linux-networking", "TCP fundamentals"): [
        ("RFC 793 - TCP", "https://www.rfc-editor.org/rfc/rfc793"),
    ],
    ("09-linux-networking", "DNS resolution path end-to-end, and how a misconfigured resolver show…"): [
        ("RFC 1035 - DNS", "https://www.rfc-editor.org/rfc/rfc1035"),
    ],
    ("09-linux-networking", "Common diagnostic tools"): [
        ("man7.org - ss(8)", "https://man7.org/linux/man-pages/man8/ss.8.html"),
        ("man7.org - tcpdump(8)", "https://man7.org/linux/man-pages/man8/tcpdump.8.html"),
    ],
    ("09-linux-networking", "Filesystem/disk"): [
        ("man7.org - df(1)", "https://man7.org/linux/man-pages/man1/df.1.html"),
        ("man7.org - du(1)", "https://man7.org/linux/man-pages/man1/du.1.html"),
    ],
    ("09-linux-networking", "SIP-specific"): [
        ("RFC 3261 - SIP", "https://www.rfc-editor.org/rfc/rfc3261"),
    ],
}


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
    return re.sub(r"^\[ \]\s*", "", item)


def short_title(item, limit=70):
    head = item.split(":", 1)[0].strip()
    if len(head) < len(item) and len(head) <= limit:
        head = head.strip("*").strip()
        return head
    cleaned = item.strip("*").strip()
    return (cleaned[: limit - 1] + "…") if len(cleaned) > limit else cleaned


def resources_block_for(module_dir, item, module_fallback):
    key = (module_dir, short_title(item))
    pairs = RESOURCES.get(key)
    if not pairs:
        return module_fallback
    return "\n".join(f"- [{label}]({url})" for label, url in pairs)


def existing_issue(title):
    out = run([
        "gh", "issue", "list", "--repo", REPO,
        "--search", f'in:title "{title}"', "--state", "open",
        "--json", "url,title,number",
    ])
    for row in json.loads(out):
        if row["title"] == title:
            return row["url"], row["number"]
    return None, None


def main():
    for module_dir, (parent_issue, label) in MODULES.items():
        readme = ROOT / module_dir / "README.md"
        text = readme.read_text()
        checklist = [clean_checklist_item(i) for i in parse_section(text, "Depth checklist")]
        module_resources = parse_section(text, "Where to learn")
        module_fallback = "\n".join(f"- {r}" for r in module_resources) or "See module README."

        iteration_id = MODULE_ITERATION.get(module_dir)

        print(f"\n=== {module_dir} ({len(checklist)} subtopics) ===")
        for item in checklist:
            title = f"[{label}] {short_title(item)}"
            resources_block = resources_block_for(module_dir, item, module_fallback)
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

            url, number = existing_issue(title)
            if url:
                run(["gh", "issue", "edit", str(number), "--repo", REPO, "--body-file", body_path])
                print(f"  updated body: {title} -> {url}")
            else:
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
