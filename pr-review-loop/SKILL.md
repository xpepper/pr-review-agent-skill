---
name: pr-review-loop
description: Use when addressing open PR review comments — triages each comment (MUST_FIX, SHOULD_FIX, PARK, OUT_OF_SCOPE), fixes one at a time, commits, replies, and resolves. Works with any reviewer (human or bot). Resumable across context windows.
license: MIT
compatibility: Requires gh CLI (recommended) or GitHub token for REST API fallback. PR branch must be checked out locally.
metadata:
  author: Pietro Di Bello
  version: "1.0.0"
allowed-tools: Bash(gh:*)
---

# PR Review Loop

## Purpose

Address all open PR review comments one at a time using an opinionated, resumable workflow. Works with comments from any reviewer (human or bot).

## Prerequisites

- `gh` CLI (preferred). If unavailable, fall back to the GitHub REST API.
- The PR branch must be checked out locally.

## Process

### Step 1 — Pre-flight

Inspect the project for safeguard conventions by checking these files (if they exist):
- `CLAUDE.md`, `AGENTS.md`
- `Makefile`
- `.github/workflows/`
- `README.md`

Identify all required safeguards (tests, compilation, linting, formatting, etc.).
Run all of them. If any fail, stop immediately and report — do not proceed on a broken baseline.

### Step 2 — Collect

Fetch all unresolved PR comments.

Preferred (gh CLI):
```bash
gh pr view --json comments,reviews
gh api repos/{owner}/{repo}/pulls/{pr}/comments
```

Fallback (REST API):
```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/{owner}/{repo}/pulls/{pr}/comments
```

Filter to only unresolved comments.

### Step 3 — Triage

Read `references/triage-guide.md`.

Classify every unresolved comment as: MUST_FIX, SHOULD_FIX, PARK, or OUT_OF_SCOPE.

Triage all comments before acting on any.

If Perplexity is available and a comment requires external knowledge to classify (e.g., library idioms, language conventions), use it:
```bash
llm -m sonar 'your question here'
```

### Step 4 — Process one comment at a time

Process in order: all MUST_FIX first, then SHOULD_FIX.
Skip PARK and OUT_OF_SCOPE for now (they are handled in the summary).

For each comment:

**4a. Assess complexity**

Is this trivial (e.g., rename a function, fix a typo, adjust formatting)?
- Yes → fix directly, no plan needed
- No → create a plan file at `.pr-review/plan-<comment-id>.md` before touching any code

The plan file must describe:
- What the comment is asking for
- The approach to fix it
- Files that will be changed

**4b. Run safeguards**

Run all safeguards identified in Step 1. They must all pass before you touch any code.
If they fail, stop and report.

**4c. Fix or park**

- Fix: implement the change
- Park (if you discover mid-fix that it should be parked): write reasoning, revert any partial changes, no commit

**4d. Run safeguards again**

Run all safeguards. They must all pass.
If they fail, fix the regression before moving on — do not skip this step.

**4e. Commit and push**

Each comment gets its own focused commit. Reference the comment author in the message body.

```bash
git add <changed files>
git commit -m "<conventional commit message describing the fix>

Addresses PR comment from @<reviewer>."
git push
```

Example commit flow across multiple comments:
```bash
# Comment 1: Add missing documentation
git commit -m "docs: add module-level documentation for MetricsRecorder

Addresses PR comment from @reviewer about missing module docs."
git push

# Comment 2: Use Duration instead of i64
git commit -m "refactor: use Duration type for timing parameters

Addresses PR comment from @reviewer - improves type safety."
git push
```

**4f. Reply to the PR comment**

Post a reply on the PR comment explaining:
- What was done (for fixes: reference the commit)
- Why it was parked (for deferred items)
- Why it was rejected (for out-of-scope items)

Preferred (gh CLI):
```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/replies \
  -f body="<reply text>"
```

**4g. Resolve the comment**

Mark the comment as resolved on GitHub using GraphQL (the REST API does not support resolution).

First, find the thread ID for the comment:
```bash
gh api graphql -f query='
query {
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {pr_number}) {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          comments(first: 1) { nodes { body } }
        }
      }
    }
  }
}'
```

Then resolve the thread:
```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "{thread_id}"}) {
    thread { id isResolved }
  }
}'
```

**4h. Delete plan file**

If a plan file was created, delete it:
```bash
rm .pr-review/plan-<comment-id>.md
```

### Step 5 — Stop condition

Stop when no MUST_FIX or SHOULD_FIX comments remain.

If you prefer to batch-resolve all threads at once rather than one by one, you can do so here:
```bash
gh api graphql -f query='
query {
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {pr_number}) {
      reviewThreads(first: 50) {
        nodes { id isResolved comments(first: 1) { nodes { body } } }
      }
    }
  }
}' | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false) | .id' \
  | while read thread_id; do
    gh api graphql -f query="mutation { resolveReviewThread(input: {threadId: \"$thread_id\"}) { thread { id } } }"
  done
```

### Step 6 — Summary

Post a final comment on the PR summarising:

```
## PR Review Loop — Summary

### Fixed
- [commit abc1234] Renamed `foo` to `bar` (comment by @alice)
- ...

### Parked
- Refactor of X module deferred — tracked in #<issue> (comment by @bob)
- ...

### Rejected
- Suggestion to use Y rejected: project convention is Z (comment by @carol)
- ...
```

## Resumability

This skill is designed to be interrupted and restarted in a fresh context at any point.

On startup:
1. Run pre-flight (Step 1)
2. Re-fetch unresolved comments from GitHub (Step 2) — already-resolved comments won't appear
3. Check for an existing `.pr-review/plan-*.md` file — if found, you are mid-fix on that comment; continue from Step 4b
4. Triage remaining comments and continue

This means no progress is ever lost. Each fix is committed and pushed before moving on.

## State Directory

`.pr-review/` at the repo root (gitignored by the project).
- `plan-<comment-id>.md` — plan for the comment currently in progress (deleted after resolution)

## Do Not

- Bundle all PR feedback into one large commit
- Make multiple unrelated changes in a single commit
- Push all changes at once without intermediate commits
- Leave comments unresolved after addressing them
