# Prepare Review Commits

An [Agent Skills](https://agentskills.io) skill that turns the current
uncommitted diff into a logical sequence of conventional commits, ready for
pull-request review.

## Install

```bash
npx skills add xpepper/pr-review-agent-skill/prepare-review-commits
```

## Usage

This skill activates only for an explicit review-readiness request. It does
**not** run for generic requests like "commit my changes" — those stay out of
scope.

```
Prepare review-ready commits for this branch
```
```
Make this branch review-ready before I push
```
```
Use prepare-review-commits against release/2.4
```

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
- Restores the original working tree and index state if staging, committing,
  or validation fails partway through.
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
- `HEAD` is detached.
- A merge, rebase, or cherry-pick is already in progress, or unmerged paths
  exist.
- The diff mixes unrelated work, or the intended narrative stays materially
  ambiguous.

An already-clean working tree is reported as a successful no-op, not a
failure.

## Final report

Every run reports:

- The base branch and the current branch's relationship to it.
- The ordered list of commits created, each with its message and files.
- Validation results for each commit and the final state — or an explicit
  "unvalidated" warning if no command was discoverable.
- Warnings, such as a commit sequence longer than eight commits.
- Explicit confirmation that nothing was pushed.
