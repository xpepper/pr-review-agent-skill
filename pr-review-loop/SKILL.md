---
name: pr-review-loop
description: Use when addressing open PR review comments from any reviewer (human or bot) within the current agent session. For a fresh-context-per-comment approach, use ralph-wiggum-loop instead.
license: MIT
compatibility: Requires gh CLI or any other tool to interact with GitHub. PR branch must be checked out locally.
metadata:
  author: Pietro Di Bello
  version: "1.1.0"
allowed-tools: Bash(gh:*)
---

# PR Review Loop

## Purpose

Address all open PR review comments one at a time using an opinionated, resumable workflow. Works with comments from any reviewer (human or bot).

## Typical invocations

Users trigger this skill with prompts like:

- "Address all open review comments on this PR"
- "Work through the code review feedback on PR #42"
- "Fix the review comments left by @alice on this pull request"
- "Use pr-review-loop on PR #123"

## Prerequisites

- `gh` CLI (preferred). If unavailable, fall back to any tool available to interact with GitHub.
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

### Step 2 — Get Current PR Number and Basic Info

```bash
# Get current PR details
gh pr status

# View PR with all comments
gh pr view
```

### Step 3 — Collect Unresolved PR Comments

```bash
# Get review comments (comments on specific lines of code)
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '.[] | {id: .id, user: .user.login, author: .author.login, body: .body, created_at: .created_at, in_reply_to_id: .in_reply_to_id}'

# For current repo, use variables:
gh api repos/$(gh repo view --json owner,name | jq -r '.owner.login')/$(gh repo view --json owner,name | jq -r '.name')/pulls/$(gh pr view --json number | jq -r '.number')/comments | jq '.[] | {id: .id, user: .user.login, author: .author.login, body: .body, created_at: .created_at, in_reply_to_id: .in_reply_to_id}'
```

Filter to only unresolved comments.

### Step 4 — Triage
Read [the triage guide](references/triage-guide.md) for the specific classification framework and examples. If the guide is not available, use the MUST_FIX / SHOULD_FIX / PARK / OUT_OF_SCOPE classification with your own judgment (see definitions below).

Classify every unresolved comment as: MUST_FIX, SHOULD_FIX, PARK, or OUT_OF_SCOPE.

Triage all comments before acting on any.

If Perplexity or other research tools are available and a comment requires external knowledge to classify (e.g., library idioms, language conventions), use them to inform your decision.

### Step 5 — Process ONE comment at a time

Process in order: all MUST_FIX first, then SHOULD_FIX.
Skip PARK and OUT_OF_SCOPE for now (they are handled in the summary).

**Cascading comments:** When multiple comments form a cascade (e.g., changing a trait signature requires updating all impls, callers, and tests), group them into a single commit referencing all comment IDs. Implement the full cascade atomically — applying any single comment without the others would leave the code in an inconsistent state.

For each comment (or group of cascading comments):

**5a. Assess complexity**

Is this trivial (e.g., rename a function, fix a typo, adjust formatting)?
- Yes → fix directly, no plan needed
- No → create a plan file at `.pr-review/plan-<comment-id>.md` before touching any code

The plan file must describe:
- What the comment is asking for
- The approach to fix it
- Files that will be changed

**5b. Run safeguards**

Run all safeguards identified in Step 1. They must all pass before you touch any code.
If they fail, stop and report.

**5c. Fix or park**

- Fix: implement the change
- Fix with adaptation: if the reviewer's suggestion is directionally right but the exact code won't compile or is otherwise infeasible, implement the closest working alternative. Document the constraint in your reply (Step 5f) so the reviewer understands why the implementation differs from their suggestion.
- Park (if you discover mid-fix that it should be parked): write reasoning, revert any partial changes, no commit

**5d. Run safeguards again**

Run all safeguards. They must all pass.
If they fail, fix the regression before moving on — do not skip this step.

**5e. Commit and push**

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

**5f. Reply to the PR comment**

Post a reply on the PR comment explaining:
- What was done (for fixes: reference the commit)
- Why it was parked (for deferred items)
- Why it was rejected (for out-of-scope items)

Preferred (gh CLI):
```bash
gh api repos/{owner}/{repo}/pulls/{pull_number}/comments/{comment_id}/replies \
  -f body="<reply text>"
```

**5g. Resolve the comment**

Mark the comment as resolved on GitHub.

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

**5h. Delete plan file**

If a plan file was created, delete it:
```bash
rm .pr-review/plan-<comment-id>.md
```

### Step 6 — Stop condition

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

### Step 7 — Summary

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
