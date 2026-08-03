# Prepare Review Commits

An [Agent Skills](https://agentskills.io) skill that turns the current
uncommitted diff into a logical sequence of conventional commits, ready for
pull-request review.

## Install

```bash
npx skills add xpepper/pr-review-agent-skill/prepare-review-commits
```

## Usage

This skill is **manual-only**. Its frontmatter sets
`disable-model-invocation: true`, so the agent never auto-loads it from
context relevance — you have to invoke it yourself:

```
/prepare-review-commits
```

Naming the skill in a request works too:

```
Use prepare-review-commits against release/2.4
```
```
Run the prepare-review-commits skill, then stop
```

Once invoked, it still expects a review-readiness request — "prepare
review-ready commits for this branch", "make this branch review-ready before I
push". It does **not** run for generic requests like "commit my changes";
those stay out of scope.

> `disable-model-invocation` is honoured by Claude Code. Agents that do not
> support the field ignore it and fall back to the description, which already
> restricts activation to explicit review-readiness requests.

## What it does

- Organizes all uncommitted, non-ignored changes (tracked and untracked) into
  an ordered sequence of self-contained commits.
- Writes Conventional Commit messages (`type: imperative subject`).
- Keeps each commit's tests together with the behavior they establish, rather
  than splitting production code from its tests.
- Runs discovered validation commands after each commit and after the final
  commit, when the repository exposes one (e.g. via scripts, a Makefile, or
  CI config). If no validation command can be discovered, it proceeds anyway
  and reports the work as unvalidated rather than inventing a check.
- Restores the original working tree and index state — including deletions —
  if staging, committing, or validation fails partway through, and verifies
  that restoration before reporting success.
- Never pushes, fetches, rebases, or rewrites/reorders any commit that existed
  before it ran.

## Prerequisites

- Git (required).
- [`gh` CLI](https://cli.github.com/) (optional) — used for pull request and
  issue context when available.

## Base branch and abort conditions

You can supply an explicit base branch (as in the `release/2.4` example
above); otherwise the skill infers one from branch tracking configuration,
the repository default branch, or available PR context.

The skill aborts without changing any Git state when:

- No base branch can be identified.
- The branch has no commit yet (unborn `HEAD`).
- `HEAD` is detached.
- A merge, rebase, or cherry-pick is already in progress, or unmerged paths
  exist.
- The working tree already contains an untracked embedded Git repository —
  Git records such a directory only as a gitlink, so its contents cannot be
  backed up and the run cannot be made safe.
- The diff mixes unrelated work, or the intended narrative stays materially
  ambiguous.

An already-clean working tree — or one whose only changes are ignored paths —
is reported as a successful no-op, not a failure.

## Recovery guarantees and limits

If anything fails partway through — staging, a hook, a commit, or a discovered
validation command — the skill restores the exact state it started from:
`HEAD`, the index, and every non-ignored tracked and untracked file, including
files that were deleted before the run and files a hook or validation command
rewrote or removed. It then verifies the restoration and refuses to claim
success unless every check passes.

Three things sit outside that guarantee, and the skill says so rather than
hiding them:

- **Ignored files are never touched**, so an ignored build artifact that a hook
  or validation command wrote or changed is not reverted.
- **Empty directories cannot be tracked by Git**, so a directory that was empty
  before the run — or that only held untracked files — is not recreated. No
  file content is lost.
- **A Git repository created inside the working tree during the run** cannot be
  removed safely, so recovery leaves it in place, reports it, and keeps the
  backup instead of claiming exact restoration.

When recovery cannot be verified, the skill stops and reports the retained
backup refs (`refs/prepare-review-commits/<run-id>/worktree` and
`.../index`) plus the state directory, so the original state is always
recoverable by hand.

## Final report

Every run reports:

- The base branch and the current branch's relationship to it.
- The ordered list of commits created, each with its message and files.
- Validation results for each commit and the final state — or an explicit
  "unvalidated" warning if no command was discoverable.
- Warnings, such as a commit sequence longer than eight commits.
- Explicit confirmation that nothing was pushed.
