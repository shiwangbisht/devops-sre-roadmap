# Tracking this roadmap on GitHub

This repo is local-only right now (no GitHub remote). Two ways to get it onto GitHub with an Issue per module and a Project board to track them — pick one.

## Option A — one script (needs the `gh` CLI)

1. Install the GitHub CLI: https://cli.github.com (macOS: `brew install gh`, or download the installer if you don't have Homebrew).
2. Authenticate: `gh auth login` — follow the browser prompt.
3. From this repo's root, run:
   ```
   ./scripts/create_github_project.sh
   ```
   This pushes the repo to GitHub (private by default — set `VISIBILITY=public` before running if you want it public), files one issue per module (each issue body is that module's full README — checklist, resources, self-test, scenario projects), creates a Project board, and adds every issue to it.
4. Open the board: `gh project view <number> --owner @me --web` (the script prints the exact command with the number filled in).
5. In the board's web UI, rename the default Status options (Todo/In Progress/Done) to **Backlog / Learning / Practicing / Done** if you want the exact 4-column flow — `gh` can't set custom option names on creation.

## Option B — manual, no CLI needed

1. On github.com, create a new repository named `devops-sre-roadmap` (private or public, your call).
2. From this folder, push it:
   ```
   git remote add origin <the URL GitHub gives you>
   git branch -M main
   git push -u origin main
   ```
3. On the repo page: **Issues → New issue**. You should see the "Learning task" form (from `.github/ISSUE_TEMPLATE/learning-module.yml`) as an option once the repo is pushed — use it once per module, or just paste each module's README content straight into a plain issue if you'd rather move faster.
4. On the repo page: **Projects → New project → Board**. Add a "Status" field (or use the default one) with columns **Backlog / Learning / Practicing / Done**.
5. Open each issue and add it to the project from the issue sidebar; set its status to Backlog.

## Using it day to day

- Move an issue Backlog → Learning when you start a module, → Practicing once you're doing the scenario projects, → Done once you can pass the module's self-test cold.
- When you finish a real incident writeup (module 08) or a scenario project, drop a comment on that module's issue — over time the issue becomes a log of what you actually did, which is useful on its own when prepping for interviews.
- Follow the order in the root [README.md](README.md#learning-order) — file/start issues roughly in that sequence rather than all nine at once.
