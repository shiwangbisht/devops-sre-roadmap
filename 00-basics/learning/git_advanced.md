# Git — beyond the basics

Skipping `add`/`commit`/`push`/`branch` — you know those. This is the part that actually gets asked
about and actually gets used when something's gone wrong at 11pm.

## Rebase — what it actually does, and interactive rebase

`git rebase main` replays your branch's commits one by one *on top of* the latest `main`, as if you'd
branched from there originally — rewrites commit history (new commit hashes), unlike `merge` which
creates a new merge commit and preserves both histories as-is.

**Golden rule:** never rebase a branch that others have already pulled/based work on — you'd be
rewriting history they already have, causing painful divergence. Rebase is for your own
not-yet-shared local work; merge (or a team-agreed rebase workflow with force-push discipline) for
shared branches.

```bash
git rebase -i HEAD~3   # interactive rebase of the last 3 commits
```
Opens an editor listing the last 3 commits — `pick`/`squash`/`fixup`/`reword`/`drop` each one. Real use:
cleaning up a messy WIP commit history into logical, reviewable commits *before* opening a PR.

## `git bisect` — binary search for the commit that broke something

```bash
git bisect start
git bisect bad                  # current commit is broken
git bisect good v1.2.0          # this known-good commit wasn't
# Git checks out a commit halfway between — test it, then:
git bisect good   # or: git bisect bad
# repeat until Git identifies the exact breaking commit
git bisect reset
```
Turns "something broke sometime in the last 200 commits" into `log2(200) ≈ 8` tests instead of checking
commits one by one — a genuinely practical tool, not just a trivia answer.

## Reflog — the actual undo button

`git reflog` shows **every** position `HEAD` has pointed to, including commits a `reset --hard` or a
rebase just "destroyed" — those commits aren't actually gone until garbage collected (default ~90 days).
```bash
git reflog                      # find the commit hash from before the mistake
git reset --hard <hash>         # or: git branch recovered-work <hash>
```
This is the real answer to "I ran `git reset --hard` and lost work" — it's recoverable, not gone,
almost every time, as long as it's recent.

## Cherry-pick

```bash
git cherry-pick <commit-hash>
```
Applies one specific commit from another branch onto your current branch, without merging the whole
branch. Real use: a hotfix made on a feature branch that also needs to land on `main` immediately,
without pulling in the rest of the feature branch's unfinished work.

## Stash

```bash
git stash              # shelve uncommitted changes
git stash pop           # bring them back (and remove from stash list)
git stash list           # see everything stashed
```
Real use: mid-change, need to switch branches urgently (prod hotfix) without committing half-done work
or losing it.

## Resolving a merge conflict — the actual mechanics, not just "edit the file"

```
<<<<<<< HEAD
your branch's version
=======
their version
>>>>>>> main
```
Edit to the final desired content, remove the markers, `git add <file>`, then `git commit` (for a
merge) or `git rebase --continue` (for a rebase). Know the difference: during a **rebase conflict**,
`git add` + `git rebase --continue` moves to the *next* commit being replayed, not a final commit —
confusing for anyone used to only resolving merge conflicts.

## `.gitignore` and already-tracked files

A `.gitignore` entry only prevents **newly untracked** files from being added — it does nothing for a
file already tracked. To actually stop tracking a file while keeping it on disk:
```bash
git rm --cached path/to/file
```
(Exactly what was done earlier in this repo's history to swap `go.mod` from tracked to ignored.)

---

## Interview questions (with the short answer you should be able to give cold)

1. *What's the actual difference between `merge` and `rebase`, beyond "one is cleaner history"?* —
   Merge creates a new commit joining two histories, preserving both as they actually happened; rebase
   replays your commits on top of the target branch, rewriting commit hashes — rebase gives linear
   history at the cost of altering what actually happened, which is exactly why it's unsafe on shared branches.
2. *Why is rebasing a shared/already-pushed branch dangerous?* — It rewrites commit hashes that others
   may have already pulled and built on — their history now diverges from yours in a way that causes
   painful, confusing conflicts when they try to sync, since Git sees the rewritten commits as entirely
   different from the ones they have.
3. *You accidentally ran `git reset --hard` and lost commits. Are they actually gone?* — Almost
   certainly not — `git reflog` shows every position `HEAD` has pointed to, including the commit from
   right before the reset; the data isn't garbage collected for a default ~90 days, so it's recoverable.
4. *What does `git bisect` actually do, and why is it faster than checking commits one by one?* — Binary
   searches between a known-good and known-bad commit, testing the midpoint repeatedly — turns an
   N-commit search into roughly log2(N) tests instead of a linear walk through history.
5. *When would you use `cherry-pick` instead of merging a whole branch?* — When you need one specific
   commit (e.g. a hotfix) from a branch without pulling in the rest of that branch's unfinished/unrelated work.
6. *During a rebase conflict, after fixing the file and `git add`-ing it, what do you run next — and why
   is it different from a merge conflict?* — `git rebase --continue`, not `git commit` — a rebase is
   replaying a sequence of commits one at a time, so continuing moves to replaying the *next* commit in
   the sequence, not finalizing a single merge commit the way a plain merge conflict resolution does.
7. *Does adding a file to `.gitignore` stop it from showing up in `git status` if it's already tracked?*
   — No — `.gitignore` only affects untracked files; an already-tracked file needs `git rm --cached` to
   stop being tracked (while optionally staying on disk) before `.gitignore` has any effect on it.