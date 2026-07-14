# Tracking this roadmap on GitHub

You've already created the **DevOps_learning** project board on GitHub (`github.com/users/<you>/projects/1`) with Backlog / Ready / In progress / In review / Done columns. This repo is still local-only, though — nothing has been pushed, so there's nothing in that board yet. Two ways to populate it — pick one.

## Option A — one script (needs the `gh` CLI)

1. Install the GitHub CLI: https://cli.github.com (macOS: `brew install gh`, or download the installer if you don't have Homebrew).
2. Authenticate: `gh auth login` — follow the browser prompt.
3. From this repo's root, run:
   ```
   ./scripts/create_github_project.sh
   ```
   This pushes the repo to GitHub (private by default — set `VISIBILITY=public` before running if you want it public), finds your existing **DevOps_learning** project by name, files one issue per module (each issue body is that module's full README — checklist, resources, self-test, scenario projects), adds every issue to the board, and sets each one's Status to **Backlog** so they land in the right column automatically.
4. Open the board: `gh project view <number> --owner <you> --web` (the script prints the exact command).
5. Script is safe to re-run later — it skips creating an issue that already exists (matched by title) and just re-adds it to the board if needed.

If your project isn't literally named `DevOps_learning`, run it as `PROJECT_TITLE="your exact name" ./scripts/create_github_project.sh` instead.

## Option B — manual, no CLI needed

1. On github.com, create a new repository named `devops-sre-roadmap` (private or public, your call).
2. From this folder, push it:
   ```
   git remote add origin <the URL GitHub gives you>
   git branch -M main
   git push -u origin main
   ```
3. On the repo page: **Issues → New issue**. You should see the "Learning task" form (from `.github/ISSUE_TEMPLATE/learning-module.yml`) once the repo is pushed — use it once per module (paste in the What to learn / Where to learn / Self-test content from that module's README), or just paste the whole README into a plain issue if you'd rather move faster.
4. Open your existing **DevOps_learning** project, click **+ Add item** in the Backlog column for each module, and link the issue you just created (search by title).

## Using it day to day

- Drag an issue Backlog → Ready → In progress → In review → Done as you work through a module — Ready/In review map naturally to "queued to start" and "doing the scenario projects, not yet confident," if you want a finer split than a straight 3-stage flow.
- Consider it **Done** once you can pass that module's self-test cold, not just once you've read the material.
- When you finish a real incident writeup (module 08) or a scenario project, drop a comment on that module's issue — over time the issue becomes a log of what you actually did, useful on its own when prepping for interviews.
- Follow the order in the root [README.md](README.md#learning-order) — move/start issues roughly in that sequence rather than all nine at once.
