---
name: prepare-review-commits
description: Use when explicitly asked to prepare review-ready commits or make an uncommitted branch review-ready before pushing. Organizes only uncommitted changes into validated, self-contained Conventional Commits; never rewrites history or pushes.
license: MIT
compatibility: Requires Git. Optionally uses gh CLI for pull request and issue context.
metadata:
  author: Pietro Di Bello
  version: "1.0.0"
allowed-tools: Bash(git:*), Bash(gh:*)
---

# Prepare Review Commits

## Trigger

This workflow activates only for an explicit review-readiness request — for
example "prepare review-ready commits" or "make this branch review-ready
before I push". It must **not** activate for generic requests such as "commit
my changes"; those are out of scope for this skill.

## Preflight

1. Read repository instructions and contributor documentation, then inspect
   the current branch, `HEAD`, status including untracked files, staged and
   unstaged diffs, ignored files, recent history, and the candidate base.
2. Accept an explicit base from the request. Otherwise infer one from the
   branch's tracking configuration, repository default branch, or available
   PR context. Abort if no base can be identified.
3. Abort without changing Git state when `HEAD` is detached, a merge/rebase/
   cherry-pick is active, unmerged paths exist, or there are no relevant
   changes.
4. Infer the goal from repository guidance, local history, and optional PR or
   issue context. Abort if the full diff contains unrelated work or the intended
   narrative remains materially ambiguous.

Report an already-clean working tree as a successful no-op — this is not a
failure.

Inspect the base relationship only. Never run `git fetch`, `git rebase`, or
any command that mutates a remote.

## Plan Commit Boundaries

Form an ordered, dependency-respecting sequence of vertical commits. Each
commit must:

- Explain one reviewable behavior or independently valuable change.
- Include its production code and the tests that establish that behavior.
- Keep pure refactors, documentation, tooling, and formatting separate only
  when each is independently valuable.
- Use `type: imperative subject`; add `(scope)` only where existing repository
  convention makes that scope unambiguous.
- Include generated artifacts and binary files with their unique owning source
  change. Abort if ownership is ambiguous.

Group dependent changes together rather than emitting a temporarily broken
commit. Never cap the number of commits at an arbitrary limit, but warn the
user when the plan produces more than eight commits.

## Make Changes Transactionally

Before unstaging or creating any commit, record the recovery state in a
unique, secure temporary state directory. Create it **outside the working
tree** (for example under the repository's `.git` directory or the OS temp
directory) so that it never appears in `git status`, diffs, or the sequence of
staged changes it is meant to describe:

```bash
state_dir="$(mktemp -d "$(git rev-parse --git-dir)/prc-state.XXXXXX")"
start_head="$(git rev-parse HEAD)"
git diff --binary > "$state_dir/unstaged.patch"
git diff --cached --binary > "$state_dir/staged.patch"
git status --porcelain=v1 -uall > "$state_dir/status.before"
```

Clean up the state directory only after the entire sequence succeeds.

Preserve the original staged/unstaged split by resetting first, then staging
only what belongs to the next planned commit:

```bash
git reset
# Stage only the files and hunks that belong to the next planned commit.
git add -- <whole-file-paths>
git add -p -- <partially-owned-paths>
git commit -m "<conventional message>"
```

Use ordinary `git commit`. Never pass hook-bypass flags (e.g. `--no-verify`) —
honor hooks and commit signing as configured.

If staging, commit, or a discovered validation check fails, restore all
created commits and the original index split:

```bash
git reset --mixed "$start_head"
git apply --cached "$state_dir/staged.patch"
```

Then compare the saved status, staged patch, and unstaged patch with the
restored repository. If they differ, stop and report the discrepancy instead
of claiming recovery succeeded. Untracked paths are left in place by the mixed
reset and must be checked against `status.before`.

## Validate Each Commit

1. Discover repository validation commands from instructions, scripts,
   Makefiles, and CI configuration; never invent a command.
2. Run the smallest relevant discovered command after each commit.
3. Run the normal full discovered validation after the final commit.
4. On any discovered-command failure, run transactional recovery and report
   the failing command and output.
5. If no validation command exists, proceed but mark every created commit and
   the final summary as unvalidated.

## Report

The final report must include:

- The inferred or explicit base and its local relationship to the branch.
- The ordered commit list, each with its message and changed files.
- Targeted and final validation results (or the unvalidated warning).
- Warnings, including a long commit sequence (more than eight) and an
  unvalidated state.
- An explicit statement that nothing was pushed.

## Do Not

- Activate for a generic "commit my changes" request without explicit
  review-readiness intent.
- Rewrite, amend, or reorder any commit that existed before this workflow ran.
- Run `git fetch`, `git rebase`, `git push`, or any other remote mutation.
- Bypass hooks or commit signing.
- Cap the commit count at an arbitrary number.
- Claim recovery succeeded without verifying the restored state matches the
  recorded status and patches.
